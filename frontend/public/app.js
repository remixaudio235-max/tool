/* ═══════════════════════════════════════
   BeatStyle – app logic
   ═══════════════════════════════════════ */

const API = '';   // same-origin

// ── State ──────────────────────────────
let beatFile   = null;
let origURL    = null;
let chosenStyle = null;   // { id, name, emoji }

// ── DOM refs ────────────────────────────
const dropzone   = document.getElementById('dropzone');
const fileInput  = document.getElementById('file-input');
const fileBar    = document.getElementById('file-bar');
const fbName     = document.getElementById('fb-name');
const fbSize     = document.getElementById('fb-size');
const btnRemove  = document.getElementById('btn-remove');
const origPlayer = document.getElementById('orig-player');

const styleCard  = document.getElementById('style-card');
const styleGroups= document.getElementById('style-groups');

const ixCard     = document.getElementById('intensity-card');
const ixSlider   = document.getElementById('ix-slider');
const ixVal      = document.getElementById('ix-val');
const ixDesc     = document.getElementById('ix-desc');
const presets    = document.querySelectorAll('.preset');

const convertRow = document.getElementById('convert-row');
const selSummary = document.getElementById('selected-summary');
const btnConvert = document.getElementById('btn-convert');

const progWrap   = document.getElementById('progress-wrap');
const progTitle  = document.getElementById('prog-title');
const progBar    = document.getElementById('prog-bar');
const progStep   = document.getElementById('prog-step');

const resultCard = document.getElementById('result-card');
const resultMeta = document.getElementById('result-meta');
const rStyleName = document.getElementById('r-style-name');
const rOrig      = document.getElementById('r-orig');
const rConv      = document.getElementById('r-conv');
const dlLink     = document.getElementById('dl-link');
const btnAnother = document.getElementById('btn-another');
const btnReStyle = document.getElementById('btn-re-style');

const toastEl    = document.getElementById('toast');

// ── Toast ───────────────────────────────
let toastTimer = null;
function toast(msg, type = 'info') {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.className = 'toast hidden'; }, 4000);
}

// ── File handling ───────────────────────
const FMT = n =>
  n < 1024 ? n + ' B' :
  n < 1048576 ? (n/1024).toFixed(1) + ' KB' :
  (n/1048576).toFixed(2) + ' MB';

function setFile(f) {
  const ext = f.name.split('.').pop().toLowerCase();
  if (!['mp3','wav','ogg','flac','m4a','aac'].includes(ext))
    return toast('Định dạng không hỗ trợ.', 'error');
  if (f.size > 50 * 1024 ** 2)
    return toast('File quá lớn (tối đa 50 MB).', 'error');

  beatFile = f;
  fbName.textContent = f.name;
  fbSize.textContent = FMT(f.size);
  if (origURL) URL.revokeObjectURL(origURL);
  origURL = URL.createObjectURL(f);
  origPlayer.src = origURL;

  fileBar.classList.remove('hidden');
  origPlayer.classList.remove('hidden');
  dropzone.classList.add('hidden');

  styleCard.classList.remove('hidden');
  ixCard.classList.remove('hidden');
  updateConvert();
}

function clearFile() {
  beatFile = null; fileInput.value = '';
  fileBar.classList.add('hidden');
  origPlayer.classList.add('hidden');
  dropzone.classList.remove('hidden');
  styleCard.classList.add('hidden');
  ixCard.classList.add('hidden');
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
btnRemove.addEventListener('click', clearFile);

// ── Intensity ───────────────────────────
const IX_DESCS = {
  low:  'Giữ phần lớn âm thanh gốc, chỉ thêm màu sắc nhẹ.',
  mid:  'Style được áp dụng ở mức chuẩn, cân bằng giữa gốc và mới.',
  high: 'Toàn bộ hiệu ứng style, sound thay đổi hoàn toàn.',
};

function syncIx(val) {
  ixVal.textContent = val + '%';
  ixSlider.style.background =
    `linear-gradient(to right,var(--acc) 0%,var(--acc) ${val}%,var(--b) ${val}%)`;
  ixDesc.textContent =
    val < 40 ? IX_DESCS.low :
    val < 80 ? IX_DESCS.mid : IX_DESCS.high;

  presets.forEach(p => {
    p.classList.toggle('active', parseInt(p.dataset.val) === parseInt(val));
  });
}

ixSlider.addEventListener('input', () => syncIx(ixSlider.value));
presets.forEach(p => {
  p.addEventListener('click', () => {
    ixSlider.value = p.dataset.val;
    syncIx(p.dataset.val);
  });
});
syncIx(70);

// ── Style picker ─────────────────────────
async function loadStyles() {
  try {
    const res = await fetch(`${API}/api/styles`);
    const { groups } = await res.json();
    renderGroups(groups);
  } catch {
    renderGroups([
      { label: '🎹 Nhạc Sống Việt Nam', styles: [
        { id:'bolero',    emoji:'💙', name:'Bolero',      bpm:72,  time:'4/4', desc:'Trữ tình, sâu lắng — Yamaha organ' },
        { id:'rumba',     emoji:'🌹', name:'Rumba',        bpm:108, time:'4/4', desc:'Lãng mạn, Latin groove' },
        { id:'chachacha', emoji:'💃', name:'Cha-cha-cha',  bpm:124, time:'4/4', desc:'Vui tươi, Roland organ' },
        { id:'slowrock',  emoji:'🎹', name:'Slow Rock',    bpm:76,  time:'4/4', desc:'Organ + nhẹ overdrive' },
        { id:'tango',     emoji:'🌊', name:'Tango',        bpm:122, time:'4/4', desc:'Kịch tính, mạnh mẽ' },
        { id:'valse',     emoji:'🌸', name:'Valse',        bpm:172, time:'3/4', desc:'Nhịp 3/4 lả lướt' },
      ]},
      { label: '🎸 Rock & Metal', styles: [
        { id:'hardrock',   emoji:'🎸', name:'Hard Rock',   bpm:120, time:'4/4', desc:'Marshall amp, punchy' },
        { id:'heavymetal', emoji:'💀', name:'Heavy Metal', bpm:160, time:'4/4', desc:'High-gain, scooped mids' },
        { id:'numetal',    emoji:'🔥', name:'Nu-Metal',    bpm:100, time:'4/4', desc:'Groove + heavy' },
        { id:'punk',       emoji:'⚡', name:'Punk Rock',   bpm:180, time:'4/4', desc:'Raw, fast, lo-fi' },
      ]},
      { label: '🎧 Modern', styles: [
        { id:'edm',    emoji:'🎧', name:'EDM',          bpm:128, time:'4/4', desc:'Sidechain, sub-bass' },
        { id:'trap',   emoji:'🔊', name:'Trap',         bpm:80,  time:'4/4', desc:'808, hi-hat space' },
        { id:'lofi',   emoji:'🎵', name:'Lo-fi',        bpm:75,  time:'4/4', desc:'Vinyl crackle, warm' },
        { id:'rnb',    emoji:'💜', name:'R&B / Soul',   bpm:90,  time:'4/4', desc:'Smooth, tape warmth' },
        { id:'phonk',  emoji:'🌑', name:'Phonk',        bpm:130, time:'4/4', desc:'Memphis, distorted 808' },
        { id:'ambient',emoji:'🌊', name:'Ambient',      bpm:70,  time:'4/4', desc:'Dreamy, massive reverb' },
      ]},
    ]);
  }
}

function renderGroups(groups) {
  styleGroups.innerHTML = '';
  groups.forEach(g => {
    const section = document.createElement('div');
    section.innerHTML = `<p class="group-label">${g.label}</p>`;
    const grid = document.createElement('div');
    grid.className = 'style-grid';
    g.styles.forEach(s => {
      const btn = document.createElement('div');
      btn.className = 'style-btn';
      btn.dataset.id = s.id;
      btn.innerHTML = `
        <div class="sty-emoji">${s.emoji}</div>
        <div class="sty-name">${s.name}</div>
        <div class="sty-bpm">♩ ${s.bpm} · ${s.time}</div>
        <div class="sty-desc">${s.desc}</div>
      `;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('sel'));
        btn.classList.add('sel');
        chosenStyle = { id: s.id, name: s.name, emoji: s.emoji };
        updateConvert();
      });
      grid.appendChild(btn);
    });
    section.appendChild(grid);
    styleGroups.appendChild(section);
  });
}

// ── Convert row ──────────────────────────
function updateConvert() {
  if (beatFile && chosenStyle) {
    selSummary.innerHTML = `
      <span>${beatFile.name}</span>
      <span class="sum-arrow">→</span>
      <strong>${chosenStyle.emoji} ${chosenStyle.name}</strong>
      <span style="color:var(--muted);font-size:.8rem">@ ${ixSlider.value}%</span>
    `;
    convertRow.classList.remove('hidden');
  } else {
    convertRow.classList.add('hidden');
  }
}

ixSlider.addEventListener('input', updateConvert);

// ── Progress steps ───────────────────────
const STEPS = [
  { pct: 8,  msg: '📂 Đọc file beat…' },
  { pct: 20, msg: '🎵 Phân tích BPM, nhịp…' },
  { pct: 35, msg: '⏱ Chuẩn hoá tempo…' },
  { pct: 52, msg: '🎛️  Áp dụng EQ & dynamics…' },
  { pct: 68, msg: '🔊 Xử lý hiệu ứng style…' },
  { pct: 82, msg: '🎹 Giả lập amp / organ…' },
  { pct: 92, msg: '✨ Normalize & export…' },
];

let progTimer = null;
function startProg() {
  let i = 0;
  progBar.style.width = '3%';
  progTitle.textContent = 'Bắt đầu…';
  progStep.textContent  = '';
  progTimer = setInterval(() => {
    if (i >= STEPS.length) { clearInterval(progTimer); return; }
    progBar.style.width  = STEPS[i].pct + '%';
    progTitle.textContent = STEPS[i].msg;
    progStep.textContent  = `Bước ${i+1} / ${STEPS.length}`;
    i++;
  }, 1000);
}
function stopProg() {
  clearInterval(progTimer);
  progBar.style.width   = '100%';
  progTitle.textContent = '✅ Hoàn thành!';
  progStep.textContent  = '';
}

// ── Convert ──────────────────────────────
btnConvert.addEventListener('click', async () => {
  if (!beatFile || !chosenStyle) return;

  convertRow.classList.add('hidden');
  resultCard.classList.add('hidden');
  progWrap.classList.remove('hidden');
  startProg();

  const fd = new FormData();
  fd.append('file', beatFile);
  fd.append('style', chosenStyle.id);
  fd.append('intensity', (parseInt(ixSlider.value) / 100).toFixed(2));

  try {
    const res = await fetch(`${API}/api/convert`, { method:'POST', body:fd });
    stopProg();
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail:`HTTP ${res.status}` }));
      throw new Error(err.detail);
    }
    showResult(await res.json());
  } catch (e) {
    stopProg();
    progWrap.classList.add('hidden');
    convertRow.classList.remove('hidden');
    toast(`Lỗi: ${e.message}`, 'error');
  }
});

// ── Show result ──────────────────────────
function fmtDur(s) {
  return `${Math.floor(s/60)}:${String(Math.round(s%60)).padStart(2,'0')}`;
}

function showResult(data) {
  progWrap.classList.add('hidden');
  const i = data.info || {};

  resultMeta.innerHTML = '';
  [
    { l:'Style',        v: data.style_name },
    { l:'BPM gốc',      v: i.original_bpm ? i.original_bpm + ' bpm' : '—' },
    { l:'BPM mục tiêu', v: i.target_bpm   ? i.target_bpm   + ' bpm' : '—' },
    { l:'Thời gian',    v: i.duration_sec  ? fmtDur(i.duration_sec)  : '—' },
    { l:'Số nhịp',      v: i.beat_count    ?? '—' },
  ].forEach(({ l, v }) => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.innerHTML = `<span class="chip-l">${l}</span><span class="chip-v">${v}</span>`;
    resultMeta.appendChild(chip);
  });

  rOrig.src = origURL;
  const convURL = `${API}${data.download_url}`;
  rConv.src = convURL;
  rStyleName.textContent = `${data.style_name} Beat`;

  dlLink.href     = convURL;
  dlLink.download = beatFile.name.replace(/\.[^.]+$/, '') + `_${data.style}.wav`;

  resultCard.classList.remove('hidden');
  resultCard.scrollIntoView({ behavior:'smooth', block:'start' });
  toast(`${chosenStyle.emoji} Beat ${data.style_name} sẵn sàng!`, 'success');
}

// ── Re-actions ───────────────────────────
btnAnother.addEventListener('click', () => {
  resultCard.classList.add('hidden');
  clearFile();
  chosenStyle = null;
  document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('sel'));
  convertRow.classList.add('hidden');
  window.scrollTo({ top:0, behavior:'smooth' });
});

btnReStyle.addEventListener('click', () => {
  resultCard.classList.add('hidden');
  styleCard.scrollIntoView({ behavior:'smooth', block:'start' });
});

// ── Init ─────────────────────────────────
loadStyles();
