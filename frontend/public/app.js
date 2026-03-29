/* =====================================================
   BeatShift – Frontend Application Logic
   ===================================================== */

const API_BASE = '';   // same-origin; change to http://localhost:8000 for dev

// --- State ---
let selectedFile = null;
let selectedStyle = null;
let originalObjectURL = null;

// --- DOM refs ---
const dropzone        = document.getElementById('dropzone');
const fileInput       = document.getElementById('file-input');
const filePreview     = document.getElementById('file-preview');
const fileNameEl      = document.getElementById('file-name');
const fileSizeEl      = document.getElementById('file-size');
const removeFileBtn   = document.getElementById('remove-file');
const originalPlayer  = document.getElementById('original-player');

const styleSection    = document.getElementById('style-section');
const styleGrid       = document.getElementById('style-grid');

const intensitySlider = document.getElementById('intensity-slider');
const intensityDisplay= document.getElementById('intensity-display');

const convertRow      = document.getElementById('convert-row');
const convertBtn      = document.getElementById('convert-btn');

const progressSection = document.getElementById('progress-section');
const progressTitle   = document.getElementById('progress-title');
const progressBar     = document.getElementById('progress-bar');

const resultSection       = document.getElementById('result-section');
const resultInfo          = document.getElementById('result-info');
const resultStyleLabel    = document.getElementById('result-style-label');
const resultOriginalPlayer= document.getElementById('result-original-player');
const resultConvertedPlayer=document.getElementById('result-converted-player');
const downloadLink        = document.getElementById('download-link');
const convertAnotherBtn   = document.getElementById('convert-another');

const toast               = document.getElementById('toast');

// =====================================================
// Toast notification
// =====================================================
let toastTimer = null;
function showToast(msg, type = 'info') {
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = 'toast hidden'; }, 4000);
}

// =====================================================
// File handling
// =====================================================
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function setFile(file) {
  const allowed = ['audio/mpeg','audio/wav','audio/ogg','audio/flac','audio/mp4',
                   'audio/aac','audio/x-m4a','audio/x-flac'];
  const ext = file.name.split('.').pop().toLowerCase();
  const allowedExt = ['mp3','wav','ogg','flac','m4a','aac'];
  if (!allowedExt.includes(ext)) {
    showToast('Unsupported file type. Please upload MP3, WAV, OGG, FLAC, or M4A.', 'error');
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast('File too large. Maximum size is 50 MB.', 'error');
    return;
  }

  selectedFile = file;
  fileNameEl.textContent = file.name;
  fileSizeEl.textContent = formatSize(file.size);

  if (originalObjectURL) URL.revokeObjectURL(originalObjectURL);
  originalObjectURL = URL.createObjectURL(file);
  originalPlayer.src = originalObjectURL;

  filePreview.classList.remove('hidden');
  dropzone.classList.add('hidden');

  styleSection.classList.remove('hidden');
  updateConvertButton();
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  filePreview.classList.add('hidden');
  dropzone.classList.remove('hidden');
  styleSection.classList.add('hidden');
  convertRow.classList.add('hidden');
  if (originalObjectURL) { URL.revokeObjectURL(originalObjectURL); originalObjectURL = null; }
}

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

removeFileBtn.addEventListener('click', clearFile);

// =====================================================
// Styles
// =====================================================
async function loadStyles() {
  try {
    const res = await fetch(`${API_BASE}/api/styles`);
    const data = await res.json();
    renderStyleGrid(data.styles);
  } catch {
    // Fallback hardcoded styles
    renderStyleGrid([
      { id: 'lofi',      name: 'Lo-fi Hip Hop',   emoji: '🎵', description: 'Chill, warm, vinyl crackle' },
      { id: 'edm',       name: 'EDM / Electronic', emoji: '⚡', description: 'High-energy, pumping bass' },
      { id: 'trap',      name: 'Trap',             emoji: '🔥', description: '808s, hi-hats, dark vibes' },
      { id: 'jazz',      name: 'Jazz',             emoji: '🎷', description: 'Swing feel, warm tone' },
      { id: 'rock',      name: 'Rock',             emoji: '🎸', description: 'Driven, punchy, loud' },
      { id: 'reggaeton', name: 'Reggaeton',        emoji: '🌴', description: 'Dembow rhythm, dancehall' },
      { id: 'bossanova', name: 'Bossa Nova',       emoji: '🌸', description: 'Smooth, Brazilian groove' },
      { id: 'rnb',       name: 'R&B / Soul',       emoji: '💜', description: 'Soulful, smooth, groovy' },
      { id: 'phonk',     name: 'Phonk',            emoji: '💀', description: 'Memphis rap, distorted 808' },
      { id: 'ambient',   name: 'Ambient',          emoji: '🌊', description: 'Atmospheric, dreamy pads' },
    ]);
  }
}

function renderStyleGrid(styles) {
  styleGrid.innerHTML = '';
  styles.forEach(s => {
    const card = document.createElement('div');
    card.className = 'style-card';
    card.dataset.id = s.id;
    card.innerHTML = `
      <div class="style-emoji">${s.emoji}</div>
      <div class="style-name">${s.name}</div>
      <div class="style-desc">${s.description}</div>
    `;
    card.addEventListener('click', () => selectStyle(s.id));
    styleGrid.appendChild(card);
  });
}

function selectStyle(id) {
  selectedStyle = id;
  document.querySelectorAll('.style-card').forEach(c => {
    c.classList.toggle('selected', c.dataset.id === id);
  });
  updateConvertButton();
}

function updateConvertButton() {
  if (selectedFile && selectedStyle) {
    convertRow.classList.remove('hidden');
  } else {
    convertRow.classList.add('hidden');
  }
}

// =====================================================
// Intensity slider
// =====================================================
intensitySlider.addEventListener('input', () => {
  const val = intensitySlider.value;
  intensityDisplay.textContent = val + '%';
  // Update gradient
  intensitySlider.style.background =
    `linear-gradient(to right, var(--accent) 0%, var(--accent) ${val}%, var(--border) ${val}%)`;
});

// =====================================================
// Conversion
// =====================================================
const PROGRESS_STEPS = [
  { pct: 10, text: 'Reading audio file…' },
  { pct: 25, text: 'Detecting BPM and beats…' },
  { pct: 45, text: 'Applying style transformations…' },
  { pct: 70, text: 'Processing EQ and effects…' },
  { pct: 88, text: 'Normalizing output…' },
  { pct: 95, text: 'Finalizing file…' },
];

let progressInterval = null;

function startFakeProgress() {
  let step = 0;
  progressBar.style.width = '5%';
  progressTitle.textContent = 'Preparing…';

  progressInterval = setInterval(() => {
    if (step >= PROGRESS_STEPS.length) {
      clearInterval(progressInterval);
      return;
    }
    const { pct, text } = PROGRESS_STEPS[step++];
    progressBar.style.width = pct + '%';
    progressTitle.textContent = text;
  }, 900);
}

function stopFakeProgress() {
  clearInterval(progressInterval);
  progressBar.style.width = '100%';
}

convertBtn.addEventListener('click', async () => {
  if (!selectedFile || !selectedStyle) return;

  // UI transitions
  convertRow.classList.add('hidden');
  resultSection.classList.add('hidden');
  progressSection.classList.remove('hidden');
  startFakeProgress();

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('style', selectedStyle);
  formData.append('intensity', (parseFloat(intensitySlider.value) / 100).toFixed(2));

  try {
    const res = await fetch(`${API_BASE}/api/convert`, {
      method: 'POST',
      body: formData,
    });

    stopFakeProgress();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    showResult(data);

  } catch (err) {
    stopFakeProgress();
    progressSection.classList.add('hidden');
    convertRow.classList.remove('hidden');
    showToast(`Conversion failed: ${err.message}`, 'error');
  }
});

function showResult(data) {
  progressSection.classList.add('hidden');

  // Chips
  const info = data.info || {};
  resultInfo.innerHTML = '';
  const chips = [
    { label: 'Style',    value: data.style.toUpperCase() },
    { label: 'BPM',      value: info.original_bpm ? info.original_bpm + ' bpm' : '—' },
    { label: 'Duration', value: info.duration_sec ? formatDur(info.duration_sec) : '—' },
    { label: 'Beats',    value: info.beat_count ?? '—' },
    { label: 'Sample Rate', value: info.output_sr ? info.output_sr + ' Hz' : '—' },
  ];
  chips.forEach(({ label, value }) => {
    const chip = document.createElement('div');
    chip.className = 'info-chip';
    chip.innerHTML = `<span class="info-chip-label">${label}</span><span class="info-chip-value">${value}</span>`;
    resultInfo.appendChild(chip);
  });

  // Players
  resultOriginalPlayer.src = originalObjectURL;
  const convertedURL = `${API_BASE}${data.download_url}`;
  resultConvertedPlayer.src = convertedURL;

  // Style label
  const styleCard = document.querySelector(`.style-card[data-id="${data.style}"]`);
  const styleName = styleCard ? styleCard.querySelector('.style-name').textContent : data.style;
  resultStyleLabel.textContent = styleName;

  // Download link
  downloadLink.href = convertedURL;
  downloadLink.download = `${selectedFile.name.replace(/\.[^.]+$/, '')}_${data.style}.wav`;

  resultSection.classList.remove('hidden');
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  showToast('Conversion complete!', 'success');
}

function formatDur(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

// =====================================================
// Convert another
// =====================================================
convertAnotherBtn.addEventListener('click', () => {
  resultSection.classList.add('hidden');
  clearFile();
  selectedStyle = null;
  document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
  convertRow.classList.add('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// =====================================================
// Init
// =====================================================
loadStyles();
