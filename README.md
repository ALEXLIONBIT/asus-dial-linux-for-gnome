# ASUS Dial Linux for GNOME

**English** · [Español](#español) · [Italiano](#italiano)

---

# English

Unofficial driver for the **ASUS Dial** knob (found on ProArt StudioBook laptops) on Linux with GNOME, with an on-screen radial menu and 18 modes.

The kernel creates no input device for the dial. This program reads the raw data from `hidraw`, turns it into actions (scroll, volume, zoom…) and shows a menu and messages on screen.

> Tested on: ASUS ProArt StudioBook H5600QM, Ubuntu with GNOME 46, **X11** session, dial `0B05:0220`.
> Other models with the same ID should work. Not tested on Wayland (see *Limitations*).

## How to use it

- **Rotate** the dial: does what the current mode says.
- **Short click**: the mode's action (play/pause, mute, zoom 100%, …).
- **Long press** (or press and rotate): opens the **radial menu**. Rotate to pick a mode and click to confirm (or hold, rotate and release).
- The chosen mode is remembered after a reboot.

## Modes

| Mode | Rotate | Click |
|---|---|---|
| ↕ **Scroll** | scrolls the page | middle click |
| 🔊 **Volume** | volume | mute |
| ☀ **Brightness** | screen brightness | – |
| ⌨ **Keyboard** | keyboard backlight (levels 0–3) | off / back on |
| 🌙 **Night light** | night light (1700–4700 K), turns on by itself | on / off |
| 🔍 **Zoom** | in a browser: page zoom; **outside a browser: screen zoom** (GNOME magnifier, up to 16×) | back to 100% |
| ▶ **Video** | seek ±5 seconds | play / pause |
| ⏩ **Speed** | video speed from 0.25× to 3× | back to 1× |
| ⏲ **Timer** | sets the minutes (1 per step up to 10, then 5) | start / cancel |
| 🗂 **Tabs** *(browser only)* | next / previous tab | – |
| 🔎 **Find** *(browser only)* | next / previous search result | opens find-in-page |
| 🪟 **Windows** | switches between windows (like Alt+Tab) | confirm / previous window |
| ↔ **Arrows** | left / right arrow keys | Enter |
| 🎲 **Dice** | picks the die (d4…d20) | rolls it, with an animation |
| 🏠 **House** | tilts a picture (see below) | – |
| ✨ **Rickroll** | – | a divine light show, then your default browser opens the video full screen |
| 🌐 **Language** | cycles English → Español → Italiano (default: English) | shows the current language |
| ⏻ **Power off** | keep rotating clockwise to arm a 5-second shutdown countdown | – |

**Context-aware modes.** *Tabs* and *Find* show up in the menu only while the active window is a browser (Firefox, Chrome, Chromium, Brave, Vivaldi, Opera, Edge, LibreWolf, Epiphany, Zen, Floorp, Waterfox, Tor Browser). Outside a browser they disappear, and if one of them was your chosen mode the dial behaves like *Scroll* until you are back in the browser.

**Timer.** When time is up the system alarm sound plays and a giant 🍅 splats on your screen for 10 seconds, with a random message ("Timer expired!", "Completed!", "Finished!" or "BOO!", in the chosen language). Click the dial to stop it.

**Rickroll.** Click the dial in this mode: the screen dims, golden rays and sparkles fill it with heavenly light, the lyrics appear and, in a blinding white flash, your default browser opens a famous 1987 music video and puts it **full screen** (it presses `K` if autoplay was blocked, then `F`, so it needs a YouTube page; press `Esc` to leave). Change the video by editing `RICKROLL_URL` at the top of the `asus-dial` file.

**Language.** Menu, messages and timer texts are in **English by default**. The *Language* mode switches between English, Spanish and Italian; the choice is saved in `~/.config/asus-dial.lang`. To add a language, add it to `LANGS`, `LANG_NAMES`, `NAMES_L`, `TIMER_MESSAGES_L` and add a column to every entry of `STR` in the `asus-dial` file.

**House.** Shows a picture that tilts as you rotate. Set the path of your own image in `HOUSE_IMAGE` at the top of the `asus-dial` file; if the file is missing you just get an "image not found" message.

## Installation

### 1. Dependencies (Ubuntu / Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 \
                 wireplumber x11-utils pulseaudio-utils xdg-utils
```

- `wireplumber` (the `wpctl` command): volume.
- `x11-utils` (the `xprop` command): to tell whether the active window is a browser.
- `pulseaudio-utils` (the `paplay` command): timer sound.
- `xdg-utils`: opens the default browser.

### 2. Permissions (once)

The program reads the dial from `/dev/hidraw*` and creates virtual keyboard/mouse events through `/dev/uinput`. The `input` group needs access:

```bash
sudo cp udev/99-asus-dial.rules /etc/udev/rules.d/
sudo usermod -aG input "$USER"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw
sudo udevadm trigger --name-match=uinput
```

Then **log out and back in** (or reboot) so the `input` group takes effect.

### 3. The program

```bash
mkdir -p ~/.local/bin
cp asus-dial ~/.local/bin/asus-dial
chmod +x ~/.local/bin/asus-dial
```

To try it right away, from a terminal: `~/.local/bin/asus-dial`.

### 4. Start at login

```bash
mkdir -p ~/.config/systemd/user
cp systemd/asus-dial.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now asus-dial
```

Status and logs:

```bash
systemctl --user status asus-dial
journalctl --user -u asus-dial -f
```

After every change to the file: `systemctl --user restart asus-dial`.

## Options

Put them on the `ExecStart=` line of the service (or on the command line):

| Option | Effect |
|---|---|
| `--invert` | reverses the rotation direction |
| `--menu-step N` | how far to rotate to move to the next menu item (default 8) |

## What you can change

Everything is at the top of the `asus-dial` file: mode names and icons (`NAMES`, `ICONS`), menu order (`MENU_ORDER`), timings (`HOLD_MS`, `TIMER_MAX`, `TOMATO_S`), alarm sound (`ALARM_SOUND`), browser list (`BROWSER_CLASSES`), browser-only modes (`BROWSER_ONLY`) and the shutdown command (`POWER_CMD`).

## Limitations and things to know

- **Browser detection is X11 only.** It uses `xprop`. On Wayland the program starts, but it cannot recognise the browser, so *Tabs* and *Find* never show up and zoom outside the browser is always screen zoom.
- **Video speed.** It changes the speed through MPRIS (the system media-control interface). If the browser does not allow that, the program falls back to the `Shift+<` and `Shift+>` keys of YouTube-style players, which only work if the video is in the active page, up to 2×.
- **Night light.** To make it visible at once, the program sets GNOME's schedule to "all day" and saves your own settings in `~/.config/asus-dial.night.json`. When you turn it off it puts them back.
- **Screen zoom and night light** use GNOME settings (`org.gnome.desktop.a11y.magnifier`, `org.gnome.settings-daemon.plugins.color`).
- **Keyboard backlight** uses GNOME's power daemon; it is meant for the ASUS keyboard with levels 0 to 3.
- *Power off* **really shuts the computer down**: rotate clockwise until the bar is full, then you have 5 seconds to cancel with a click or by rotating.
- It has been tested on a single laptop. If your dial has a different ID, change `HID_ID` in `asus-dial` (find it with `cat /sys/class/hidraw/hidraw*/device/uevent | grep HID_ID`).

## Uninstall

```bash
systemctl --user disable --now asus-dial
rm ~/.config/systemd/user/asus-dial.service ~/.local/bin/asus-dial
rm -f ~/.config/asus-dial.tool ~/.config/asus-dial.night.json ~/.config/asus-dial.lang
sudo rm /etc/udev/rules.d/99-asus-dial.rules
```

## How it works (in short)

1. It reads `hidraw` reports (id 1: byte 1 bit 0 = button, bytes 2–3 = `int16` rotation, about 8–10 units per detent).
2. It turns rotation and clicks into events through a virtual `uinput` device, or calls system services (`wpctl`, D-Bus/MPRIS, GNOME).
3. It draws the menu, messages and animations with GTK 3 and Cairo, in transparent windows that let mouse clicks through.

## License

To be chosen by the author.

---

# Español

Controlador no oficial para la rueda **ASUS Dial** (la de los portátiles ProArt StudioBook) en Linux con GNOME, con un menú circular en pantalla y 18 modos.

El kernel no crea ningún dispositivo de entrada para la rueda. Este programa lee los datos en bruto de `hidraw`, los convierte en acciones (desplazar, volumen, zoom…) y muestra un menú y mensajes en pantalla.

> Probado en: ASUS ProArt StudioBook H5600QM, Ubuntu con GNOME 46, sesión **X11**, rueda `0B05:0220`.
> Otros modelos con el mismo identificador deberían funcionar. No probado en Wayland (ver *Limitaciones*).

## Cómo se usa

- **Girar** la rueda: hace lo que indica el modo actual.
- **Clic corto**: la acción del modo (reproducir/pausa, silenciar, zoom al 100 %, …).
- **Pulsación larga** (o pulsar y girar): abre el **menú circular**. Gira para elegir un modo y haz clic para confirmar (o mantén pulsado, gira y suelta).
- El modo elegido se recuerda después de reiniciar.

## Modos

| Modo | Girar | Clic |
|---|---|---|
| ↕ **Desplazar** | desplaza la página | clic central |
| 🔊 **Volumen** | volumen | silenciar |
| ☀ **Brillo** | brillo de la pantalla | – |
| ⌨ **Teclado** | retroiluminación del teclado (niveles 0–3) | apaga / vuelve a encender |
| 🌙 **Luz nocturna** | luz nocturna (1700–4700 K), se enciende sola | enciende / apaga |
| 🔍 **Zoom** | en el navegador: zoom de la página; **fuera del navegador: zoom de pantalla** (lupa de GNOME, hasta 16×) | vuelve al 100 % |
| ▶ **Vídeo** | avanza / retrocede 5 segundos | reproducir / pausa |
| ⏩ **Velocidad** | velocidad del vídeo de 0,25× a 3× | vuelve a 1× |
| ⏲ **Temporizador** | fija los minutos (1 por paso hasta 10, luego 5) | iniciar / cancelar |
| 🗂 **Pestañas** *(solo navegador)* | pestaña siguiente / anterior | – |
| 🔎 **Buscar** *(solo navegador)* | resultado siguiente / anterior | abre la búsqueda en la página |
| 🪟 **Ventanas** | cambia entre ventanas (como Alt+Tab) | confirmar / ventana anterior |
| ↔ **Flechas** | teclas de flecha izquierda / derecha | Intro |
| 🎲 **Dado** | elige el dado (d4…d20) | lo tira, con animación |
| 🏠 **Casa** | inclina una imagen (ver abajo) | – |
| ✨ **Rickroll** | – | un espectáculo de luz divina y luego tu navegador predeterminado abre el vídeo a pantalla completa |
| 🌐 **Idioma** | cambia entre English → Español → Italiano (por defecto: English) | muestra el idioma actual |
| ⏻ **Apagar** | sigue girando en sentido horario para activar una cuenta atrás de 5 segundos | – |

**Modos según el contexto.** *Pestañas* y *Buscar* aparecen en el menú solo cuando la ventana activa es un navegador (Firefox, Chrome, Chromium, Brave, Vivaldi, Opera, Edge, LibreWolf, Epiphany, Zen, Floorp, Waterfox, Tor Browser). Fuera del navegador desaparecen, y si uno de ellos era el modo elegido, la rueda se comporta como *Desplazar* hasta que vuelvas al navegador.

**Temporizador.** Al terminar el tiempo suena la alarma del sistema y un 🍅 gigante se estrella contra la pantalla durante 10 segundos, con un mensaje al azar («¡Temporizador agotado!», «¡Completado!», «¡Terminado!» o «¡BU!», en el idioma elegido). Un clic en la rueda lo detiene.

**Rickroll.** Haz clic en la rueda en este modo: la pantalla se oscurece, rayos dorados y destellos la llenan de luz celestial, aparece la letra y, con un destello blanco cegador, tu navegador predeterminado abre un famoso videoclip de 1987 y lo pone a **pantalla completa** (pulsa `K` si la reproducción automática estaba bloqueada y luego `F`, así que necesita una página de YouTube; pulsa `Esc` para salir). Para cambiar el vídeo, edita `RICKROLL_URL` al principio del archivo `asus-dial`.

**Idioma.** El menú, los mensajes y los textos del temporizador están en **inglés por defecto**. El modo *Idioma* cambia entre inglés, español e italiano; la elección se guarda en `~/.config/asus-dial.lang`. Para añadir un idioma, añádelo a `LANGS`, `LANG_NAMES`, `NAMES_L`, `TIMER_MESSAGES_L` y añade una columna a cada entrada de `STR` en el archivo `asus-dial`.

**Casa.** Muestra una imagen que se inclina al girar. Pon la ruta de tu propia imagen en `HOUSE_IMAGE`, al principio del archivo `asus-dial`; si el archivo no existe solo verás el mensaje «imagen no encontrada».

## Instalación

### 1. Dependencias (Ubuntu / Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 \
                 wireplumber x11-utils pulseaudio-utils xdg-utils
```

- `wireplumber` (comando `wpctl`): volumen.
- `x11-utils` (comando `xprop`): para saber si la ventana activa es un navegador.
- `pulseaudio-utils` (comando `paplay`): sonido del temporizador.
- `xdg-utils`: abre el navegador predeterminado.

### 2. Permisos (una sola vez)

El programa lee la rueda desde `/dev/hidraw*` y crea eventos virtuales de teclado/ratón con `/dev/uinput`. El grupo `input` necesita acceso:

```bash
sudo cp udev/99-asus-dial.rules /etc/udev/rules.d/
sudo usermod -aG input "$USER"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw
sudo udevadm trigger --name-match=uinput
```

Después **cierra la sesión y vuelve a entrar** (o reinicia) para que se aplique el grupo `input`.

### 3. El programa

```bash
mkdir -p ~/.local/bin
cp asus-dial ~/.local/bin/asus-dial
chmod +x ~/.local/bin/asus-dial
```

Para probarlo enseguida, desde una terminal: `~/.local/bin/asus-dial`.

### 4. Inicio automático

```bash
mkdir -p ~/.config/systemd/user
cp systemd/asus-dial.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now asus-dial
```

Estado y registros:

```bash
systemctl --user status asus-dial
journalctl --user -u asus-dial -f
```

Tras cada cambio en el archivo: `systemctl --user restart asus-dial`.

## Opciones

Se ponen en la línea `ExecStart=` del servicio (o en la terminal):

| Opción | Efecto |
|---|---|
| `--invert` | invierte el sentido de giro |
| `--menu-step N` | cuánto hay que girar para pasar al siguiente elemento del menú (por defecto 8) |

## Qué se puede cambiar

Todo está al principio del archivo `asus-dial`: nombres e iconos de los modos (`NAMES`, `ICONS`), orden del menú (`MENU_ORDER`), tiempos (`HOLD_MS`, `TIMER_MAX`, `TOMATO_S`), sonido de la alarma (`ALARM_SOUND`), lista de navegadores (`BROWSER_CLASSES`), modos solo para navegador (`BROWSER_ONLY`) y el comando de apagado (`POWER_CMD`).

## Limitaciones y cosas que conviene saber

- **La detección del navegador solo funciona en X11.** Usa `xprop`. En Wayland el programa arranca, pero no reconoce el navegador: *Pestañas* y *Buscar* nunca aparecen y el zoom fuera del navegador es siempre el de pantalla.
- **Velocidad de vídeo.** Cambia la velocidad mediante MPRIS (la interfaz de control multimedia del sistema). Si el navegador no lo permite, el programa recurre a las teclas `Mayús+<` y `Mayús+>` de los reproductores tipo YouTube, que solo funcionan si el vídeo está en la página activa y hasta 2×.
- **Luz nocturna.** Para que se vea al instante, el programa pone el horario de GNOME en «todo el día» y guarda tu configuración en `~/.config/asus-dial.night.json`. Al apagarla la restaura.
- **El zoom de pantalla y la luz nocturna** usan ajustes de GNOME (`org.gnome.desktop.a11y.magnifier`, `org.gnome.settings-daemon.plugins.color`).
- **La retroiluminación del teclado** usa el demonio de energía de GNOME; está pensada para el teclado ASUS con niveles de 0 a 3.
- *Apagar* **apaga el ordenador de verdad**: gira en sentido horario hasta llenar la barra y tendrás 5 segundos para cancelar con un clic o girando.
- Solo se ha probado en un portátil. Si tu rueda tiene otro identificador, cambia `HID_ID` en `asus-dial` (lo encuentras con `cat /sys/class/hidraw/hidraw*/device/uevent | grep HID_ID`).

## Desinstalar

```bash
systemctl --user disable --now asus-dial
rm ~/.config/systemd/user/asus-dial.service ~/.local/bin/asus-dial
rm -f ~/.config/asus-dial.tool ~/.config/asus-dial.night.json ~/.config/asus-dial.lang
sudo rm /etc/udev/rules.d/99-asus-dial.rules
```

## Cómo funciona (resumen)

1. Lee los informes de `hidraw` (id 1: byte 1 bit 0 = botón, bytes 2–3 = rotación `int16`, unas 8–10 unidades por paso).
2. Convierte el giro y los clics en eventos con un dispositivo `uinput` virtual, o llama a servicios del sistema (`wpctl`, D-Bus/MPRIS, GNOME).
3. Dibuja el menú, los mensajes y las animaciones con GTK 3 y Cairo, en ventanas transparentes que dejan pasar los clics del ratón.

## Licencia

Por elegir por el autor.

---

# Italiano

Driver non ufficiale per la **manopola ASUS Dial** (quella dei portatili ProArt StudioBook) su Linux con GNOME, con un menu circolare a schermo e 18 modalità.

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
| ✨ **Rickroll** | – | uno spettacolo di luce divina, poi il browser predefinito apre il video a schermo intero |
| 🌐 **Lingua** | passa da English → Español → Italiano (predefinita: English) | mostra la lingua attuale |
| ⏻ **Arresta** | ruotando a lungo in senso orario spegne il PC dopo un conto alla rovescia di 5 secondi | – |

**Modalità che dipendono dal contesto.** *Schede* e *Trova* compaiono nel menu solo quando la finestra attiva è un browser (Firefox, Chrome, Chromium, Brave, Vivaldi, Opera, Edge, LibreWolf, Epiphany, Zen, Floorp, Waterfox, Tor Browser). Fuori dal browser spariscono, e se erano la modalità scelta la manopola si comporta come *Scorri* finché non torni nel browser.

**Timer.** Alla fine suona la sveglia di sistema e un 🍅 gigante si spiaccica sullo schermo per 10 secondi, con una scritta a caso («Timer scaduto!», «Completato!», «Finito!», «BOO!», nella lingua scelta). Un clic sulla manopola ferma tutto.

**Rickroll.** Clicca la manopola in questa modalità: lo schermo si oscura, raggi dorati e scintille lo riempiono di luce divina, compare il testo della canzone e, con un lampo bianco accecante, il browser predefinito apre un famoso video musicale del 1987 e lo mette a **schermo intero** (preme `K` se la riproduzione automatica era bloccata, poi `F`, quindi serve una pagina di YouTube; premi `Esc` per uscire). Per cambiare il video modifica `RICKROLL_URL` in cima al file `asus-dial`.

**Lingua.** Menu, messaggi e testi del timer sono in **inglese per impostazione predefinita**. La modalità *Lingua* passa tra inglese, spagnolo e italiano; la scelta viene salvata in `~/.config/asus-dial.lang`. Per aggiungere una lingua, aggiungila a `LANGS`, `LANG_NAMES`, `NAMES_L`, `TIMER_MESSAGES_L` e aggiungi una colonna a ogni voce di `STR` nel file `asus-dial`.

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
rm -f ~/.config/asus-dial.tool ~/.config/asus-dial.night.json ~/.config/asus-dial.lang
sudo rm /etc/udev/rules.d/99-asus-dial.rules
```

## Come funziona (in breve)

1. Legge i rapporti di `hidraw` (id 1: byte 1 bit 0 = pulsante, byte 2-3 = rotazione `int16`, circa 8-10 unità per scatto).
2. Trasforma rotazione e clic in eventi con un dispositivo `uinput` virtuale oppure chiama servizi di sistema (`wpctl`, D-Bus/MPRIS, GNOME).
3. Disegna menu, messaggi e animazioni con GTK 3 e Cairo, in finestre trasparenti che non intercettano il mouse.

## Licenza

Da scegliere dall'autore.
