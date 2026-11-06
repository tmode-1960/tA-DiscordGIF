"""tA-DiscordGIF - A lightweight desktop animated GIF manager and Discord inserter.
Designed in the thomo.ART aesthetic (tA-MusicMaker).

Usage:
    python server.py [--no-window] [--port 8769]
"""

from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_VERSION = "1.7"
IS_FROZEN = getattr(sys, "frozen", False)
BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(os.path.abspath(sys.executable)) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BUNDLE_DIR, "web") if os.path.isdir(os.path.join(BUNDLE_DIR, "web")) else os.path.join(APP_DIR, "web")
WORKFLOWS_DIR = os.path.join(BUNDLE_DIR, "workflows") if os.path.isdir(os.path.join(BUNDLE_DIR, "workflows")) else os.path.join(APP_DIR, "workflows")


def _resolve_data_dir() -> str:
    local_data = os.path.join(APP_DIR, "data")
    try:
        os.makedirs(os.path.join(local_data, "gifs"), exist_ok=True)
        probe = os.path.join(local_data, ".write_test")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("ok")
        os.remove(probe)
        return local_data
    except OSError:
        appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        fallback = os.path.join(appdata, "tA-DiscordGIF", "data")
        os.makedirs(os.path.join(fallback, "gifs"), exist_ok=True)
        return fallback

DATA_DIR = _resolve_data_dir()
GIFS_DIR = os.path.join(DATA_DIR, "gifs")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
LIBRARY_PATH = os.path.join(DATA_DIR, "library.json")

if sys.stdout is None or sys.stderr is None:
    try:
        _log_fh = open(os.path.join(DATA_DIR, "app.log"), "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = _log_fh
        if sys.stderr is None:
            sys.stderr = _log_fh
    except Exception:
        pass

os.makedirs(GIFS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Windows Win32 API Definitions (ctypes)
# ---------------------------------------------------------------------------
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]

CF_UNICODETEXT = 13
CF_HDROP = 15
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

VK_CONTROL = 0x11
VK_V = 0x56
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002

class DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("fNC", wintypes.BOOL),
        ("fWide", wintypes.BOOL),
    ]

# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
LAST_TARGET_HWND: int | None = None
OUR_WINDOW_HWND: int | None = None
HOTKEY_REGISTERED = False
LAST_PING: float = time.time()
HAD_FIRST_PING: bool = False

def record_ping():
    global LAST_PING, HAD_FIRST_PING
    LAST_PING = time.time()
    HAD_FIRST_PING = True

def watchdog():
    """Terminate the process when the window was closed (no ping received)."""
    start_time = time.time()
    while True:
        time.sleep(2)
        now = time.time()
        if HAD_FIRST_PING:
            if now - LAST_PING > 5:
                os._exit(0)
        else:
            # If after 25 seconds no initial ping arrived, assume startup aborted
            if now - start_time > 25:
                os._exit(0)

def try_terminate_previous_instance(port: int = 8769):
    """If a previous instance is lingering on the port, request clean shutdown."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/shutdown",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
        time.sleep(0.6)
    except Exception:
        pass

ACTIVE_WEBVIEW_WINDOW = None

DEFAULT_CONFIG = {
    "port": 8769,
    "theme": "dark",
    "language": "en",
    "auto_send": False,
    "paste_mode": "file",  # "file" or "url"
    "hotkey": "Alt+G",
    "gif_dir": "",
    "tenor_api_key": "",
    "comfyui_url": "http://127.0.0.1:8188",
    "comfyui_dir": "",
    "ai_workflow": "svd_xt",
    "ai_fps": 12,
    "ai_motion_bucket": 100,
    "ai_loop_mode": "pingpong",
}

CUSTOM_GIF_INDEX: dict[str, dict] = {}
TENOR_CACHE: dict[str, dict] = {}

def fetch_tenor_gifs(query: str = "", limit: int = 36) -> list[dict]:
    """Fetch online GIFs from Tenor (the engine powering Discord GIF picker).
    Scrapes public search/trending results directly from tenor.com so no API key is required.
    Falls back to official API if an explicit key is configured.
    """
    global TENOR_CACHE
    cfg = load_config()
    api_key = cfg.get("tenor_api_key", "").strip()

    # 1. Public web scraper (no API key required, zero risk, matches Discord picker)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        ssl_ctx = ssl.create_default_context()
    except Exception:
        ssl_ctx = ssl._create_unverified_context()

    q_clean = query.strip()
    if not q_clean or q_clean.lower() in ("trending", "featured", "all"):
        urls = [
            "https://tenor.com/search/trending-gifs",
            "https://tenor.com/",
        ]
    else:
        # replace spaces and punctuation with dashes
        slug = re.sub(r"[\s_]+", "-", q_clean.lower())
        encoded_slug = urllib.parse.quote(slug)
        urls = [
            f"https://tenor.com/search/{encoded_slug}-gifs",
            f"https://tenor.com/search/{encoded_slug}",
        ]

    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            content = ""
            try:
                with urllib.request.urlopen(req, timeout=6, context=ssl_ctx) as resp:
                    content = resp.read().decode("utf-8", "ignore")
            except Exception:
                # Retry with unverified SSL context if root certificates differ
                with urllib.request.urlopen(req, timeout=6, context=ssl._create_unverified_context()) as resp:
                    content = resp.read().decode("utf-8", "ignore")

            if not content:
                continue

            matches = re.findall(
                r'<img[^>]+src=["\'](https://media[0-9]*\.tenor\.com/[^"\']+)["\'][^>]*alt=["\']([^"\']*)["\']',
                content
            )
            if not matches:
                matches_rev = re.findall(
                    r'<img[^>]+alt=["\']([^"\']*)["\'][^>]*src=["\'](https://media[0-9]*\.tenor\.com/[^"\']+)["\']',
                    content
                )
                matches = [(src, alt) for alt, src in matches_rev]

            if not matches:
                raw_urls = re.findall(r'https://media[0-9]*\.tenor\.com/[a-zA-Z0-9_\-]+AAAAM/[a-zA-Z0-9_\-]+\.gif', content)
                matches = [(u, "") for u in raw_urls]

            results = []
            seen_urls = set()

            for src, alt in matches:
                if not src.endswith(".gif"):
                    continue

                preview_url = src
                full_url = src.replace("AAAAM/", "AAAAC/") if "AAAAM/" in src else src

                if preview_url in seen_urls:
                    continue
                seen_urls.add(preview_url)

                raw_alt = html.unescape(alt).strip()
                filename_part = src.rsplit("/", 1)[-1].replace(".gif", "")
                clean_title = re.sub(r"[-_]+", " ", filename_part).strip().title()
                if not clean_title or len(clean_title) < 3:
                    clean_title = raw_alt[:35].title() if raw_alt else "Discord GIF"

                # Extract tags
                words = re.findall(r"\w+", (filename_part + " " + raw_alt).lower())
                tags = [w for w in words if len(w) > 2 and not w.isdigit()]

                gid = "tenor_" + hashlib.md5(preview_url.encode("utf-8")).hexdigest()[:10]
                entry = {
                    "id": gid,
                    "title": clean_title,
                    "url": full_url,
                    "preview_url": preview_url,
                    "tags": list(dict.fromkeys(tags))[:6] if tags else ["discord", "tenor"],
                    "is_tenor": True,
                    "favorite": False,
                    "use_count": 0,
                    "created_at": int(time.time()),
                }
                results.append(entry)
                TENOR_CACHE[gid] = entry
                if len(results) >= limit:
                    break

            if results:
                return results

        except Exception as ex:
            print(f"[tenor] Web scrape error for {url[:50]}: {ex}")

    # 2. Fallback to API if an explicit key was provided by user
    if api_key:
        encoded_q = urllib.parse.quote(query) if query else ""
        api_url = (
            f"https://tenor.googleapis.com/v2/search?q={encoded_q}&key={api_key}&limit={limit}"
            if encoded_q
            else f"https://tenor.googleapis.com/v2/featured?key={api_key}&limit={limit}"
        )
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=7, context=ssl._create_unverified_context()) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("results", []):
                gid = "tenor_" + str(item.get("id", uuid.uuid4().hex[:8]))
                title = item.get("title", "") or item.get("content_description", "GIF").title()
                gif_url = ""
                preview_url = ""
                if "media_formats" in item and isinstance(item["media_formats"], dict):
                    mf = item["media_formats"]
                    gif_url = mf.get("gif", {}).get("url") or mf.get("mediumgif", {}).get("url") or ""
                    preview_url = mf.get("tinygif", {}).get("url") or mf.get("nanogif", {}).get("url") or gif_url
                if not gif_url and item.get("url"):
                    gif_url = item["url"]
                if not preview_url:
                    preview_url = gif_url
                tags = item.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]
                entry = {
                    "id": gid,
                    "title": title or "Discord GIF",
                    "url": gif_url,
                    "preview_url": preview_url,
                    "tags": tags[:6] if tags else ["discord", "tenor"],
                    "is_tenor": True,
                    "favorite": False,
                    "use_count": 0,
                    "created_at": int(time.time()),
                }
                results.append(entry)
                TENOR_CACHE[gid] = entry
            if results:
                return results
        except Exception as ex:
            print(f"[tenor] API request failed: {ex}")

    return []

def scan_custom_directory(custom_dir: str) -> list[dict]:
    """Scan a custom directory recursively for .gif files and extract subfolders as categories."""
    global CUSTOM_GIF_INDEX
    if not os.path.isdir(custom_dir):
        return []

    import hashlib
    import re

    results = []
    try:
        for root, dirs, files in os.walk(custom_dir):
            for file in files:
                if file.lower().endswith(".gif"):
                    full_path = os.path.abspath(os.path.join(root, file))
                    rel = os.path.relpath(full_path, custom_dir)
                    parts = rel.split(os.sep)
                    # Category is first subfolder name (or empty if in root)
                    category = parts[0] if len(parts) > 1 else ""

                    # Clean title from file name
                    raw_name = os.path.splitext(file)[0]
                    # Strip trailing random hex hash or number suffix for clean title display
                    clean_raw = re.sub(r"_[0-9a-fA-F]{4,8}$", "", raw_name)
                    clean_name = re.sub(r"[-_.]+", " ", clean_raw).strip()
                    title = clean_name.title() if clean_name else "GIF"

                    # Custom folder tags: only folder category, do NOT flood tags with filename words
                    tags = [category.lower()] if category else []

                    gid = "ext_" + hashlib.sha1(rel.encode("utf-8", "ignore")).hexdigest()[:10]
                    item = {
                        "id": gid,
                        "title": title,
                        "category": category,
                        "filename": None,
                        "abs_path": full_path,
                        "rel_path": rel,
                        "url": f"/api/gif_file?id={gid}",
                        "tags": tags,
                        "is_custom_folder": True,
                        "favorite": False,
                        "use_count": 0,
                        "created_at": int(os.path.getmtime(full_path)),
                    }
                    results.append(item)
                    CUSTOM_GIF_INDEX[gid] = item
    except Exception as ex:
        print("[scan] Error scanning custom gif directory:", ex)

    # Sort alphabetical by category then title
    results.sort(key=lambda x: (x["category"].lower(), x["title"].lower()))
    return results

def get_active_library() -> list[dict]:
    """Return all GIFs: from custom directory if set, or local storage otherwise."""
    cfg = load_config()
    custom_dir = cfg.get("gif_dir", "").strip()
    saved_lib = load_library()
    saved_meta = {item.get("id"): item for item in saved_lib if item.get("id")}

    if custom_dir and os.path.isdir(custom_dir):
        custom_items = scan_custom_directory(custom_dir)
        for item in custom_items:
            gid = item["id"]
            if gid in saved_meta:
                meta = saved_meta[gid]
                item["favorite"] = meta.get("favorite", False)
                item["use_count"] = meta.get("use_count", 0)
                if meta.get("title"):
                    item["title"] = meta["title"]
                if "tags" in meta and isinstance(meta["tags"], list):
                    item["tags"] = meta["tags"]
        return custom_items

    # Fallback to local gifs/
    for item in saved_lib:
        if item.get("filename"):
            CUSTOM_GIF_INDEX[item["id"]] = item
    return saved_lib

def select_folder_dialog(initial_dir: str = "", title: str = "Ordner auswählen") -> str | None:
    """Open crash-proof Windows directory dialog via an isolated subprocess."""
    safe_title = title.replace('"', '').replace("'", "")
    init_path = initial_dir.replace("'", "''") if initial_dir and os.path.isdir(initial_dir) else ""
    ps_script = f"""
    [System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null
    $f = New-Object System.Windows.Forms.FolderBrowserDialog
    $f.Description = '{safe_title}'
    $f.ShowNewFolderButton = $true
    if ('{init_path}' -and (Test-Path '{init_path}')) {{ $f.SelectedPath = '{init_path}' }}
    $top = New-Object System.Windows.Forms.Form
    $top.TopMost = $true
    $res = $f.ShowDialog($top)
    if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
        Write-Output $f.SelectedPath
    }}
    """
    try:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
        creation_flags = 0x08000000 if sys.platform == "win32" else 0
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
            creationflags=creation_flags,
        )
        out = proc.stdout.strip()
        if out and os.path.isdir(out):
            return out
    except Exception as ex:
        print("[dialog] Error showing folder dialog:", ex)
    return None

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)

def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    except Exception as ex:
        print("[config] Error saving:", ex)

def load_library() -> list[dict]:
    if os.path.exists(LIBRARY_PATH):
        try:
            with open(LIBRARY_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return []

def save_library(lib: list[dict]) -> None:
    try:
        with open(LIBRARY_PATH, "w", encoding="utf-8") as fh:
            json.dump(lib, fh, indent=2, ensure_ascii=False)
    except Exception as ex:
        print("[library] Error saving:", ex)

# ---------------------------------------------------------------------------
# Windows Clipboard & Automation Helpers
# ---------------------------------------------------------------------------
def get_window_title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    return ""

def find_discord_window() -> int | None:
    """Scan top-level visible windows for Discord."""
    discord_hwnd = None

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_cb(hwnd, lparam):
        nonlocal discord_hwnd
        if user32.IsWindowVisible(hwnd):
            title = get_window_title(hwnd)
            if "Discord" in title:
                discord_hwnd = hwnd
                return False  # stop enumeration
        return True

    cb = WNDENUMPROC(enum_cb)
    user32.EnumWindows(cb, 0)
    return discord_hwnd

def copy_file_to_clipboard(file_path: str) -> bool:
    """Set CF_HDROP clipboard data for pasting actual file into Discord."""
    try:
        abs_path = os.path.abspath(file_path)
        files = abs_path + "\0\0"
        files_bytes = files.encode("utf-16le")

        df = DROPFILES()
        df.pFiles = ctypes.sizeof(DROPFILES)
        df.pt = wintypes.POINT(0, 0)
        df.fNC = False
        df.fWide = True
        df_bytes = bytes(df)
        total_bytes = df_bytes + files_bytes

        hGlobal = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(total_bytes))
        if not hGlobal:
            return False
        pGlobal = kernel32.GlobalLock(hGlobal)
        if not pGlobal:
            return False
        ctypes.memmove(pGlobal, total_bytes, len(total_bytes))
        kernel32.GlobalUnlock(hGlobal)

        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_HDROP, hGlobal)
        user32.CloseClipboard()
        return True
    except Exception as ex:
        print("[clipboard] Error copying file:", ex)
        return False

def copy_text_to_clipboard(text: str) -> bool:
    """Set CF_UNICODETEXT clipboard data."""
    try:
        text_bytes = (text + "\0").encode("utf-16le")
        hGlobal = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(text_bytes))
        if not hGlobal:
            return False
        pGlobal = kernel32.GlobalLock(hGlobal)
        if not pGlobal:
            return False
        ctypes.memmove(pGlobal, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(hGlobal)

        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, hGlobal)
        user32.CloseClipboard()
        return True
    except Exception as ex:
        print("[clipboard] Error copying text:", ex)
        return False

def activate_window_and_paste(hwnd: int, send_enter: bool = False) -> bool:
    """Brings the target window to foreground and simulates Ctrl+V."""
    try:
        # Give focus to target window
        cur_thread = kernel32.GetCurrentThreadId()
        target_pid = wintypes.DWORD()
        target_thread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))

        if cur_thread != target_thread:
            user32.AttachThreadInput(cur_thread, target_thread, True)

        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)

        if cur_thread != target_thread:
            user32.AttachThreadInput(cur_thread, target_thread, False)

        # Allow window focus transition
        time.sleep(0.12)

        # Send Ctrl+V
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        if send_enter:
            time.sleep(0.06)
            user32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

        return True
    except Exception as ex:
        print("[paste] Error during paste simulation:", ex)
        return False

# ---------------------------------------------------------------------------
# Global Hotkey Worker (Alt + G)
# ---------------------------------------------------------------------------
def hotkey_thread_worker():
    global LAST_TARGET_HWND, HOTKEY_REGISTERED
    MOD_ALT = 0x0001
    VK_G = 0x47
    HOTKEY_ID = 101

    if not user32.RegisterHotKey(0, HOTKEY_ID, MOD_ALT, VK_G):
        print("[hotkey] Could not register global hotkey Alt+G (might already be in use).")
        return

    HOTKEY_REGISTERED = True
    print("[hotkey] Registered global hotkey: Alt + G")

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        if msg.message == 0x0312:  # WM_HOTKEY
            if msg.wParam == HOTKEY_ID:
                fg_hwnd = user32.GetForegroundWindow()
                fg_title = get_window_title(fg_hwnd)
                # Store if not our own window
                if "DiscordGIF" not in fg_title:
                    LAST_TARGET_HWND = fg_hwnd

                # If our window exists, bring it to front
                if OUR_WINDOW_HWND and user32.IsWindowVisible(OUR_WINDOW_HWND):
                    user32.ShowWindow(OUR_WINDOW_HWND, 9)
                    user32.SetForegroundWindow(OUR_WINDOW_HWND)
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

# ---------------------------------------------------------------------------
# ComfyUI & Local AI Image-to-GIF Generator Engine
# ---------------------------------------------------------------------------
def _srv_t(de: str, en: str) -> str:
    try:
        return de if load_config().get("language") == "de" else en
    except Exception:
        return en

AI_STATE = {
    "busy": False,
    "progress": 0,
    "status_text": "Ready",
    "error": None,
    "current_gif": None,
    "prompt_id": None,
    "start_time": 0.0,
}
AI_STATE_LOCK = threading.Lock()

DOWNLOAD_STATE = {
    "downloading": False,
    "progress": 0.0,
    "downloaded_mb": 0.0,
    "total_mb": 0.0,
    "speed_mb": 0.0,
    "status_text": "Ready",
    "error": None,
}
DOWNLOAD_STATE_LOCK = threading.Lock()

def get_ffmpeg_path() -> str | None:
    """Find local or system ffmpeg executable."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    local_bin = os.path.join(APP_DIR, "bin", "ffmpeg.exe")
    if os.path.isfile(local_bin):
        return local_bin
    for probe in [
        r"C:\PortableApps\FFmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
    ]:
        if os.path.isfile(probe):
            return probe
    return None

def get_workflows_list() -> list[dict]:
    manifest_path = os.path.join(WORKFLOWS_DIR, "workflows.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as ex:
            print("[ai] Error reading workflows.json:", ex)
    return []

def check_comfyui_status(comfy_url: str = "") -> dict:
    cfg = load_config()
    url = (comfy_url or cfg.get("comfyui_url") or "http://127.0.0.1:8188").rstrip("/")
    ffmpeg_exe = get_ffmpeg_path()
    result = {
        "online": False,
        "url": url,
        "ffmpeg_installed": ffmpeg_exe is not None,
        "ffmpeg_path": ffmpeg_exe or "",
        "installed_models": [],
        "devices": [],
        "workflows": get_workflows_list(),
    }
    try:
        req = urllib.request.Request(f"{url}/system_stats", headers={"User-Agent": "tA-DiscordGIF"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result["online"] = True
            result["devices"] = data.get("devices", [])
    except Exception:
        result["online"] = False
        return result

    # Check available checkpoints & text encoders in ComfyUI
    for loader, param in [
        ("ImageOnlyCheckpointLoader", "ckpt_name"),
        ("CheckpointLoaderSimple", "ckpt_name"),
        ("CLIPLoader", "clip_name"),
        ("DualCLIPLoader", "clip_name1"),
        ("UNETLoader", "unet_name"),
        ("VAELoader", "vae_name"),
        ("LoraLoader", "lora_name"),
    ]:
        try:
            req_ckpt = urllib.request.Request(f"{url}/object_info/{loader}", headers={"User-Agent": "tA-DiscordGIF"})
            with urllib.request.urlopen(req_ckpt, timeout=1.8) as resp_ckpt:
                info = json.loads(resp_ckpt.read().decode("utf-8"))
                ckpts = info.get(loader, {}).get("input", {}).get("required", {}).get(param, [[]])[0]
                if isinstance(ckpts, list):
                    for c in ckpts:
                        if c not in result["installed_models"]:
                            result["installed_models"].append(c)
        except Exception:
            pass

    # Also check if models physically exist in auto-detected checkpoints & text_encoders folders
    auto_dir = auto_detect_comfy_checkpoints()
    result["detected_checkpoints_dir"] = auto_dir or ""
    if auto_dir and os.path.isdir(auto_dir):
        for root, _, files in os.walk(auto_dir):
            for f in files:
                low = f.lower()
                if low.endswith(".safetensors") or low.endswith(".ckpt"):
                    rel = os.path.relpath(os.path.join(root, f), auto_dir).replace("\\", "/")
                    if rel not in result["installed_models"]:
                        result["installed_models"].append(rel)
                    if f not in result["installed_models"]:
                        result["installed_models"].append(f)

        base_dir = os.path.dirname(auto_dir.rstrip(r"\/"))
        for sub in [
            "text_encoders", "clip", "models/text_encoders", "models/clip",
            "diffusion_models", "unet", "models/diffusion_models", "models/unet",
            "vae", "models/vae", "loras", "models/loras"
        ]:
            sub_dir = os.path.join(base_dir, sub)
            if os.path.isdir(sub_dir):
                for root, _, files in os.walk(sub_dir):
                    for f in files:
                        low = f.lower()
                        if low.endswith(".safetensors") or low.endswith(".ckpt") or low.endswith(".bin"):
                            rel = os.path.relpath(os.path.join(root, f), sub_dir).replace("\\", "/")
                            if rel not in result["installed_models"]:
                                result["installed_models"].append(rel)
                            if f not in result["installed_models"]:
                                result["installed_models"].append(f)

    return result

def comfy_upload_image(comfy_url: str, img_bytes: bytes, filename: str) -> str:
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    crlf = b"\r\n"
    data = []
    data.append(b"--" + boundary.encode("ascii") + crlf)
    data.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"'.encode("utf-8") + crlf)
    data.append(b"Content-Type: image/png" + crlf + crlf)
    data.append(img_bytes + crlf)
    data.append(b"--" + boundary.encode("ascii") + crlf)
    data.append(b'Content-Disposition: form-data; name="overwrite"' + crlf + crlf)
    data.append(b"true" + crlf)
    data.append(b"--" + boundary.encode("ascii") + b"--" + crlf)
    body = b"".join(data)

    req = urllib.request.Request(
        f"{comfy_url.rstrip('/')}/upload/image",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "tA-DiscordGIF",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        return res_data.get("name", filename)

def comfy_queue_prompt(comfy_url: str, workflow_dict: dict, client_id: str) -> str:
    payload = json.dumps({"prompt": workflow_dict, "client_id": client_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{comfy_url.rstrip('/')}/prompt",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "tA-DiscordGIF"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("prompt_id", "")
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8", "ignore")
        try:
            err_json = json.loads(err_body)
            if "node_errors" in err_json:
                msgs = []
                for n_id, n_err in err_json["node_errors"].items():
                    for e in n_err.get("errors", []):
                        msg = e.get("message", str(e)) if isinstance(e, dict) else str(e)
                        msgs.append(msg)
                raise RuntimeError("ComfyUI: " + "; ".join(msgs))
            if "error" in err_json:
                err_info = err_json["error"]
                msg = err_info.get("message", str(err_info)) if isinstance(err_info, dict) else str(err_info)
                raise RuntimeError("ComfyUI: " + msg)
        except Exception:
            pass
        raise RuntimeError(f"ComfyUI Fehler: {err_body}")

def comfy_interrupt(comfy_url: str) -> bool:
    try:
        req = urllib.request.Request(
            f"{comfy_url.rstrip('/')}/interrupt",
            data=b"{}",
            headers={"Content-Type": "application/json", "User-Agent": "tA-DiscordGIF"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as ex:
        print("[ai] Interrupt error:", ex)
        return False

def compile_frames_to_gif(frames_dir: str, output_path: str, fps: int = 12, scale_width: int = 400, pingpong: bool = True) -> bool:
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        print("[ai] FFmpeg not found!")
        return False

    input_pattern = os.path.join(frames_dir, "frame_%05d.png")
    if pingpong:
        filter_str = (
            f"[0:v]reverse[r];"
            f"[0:v][r]concat=n=2:v=1[full];"
            f"[full]fps={fps},scale={scale_width}:-1:flags=lanczos,split[s0][s1];"
            f"[s0]palettegen=max_colors=128:reserve_transparent=0[p];"
            f"[s1][p]paletteuse=dither=bayer:bayer_scale=3"
        )
    else:
        filter_str = (
            f"[0:v]fps={fps},scale={scale_width}:-1:flags=lanczos,split[s0][s1];"
            f"[s0]palettegen=max_colors=128:reserve_transparent=0[p];"
            f"[s1][p]paletteuse=dither=bayer:bayer_scale=3"
        )

    cmd = [
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-i", input_pattern,
        "-filter_complex", filter_str,
        "-loop", "0",
        output_path,
    ]
    creation_flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            creationflags=creation_flags,
        )
        if proc.returncode != 0:
            print("[ai] FFmpeg compile error:", proc.stderr)
            return False
        return os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    except Exception as ex:
        print("[ai] FFmpeg execution error:", ex)
        return False

def _safe_json_str(val: str) -> str:
    """Safely escape arbitrary string (paths, model names, prompts) for raw JSON template insertion."""
    return json.dumps(str(val))[1:-1]

def _run_ai_generation_thread(params: dict):
    global AI_STATE
    client_id = str(uuid.uuid4())
    temp_frames_dir = None
    try:
        with AI_STATE_LOCK:
            AI_STATE["busy"] = True
            AI_STATE["progress"] = 5
            AI_STATE["status_text"] = _srv_t("Prüfe ComfyUI...", "Checking ComfyUI...")
            AI_STATE["error"] = None
            AI_STATE["current_gif"] = None
            AI_STATE["start_time"] = time.time()

        cfg = load_config()
        comfy_url = (cfg.get("comfyui_url") or "http://127.0.0.1:8188").rstrip("/")

        # 1. Decode source image
        img_b64 = params.get("image_data", "")
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(img_b64)
        source_filename = f"tA_source_{str(uuid.uuid4())[:8]}.png"

        # 2. Upload image to ComfyUI
        with AI_STATE_LOCK:
            AI_STATE["progress"] = 12
            AI_STATE["status_text"] = _srv_t("Lade Ausgangsbild zu ComfyUI hoch...", "Uploading source image to ComfyUI...")

        uploaded_name = comfy_upload_image(comfy_url, img_bytes, source_filename)

        # 3. Load workflow
        workflow_id = params.get("workflow_id") or cfg.get("ai_workflow") or "svd_xt"
        workflow_path = os.path.join(WORKFLOWS_DIR, f"{workflow_id}.json")
        if not os.path.isfile(workflow_path):
            raise FileNotFoundError(f"Workflow '{workflow_id}.json' nicht gefunden.")

        with open(workflow_path, "r", encoding="utf-8") as fh:
            wf_str = fh.read()

        # Auto-detect source image aspect ratio to avoid squishing/stretching
        import io
        from PIL import Image

        orig_w, orig_h = 512, 512
        try:
            with Image.open(io.BytesIO(img_bytes)) as pil_img:
                orig_w, orig_h = pil_img.size
        except Exception:
            pass

        req_w = int(params.get("width") or 512)
        req_h = int(params.get("height") or 512)
        target_area = req_w * req_h

        if orig_w > 0 and orig_h > 0:
            aspect = float(orig_w) / float(orig_h)
            calc_h = (target_area / aspect) ** 0.5
            calc_w = calc_h * aspect
            width = max(192, min(832, int(round(calc_w / 32.0)) * 32))
            height = max(192, min(832, int(round(calc_h / 32.0)) * 32))
        else:
            width = req_w
            height = req_h

        frames = int(params.get("frames") or 44)
        fps = int(params.get("fps") or 12)
        motion_bucket = int(params.get("motion_bucket") or 100)
        seed = int(params.get("seed") or int(time.time() * 1000) % 1000000000)
        steps = int(params.get("steps") or 20)

        # Workflow-specific adjustments
        if "ltx" in workflow_id.lower():
            width = max(64, (width // 32) * 32)
            height = max(64, (height // 32) * 32)
            frames = max(9, (((frames - 1) // 8) * 8) + 1)
            # Map motion_bucket (20 - 200) to strength (0.85 down to 0.48)
            # motion_bucket 20 -> 0.85 (subtle/rigid)
            # motion_bucket 100 -> 0.65 (active dynamic motion)
            # motion_bucket 200 -> 0.48 (maximum motion freedom)
            t = max(0.0, min(1.0, (motion_bucket - 20) / (200 - 20)))
            ltx_strength = round(0.85 - (t * 0.37), 2)
            ltx_cfg = 3.5
            if steps < 25:
                steps = 25
        elif "minimax" in workflow_id.lower() or "h3" in workflow_id.lower():
            width = max(64, (width // 32) * 32)
            height = max(64, (height // 32) * 32)
            ltx_strength = 0.85
            ltx_cfg = 1.0
            # FastH3 / MiniMax H3 produces photorealistic motion in 8 steps
            steps = 8

            # Dynamically resolve exact installed model names from ComfyUI
            comfy_status = check_comfyui_status(comfy_url)
            avail_models = comfy_status.get("installed_models", [])

            def _resolve_model_name(candidates, default_val, keywords=None):
                for cand in candidates:
                    for m in avail_models:
                        ml = m.lower().replace("\\", "/")
                        cl = cand.lower().replace("\\", "/")
                        if ml == cl or ml.endswith("/" + cl):
                            return m
                if keywords:
                    for m in avail_models:
                        ml = m.lower()
                        if all(kw.lower() in ml for kw in keywords):
                            return m
                return default_val

            unet_name = _resolve_model_name([
                "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
                "fastvideo_fasth3_8step_v2_pruned_int8_convrot.safetensors",
                "minimax_h3_hybrid_fl2va_ref2va_b30-49-int8.safetensors",
                "MiniMax_H3_Ref2VA_pruned_int8_convrot.safetensors",
                "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
                "minimax_h3_fl2va_bf16.safetensors",
            ], "minimax_h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors", ["minimax", "fl2va"])

            clip_name = _resolve_model_name([
                "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
                "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "qwen3vl_32b_minimax_h3_int4_convrot.safetensors",
                "qwen3vl_32b_minimax_h3_bf16.safetensors",
            ], "minimax_h3/qwen3vl_32b_minimax_h3_int8_convrot.safetensors", ["qwen3vl", "minimax"])

            vae_name = _resolve_model_name([
                "minimax_h3_video_vae_fp16.safetensors",
                "minimax_h3_video_vae_bf16.safetensors",
                "minimax_h3_video_vae.safetensors",
                "minimax_video_vae_fp16.safetensors",
            ], "minimax_h3/minimax_h3_video_vae_fp16.safetensors", ["minimax", "vae"])

            wf_str = wf_str.replace("{{UNET_NAME}}", _safe_json_str(unet_name))
            wf_str = wf_str.replace("{{CLIP_NAME}}", _safe_json_str(clip_name))
            wf_str = wf_str.replace("{{VAE_NAME}}", _safe_json_str(vae_name))
        else:
            ltx_strength = 0.85
            ltx_cfg = 3.0

        wf_str = wf_str.replace("{{IMAGE_FILENAME}}", _safe_json_str(uploaded_name))
        wf_str = wf_str.replace("{{WIDTH}}", str(width))
        wf_str = wf_str.replace("{{HEIGHT}}", str(height))
        wf_str = wf_str.replace("{{FRAMES}}", str(frames))
        wf_str = wf_str.replace("{{FPS}}", str(float(fps)))
        wf_str = wf_str.replace("{{MOTION_BUCKET}}", str(motion_bucket))
        wf_str = wf_str.replace("{{STRENGTH}}", str(ltx_strength))
        wf_str = wf_str.replace("{{CFG}}", str(ltx_cfg))
        wf_str = wf_str.replace("{{SEED}}", str(seed))
        wf_str = wf_str.replace("{{STEPS}}", str(steps))
        prompt_txt = str(params.get("prompt") or "").strip()
        wf_str = wf_str.replace("{{PROMPT}}", _safe_json_str(prompt_txt))

        wf_dict = json.loads(wf_str)

        # 4. Queue prompt
        with AI_STATE_LOCK:
            AI_STATE["progress"] = 20
            AI_STATE["status_text"] = _srv_t("Sende Prompt an ComfyUI Queue...", "Sending prompt to ComfyUI queue...")

        prompt_id = comfy_queue_prompt(comfy_url, wf_dict, client_id)
        if not prompt_id:
            raise RuntimeError("ComfyUI hat keine Prompt-ID zurückgegeben.")

        with AI_STATE_LOCK:
            AI_STATE["prompt_id"] = prompt_id
            AI_STATE["progress"] = 25
            AI_STATE["status_text"] = _srv_t("ComfyUI rendert Video-Frames...", "ComfyUI is rendering video frames...")

        # 5. Poll for completion
        history_url = f"{comfy_url}/history/{prompt_id}"
        poll_start = time.time()
        output_images = []

        while True:
            if not AI_STATE["busy"]:
                # Aborted by user
                comfy_interrupt(comfy_url)
                return

            try:
                req_h = urllib.request.Request(history_url, headers={"User-Agent": "tA-DiscordGIF"})
                with urllib.request.urlopen(req_h, timeout=5) as resp_h:
                    h_data = json.loads(resp_h.read().decode("utf-8"))
                    if prompt_id in h_data:
                        prompt_hist = h_data[prompt_id]
                        outputs = prompt_hist.get("outputs", {})
                        for node_id, node_out in outputs.items():
                            if "images" in node_out:
                                output_images.extend(node_out["images"])
                        break
            except Exception:
                pass

            elapsed = int(time.time() - poll_start)
            sim_progress = min(85, 25 + int(elapsed * 1.5))
            with AI_STATE_LOCK:
                AI_STATE["progress"] = sim_progress
                AI_STATE["status_text"] = _srv_t(f"Generiere AI Video-Frames ({elapsed}s)...", f"Generating AI video frames ({elapsed}s)...")

            time.sleep(0.8)

        if not output_images:
            raise RuntimeError("ComfyUI hat keine gerenderten Bilder ausgegeben.")

        # 6. Download rendered frames to temp dir
        with AI_STATE_LOCK:
            AI_STATE["progress"] = 88
            AI_STATE["status_text"] = _srv_t("Lade gerenderte Frames herunter...", "Downloading rendered frames...")

        temp_frames_dir = os.path.join(DATA_DIR, "temp", f"ai_{client_id[:8]}")
        os.makedirs(temp_frames_dir, exist_ok=True)

        for idx, img_info in enumerate(output_images):
            fn = img_info.get("filename")
            subf = img_info.get("subfolder", "")
            img_type = img_info.get("type", "output")
            view_url = f"{comfy_url}/view?filename={urllib.parse.quote(fn)}&subfolder={urllib.parse.quote(subf)}&type={img_type}"
            dest_frame = os.path.join(temp_frames_dir, f"frame_{idx:05d}.png")
            req_v = urllib.request.Request(view_url, headers={"User-Agent": "tA-DiscordGIF"})
            with urllib.request.urlopen(req_v, timeout=15) as resp_v, open(dest_frame, "wb") as out_f:
                shutil.copyfileobj(resp_v, out_f)

        # 7. Convert frames to GIF using FFmpeg
        with AI_STATE_LOCK:
            AI_STATE["progress"] = 93
            AI_STATE["status_text"] = _srv_t("Optimiere Discord-GIF (FFmpeg Palette)...", "Optimizing Discord GIF (FFmpeg Palette)...")

        # Determine target folder
        custom_dir = cfg.get("gif_dir", "").strip()
        target_base = custom_dir if custom_dir and os.path.isdir(custom_dir) else GIFS_DIR
        ai_folder = os.path.join(target_base, "AI-Generated")
        os.makedirs(ai_folder, exist_ok=True)

        user_title = params.get("title", "").strip() or "AI_GIF"
        clean_title = re.sub(r'[\\/*?:"<>|]+', '', user_title).strip().replace(" ", "_")

        # Find next available 3-digit index (_001, _002, ...)
        existing = set(os.listdir(ai_folder)) if os.path.isdir(ai_folder) else set()
        idx = 1
        while True:
            candidate = f"{clean_title}_{idx:03d}.gif"
            if candidate not in existing:
                gif_filename = candidate
                break
            idx += 1

        final_gif_path = os.path.join(ai_folder, gif_filename)

        scale_width = int(params.get("scale_width") or (480 if width > height else 400))
        if width > height and scale_width < 480:
            scale_width = 480
        pingpong = bool(params.get("loop_mode", "pingpong") == "pingpong")

        compile_ok = compile_frames_to_gif(temp_frames_dir, final_gif_path, fps=fps, scale_width=scale_width, pingpong=pingpong)
        if not compile_ok:
            raise RuntimeError("FFmpeg GIF-Erstellung fehlgeschlagen.")

        # 8. Register in library
        file_size_mb = round(os.path.getsize(final_gif_path) / (1024 * 1024), 2)
        rel_path = f"AI-Generated/{gif_filename}"
        gid = "ai_" + hashlib.sha1(rel_path.encode("utf-8", "ignore")).hexdigest()[:10]

        gif_item = {
            "id": gid,
            "title": clean_title.replace("_", " ").title(),
            "category": "AI-Generated",
            "filename": rel_path if target_base == GIFS_DIR else None,
            "abs_path": final_gif_path,
            "rel_path": rel_path,
            "url": f"/api/gif_file?id={gid}",
            "tags": ["ai", "animated", "reaction"],
            "favorite": False,
            "use_count": 0,
            "created_at": int(time.time()),
            "file_size_mb": file_size_mb,
        }

        CUSTOM_GIF_INDEX[gid] = gif_item
        lib = load_library()
        lib.insert(0, gif_item)
        save_library(lib)

        with AI_STATE_LOCK:
            AI_STATE["busy"] = False
            AI_STATE["progress"] = 100
            AI_STATE["status_text"] = _srv_t(f"Fertig! GIF erstellt ({file_size_mb} MB)", f"Done! GIF created ({file_size_mb} MB)")
            AI_STATE["current_gif"] = gif_item

    except Exception as ex:
        print("[ai] Generation error:", ex)
        with AI_STATE_LOCK:
            AI_STATE["busy"] = False
            AI_STATE["error"] = str(ex)
            AI_STATE["status_text"] = _srv_t(f"Fehler: {ex}", f"Error: {ex}")
    finally:
        if temp_frames_dir and os.path.isdir(temp_frames_dir):
            try:
                shutil.rmtree(temp_frames_dir, ignore_errors=True)
            except Exception:
                pass

def _is_backup_path(p: str) -> bool:
    if not p:
        return False
    low = p.lower()
    return low.startswith("i:") or any(x in low for x in ["backup", "veeam", "clonezilla", "$recycle.bin", "system volume information"])

def _parse_extra_model_paths_yaml(yaml_path: str) -> str | None:
    try:
        with open(yaml_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        base_path = ""
        checkpoints_path = ""
        for line in lines:
            line_s = line.strip()
            if line_s.startswith("base_path:"):
                base_path = line_s.split(":", 1)[1].strip().strip('"\'')
            elif line_s.startswith("checkpoints:"):
                checkpoints_path = line_s.split(":", 1)[1].strip().strip('"\'')
        target = checkpoints_path or (base_path + "/checkpoints" if base_path else "")
        if target and not target.startswith("/home/") and not target.startswith("/"):
            if os.path.isdir(target) and not _is_backup_path(target):
                return target
    except Exception:
        pass
    return None

def auto_detect_comfy_checkpoints() -> str | None:
    """
    Intelligently discovers the ComfyUI models/checkpoints directory without prompting the user:
    1. Checks sibling tA-VideoMaker config (models_dir & comfy_dir).
    2. Checks user-configured 'comfyui_dir' from config.json.
    3. Known local candidate directories (EXCLUDING drive I: and backup directories).
    4. Parses extra_model_paths.yaml in any discovered ComfyUI directory.
    5. Inspects running processes on port 8188 silently without console popup.
    6. Fast scan drive roots (C: to H:).
    """
    # 1. Check sibling tA-VideoMaker config (models_dir & comfy_dir)
    sibling_configs = [
        os.path.join(APP_DIR, "..", "tA-VideoMaker", "dist", "data", "config.json"),
        os.path.join(APP_DIR, "..", "tA-VideoMaker", "data", "config.json"),
        r"D:\Workspace\AG\tA-VideoMaker\dist\data\config.json",
        r"D:\Workspace\AG\tA-VideoMaker\data\config.json",
    ]
    for scp in sibling_configs:
        if os.path.isfile(scp):
            try:
                with open(scp, "r", encoding="utf-8") as f_sc:
                    sc = json.load(f_sc)
                    md = sc.get("models_dir", "").strip()
                    if md and os.path.isdir(md) and not _is_backup_path(md):
                        for sub in [os.path.join(md, "checkpoints"), md]:
                            if os.path.isdir(sub):
                                return sub
                    cd = sc.get("comfy_dir", "").strip()
                    if cd and os.path.isdir(cd) and not _is_backup_path(cd):
                        for sub in [os.path.join(cd, "models", "checkpoints"), os.path.join(cd, "checkpoints")]:
                            if os.path.isdir(sub):
                                return sub
            except Exception:
                pass

    # 2. Config check
    try:
        cfg = load_config()
        saved = cfg.get("comfyui_dir", "").strip()
        if saved and os.path.isdir(saved) and not _is_backup_path(saved):
            for sub in [os.path.join(saved, "models", "checkpoints"), os.path.join(saved, "checkpoints"), saved]:
                if os.path.isdir(sub):
                    return sub
    except Exception:
        pass

    # 3. Known local candidate directories (EXCLUDING drive I: and backup directories)
    known_candidates = [
        r"E:\Tools\ComfyUI\CEI-1\ComfyUI",
        r"E:\Tools\ComfyUI\CEI-1-DEV\ComfyUI",
        r"C:\ComfyUI_windows_portable\ComfyUI",
        r"D:\ComfyUI_windows_portable\ComfyUI",
        r"E:\ComfyUI_windows_portable\ComfyUI",
        r"C:\ComfyUI",
        r"D:\ComfyUI",
        r"E:\ComfyUI",
    ]
    for k in known_candidates:
        if os.path.isdir(k) and not _is_backup_path(k):
            yaml_path = os.path.join(k, "extra_model_paths.yaml")
            if os.path.isfile(yaml_path):
                parsed = _parse_extra_model_paths_yaml(yaml_path)
                if parsed:
                    return parsed
            for sub in [os.path.join(k, "models", "checkpoints"), os.path.join(k, "checkpoints")]:
                if os.path.isdir(sub):
                    return sub

    # 4. Active process listening on port 8188 (silent subprocess)
    creation_flags = 0x08000000 if sys.platform == "win32" else 0
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True, text=True, timeout=3,
            creationflags=creation_flags
        )
        pid = None
        for line in out.stdout.splitlines():
            if ":8188" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    break
        if pid:
            cmd = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", f"(Get-Process -Id {pid}).Path"],
                capture_output=True, text=True, timeout=3,
                creationflags=creation_flags
            )
            p_path = cmd.stdout.strip()
            if p_path and os.path.isfile(p_path) and not _is_backup_path(p_path):
                base = os.path.dirname(p_path)
                for candidate in [base, os.path.dirname(base)]:
                    if not _is_backup_path(candidate):
                        yaml_path = os.path.join(candidate, "extra_model_paths.yaml")
                        if os.path.isfile(yaml_path):
                            parsed = _parse_extra_model_paths_yaml(yaml_path)
                            if parsed:
                                return parsed
                        for sub in [
                            os.path.join(candidate, "ComfyUI", "models", "checkpoints"),
                            os.path.join(candidate, "models", "checkpoints")
                        ]:
                            if os.path.isdir(sub):
                                return sub
    except Exception:
        pass

    # 5. Fast scan drive roots (strictly ignoring I: and any backup drive)
    drives = [f"{chr(c)}:\\" for c in range(ord('C'), ord('H')+1)]
    for d in drives:
        if not os.path.exists(d):
            continue
        try:
            for entry in os.listdir(d):
                low = entry.lower()
                if "comfy" in low or "cei" in low:
                    full = os.path.join(d, entry)
                    if os.path.isdir(full) and not _is_backup_path(full):
                        for sub in [
                            os.path.join(full, "ComfyUI", "models", "checkpoints"),
                            os.path.join(full, "models", "checkpoints")
                        ]:
                            if os.path.isdir(sub):
                                return sub
        except Exception:
            pass

    return None

def get_comfy_model_folder(folder_type: str = "checkpoints") -> str | None:
    """
    Returns the target ComfyUI folder for a given model type:
    - 'checkpoints' -> models/checkpoints
    - 'text_encoders' or 'clip' -> models/text_encoders or models/clip
    - other -> models/<folder_type>
    Auto-detects live ComfyUI installation, creating subdirectories if needed.
    """
    ckpt_dir = auto_detect_comfy_checkpoints()
    if not ckpt_dir:
        # Fallback to configured comfyui_dir
        try:
            cfg = load_config()
            saved = cfg.get("comfyui_dir", "").strip()
            if saved and os.path.isdir(saved) and not _is_backup_path(saved):
                for sub in [os.path.join(saved, "models", "checkpoints"), os.path.join(saved, "checkpoints"), saved]:
                    if os.path.isdir(sub):
                        ckpt_dir = sub
                        break
        except Exception:
            pass

    if not ckpt_dir:
        return None

    if folder_type == "checkpoints":
        return ckpt_dir

    # Find the models base directory
    if ckpt_dir.rstrip(r"\/").endswith("checkpoints"):
        models_base = os.path.dirname(ckpt_dir.rstrip(r"\/"))
    else:
        models_base = ckpt_dir

    if folder_type in ("text_encoders", "clip"):
        # Check existing directories
        for cand in [
            os.path.join(models_base, "text_encoders"),
            os.path.join(models_base, "clip"),
            os.path.join(models_base, "models", "text_encoders"),
            os.path.join(models_base, "models", "clip"),
        ]:
            if os.path.isdir(cand):
                return cand
        # If neither exists, default to text_encoders and create it
        target = os.path.join(models_base, "text_encoders")
        try:
            os.makedirs(target, exist_ok=True)
            return target
        except Exception:
            return os.path.join(models_base, "clip")

    # Other folder types (e.g. vae, loras)
    target = os.path.join(models_base, folder_type)
    try:
        os.makedirs(target, exist_ok=True)
        return target
    except Exception:
        return target

def _run_model_download_thread(model_url: str, dest_dir: str, custom_filename: str = ""):
    global DOWNLOAD_STATE
    try:
        with DOWNLOAD_STATE_LOCK:
            DOWNLOAD_STATE["downloading"] = True
            DOWNLOAD_STATE["progress"] = 0.0
            DOWNLOAD_STATE["downloaded_mb"] = 0.0
            DOWNLOAD_STATE["total_mb"] = 0.0
            DOWNLOAD_STATE["speed_mb"] = 0.0
            DOWNLOAD_STATE["status_text"] = _srv_t("Starte Download...", "Starting download...")
            DOWNLOAD_STATE["error"] = None

        if custom_filename:
            filename = custom_filename
        else:
            filename = os.path.basename(urllib.parse.urlparse(model_url).path)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, filename)

        ssl_ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            model_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        start_time = time.time()
        last_time = start_time
        downloaded = 0

        # Try connecting with retry on temporary DNS / socket blips (e.g. Errno 11002 WSATRY_AGAIN)
        resp = None
        for attempt in range(1, 4):
            try:
                resp = urllib.request.urlopen(req, timeout=30, context=ssl_ctx)
                break
            except Exception as e:
                if attempt >= 3:
                    raise
                with DOWNLOAD_STATE_LOCK:
                    DOWNLOAD_STATE["status_text"] = _srv_t(f"Verbindungsversuch {attempt}/3 fehlgeschlagen, neuer Versuch...", f"Connection attempt {attempt}/3 failed, retrying...")
                time.sleep(2)

        with resp, open(dest_file, "wb") as out_f:
            total_size = int(resp.headers.get("content-length", 0))
            total_mb = round(total_size / (1024 * 1024), 1)
            with DOWNLOAD_STATE_LOCK:
                DOWNLOAD_STATE["total_mb"] = total_mb

            chunk_size = 1024 * 1024 * 2  # 2 MB buffer for faster throughput
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_time >= 0.5:
                    downloaded_mb = round(downloaded / (1024 * 1024), 1)
                    speed = round((downloaded / (1024 * 1024)) / max(0.1, now - start_time), 2)
                    pct = round((downloaded / total_size) * 100, 1) if total_size else 0.0
                    with DOWNLOAD_STATE_LOCK:
                        DOWNLOAD_STATE["progress"] = pct
                        DOWNLOAD_STATE["downloaded_mb"] = downloaded_mb
                        DOWNLOAD_STATE["speed_mb"] = speed
                        DOWNLOAD_STATE["status_text"] = f"{downloaded_mb} MB / {total_mb} MB ({pct}%) • {speed} MB/s"
                    last_time = now

        with DOWNLOAD_STATE_LOCK:
            DOWNLOAD_STATE["downloading"] = False
            DOWNLOAD_STATE["progress"] = 100.0
            DOWNLOAD_STATE["status_text"] = _srv_t(f"Download abgeschlossen! ({filename})", f"Download complete! ({filename})")

    except Exception as ex:
        print("[ai] Download error:", ex)
        with DOWNLOAD_STATE_LOCK:
            DOWNLOAD_STATE["downloading"] = False
            DOWNLOAD_STATE["error"] = str(ex)
            DOWNLOAD_STATE["status_text"] = _srv_t(f"Fehler: {ex}", f"Error: {ex}")

# ---------------------------------------------------------------------------
# HTTP Server & API
# ---------------------------------------------------------------------------
class AppHandler(BaseHTTPRequestHandler):
    server_version = "tA-DiscordGIF/" + APP_VERSION

    def log_message(self, format, *args):
        # Keep terminal output clean
        pass

    def send_json(self, data: any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400):
        self.send_json({"error": message, "ok": False}, status=status)

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        if path == "/api/ping":
            record_ping()
            self.send_json({"ok": True})
            return

        if path == "/api/status":
            record_ping()
            global LAST_TARGET_HWND
            discord_hwnd = find_discord_window()
            target_title = ""
            if LAST_TARGET_HWND:
                target_title = get_window_title(LAST_TARGET_HWND)
            elif discord_hwnd:
                target_title = get_window_title(discord_hwnd)

            self.send_json({
                "ok": True,
                "version": APP_VERSION,
                "discord_found": discord_hwnd is not None,
                "discord_title": get_window_title(discord_hwnd) if discord_hwnd else None,
                "target_window": target_title or "Discord",
                "hotkey_registered": HOTKEY_REGISTERED,
            })
            return

        if path == "/api/gifs":
            lib = get_active_library()
            cfg = load_config()
            self.send_json({
                "ok": True,
                "gifs": lib,
                "gif_dir": cfg.get("gif_dir", ""),
                "is_custom": bool(cfg.get("gif_dir") and os.path.isdir(cfg.get("gif_dir"))),
            })
            return

        if path == "/api/gif_file":
            query = urllib.parse.parse_qs(url_parsed.query)
            gid = query.get("id", [""])[0]
            item = CUSTOM_GIF_INDEX.get(gid)
            if item and item.get("abs_path") and os.path.isfile(item["abs_path"]):
                self.serve_file(item["abs_path"], "image/gif")
                return
            self.send_error(404, "GIF not found")
            return

        if path == "/api/tenor/search":
            query = urllib.parse.parse_qs(url_parsed.query)
            q = query.get("q", [""])[0]
            limit = int(query.get("limit", [28])[0])
            results = fetch_tenor_gifs(q, limit=limit)
            self.send_json({"ok": True, "gifs": results, "query": q})
            return

        if path == "/api/shutdown":
            self.send_json({"ok": True})
            threading.Thread(target=lambda: (time.sleep(0.1), os._exit(0)), daemon=True).start()
            return

        if path == "/api/settings":
            cfg = load_config()
            self.send_json({"ok": True, "settings": cfg})
            return

        if path == "/api/ai/status":
            url_param = urllib.parse.parse_qs(url_parsed.query).get("url", [""])[0]
            st = check_comfyui_status(url_param)
            self.send_json(st)
            return

        if path == "/api/ai/workflows":
            self.send_json({"ok": True, "workflows": get_workflows_list()})
            return

        if path == "/api/ai/progress":
            with AI_STATE_LOCK:
                self.send_json(dict(AI_STATE))
            return

        if path == "/api/ai/download_progress":
            with DOWNLOAD_STATE_LOCK:
                self.send_json(dict(DOWNLOAD_STATE))
            return

        # Static file delivery
        if path.startswith("/gifs/"):
            gif_filename = os.path.basename(urllib.parse.unquote(path[6:]))
            local_gif_path = os.path.join(GIFS_DIR, gif_filename)
            if os.path.isfile(local_gif_path):
                self.serve_file(local_gif_path, "image/gif")
                return
            self.send_error(404, "GIF not found")
            return

        # Web static files
        req_path = path.lstrip("/")
        if not req_path:
            req_path = "index.html"
        full_path = os.path.abspath(os.path.join(WEB_DIR, req_path))

        if not full_path.startswith(os.path.abspath(WEB_DIR)):
            self.send_error(403, "Forbidden")
            return

        if os.path.isfile(full_path):
            ctype, _ = mimetypes.guess_type(full_path)
            self.serve_file(full_path, ctype or "application/octet-stream")
            return

        self.send_error(404, "Not Found")

    def serve_file(self, file_path: str, content_type: str):
        try:
            with open(file_path, "rb") as fh:
                content = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type + ("; charset=utf-8" if file_path.endswith((".html", ".js", ".css")) else ""))
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(content)
        except Exception as ex:
            self.send_error(500, str(ex))

    def read_json_body(self) -> dict:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len)
        return json.loads(raw.decode("utf-8"))

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path

        if path == "/api/shutdown":
            self.send_json({"ok": True})
            threading.Thread(target=lambda: (time.sleep(0.1), os._exit(0)), daemon=True).start()
            return

        if path == "/api/settings":
            body = self.read_json_body()
            cfg = load_config()
            cfg.update(body)
            save_config(cfg)
            self.send_json({"ok": True, "settings": cfg})
            return

        if path == "/api/ai/generate":
            body = self.read_json_body()
            with AI_STATE_LOCK:
                if AI_STATE["busy"]:
                    self.send_error_json(_srv_t("Eine GIF-Generierung läuft bereits.", "A GIF generation is already in progress."), 400)
                    return
            threading.Thread(target=_run_ai_generation_thread, args=(body,), daemon=True).start()
            self.send_json({"ok": True, "status": "started"})
            return

        if path == "/api/ai/cancel":
            with AI_STATE_LOCK:
                AI_STATE["busy"] = False
                AI_STATE["status_text"] = _srv_t("Abgebrochen", "Canceled")
            cfg = load_config()
            comfy_interrupt(cfg.get("comfyui_url") or "http://127.0.0.1:8188")
            self.send_json({"ok": True})
            return

        if path == "/api/ai/download_model":
            body = self.read_json_body()
            model_url = body.get("model_url", "").strip()
            folder_type = body.get("folder_type", "checkpoints").strip()
            custom_filename = body.get("filename", "").strip()
            if not model_url:
                self.send_error_json("Keine Download-URL angegeben", 400)
                return
            
            # Automatic discovery based on folder_type (checkpoints or text_encoders/clip)
            dest_dir = get_comfy_model_folder(folder_type)
            
            # Fallback if manual comfy_dir was provided
            if not dest_dir:
                cfg = load_config()
                comfy_dir = body.get("comfy_dir") or cfg.get("comfyui_dir", "").strip()
                if comfy_dir and os.path.isdir(comfy_dir):
                    sub = "text_encoders" if folder_type in ("text_encoders", "clip") else "checkpoints"
                    if os.path.isdir(os.path.join(comfy_dir, "models", sub)):
                        dest_dir = os.path.join(comfy_dir, "models", sub)
                    elif os.path.isdir(os.path.join(comfy_dir, sub)):
                        dest_dir = os.path.join(comfy_dir, sub)
                    else:
                        dest_dir = os.path.join(comfy_dir, "models", sub)
            
            if not dest_dir:
                self.send_error_json("ComfyUI-Ordner konnte nicht automatisch gefunden werden.", 400)
                return
            
            # Save detected base directory in config
            try:
                cfg = load_config()
                base_dir = os.path.dirname(os.path.dirname(dest_dir)) if any(dest_dir.endswith(x) for x in ["checkpoints", "text_encoders", "clip"]) else dest_dir
                if cfg.get("comfyui_dir") != base_dir:
                    cfg["comfyui_dir"] = base_dir
                    save_config(cfg)
            except Exception:
                pass
            
            with DOWNLOAD_STATE_LOCK:
                if DOWNLOAD_STATE["downloading"]:
                    self.send_error_json("Download läuft bereits.", 400)
                    return
            threading.Thread(target=_run_model_download_thread, args=(model_url, dest_dir, custom_filename), daemon=True).start()
            self.send_json({"ok": True, "dest_dir": dest_dir})
            return

        if path == "/api/select_folder":
            cfg = load_config()
            chosen = select_folder_dialog(cfg.get("gif_dir", ""))
            self.send_json({"ok": True, "path": chosen or ""})
            return

        if path == "/api/gifs/add":
            # Supports adding from URL or base64/upload
            body = self.read_json_body()
            title = body.get("title", "").strip() or "Neues GIF"
            tags_raw = body.get("tags", "")
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else tags_raw
            url = body.get("url", "").strip()

            item_id = str(uuid.uuid4())[:8]
            local_filename = None
            data_b64 = body.get("data")

            if data_b64:
                try:
                    if "," in data_b64:
                        data_b64 = data_b64.split(",", 1)[1]
                    raw_bytes = base64.b64decode(data_b64)
                    local_filename = f"{item_id}.gif"
                    target_path = os.path.join(GIFS_DIR, local_filename)
                    with open(target_path, "wb") as out:
                        out.write(raw_bytes)
                except Exception as ex:
                    print(f"[import] Could not decode base64 data: {ex}")
                    local_filename = None
            elif url and (url.startswith("http://") or url.startswith("https://")):
                # Download remote GIF to local store
                try:
                    local_filename = f"{item_id}.gif"
                    target_path = os.path.join(GIFS_DIR, local_filename)
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp, open(target_path, "wb") as out:
                        shutil.copyfileobj(resp, out)
                except Exception as ex:
                    print(f"[import] Could not download {url}: {ex}. Storing URL only.")
                    local_filename = None

            gif_item = {
                "id": item_id,
                "title": title,
                "filename": local_filename,
                "url": url,
                "tags": tags,
                "favorite": False,
                "use_count": 0,
                "created_at": int(time.time()),
            }

            lib = load_library()
            lib.insert(0, gif_item)
            save_library(lib)
            self.send_json({"ok": True, "gif": gif_item})
            return

        if path == "/api/gifs/update":
            body = self.read_json_body()
            gid = body.get("id")
            lib = load_library()
            found = False
            for item in lib:
                if item["id"] == gid:
                    if "title" in body:
                        item["title"] = body["title"]
                    if "tags" in body:
                        tags_raw = body["tags"]
                        item["tags"] = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else tags_raw
                    if "favorite" in body:
                        item["favorite"] = bool(body["favorite"])
                    found = True
                    break
            if not found and gid:
                entry = {"id": gid}
                if "favorite" in body:
                    entry["favorite"] = bool(body["favorite"])
                if "title" in body:
                    entry["title"] = body["title"].strip()
                if "tags" in body:
                    tags_raw = body["tags"]
                    entry["tags"] = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else tags_raw
                lib.append(entry)
            save_library(lib)
            self.send_json({"ok": True})
            return

        if path == "/api/gifs/delete":
            body = self.read_json_body()
            gid = body.get("id")
            lib = load_library()
            item_to_remove = next((item for item in lib if item["id"] == gid), None)
            if item_to_remove:
                if item_to_remove.get("filename"):
                    file_path = os.path.join(GIFS_DIR, item_to_remove["filename"])
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                lib = [x for x in lib if x["id"] != gid]
                save_library(lib)
                self.send_json({"ok": True})
            else:
                self.send_error_json("GIF not found", 404)
            return

        if path == "/api/tenor/download":
            body = self.read_json_body()
            url = body.get("url", "").strip()
            title = body.get("title", "").strip() or "Discord_GIF"
            subfolder = body.get("subfolder", "").strip()

            if not url:
                self.send_error_json("Keine URL angegeben", 400)
                return

            cfg = load_config()
            target_base = cfg.get("gif_dir", "").strip()
            if not target_base or not os.path.isdir(target_base):
                target_base = GIFS_DIR

            if subfolder:
                dest_dir = os.path.join(target_base, subfolder)
            else:
                dest_dir = os.path.join(target_base, "Downloads")
            os.makedirs(dest_dir, exist_ok=True)

            safe_title = re.sub(r'[\\/*?:"<>|]+', '', title).strip().replace(' ', '_')
            if not safe_title:
                safe_title = "GIF"
            filename = f"{safe_title}_{str(uuid.uuid4())[:6]}.gif"
            dest_file = os.path.join(dest_dir, filename)

            try:
                ssl_ctx = ssl._create_unverified_context()
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=14, context=ssl_ctx) as resp, open(dest_file, "wb") as out:
                    shutil.copyfileobj(resp, out)
                self.send_json({"ok": True, "path": dest_file, "filename": filename})
            except Exception as ex:
                self.send_error_json(f"Download fehlgeschlagen: {ex}", 500)
            return

        if path == "/api/send":
            # The core action: Copy GIF to clipboard and paste in Discord
            global LAST_TARGET_HWND
            body = self.read_json_body()
            gid = body.get("id")
            cfg = load_config()

            paste_mode = body.get("mode") or cfg.get("paste_mode", "file")
            auto_enter = body.get("auto_send") if "auto_send" in body else cfg.get("auto_send", False)

            all_gifs = get_active_library()
            item = next((x for x in all_gifs if x["id"] == gid), None)
            if not item:
                item = CUSTOM_GIF_INDEX.get(gid)
            if not item:
                item = TENOR_CACHE.get(gid)
            if not item:
                self.send_error_json("GIF not found", 404)
                return

            # Update usage counter
            lib = load_library()
            found_in_lib = False
            for x in lib:
                if x.get("id") == gid:
                    x["use_count"] = x.get("use_count", 0) + 1
                    found_in_lib = True
                    break
            if not found_in_lib and gid:
                lib.append({"id": gid, "use_count": 1})
            save_library(lib)

            # Determine content to copy
            copied = False
            local_path = None
            if item.get("abs_path") and os.path.isfile(item["abs_path"]):
                local_path = item["abs_path"]
            elif item.get("filename"):
                cand = os.path.join(GIFS_DIR, item["filename"])
                if os.path.isfile(cand):
                    local_path = cand

            # If Tenor GIF and file mode requested, download to local temp
            if item.get("is_tenor") and paste_mode == "file" and item.get("url"):
                temp_dir = os.path.join(DATA_DIR, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"{item['id']}.gif")
                if not os.path.isfile(temp_file):
                    try:
                        ssl_ctx = ssl._create_unverified_context()
                        req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                        with urllib.request.urlopen(req, timeout=12, context=ssl_ctx) as resp, open(temp_file, "wb") as out:
                            shutil.copyfileobj(resp, out)
                    except Exception as ex:
                        print(f"[send] Tenor temp download failed: {ex}")
                if os.path.isfile(temp_file):
                    local_path = temp_file

            if paste_mode == "file" and local_path and os.path.isfile(local_path):
                copied = copy_file_to_clipboard(local_path)
            elif item.get("url"):
                copied = copy_text_to_clipboard(item["url"])
            elif local_path and os.path.isfile(local_path):
                copied = copy_file_to_clipboard(local_path)

            if not copied:
                self.send_error_json("Konnte Daten nicht in die Zwischenablage kopieren.")
                return

            # Target Window resolution
            target_hwnd = None
            if LAST_TARGET_HWND and user32.IsWindowVisible(LAST_TARGET_HWND):
                target_hwnd = LAST_TARGET_HWND
            else:
                target_hwnd = find_discord_window()

            if not target_hwnd:
                # Still copied to clipboard successfully!
                self.send_json({
                    "ok": True,
                    "warning": "Discord-Fenster nicht gefunden. Das GIF wurde in die Zwischenablage kopiert. Du kannst es manuell mit Strg+V einfügen."
                })
                return

            # Execute focus switch & paste in separate thread to let HTTP request return cleanly
            def delayed_paste():
                time.sleep(0.05)
                activate_window_and_paste(target_hwnd, send_enter=auto_enter)

            threading.Thread(target=delayed_paste, daemon=True).start()

            self.send_json({
                "ok": True,
                "message": "GIF erfolgreich in Discord eingefügt!"
            })
            return

        self.send_error(404, "Endpoint not found")

# ---------------------------------------------------------------------------
# Window & Starter Helpers
# ---------------------------------------------------------------------------
def find_browser() -> str | None:
    for name in ("msedge", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    return next((c for c in candidates if os.path.exists(c)), None)

def open_app_window(url: str):
    browser = find_browser()
    profile = os.path.join(DATA_DIR, "browser_profile")
    if browser:
        proc = subprocess.Popen([
            browser,
            f"--app={url}",
            "--window-size=1120,740",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
            "--disable-features=msImplicitSignin,msEdgeSyncConsent,msUndersideSignIn",
        ])
        def monitor_browser():
            proc.wait()
            os._exit(0)
        threading.Thread(target=monitor_browser, daemon=True).start()
        return proc
    webbrowser.open(url)
    return None

def run_native_window(url: str, server: ThreadingHTTPServer) -> bool:
    """Open UI in a native Windows desktop window using pywebview (WebView2)."""
    try:
        import webview  # type: ignore
    except ImportError:
        return False

    try:
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        threading.Thread(target=server.serve_forever, daemon=True).start()

        cfg = load_config()
        bg = "#f3f4f8" if cfg.get("theme") == "light" else "#0f1117"
        icon_path = os.path.join(BUNDLE_DIR, "app.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.join(APP_DIR, "app.ico")

        window = webview.create_window(
            f"thomo.ART DiscordGIF v{APP_VERSION}",
            url,
            width=1120,
            height=740,
            min_size=(800, 520),
            background_color=bg,
        )

        global ACTIVE_WEBVIEW_WINDOW
        ACTIVE_WEBVIEW_WINDOW = window

        def on_closing():
            threading.Thread(target=lambda: (time.sleep(0.05), os._exit(0)), daemon=True).start()
            return True

        def on_closed():
            os._exit(0)

        window.events.closing += on_closing
        window.events.closed += on_closed

        webview.start(icon=icon_path if os.path.isfile(icon_path) else None)
        os._exit(0)
    except Exception as exc:
        print("[pywebview] Native window failed, falling back to browser mode:", exc)
        return False

def create_starter_gifs():
    """Create a few friendly starter animated GIFs if library is completely empty."""
    lib = load_library()
    if lib:
        return

    try:
        from PIL import Image, ImageDraw

        starter_defs = [
            ("Lachender Smiley", ["lachen", "funny", "lol", "happy"], (255, 184, 77), ":D"),
            ("Thumbs Up!", ["super", "yes", "top", "nice"], (51, 214, 166), "👍"),
            ("Party Hype", ["party", "dance", "hype", "feier"], (124, 92, 255), "🎉"),
            ("Mind Blown", ["wow", "boom", "mindblown"], (255, 93, 108), "💥"),
        ]

        created_items = []
        for title, tags, color, text in starter_defs:
            gid = str(uuid.uuid4())[:8]
            fname = f"starter_{gid}.gif"
            fpath = os.path.join(GIFS_DIR, fname)

            frames = []
            for i in range(8):
                img = Image.new("RGBA", (140, 140), (23, 26, 35, 255))
                draw = ImageDraw.Draw(img)
                offset = int((i % 4) * 3)
                radius = 45 + (offset if i < 4 else -offset)
                cx, cy = 70, 70
                # Draw outer glow circle
                draw.ellipse(
                    (cx - radius, cy - radius, cx + radius, cy + radius),
                    outline=color,
                    width=4
                )
                frames.append(img)

            frames[0].save(
                fpath,
                save_all=True,
                append_images=frames[1:],
                duration=120,
                loop=0,
                optimize=False
            )

            created_items.append({
                "id": gid,
                "title": title,
                "filename": fname,
                "url": "",
                "tags": tags,
                "favorite": True if "funny" in tags else False,
                "use_count": 0,
                "created_at": int(time.time()),
            })

        save_library(created_items)
        print(f"[init] Created {len(created_items)} starter GIFs.")
    except Exception as ex:
        print("[init] Could not create starter GIFs:", ex)

# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="tA-DiscordGIF Server")
    parser.add_argument("--port", type=int, default=8769, help="Port to listen on (default: 8769)")
    parser.add_argument("--no-window", action="store_true", help="Do not open desktop window")
    parser.add_argument("--browser", action="store_true", help="Open in browser app mode instead of native window")
    args = parser.parse_args()

    cfg = load_config()
    port = args.port or cfg.get("port", 8769)

    # Cleanly terminate any lingering background instance on this port
    try_terminate_previous_instance(port)

    # Single Instance Guard
    MUTEX_NAME = "Global\\thomo_ART_DiscordGIF_SingleInstance"
    h_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        time.sleep(0.5)
        # Check if previous instance terminated
        h_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if kernel32.GetLastError() == 183:
            print("[app] Another instance is already running. Exiting.")
            sys.exit(0)

    create_starter_gifs()

    # Start Hotkey Listener
    t_hotkey = threading.Thread(target=hotkey_thread_worker, daemon=True)
    t_hotkey.start()

    # Start Watchdog for clean shutdown when window is closed
    threading.Thread(target=watchdog, daemon=True).start()

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), AppHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}"
    print(f"=====================================================")
    print(f" tA-DiscordGIF v{APP_VERSION} (thomo.ART)")
    print(f" Web UI running at: {url}")
    print(f" Global Hotkey: Alt + G")
    print(f"=====================================================")

    if not args.no_window:
        if not args.browser and run_native_window(url, server):
            return
        open_app_window(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down tA-DiscordGIF...")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
