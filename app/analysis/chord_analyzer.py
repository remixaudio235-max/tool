from __future__ import annotations

from app.models.chord import ChordEvent


class ChordAnalyzer:
    """Placeholder deterministic chord pass mapped to bar count."""

    def analyze(self, bar_positions_sec: list[float], key_hint: str | None = None) -> dict:
        if not bar_positions_sec:
            return {"chords": [], "confidence": 0.0}
        chords = []
        pattern = [f"{key_hint or 'C'}", "Am", "F", "G"]
        for i in range(len(bar_positions_sec)):
            chords.append(
                ChordEvent(start_bar=i + 1, end_bar=i + 1, chord_name=pattern[i % len(pattern)], confidence=0.55)
            )
        return {"chords": chords, "confidence": 0.55}
