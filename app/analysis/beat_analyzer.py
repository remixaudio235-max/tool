from __future__ import annotations

import librosa
import numpy as np


class BeatAnalyzer:
    def analyze(self, audio: np.ndarray, sr: int) -> dict:
        _, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, units="frames")
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return {"beat_positions_sec": [float(x) for x in beat_times]}
