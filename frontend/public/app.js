/* ═══════════════════════════════════════════════
   NhạcSống Beat – Frontend Logic
   ═══════════════════════════════════════════════ */

const API = '';   // same-origin; set to http://localhost:8000 for standalone dev

// ── State ──
let file          = null;
let origURL       = null;
let selectedStyle = null;
let selectedBrand = 'yamaha';

// ── DOM ──
const dropzone    = document.getElementById('dropzone');
const fileInput   = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const fileNameEl  = document.getElementById('file-name');
const fileSizeEl  = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');
const origPlayer  = document.getElementById('original-player');

const optSection  = document.getElementById('options-section');
const styleSection= document.getElementById('style-section');
const styleGrid   = document.getElementById('style-grid');

const vocalToggle = document.getElementById('vocal-toggle');
const vocalRow    = document.getElementById('vocal-strength-row');
const vocalSlider = document.getElementById('vocal-strength');
const vocalDisp   = document.getElementById('vocal-strength-display');

const intensSlider= document.getElementById('intensity-slider');
const intensDisp  = document.getElementById('intensity-display');

const convertRow  = document.getElementById('convert-row');
const convertBtn  = document.getElementById('convert-btn');

const progSection = document.getElementById('progress-section');
const progTitle   = document.getElementById('progress-title');
const progSub     = document.getElementById('progress-sub');
const progBar     = document.getElementById('progress-bar');
const progStep    = document.getElementById('progress-step');

const resultSection = document.getElementById('result-section');
const resultChips   = document.getElementById('result-chips');
const resStyleName  = document.getElementById('res-style-name');
const resOrig       = document.getElementById('res-orig');
const resConv       = document.getElementById('res-conv');
const downloadLink  = document.getElementById('download-link');
const convAnother   = document.getElementById('convert-another');

const toastEl = document.getElementById('toast');

// ═══════════════════════════════
// Toast
// ═══════════════════════════════
let toastTimer = null;
function toast(msg, type = 'info') {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.className = 'toast hidden'; }, 4500);
}

// ═══════════════════════════════
// File handling
// ═══════════════════════════════
function fmtSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024 ** 2) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1024 ** 2).toFixed(2) + ' MB';
}

function setFile(f) {
  const ext = f.name.split('.').pop().toLowerCase();
  const ok  = ['mp3','wav','ogg','flac','m4a','aac'];
  if (!ok.includes(ext)) { toast('Định dạng không được hỗ trợ.', 'error'); return; }
  if (f.size > 50 * 1024 ** 2) { toast('File quá lớn (tối đa 50 MB).', 'error'); return; }

  file = f;
  fileNameEl.textContent = f.name;
  fileSizeEl.textContent = fmtSize(f.size);
  if (origURL) URL.revokeObjectURL(origURL);
  origURL = URL.createObjectURL(f);
  origPlayer.src = origURL;

  filePreview.classList.remove('hidden');
  dropzone.classList.add('hidden');

  optSection.classList.remove('hidden');
  styleSection.classList.remove('hidden');
  updateConvert();
}

function clearFile() {
  file = null;
  fileInput.value = '';
  filePreview.classList.add('hidden');
  dropzone.classList.remove('hidden');
  optSection.classList.add('hidden');
  styleSection.classList.add('hidden');
  convertRow.classList.add('hidden');
  if (origURL) { URL.revokeObjectURL(origURL); origURL = null; }
}

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault(); dropzone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });
removeFileBtn.addEventListener('click', clearFile);

// ═══════════════════════════════
// Options
// ═══════════════════════════════
vocalToggle.addEventListener('change', () => {
  vocalRow.style.opacity = vocalToggle.checked ? '1' : '0.4';
  vocalRow.style.pointerEvents = vocalToggle.checked ? 'auto' : 'none';
});

function syncSlider(slider, display, suffix = '%') {
  const v = slider.value;
  display.textContent = v + suffix;
  slider.style.background =
    `linear-gradient(to right, var(--accent) 0%, var(--accent) ${v}%, var(--border) ${v}%)`;
}

vocalSlider.addEventListener('input', () => syncSlider(vocalSlider, vocalDisp));
intensSlider.addEventListener('input', () => syncSlider(intensSlider, intensDisp));
syncSlider(vocalSlider, vocalDisp);
syncSlider(intensSlider, intensDisp);

// Brand selection
document.querySelectorAll('.brand-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.brand-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedBrand = card.dataset.brand;
  });
});

// ═══════════════════════════════
// Styles
// ═══════════════════════════════
async function loadStyles() {
  try {
    const res = await fetch(`${API}/api/styles`);
    const data = await res.json();
    renderStyles(data.styles);
  } catch {
    // fallback
    renderStyles([
      { id:'bolero',    emoji:'💙', name:'Bolero',      bpm:72,  mood:'Trữ tình, buồn' },
      { id:'rumba',     emoji:'🌹', name:'Rumba',        bpm:108, mood:'Lãng mạn, nhẹ nhàng' },
      { id:'chachacha', emoji:'💃', name:'Cha-cha-cha',  bpm:124, mood:'Vui tươi, sôi động' },
      { id:'slowrock',  emoji:'🎸', name:'Slow Rock',    bpm:76,  mood:'Cảm xúc, mạnh mẽ' },
      { id:'tango',     emoji:'🌊', name:'Tango',        bpm:122, mood:'Kịch tính, mạnh mẽ' },
      { id:'disco',     emoji:'🪩', name:'Disco',        bpm:122, mood:'Sôi động, vui nhộn' },
      { id:'valse',     emoji:'🌸', name:'Valse',        bpm:172, mood:'Lãng mạn, nhẹ nhàng' },
      { id:'fox',       emoji:'🦊', name:'Fox Trot',     bpm:135, mood:'Duyên dáng, nhẹ nhàng' },
      { id:'twist',     emoji:'🕺', name:'Twist',        bpm:130, mood:'Vui nhộn, retro' },
      { id:'ballade',   emoji:'🌙', name:'Ballade',      bpm:56,  mood:'Sâu lắng, cô đơn' },
    ]);
  }
}

function renderStyles(styles) {
  styleGrid.innerHTML = '';
  styles.forEach(s => {
    const card = document.createElement('div');
    card.className = 'style-card';
    card.dataset.id = s.id;
    card.innerHTML = `
      <div class="style-emoji">${s.emoji}</div>
      <div class="style-name">${s.name}</div>
      <div class="style-bpm">♩ ${s.bpm} BPM · ${s.time_sig || '4/4'}</div>
      <div class="style-mood">${s.mood}</div>
    `;
    card.addEventListener('click', () => {
      document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedStyle = s.id;
      updateConvert();
    });
    styleGrid.appendChild(card);
  });
}

function updateConvert() {
  convertRow.classList.toggle('hidden', !(file && selectedStyle));
}

// ═══════════════════════════════
// Progress simulation
// ═══════════════════════════════
const STEPS = [
  { pct:  8, msg: '📂 Đang đọc file âm thanh…' },
  { pct: 22, msg: '🎵 Phân tích BPM và nhịp…' },
  { pct: 40, msg: '🎤 Đang tách giọng vocal…' },
  { pct: 58, msg: '🎹 Áp dụng âm sắc Organ…' },
  { pct: 72, msg: '🔊 Xử lý hiệu ứng Leslie…' },
  { pct: 84, msg: '⚙️  Điều chỉnh EQ và dynamics…' },
  { pct: 93, msg: '✨ Chuẩn hoá output…' },
];

let progTimer = null;

function startProgress() {
  let i = 0;
  progBar.style.width = '3%';
  progTitle.textContent = 'Bắt đầu xử lý…';
  progStep.textContent  = '';
  progTimer = setInterval(() => {
    if (i >= STEPS.length) { clearInterval(progTimer); return; }
    progBar.style.width  = STEPS[i].pct + '%';
    progTitle.textContent = STEPS[i].msg;
    progStep.textContent  = `Bước ${i + 1} / ${STEPS.length}`;
    i++;
  }, 1100);
}

function stopProgress() {
  clearInterval(progTimer);
  progBar.style.width  = '100%';
  progTitle.textContent = '✅ Hoàn thành!';
  progStep.textContent  = '';
}

// ═══════════════════════════════
// Conversion
// ═══════════════════════════════
convertBtn.addEventListener('click', async () => {
  if (!file || !selectedStyle) return;

  convertRow.classList.add('hidden');
  resultSection.classList.add('hidden');
  progSection.classList.remove('hidden');
  startProgress();

  const fd = new FormData();
  fd.append('file', file);
  fd.append('style', selectedStyle);
  fd.append('intensity', (parseInt(intensSlider.value) / 100).toFixed(2));
  fd.append('vocal_removal', vocalToggle.checked);
  fd.append('vocal_strength', (parseInt(vocalSlider.value) / 100).toFixed(2));
  fd.append('organ_brand', selectedBrand);

  try {
    const res = await fetch(`${API}/api/convert`, { method: 'POST', body: fd });
    stopProgress();
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    showResult(data);
  } catch (err) {
    stopProgress();
    progSection.classList.add('hidden');
    convertRow.classList.remove('hidden');
    toast(`Lỗi: ${err.message}`, 'error');
  }
});

function fmtDur(s) {
  return `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;
}

function showResult(data) {
  progSection.classList.add('hidden');

  const info = data.info || {};

  // Chips
  resultChips.innerHTML = '';
  [
    { label: 'Điệu',        value: data.style.toUpperCase() },
    { label: 'BPM gốc',     value: info.original_bpm ? info.original_bpm + ' bpm' : '—' },
    { label: 'BPM mục tiêu',value: info.target_bpm ? info.target_bpm + ' bpm' : '—' },
    { label: 'Thời gian',   value: info.duration_sec ? fmtDur(info.duration_sec) : '—' },
    { label: 'Số nhịp',     value: info.beat_count ?? '—' },
    { label: 'Organ',       value: (info.organ_brand || '—').toUpperCase() },
    { label: 'Tách vocal',  value: info.vocal_removed ? '✅ Đã tách' : '⏭ Bỏ qua' },
  ].forEach(({ label, value }) => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.innerHTML = `<span class="chip-label">${label}</span><span class="chip-value">${value}</span>`;
    resultChips.appendChild(chip);
  });

  // Players
  resOrig.src = origURL;
  const convURL = `${API}${data.download_url}`;
  resConv.src = convURL;

  const card = document.querySelector(`.style-card[data-id="${data.style}"]`);
  resStyleName.textContent = card
    ? card.querySelector('.style-name').textContent + ' Beat'
    : 'Beat đã chuyển';

  downloadLink.href     = convURL;
  downloadLink.download = file.name.replace(/\.[^.]+$/, '') + `_${data.style}_karaoke.wav`;

  resultSection.classList.remove('hidden');
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  toast('Beat karaoke đã sẵn sàng! 🎹', 'success');
}

// ── Convert another ──
convAnother.addEventListener('click', () => {
  resultSection.classList.add('hidden');
  clearFile();
  selectedStyle = null;
  document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
  convertRow.classList.add('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Init ──
loadStyles();
