from __future__ import annotations

import librosa
import numpy as np

from app.models.section import Section


class SectionAnalyzer:
    """Novelty + RMS heuristics for rough section boundaries."""

    def analyze(self, audio: np.ndarray, sr: int) -> dict:
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        novelty = librosa.onset.onset_strength(sr=sr, S=chroma)
        rms = librosa.feature.rms(y=audio)[0]

        peaks = librosa.util.peak_pick(novelty, 6, 6, 6, 6, 0.15, 8)
        peak_times = librosa.frames_to_time(peaks, sr=sr)
        duration = len(audio) / sr
        boundaries = [0.0] + [float(x) for x in peak_times if 4.0 < x < duration - 4.0] + [duration]
        boundaries = sorted(set(round(x, 2) for x in boundaries))

        roles = ["intro", "verse", "chorus", "bridge", "break", "outro"]
        sections: list[Section] = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            energy = float(np.mean(rms[int(i * len(rms) / max(len(boundaries), 1)) :])) if len(rms) else 0.0
            role = roles[min(i, len(roles) - 1)]
            sections.append(
                Section(
                    name=f"{role.title()} {i+1}",
                    role=role,
                    start_time_sec=start,
                    end_time_sec=end,
                    confidence=min(0.9, 0.5 + energy),
                )
            )
        return {"sections": sections, "confidence": 0.65 if sections else 0.0}
