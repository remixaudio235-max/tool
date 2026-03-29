from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MixerPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Mixer (placeholder): source/stems/arrangement mute-solo routing"))
