from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.models.chord import ChordEvent


class ChordEditorPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Start Bar", "End Bar", "Chord", "Conf."])
        layout.addWidget(self.table)

    def set_chords(self, chords: list[ChordEvent]) -> None:
        self.table.setRowCount(len(chords))
        for row, chord in enumerate(chords):
            self.table.setItem(row, 0, QTableWidgetItem(str(chord.start_bar)))
            self.table.setItem(row, 1, QTableWidgetItem(str(chord.end_bar)))
            self.table.setItem(row, 2, QTableWidgetItem(chord.chord_name))
            self.table.setItem(row, 3, QTableWidgetItem(f"{chord.confidence:.2f}"))
