"""
Beat Converter – audio style transformation engine.

Each style applies a chain of signal-processing steps using
librosa (analysis), numpy/scipy (DSP) and soundfile (I/O).
No external ML models are required.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf
import librosa
from scipy import signal as scipy_signal
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: str) -> tuple[np.ndarray, int]:
    """Load audio as mono float32, return (samples, sr)."""
    y, sr = librosa.load(path, sr=None, mono=True)
    return y.astype(np.float32), int(sr)


def _save(y: np.ndarray, sr: int, path: str):
    sf.write(path, np.clip(y, -1.0, 1.0), sr, subtype="PCM_16")


def _normalize(y: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    peak = np.max(np.abs(y))
    if peak < 1e-9:
        return y
    gain = (10 ** (target_db / 20.0)) / peak
    return y * gain


def _biquad(y: np.ndarray, sr: int, ftype: str, freq: float, Q: float = 0.707,
            gain_db: float = 0.0) -> np.ndarray:
    """Apply a biquad filter (lowpass, highpass, peak, shelf)."""
    nyq = sr / 2.0
    freq = min(freq, nyq * 0.99)

    if ftype == "lowpass":
        b, a = scipy_signal.butter(2, freq / nyq, btype="low")
    elif ftype == "highpass":
        b, a = scipy_signal.butter(2, freq / nyq, btype="high")
    elif ftype == "peak":
        # Parametric EQ peak using iirpeak
        w0 = freq / nyq
        b, a = scipy_signal.iirpeak(w0, Q)
        lin_gain = 10 ** (gain_db / 20.0)
        b = b * lin_gain
    elif ftype == "bandpass":
        bw_low = max(freq * 0.5, 20) / nyq
        bw_high = min(freq * 2.0, nyq * 0.99) / nyq
        b, a = scipy_signal.butter(2, [bw_low, bw_high], btype="band")
    else:
        return y

    return scipy_signal.lfilter(b, a, y).astype(np.float32)


def _reverb(y: np.ndarray, sr: int, room_size: float = 0.5, wet: float = 0.3) -> np.ndarray:
    """Simple FDN-style reverb via exponential decay convolution."""
    decay_time = room_size * 3.0  # seconds
    ir_len = int(decay_time * sr)
    t = np.linspace(0, decay_time, ir_len)
    ir = np.random.randn(ir_len).astype(np.float32)
    ir *= np.exp(-6.0 * t / decay_time).astype(np.float32)
    ir /= np.max(np.abs(ir) + 1e-9)
    wet_signal = np.convolve(y, ir, mode="full")[: len(y)]
    return (1 - wet) * y + wet * wet_signal.astype(np.float32)


def _chorus(y: np.ndarray, sr: int, depth_ms: float = 8.0, rate_hz: float = 0.8,
            wet: float = 0.3) -> np.ndarray:
    depth = int(depth_ms / 1000.0 * sr)
    max_delay = depth * 2
    lfo = (np.sin(2 * np.pi * rate_hz * np.arange(len(y)) / sr) * 0.5 + 0.5) * depth
    out = np.zeros_like(y)
    for i in range(len(y)):
        delay = int(lfo[i]) + max_delay // 2
        src = i - delay
        out[i] = y[src] if 0 <= src < len(y) else 0.0
    return (1 - wet) * y + wet * out


def _vinyl_noise(length: int, sr: int, amount: float = 0.015) -> np.ndarray:
    """Generate vinyl crackle and hiss."""
    hiss = np.random.randn(length).astype(np.float32) * amount * 0.4
    # Sparse crackles
    crackles = np.zeros(length, dtype=np.float32)
    n_crackles = int(sr * 0.3)  # ~0.3 per second
    positions = np.random.randint(0, length, n_crackles)
    for p in positions:
        click_len = np.random.randint(50, 300)
        end = min(p + click_len, length)
        crackles[p:end] += np.random.randn(end - p).astype(np.float32) * amount * 0.8
    return hiss + crackles


def _tape_saturation(y: np.ndarray, drive: float = 0.5) -> np.ndarray:
    """Soft-clip saturation emulating tape."""
    return np.tanh(y * (1.0 + drive * 3.0)) / (1.0 + drive * 0.5)


def _distortion(y: np.ndarray, gain: float = 4.0, mix: float = 0.5) -> np.ndarray:
    driven = np.clip(y * gain, -1.0, 1.0)
    driven = np.sign(driven) * (1 - np.exp(-np.abs(driven * 3.0)))
    return (1 - mix) * y + mix * driven


def _bit_crush(y: np.ndarray, bits: int = 12) -> np.ndarray:
    steps = 2 ** bits
    return np.round(y * steps) / steps


def _pitch_shift_simple(y: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    if abs(semitones) < 0.01:
        return y
    try:
        return librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
    except Exception:
        return y


def _time_stretch_simple(y: np.ndarray, rate: float) -> np.ndarray:
    if abs(rate - 1.0) < 0.01:
        return y
    try:
        return librosa.effects.time_stretch(y, rate=rate)
    except Exception:
        return y


def _sidechain_compress(y: np.ndarray, sr: int, threshold: float = 0.4,
                        attack_ms: float = 5.0, release_ms: float = 80.0) -> np.ndarray:
    """Simulated sidechaining: duck audio on every beat."""
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_samples = librosa.frames_to_samples(beats)

    env = np.ones(len(y), dtype=np.float32)
    attack = int(attack_ms / 1000.0 * sr)
    release = int(release_ms / 1000.0 * sr)

    for b in beat_samples:
        # Duck down
        end_a = min(b + attack, len(y))
        env[b:end_a] = np.linspace(1.0, threshold, end_a - b)
        # Release back up
        end_r = min(end_a + release, len(y))
        env[end_a:end_r] = np.linspace(threshold, 1.0, end_r - end_a)

    return (y * env).astype(np.float32)


def _swing_quantize(y: np.ndarray, sr: int, swing: float = 0.6) -> np.ndarray:
    """Add swing feel by slightly stretching/squeezing alternating beats."""
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    if len(beats) < 4:
        return y
    beat_samples = librosa.frames_to_samples(beats)

    out_chunks = []
    for i in range(0, len(beat_samples) - 1, 2):
        s1 = beat_samples[i]
        s2 = beat_samples[i + 1]
        s3 = beat_samples[i + 2] if i + 2 < len(beat_samples) else len(y)
        half = (s3 - s1) / 2

        # On-beat: longer
        on_len = int(half * (1 + swing - 0.5))
        # Off-beat: shorter
        off_len = int(half * (1 - (swing - 0.5)))

        chunk_on = y[s1:s2]
        chunk_off = y[s2:s3]
        if len(chunk_on) > 0 and on_len > 0:
            chunk_on = _time_stretch_simple(chunk_on, len(chunk_on) / max(on_len, 1))
        if len(chunk_off) > 0 and off_len > 0:
            chunk_off = _time_stretch_simple(chunk_off, len(chunk_off) / max(off_len, 1))
        out_chunks.extend([chunk_on, chunk_off])

    if out_chunks:
        return np.concatenate(out_chunks).astype(np.float32)
    return y


# ---------------------------------------------------------------------------
# Style processors
# ---------------------------------------------------------------------------

class StyleProcessor:
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        raise NotImplementedError


class LofiProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slow down slightly (95%)
        y = _time_stretch_simple(y, 1.0 / 0.95)
        # 2. Low-pass filter (warm, dull)
        cutoff = int(8000 - intensity * 4000)
        y = _biquad(y, sr, "lowpass", cutoff)
        # 3. Tape saturation
        y = _tape_saturation(y, drive=intensity * 0.6)
        # 4. Bit crush for vintage feel
        bits = int(16 - intensity * 4)
        y = _bit_crush(y, bits=max(bits, 10))
        # 5. Vinyl noise
        noise = _vinyl_noise(len(y), sr, amount=0.012 * intensity)
        y = y + noise
        # 6. Gentle reverb
        y = _reverb(y, sr, room_size=0.3, wet=0.15 * intensity)
        return y


class EDMProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Sidechain compression (pumping)
        y = _sidechain_compress(y, sr, threshold=0.3 + (1 - intensity) * 0.4)
        # 2. Sub-bass boost
        y_bass = _biquad(y, sr, "lowpass", 80)
        y = y + y_bass * intensity * 0.5
        # 3. High-frequency air boost
        y_air = _biquad(y, sr, "highpass", 10000)
        y = y + y_air * intensity * 0.3
        # 4. Chorus/width
        y = _chorus(y, sr, depth_ms=6.0, rate_hz=0.5, wet=intensity * 0.25)
        # 5. Hard clip for loudness
        y = np.clip(y * (1.0 + intensity * 0.4), -1.0, 1.0)
        return y


class TrapProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slow down (trap is ~70–90 BPM feel)
        y = _time_stretch_simple(y, 1.0 / 0.92)
        # 2. Heavy sub-bass (808-style)
        y_sub = _biquad(y, sr, "lowpass", 60)
        y = y + y_sub * intensity * 1.2
        # 3. Cut mids, boost highs (hi-hat space)
        y = _biquad(y, sr, "highpass", 60)
        y_hi = _biquad(y, sr, "highpass", 6000)
        y = y + y_hi * intensity * 0.4
        # 4. Distort 808
        y = _distortion(y, gain=1.5 + intensity, mix=intensity * 0.35)
        # 5. Reverb tail
        y = _reverb(y, sr, room_size=0.6, wet=0.2 * intensity)
        return y


class JazzProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Swing quantization
        y = _swing_quantize(y, sr, swing=0.55 + intensity * 0.15)
        # 2. Warm low-pass (tube amp feel)
        y = _biquad(y, sr, "lowpass", 12000 - intensity * 2000)
        # 3. Tape saturation (warm)
        y = _tape_saturation(y, drive=intensity * 0.3)
        # 4. Room reverb
        y = _reverb(y, sr, room_size=0.4, wet=0.2 * intensity)
        # 5. Mid boost (presence)
        y_mid = _biquad(y, sr, "bandpass", 1500)
        y = y + y_mid * intensity * 0.1
        return y


class RockProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Guitar amp distortion
        y = _distortion(y, gain=2.0 + intensity * 3.0, mix=intensity * 0.6)
        # 2. High-pass (tighten low end)
        y = _biquad(y, sr, "highpass", 120)
        # 3. Upper-mid boost (aggression)
        y_mid = _biquad(y, sr, "bandpass", 3000)
        y = y + y_mid * intensity * 0.3
        # 4. Cabinet sim: low-pass roll off highs
        y = _biquad(y, sr, "lowpass", 7000 + (1 - intensity) * 4000)
        # 5. Plate reverb
        y = _reverb(y, sr, room_size=0.35, wet=0.15 * intensity)
        return y


class ReggaetonProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Bump BPM slightly (dembow feel ~95–100)
        y = _time_stretch_simple(y, 0.97)
        # 2. Bass boost
        y_bass = _biquad(y, sr, "lowpass", 120)
        y = y + y_bass * intensity * 0.8
        # 3. Sidechain on off-beats
        y = _sidechain_compress(y, sr, threshold=0.5, attack_ms=3.0, release_ms=60.0)
        # 4. Bright, crispy highs
        y_hi = _biquad(y, sr, "highpass", 8000)
        y = y + y_hi * intensity * 0.2
        # 5. Chorus (space)
        y = _chorus(y, sr, depth_ms=4.0, rate_hz=0.4, wet=intensity * 0.15)
        return y


class BossanovaProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slight swing
        y = _swing_quantize(y, sr, swing=0.52 + intensity * 0.06)
        # 2. Warm EQ: boost low-mids
        y_lm = _biquad(y, sr, "bandpass", 400)
        y = y + y_lm * intensity * 0.15
        # 3. High-pass (remove rumble)
        y = _biquad(y, sr, "highpass", 80)
        # 4. Gentle chorus (nylon string feel)
        y = _chorus(y, sr, depth_ms=5.0, rate_hz=0.6, wet=intensity * 0.2)
        # 5. Hall reverb
        y = _reverb(y, sr, room_size=0.5, wet=0.25 * intensity)
        return y


class RnBProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slight slowdown (smooth)
        y = _time_stretch_simple(y, 1.0 / 0.97)
        # 2. Low-end warmth
        y_bass = _biquad(y, sr, "lowpass", 200)
        y = y + y_bass * intensity * 0.4
        # 3. Smooth highs
        y = _biquad(y, sr, "lowpass", 14000)
        # 4. Tape saturation
        y = _tape_saturation(y, drive=intensity * 0.4)
        # 5. Deep reverb
        y = _reverb(y, sr, room_size=0.55, wet=0.3 * intensity)
        # 6. Lush chorus
        y = _chorus(y, sr, depth_ms=10.0, rate_hz=0.4, wet=intensity * 0.2)
        return y


class PhonkProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slow + pitch down (dark Memphis feel)
        y = _time_stretch_simple(y, 1.0 / 0.88)
        y = _pitch_shift_simple(y, sr, semitones=-2.0 * intensity)
        # 2. Heavy distorted 808 sub
        y_sub = _biquad(y, sr, "lowpass", 80)
        y_sub = _distortion(y_sub, gain=3.0, mix=0.8)
        y = y + y_sub * intensity
        # 3. Vinyl texture
        noise = _vinyl_noise(len(y), sr, amount=0.02 * intensity)
        y = y + noise
        # 4. Bit crush for grit
        y = _bit_crush(y, bits=int(14 - intensity * 3))
        # 5. Dark low-pass
        y = _biquad(y, sr, "lowpass", 10000 - intensity * 3000)
        return y


class AmbientProcessor(StyleProcessor):
    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # 1. Slow down dramatically
        y = _time_stretch_simple(y, 1.0 / 0.7)
        # 2. Pitch shift up slightly (ethereal)
        y = _pitch_shift_simple(y, sr, semitones=intensity * 3)
        # 3. Remove harshness
        y = _biquad(y, sr, "lowpass", 6000 - intensity * 1000)
        y = _biquad(y, sr, "highpass", 200)
        # 4. Massive reverb
        y = _reverb(y, sr, room_size=0.9, wet=0.6 * intensity)
        # 5. Lush chorus
        y = _chorus(y, sr, depth_ms=15.0, rate_hz=0.25, wet=intensity * 0.5)
        # 6. Fade edges
        fade = int(sr * 2.0)
        if len(y) > fade * 2:
            y[:fade] *= np.linspace(0, 1, fade)
            y[-fade:] *= np.linspace(1, 0, fade)
        return y


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

PROCESSORS: Dict[str, StyleProcessor] = {
    "lofi":      LofiProcessor(),
    "edm":       EDMProcessor(),
    "trap":      TrapProcessor(),
    "jazz":      JazzProcessor(),
    "rock":      RockProcessor(),
    "reggaeton": ReggaetonProcessor(),
    "bossanova": BossanovaProcessor(),
    "rnb":       RnBProcessor(),
    "phonk":     PhonkProcessor(),
    "ambient":   AmbientProcessor(),
}


class BeatConverter:
    def convert(
        self,
        input_path: str,
        output_path: str,
        style: str,
        intensity: float = 0.7,
    ) -> Dict[str, Any]:
        y, sr = _load(input_path)

        # Analyse before conversion
        duration = len(y) / sr
        try:
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(np.atleast_1d(tempo)[0])
        except Exception:
            bpm = 0.0
            beats = np.array([])

        spectral_centroid = float(
            np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        )
        rms = float(np.sqrt(np.mean(y ** 2)))

        # Apply style
        processor = PROCESSORS[style]
        y_out = processor.process(y.copy(), sr, intensity)

        # Final normalize
        y_out = _normalize(y_out, target_db=-3.0)

        _save(y_out, sr, output_path)

        return {
            "original_bpm": round(bpm, 1),
            "duration_sec": round(duration, 2),
            "spectral_centroid_hz": round(spectral_centroid, 1),
            "original_rms": round(rms, 4),
            "output_sr": sr,
            "beat_count": int(len(beats)),
        }
