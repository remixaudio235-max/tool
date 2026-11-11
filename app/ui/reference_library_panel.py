from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget

from app.models.reference_sample import ReferenceSample


class ReferenceLibraryPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def set_references(self, references: list[ReferenceSample]) -> None:
        self.list_widget.clear()
        for ref in references:
            self.list_widget.addItem(f"{ref.display_name} | tags={','.join(ref.tags)} | rating={ref.user_rating}")
