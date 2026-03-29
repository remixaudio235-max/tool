from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".aac"}


def load_audio_for_waveform(path: str, max_points: int = 24000) -> tuple[np.ndarray, int, float]:
    data, sample_rate = sf.read(path, always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    duration_sec = float(len(data) / sample_rate) if sample_rate else 0.0
    if len(data) > max_points:
        step = max(1, len(data) // max_points)
        data = data[::step]
    return data.astype(np.float32), int(sample_rate), duration_sec


def is_supported_audio(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
