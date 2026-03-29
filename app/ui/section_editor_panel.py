from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.models.section import Section


class SectionEditorPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Role", "Start(s)", "End(s)"])
        layout.addWidget(self.table)

    def set_sections(self, sections: list[Section]) -> None:
        self.table.setRowCount(len(sections))
        for row, section in enumerate(sections):
            self.table.setItem(row, 0, QTableWidgetItem(section.name))
            self.table.setItem(row, 1, QTableWidgetItem(section.role))
            self.table.setItem(row, 2, QTableWidgetItem(f"{section.start_time_sec:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{section.end_time_sec:.2f}"))
