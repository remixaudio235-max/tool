#!/usr/bin/env python3
"""BeatStyle – Desktop entry point (PySide6 + PyQtGraph)."""

import sys
import os

# Make sure the project root is in path so `backend` and `gui` are importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tell pyqtgraph to use PySide6 before any other import
os.environ.setdefault("PYQTGRAPH_QT_LIB", "PySide6")

import pyqtgraph as pg
pg.setConfigOptions(antialias=True, background=None)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore    import Qt
from PySide6.QtGui     import QFont

from gui.main_window import MainWindow


def main():
    # High-DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BeatStyle")
    app.setApplicationDisplayName("BeatStyle – Beat Converter")
    app.setStyle("Fusion")

    # Base font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
