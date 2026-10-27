"use strict";

// UI translations for tA-DiscordGIF (Deutsch & English)
const I18N = {
  de: {
    _name: "Deutsch",
    connecting: "Discord wird gesucht...",
    discordReady: "Discord bereit",
    discordNotFound: "Discord nicht im Hintergrund erkannt",
    serverOffline: "Server nicht erreichbar",
    hotkeyTitle: "Globales Tastenkürzel zum Aufrufen",
    refreshTitle: "Aktualisieren",
    settings: "⚙ Einstellungen",
    settingsTitle: "⚙ EINSTELLUNGEN",

    // Search & Filter
    searchAndFilter: "Suche & Filter",
    searchPlaceholder: "Suche nach Name oder Tag...",
    tabAll: "Alle",
    tabFav: "⭐ Favoriten",
    tabSourceLocal: "📁 Meine GIFs",
    tabSourceTenor: "🌐 Discord / Tenor",
    tenorSearchPh: "Discord / Tenor durchsuchen (z. B. dance, lol, cat)...",
    tenorCategories: "Discord Trend-Kategorien",
    downloadToFolder: "In Ordner speichern",

    // Discord Behavior
    discordBehavior: "Discord-Verhalten",
    pasteMode: "Einfüge-Modus",
    pasteModeFile: "Datei (Dateiupload)",
    pasteModeUrl: "Link (URL)",
    pasteModeFileTip: "Sendet echte GIF-Datei (Dateiupload)",
    pasteModeUrlTip: "Sendet direkte URL als Text",
    chkAutoSend: "Sofort mit Enter absenden",
    tipHotkey: "Drücke Alt + G im Discord-Chat, wähle ein GIF, und es wird direkt eingefügt!",

    // Add GIF
    addGif: "GIF Hinzufügen",
    dropPrompt: "GIF hierher ziehen oder klicken",
    dropChange: "Klicken zum Ändern",
    orWebUrl: "Oder Web-URL (Tenor, Giphy, Direct)",
    urlPlaceholder: "https://.../beispiel.gif",
    titleOpt: "Titel (optional)",
    titlePlaceholder: "z. B. Haha Lachen",
    tagsLabel: "Tags (kommagetrennt)",
    tagsPlaceholder: "z. B. lachen, lol, meme",
    btnSaveGif: "GIF Speichern",
    savingGif: "Wird gespeichert...",

    // Gallery
    galleryTitle: "GIF Sammlung",
    btnReload: "Ordner neu laden",
    countSuffix: "GIFs",
    countSingle: "GIF",
    emptyTitle: "Keine passenden GIFs gefunden.",
    emptyHint: "Ziehe links eine Datei hinein oder ändere den Suchbegriff.",
    insertBtn: "⚡ In Discord einfügen",
    favoriteTitle: "Favorisieren",
    editTitle: "✏️ GIF Bearbeiten",
    editBtn: "Bearbeiten",
    deleteTitle: "Löschen",
    deleteConfirm: "Möchtest du \"{title}\" wirklich löschen?",

    // Settings Dialog
    cfgLang: "Language / Sprache",
    cfgTheme: "Theme / Farbschema",
    themeDark: "Dark (Standard)",
    themeLight: "Light",
    cfgPasteMode: "Standard Einfüge-Modus",
    cfgGifDir: "GIF-Verzeichnis (Ordner mit Unterordnern)",
    cfgGifDirPh: "Standard (App-Daten) oder z. B. D:\\MeineGIFs",
    btnBrowse: "📁 Durchsuchen...",
    btnResetFolder: "Zurücksetzen",
    catGeneral: "Allgemein",
    creditsTitle: "Copyright & Credits",
    creditsText: "I would like to thank CodexMundi for their support and for testing the app.",
    creditsCopy: "© 2026 thomo.ART • DiscordGIF Edition",
    cancel: "Abbrechen",
    save: "Speichern",

    // Toasts
    toastRefresh: "Sammlung aktualisiert",
    toastReloaded: "Ordner neu eingelesen ({count} GIFs)",
    toastDownloading: "Lade GIF in deinen Ordner herunter...",
    toastDownloaded: "GIF erfolgreich in deinen Ordner gespeichert!",
    toastFileOnlyGif: "Bitte nur animierte .gif-Dateien auswählen!",
    toastNoFileOrUrl: "Bitte wähle eine GIF-Datei aus oder gib eine URL ein.",
    toastSaved: "GIF erfolgreich hinzugefügt!",
    toastEditSaved: "GIF erfolgreich aktualisiert!",
    toastDeleted: "GIF gelöscht",
    toastInserting: "Füge \"{title}\" in Discord ein...",
    toastInserted: "⚡ Erfolgreich in Discord eingefügt!",
    toastSaveSettings: "Einstellungen gespeichert",
  },

  en: {
    _name: "English",
    connecting: "Looking for Discord...",
    discordReady: "Discord ready",
    discordNotFound: "Discord not detected in background",
    serverOffline: "Server offline",
    hotkeyTitle: "Global shortcut to open picker",
    refreshTitle: "Refresh",
    settings: "⚙ Settings",
    settingsTitle: "⚙ SETTINGS",

    // Search & Filter
    searchAndFilter: "Search & Filter",
    searchPlaceholder: "Search by name or tag...",
    tabAll: "All",
    tabFav: "⭐ Favorites",
    tabSourceLocal: "📁 My GIFs",
    tabSourceTenor: "🌐 Discord / Tenor",
    tenorSearchPh: "Search Discord / Tenor (e.g. dance, lol, cat)...",
    tenorCategories: "Discord Trending Categories",
    downloadToFolder: "Save to folder",

    // Discord Behavior
    discordBehavior: "Discord Behavior",
    pasteMode: "Paste Mode",
    pasteModeFile: "File (Upload)",
    pasteModeUrl: "Link (URL)",
    pasteModeFileTip: "Uploads real GIF file (File upload)",
    pasteModeUrlTip: "Sends direct URL as text",
    chkAutoSend: "Auto-send with Enter immediately",
    tipHotkey: "Press Alt + G in Discord chat, click a GIF, and it pastes right in!",

    // Add GIF
    addGif: "Add GIF",
    dropPrompt: "Drop GIF here or click to browse",
    dropChange: "Click to change",
    orWebUrl: "Or Web URL (Tenor, Giphy, Direct)",
    urlPlaceholder: "https://.../example.gif",
    titleOpt: "Title (optional)",
    titlePlaceholder: "e.g. Haha Laugh",
    tagsLabel: "Tags (comma-separated)",
    tagsPlaceholder: "e.g. laugh, lol, meme",
    btnSaveGif: "Save GIF",
    savingGif: "Saving...",

    // Gallery
    galleryTitle: "GIF Collection",
    btnReload: "Reload folder",
    countSuffix: "GIFs",
    countSingle: "GIF",
    emptyTitle: "No matching GIFs found.",
    emptyHint: "Drag a file on the left or change the search query.",
    insertBtn: "⚡ Insert in Discord",
    favoriteTitle: "Toggle Favorite",
    editTitle: "✏️ Edit GIF",
    editBtn: "Edit",
    deleteTitle: "Delete",
    deleteConfirm: "Do you really want to delete \"{title}\"?",

    // Settings Dialog
    cfgLang: "Language",
    cfgTheme: "Theme",
    themeDark: "Dark (Default)",
    themeLight: "Light",
    cfgPasteMode: "Default Paste Mode",
    cfgGifDir: "GIF Directory (Folder with subfolders)",
    cfgGifDirPh: "Default (App data) or e.g. D:\\MyGIFs",
    btnBrowse: "📁 Browse...",
    btnResetFolder: "Reset",
    catGeneral: "General",
    creditsTitle: "Copyright & Credits",
    creditsText: "I would like to thank CodexMundi for their support and for testing the app.",
    creditsCopy: "© 2026 thomo.ART • DiscordGIF Edition",
    cancel: "Cancel",
    save: "Save",

    // Toasts
    toastRefresh: "Collection refreshed",
    toastReloaded: "Reloaded {count} GIFs",
    toastDownloading: "Downloading GIF to your folder...",
    toastDownloaded: "GIF successfully saved to your folder!",
    toastFileOnlyGif: "Please select animated .gif files only!",
    toastNoFileOrUrl: "Please select a GIF file or enter a URL.",
    toastSaved: "GIF added successfully!",
    toastEditSaved: "GIF updated successfully!",
    toastDeleted: "GIF deleted",
    toastInserting: "Inserting \"{title}\" into Discord...",
    toastInserted: "⚡ Inserted into Discord successfully!",
    toastSaveSettings: "Settings saved",
  },
};

let CURRENT_LANG = "en";

function setLanguage(lang) {
  if (I18N[lang]) {
    CURRENT_LANG = lang;
  } else {
    CURRENT_LANG = "en";
  }
  document.documentElement.lang = CURRENT_LANG;
  try {
    localStorage.setItem("tadiscordgif.lang", CURRENT_LANG);
  } catch (e) {}
  applyI18n();
}

function t(key, vars) {
  let s = (I18N[CURRENT_LANG] && I18N[CURRENT_LANG][key]) ?? I18N.en[key] ?? key;
  for (const [k, v] of Object.entries(vars || {})) {
    s = s.replace(new RegExp(`\\{${k}\\}`, "g"), v);
  }
  return s;
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
}
