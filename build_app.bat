@echo off
setlocal enabledelayedexpansion
title "tA DiscordGIF - Standalone .exe bauen"
chcp 65001 >nul
cd /d "%~dp0"

set "DO_BUMP=1"
for %%a in (%*) do (
    if "%%a"=="--nobump" set "DO_BUMP=0"
)

echo ============================================================
echo   tA DiscordGIF - Erstelle Standalone .exe
echo ============================================================
echo.

if "!DO_BUMP!"=="1" (
    echo [1/3] Backup anlegen und Version um 0.1 erhoehen...
    python bump_version.py --bump
) else (
    echo [1/3] Synchronisiere bestehende Version...
    python bump_version.py --sync
)
if errorlevel 1 (
    echo [FEHLER] Versions-Update fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo [2/3] Pruefe PyInstaller...
python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
    echo Installiere PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo [3/3] Baue Standalone Desktop-App (dist\tA-DiscordGIF.exe)...
python -m PyInstaller --noconfirm --clean --onefile --noconsole ^
    --name "tA-DiscordGIF" ^
    --icon "app.ico" ^
    --add-data "web;web" ^
    --add-data "app.ico;." ^
    server.py

if errorlevel 1 (
    echo.
    echo [FEHLER] PyInstaller-Build fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Fertig! Die Datei "dist\tA-DiscordGIF.exe" wurde erfolgreich erstellt.
echo ============================================================
echo.
pause
