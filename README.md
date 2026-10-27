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
- **Folder & Subfolder Categorization:** Automatically turns subfolders in your GIF directory into category tabs.

---

## 🚀 How to Run

### Option 1: Standalone Application (Recommended for Users)
**No Python or installation required!**
1. Go to the [**Releases**](https://github.com/tmode-1960/tA-DiscordGIF/releases) section on the right side of this repository.
2. Download `tA-DiscordGIF-v1.2.zip`.
3. Extract the ZIP to any location on your PC.
4. Double-click `tA-DiscordGIF.exe` to run.

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
pip install -r requirements.txt

# Start the application
start.bat
# or
python server.py
```

---

## 📖 User Guide & Configuration

### 1. Typical Daily Workflow
1. Open Discord and enter any chat channel or direct message.
2. Press **`Alt + G`** on your keyboard &rarr; the **tA-DiscordGIF** selector opens over Discord.
3. Click any GIF card &rarr; the app focuses Discord, pastes the GIF (`Ctrl + V`), and sends it!

---

### 2. Settings Configuration (`⚙ Settings`)

Click the **`⚙ Settings`** button in the top-right header:

| Setting | Description |
| :--- | :--- |
| **Language** | Switch the UI between **English** and **Deutsch**. |
| **Theme** | Switch between **Dark (Default)** and **Light**. |
| **Default Paste Mode** | Select whether new GIFs default to **File** or **Link (URL)**. |
| **GIF Directory** *(Key Feature)* | **Choose where your GIFs are stored on your computer:**<br>• **Default:** Leaves GIFs inside the app's internal folder (`data/gifs`).<br>• **Custom Folder:** Click **`📁 Browse...`** to select any folder on your hard drive (e.g. `D:\MyGIFs` or `C:\Users\YourName\Pictures\GIFs`).<br>• **Automatic Category Tabs:** If your folder contains subfolders (e.g., `Memes`, `Reactions`, `Anime`), **tA-DiscordGIF automatically creates tabs** at the top for each folder!<br>• **`Reset` Button:** Reverts the directory back to the app's default storage. |

---

### 3. Controls & Buttons Breakdown

#### Header Bar
* **Discord Status Indicator:**  
  * 🟢 **`Discord ready`**: Discord was detected running in the background. 1-click paste will seamlessly focus Discord.
  * ⚪ **`Looking for Discord...`**: Discord is currently not detected or not open.
* **`Alt + G` Badge:** Visual reminder of your global summon shortcut.
* **`🔄` (Refresh):** Quick-reloads the current view.
* **`⚙ Settings`:** Opens the settings modal.

#### Left Column (Controls & Import)
* **Source Switcher:**
  * **`📁 Local GIFs` (Meine GIFs):** Displays your offline collection from your local PC folder.
  * **`🌐 Discord / Tenor`:** Lets you browse live Discord/Tenor trending categories and search online GIFs in real time.
* **Search & Filters:**
  * **`🔍 Search input`:** Fast live filter by name, tag, or filename.
  * **`All` / `⭐ Favorites`:** Toggle between all GIFs and your starred favorites.
* **Discord Behavior:**
  * **`File`:** Copies and uploads the raw image file. Best for personal GIFs.
  * **`Link (URL)`:** Sends the direct web URL. Perfect for larger GIFs to bypass Discord's upload limit (8 MB / 25 MB).
  * **`Auto-send with Enter immediately` Checkbox:**  
    • *Enabled:* Pastes and sends instantly.  
    • *Disabled:* Pastes the GIF into Discord's text box, allowing you to type a message before pressing Enter yourself.
* **Add GIF:**
  * **Dropzone:** Drag and drop `.gif` files directly from Windows Explorer, or click to browse.
  * **Web URL:** Paste any direct GIF link (Tenor, Giphy, Imgur, etc.).
  * **Title & Tags:** Assign custom search tags (e.g. `dance, cat, funny`) for instant retrieval.
  * **`Save GIF`:** Stores the GIF into your collection.

#### Right Column (Gallery)
* **`Reload Folder` (`🔄`):**  
  Click this button whenever you add, rename, or delete GIF files directly in Windows Explorer to refresh your collection immediately.
* **GIF Cards:**
  * **Click Card / `⚡ In Discord einfügen`:** Automatically pastes the GIF into Discord.
  * **`⭐` Star:** Marks the GIF as a favorite.
  * **`✏️` Edit:** Opens a dialog to edit the title or tags.
  * **`🗑️` Delete:** Deletes the GIF.
  * **`📥 Save to Folder` (in Tenor mode):** Downloads an online Tenor GIF directly to your local PC collection!

---

## ⌨️ Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Alt + G`** | Global hotkey: summon / minimize the GIF selector |
| **`Escape`** | Close or minimize the GIF selector |
| **`Enter`** | Send selected GIF to Discord |

---

## 📜 Credits & License

Created by **thomo.ART**.  
Special thanks to **CodexMundi** for testing and support.  
Released under the MIT License.
