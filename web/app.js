// tA-DiscordGIF Frontend Application Logic
// Inspired by the thomo.ART UI Architecture

(function () {
  "use strict";

  // State
  let gifs = [];
  let currentSource = "local"; // "local" or "tenor"
  let tenorGifs = [];
  let tenorLoading = false;
  let activeFilter = "all";
  let searchQuery = "";
  let searchDebounceTimer = null;
  let pasteMode = "file";
  let autoSend = false;
  let selectedFileData = null;
  let toastTimer = null;

  const TENOR_CATEGORIES = [
    { id: "", label: "🔥 Trending" },
    { id: "dance", label: "💃 Dance" },
    { id: "applause", label: "👏 Applause" },
    { id: "facepalm", label: "🤦 Facepalm" },
    { id: "party", label: "🎉 Party" },
    { id: "laugh", label: "😂 Laugh" },
    { id: "hug", label: "🤗 Hug" },
    { id: "cat", label: "🐱 Cats" },
    { id: "anime", label: "✨ Anime" },
    { id: "spooky", label: "💀 Spooky" },
    { id: "yes", label: "👍 Yes" },
    { id: "no", label: "🙅 No" },
  ];

  // DOM Elements
  const sourceSeg = document.getElementById("sourceSeg");
  const statusEl = document.getElementById("discordStatus");
  const statusTextEl = document.getElementById("statusText");
  const hotkeyBadge = document.getElementById("hotkeyBadge");
  const searchInput = document.getElementById("searchInput");
  const categoryTabs = document.getElementById("categoryTabs");
  const gifGrid = document.getElementById("gifGrid");
  const gifCount = document.getElementById("gifCount");
  const pasteModeSeg = document.getElementById("pasteModeSeg");
  const chkAutoSend = document.getElementById("chkAutoSend");
  const dropZone = document.getElementById("dropZone");
  const dropPrompt = document.getElementById("dropPrompt");
  const fileInput = document.getElementById("fileInput");
  const inputUrl = document.getElementById("inputUrl");
  const inputTitle = document.getElementById("inputTitle");
  const inputTags = document.getElementById("inputTags");
  const btnSaveGif = document.getElementById("btnSaveGif");
  const btnRefresh = document.getElementById("btnRefresh");
  const btnReloadGallery = document.getElementById("btnReloadGallery");
  const btnSettings = document.getElementById("btnSettings");
  const dlgSettings = document.getElementById("settings");
  const cfgLang = document.getElementById("cfgLang");
  const cfgTheme = document.getElementById("cfgTheme");
  const cfgPasteMode = document.getElementById("cfgPasteMode");
  const cfgGifDir = document.getElementById("cfgGifDir");
  const btnBrowseFolder = document.getElementById("btnBrowseFolder");
  const btnResetFolder = document.getElementById("btnResetFolder");
  const cfgSave = document.getElementById("cfgSave");
  const dlgEdit = document.getElementById("editModal");
  const editPreview = document.getElementById("editPreview");
  const editTitleInput = document.getElementById("editTitleInput");
  const editTagsInput = document.getElementById("editTagsInput");
  const btnSaveEdit = document.getElementById("btnSaveEdit");
  let currentlyEditingGif = null;
  const toastEl = document.getElementById("toast");

  // AI Studio Elements & State
  let aiSelectedImageData = null;
  let aiWorkflows = [];
  let aiLatestGif = null;
  let aiProgressPollTimer = null;
  let aiDownloadPollTimer = null;
  let comfyOnline = false;
  let comfyInstalledModels = [];

  const searchBoxContainer = document.getElementById("searchBoxContainer");
  const behaviorCard = document.getElementById("behaviorCard");
  const addGifCard = document.getElementById("addGifCard");
  const aiSettingsCard = document.getElementById("aiSettingsCard");
  const galleryCard = document.getElementById("galleryCard");
  const aiStudioCard = document.getElementById("aiStudioCard");

  const aiModelSelect = document.getElementById("aiModelSelect");
  const aiResolutionSelect = document.getElementById("aiResolutionSelect");
  const aiMotionRange = document.getElementById("aiMotionRange");
  const aiMotionVal = document.getElementById("aiMotionVal");
  const aiFramesSelect = document.getElementById("aiFramesSelect");
  const aiFpsSelect = document.getElementById("aiFpsSelect");
  const chkAiPingPong = document.getElementById("chkAiPingPong");

  const aiStatusBadge = document.getElementById("aiStatusBadge");
  const aiStatusDot = document.getElementById("aiStatusDot");
  const aiStatusText = document.getElementById("aiStatusText");
  const aiOfflineBanner = document.getElementById("aiOfflineBanner");
  const btnCheckComfy = document.getElementById("btnCheckComfy");
  const btnOpenComfyHelp = document.getElementById("btnOpenComfyHelp");

  const aiModelMissingBanner = document.getElementById("aiModelMissingBanner");
  const aiModelMissingTitle = document.getElementById("aiModelMissingTitle");
  const aiModelMissingText = document.getElementById("aiModelMissingText");
  const aiRequiredFilesList = document.getElementById("aiRequiredFilesList");
  const btnDownloadAllModels = document.getElementById("btnDownloadAllModels");
  const btnDownloadModel = document.getElementById("btnDownloadModel");
  const aiDownloadProgressBox = document.getElementById("aiDownloadProgressBox");
  const aiDownloadProgressBar = document.getElementById("aiDownloadProgressBar");
  const aiDownloadProgressText = document.getElementById("aiDownloadProgressText");

  const aiDropZone = document.getElementById("aiDropZone");
  const aiDropPlaceholder = document.getElementById("aiDropPlaceholder");
  const aiSourcePreview = document.getElementById("aiSourcePreview");
  const aiFileInput = document.getElementById("aiFileInput");
  const aiImageInfo = document.getElementById("aiImageInfo");
  const btnClearAiImage = document.getElementById("btnClearAiImage");

  const aiPromptInput = document.getElementById("aiPromptInput");
  const aiPromptPills = document.getElementById("aiPromptPills");
  const aiTitleInput = document.getElementById("aiTitleInput");
  const btnGenerateAi = document.getElementById("btnGenerateAi");
  const btnCancelAi = document.getElementById("btnCancelAi");

  const aiProgressCard = document.getElementById("aiProgressCard");
  const aiProgressText = document.getElementById("aiProgressText");
  const aiProgressPercent = document.getElementById("aiProgressPercent");
  const aiProgressBar = document.getElementById("aiProgressBar");

  const aiResultCard = document.getElementById("aiResultCard");
  const aiResultImg = document.getElementById("aiResultImg");
  const aiResultTitle = document.getElementById("aiResultTitle");
  const aiResultInfo = document.getElementById("aiResultInfo");
  const btnSendAiToDiscord = document.getElementById("btnSendAiToDiscord");
  const btnViewInCollection = document.getElementById("btnViewInCollection");

  const cfgComfyUrl = document.getElementById("cfgComfyUrl");
  const cfgComfyDir = document.getElementById("cfgComfyDir");
  const btnTestComfy = document.getElementById("btnTestComfy");
  const btnBrowseComfyFolder = document.getElementById("btnBrowseComfyFolder");

  // Init
  init();

  async function init() {
    // Initial language setup from localStorage or default
    const savedLang = localStorage.getItem("tadiscordgif.lang") || "en";
    if (typeof setLanguage === "function") {
      setLanguage(savedLang);
    }

    setupEventListeners();
    await loadSettings();
    await loadGifs();
    await checkStatus();

    // Periodic status check for Discord focus
    setInterval(checkStatus, 3000);

    // Heartbeat ping so server terminates cleanly when window closes
    setInterval(() => {
      fetch("/api/ping").catch(() => {});
    }, 2000);

    // Notify server immediately on window close
    const notifyShutdown = () => {
      try {
        navigator.sendBeacon("/api/shutdown");
      } catch (e) {
        try {
          fetch("/api/shutdown", { method: "POST", keepalive: true }).catch(() => {});
        } catch (e2) {}
      }
    };

    window.addEventListener("beforeunload", notifyShutdown);
    window.addEventListener("unload", notifyShutdown);
    window.addEventListener("pagehide", notifyShutdown);
  }

  function setupEventListeners() {
    // Source Segmented Control (Local vs Discord/Tenor vs AI Studio)
    if (sourceSeg) {
      sourceSeg.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", async () => {
          sourceSeg.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          currentSource = btn.dataset.source;
          searchInput.value = "";
          searchQuery = "";

          if (currentSource === "ai") {
            if (searchBoxContainer) searchBoxContainer.style.display = "none";
            if (categoryTabs) categoryTabs.style.display = "none";
            if (behaviorCard) behaviorCard.style.display = "none";
            if (addGifCard) addGifCard.style.display = "none";
            if (aiSettingsCard) aiSettingsCard.style.display = "block";
            if (galleryCard) galleryCard.style.display = "none";
            if (aiStudioCard) aiStudioCard.style.display = "flex";
            await checkComfyStatus();
          } else {
            if (searchBoxContainer) searchBoxContainer.style.display = "";
            if (categoryTabs) categoryTabs.style.display = "";
            if (behaviorCard) behaviorCard.style.display = "";
            if (addGifCard) addGifCard.style.display = "";
            if (aiSettingsCard) aiSettingsCard.style.display = "none";
            if (galleryCard) galleryCard.style.display = "flex";
            if (aiStudioCard) aiStudioCard.style.display = "none";

            if (currentSource === "tenor") {
              searchInput.placeholder = t("tenorSearchPh");
              updateCategoryTabs();
              if (tenorGifs.length === 0) {
                await loadTenorGifs();
              } else {
                renderGallery();
              }
            } else {
              searchInput.placeholder = t("searchPlaceholder");
              updateCategoryTabs();
              renderGallery();
            }
          }
        });
      });
    }

    // Search input
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      if (currentSource === "tenor") {
        if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
          loadTenorGifs(searchQuery);
        }, 400);
      } else {
        renderGallery();
      }
    });

    // Refresh button (Header)
    btnRefresh.addEventListener("click", async () => {
      await loadGifs();
      await checkStatus();
      showToast(t("toastReloaded", { count: gifs.length }), "ok");
    });

    // Reload Gallery Button
    if (btnReloadGallery) {
      btnReloadGallery.addEventListener("click", async () => {
        const icon = btnReloadGallery.querySelector(".reload-icon");
        if (icon) icon.style.animation = "spin 0.6s linear infinite";
        btnReloadGallery.disabled = true;

        try {
          await loadGifs();
          await checkStatus();
          showToast(t("toastReloaded", { count: gifs.length }), "ok");
        } finally {
          setTimeout(() => {
            if (icon) icon.style.animation = "";
            btnReloadGallery.disabled = false;
          }, 350);
        }
      });
    }

    // Settings Modal Open
    btnSettings.addEventListener("click", () => {
      const curTheme = document.documentElement.getAttribute("data-theme") || "dark";
      cfgLang.value = CURRENT_LANG;
      cfgTheme.value = curTheme;
      cfgPasteMode.value = pasteMode;
      dlgSettings.showModal();
    });

    // Browse folder button
    if (btnBrowseFolder) {
      btnBrowseFolder.addEventListener("click", async () => {
        btnBrowseFolder.disabled = true;
        try {
          const res = await fetch("/api/select_folder", { method: "POST" });
          const data = await res.json();
          if (data.ok && data.path) {
            cfgGifDir.value = data.path;
          }
        } catch (e) {
          console.warn("Folder picker error:", e);
        } finally {
          btnBrowseFolder.disabled = false;
        }
      });
    }

    // Reset folder button
    if (btnResetFolder) {
      btnResetFolder.addEventListener("click", () => {
        cfgGifDir.value = "";
      });
    }

    // Browse ComfyUI folder button
    if (btnBrowseComfyFolder) {
      btnBrowseComfyFolder.addEventListener("click", async () => {
        btnBrowseComfyFolder.disabled = true;
        try {
          const res = await fetch("/api/select_folder", { method: "POST" });
          const data = await res.json();
          if (data.ok && data.path) {
            cfgComfyDir.value = data.path;
          }
        } catch (e) {
          console.warn("Folder picker error:", e);
        } finally {
          btnBrowseComfyFolder.disabled = false;
        }
      });
    }

    // Test ComfyUI connection button
    if (btnTestComfy) {
      btnTestComfy.addEventListener("click", async () => {
        const testUrl = cfgComfyUrl ? cfgComfyUrl.value.trim() : "";
        btnTestComfy.disabled = true;
        btnTestComfy.textContent = "⏳...";
        try {
          const res = await fetch(`/api/ai/status?url=${encodeURIComponent(testUrl)}`);
          const data = await res.json();
          if (data.online) {
            showToast(t("toastComfyConnected"), "ok");
          } else {
            showToast(t("toastComfyOfflineUrl"), "err");
          }
        } catch (e) {
          showToast(t("toastConnectionError"), "err");
        } finally {
          btnTestComfy.disabled = false;
          btnTestComfy.textContent = "⚡ Test";
        }
      });
    }

    // Theme change inside Settings
    cfgTheme.addEventListener("change", (e) => {
      applyTheme(e.target.value);
    });

    // Language dropdown change inside Settings
    cfgLang.addEventListener("change", (e) => {
      setLanguage(e.target.value);
      updateCategoryTabs();
      renderGallery();
    });

    // Save Settings
    cfgSave.addEventListener("click", (e) => {
      e.preventDefault();
      const newLang = cfgLang.value;
      const newTheme = cfgTheme.value;
      const newPasteMode = cfgPasteMode.value;
      const newGifDir = cfgGifDir ? cfgGifDir.value.trim() : "";
      const newComfyUrl = cfgComfyUrl ? cfgComfyUrl.value.trim() : "";
      const newComfyDir = cfgComfyDir ? cfgComfyDir.value.trim() : "";

      // Apply
      setLanguage(newLang);
      applyTheme(newTheme);

      pasteMode = newPasteMode;
      pasteModeSeg.querySelectorAll("button").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.mode === pasteMode);
      });

      // Save to server and refresh GIFs
      saveSettingsBatch({
        language: newLang,
        theme: newTheme,
        paste_mode: newPasteMode,
        auto_send: autoSend,
        gif_dir: newGifDir,
        comfyui_url: newComfyUrl,
        comfyui_dir: newComfyDir,
      }).then(() => {
        loadGifs();
        if (currentSource === "ai") checkComfyStatus();
      });

      dlgSettings.close();
      showToast(t("toastSaveSettings"), "ok");
    });

    // Save Edit Modal
    if (btnSaveEdit) {
      btnSaveEdit.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!currentlyEditingGif) return;

        const newTitle = editTitleInput.value.trim() || currentlyEditingGif.title;
        const newTagsRaw = editTagsInput.value.trim();
        const newTags = newTagsRaw ? newTagsRaw.split(",").map((t) => t.trim().toLowerCase()).filter(Boolean) : [];

        currentlyEditingGif.title = newTitle;
        currentlyEditingGif.tags = newTags;

        try {
          await fetch("/api/gifs/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              id: currentlyEditingGif.id,
              title: newTitle,
              tags: newTags,
            }),
          });
          showToast(t("toastEditSaved"), "ok");
          updateCategoryTabs();
          renderGallery();
        } catch (err) {
          console.warn("Could not save edit:", err);
        } finally {
          dlgEdit.close();
          currentlyEditingGif = null;
        }
      });
    }

    // Paste Mode Segmented Control
    pasteModeSeg.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        pasteModeSeg.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        pasteMode = btn.dataset.mode;
        saveSetting("paste_mode", pasteMode);
      });
    });

    // Auto Send Checkbox
    chkAutoSend.addEventListener("change", (e) => {
      autoSend = e.target.checked;
      saveSetting("auto_send", autoSend);
    });

    // Drag & Drop
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });

    // Save GIF button
    btnSaveGif.addEventListener("click", saveNewGif);

    // Setup AI Studio events
    setupAiStudioEventListeners();
  }

  function setupAiStudioEventListeners() {
    // Motion slider
    if (aiMotionRange && aiMotionVal) {
      aiMotionRange.addEventListener("input", (e) => {
        aiMotionVal.textContent = e.target.value;
      });
    }

    // Prompt pills
    if (aiPromptPills) {
      aiPromptPills.querySelectorAll(".pill-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (aiPromptInput) {
            aiPromptInput.value = btn.dataset.prompt;
            aiPromptInput.focus();
          }
        });
      });
    }

    // Image dropzone click & drag
    if (aiDropZone && aiFileInput) {
      aiDropZone.addEventListener("click", () => aiFileInput.click());

      aiDropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        aiDropZone.style.borderColor = "var(--accent)";
      });

      aiDropZone.addEventListener("dragleave", () => {
        aiDropZone.style.borderColor = "";
      });

      aiDropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        aiDropZone.style.borderColor = "";
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          handleAiImageFile(e.dataTransfer.files[0]);
        }
      });

      aiFileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
          handleAiImageFile(e.target.files[0]);
        }
      });
    }

    // Clear image
    if (btnClearAiImage) {
      btnClearAiImage.addEventListener("click", (e) => {
        e.stopPropagation();
        clearAiImage();
      });
    }

    // Model selection change
    if (aiModelSelect) {
      aiModelSelect.addEventListener("change", () => checkComfyStatus());
    }

    // Check ComfyUI button in banner
    if (btnCheckComfy) {
      btnCheckComfy.addEventListener("click", () => checkComfyStatus());
    }

    // Help button in banner
    if (btnOpenComfyHelp) {
      btnOpenComfyHelp.addEventListener("click", () => {
        alert(t("comfyHelpText"));
      });
    }

    // Generate AI GIF button
    if (btnGenerateAi) {
      btnGenerateAi.addEventListener("click", startAiGeneration);
    }

    // Cancel AI button
    if (btnCancelAi) {
      btnCancelAi.addEventListener("click", cancelAiGeneration);
    }

    // Send AI to Discord button
    if (btnSendAiToDiscord) {
      btnSendAiToDiscord.addEventListener("click", () => {
        if (aiLatestGif) {
          sendGif(aiLatestGif);
        }
      });
    }

    // View in Collection
    if (btnViewInCollection) {
      btnViewInCollection.addEventListener("click", () => {
        const localBtn = sourceSeg.querySelector('[data-source="local"]');
        if (localBtn) localBtn.click();
      });
    }
  }

  function handleAiImageFile(file) {
    if (!file.type.startsWith("image/")) {
      showToast(t("toastFileOnlyImage"), "err");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      aiSelectedImageData = e.target.result;
      if (aiSourcePreview) {
        aiSourcePreview.src = aiSelectedImageData;
        aiSourcePreview.style.display = "block";
      }
      if (aiDropPlaceholder) aiDropPlaceholder.style.display = "none";
      if (btnClearAiImage) btnClearAiImage.style.display = "inline-block";
      if (aiImageInfo) aiImageInfo.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
    };
    reader.readAsDataURL(file);
  }

  function clearAiImage() {
    aiSelectedImageData = null;
    if (aiFileInput) aiFileInput.value = "";
    if (aiSourcePreview) {
      aiSourcePreview.src = "";
      aiSourcePreview.style.display = "none";
    }
    if (aiDropPlaceholder) aiDropPlaceholder.style.display = "block";
    if (btnClearAiImage) btnClearAiImage.style.display = "none";
    if (aiImageInfo) aiImageInfo.textContent = "";
  }

  async function checkComfyStatus(overrideUrl) {
    const url = overrideUrl || (cfgComfyUrl ? cfgComfyUrl.value.trim() : "");
    if (aiStatusText) aiStatusText.textContent = t("aiStatusChecking");
    if (aiStatusBadge) aiStatusBadge.className = "ai-status-badge";

    try {
      const res = await fetch(`/api/ai/status?url=${encodeURIComponent(url)}`);
      const data = await res.json();

      if (data.online) {
        comfyOnline = true;
        if (aiStatusBadge) aiStatusBadge.className = "ai-status-badge online";
        let gpuName = `ComfyUI ${t("statusReady")}`;
        if (data.devices && data.devices.length > 0 && data.devices[0].name) {
          gpuName = `${data.devices[0].name.replace("NVIDIA GeForce ", "")} ${t("statusReady")}`;
        }
        if (aiStatusText) aiStatusText.textContent = `🟢 ${gpuName}`;
        if (aiOfflineBanner) aiOfflineBanner.style.display = "none";

        // Workflows
        aiWorkflows = data.workflows || [];
        if (aiModelSelect && aiWorkflows.length > 0) {
          const prevVal = aiModelSelect.value;
          aiModelSelect.innerHTML = aiWorkflows
            .map((wf) => `<option value="${escapeHtml(wf.id)}">${escapeHtml(wf.name)} (${escapeHtml(wf.vram_rec)})</option>`)
            .join("");
          if (prevVal && aiWorkflows.some((w) => w.id === prevVal)) {
            aiModelSelect.value = prevVal;
          }
        }

        // Check required models/files
        comfyInstalledModels = data.installed_models || [];
        const currentWf = aiWorkflows.find((w) => w.id === (aiModelSelect ? aiModelSelect.value : "minimax_h3")) || aiWorkflows[0];

        if (currentWf) {
          let filesWithStatus = [];
          if (Array.isArray(currentWf.required_files) && currentWf.required_files.length > 0) {
            filesWithStatus = currentWf.required_files.map((rf) => {
              const fn = (rf.filename || "").toLowerCase();
              const alts = Array.isArray(rf.alternatives) ? rf.alternatives.map((a) => a.toLowerCase()) : [];
              const candidates = [fn, ...alts];
              const has = comfyInstalledModels.some((m) => {
                const ml = m.toLowerCase();
                return candidates.some((c) => ml === c || ml.endsWith("/" + c) || ml.endsWith("\\" + c) || ml.includes(c));
              });
              return { ...rf, installed: has };
            });
          } else if (currentWf.checkpoint) {
            const hasModel = comfyInstalledModels.some((m) => m.toLowerCase().includes(currentWf.checkpoint.toLowerCase()));
            filesWithStatus = [{
              id: "ckpt",
              name: currentWf.checkpoint,
              filename: currentWf.checkpoint,
              folder_type: "checkpoints",
              url: currentWf.model_url,
              size_str: currentWf.model_size || "4.7 GB",
              installed: hasModel,
            }];
          }

          const missingFiles = filesWithStatus.filter((f) => !f.installed);

          if (missingFiles.length > 0) {
            if (aiModelMissingBanner) {
              aiModelMissingBanner.style.display = "block";
              if (aiModelMissingTitle) aiModelMissingTitle.textContent = t("aiRequiredModelsTitle");
              if (aiModelMissingText) aiModelMissingText.textContent = t("aiRequiredModelsSub", { name: currentWf.name });

              if (aiRequiredFilesList) {
                aiRequiredFilesList.innerHTML = filesWithStatus
                  .map((f) => `
                    <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(0,0,0,0.25); border:1px solid ${f.installed ? "rgba(74,222,128,0.2)" : "rgba(255,100,100,0.2)"}; padding:6px 10px; border-radius:6px; font-size:12px;">
                      <div style="display:flex; align-items:center; gap:8px;">
                        <span>${f.installed ? "✅" : "❌"}</span>
                        <div>
                          <b style="color:var(--text);">${escapeHtml(f.name)}</b>
                          <span style="display:block; font-size:10px; color:var(--mute);">models/${escapeHtml(f.folder_type)}/${escapeHtml(f.filename)}</span>
                        </div>
                      </div>
                      <div>
                        ${f.installed
                          ? `<span style="color:#4ade80; font-size:11px; font-weight:600;">✓ ${t("aiModelInstalled")}</span>`
                          : `<button class="ghost mini btn-single-dl" style="padding:4px 8px; font-size:11px; border:1px solid var(--accent); cursor:pointer;" data-dl-url="${escapeHtml(f.url)}" data-dl-folder="${escapeHtml(f.folder_type)}" data-dl-fn="${escapeHtml(f.filename)}">📥 ${t("aiBtnDownloadSingle", { size: f.size_str })}</button>`
                        }
                      </div>
                    </div>
                  `)
                  .join("");

                aiRequiredFilesList.querySelectorAll(".btn-single-dl").forEach((btn) => {
                  btn.addEventListener("click", () => {
                    startModelDownload(btn.dataset.dlUrl, btn.dataset.dlFolder, btn.dataset.dlFn);
                  });
                });
              }

              if (missingFiles.length > 1) {
                if (btnDownloadAllModels) {
                  btnDownloadAllModels.style.display = "block";
                  btnDownloadAllModels.textContent = t("aiBtnDownloadAll", { size: missingFiles.map((x) => x.size_str).join(" + ") });
                  btnDownloadAllModels.onclick = () => queueModelDownloads(missingFiles);
                }
                if (btnDownloadModel) btnDownloadModel.style.display = "none";
              } else {
                if (btnDownloadAllModels) btnDownloadAllModels.style.display = "none";
                if (btnDownloadModel) {
                  btnDownloadModel.style.display = "block";
                  btnDownloadModel.textContent = `📥 ${missingFiles[0].name} (${missingFiles[0].size_str})`;
                  btnDownloadModel.onclick = () => startModelDownload(missingFiles[0].url, missingFiles[0].folder_type, missingFiles[0].filename);
                }
              }
            }
          } else {
            if (aiModelMissingBanner) aiModelMissingBanner.style.display = "none";
          }

          const aiPromptNotice = document.getElementById("aiPromptNotice");
          if (aiPromptNotice) {
            aiPromptNotice.style.display = currentWf.supports_prompt ? "none" : "block";
          }
        }
      } else {
        comfyOnline = false;
        if (aiStatusBadge) aiStatusBadge.className = "ai-status-badge offline";
        if (aiStatusText) aiStatusText.textContent = `⚪ ${t("aiStatusOffline")}`;
        if (aiOfflineBanner) aiOfflineBanner.style.display = "block";
        if (aiModelMissingBanner) aiModelMissingBanner.style.display = "none";
      }
    } catch (e) {
      comfyOnline = false;
      if (aiStatusBadge) aiStatusBadge.className = "ai-status-badge offline";
      if (aiStatusText) aiStatusText.textContent = `⚪ ${t("aiStatusOffline")}`;
      if (aiOfflineBanner) aiOfflineBanner.style.display = "block";
      if (aiModelMissingBanner) aiModelMissingBanner.style.display = "none";
    }
  }

  let downloadQueue = [];
  let isDownloadingQueue = false;

  async function queueModelDownloads(files) {
    if (!files || files.length === 0) return;
    if (isDownloadingQueue) {
      showToast(t("toastDlAlreadyRunning"), "err");
      return;
    }
    downloadQueue = [...files];
    isDownloadingQueue = true;
    processNextDownload();
  }

  async function processNextDownload() {
    if (downloadQueue.length === 0) {
      isDownloadingQueue = false;
      if (btnDownloadAllModels) btnDownloadAllModels.disabled = false;
      showToast(t("toastAllModelsDownloaded"), "ok");
      setTimeout(() => {
        if (aiDownloadProgressBox) aiDownloadProgressBox.style.display = "none";
        checkComfyStatus();
      }, 1200);
      return;
    }

    const currentItem = downloadQueue.shift();
    if (btnDownloadAllModels) btnDownloadAllModels.disabled = true;
    if (btnDownloadModel) btnDownloadModel.disabled = true;
    if (aiDownloadProgressBox) aiDownloadProgressBox.style.display = "block";
    if (aiDownloadProgressBar) aiDownloadProgressBar.style.width = "0%";
    if (aiDownloadProgressText) aiDownloadProgressText.textContent = t("downloadingFile", { name: currentItem.name });

    try {
      const res = await fetch("/api/ai/download_model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_url: currentItem.url,
          folder_type: currentItem.folder_type || "checkpoints",
          filename: currentItem.filename,
        }),
      });
      const data = await res.json();
      if (!data.ok) {
        showToast(t("toastDlError", { error: data.error || "" }), "err");
        isDownloadingQueue = false;
        if (btnDownloadAllModels) btnDownloadAllModels.disabled = false;
        if (btnDownloadModel) btnDownloadModel.disabled = false;
        return;
      }

      if (aiDownloadPollTimer) clearInterval(aiDownloadPollTimer);
      aiDownloadPollTimer = setInterval(async () => {
        try {
          const pRes = await fetch("/api/ai/download_progress");
          const pData = await pRes.json();
          if (aiDownloadProgressBar) aiDownloadProgressBar.style.width = `${pData.progress || 0}%`;
          if (aiDownloadProgressText) {
            const queueSuffix = downloadQueue.length > 0 ? t("queuedFilesPending", { count: downloadQueue.length }) : "";
            aiDownloadProgressText.textContent = `${currentItem.name}: ${pData.status_text || pData.progress + "%"}${queueSuffix}`;
          }

          if (!pData.downloading) {
            clearInterval(aiDownloadPollTimer);
            if (pData.error) {
              showToast(t("toastDlError", { error: pData.error }), "err");
              isDownloadingQueue = false;
              if (btnDownloadAllModels) btnDownloadAllModels.disabled = false;
              if (btnDownloadModel) btnDownloadModel.disabled = false;
            } else {
              showToast(t("toastModelDownloaded", { name: currentItem.name }), "ok");
              await checkComfyStatus();
              setTimeout(() => {
                processNextDownload();
              }, 800);
            }
          }
        } catch (e) {
          clearInterval(aiDownloadPollTimer);
          isDownloadingQueue = false;
          if (btnDownloadAllModels) btnDownloadAllModels.disabled = false;
          if (btnDownloadModel) btnDownloadModel.disabled = false;
        }
      }, 1000);
    } catch (e) {
      showToast(t("toastDlFailed"), "err");
      isDownloadingQueue = false;
      if (btnDownloadAllModels) btnDownloadAllModels.disabled = false;
      if (btnDownloadModel) btnDownloadModel.disabled = false;
    }
  }

  async function startModelDownload(modelUrl, folderType = "checkpoints", filename = "") {
    if (!modelUrl) return;
    queueModelDownloads([{
      name: filename || "Model",
      url: modelUrl,
      folder_type: folderType,
      filename: filename,
    }]);
  }

  async function startAiGeneration() {
    if (!aiSelectedImageData) {
      showToast(t("toastSelectSourceImage"), "err");
      return;
    }
    if (!comfyOnline) {
      showToast(t("aiComfyOfflineTip"), "err");
      return;
    }

    const currentWf = aiWorkflows.find((w) => w.id === (aiModelSelect ? aiModelSelect.value : "minimax_h3")) || aiWorkflows[0];
    let missingFiles = [];
    if (currentWf) {
      if (Array.isArray(currentWf.required_files) && currentWf.required_files.length > 0) {
        for (const rf of currentWf.required_files) {
          const fn = (rf.filename || "").toLowerCase();
          const alts = Array.isArray(rf.alternatives) ? rf.alternatives.map((a) => a.toLowerCase()) : [];
          const candidates = [fn, ...alts];
          const has = comfyInstalledModels.some((m) => {
            const ml = m.toLowerCase();
            return candidates.some((c) => ml === c || ml.endsWith("/" + c) || ml.endsWith("\\" + c) || ml.includes(c));
          });
          if (!has) {
            missingFiles.push(rf);
          }
        }
      } else if (currentWf.checkpoint) {
        const hasModel = comfyInstalledModels.some((m) => m.toLowerCase().includes(currentWf.checkpoint.toLowerCase()));
        if (!hasModel) {
          missingFiles.push({
            name: currentWf.checkpoint,
            filename: currentWf.checkpoint,
            folder_type: "checkpoints",
            url: currentWf.model_url,
            size_str: currentWf.model_size || "4.7 GB",
          });
        }
      }
    }

    if (comfyInstalledModels.length > 0 && missingFiles.length > 0) {
      if (aiModelMissingBanner) aiModelMissingBanner.style.display = "block";
      const fileNames = missingFiles.map((f) => `• ${f.name} (${f.size_str})`).join("\n");
      const ask = confirm(
        t("confirmMissingModels", { files: fileNames })
      );
      if (ask) {
        queueModelDownloads(missingFiles);
      }
      return;
    }

    if (btnGenerateAi) btnGenerateAi.disabled = true;
    if (btnCancelAi) btnCancelAi.style.display = "inline-flex";
    if (aiProgressCard) aiProgressCard.style.display = "block";
    if (aiResultCard) aiResultCard.style.display = "none";
    if (aiProgressBar) aiProgressBar.style.width = "10%";
    if (aiProgressPercent) aiProgressPercent.textContent = "10%";
    if (aiProgressText) aiProgressText.textContent = t("aiInitComfy");

    let width = 576;
    let height = 576;
    let scaleWidth = 480;
    const resProfile = aiResolutionSelect ? aiResolutionSelect.value : "high";
    if (resProfile === "standard") {
      width = 512;
      height = 512;
      scaleWidth = 400;
    } else if (resProfile === "fast") {
      width = 480;
      height = 272;
      scaleWidth = 384;
    }

    const payload = {
      image_data: aiSelectedImageData,
      prompt: aiPromptInput ? aiPromptInput.value.trim() : "",
      workflow_id: aiModelSelect ? aiModelSelect.value : "svd_xt",
      motion_bucket: aiMotionRange ? parseInt(aiMotionRange.value, 10) : 100,
      frames: aiFramesSelect ? parseInt(aiFramesSelect.value, 10) : 44,
      fps: aiFpsSelect ? parseInt(aiFpsSelect.value, 10) : 12,
      width: width,
      height: height,
      scale_width: scaleWidth,
      loop_mode: chkAiPingPong && chkAiPingPong.checked ? "pingpong" : "normal",
      title: aiTitleInput ? aiTitleInput.value.trim() : "",
    };

    try {
      const res = await fetch("/api/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!data.ok) {
        showToast(t("toastGenStartFailed", { error: data.error || "" }), "err");
        resetAiControls();
        return;
      }

      // Start polling progress
      if (aiProgressPollTimer) clearInterval(aiProgressPollTimer);
      aiProgressPollTimer = setInterval(async () => {
        try {
          const pRes = await fetch("/api/ai/progress");
          const pData = await pRes.json();

          if (aiProgressBar) aiProgressBar.style.width = `${pData.progress || 0}%`;
          if (aiProgressPercent) aiProgressPercent.textContent = `${pData.progress || 0}%`;
          if (aiProgressText) aiProgressText.textContent = pData.status_text || t("calculating");

          if (!pData.busy) {
            clearInterval(aiProgressPollTimer);
            resetAiControls();

            if (pData.current_gif) {
              aiLatestGif = pData.current_gif;
              if (aiResultCard) aiResultCard.style.display = "block";
              if (aiResultImg) aiResultImg.src = `${aiLatestGif.url}&t=${Date.now()}`;
              if (aiResultTitle) aiResultTitle.textContent = aiLatestGif.title;
              if (aiResultInfo) {
                aiResultInfo.textContent = `${aiLatestGif.file_size_mb || "2.1"} MB • ${payload.frames} Frames • Discord Ready ✨`;
              }
              showToast(t("aiSuccessToast"), "ok");
              await loadGifs();
            } else if (pData.error) {
              showToast(t("aiErrorToast", { error: pData.error }), "err");
            }
          }
        } catch (e) {
          console.warn("Progress poll error:", e);
        }
      }, 800);
    } catch (e) {
      showToast(t("aiErrorToast", { error: e.message || e }), "err");
      resetAiControls();
    }
  }

  async function cancelAiGeneration() {
    try {
      await fetch("/api/ai/cancel", { method: "POST" });
      if (aiProgressPollTimer) clearInterval(aiProgressPollTimer);
      resetAiControls();
      showToast(t("aiCancelToast"), "ok");
    } catch (e) {
      console.warn("Cancel error:", e);
    }
  }

  function resetAiControls() {
    if (btnGenerateAi) btnGenerateAi.disabled = false;
    if (btnCancelAi) btnCancelAi.style.display = "none";
    if (aiProgressCard) aiProgressCard.style.display = "none";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tadiscordgif.theme", theme);
    if (cfgTheme) cfgTheme.value = theme;
  }

  function handleFileSelect(file) {
    if (!file.type.includes("gif") && !file.name.toLowerCase().endsWith(".gif")) {
      showToast(t("toastFileOnlyGif"), "err");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      selectedFileData = e.target.result;
      dropZone.innerHTML = `<p>✅ <b>${escapeHtml(file.name)}</b> (${(file.size / 1024).toFixed(1)} KB)<br><span style="color:var(--accent)">${t("dropChange")}</span></p>`;
      if (!inputTitle.value) {
        inputTitle.value = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      }
    };
    reader.readAsDataURL(file);
  }

  // --- API Calls ---

  async function checkStatus() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (!data.ok) return;

      if (data.discord_found) {
        statusEl.className = "status ok";
        statusTextEl.textContent = `${t("discordReady")} (${data.target_window || "Discord"})`;
      } else {
        statusEl.className = "status bad";
        statusTextEl.textContent = t("discordNotFound");
      }

      if (data.version) {
        const bv = document.getElementById("brandVersion");
        if (bv) bv.textContent = `v${data.version}`;
      }
    } catch (e) {
      statusEl.className = "status bad";
      statusTextEl.textContent = t("serverOffline");
    }
  }

  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      if (data.ok && data.settings) {
        const s = data.settings;
        if (s.language && !localStorage.getItem("tadiscordgif.lang")) {
          setLanguage(s.language);
        }
        if (s.paste_mode) {
          pasteMode = s.paste_mode;
          pasteModeSeg.querySelectorAll("button").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.mode === pasteMode);
          });
        }
        if (s.auto_send !== undefined) {
          autoSend = s.auto_send;
          chkAutoSend.checked = autoSend;
        }
        if (s.theme) {
          applyTheme(s.theme);
        }
        if (s.gif_dir !== undefined && cfgGifDir) {
          cfgGifDir.value = s.gif_dir;
        }
        if (s.comfyui_url && cfgComfyUrl) {
          cfgComfyUrl.value = s.comfyui_url;
        }
        if (s.comfyui_dir && cfgComfyDir) {
          cfgComfyDir.value = s.comfyui_dir;
        }
      }
    } catch (e) {
      console.warn("Could not load settings:", e);
    }
  }

  async function saveSetting(key, val) {
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [key]: val }),
      });
    } catch (e) {
      console.warn("Could not save setting:", e);
    }
  }

  async function saveSettingsBatch(obj) {
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
    } catch (e) {
      console.warn("Could not save settings batch:", e);
    }
  }

  async function loadGifs() {
    try {
      const res = await fetch("/api/gifs");
      const data = await res.json();
      if (data.ok) {
        gifs = data.gifs || [];
        if (currentSource === "local") {
          updateCategoryTabs();
          renderGallery();
        }
      }
    } catch (e) {
      if (currentSource === "local") showToast(t("emptyTitle"), "err");
    }
  }

  async function loadTenorGifs(query = "") {
    tenorLoading = true;
    gifGrid.innerHTML = `
      <div class="empty-state">
        <p style="font-size:24px; margin-bottom:8px; animation: spin 1s linear infinite;">🔄</p>
        <p>${t("connecting")}</p>
      </div>
    `;

    try {
      const res = await fetch(`/api/tenor/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (data.ok) {
        tenorGifs = data.gifs || [];
      } else {
        tenorGifs = [];
      }
    } catch (e) {
      console.warn("Tenor error:", e);
      tenorGifs = [];
    } finally {
      tenorLoading = false;
      if (currentSource === "tenor") {
        renderGallery();
      }
    }
  }

  async function downloadTenorGif(gif, e) {
    if (e) e.stopPropagation();
    showToast(t("toastDownloading"), "ok");

    try {
      const res = await fetch("/api/tenor/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: gif.url,
          title: gif.title,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        showToast(t("toastDownloaded"), "ok");
        await loadGifs();
      } else {
        showToast(data.error || "Download error", "err");
      }
    } catch (err) {
      showToast("Download failed", "err");
    }
  }

  async function saveNewGif() {
    const title = inputTitle.value.trim();
    const tags = inputTags.value.trim();
    const url = inputUrl.value.trim();

    if (!selectedFileData && !url) {
      showToast(t("toastNoFileOrUrl"), "err");
      return;
    }

    btnSaveGif.disabled = true;
    btnSaveGif.textContent = t("savingGif");

    try {
      const payload = {
        title: title || (CURRENT_LANG === "de" ? "Neues GIF" : "New GIF"),
        tags: tags,
        url: url,
        data: selectedFileData || null,
      };

      const res = await fetch("/api/gifs/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (data.ok) {
        showToast(t("toastSaved"), "ok");
        // Reset form
        inputTitle.value = "";
        inputTags.value = "";
        inputUrl.value = "";
        selectedFileData = null;
        dropZone.innerHTML = `<p>📁 <b>${t("dropPrompt")}</b></p>`;
        await loadGifs();
      } else {
        showToast(data.error || "Error", "err");
      }
    } catch (e) {
      showToast("Network Error", "err");
    } finally {
      btnSaveGif.disabled = false;
      btnSaveGif.textContent = t("btnSaveGif");
    }
  }

  async function sendGif(gif) {
    showToast(t("toastInserting", { title: gif.title }), "ok");

    try {
      const res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: gif.id,
          mode: pasteMode,
          auto_send: autoSend,
        }),
      });

      const data = await res.json();
      if (data.ok) {
        if (data.warning) {
          showToast(data.warning, "err");
        } else {
          showToast(t("toastInserted"), "ok");
        }
      } else {
        showToast(data.error || "Error", "err");
      }
    } catch (e) {
      showToast("Error during insert", "err");
    }
  }

  async function toggleFavorite(gif, e) {
    e.stopPropagation();
    const newFav = !gif.favorite;
    gif.favorite = newFav;

    try {
      await fetch("/api/gifs/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: gif.id, favorite: newFav }),
      });
      renderGallery();
    } catch (e) {
      console.warn("Could not toggle favorite:", e);
    }
  }

  async function deleteGif(gif, e) {
    e.stopPropagation();
    if (!confirm(t("deleteConfirm", { title: gif.title }))) return;

    try {
      const res = await fetch("/api/gifs/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: gif.id }),
      });
      const data = await res.json();
      if (data.ok) {
        showToast(t("toastDeleted"), "ok");
        await loadGifs();
      } else {
        showToast(data.error || "Error", "err");
      }
    } catch (e) {
      showToast("Error deleting", "err");
    }
  }

  // --- Rendering Helpers ---

  function updateCategoryTabs() {
    if (currentSource === "tenor") {
      let html = "";
      TENOR_CATEGORIES.forEach((cat) => {
        const isAct = activeFilter === (cat.id || "all");
        html += `<button class="${isAct ? "active" : ""}" data-tenor-cat="${escapeHtml(cat.id)}">${escapeHtml(cat.label)}</button>`;
      });
      categoryTabs.innerHTML = html;
      categoryTabs.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
          categoryTabs.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          const q = btn.dataset.tenorCat;
          activeFilter = q || "all";
          searchInput.value = q;
          loadTenorGifs(q);
        });
      });
      return;
    }

    const catSet = new Set();
    const tagSet = new Set();

    gifs.forEach((g) => {
      if (g.category && g.category.trim()) {
        catSet.add(g.category.trim());
      }
      if (Array.isArray(g.tags)) {
        g.tags.forEach((t) => {
          if (!t) return;
          const tl = t.toLowerCase().trim();
          // Filter out filename-like tags, hex hashes, and generic noise
          if (tl.length < 3 || tl === "gif" || tl === "generated" || tl.includes("_") || /[0-9a-f]{5,}/.test(tl)) return;
          tagSet.add(t);
        });
      }
    });

    const currentActive = activeFilter;
    let html = `
      <button class="${currentActive === "all" ? "active" : ""}" data-filter="all">${t("tabAll")}</button>
      <button class="${currentActive === "fav" ? "active" : ""}" data-filter="fav">${t("tabFav")}</button>
    `;

    // Folder subcategories first
    Array.from(catSet).sort().forEach((cat) => {
      const isAct = currentActive === `cat:${cat}`;
      html += `<button class="${isAct ? "active" : ""}" data-filter="cat:${escapeHtml(cat)}">📁 ${escapeHtml(cat)}</button>`;
    });

    // Other tags
    Array.from(tagSet).sort().forEach((tag) => {
      if (catSet.has(tag)) return;
      const isAct = currentActive === tag;
      html += `<button class="${isAct ? "active" : ""}" data-filter="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`;
    });

    categoryTabs.innerHTML = html;

    categoryTabs.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        categoryTabs.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = btn.dataset.filter;
        renderGallery();
      });
    });
  }

  function openEditModal(gif) {
    currentlyEditingGif = gif;
    editTitleInput.value = gif.title || "";
    editTagsInput.value = Array.isArray(gif.tags) ? gif.tags.join(", ") : "";
    const imgSrc = gif.url || (gif.filename ? `/gifs/${encodeURIComponent(gif.filename)}` : "");
    editPreview.src = imgSrc;
    dlgEdit.showModal();
  }

  function renderGallery() {
    if (currentSource === "tenor") {
      const list = tenorGifs;
      const countWord = list.length === 1 ? t("countSingle") : t("countSuffix");
      gifCount.textContent = `${list.length} ${countWord}`;

      if (list.length === 0 && !tenorLoading) {
        gifGrid.innerHTML = `
          <div class="empty-state">
            <p style="font-size:24px; margin-bottom:8px;">🌐</p>
            <p>${t("emptyTitle")}</p>
            <p style="font-size:12px;">${t("emptyHint")}</p>
          </div>
        `;
        return;
      }

      gifGrid.innerHTML = list
        .map((g) => {
          const imgSrc = g.preview_url || g.url || "";
          const tagsHtml = (g.tags || []).slice(0, 3).map((t) => `<span class="badge">${escapeHtml(t)}</span>`).join("");

          return `
            <div class="gif-card" data-id="${g.id}">
              <div class="gif-thumb-wrap">
                <img class="gif-thumb" src="${escapeHtml(imgSrc)}" alt="${escapeHtml(g.title)}" loading="lazy">
                <div class="gif-overlay">
                  <button class="primary" data-action="send">${t("insertBtn")}</button>
                </div>
              </div>
              <div class="gif-info">
                <div class="gif-info-row">
                  <span class="gif-title" title="${escapeHtml(g.title)}">${escapeHtml(g.title)}</span>
                  <span class="badge" style="font-size:10px; background:var(--accent); color:#fff; padding:2px 5px; border-radius:4px;">Tenor</span>
                </div>
                <div class="gif-tags">${tagsHtml}</div>
                <div class="gif-actions" style="margin-top:6px;">
                  <button class="ghost" data-action="download" style="width:100%; display:flex; align-items:center; justify-content:center; gap:5px; padding:5px 8px; font-size:11px; border-radius:6px; cursor:pointer;" title="${t("downloadToFolder")}">
                    <span>💾</span>
                    <span>${t("downloadToFolder")}</span>
                  </button>
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      gifGrid.querySelectorAll(".gif-card").forEach((card) => {
        const gid = card.dataset.id;
        const gif = tenorGifs.find((x) => x.id === gid);
        if (!gif) return;

        card.querySelector(".gif-thumb-wrap").addEventListener("click", () => sendGif(gif));
        const dlBtn = card.querySelector('[data-action="download"]');
        if (dlBtn) {
          dlBtn.addEventListener("click", (e) => downloadTenorGif(gif, e));
        }
      });
      return;
    }

    const filtered = gifs.filter((g) => {
      if (activeFilter === "fav") {
        if (!g.favorite) return false;
      } else if (activeFilter.startsWith("cat:")) {
        const targetCat = activeFilter.slice(4);
        if ((g.category || "").toLowerCase() !== targetCat.toLowerCase()) return false;
      } else if (activeFilter !== "all") {
        if (!Array.isArray(g.tags) || !g.tags.includes(activeFilter)) return false;
      }

      if (searchQuery) {
        const titleMatch = (g.title || "").toLowerCase().includes(searchQuery);
        const tagMatch = Array.isArray(g.tags) && g.tags.some((t) => t.toLowerCase().includes(searchQuery));
        const catMatch = (g.category || "").toLowerCase().includes(searchQuery);
        if (!titleMatch && !tagMatch && !catMatch) return false;
      }

      return true;
    });

    const countWord = filtered.length === 1 ? t("countSingle") : t("countSuffix");
    gifCount.textContent = `${filtered.length} ${countWord}`;

    if (filtered.length === 0) {
      gifGrid.innerHTML = `
        <div class="empty-state">
          <p style="font-size:24px; margin-bottom:8px;">🔍</p>
          <p>${t("emptyTitle")}</p>
          <p style="font-size:12px;">${t("emptyHint")}</p>
        </div>
      `;
      return;
    }

    gifGrid.innerHTML = filtered
      .map((g) => {
        const imgSrc = g.url || (g.filename ? `/gifs/${encodeURIComponent(g.filename)}` : "");
        const tagsHtml = (g.tags || []).map((t) => `<span class="badge">${escapeHtml(t)}</span>`).join("");
        const actionHtml = g.is_custom_folder
          ? (g.category ? `<span class="badge" style="opacity:0.75; font-size:11px;">📁 ${escapeHtml(g.category)}</span>` : "")
          : `<button class="mini danger ghost" data-action="delete" title="${t("deleteTitle")}">🗑️</button>`;

        return `
          <div class="gif-card" data-id="${g.id}">
            <div class="gif-thumb-wrap">
              <img class="gif-thumb" src="${escapeHtml(imgSrc)}" alt="${escapeHtml(g.title)}" loading="lazy">
              <div class="gif-overlay">
                <button class="primary" data-action="send">${t("insertBtn")}</button>
              </div>
            </div>
            <div class="gif-info">
              <div class="gif-info-row">
                <span class="gif-title" title="${escapeHtml(g.title)}">${escapeHtml(g.title)}</span>
                <div style="display:flex; align-items:center; gap:4px;">
                  <button class="mini ghost" data-action="edit" title="${t("editBtn")}" style="padding: 2px 5px; font-size: 11px; opacity: 0.85; cursor: pointer; border-radius: 4px;">✏️</button>
                  <button class="gif-fav-btn ${g.favorite ? "active" : ""}" data-action="fav" title="${t("favoriteTitle")}">
                    ${g.favorite ? "★" : "☆"}
                  </button>
                </div>
              </div>
              <div class="gif-tags">${tagsHtml}</div>
              <div class="gif-actions">
                ${actionHtml}
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    gifGrid.querySelectorAll(".gif-card").forEach((card) => {
      const gid = card.dataset.id;
      const gif = gifs.find((x) => x.id === gid);
      if (!gif) return;

      card.querySelector(".gif-thumb-wrap").addEventListener("click", () => sendGif(gif));
      card.querySelector('[data-action="fav"]').addEventListener("click", (e) => toggleFavorite(gif, e));
      const editBtn = card.querySelector('[data-action="edit"]');
      if (editBtn) {
        editBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          openEditModal(gif);
        });
      }
      const delBtn = card.querySelector('[data-action="delete"]');
      if (delBtn) {
        delBtn.addEventListener("click", (e) => deleteGif(gif, e));
      }
    });
  }

  function showToast(msg, type = "ok") {
    if (toastTimer) clearTimeout(toastTimer);
    toastEl.textContent = msg;
    toastEl.className = `toast ${type}`;
    toastEl.hidden = false;
    toastTimer = setTimeout(() => {
      toastEl.hidden = true;
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
})();
