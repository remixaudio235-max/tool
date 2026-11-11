from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProjectSidebar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.name_label = QLabel("Project: -")
        self.info_label = QLabel("Duration: - | Sample rate: -")
        self.analysis_label = QLabel("BPM: - | Key: -")
        layout.addWidget(self.name_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.analysis_label)
        layout.addStretch()

    def update_labels(self, name: str, duration: float, sr: int, bpm: float | None, key: str | None) -> None:
        self.name_label.setText(f"Project: {name}")
        self.info_label.setText(f"Duration: {duration:.1f}s | Sample rate: {sr}")
        self.analysis_label.setText(f"BPM: {bpm or '-'} | Key: {key or '-'}")
