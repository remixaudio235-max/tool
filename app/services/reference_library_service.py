from __future__ import annotations

from pathlib import Path

from app.models.reference_sample import ReferenceSample
from app.utils.audio_io import load_audio_for_waveform


class ReferenceLibraryService:
    def create_sample(self, file_path: str, tags: list[str] | None = None) -> ReferenceSample:
        waveform, sr, duration = load_audio_for_waveform(file_path)
        _ = waveform, sr
        p = Path(file_path)
        return ReferenceSample(file_path=file_path, display_name=p.name, tags=tags or [], duration_sec=duration)

    def filter_by_tag(self, samples: list[ReferenceSample], tag: str) -> list[ReferenceSample]:
        return [sample for sample in samples if tag in sample.tags]
