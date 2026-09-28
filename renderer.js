let currentSourceMode = "youtube";
let selectedLocalFilePath = null;
let currentModalFilePath = null;
let selectedStyle = "luxury_doc";

// Style selector
function selectStyle(styleKey) {
  selectedStyle = styleKey;
  const cards = document.querySelectorAll(".style-card");
  cards.forEach(card => {
    if (card.getAttribute("data-style") === styleKey) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }
  });
}


// Tab switcher
function switchSourceTab(mode) {
  currentSourceMode = mode;
  document.getElementById("tabYoutube").classList.toggle("active", mode === "youtube");
  document.getElementById("tabLocal").classList.toggle("active", mode === "local");
  document.getElementById("youtubeInputView").classList.toggle("active", mode === "youtube");
  document.getElementById("localInputView").classList.toggle("active", mode === "local");
}

// Paste from clipboard
async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      document.getElementById("youtubeUrl").value = text.trim();
    }
  } catch (err) {
    console.error("Clipboard read error:", err);
  }
}

// Browse local file
async function browseLocalFile() {
  try {
    const filePath = await window.electronAPI.selectVideoFile();
    if (filePath) {
      selectedLocalFilePath = filePath;
      const fileName = filePath.split("/").pop();
      document.getElementById("dropText").textContent = `Selected: ${fileName}`;
    }
  } catch (err) {
    console.error("Browse file error:", err);
  }
}

// Drag & Drop
const dropZone = document.getElementById("dropZone");
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "var(--accent-yellow)";
});
dropZone.addEventListener("dragleave", () => {
  dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
});
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    selectedLocalFilePath = file.path;
    document.getElementById("dropText").textContent = `Selected: ${file.name}`;
  }
});

// Start generation
function startGeneration() {
  let inputPath = "";
  if (currentSourceMode === "youtube") {
    inputPath = document.getElementById("youtubeUrl").value.trim();
    if (!inputPath) {
      alert("Please enter a valid YouTube URL.");
      return;
    }
  } else {
    inputPath = selectedLocalFilePath;
    if (!inputPath) {
      alert("Please select a local video file.");
      return;
    }
  }

  const numClips = parseInt(document.getElementById("numClips").value);
  const duration = parseFloat(document.getElementById("duration").value);
  const framingMode = document.getElementById("framingMode").value;
  const langMode = document.getElementById("langMode").value;
  const zoomCuts = document.getElementById("zoomCutsToggle").checked;
  const broll = document.getElementById("brollToggle") ? document.getElementById("brollToggle").checked : false;
  const sfx = document.getElementById("sfxToggle") ? document.getElementById("sfxToggle").checked : false;

  // Update UI to running state
  document.getElementById("generateBtn").disabled = true;
  document.getElementById("progressBox").style.display = "block";
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("progressStatus").textContent = "Launching AI pipeline...";
  document.getElementById("progressPercent").textContent = "0%";
  document.getElementById("progressBarFill").style.width = "0%";

  window.electronAPI.startClipping({
    input: inputPath,
    numClips,
    duration,
    mode: framingMode,
    style: selectedStyle,
    langMode,
    zoomCuts,
    broll,
    sfx
  });
}

function cancelGeneration() {
  window.electronAPI.cancelClipping();
  document.getElementById("generateBtn").disabled = false;
  document.getElementById("progressBox").style.display = "none";
  document.getElementById("emptyState").style.display = "flex";
}

// Progress listener
window.electronAPI.onProgress((data) => {
  const { step, percent, message, data: extra } = data;
  document.getElementById("progressPercent").textContent = `${percent}%`;
  document.getElementById("progressBarFill").style.width = `${percent}%`;
  document.getElementById("progressStatus").textContent = message;

  if (step === "finished" && extra && extra.clips) {
    document.getElementById("generateBtn").disabled = false;
    document.getElementById("progressBox").style.display = "none";
    renderClipsGallery(extra.clips);
  }
});

// Error listener
window.electronAPI.onError((err) => {
  document.getElementById("generateBtn").disabled = false;
  document.getElementById("progressStatus").textContent = "Error during processing.";
  alert(`Error: ${err.message}`);
});

// Render Clips Gallery
function renderClipsGallery(clips) {
  const grid = document.getElementById("clipsGrid");
  const countBadge = document.getElementById("clipsCount");
  grid.innerHTML = "";
  countBadge.textContent = `${clips.length} Ready`;

  clips.forEach((clip) => {
    const card = document.createElement("div");
    card.className = "clip-card";

    const score = clip.score || 92;
    const title = clip.title || `Viral Clip #${clip.index}`;
    const hashtags = clip.hashtags || "#shorts #viral #podcast";
    const lang = clip.lang ? clip.lang : "AUTO";

    card.innerHTML = `
      <div class="clip-thumb" onclick="openModal('${clip.path}', '${title}', '${hashtags}', ${score})">
        <video src="file://${clip.path}" preload="metadata" muted></video>
        <div class="clip-play-overlay">
          <div class="play-circle">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          </div>
        </div>
        <span class="clip-duration-badge">${clip.duration}s</span>
      </div>
      <div class="clip-info">
        <div class="clip-header-row">
          <span class="clip-score">${score}% VIRAL SCORE</span>
          <span class="clip-lang">${lang}</span>
        </div>
        <div class="clip-title">${title}</div>
        <div class="clip-actions">
          <button onclick="revealFile('${clip.path}')">Finder</button>
          <button id="copyBtn_${clip.index}" onclick="copyCaption('${title.replace(/'/g, "\\'")}', '${hashtags.replace(/'/g, "\\'")}', 'copyBtn_${clip.index}')">Copy Tags</button>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });

  grid.style.display = "grid";
  document.getElementById("emptyState").style.display = "none";
}

function revealFile(path) {
  window.electronAPI.revealInFinder(path);
}

function openExportFolder() {
  window.electronAPI.openDocumentsFolder();
}

function copyCaption(title, hashtags, btnId) {
  const text = `${title}\n\n${hashtags}`;
  navigator.clipboard.writeText(text);
  const btn = document.getElementById(btnId);
  if (btn) {
    const orig = btn.textContent;
    btn.textContent = "Copied!";
    btn.style.color = "var(--accent-gold)";
    setTimeout(() => {
      btn.textContent = orig;
      btn.style.color = "";
    }, 1500);
  }
}

// Modal Video Player
function openModal(filePath, title) {
  currentModalFilePath = filePath;
  const modal = document.getElementById("videoModal");
  const player = document.getElementById("modalVideoPlayer");
  const titleElem = document.getElementById("modalVideoTitle");
  
  titleElem.textContent = title;
  player.src = `file://${filePath}`;
  modal.classList.add("active");
  player.play();

  document.getElementById("modalRevealBtn").onclick = () => revealFile(filePath);
}

function closeModal(e) {
  if (e && e.target !== e.currentTarget && !e.target.classList.contains("close-modal-btn")) {
    return;
  }
  const modal = document.getElementById("videoModal");
  const player = document.getElementById("modalVideoPlayer");
  player.pause();
  player.src = "";
  modal.classList.remove("active");
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeModal();
  }
});
