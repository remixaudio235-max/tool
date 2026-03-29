from __future__ import annotations

import librosa
import numpy as np

from app.utils.music_utils import KEYS


class KeyAnalyzer:
    def analyze(self, audio: np.ndarray, sr: int) -> dict:
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        profile = np.mean(chroma, axis=1)
        idx = int(np.argmax(profile))
        confidence = float(profile[idx] / (np.sum(profile) + 1e-6))
        return {"key": KEYS[idx], "confidence": confidence}
