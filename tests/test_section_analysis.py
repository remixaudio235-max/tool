import numpy as np

from app.analysis.section_analyzer import SectionAnalyzer


def test_section_analysis_smoke() -> None:
    sr = 22050
    x = np.random.randn(sr * 4).astype(np.float32) * 0.01
    result = SectionAnalyzer().analyze(x, sr)
    assert "sections" in result
