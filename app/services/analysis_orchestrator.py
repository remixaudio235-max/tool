from __future__ import annotations

import numpy as np

from app.analysis.bar_grid_analyzer import BarGridAnalyzer
from app.analysis.beat_analyzer import BeatAnalyzer
from app.analysis.chord_analyzer import ChordAnalyzer
from app.analysis.key_analyzer import KeyAnalyzer
from app.analysis.section_analyzer import SectionAnalyzer
from app.analysis.tempo_analyzer import TempoAnalyzer
from app.models.project import Project


class AnalysisOrchestrator:
    def __init__(self) -> None:
        self.tempo = TempoAnalyzer()
        self.beats = BeatAnalyzer()
        self.bars = BarGridAnalyzer()
        self.sections = SectionAnalyzer()
        self.keys = KeyAnalyzer()
        self.chords = ChordAnalyzer()

    def run_core_analysis(self, project: Project, audio: np.ndarray, sr: int) -> Project:
        tempo = self.tempo.analyze(audio, sr)
        beats = self.beats.analyze(audio, sr)
        bars = self.bars.build_bar_grid(beats["beat_positions_sec"])
        sec = self.sections.analyze(audio, sr)
        key = self.keys.analyze(audio, sr)
        chord = self.chords.analyze(bars["bar_positions_sec"], key_hint=key["key"])

        project.bpm_detected = tempo["bpm"]
        project.tempo_confidence = tempo["confidence"]
        project.beat_positions_sec = beats["beat_positions_sec"]
        project.downbeat_offset_sec = bars["downbeat_offset_sec"]
        project.bar_positions_sec = bars["bar_positions_sec"]
        project.bar_grid_confidence = bars["bar_grid_confidence"]
        project.sections = sec["sections"]
        project.key_detected = key["key"]
        project.key_confidence = key["confidence"]
        project.chord_events = chord["chords"]
        project.mark_updated()
        return project
