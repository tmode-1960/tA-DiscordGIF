# Projekt-Richtlinien für tA-DiscordGIF

## Automatischer Version-Bump und Build
Bei jeder Änderung am Projekt (Code, Templates, Styles oder Workflows):
1. Versionsnummer automatisch um 0.1 erhöhen und Backup erstellen:
   ```powershell
   python bump_version.py --bump
   ```
2. Automatisch einen neuen Standalone-Build erstellen:
   ```powershell
   python -m PyInstaller --noconfirm --clean --onefile --noconsole --name "tA-DiscordGIF" --icon "app.ico" --add-data "web;web" --add-data "workflows;workflows" --add-data "app.ico;." server.py
   ```
   Die resultierende Binary liegt in `dist\tA-DiscordGIF.exe`.
