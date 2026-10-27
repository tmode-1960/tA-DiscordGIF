# tA-DiscordGIF (v1.2)

A lightweight Windows desktop manager for animated GIFs with instant Discord integration, featuring the signature **thomo.ART** dark UI.

---

## ✨ Features

- **Sleek Dark Theme:** Inspired by the *tA-MusicMaker* interface — clean sidebar, responsive card grid, and fluid animations.
- **Direct Discord Insertion:**
  - Select any GIF with a single click.
  - Automatically restores focus to Discord.
  - Pastes the GIF via clipboard (`Ctrl + V`) and optionally sends it immediately with `Enter`.
- **Global Hotkey (`Alt + G`):**
  - Press `Alt + G` from anywhere (e.g. while chatting in Discord) to bring up your GIF selector instantly.
- **Two Insertion Modes:**
  - **File Upload:** Pastes the actual GIF image file (ideal for your personal collection).
  - **Direct URL:** Pastes the web URL (e.g., Tenor/Giphy), bypassing Discord's non-Nitro file upload size limits.
- **Tagging & Live Search:** Quick real-time filtering by tags, titles, and favorites.
- **Drag & Drop Import:** Easily drop local GIF files into the app or paste web URLs.

---

## 🚀 How to Run

### Option 1: Standalone Application (Recommended for Users)
**No Python or installation required!**
1. Go to the [**Releases**](https://github.com/tmode-1960/tA-DiscordGIF/releases) section on the right side of this repository.
2. Download `tA-DiscordGIF-v1.2.zip`.
3. Extract the ZIP and double-click `tA-DiscordGIF.exe` to run.

> **Windows SmartScreen Note:**  
> Because this executable is built independently and not signed with an enterprise certificate, Windows may show *"Windows protected your PC"*.  
> Simply click **"More info"** &rarr; **"Run anyway"**.

---

### Option 2: Running from Source (For Developers)

Requirements: Python 3.10+

```bash
# Clone the repository
git clone https://github.com/tmode-1960/tA-DiscordGIF.git
cd tA-DiscordGIF

# Install dependencies (if needed)
pip install -r requirements.txt  # or run server.py directly

# Start the application
start.bat
# or
python server.py
```

---

## ⌨️ Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Alt + G` | Toggle / focus the GIF manager window |
| `Escape` | Minimize / close the GIF manager |
| `Enter` | Send selected GIF to Discord |
