"""Version manager, backup creator and bumper for tA-DiscordGIF.
Modeled after the tA-MusicMaker workflow.

Usage:
    python bump_version.py --bump       # Increments version by 0.1 and creates a backup
    python bump_version.py --backup     # Creates a backup snapshot in _backups/
    python bump_version.py --set 0.2    # Sets specific version
    python bump_version.py --sync       # Syncs current version across all project files
    python bump_version.py              # Defaults to --bump
"""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
import os
import re
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")
SERVER_FILE = os.path.join(BASE_DIR, "server.py")
HTML_FILE = os.path.join(BASE_DIR, "web", "index.html")
BACKUP_DIR = os.path.join(BASE_DIR, "_backups")


def create_backup(label: str = "auto") -> list[str]:
    """Creates a timestamped snapshot of core source files in _backups/."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backed_up = []

    files_to_backup = [
        "server.py",
        "version.txt",
        "build_app.bat",
        os.path.join("web", "index.html"),
        os.path.join("web", "style.css"),
        os.path.join("web", "app.js"),
        os.path.join("web", "i18n.js"),
    ]

    for rel_path in files_to_backup:
        src = os.path.join(BASE_DIR, rel_path)
        if os.path.isfile(src):
            basename = os.path.basename(rel_path)
            name, ext = os.path.splitext(basename)
            dst_name = f"{name}-{ts}{ext}"
            dst = os.path.join(BACKUP_DIR, dst_name)
            shutil.copy2(src, dst)
            backed_up.append(dst_name)

    print(f"[_backups] {len(backed_up)} Dateien gesichert nach _backups/ (Zeitstempel: {ts})")
    return backed_up


def read_version() -> str:
    if os.path.isfile(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as fh:
            v = fh.read().strip()
            if v:
                return v
    return "0.1"


def write_version(ver: str) -> None:
    with open(VERSION_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(ver + "\n")


def update_server_py(ver: str) -> None:
    if not os.path.isfile(SERVER_FILE):
        return
    with open(SERVER_FILE, "r", encoding="utf-8") as fh:
        content = fh.read()

    if re.search(r'APP_VERSION\s*=\s*"[^"]*"', content):
        content = re.sub(r'APP_VERSION\s*=\s*"[^"]*"', f'APP_VERSION = "{ver}"', content, count=1)
    else:
        content = f'APP_VERSION = "{ver}"\n' + content

    with open(SERVER_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def update_html(ver: str) -> None:
    if not os.path.isfile(HTML_FILE):
        return
    with open(HTML_FILE, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Update <title>
    content = re.sub(
        r"<title>.*?</title>",
        f"<title>thomo.ART DiscordGIF v{ver}</title>",
        content,
        count=1,
    )

    # Update header version badge
    content = re.sub(
        r'<span class="brand-version"[^>]*>.*?</span>',
        f'<span class="brand-version" id="brandVersion">v{ver}</span>',
        content,
        count=1,
    )

    # Update asset query strings ?v=...
    content = re.sub(r'(\.(?:css|js))\?v=[^"\'>\s]*', f'\\1?v={ver}', content)

    with open(HTML_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def sync_all(ver: str) -> None:
    write_version(ver)
    update_server_py(ver)
    update_html(ver)
    print(f"[Version] Synchronisiert auf v{ver}")


def bump_version(step: str = "0.1") -> str:
    # Vor dem Bumpen immer ein Backup erstellen!
    create_backup(label="pre_bump")

    cur = read_version()
    try:
        d = Decimal(cur) + Decimal(step)
        # Format with 1 decimal place if clean (0.2, 0.3)
        new_v = f"{d:.1f}" if d == d.quantize(Decimal("0.1")) else f"{d:.2f}"
    except Exception:
        new_v = "0.2"

    sync_all(new_v)
    return new_v


def main():
    parser = argparse.ArgumentParser(description="tA-DiscordGIF Version Manager")
    parser.add_argument("--bump", action="store_true", help="Increment version by 0.1 (with backup)")
    parser.add_argument("--backup", action="store_true", help="Create backup snapshot in _backups/")
    parser.add_argument("--set", type=str, dest="set_ver", help="Set explicit version")
    parser.add_argument("--sync", action="store_true", help="Sync existing version.txt")
    args = parser.parse_args()

    if args.backup:
        create_backup()
    elif args.set_ver:
        create_backup(label="pre_set")
        sync_all(args.set_ver)
    elif args.sync:
        cur = read_version()
        sync_all(cur)
    else:
        # Default behavior: bump by 0.1 with backup
        bump_version()


if __name__ == "__main__":
    main()
