from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class TransportPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
