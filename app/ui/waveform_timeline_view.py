from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout


class WaveformTimelineView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.plot = pg.PlotWidget(background="#1d1f21")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("bottom", "Time (normalized)")
        self.plot.setLabel("left", "Amplitude")
        layout.addWidget(self.plot)
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#4aa3ff", width=1))

    def set_waveform(self, waveform: np.ndarray) -> None:
        if waveform.size == 0:
            self.curve.setData([], [])
            return
        x = np.linspace(0.0, 1.0, num=waveform.shape[0])
        self.curve.setData(x, waveform)
