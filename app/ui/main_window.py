from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.arranger.arrangement_builder import ArrangementBuilder
from app.models.project import Project
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.reference_library_service import ReferenceLibraryService
from app.ui.arranger_panel import ArrangerPanel
from app.ui.chord_editor_panel import ChordEditorPanel
from app.ui.project_sidebar import ProjectSidebar
from app.ui.reference_library_panel import ReferenceLibraryPanel
from app.ui.section_editor_panel import SectionEditorPanel
from app.ui.status_panel import StatusPanel
from app.ui.transport_panel import TransportPanel
from app.ui.waveform_timeline_view import WaveformTimelineView
from app.utils.audio_io import is_supported_audio, load_audio_for_waveform

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VN Live Arranger Studio")
        self.resize(1400, 860)
        self.setAcceptDrops(True)

        self.project: Project | None = None
        self.audio_data = None
        self.audio_sr = 0

        self.analysis = AnalysisOrchestrator()
        self.ref_service = ReferenceLibraryService()
        self.arrangement_builder = ArrangementBuilder()

        self._build_toolbar()
        self._build_layout()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.open_btn = QPushButton("Open Beat")
        self.open_btn.clicked.connect(self.open_audio_dialog)
        toolbar.addWidget(self.open_btn)

        self.import_ref_btn = QPushButton("Import Reference")
        self.import_ref_btn.clicked.connect(self.import_reference_dialog)
        toolbar.addWidget(self.import_ref_btn)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.run_analysis)
        toolbar.addWidget(self.analyze_btn)

        self.generate_btn = QPushButton("Generate Arrangement")
        self.generate_btn.clicked.connect(self.generate_arrangement)
        toolbar.addWidget(self.generate_btn)

    def _build_layout(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = ProjectSidebar()
        splitter.addWidget(self.sidebar)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        self.wave_view = WaveformTimelineView()
        self.transport = TransportPanel()
        center_layout.addWidget(self.wave_view)
        center_layout.addWidget(self.transport)
        splitter.addWidget(center)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        top = QHBoxLayout()
        self.section_panel = SectionEditorPanel()
        self.chord_panel = ChordEditorPanel()
        top.addWidget(self.section_panel)
        top.addWidget(self.chord_panel)
        right_layout.addLayout(top)
        self.arranger_panel = ArrangerPanel()
        self.reference_panel = ReferenceLibraryPanel()
        right_layout.addWidget(self.arranger_panel)
        right_layout.addWidget(self.reference_panel)
        splitter.addWidget(right)

        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        self.status_panel = StatusPanel()
        layout.addWidget(splitter)
        layout.addWidget(self.status_panel)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and is_supported_audio(local):
                self.load_source_audio(local)
                break

    def open_audio_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open beat/song",
            "",
            "Audio (*.wav *.mp3 *.flac *.m4a *.aac)",
        )
        if path:
            self.load_source_audio(path)

    def load_source_audio(self, path: str) -> None:
        try:
            waveform, sr, duration = load_audio_for_waveform(path)
        except Exception as exc:
            logger.exception("Failed to load source audio")
            QMessageBox.critical(self, "Load error", str(exc))
            return

        self.audio_data = waveform
        self.audio_sr = sr
        self.project = Project.from_source(path, sr, duration)
        self.wave_view.set_waveform(waveform)
        self.sidebar.update_labels(self.project.name, duration, sr, None, None)
        self.status_panel.set_status(f"Loaded source audio: {Path(path).name}")

    def import_reference_dialog(self) -> None:
        if not self.project:
            QMessageBox.warning(self, "No project", "Open source audio first.")
            return
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import references",
            "",
            "Audio (*.wav *.mp3 *.flac *.m4a *.aac)",
        )
        for f in files:
            ref = self.ref_service.create_sample(f, tags=["style_color"])
            self.project.reference_samples.append(ref)
        self.reference_panel.set_references(self.project.reference_samples)
        self.status_panel.set_status(f"Imported {len(files)} reference sample(s)")

    def run_analysis(self) -> None:
        if self.project is None or self.audio_data is None:
            QMessageBox.warning(self, "No project", "Open source audio first.")
            return
        self.analysis.run_core_analysis(self.project, self.audio_data, self.audio_sr)
        self.sidebar.update_labels(
            self.project.name,
            self.project.duration_sec,
            self.project.sample_rate,
            self.project.bpm_detected,
            self.project.key_detected,
        )
        self.section_panel.set_sections(self.project.sections)
        self.chord_panel.set_chords(self.project.chord_events)
        self.status_panel.set_status("Analysis complete: BPM/beat/bar/section/key/chords")

    def generate_arrangement(self) -> None:
        if not self.project:
            QMessageBox.warning(self, "No project", "Open source audio first.")
            return
        self.arrangement_builder.build(self.project, density="medium")
        self.arranger_panel.set_blocks(self.project.arrangement_blocks)
        self.status_panel.set_status("Arrangement blocks generated")
