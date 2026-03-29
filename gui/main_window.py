"""
BeatStyle – Main Window (PySide6)

Layout (vertical scroll):
  ┌─ Header ────────────────────────────────────────┐
  ├─ BƯỚC 1 · Upload Beat ──────────────────────────┤
  │   drop-zone  OR  file-bar + waveform + player   │
  ├─ BƯỚC 2 · Chọn Style ──────────────────────────┤
  │   Nhạc Sống / Rock & Metal / Modern             │
  ├─ BƯỚC 3 · Cường độ hiệu ứng ───────────────────┤
  │   preset buttons + slider                        │
  ├─ [🎛️ CHUYỂN BEAT] ──────────────────────────────┤
  ├─ Progress bar (hidden until converting) ─────────┤
  └─ Result (hidden until done) ────────────────────┘
"""

from __future__ import annotations

import os, sys, shutil, tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore  import Qt, QMimeData, QTimer, QSize
from PySide6.QtGui   import QDragEnterEvent, QDropEvent, QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QScrollArea, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QProgressBar,
    QFileDialog, QMessageBox, QSizePolicy, QGroupBox,
    QApplication,
)

from .theme   import QSS, C
from .widgets  import WaveformWidget, AudioPlayer, StyleCard, SectionCard
from .worker   import ConvertWorker


# ─────────────────────────────────────────────────────
#  Style catalogue
# ─────────────────────────────────────────────────────

STYLE_GROUPS = [
    {
        "label": "🎹 Nhạc Sống Việt Nam",
        "styles": [
            ("bolero",    "💙", "Bolero",      72,  "4/4", "Trữ tình · Yamaha organ"),
            ("rumba",     "🌹", "Rumba",        108, "4/4", "Lãng mạn · Latin groove"),
            ("chachacha", "💃", "Cha-cha-cha",  124, "4/4", "Vui tươi · Roland organ"),
            ("slowrock",  "🎹", "Slow Rock",    76,  "4/4", "Organ + nhẹ overdrive"),
            ("tango",     "🌊", "Tango",        122, "4/4", "Kịch tính · Roland"),
            ("valse",     "🌸", "Valse",        172, "3/4", "Nhịp 3/4 · Yamaha ấm"),
        ],
    },
    {
        "label": "🎸 Rock & Metal",
        "styles": [
            ("hardrock",   "🎸", "Hard Rock",   120, "4/4", "Marshall amp · punchy"),
            ("heavymetal", "💀", "Heavy Metal", 160, "4/4", "High-gain · scooped mids"),
            ("numetal",    "🔥", "Nu-Metal",    100, "4/4", "Groove + heavy"),
            ("punk",       "⚡", "Punk Rock",   180, "4/4", "Raw · fast · lo-fi"),
        ],
    },
    {
        "label": "🎧 Modern",
        "styles": [
            ("edm",    "🎧", "EDM",          128, "4/4", "Sidechain · sub-bass"),
            ("trap",   "🔊", "Trap",         80,  "4/4", "808 · hi-hat space"),
            ("lofi",   "🎵", "Lo-fi",        75,  "4/4", "Vinyl · warm · chill"),
            ("rnb",    "💜", "R&B / Soul",   90,  "4/4", "Smooth · tape warmth"),
            ("phonk",  "🌑", "Phonk",        130, "4/4", "Memphis · 808 grit"),
            ("ambient","🌊", "Ambient",      70,  "4/4", "Dreamy · massive reverb"),
        ],
    },
]

INTENSITY_PRESETS = [
    (30,  "Nhẹ",       "Giữ phần lớn âm gốc, thêm màu nhẹ."),
    (70,  "Chuẩn",     "Cân bằng giữa beat gốc và style mới."),
    (100, "Mạnh nhất", "Toàn bộ hiệu ứng, sound thay đổi hoàn toàn."),
]

OUTPUT_DIR = Path(tempfile.gettempdir()) / "beatstyle_output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────
#  Drop-zone frame
# ─────────────────────────────────────────────────────

class DropZone(QFrame):
    """Drag-and-drop area for audio files."""
    file_dropped = __import__("PySide6.QtCore", fromlist=["Signal"]).Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setFixedHeight(160)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        em = QLabel("🎚️")
        em.setAlignment(Qt.AlignCenter)
        em.setStyleSheet("font-size:36px; background:transparent;")
        lay.addWidget(em)

        t = QLabel("Kéo thả beat vào đây")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"font-weight:600; font-size:14px; background:transparent; color:{C['text']};")
        lay.addWidget(t)

        h = QLabel("MP3 · WAV · FLAC · OGG · M4A · Tối đa 50 MB")
        h.setAlignment(Qt.AlignCenter)
        h.setStyleSheet(f"font-size:11px; background:transparent; color:{C['muted']};")
        lay.addWidget(h)

        btn = QPushButton("Chọn file")
        btn.setFixedWidth(120)
        btn.clicked.connect(self._browse)
        lay.addWidget(btn, alignment=Qt.AlignCenter)

    # ── Drag events ──────────────────────
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setProperty("drag", "true")
            self.style().unpolish(self); self.style().polish(self)

    def dragLeaveEvent(self, _):
        self.setProperty("drag", "false")
        self.style().unpolish(self); self.style().polish(self)

    def dropEvent(self, e: QDropEvent):
        self.setProperty("drag", "false")
        self.style().unpolish(self); self.style().polish(self)
        urls = e.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())

    def mousePressEvent(self, _):
        self._browse()

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn beat", "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)"
        )
        if path:
            self.file_dropped.emit(path)


# ─────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._beat_path: Optional[str] = None
        self._out_path:  Optional[str] = None
        self._chosen_style: Optional[tuple] = None  # (id, name, emoji)
        self._style_cards: list[StyleCard] = []
        self._worker: Optional[ConvertWorker] = None

        self._setup_window()
        self._build_ui()

    # ══════════════════════════════════════
    #  Window setup
    # ══════════════════════════════════════

    def _setup_window(self):
        self.setWindowTitle("BeatStyle – Chuyển Beat sang Style Khác")
        self.setMinimumSize(960, 700)
        self.resize(1060, 820)
        self.setStyleSheet(QSS)

    # ══════════════════════════════════════
    #  UI construction
    # ══════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        central.setStyleSheet(f"background:{C['bg']};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea{{background:{C['bg']};border:none;}}")

        content = QWidget()
        content.setStyleSheet(f"background:{C['bg']};")
        self._main_lay = QVBoxLayout(content)
        self._main_lay.setContentsMargins(24, 24, 24, 40)
        self._main_lay.setSpacing(16)

        self._build_header()
        self._build_upload_section()
        self._build_style_section()
        self._build_intensity_section()
        self._build_convert_row()
        self._build_progress_section()
        self._build_result_section()
        self._main_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

        # Initial visibility
        self._style_card_widget.hide()
        self._intensity_card.hide()
        self._convert_row.hide()
        self._progress_card.hide()
        self._result_card.hide()

    # ── Header ────────────────────────────

    def _build_header(self):
        hdr = QWidget()
        hdr.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(hdr)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        title = QLabel("🎛️  Beat<span style='color:#a855f7;'>Style</span>")
        title.setTextFormat(Qt.RichText)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size:32px; font-weight:800; letter-spacing:-1px; "
            f"background:transparent; color:{C['text']};"
        )
        lay.addWidget(title)

        sub = QLabel(
            "Upload beat gốc (đã tách vocal)  →  Chọn style  →  Chuyển đổi<br>"
            "<span style='color:#4a4a70; font-size:11px;'>"
            "Nhạc Sống · Hard Rock · Heavy Metal · EDM · Trap · Lo-fi …"
            "</span>"
        )
        sub.setTextFormat(Qt.RichText)
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("background:transparent; font-size:13px; color:#7070a0;")
        lay.addWidget(sub)

        self._main_lay.addWidget(hdr)

    # ── Upload section ─────────────────────

    def _build_upload_section(self):
        self._upload_card = SectionCard("BƯỚC 1 · UPLOAD BEAT")
        lay = self._upload_card.inner_layout()

        # Drop zone (shown when no file)
        self._drop_zone = DropZone()
        self._drop_zone.file_dropped.connect(self._on_file_chosen)
        lay.addWidget(self._drop_zone)

        # File bar (shown after file chosen)
        self._file_bar = QWidget()
        self._file_bar.hide()
        fb_lay = QHBoxLayout(self._file_bar)
        fb_lay.setContentsMargins(0, 0, 0, 0)
        fb_lay.setSpacing(10)

        self._fb_icon = QLabel("🎚️")
        self._fb_icon.setStyleSheet("font-size:24px; background:transparent;")
        fb_lay.addWidget(self._fb_icon)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self._fb_name = QLabel("—")
        self._fb_name.setStyleSheet(f"font-weight:600; font-size:13px; background:transparent; color:{C['text']};")
        self._fb_size = QLabel("")
        self._fb_size.setStyleSheet(f"font-size:11px; background:transparent; color:{C['muted']};")
        info_col.addWidget(self._fb_name)
        info_col.addWidget(self._fb_size)
        fb_lay.addLayout(info_col)
        fb_lay.addStretch()

        btn_rem = QPushButton("✕  Xoá")
        btn_rem.setFixedHeight(30)
        btn_rem.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {C['border']};"
            f"border-radius:6px;color:{C['muted']};font-size:11px;padding:2px 10px;}}"
            f"QPushButton:hover{{border-color:{C['red']};color:{C['red']};}}"
        )
        btn_rem.clicked.connect(self._clear_file)
        fb_lay.addWidget(btn_rem)
        lay.addWidget(self._file_bar)

        # Original audio player with waveform
        self._orig_player = AudioPlayer(
            label="Beat gốc", wave_color=C["muted"]
        )
        self._orig_player.hide()
        lay.addWidget(self._orig_player)

        self._main_lay.addWidget(self._upload_card)

    # ── Style section ──────────────────────

    def _build_style_section(self):
        self._style_card_widget = SectionCard("BƯỚC 2 · CHỌN STYLE MỚI")
        lay = self._style_card_widget.inner_layout()

        for group in STYLE_GROUPS:
            gb = QGroupBox(group["label"])
            gb.setStyleSheet(
                f"QGroupBox{{color:{C['muted']};font-size:11px;font-weight:700;"
                f"letter-spacing:1.5px;border:none;margin-top:4px;padding-top:18px;}}"
                f"QGroupBox::title{{subcontrol-origin:margin;left:0;top:0;}}"
            )
            grid = QGridLayout(gb)
            grid.setSpacing(8)
            grid.setContentsMargins(0, 6, 0, 0)

            for col, (sid, emoji, name, bpm, time_sig, desc) in enumerate(group["styles"]):
                card = StyleCard(sid, emoji, name, bpm, time_sig, desc)
                card.clicked.connect(lambda checked, c=card: self._on_style_clicked(c))
                grid.addWidget(card, 0, col)
                self._style_cards.append(card)

            # Stretch empty columns so cards don't expand
            for c in range(len(group["styles"]), 8):
                grid.setColumnStretch(c, 1)

            lay.addWidget(gb)

        self._main_lay.addWidget(self._style_card_widget)

    # ── Intensity section ──────────────────

    def _build_intensity_section(self):
        self._intensity_card = SectionCard("BƯỚC 3 · CƯỜNG ĐỘ HIỆU ỨNG")
        lay = self._intensity_card.inner_layout()

        # Preset buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        self._preset_btns: list[QPushButton] = []
        for val, label, _ in INTENSITY_PRESETS:
            btn = QPushButton(f"{label}\n{val}%")
            btn.setObjectName("preset")
            btn.setProperty("active", "false")
            btn.setFixedHeight(54)
            btn.clicked.connect(lambda _, v=val: self._set_intensity(v))
            preset_row.addWidget(btn)
            self._preset_btns.append(btn)
        lay.addLayout(preset_row)

        # Slider row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)

        self._ix_slider = QSlider(Qt.Horizontal)
        self._ix_slider.setRange(0, 100)
        self._ix_slider.setValue(70)
        self._ix_slider.valueChanged.connect(self._on_ix_changed)

        self._ix_lbl = QLabel("70%")
        self._ix_lbl.setFixedWidth(40)
        self._ix_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._ix_lbl.setStyleSheet(f"color:{C['accent2']};font-weight:700;font-size:14px;background:transparent;")

        slider_row.addWidget(self._ix_slider)
        slider_row.addWidget(self._ix_lbl)
        lay.addLayout(slider_row)

        # Description
        self._ix_desc = QLabel(INTENSITY_PRESETS[1][2])
        self._ix_desc.setStyleSheet(f"color:{C['muted']};font-size:11px;font-style:italic;background:transparent;")
        lay.addWidget(self._ix_desc)

        self._set_intensity(70)
        self._main_lay.addWidget(self._intensity_card)

    # ── Convert button row ─────────────────

    def _build_convert_row(self):
        self._convert_row = QWidget()
        self._convert_row.setStyleSheet("background:transparent;")
        row_lay = QVBoxLayout(self._convert_row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(10)
        row_lay.setAlignment(Qt.AlignCenter)

        # Summary chip
        self._summary_lbl = QLabel()
        self._summary_lbl.setAlignment(Qt.AlignCenter)
        self._summary_lbl.setStyleSheet(
            f"background:{C['hover']};border:1px solid {C['border_hi']};"
            f"border-radius:10px;padding:10px 18px;font-size:13px;"
        )
        row_lay.addWidget(self._summary_lbl)

        self._btn_convert = QPushButton("🎛️   Chuyển Beat")
        self._btn_convert.setObjectName("primary")
        self._btn_convert.setFixedHeight(52)
        self._btn_convert.setFixedWidth(260)
        self._btn_convert.clicked.connect(self._start_convert)
        row_lay.addWidget(self._btn_convert, alignment=Qt.AlignCenter)

        self._main_lay.addWidget(self._convert_row)

    # ── Progress section ────────────────────

    def _build_progress_section(self):
        self._progress_card = SectionCard("CONVERTANDO…")
        self._progress_card.set_tag_color(C["accent"])
        lay = self._progress_card.inner_layout()
        lay.setAlignment(Qt.AlignCenter)

        self._prog_title = QLabel("Đang xử lý…")
        self._prog_title.setAlignment(Qt.AlignCenter)
        self._prog_title.setStyleSheet(f"font-weight:600;font-size:14px;background:transparent;")
        lay.addWidget(self._prog_title)

        self._prog_bar = QProgressBar()
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setValue(0)
        self._prog_bar.setFixedHeight(10)
        lay.addWidget(self._prog_bar)

        self._prog_step = QLabel("")
        self._prog_step.setAlignment(Qt.AlignCenter)
        self._prog_step.setStyleSheet(f"color:{C['muted']};font-size:11px;background:transparent;")
        lay.addWidget(self._prog_step)

        self._main_lay.addWidget(self._progress_card)

    # ── Result section ─────────────────────

    def _build_result_section(self):
        self._result_card = SectionCard("✅  HOÀN THÀNH")
        self._result_card.set_tag_color(C["green"])
        lay = self._result_card.inner_layout()

        # Meta chips row
        self._chip_row = QHBoxLayout()
        self._chip_row.setSpacing(8)
        lay.addLayout(self._chip_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{C['border']};")
        lay.addWidget(sep)

        # Before/After players
        compare = QHBoxLayout()
        compare.setSpacing(20)

        self._res_orig = AudioPlayer(label="◉  Beat gốc", wave_color=C["muted"])
        self._res_conv = AudioPlayer(label="◉  Style mới", wave_color=C["accent"])

        compare.addWidget(self._res_orig)

        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet(f"font-size:22px; color:{C['accent2']}; background:transparent;")
        arrow.setFixedWidth(30)
        compare.addWidget(arrow)

        compare.addWidget(self._res_conv)
        lay.addLayout(compare)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{C['border']};")
        lay.addWidget(sep2)

        # Action row
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        self._btn_dl = QPushButton("⬇  Tải về WAV")
        self._btn_dl.setObjectName("dl")
        self._btn_dl.setFixedHeight(40)
        self._btn_dl.clicked.connect(self._do_download)

        btn_re_style = QPushButton("🎛️  Đổi style khác")
        btn_re_style.setFixedHeight(40)
        btn_re_style.clicked.connect(self._re_style)

        btn_another = QPushButton("🔄  Beat khác")
        btn_another.setFixedHeight(40)
        btn_another.clicked.connect(self._clear_all)

        act_row.addWidget(self._btn_dl)
        act_row.addWidget(btn_re_style)
        act_row.addWidget(btn_another)
        act_row.addStretch()
        lay.addLayout(act_row)

        self._main_lay.addWidget(self._result_card)

    # ══════════════════════════════════════
    #  Event handlers
    # ══════════════════════════════════════

    def _on_file_chosen(self, path: str):
        if not os.path.isfile(path):
            return
        ext = Path(path).suffix.lower()
        if ext not in {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}:
            QMessageBox.warning(self, "Định dạng không hỗ trợ",
                                f"Vui lòng chọn file âm thanh (MP3/WAV/FLAC/OGG/M4A).\nGot: {ext}")
            return
        size = os.path.getsize(path)
        if size > 50 * 1024 ** 2:
            QMessageBox.warning(self, "File quá lớn", "Tối đa 50 MB.")
            return

        self._beat_path = path
        self._fb_name.setText(Path(path).name)
        self._fb_size.setText(self._fmt_size(size))

        self._drop_zone.hide()
        self._file_bar.show()
        self._orig_player.load(path)
        self._orig_player.show()

        self._style_card_widget.show()
        self._intensity_card.show()
        self._update_convert_row()

        # Scroll to style section
        QTimer.singleShot(50, lambda: self._style_card_widget.setFocus())

    def _clear_file(self):
        self._beat_path = None
        self._drop_zone.show()
        self._file_bar.hide()
        self._orig_player.clear()
        self._orig_player.hide()
        self._style_card_widget.hide()
        self._intensity_card.hide()
        self._convert_row.hide()

    def _on_style_clicked(self, card: StyleCard):
        for c in self._style_cards:
            c.set_selected(False)
        card.set_selected(True)

        # Find name/emoji
        for group in STYLE_GROUPS:
            for sid, emoji, name, *_ in group["styles"]:
                if sid == card.sid:
                    self._chosen_style = (sid, name, emoji)
                    break

        self._update_convert_row()

    def _set_intensity(self, val: int):
        self._ix_slider.setValue(val)
        self._ix_lbl.setText(f"{val}%")
        for btn, (pv, _, desc) in zip(self._preset_btns, INTENSITY_PRESETS):
            active = (pv == val)
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)
            if active:
                self._ix_desc.setText(desc)
        self._update_convert_row()

    def _on_ix_changed(self, val: int):
        self._ix_lbl.setText(f"{val}%")
        # Update presets
        for btn, (pv, _, desc) in zip(self._preset_btns, INTENSITY_PRESETS):
            active = (pv == val)
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)
            if active:
                self._ix_desc.setText(desc)
        # Set generic desc if not a preset
        if val not in [p[0] for p in INTENSITY_PRESETS]:
            if val < 40:
                self._ix_desc.setText(INTENSITY_PRESETS[0][2])
            elif val < 80:
                self._ix_desc.setText(INTENSITY_PRESETS[1][2])
            else:
                self._ix_desc.setText(INTENSITY_PRESETS[2][2])
        self._update_convert_row()

    def _update_convert_row(self):
        if self._beat_path and self._chosen_style:
            sid, name, emoji = self._chosen_style
            ix = self._ix_slider.value()
            self._summary_lbl.setText(
                f"<b>{Path(self._beat_path).name}</b>"
                f"  <span style='color:{C['accent2']}'>→</span>  "
                f"<b>{emoji} {name}</b>"
                f"  <span style='color:{C['muted']}'>@ {ix}%</span>"
            )
            self._convert_row.show()
        else:
            self._convert_row.hide()

    # ── Conversion ──────────────────────────

    def _start_convert(self):
        if not self._beat_path or not self._chosen_style:
            return

        sid, name, emoji = self._chosen_style
        intensity = self._ix_slider.value() / 100.0
        fname = Path(self._beat_path).stem + f"_{sid}.wav"
        self._out_path = str(OUTPUT_DIR / fname)

        # UI: show progress
        self._convert_row.hide()
        self._result_card.hide()
        self._progress_card.show()
        self._prog_bar.setValue(0)
        self._prog_title.setText("Bắt đầu xử lý…")
        self._prog_step.setText("")
        self._btn_convert.setEnabled(False)

        # Worker
        self._worker = ConvertWorker(
            self._beat_path, self._out_path, sid, intensity
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self._prog_bar.setValue(pct)
        self._prog_title.setText(msg)

    def _on_finished(self, info: dict):
        self._progress_card.hide()
        self._btn_convert.setEnabled(True)
        self._show_result(info)

    def _on_error(self, msg: str):
        self._progress_card.hide()
        self._convert_row.show()
        self._btn_convert.setEnabled(True)
        QMessageBox.critical(self, "Lỗi xử lý", f"Quá trình chuyển beat thất bại:\n\n{msg}")

    # ── Result display ──────────────────────

    def _show_result(self, info: dict):
        # Clear old chips
        while self._chip_row.count():
            item = self._chip_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sid, name, emoji = self._chosen_style
        chips = [
            ("Style",       f"{emoji} {name}"),
            ("BPM gốc",     f"{info.get('original_bpm', '—')} bpm"),
            ("BPM mục tiêu",f"{info.get('target_bpm', '—')} bpm"),
            ("Thời gian",   self._fmt_dur(info.get("duration_sec", 0))),
            ("Nhịp",        str(info.get("beat_count", "—"))),
        ]
        for lbl, val in chips:
            chip = QFrame()
            chip.setStyleSheet(
                f"background:{C['hover']};border:1px solid {C['border']};"
                f"border-radius:8px;padding:6px 12px;"
            )
            cl = QVBoxLayout(chip)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(1)
            l1 = QLabel(lbl)
            l1.setStyleSheet(f"font-size:9px;color:{C['muted']};text-transform:uppercase;letter-spacing:.5px;background:transparent;")
            l2 = QLabel(val)
            l2.setStyleSheet(f"font-weight:700;font-size:13px;color:{C['accent2']};background:transparent;")
            cl.addWidget(l1); cl.addWidget(l2)
            self._chip_row.addWidget(chip)
        self._chip_row.addStretch()

        # Load players
        self._res_orig.load(self._beat_path)
        self._res_conv.load(self._out_path)

        self._result_card.show()
        # Scroll to result
        QTimer.singleShot(80, lambda: self._result_card.setFocus())

    # ── Actions ─────────────────────────────

    def _do_download(self):
        if not self._out_path or not os.path.exists(self._out_path):
            return
        sid, name, _ = self._chosen_style
        default = str(Path.home() / "Downloads" /
                      (Path(self._beat_path).stem + f"_{sid}_beatstyle.wav"))
        dest, _ = QFileDialog.getSaveFileName(
            self, "Lưu beat", default, "WAV Files (*.wav)"
        )
        if dest:
            shutil.copy2(self._out_path, dest)
            QMessageBox.information(self, "Đã lưu", f"Đã lưu:\n{dest}")

    def _re_style(self):
        """Keep same file, let user pick a different style."""
        self._result_card.hide()
        self._convert_row.show()
        self._style_card_widget.setFocus()

    def _clear_all(self):
        self._result_card.hide()
        self._res_orig.clear()
        self._res_conv.clear()
        for c in self._style_cards:
            c.set_selected(False)
        self._chosen_style = None
        self._out_path = None
        self._clear_file()

    # ── Helpers ─────────────────────────────

    @staticmethod
    def _fmt_size(b: int) -> str:
        if b < 1024:          return f"{b} B"
        if b < 1024 ** 2:     return f"{b/1024:.1f} KB"
        return f"{b/1024**2:.2f} MB"

    @staticmethod
    def _fmt_dur(sec: float) -> str:
        s = int(sec)
        return f"{s//60}:{s%60:02d}"
