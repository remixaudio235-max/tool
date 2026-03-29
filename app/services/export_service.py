from __future__ import annotations

from pathlib import Path

import soundfile as sf


class ExportService:
    def export_wave(self, path: Path, audio, sample_rate: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), audio, sample_rate)
