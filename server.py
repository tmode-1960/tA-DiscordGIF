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

APP_VERSION = "1.2"
IS_FROZEN = getattr(sys, "frozen", False)
BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(os.path.abspath(sys.executable)) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BUNDLE_DIR, "web") if os.path.isdir(os.path.join(BUNDLE_DIR, "web")) else os.path.join(APP_DIR, "web")

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
    "language": "de",
    "auto_send": False,
    "paste_mode": "file",  # "file" or "url"
    "hotkey": "Alt+G",
    "gif_dir": "",
    "tenor_api_key": "",
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
                    clean_name = re.sub(r"[-_.]+", " ", raw_name).strip()
                    title = clean_name.title() if clean_name else "GIF"

                    # Generate searchable tags from relative path and name
                    words = set(re.findall(r"\w+", rel.lower()))
                    tags = [w for w in words if len(w) > 1 and not w.isdigit()]

                    gid = "ext_" + hashlib.sha1(rel.encode("utf-8", "ignore")).hexdigest()[:10]
                    item = {
                        "id": gid,
                        "title": title,
                        "category": category,
                        "filename": None,
                        "abs_path": full_path,
                        "rel_path": rel,
                        "url": f"/api/gif_file?id={gid}",
                        "tags": sorted(tags),
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

def select_folder_dialog(initial_dir: str = "") -> str | None:
    """Open native Windows directory selection dialog."""
    global ACTIVE_WEBVIEW_WINDOW
    if ACTIVE_WEBVIEW_WINDOW:
        try:
            import webview
            res = ACTIVE_WEBVIEW_WINDOW.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=initial_dir if os.path.isdir(initial_dir) else ""
            )
            if res:
                return res[0] if isinstance(res, (list, tuple)) else str(res)
            return None
        except Exception as ex:
            print("[dialog] pywebview dialog error:", ex)

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        selected = filedialog.askdirectory(
            initialdir=initial_dir if os.path.isdir(initial_dir) else None,
            title="GIF-Verzeichnis auswählen"
        )
        root.destroy()
        return selected if selected else None
    except Exception as ex:
        print("[dialog] tkinter dialog error:", ex)

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
