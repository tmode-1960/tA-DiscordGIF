[🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

# tA-DiscordGIF (v2.5)

Ein schlanker Windows-Desktop-Manager für animierte GIFs mit direkter Discord-Integration im **thomo.ART** Dark-UI-Design.

---

## ✨ Funktionen

- **Dark & Light Theme:** Inspiriert von *tA-MusicMaker* – aufgeräumte Seitenleiste, responsives Kachel-Grid und flüssige Animationen.
- **Direktes Einfügen in Discord:**
  - GIF mit einem Klick auswählen.
  - Der Fokus wechselt automatisch zurück zu Discord.
  - Fügt das GIF über die Zwischenablage (`Strg + V`) ein und sendet es auf Wunsch sofort mit `Enter`.
- **Globaler Hotkey (`Alt + G`):**
  - Öffnet den GIF-Selector jederzeit von überall (z. B. direkt aus einem Discord-Chat heraus).
- **Zwei Einfüge-Modi:**
  - **Datei-Upload:** Fügt die echte GIF-Datei ein (ideal für die eigene lokale Sammlung).
  - **Direkt-Link (URL):** Fügt die Web-URL ein (z. B. Tenor/Giphy) und umgeht damit Discords Datei-Größenlimit für Nicht-Nitro-Nutzer.
- **Tags & Live-Suche:** Schnelles Filtern in Echtzeit nach Tags, Titeln und Favoriten.
- **Drag & Drop Import:** Lokale `.gif`-Dateien einfach ins Fenster ziehen oder Web-URLs einfügen.
- **Ordner- & Unterordner-Kategorien:** Unterordner in deinem GIF-Verzeichnis werden automatisch als Kategorie-Tabs angezeigt.
- **Lokales AI GIF Studio (ComfyUI):** Eigene animierte GIFs direkt in der App generieren – unterstützt **MiniMax H3 (Hailuo)**, **LTX-Video** und **SVD-XT**:
  - **Text-Overlay:** Dezenter Text mit Kontur direkt auf generierte GIFs legen (Position: *Oben* / *Unten*; Effekte: *Fade-In*, *Verzögert (~1s)* oder *Statisch*).
  - **Loop-Modi:** *Ping-Pong* (vorwärts + rückwärts) sowie **Reverse-Loop** für nahtlose Schleifen.
  - **AI Studio Remix:** Prompts und Einstellungen bestehender AI-GIFs direkt wieder ins AI Studio laden.
  - **Prompt-Helfer & Kontextmenü:** **Kopieren**- / **Leeren**-Buttons am Prompt-Feld sowie ein eigenes Rechtsklick-Kontextmenü (Ausschneiden, Kopieren, Einfügen, Alles auswählen) im Desktop-Fenster.
  - **Automatische GIF-Erstellung:** Findet `ffmpeg` automatisch (PATH, WinGet oder das in ComfyUI enthaltene `imageio_ffmpeg`) und nutzt **Pillow** als Fallback, falls kein `ffmpeg` installiert ist.
  - **Intelligente Modell-Diagnose:** Erkennt fehlende ComfyUI-Modelle, Dateien im falschen `ComfyUI/models/...`-Ordner sowie lokal vorhandene Modelle, für die ComfyUI noch neu gestartet werden muss.

---

## 🚀 Starten der App

### Option 1: Standalone-Anwendung (Empfohlen für Nutzer)
**Kein Python und keine Installation nötig!**
1. Öffne den Bereich [**Releases**](https://github.com/tmode-1960/tA-DiscordGIF/releases) rechts im Repository.
2. Lade `tA-DiscordGIF.zip` aus dem neuesten Release herunter.
3. Entpacke die ZIP-Datei an einen beliebigen Ort auf deinem PC.
4. Starte `tA-DiscordGIF.exe` per Doppelklick.

> **Hinweis zu Windows SmartScreen:**  
> Da die EXE unabhängig gebaut und nicht mit einem kostenpflichtigen Unternehmens-Zertifikat signiert ist, zeigt Windows ggf. *„Der Computer wurde durch Windows geschützt“*.  
> Klicke einfach auf **„Weitere Informationen“** &rarr; **„Trotzdem ausführen“**.

---

### Option 2: Aus dem Quellcode starten (Für Entwickler)

Voraussetzung: Python 3.10+

```bash
# Repository klonen
git clone https://github.com/tmode-1960/tA-DiscordGIF.git
cd tA-DiscordGIF

# Abhängigkeiten installieren (falls nötig)
pip install -r requirements.txt

# Anwendung starten
start.bat
# oder
python server.py
```

---

## 📖 Benutzerhandbuch & Konfiguration

### 1. Typischer Ablauf im Alltag
1. Öffne Discord und gehe in einen Chat-Kanal oder eine Direktnachricht.
2. Drücke **`Alt + G`** &rarr; **tA-DiscordGIF** öffnet sich über Discord.
3. Klicke auf ein GIF &rarr; die App fokussiert Discord, fügt das GIF ein (`Strg + V`) und sendet es!

---

### 2. Einstellungen (`⚙ Einstellungen`)

Klicke oben rechts auf **`⚙ Einstellungen`**:

| Einstellung | Beschreibung |
| :--- | :--- |
| **Sprache** | Schaltet die Oberfläche zwischen **Deutsch** und **English** um. |
| **Design (Theme)** | Wechselt zwischen **Dunkel (Standard)** und **Hell**. |
| **Standard-Einfügemodus** | Legt fest, ob neue GIFs standardmäßig als **Datei** oder **Link (URL)** eingefügt werden. |
| **GIF-Ordner** *(Kernfunktion)* | **Wähle, wo deine GIFs auf dem PC gespeichert sind:**<br>• **Standard:** Speichert GIFs im internen App-Ordner (`data/gifs`).<br>• **Eigener Ordner:** Über **`📁 Durchsuchen...`** kannst du jeden beliebigen Ordner wählen (z. B. `D:\MeineGIFs`).<br>• **Automatische Kategorie-Tabs:** Enthält dein Ordner Unterordner (z. B. `Memes`, `Reactions`, `Anime`), erstellt **tA-DiscordGIF automatisch Tabs** für jeden Ordner.<br>• **`Zurücksetzen`:** Stellt wieder den Standard-Speicherort ein. |

---

### 3. Übersicht der Bedienelemente

#### Kopfzeile (Header)
* **Discord-Statusanzeige:**  
  * 🟢 **`Discord bereit`**: Discord läuft im Hintergrund; 1-Klick-Einfügen fokussiert Discord automatisch.
  * ⚪ **`Suche Discord...`**: Discord wurde aktuell nicht erkannt oder ist nicht geöffnet.
* **`Alt + G` Badge:** Hinweis auf den globalen Hotkey.
* **`🔄` (Aktualisieren):** Lädt die aktuelle Ansicht neu.
* **`⚙ Einstellungen`:** Öffnet das Einstellungsfenster.

#### Linke Spalte (Steuerung & Import)
* **Quellen-Umschalter:**
  * **`📁 Meine GIFs`:** Zeigt deine lokale Sammlung aus deinem PC-Ordner.
  * **`🌐 Discord / Tenor`:** Durchsucht Live-Kategorien und Online-GIFs von Discord/Tenor in Echtzeit.
  * **`🎬 AI Studio`:** Öffnet den lokalen ComfyUI-GIF-Generator.
* **Suche & Filter:**
  * **`🔍 Suchfeld`:** Sofortiger Live-Filter nach Titel, Tags oder Dateinamen.
  * **`Alle` / `⭐ Favoriten`:** Wechselt zwischen allen GIFs und deinen Favoriten.
* **Discord-Verhalten:**
  * **`Datei`:** Kopiert und lädt die eigentliche Bilddatei hoch (ideal für eigene GIFs).
  * **`Link (URL)`:** Sendet die direkte Web-URL (ideal für größere GIFs über dem Discord-Upload-Limit).
  * **`Sofort mit Enter absenden`:**  
    • *Aktiviert:* Fügt das GIF ein und sendet es direkt ab.  
    • *Deaktiviert:* Fügt das GIF nur ins Textfeld ein, sodass du noch Text dazuschreiben kannst.
* **GIF hinzufügen:**
  * **Dropzone:** `.gif`-Dateien per Drag & Drop aus dem Windows-Explorer ablegen oder per Klick auswählen.
  * **Web-URL:** Direkten GIF-Link (Tenor, Giphy, Imgur usw.) einfügen.
  * **Titel & Tags:** Eigene Suchbegriffe vergeben (z. B. `tanzen, katze, lustig`).
  * **`GIF speichern`:** Speichert das GIF in deiner Sammlung.

#### Rechte Spalte (Galerie)
* **`Ordner neu laden` (`🔄`):**  
  Aktualisiert die Ansicht sofort, wenn du Dateien direkt im Windows-Explorer hinzugefügt, umbenannt oder gelöscht hast.
* **GIF-Karten:**
  * **Klick auf Karte / `⚡ In Discord einfügen`:** Sendet das GIF direkt an Discord.
  * **`⭐` Stern:** Als Favorit markieren.
  * **`✏️` Bearbeiten:** Titel oder Tags anpassen.
  * **`🎬` Remix (bei AI-GIFs):** Lädt Prompt und Einstellungen des GIFs zurück ins AI Studio.
  * **`🗑️` Löschen:** Öffnet einen Bestätigungsdialog zum sicheren Löschen.
  * **`📥 In Ordner speichern` (im Tenor-Modus):** Lädt ein Online-GIF direkt in deine lokale Sammlung herunter.

---

## 🎬 AI-GIF-Generierung & Voraussetzungen (MiniMax H3)

tA-DiscordGIF enthält einen integrierten AI-Videogenerator auf Basis deiner lokalen **ComfyUI**-Installation.

### ✨ Unterstützte Modelle
* **MiniMax H3 (Hailuo) • Ultra Action & Character:**  
  Spezialisiert auf realistische menschliche Bewegungen, Mimik und dynamische Aktionen (Essen, Trinken, Sprechen, Lachen usw.) in nur **8 Steps**.
* **LTX-Video:** Sehr schnelle Text-/Image-to-Video-Generierung in hoher Auflösung.
* **SVD-XT (Stable Video Diffusion):** Konsistente, sanfte Bewegungserzeugung aus Standbildern.

---

### ⚙️ Voraussetzungen für AI-Generierung

> [!NOTE]  
> Alle normalen GIF-Manager-Funktionen (Suche, Sammlung, `Alt + G` Discord-Einfügen) benötigen **kein** ComfyUI und laufen komplett eigenständig! Die folgenden Punkte gelten nur für die lokale AI-Generierung.

1. **Lokales ComfyUI:**  
   * ComfyUI läuft lokal (Standard-Endpunkt: `http://127.0.0.1:8188`).
2. **Hardware / GPU:**  
   * NVIDIA-GPU mit **8 GB bis 24 GB VRAM**.
   * Dank INT8-Quantisierung läuft MiniMax H3 auch auf Mittelklasse-GPUs (8–12 GB VRAM) flüssig.
3. **Modelldateien für MiniMax H3:**  
   Lade die folgenden `.safetensors`-Dateien herunter (oder nutze den integrierten Downloader im AI Studio) und lege sie in den jeweiligen ComfyUI-Ordnern ab:
   * **Diffusion Model** (`ComfyUI/models/diffusion_models/`):  
     `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (~14,5 GB)  
     *(Alternative: `fastvideo_fasth3_8step_v2_pruned_int8_convrot.safetensors`)*
   * **Text Encoder** (`ComfyUI/models/text_encoders/`):  
     `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (~15,7 GB)  
     *(Alternative: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`)*
   * **Video VAE** (`ComfyUI/models/vae/`):  
     `minimax_h3_video_vae_fp16.safetensors` (~400 MB)

### 🚀 So generierst du ein AI-GIF
1. Starte ComfyUI auf deinem PC.
2. Öffne in **tA-DiscordGIF** den Tab **AI Studio**.
3. Wähle einen Workflow (z. B. **MiniMax H3**) und prüfe, ob alle Modelle als **Installiert** angezeigt werden (bei falschem Unterordner oder nötigem ComfyUI-Neustart erscheint automatisch ein entsprechender Hinweis).
4. Gib deinen Bewegungs-Prompt ein (nutze bei Bedarf die Buttons **Kopieren** / **Leeren** oder die Schnell-Ideen) oder lade ein Startbild hoch, stelle Frames/FPS/Loop-Modus (**Ping-Pong** oder **Reverse**) ein und aktiviere optional **Text-Overlay hinzufügen** (*Oben* / *Unten*, *Fade-In* / *Verzögert (~1s)* / *Statisch*).
5. Klicke auf **Generieren**. Nach Abschluss wird das GIF automatisch erstellt und deiner Sammlung hinzugefügt – sofort einsatzbereit mit **`Alt + G`**!

---

## ⌨️ Tastenkürzel

| Tastenkürzel | Aktion |
| :--- | :--- |
| **`Alt + G`** | Globaler Hotkey: GIF-Selector öffnen / minimieren |
| **`Escape`** | GIF-Selector schließen oder minimieren |
| **`Enter`** | Ausgewähltes GIF an Discord senden |

---

## 📜 Credits & Lizenz

Erstellt von **thomo.ART**.  
Besonderer Dank an **CodexMundi** für Testing und Support.  
Veröffentlicht unter der MIT-Lizenz.
