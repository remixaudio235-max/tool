from __future__ import annotations


class BarGridAnalyzer:
    def build_bar_grid(self, beat_positions_sec: list[float], beats_per_bar: int = 4) -> dict:
        bars = [beat_positions_sec[i] for i in range(0, len(beat_positions_sec), beats_per_bar)]
        confidence = 0.7 if bars else 0.0
        return {
            "downbeat_offset_sec": bars[0] if bars else 0.0,
            "bar_positions_sec": bars,
            "bar_grid_confidence": confidence,
        }
