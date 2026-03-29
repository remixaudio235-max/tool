from __future__ import annotations

from app.models.stem import StemSet


class StemSeparator:
    def separate(self, source_path: str, output_dir: str) -> StemSet:
        stems = StemSet(status="unavailable", backend="demucs")
        stems.errors.append("Demucs wrapper not yet wired in this milestone.")
        return stems
