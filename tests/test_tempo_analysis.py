import numpy as np

from app.analysis.tempo_analyzer import TempoAnalyzer


def test_tempo_analysis_smoke() -> None:
    sr = 22050
    t = np.linspace(0, 2, num=sr * 2, endpoint=False)
    x = 0.2 * np.sin(2 * np.pi * 220 * t)
    result = TempoAnalyzer().analyze(x.astype(np.float32), sr)
    assert "bpm" in result
