"""Shared by asus-dial (the driver) and asus-dial-manager (the settings app).

Holds the config file (~/.config/asus-dial/config.json), the list of built-in modes with their
icons and names in English / Spanish / Italian, and the key-name <-> Linux key-code tables used
by custom modes ("ctrl+shift+t", "p", "ctrl+c ctrl+v", ...).
"""
import json
import os
import re

CONFIG_DIR = os.path.expanduser("~/.config/asus-dial")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LANG_FILE = os.path.expanduser("~/.config/asus-dial.lang")
LANGS = ("en", "es", "it")
LANG_NAMES = {"en": "English", "es": "Español", "it": "Italiano"}

# Built-in modes. The position in these lists is the tool number used inside the driver.
BUILTIN_IDS = ["scroll", "volume", "brightness", "zoom", "video", "tabs", "arrows", "house", "power",
               "dice", "timer", "speed", "night", "windows", "find", "keylight", "language", "rick", "ai"]
ICONS = ["↕", "🔊", "☀", "🔍", "▶", "🗂", "↔", "🏠", "⏻", "🎲", "⏲", "⏩", "🌙", "🪟", "🔎", "⌨", "🌐", "✨", "🤖"]
NAMES_L = {
    "en": ["Scroll", "Volume", "Brightness", "Zoom", "Video", "Tabs", "Arrows", "House", "Power off",
           "Dice", "Timer", "Speed", "Light", "Windows", "Find", "Keyboard", "Language", "Rickroll", "AI"],
    "es": ["Desplazar", "Volumen", "Brillo", "Zoom", "Vídeo", "Pestañas", "Flechas", "Casa", "Apagar",
           "Dado", "Temporiz.", "Velocidad", "Luz", "Ventanas", "Buscar", "Teclado", "Idioma", "Rickroll", "IA"],
    "it": ["Scorri", "Volume", "Luminosità", "Zoom", "Video", "Schede", "Frecce", "Casa", "Arresta",
           "Dado", "Timer", "Velocità", "Luce", "Finestre", "Trova", "Tastiera", "Lingua", "Rickroll", "AI"],
}
# default order of the radial menu
DEFAULT_ORDER = ["scroll", "volume", "brightness", "keylight", "night", "zoom", "video", "speed", "timer", "ai",
                 "tabs", "find", "windows", "arrows", "dice", "house", "rick", "language", "power"]
BROWSER_ONLY_IDS = ("tabs", "find")

# Look of the radial menu and of the on-screen messages (see asus_dial_theme.py for the drawing)
DEFAULT_THEME = {
    "bg_type": "color",        # color | image | rainbow | halloween
    "bg_color": "#141419",
    "bg_opacity": 0.88,        # 0..1
    "bg_image": "",            # cropped PNG written by the manager
    "image_dim": 0.35,         # 0..1, darkens the image so the text stays readable
    "blur": 0,                 # 0..40: frosted glass (blurs a snapshot of what is behind the menu)
    "accent": "#4080ff",       # selected slice and bars
    "text": "#ffffff",
    "glow": False,
    "glow_color": "#4080ff",
    "glow_strength": 0.8,      # 0..1
    "reflection": 0.0,         # 0..1: glossy highlight
    "shadow": False,
    "shadow_strength": 0.6,    # 0..1
    "sparkles": False,
    "speed": 0.5,              # animation speed of rainbow / sparkles / halloween
}
THEME_PRESETS = {
    "default": {},
    "glass": {"bg_type": "color", "bg_color": "#ffffff", "bg_opacity": 0.16, "blur": 18, "accent": "#7ab8ff", "text": "#ffffff",
              "reflection": 0.55, "shadow": True, "shadow_strength": 0.5, "glow": False, "sparkles": False},
    "neon": {"bg_type": "color", "bg_color": "#06060f", "bg_opacity": 0.92, "accent": "#ff2bd6", "text": "#e8fbff", "glow": True,
             "glow_color": "#ff2bd6", "glow_strength": 1.0, "reflection": 0.12, "shadow": True, "shadow_strength": 0.5, "sparkles": False},
    "rainbow": {"bg_type": "rainbow", "bg_opacity": 0.92, "accent": "#101018", "text": "#ffffff", "glow": True, "glow_color": "#ffffff",
                "glow_strength": 0.6, "reflection": 0.35, "shadow": True, "shadow_strength": 0.5, "sparkles": True},
    "sunset": {"bg_type": "color", "bg_color": "#2a0f2e", "bg_opacity": 0.92, "accent": "#ff7a45", "text": "#fff1e6", "glow": True,
               "glow_color": "#ff7a45", "glow_strength": 0.6, "reflection": 0.2, "shadow": True, "shadow_strength": 0.5, "sparkles": False},
    "paper": {"bg_type": "color", "bg_color": "#f4efe6", "bg_opacity": 0.96, "accent": "#3b82f6", "text": "#2b2b2b", "glow": False,
              "reflection": 0.3, "shadow": True, "shadow_strength": 0.45, "sparkles": False},
    "halloween": {"bg_type": "halloween", "bg_opacity": 0.95, "accent": "#ff7a00", "text": "#fff3e0", "glow": True, "glow_color": "#ff7a00",
                  "glow_strength": 0.9, "reflection": 0.0, "shadow": True, "shadow_strength": 0.6, "sparkles": False},
}
PRESET_NAMES = {
    "default": ("Default", "Predeterminado", "Predefinito"), "glass": ("Glass", "Cristal", "Vetro"),
    "neon": ("Neon", "Neón", "Neon"), "rainbow": ("Rainbow ✨", "Arcoíris ✨", "Arcobaleno ✨"),
    "sunset": ("Sunset", "Atardecer", "Tramonto"), "paper": ("Paper (light)", "Papel (claro)", "Carta (chiaro)"),
    "halloween": ("Halloween 🎃", "Halloween 🎃", "Halloween 🎃"),
}


def theme_of(cfg):
    """The theme dict with every key present (and values of the right kind)."""
    th = dict(DEFAULT_THEME)
    user = cfg.get("theme") if isinstance(cfg.get("theme"), dict) else {}
    for k, v in user.items():
        if k in th and isinstance(v, type(th[k])) or (k in th and isinstance(th[k], float) and isinstance(v, int) and not isinstance(v, bool)):
            th[k] = v
    return th


DEFAULT_CONFIG = {
    "version": 1,
    "modes": {"disabled": [], "order": list(DEFAULT_ORDER)},
    "custom": [],  # {"id": "p", "name": "P", "icon": "⌨", "click": "p", "cw": "", "ccw": ""}
    "welcome": {"enabled": True, "character": "human", "color": "#4080ff", "rainbow": False, "image": "", "message": "", "name": ""},
    "theme": {},
}


# ------------------------------------------------------------------ config file
def _merge(default, data):
    out = json.loads(json.dumps(default))
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = _merge(out[k], v)
            else:
                out[k] = v
    return out


def load():
    """The config, with defaults filled in. A missing or broken file gives the defaults."""
    try:
        with open(CONFIG_FILE) as f:
            cfg = _merge(DEFAULT_CONFIG, json.load(f))
    except (OSError, ValueError):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    custom = []
    for c in cfg.get("custom", []):
        if isinstance(c, dict) and c.get("id") and c.get("name"):
            custom.append({"id": str(c["id"]), "name": str(c["name"]), "icon": str(c.get("icon") or "⌨"),
                           "click": str(c.get("click") or ""), "cw": str(c.get("cw") or ""), "ccw": str(c.get("ccw") or "")})
    cfg["custom"] = custom
    return cfg


def save(cfg):
    """Write the config atomically (the driver notices the change by itself)."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_FILE)


def config_mtime():
    try:
        return os.stat(CONFIG_FILE).st_mtime_ns
    except OSError:
        return 0


def mode_order(cfg):
    """Ids of the enabled modes, in menu order: built-ins by id, custom ones as 'custom:<id>'."""
    known = list(BUILTIN_IDS) + ["custom:" + c["id"] for c in cfg["custom"]]
    order = [i for i in cfg["modes"].get("order", []) if i in known]
    order += [i for i in DEFAULT_ORDER if i in known and i not in order]
    order += [i for i in known if i not in order]
    disabled = set(cfg["modes"].get("disabled", []))
    return [i for i in order if i not in disabled]


def all_modes(cfg):
    """Every mode (enabled or not) in menu order, as (id, enabled)."""
    disabled = set(cfg["modes"].get("disabled", []))
    cfg2 = json.loads(json.dumps(cfg))
    cfg2["modes"]["disabled"] = []
    return [(i, i not in disabled) for i in mode_order(cfg2)]


def slug(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "mode"
    n, cand = 1, base
    while cand in taken:
        n += 1
        cand = f"{base}-{n}"
    return cand


# ------------------------------------------------------------------ keys
# Linux input event codes. They are physical key positions (US layout names).
_LETTERS = dict(zip("abcdefghijklmnopqrstuvwxyz",
                    [30, 48, 46, 32, 18, 33, 34, 35, 23, 36, 37, 38, 50, 49, 24, 25, 16, 19, 31, 20, 22, 47, 17, 45, 21, 44]))
KEY_NAMES = dict(_LETTERS)
KEY_NAMES.update({str(d): c for d, c in zip(range(1, 10), range(2, 11))})
KEY_NAMES["0"] = 11
KEY_NAMES.update({
    "minus": 12, "equal": 13, "backspace": 14, "tab": 15, "bracketleft": 26, "bracketright": 27, "enter": 28,
    "semicolon": 39, "apostrophe": 40, "grave": 41, "backslash": 43, "comma": 51, "period": 52, "slash": 53,
    "space": 57, "esc": 1, "capslock": 58, "home": 102, "up": 103, "pageup": 104, "left": 105, "right": 106,
    "end": 107, "down": 108, "pagedown": 109, "insert": 110, "delete": 111, "print": 99, "pause": 119, "menu": 127,
    "kpplus": 78, "kpminus": 74, "kpasterisk": 55, "kpslash": 98, "kpenter": 96,
    "volumeup": 115, "volumedown": 114, "mute": 113, "playpause": 164, "next": 163, "previous": 165,
})
KEY_NAMES.update({f"f{i}": c for i, c in zip(range(1, 11), range(59, 69))})
KEY_NAMES.update({"f11": 87, "f12": 88})
MOD_NAMES = {"ctrl": 29, "shift": 42, "alt": 56, "super": 125, "altgr": 100}
_ALIASES = {"control": "ctrl", "ctl": "ctrl", "win": "super", "meta": "super", "windows": "super", "return": "enter",
            "escape": "esc", "del": "delete", "pgup": "pageup", "pgdn": "pagedown", "ins": "insert", "plus": "kpplus",
            "spacebar": "space", "bksp": "backspace", "arrowup": "up", "arrowdown": "down", "arrowleft": "left",
            "arrowright": "right"}
CODE_NAMES = {c: n for n, c in KEY_NAMES.items()}
CODE_NAMES.update({c: n for n, c in MOD_NAMES.items()})
ALL_KEYCODES = sorted(set(KEY_NAMES.values()) | set(MOD_NAMES.values()))


def parse_combo(text):
    """'ctrl+shift+t' -> ([29, 42], 20). A lone modifier ('super') is a key press of that modifier."""
    parts = [_ALIASES.get(p, p) for p in re.split(r"\s*\+\s*", text.strip().lower()) if p]
    if not parts:
        raise ValueError("empty")
    *mods, key = parts
    codes = []
    for m in mods:
        if m not in MOD_NAMES:
            raise ValueError(f"unknown modifier: {m}")
        codes.append(MOD_NAMES[m])
    if key in MOD_NAMES and not mods:
        return [], MOD_NAMES[key]
    if key not in KEY_NAMES:
        raise ValueError(f"unknown key: {key}")
    return codes, KEY_NAMES[key]


def parse_sequence(text):
    """'ctrl+c ctrl+v' -> [([29], 46), ([29], 47)]. Combos are separated by spaces or commas. Empty = []."""
    return [parse_combo(tok) for tok in re.split(r"[\s,]+", text.strip()) if tok]


def combo_text(mod_codes, key_code):
    return "+".join([CODE_NAMES[m] for m in mod_codes] + [CODE_NAMES.get(key_code, f"key{key_code}")])
