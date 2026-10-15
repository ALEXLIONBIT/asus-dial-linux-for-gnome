#!/usr/bin/env python3
"""Worker of ASUS Dial AI. It runs inside the private venv (~/.local/share/asus-dial-ai/venv), never in the system Python.

It speaks JSON lines: one command per line on stdin, one event per line on stdout (everything else goes to stderr).

  --mode airllm   load / chat with a big model through AirLLM (layer by layer, so a 70B fits in a few GB of VRAM)
      {"cmd":"load","model":"org/name","compression":"4bit"|"8bit"|"none","delete_original":true}
      {"cmd":"chat","messages":[{"role":..,"content":..}],"max_new_tokens":256,"temperature":0.7}
      {"cmd":"stop"}   {"cmd":"unload"}   {"cmd":"quit"}
  --mode voice    speech to text (faster-whisper) and text to speech (Piper)
      {"cmd":"stt_load","size":"small"}   {"cmd":"transcribe","wav":"/path.wav","lang":"it"}
      {"cmd":"tts_load","voice":"it_IT-paola-medium"}   {"cmd":"speak","text":"..","wav":"/path.wav"}
"""
import json
import os
import shutil
import sys
import threading

# keep the protocol channel clean: libraries love to print on stdout
_proto = os.fdopen(os.dup(1), "w", buffering=1)
os.dup2(2, 1)
sys.stdout = sys.stderr

HOME = os.path.expanduser("~/.local/share/asus-dial-ai")
os.environ.setdefault("HF_HOME", os.path.join(HOME, "hf"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
SHARDS = os.path.join(HOME, "shards")
VOICES = os.path.join(HOME, "voices")
_lock = threading.Lock()


def send(**ev):
    with _lock:
        _proto.write(json.dumps(ev, ensure_ascii=False) + "\n")
        _proto.flush()


def commands():
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except ValueError:
                continue


# ----------------------------------------------------------------------------------------------- AirLLM
class AirLLM:
    def __init__(self):
        self.model = None
        self.stop_flag = False
        self.device = "cpu"

    def progress_class(self):
        """A tqdm replacement that reports the download as events."""
        from tqdm.auto import tqdm

        outer = self
        state = {"done": 0, "total": 0}

        class P(tqdm):
            def __init__(self, *a, **k):
                k["disable"] = False
                super().__init__(*a, **k)
                if self.unit == "B" and self.total:
                    state["total"] += self.total

            def update(self, n=1):
                r = super().update(n)
                if self.unit == "B" and n:
                    state["done"] += n
                    send(event="download", done=state["done"], total=state["total"])
                return r

        return P

    def load(self, model, compression, delete_original):
        import torch  # noqa: F401
        from huggingface_hub import snapshot_download

        send(event="status", key="downloading")
        path = snapshot_download(model, tqdm_class=self.progress_class(),
                                 allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "tokenizer*"])
        send(event="status", key="splitting")
        from airllm import AutoModel

        gpu = torch.cuda.is_available()
        if not gpu:
            compression = "none"  # 4/8-bit layers need the GPU: on the CPU use the original precision
        self.device = "cuda:0" if gpu else "cpu"
        send(event="device", device=self.device)
        kw = {"layer_shards_saving_path": os.path.join(SHARDS, model.replace("/", "--") + "-" + compression),
              "device": self.device}
        if compression in ("4bit", "8bit"):
            kw["compression"] = compression
        os.makedirs(kw["layer_shards_saving_path"], exist_ok=True)
        self.model = AutoModel.from_pretrained(path, **kw)
        if delete_original and os.path.isdir(path):
            # the layer files are all that is needed now: free the original download (it is ours, in HF_HOME)
            hub = os.path.join(os.environ["HF_HOME"], "hub")
            if os.path.realpath(path).startswith(os.path.realpath(hub)):
                root = os.path.dirname(os.path.dirname(os.path.realpath(path)))
                shutil.rmtree(root, ignore_errors=True)
        send(event="loaded")

    def chat(self, messages, max_new_tokens, temperature):
        import torch
        from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer

        if self.model is None:
            send(event="error", msg="model not loaded")
            return
        tok = self.model.tokenizer
        try:
            prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\nassistant:"
        ids = tok(prompt, return_tensors="pt", return_attention_mask=False, truncation=True, max_length=3072,
                  padding=False, add_special_tokens=False)["input_ids"]
        ids = ids.to(self.device)
        self.stop_flag = False
        outer = self

        class Stop(StoppingCriteria):
            def __call__(self, input_ids, scores, **kw):
                return outer.stop_flag

        streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
        kw = dict(input_ids=ids, max_new_tokens=int(max_new_tokens), use_cache=True, return_dict_in_generate=True,
                  streamer=streamer, stopping_criteria=StoppingCriteriaList([Stop()]))
        if temperature and temperature > 0.01:
            kw.update(do_sample=True, temperature=float(temperature), top_p=0.9)
        else:
            kw.update(do_sample=False)
        err = []

        def run():
            try:
                self.model.generate(**kw)
            except Exception as e:  # noqa: BLE001
                err.append(str(e))
                streamer.end()

        th = threading.Thread(target=run, daemon=True)
        th.start()
        for piece in streamer:
            if piece:
                send(event="token", text=piece)
        th.join()
        if err:
            send(event="error", msg=err[0])
        else:
            send(event="done")

    def serve(self):
        for c in commands():
            cmd = c.get("cmd")
            try:
                if cmd == "load":
                    self.load(c["model"], c.get("compression", "4bit"), c.get("delete_original", True))
                elif cmd == "chat":
                    threading.Thread(target=self.chat, args=(c["messages"], c.get("max_new_tokens", 256),
                                                              c.get("temperature", 0.7)), daemon=True).start()
                elif cmd == "stop":
                    self.stop_flag = True
                elif cmd == "unload":
                    self.model = None
                    send(event="unloaded")
                elif cmd == "quit":
                    break
            except Exception as e:  # noqa: BLE001
                send(event="error", msg=f"{type(e).__name__}: {e}")


# ----------------------------------------------------------------------------------------------- voice
class Voice:
    def __init__(self):
        self.stt = None
        self.tts = {}

    def stt_load(self, size):
        from faster_whisper import WhisperModel

        send(event="status", key="loading_stt")
        self.stt = WhisperModel(size, device="cpu", compute_type="int8")
        send(event="stt_ready")

    def transcribe(self, wav, lang):
        if self.stt is None:
            self.stt_load("small")
        import wave

        import numpy as np

        with wave.open(wav, "rb") as w:  # decoded here: the app records 16 kHz mono 16-bit (no PyAV needed)
            audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        segs, info = self.stt.transcribe(audio, language=lang or None, vad_filter=True, beam_size=1)
        send(event="text", text=" ".join(s.text.strip() for s in segs).strip(), lang=info.language)

    def tts_load(self, voice):
        from piper import PiperVoice

        onnx = os.path.join(VOICES, voice + ".onnx")
        if not os.path.exists(onnx):
            self.download_voice(voice)
        self.tts[voice] = PiperVoice.load(onnx)
        send(event="tts_ready", voice=voice)

    @staticmethod
    def download_voice(voice):
        import urllib.request

        lang = voice.split("-")[0]  # it_IT-paola-medium
        name, quality = voice.split("-")[1], voice.split("-")[2]
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang.split('_')[0]}/{lang}/{name}/{quality}/{voice}"
        os.makedirs(VOICES, exist_ok=True)
        send(event="status", key="downloading_voice")
        for ext in (".onnx.json", ".onnx"):
            tmp = os.path.join(VOICES, voice + ext + ".part")
            urllib.request.urlretrieve(base + ext, tmp)
            os.replace(tmp, os.path.join(VOICES, voice + ext))

    def speak(self, text, wav, voice, length_scale=1.0, noise_scale=0.667, noise_w=0.8, volume=1.0, pitch=1.0, fx="none"):
        """Piper speaks; pitch is a resampling trick (the voice is made slower by `pitch`, then played `pitch` times
        faster), and fx ("robot", "echo") is a little signal processing on top."""
        import io
        import wave

        import numpy as np

        if voice not in self.tts:
            self.tts_load(voice)
        v = self.tts[voice]
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            try:
                from piper import SynthesisConfig

                cfg = SynthesisConfig(length_scale=length_scale * pitch, noise_scale=noise_scale, noise_w_scale=noise_w, volume=volume)
                v.synthesize_wav(text, w, syn_config=cfg)
            except ImportError:  # older piper: no tuning
                v.synthesize(text, w)
        buf.seek(0)
        with wave.open(buf, "rb") as r:
            rate = r.getframerate()
            x = np.frombuffer(r.readframes(r.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        if fx == "robot":
            t = np.arange(len(x)) / rate
            x = 0.4 * x + 0.9 * x * np.sin(2 * np.pi * 55 * t)
        elif fx == "echo":
            pad = int(rate * 0.55)
            y = np.concatenate([x, np.zeros(pad, dtype=np.float32)])
            for delay, gain in ((0.16, 0.5), (0.32, 0.3), (0.5, 0.16)):
                d = int(rate * delay)
                y[d:d + len(x)] += gain * x
            x = y
        x = np.clip(x, -1.0, 1.0)
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(int(rate * pitch))
            w.writeframes((x * 32767).astype(np.int16).tobytes())
        send(event="spoken", wav=wav)

    def serve(self):
        for c in commands():
            cmd = c.get("cmd")
            try:
                if cmd == "stt_load":
                    self.stt_load(c.get("size", "small"))
                elif cmd == "transcribe":
                    self.transcribe(c["wav"], c.get("lang"))
                elif cmd == "tts_load":
                    self.tts_load(c["voice"])
                elif cmd == "speak":
                    self.speak(c["text"], c["wav"], c.get("voice", "en_US-lessac-medium"), c.get("length_scale", 1.0),
                               c.get("noise_scale", 0.667), c.get("noise_w", 0.8), c.get("volume", 1.0), c.get("pitch", 1.0),
                               c.get("fx", "none"))
                elif cmd == "quit":
                    break
            except Exception as e:  # noqa: BLE001
                send(event="error", msg=f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    mode = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "airllm"
    send(event="hello", mode=mode)
    (AirLLM() if mode == "airllm" else Voice()).serve()
