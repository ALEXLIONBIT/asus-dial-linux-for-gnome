# ASUS Dial Linux for GNOME

Driver non ufficiale per la **manopola ASUS Dial** (quella dei portatili ProArt StudioBook) su Linux con GNOME, con un menu circolare a schermo e 16 modalità.

Il kernel non crea nessun dispositivo di input per la manopola. Questo programma legge i dati grezzi da `hidraw`, li trasforma in azioni (scorrere, volume, zoom…) e mostra un menu e dei messaggi a schermo.

> Provato su: ASUS ProArt StudioBook H5600QM, Ubuntu con GNOME 46, sessione **X11**, manopola `0B05:0220`.
> Altri modelli con lo stesso identificativo dovrebbero funzionare. Non è provato su Wayland (vedi *Limiti*).

## Come si usa

- **Ruoti** la manopola: fa quello che dice la modalità attuale.
- **Clic breve**: l'azione della modalità (play/pausa, muto, zoom 100%, …).
- **Tieni premuto** (o premi e ruota): si apre il **menu circolare**. Ruoti per scegliere la modalità e clicchi per confermare (oppure tieni premuto, ruota e rilascia).
- La modalità scelta viene ricordata anche dopo il riavvio.

## Modalità

| Modalità | Ruotare | Clic |
|---|---|---|
| ↕ **Scorri** | scorre la pagina | clic centrale |
| 🔊 **Volume** | volume | muto |
| ☀ **Luminosità** | luminosità dello schermo | – |
| ⌨ **Tastiera** | retroilluminazione tastiera (livelli 0–3) | spegne / riaccende |
| 🌙 **Luce** | luce notturna (1700–4700 K), si accende da sola | accende / spegne |
| 🔍 **Zoom** | nel browser zoom della pagina; **fuori dal browser zoom dello schermo** (lente di GNOME, fino a 16×) | torna a 100% |
| ▶ **Video** | avanti / indietro di 5 secondi | play / pausa |
| ⏩ **Velocità** | velocità del video da 0,25× a 3× | torna a 1× |
| ⏲ **Timer** | imposta i minuti (1 a scatto fino a 10, poi 5) | avvia / annulla |
| 🗂 **Schede** *(solo browser)* | scheda successiva / precedente | – |
| 🔎 **Trova** *(solo browser)* | risultato successivo / precedente | apre la ricerca nella pagina |
| 🪟 **Finestre** | passa da una finestra all'altra (come Alt+Tab) | conferma / finestra precedente |
| ↔ **Frecce** | tasti freccia sinistra / destra | Invio |
| 🎲 **Dado** | sceglie il dado (d4…d20) | tira, con animazione |
| 🏠 **Casa** | inclina un'immagine (vedi sotto) | – |
| ⏻ **Arresta** | ruotando a lungo in senso orario spegne il PC dopo un conto alla rovescia di 5 secondi | – |

**Modalità che dipendono dal contesto.** *Schede* e *Trova* compaiono nel menu solo quando la finestra attiva è un browser (Firefox, Chrome, Chromium, Brave, Vivaldi, Opera, Edge, LibreWolf, Epiphany, Zen, Floorp, Waterfox, Tor Browser). Fuori dal browser spariscono, e se erano la modalità scelta la manopola si comporta come *Scorri* finché non torni nel browser.

**Timer.** Alla fine suona la sveglia di sistema e un 🍅 gigante si spiaccica sullo schermo per 10 secondi, con una scritta a caso («Timer scaduto!», «Completato!», «Finito!», «BOO!»). Un clic sulla manopola ferma tutto.

**Uovo di Pasqua.** In modalità *Video*, se la finestra attiva è un browser e non c'è nessun video da controllare, il programma apre un famoso video musicale del 1987 nel browser predefinito (al massimo una volta al minuto). Per toglierlo o cambiarlo, modifica `RICKROLL_URL` e `RICKROLL_COOLDOWN_S` in cima al file `asus-dial`.

**Casa.** Mostra un'immagine che si inclina con la manopola. Metti il percorso della tua immagine in `HOUSE_IMAGE` in cima al file `asus-dial`; se il file non c'è, compare solo il messaggio «Immagine non trovata».

## Installazione

### 1. Dipendenze (Ubuntu / Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 \
                 wireplumber x11-utils pulseaudio-utils xdg-utils
```

- `wireplumber` (comando `wpctl`): volume.
- `x11-utils` (comando `xprop`): per capire se la finestra attiva è un browser.
- `pulseaudio-utils` (comando `paplay`): suono del timer.
- `xdg-utils`: apre il browser predefinito.

### 2. Permessi (una volta sola)

Il programma legge la manopola da `/dev/hidraw*` e crea tastiera/mouse virtuali con `/dev/uinput`. Serve il permesso al gruppo `input`:

```bash
sudo cp udev/99-asus-dial.rules /etc/udev/rules.d/
sudo usermod -aG input "$USER"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw
sudo udevadm trigger --name-match=uinput
```

Poi **esci e rientra dalla sessione** (o riavvia) perché il gruppo `input` venga applicato.

### 3. Programma

```bash
mkdir -p ~/.local/bin
cp asus-dial ~/.local/bin/asus-dial
chmod +x ~/.local/bin/asus-dial
```

Per provarlo subito, da terminale: `~/.local/bin/asus-dial`.

### 4. Avvio automatico

```bash
mkdir -p ~/.config/systemd/user
cp systemd/asus-dial.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now asus-dial
```

Controllo e log:

```bash
systemctl --user status asus-dial
journalctl --user -u asus-dial -f
```

Dopo ogni modifica al file: `systemctl --user restart asus-dial`.

## Opzioni

Si danno sulla riga `ExecStart=` del servizio (o da terminale):

| Opzione | Effetto |
|---|---|
| `--invert` | inverte il verso di rotazione |
| `--menu-step N` | quanto ruotare per passare alla voce successiva del menu (predefinito 8) |

## Cosa si può cambiare

Tutto è in cima al file `asus-dial`: nomi e icone delle modalità (`NAMES`, `ICONS`), ordine nel menu (`MENU_ORDER`), tempi (`HOLD_MS`, `TIMER_MAX`, `TOMATO_S`), suono della sveglia (`ALARM_SOUND`), elenco dei browser (`BROWSER_CLASSES`), modalità solo-browser (`BROWSER_ONLY`) e comando di spegnimento (`POWER_CMD`).

## Limiti e cose da sapere

- **Solo X11 per il riconoscimento del browser.** Si usa `xprop`. Su Wayland il programma parte, ma non riconosce il browser, quindi *Schede* e *Trova* non compaiono e lo zoom fuori dal browser è sempre quello dello schermo.
- **Velocità video.** Cambia la velocità tramite MPRIS (il controllo multimediale di sistema). Se il browser non lo permette, il programma passa ai tasti `Shift+<` e `Shift+>` dei lettori tipo YouTube, che funzionano solo se il video è nella pagina attiva e fino a 2×.
- **Luce notturna.** Per vederla subito il programma imposta il programma di GNOME su «tutto il giorno» e salva le tue impostazioni in `~/.config/asus-dial.night.json`. Quando la spegni le rimette com'erano.
- **Zoom dello schermo e luce notturna** usano le impostazioni di GNOME (`org.gnome.desktop.a11y.magnifier`, `org.gnome.settings-daemon.plugins.color`).
- **Retroilluminazione tastiera** usa il demone energia di GNOME; è pensata per la tastiera ASUS con livelli da 0 a 3.
- La modalità *Arresta* **spegne davvero il computer**: ruota in senso orario fino alla barra piena, poi hai 5 secondi per annullare con un clic o ruotando.
- Il programma è provato su un solo portatile. Se la tua manopola ha un identificativo diverso, cambia `HID_ID` in `asus-dial` (lo trovi con `cat /sys/class/hidraw/hidraw*/device/uevent | grep HID_ID`).

## Disinstallare

```bash
systemctl --user disable --now asus-dial
rm ~/.config/systemd/user/asus-dial.service ~/.local/bin/asus-dial
rm -f ~/.config/asus-dial.tool ~/.config/asus-dial.night.json
sudo rm /etc/udev/rules.d/99-asus-dial.rules
```

## Come funziona (in breve)

1. Legge i rapporti di `hidraw` (id 1: byte 1 bit 0 = pulsante, byte 2-3 = rotazione `int16`, circa 8-10 unità per scatto).
2. Trasforma rotazione e clic in eventi con un dispositivo `uinput` virtuale oppure chiama servizi di sistema (`wpctl`, D-Bus/MPRIS, GNOME).
3. Disegna menu, messaggi e animazioni con GTK 3 e Cairo, in finestre trasparenti che non intercettano il mouse.

## Licenza

Da scegliere dall'autore.
