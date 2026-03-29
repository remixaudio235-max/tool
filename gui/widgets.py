"""
Reusable widgets for BeatStyle:
  WaveformWidget  – PyQtGraph audio waveform
  AudioPlayer     – QMediaPlayer + transport controls
  StyleCard       – clickable beat-style card
  SectionCard     – card container with a coloured tag label
"""

from __future__ import annotations
import os, numpy as np

import pyqtgraph as pg
from PySide6.QtCore  import Qt, Signal, QUrl, QSize
from PySide6.QtGui   import QColor, QPalette, QFont
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSizePolicy,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .theme import C


# ─────────────────────────────────────────
#  Waveform (PyQtGraph)
# ─────────────────────────────────────────

class WaveformWidget(pg.PlotWidget):
    """Displays a mono audio waveform using PyQtGraph."""

    def __init__(self, color: str = C["accent"], height: int = 90, parent=None):
        super().__init__(parent, background=C["card"])
        self._color  = color
        self._curve  = None
        self._MAX_PTS = 3000

        pi = self.getPlotItem()
        pi.hideAxis("left")
        pi.hideAxis("bottom")
        pi.setMenuEnabled(False)
        pi.hideButtons()
        pi.setContentsMargins(0, 0, 0, 0)
        pi.getViewBox().setMouseEnabled(x=False, y=False)
        pi.getViewBox().setBorder(None)

        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAntialiasing(True)

        # Placeholder text
        self._placeholder = pg.TextItem(
            text="Chưa có file", color=C["muted"], anchor=(0.5, 0.5)
        )
        self.addItem(self._placeholder)
        self._placeholder.setPos(0.5, 0)

    def load(self, path: str):
        """Load an audio file and render its waveform."""
        import librosa
        try:
            y, sr = librosa.load(path, sr=None, mono=True, duration=120)
        except Exception:
            return

        step = max(1, len(y) // self._MAX_PTS)
        y_d  = y[::step].astype(np.float32)
        t_d  = np.linspace(0.0, len(y) / sr, len(y_d), dtype=np.float32)

        self.clear()
        self._curve = self.plot(
            t_d, y_d,
            pen=pg.mkPen(QColor(self._color), width=1),
            fillLevel=0,
            brush=pg.mkBrush(QColor(self._color).darker(500)),
        )
        self.setXRange(0, t_d[-1], padding=0.01)
        self.setYRange(-1.0, 1.0, padding=0.05)

    def clear_waveform(self):
        self.clear()
        self._curve = None
        self._placeholder = pg.TextItem(
            text="Chưa có file", color=C["muted"], anchor=(0.5, 0.5)
        )
        self.addItem(self._placeholder)
        self._placeholder.setPos(0.5, 0)

    # Draw playhead
    def set_position(self, sec: float):
        if self._curve is None:
            return
        # Remove old line
        for item in list(self.plotItem.items):
            if getattr(item, "_is_playhead", False):
                self.plotItem.removeItem(item)
        line = pg.InfiniteLine(pos=sec, angle=90,
                               pen=pg.mkPen(C["accent2"], width=1, style=Qt.DashLine))
        line._is_playhead = True
        self.addItem(line)


# ─────────────────────────────────────────
#  Audio Player
# ─────────────────────────────────────────

class AudioPlayer(QWidget):
    """
    Compact audio player: waveform + transport bar.
    Uses PySide6.QtMultimedia.QMediaPlayer.
    """

    def __init__(self, label: str = "", wave_color: str = C["accent"],
                 parent=None):
        super().__init__(parent)
        self._path = None
        self._media = QMediaPlayer(self)
        self._audio  = QAudioOutput(self)
        self._media.setAudioOutput(self._audio)
        self._audio.setVolume(1.0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Label
        if label:
            lbl = QLabel(label)
            lbl.setObjectName("muted")
            lbl.setStyleSheet(f"font-size:11px; font-weight:700; "
                              f"text-transform:uppercase; letter-spacing:1px; "
                              f"color:{C['muted']};")
            layout.addWidget(lbl)

        # Waveform
        self.waveform = WaveformWidget(color=wave_color, height=80)
        layout.addWidget(self.waveform)

        # Transport row
        transport = QHBoxLayout()
        transport.setSpacing(8)

        self._btn_play = QPushButton("▶")
        self._btn_play.setFixedSize(32, 32)
        self._btn_play.setStyleSheet(
            f"QPushButton{{background:{C['accent']};border:none;border-radius:16px;"
            f"color:#fff;font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{C['accent2']};}}"
        )
        self._btn_play.clicked.connect(self._toggle_play)

        self._seek = QSlider(Qt.Horizontal)
        self._seek.setRange(0, 1000)
        self._seek.setValue(0)
        self._seek.sliderMoved.connect(self._on_seek)

        self._time_lbl = QLabel("0:00")
        self._time_lbl.setStyleSheet(f"color:{C['muted']};font-size:11px;")
        self._time_lbl.setFixedWidth(36)

        transport.addWidget(self._btn_play)
        transport.addWidget(self._seek)
        transport.addWidget(self._time_lbl)
        layout.addLayout(transport)

        # Connect signals
        self._media.positionChanged.connect(self._on_position)
        self._media.durationChanged.connect(self._on_duration)
        self._media.playbackStateChanged.connect(self._on_state)

        self._duration_ms = 0

    # ── Public ──────────────────────────
    def load(self, path: str):
        self._path = path
        self._media.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
        self.waveform.load(path)
        self._btn_play.setText("▶")

    def clear(self):
        self._media.stop()
        self._media.setSource(QUrl())
        self.waveform.clear_waveform()
        self._seek.setValue(0)
        self._time_lbl.setText("0:00")
        self._btn_play.setText("▶")
        self._path = None

    # ── Slots ────────────────────────────
    def _toggle_play(self):
        if self._media.playbackState() == QMediaPlayer.PlayingState:
            self._media.pause()
        else:
            self._media.play()

    def _on_seek(self, val: int):
        if self._duration_ms > 0:
            self._media.setPosition(int(val / 1000 * self._duration_ms))

    def _on_position(self, pos_ms: int):
        if self._duration_ms > 0:
            self._seek.setValue(int(pos_ms / self._duration_ms * 1000))
        sec = pos_ms // 1000
        self._time_lbl.setText(f"{sec//60}:{sec%60:02d}")
        self.waveform.set_position(pos_ms / 1000.0)

    def _on_duration(self, dur_ms: int):
        self._duration_ms = dur_ms

    def _on_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self._btn_play.setText("⏸")
        else:
            self._btn_play.setText("▶")


# ─────────────────────────────────────────
#  Style Card
# ─────────────────────────────────────────

class StyleCard(QPushButton):
    """Checkable card button representing one beat style."""

    def __init__(self, sid: str, emoji: str, name: str,
                 bpm: int, time_sig: str, desc: str, parent=None):
        super().__init__(parent)
        self.sid = sid
        self.setObjectName("style_btn")
        self.setCheckable(True)
        self.setFixedSize(QSize(140, 108))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignCenter)

        em = QLabel(emoji)
        em.setAlignment(Qt.AlignCenter)
        em.setStyleSheet("font-size:26px; background:transparent;")
        layout.addWidget(em)

        nm = QLabel(name)
        nm.setAlignment(Qt.AlignCenter)
        nm.setStyleSheet(f"font-weight:700; font-size:12px; background:transparent; color:{C['text']};")
        layout.addWidget(nm)

        bpm_lbl = QLabel(f"♩{bpm} · {time_sig}")
        bpm_lbl.setAlignment(Qt.AlignCenter)
        bpm_lbl.setStyleSheet(f"font-size:10px; color:{C['gold']}; background:transparent;")
        layout.addWidget(bpm_lbl)

        dc = QLabel(desc)
        dc.setAlignment(Qt.AlignCenter)
        dc.setWordWrap(True)
        dc.setStyleSheet(f"font-size:9px; color:{C['muted']}; background:transparent; line-height:1.3;")
        layout.addWidget(dc)

    def set_selected(self, on: bool):
        self.setChecked(on)
        self.setProperty("selected", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ─────────────────────────────────────────
#  Section card container
# ─────────────────────────────────────────

class SectionCard(QFrame):
    """A card with a coloured pill tag in the top-left corner."""

    def __init__(self, tag: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)   # top room for tag
        outer.setSpacing(0)

        # Tag pill
        self._tag_lbl = QLabel(tag)
        self._tag_lbl.setObjectName("section_tag")
        self._tag_lbl.setFixedHeight(22)
        self._tag_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._tag_lbl.setStyleSheet(
            f"background:{C['accent']}; color:#fff; font-size:9px; "
            f"font-weight:800; letter-spacing:2px; "
            f"padding:2px 10px; border-radius:10px;"
        )

        # Place tag with absolute positioning via a container
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(18, 0, 0, 0)
        tag_row.addWidget(self._tag_lbl)
        tag_row.addStretch()
        outer.addLayout(tag_row)

        # Inner content widget
        self._inner = QWidget()
        self._inner.setObjectName("card_inner")
        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(22, 14, 22, 20)
        self._layout.setSpacing(12)
        outer.addWidget(self._inner)

    def inner_layout(self) -> QVBoxLayout:
        return self._layout

    def set_tag_color(self, color: str):
        self._tag_lbl.setStyleSheet(
            f"background:{color}; color:#fff; font-size:9px; "
            f"font-weight:800; letter-spacing:2px; "
            f"padding:2px 10px; border-radius:10px;"
        )
