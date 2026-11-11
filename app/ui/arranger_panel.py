from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget

from app.models.arrangement_block import ArrangementBlock


class ArrangerPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def set_blocks(self, blocks: list[ArrangementBlock]) -> None:
        self.list_widget.clear()
        for block in blocks:
            self.list_widget.addItem(f"{block.block_type}: bars {block.start_bar}-{block.end_bar} ({block.intensity})")
