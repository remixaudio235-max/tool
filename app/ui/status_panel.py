from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatusPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.label = QLabel("Ready")
        layout.addWidget(self.label)

    def set_status(self, message: str) -> None:
        self.label.setText(message)
