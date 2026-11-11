from __future__ import annotations

import librosa
import numpy as np


class TempoAnalyzer:
    """Local tempo detector with confidence estimate and half/double helpers."""

    def analyze(self, audio: np.ndarray, sr: int) -> dict:
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, units="frames")
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        confidence = float(np.clip(np.std(onset_env) / (np.mean(onset_env) + 1e-6), 0.0, 1.0))
        tempo_value = float(tempo.item() if hasattr(tempo, "item") else tempo)
        return {
            "bpm": tempo_value,
            "confidence": confidence,
            "bpm_half": tempo_value / 2,
            "bpm_double": tempo_value * 2,
            "beat_frames": beat_frames.tolist(),
        }
