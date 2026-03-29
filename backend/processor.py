"""
BeatStyle Processor – transforms a clean beat into different sonic styles.

Input  : any clean beat/instrumental (MP3, WAV, FLAC …)
Output : WAV with target style applied

Style groups
────────────
  NHẠC SỐNG  – Bolero, Rumba, Cha-cha-cha, Slow-Rock, Tango, Valse
  ROCK/METAL – Hard Rock, Heavy Metal, Nu-Metal, Punk
  MODERN     – EDM, Trap, Lo-fi, R&B, Phonk, Ambient

Each style applies a deterministic DSP chain:
  BPM normalise → EQ → Dynamics → FX (reverb / distortion / leslie …) → Normalize
"""

from __future__ import annotations

import numpy as np
import soundfile as sf
import librosa
from scipy import signal as sp
from typing import Dict, Any, Tuple


# ══════════════════════════════════════════════
#  I/O
# ══════════════════════════════════════════════

def _load(path: str) -> Tuple[np.ndarray, int]:
    """Load as mono float32."""
    y, sr = librosa.load(path, sr=None, mono=True)
    return y.astype(np.float32), int(sr)


def _save(y: np.ndarray, sr: int, path: str):
    sf.write(path, np.clip(y, -1.0, 1.0), sr, subtype="PCM_16")


def _normalize(y: np.ndarray, db: float = -2.0) -> np.ndarray:
    peak = np.max(np.abs(y))
    if peak < 1e-9:
        return y
    return y * (10 ** (db / 20.0)) / peak


# ══════════════════════════════════════════════
#  DSP primitives
# ══════════════════════════════════════════════

def _lpf(y, sr, freq, order=2):
    b, a = sp.butter(order, min(freq, sr*0.499) / (sr/2), "low")
    return sp.lfilter(b, a, y).astype(np.float32)


def _hpf(y, sr, freq, order=2):
    b, a = sp.butter(order, max(freq, 20) / (sr/2), "high")
    return sp.lfilter(b, a, y).astype(np.float32)


def _peak(y, sr, freq, gain_db, Q=1.4):
    """Parametric peak / notch EQ."""
    nyq = sr / 2.0
    w0  = min(freq / nyq, 0.99)
    A   = 10 ** (gain_db / 40.0)
    cos_w0  = np.cos(np.pi * w0)
    alpha   = np.sin(np.pi * w0) / (2 * Q)
    b = np.array([1 + alpha*A,  -2*cos_w0,  1 - alpha*A])
    a = np.array([1 + alpha/A,  -2*cos_w0,  1 - alpha/A])
    return sp.lfilter(b/a[0], a/a[0], y).astype(np.float32)


def _shelf_low(y, sr, freq, gain_db):
    """Low-shelf EQ."""
    nyq = sr / 2.0
    w0 = min(freq / nyq, 0.99) * np.pi
    A  = 10 ** (gain_db / 40.0)
    cos_w0 = np.cos(w0); sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt((A + 1/A)*(1/0.707 - 1) + 2)
    b = np.array([
        A*((A+1)-(A-1)*cos_w0 + 2*np.sqrt(A)*alpha),
        2*A*((A-1)-(A+1)*cos_w0),
        A*((A+1)-(A-1)*cos_w0 - 2*np.sqrt(A)*alpha),
    ])
    a = np.array([
        (A+1)+(A-1)*cos_w0 + 2*np.sqrt(A)*alpha,
        -2*((A-1)+(A+1)*cos_w0),
        (A+1)+(A-1)*cos_w0 - 2*np.sqrt(A)*alpha,
    ])
    return sp.lfilter(b/a[0], a/a[0], y).astype(np.float32)


def _compress(y, threshold=0.5, ratio=4.0, attack_ms=5, release_ms=80, sr=44100):
    """Simple feed-forward RMS compressor."""
    atk = np.exp(-1.0 / (attack_ms   * 0.001 * sr))
    rel = np.exp(-1.0 / (release_ms  * 0.001 * sr))
    env = 0.0
    gain = np.ones(len(y), dtype=np.float32)
    for i, s in enumerate(np.abs(y)):
        env = atk * env + (1 - atk) * s if s > env else rel * env + (1 - rel) * s
        if env > threshold:
            gain[i] = threshold + (env - threshold) / ratio / (env + 1e-9)
        else:
            gain[i] = 1.0
    return (y * gain).astype(np.float32)


def _reverb(y, sr, room=0.4, wet=0.25, pre_delay_ms=0.0):
    rng = np.random.default_rng(42)
    pre = int(pre_delay_ms * 0.001 * sr)
    ir_len = int(room * 3.5 * sr)
    t   = np.linspace(0, room * 3.5, ir_len)
    ir  = rng.standard_normal(ir_len).astype(np.float32)
    ir *= np.exp(-6.0 * t / (room * 3.5)).astype(np.float32)
    ir  = ir / (np.max(np.abs(ir)) + 1e-9)
    w   = np.convolve(y, ir, mode="full")[: len(y)]
    if pre > 0:
        w = np.concatenate([np.zeros(pre, dtype=np.float32), w[:-pre]])
    return ((1 - wet) * y + wet * w).astype(np.float32)


def _distortion(y, drive=4.0, mix=0.6, clip="tanh"):
    if clip == "tanh":
        dist = np.tanh(y * drive)
    elif clip == "hard":
        dist = np.clip(y * drive, -1.0, 1.0)
    elif clip == "asymm":          # asymmetric — more "tube" flavour
        pos = np.tanh(y * drive * 1.1)
        neg = np.tanh(y * drive * 0.9)
        dist = np.where(y >= 0, pos, neg)
    else:
        dist = np.tanh(y * drive)
    dist = dist.astype(np.float32)
    return ((1 - mix) * y + mix * dist).astype(np.float32)


def _sidechain(y, sr, threshold=0.4, attack_ms=4, release_ms=70):
    """Duck audio on every detected beat (pump effect)."""
    _, beats = librosa.beat.beat_track(y=y, sr=sr)
    bsamp = librosa.frames_to_samples(beats)
    env = np.ones(len(y), dtype=np.float32)
    atk = int(attack_ms  * 0.001 * sr)
    rel = int(release_ms * 0.001 * sr)
    for b in bsamp:
        e1 = min(b + atk, len(y))
        e2 = min(e1 + rel, len(y))
        env[b:e1] = np.linspace(1.0, threshold, e1 - b)
        env[e1:e2] = np.linspace(threshold, 1.0, e2 - e1)
    return (y * env).astype(np.float32)


def _chorus(y, sr, depth_ms=7.0, rate_hz=0.7, wet=0.3):
    depth = int(depth_ms * 0.001 * sr)
    t   = np.arange(len(y)) / sr
    lfo = (depth * 0.5 * (1 + np.sin(2 * np.pi * rate_hz * t))).astype(int)
    out = np.zeros_like(y)
    for i in range(len(y)):
        src = i - lfo[i] - depth // 2
        out[i] = y[src] if 0 <= src < len(y) else 0.0
    return ((1 - wet) * y + wet * out).astype(np.float32)


def _stretch(y, rate):
    """Time-stretch by `rate` (>1 = faster, <1 = slower)."""
    if abs(rate - 1.0) < 0.015:
        return y
    try:
        return librosa.effects.time_stretch(y, rate=rate).astype(np.float32)
    except Exception:
        return y


def _pitch(y, sr, semitones):
    if abs(semitones) < 0.05:
        return y
    try:
        return librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones).astype(np.float32)
    except Exception:
        return y


def _vinyl(y, sr, amount=0.012):
    rng = np.random.default_rng(7)
    hiss = rng.standard_normal(len(y)).astype(np.float32) * amount * 0.4
    crk  = np.zeros(len(y), dtype=np.float32)
    for p in rng.integers(0, len(y), int(sr * 0.25)):
        end = min(int(p) + rng.integers(60, 320), len(y))
        crk[p:end] += rng.standard_normal(end - p).astype(np.float32) * amount * 0.9
    return y + hiss + crk


# ══════════════════════════════════════════════
#  BPM normalisation
# ══════════════════════════════════════════════

def _normalise_bpm(y, sr, target):
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        detected = float(np.atleast_1d(tempo)[0])
    except Exception:
        return y, 0.0
    if detected < 20:
        return y, 0.0
    ratio = detected / target
    ratio = max(0.55, min(1.80, ratio))
    return _stretch(y, ratio), detected


# ══════════════════════════════════════════════
#  Leslie / Organ (Nhạc Sống)
# ══════════════════════════════════════════════

def _leslie(y, sr, speed="slow", depth=0.30):
    rate = 6.8 if speed == "fast" else 0.85
    t    = np.arange(len(y), dtype=np.float32) / sr

    # Treble: AM + Doppler delay
    am_hi = (1.0 - depth * 0.55 * np.sin(2 * np.pi * rate * t)).astype(np.float32)
    y_hi  = _hpf(y, sr, 800) * am_hi
    delay_curve = (int(0.003 * sr) * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t))).astype(int)
    y_dop = np.zeros_like(y_hi)
    for i in range(len(y_hi)):
        src = i - delay_curve[i]
        y_dop[i] = y_hi[src] if 0 <= src < len(y_hi) else 0.0

    # Bass: slower AM
    am_lo = (1.0 - depth * 0.28 * np.sin(2 * np.pi * rate * 0.72 * t)).astype(np.float32)
    y_lo  = _lpf(y, sr, 800) * am_lo

    return (y_lo + y_dop).astype(np.float32)


def _organ_vibrato(y, sr, rate=5.5, depth_cents=18):
    max_d = int((depth_cents / 1200.0 / rate) * sr * 10)
    if max_d < 1:
        return y
    t = np.arange(len(y), dtype=np.float32) / sr
    dc = (max_d * 0.5 * (1 + np.sin(2 * np.pi * rate * t))).astype(int)
    out = np.zeros_like(y)
    for i in range(len(y)):
        src = i - dc[i]
        out[i] = y[src] if 0 <= src < len(y) else 0.0
    return out.astype(np.float32)


def _roland_eq(y, sr):
    y = _hpf(y, sr, 60)
    y = _peak(y, sr, 300,  -2.0, Q=0.9)
    y = _peak(y, sr, 850,  +3.5, Q=1.3)
    y = _peak(y, sr, 2500, +4.0, Q=1.4)
    y = _peak(y, sr, 6000, +2.5, Q=1.0)
    y = _lpf(y, sr, 13000)
    return y


def _yamaha_eq(y, sr):
    y = _hpf(y, sr, 45)
    y = _peak(y, sr, 200,  +2.5, Q=0.8)
    y = _peak(y, sr, 500,  +3.0, Q=1.1)
    y = _peak(y, sr, 1200, +1.5, Q=1.2)
    y = _peak(y, sr, 3500, -2.0, Q=1.3)
    y = _peak(y, sr, 7000, +1.0, Q=1.0)
    y = _lpf(y, sr, 10500)
    return y


def _organ_chain(y, sr, brand="yamaha", leslie_speed="slow", depth=0.28, ix=0.7):
    y = _yamaha_eq(y, sr) if brand == "yamaha" else _roland_eq(y, sr)
    y = np.tanh(y * (1.0 + ix * 0.3)).astype(np.float32)   # tube pre-amp
    y = _leslie(y, sr, speed=leslie_speed, depth=depth * ix)
    y = _organ_vibrato(y, sr)
    y = _reverb(y, sr, room=0.30, wet=0.16 * ix)
    return y


# ══════════════════════════════════════════════
#  Style processors
# ══════════════════════════════════════════════

class Style:
    TARGET_BPM: float = 100.0
    BRAND: str = "yamaha"

    def run(self, y: np.ndarray, sr: int, ix: float) -> np.ndarray:
        raise NotImplementedError


# ── Nhạc Sống ─────────────────────────────────

class Bolero(Style):
    TARGET_BPM = 72.0
    def run(self, y, sr, ix):
        y = _peak(y, sr, 400, +2.5*ix, Q=0.9)
        y = _peak(y, sr, 1500, -2.5*ix, Q=1.2)
        y = _organ_chain(y, sr, "yamaha", "slow", 0.28, ix)
        y = _reverb(y, sr, room=0.60, wet=0.28*ix)
        y = _lpf(y, sr, 9500 + (1-ix)*3000)
        return y


class Rumba(Style):
    TARGET_BPM = 108.0
    def run(self, y, sr, ix):
        y = _peak(y, sr, 3000, +2.0*ix, Q=1.2)
        y = _peak(y, sr, 200,  +1.5*ix, Q=0.9)
        y = _organ_chain(y, sr, "yamaha", "slow", 0.22, ix)
        y = _reverb(y, sr, room=0.35, wet=0.18*ix)
        return y


class ChaCha(Style):
    TARGET_BPM = 124.0
    def run(self, y, sr, ix):
        y = _peak(y, sr, 800,  +3.0*ix, Q=1.3)
        y = _peak(y, sr, 4000, +2.5*ix, Q=1.2)
        y = _hpf(y, sr, 100)
        y = _organ_chain(y, sr, "roland", "fast", 0.30, ix)
        y = _reverb(y, sr, room=0.18, wet=0.10*ix)
        return y


class SlowRockNS(Style):
    """Slow Rock nhạc sống — organ + nhẹ overdrive."""
    TARGET_BPM = 76.0
    def run(self, y, sr, ix):
        driven = np.tanh(y * (1.4 + ix * 2.0)) / (1.4 + ix * 0.4)
        y = (1 - ix*0.4)*y + ix*0.4*driven.astype(np.float32)
        y = _hpf(y, sr, 100)
        y = _peak(y, sr, 2500, +3.0*ix, Q=1.3)
        y = _organ_chain(y, sr, "roland", "fast", 0.25, ix)
        y = _reverb(y, sr, room=0.45, wet=0.22*ix)
        return y


class Tango(Style):
    TARGET_BPM = 122.0
    def run(self, y, sr, ix):
        y = _peak(y, sr, 1000, +4.0*ix, Q=1.5)
        y = _peak(y, sr, 300,  +2.0*ix, Q=1.0)
        y = _peak(y, sr, 5000, -1.5*ix, Q=1.2)
        y = _organ_chain(y, sr, "roland", "fast", 0.26, ix)
        y = np.clip(y * (1.0 + ix*0.25), -1.0, 1.0).astype(np.float32)
        y = _reverb(y, sr, room=0.22, wet=0.10*ix)
        return y


class Valse(Style):
    TARGET_BPM = 172.0
    def run(self, y, sr, ix):
        y = _peak(y, sr, 600,  +2.0*ix, Q=0.9)
        y = _peak(y, sr, 3500, +1.5*ix, Q=1.2)
        y = _organ_chain(y, sr, "yamaha", "slow", 0.32, ix)
        y = _reverb(y, sr, room=0.68, wet=0.32*ix)
        y = _lpf(y, sr, 10500)
        return y


# ── Rock / Metal ──────────────────────────────

class HardRock(Style):
    """Classic hard rock — Marshall-style amp, punchy, mid presence."""
    TARGET_BPM = 120.0
    def run(self, y, sr, ix):
        # Pre-gain EQ (tighten low end)
        y = _hpf(y, sr, 120)
        y = _peak(y, sr, 100, -2.0*ix, Q=1.0)   # cut boomy sub
        # Amp overdrive
        y = _distortion(y, drive=2.5 + ix*3.0, mix=0.55*ix, clip="asymm")
        # Post-amp EQ (mid presence + cabinet roll-off)
        y = _peak(y, sr, 700,  +2.5*ix, Q=1.2)   # upper-low body
        y = _peak(y, sr, 2200, +3.5*ix, Q=1.3)   # presence
        y = _peak(y, sr, 5500, +1.5*ix, Q=1.0)   # pick attack
        y = _lpf(y, sr, 8000 + (1-ix)*4000)       # cabinet hi-cut
        # Plate reverb
        y = _reverb(y, sr, room=0.35, wet=0.18*ix)
        # Compress for punch
        y = _compress(y, threshold=0.55, ratio=3.0, attack_ms=8, release_ms=100, sr=sr)
        return y


class HeavyMetal(Style):
    """Heavy/Thrash Metal — high-gain amp, scooped mids, tight."""
    TARGET_BPM = 160.0
    def run(self, y, sr, ix):
        # Drop-tuning feel
        y = _pitch(y, sr, -2.0 * ix)
        # Tight HP
        y = _hpf(y, sr, 80)
        # Scooped mid EQ (Metal zone style)
        y = _shelf_low(y, sr, 100, +4.0*ix)       # sub bass thump
        y = _peak(y, sr, 400,  -5.0*ix, Q=0.8)    # scoop low-mids
        y = _peak(y, sr, 800,  -4.0*ix, Q=0.9)    # scoop mids
        y = _peak(y, sr, 3000, +3.5*ix, Q=1.2)    # attack / bite
        y = _peak(y, sr, 6000, +2.0*ix, Q=1.0)    # hi-hat clarity
        # High-gain distortion (multiple stages)
        y = _distortion(y, drive=5.0 + ix*4.0, mix=0.70*ix, clip="tanh")
        y = _distortion(y, drive=2.0,           mix=0.25*ix, clip="hard")
        # Cabinet sim
        y = _lpf(y, sr, 7000)
        # Very tight room (metal drum sound)
        y = _reverb(y, sr, room=0.15, wet=0.08*ix)
        # Brick-wall compress
        y = _compress(y, threshold=0.45, ratio=8.0, attack_ms=3, release_ms=60, sr=sr)
        return y


class NuMetal(Style):
    """Nu-Metal — groove + heavy, down-tuned, thick low-end."""
    TARGET_BPM = 100.0
    def run(self, y, sr, ix):
        y = _pitch(y, sr, -1.5 * ix)
        y = _hpf(y, sr, 60)
        # Thick low-mid (djent / chunk)
        y = _peak(y, sr, 150,  +3.5*ix, Q=0.9)
        y = _peak(y, sr, 600,  -3.0*ix, Q=1.0)   # slight scoop
        y = _peak(y, sr, 2500, +2.5*ix, Q=1.2)   # presence
        # Moderate distortion
        y = _distortion(y, drive=3.5 + ix*2.5, mix=0.55*ix, clip="asymm")
        y = _lpf(y, sr, 9000)
        y = _reverb(y, sr, room=0.28, wet=0.15*ix)
        y = _compress(y, threshold=0.5, ratio=5.0, attack_ms=5, release_ms=80, sr=sr)
        return y


class Punk(Style):
    """Punk Rock — raw, fast, lo-fi distortion."""
    TARGET_BPM = 180.0
    def run(self, y, sr, ix):
        y = _hpf(y, sr, 150)
        # Raw amp (low-fi)
        y = _distortion(y, drive=3.0 + ix*3.5, mix=0.60*ix, clip="hard")
        y = _peak(y, sr, 1500, +4.0*ix, Q=1.4)   # mid punch
        y = _peak(y, sr, 4000, +3.0*ix, Q=1.2)   # bite
        y = _lpf(y, sr, 8500)
        y = _reverb(y, sr, room=0.18, wet=0.10*ix)
        return y


# ── Modern ────────────────────────────────────

class EDM(Style):
    TARGET_BPM = 128.0
    def run(self, y, sr, ix):
        y = _sidechain(y, sr, threshold=0.30 + (1-ix)*0.40)
        y_bass = _lpf(y, sr, 80)
        y = y + y_bass * ix * 0.55
        y_air  = _hpf(y, sr, 10000)
        y = y + y_air  * ix * 0.30
        y = _chorus(y, sr, depth_ms=5.0, rate_hz=0.5, wet=ix*0.22)
        y = np.clip(y * (1.0 + ix*0.35), -1.0, 1.0).astype(np.float32)
        return y


class Trap(Style):
    TARGET_BPM = 80.0     # half-time feel (trap often 65-90)
    def run(self, y, sr, ix):
        y = _stretch(y, 1.0 / 0.92)
        # 808 sub
        y_sub = _lpf(y, sr, 65)
        y = y + y_sub * ix * 1.3
        y = _distortion(y_sub, drive=2.0, mix=0.5) * ix * 0.4 + y
        y = _hpf(y, sr, 55)
        y_hi  = _hpf(y, sr, 7000)
        y = y + y_hi * ix * 0.4
        y = _reverb(y, sr, room=0.55, wet=0.18*ix)
        return y


class Lofi(Style):
    TARGET_BPM = 75.0
    def run(self, y, sr, ix):
        y = _stretch(y, 1.0 / 0.95)
        y = _lpf(y, sr, int(8000 - ix*3500))
        y = np.tanh(y * (1.0 + ix*0.5)).astype(np.float32)
        # Bit-crush
        bits = max(10, int(16 - ix*5))
        y = np.round(y * 2**bits) / 2**bits
        y = _vinyl(y, sr, amount=0.013*ix)
        y = _reverb(y, sr, room=0.32, wet=0.14*ix)
        return y


class RnB(Style):
    TARGET_BPM = 90.0
    def run(self, y, sr, ix):
        y = _stretch(y, 1.0 / 0.96)
        y_bass = _lpf(y, sr, 200)
        y = y + y_bass * ix * 0.40
        y = _lpf(y, sr, 14000)
        y = np.tanh(y * (1.0 + ix*0.35)).astype(np.float32)
        y = _reverb(y, sr, room=0.52, wet=0.28*ix)
        y = _chorus(y, sr, depth_ms=9.0, rate_hz=0.4, wet=ix*0.18)
        return y


class Phonk(Style):
    TARGET_BPM = 130.0
    def run(self, y, sr, ix):
        y = _stretch(y, 1.0 / 0.88)
        y = _pitch(y, sr, -2.0*ix)
        y_sub = _distortion(_lpf(y, sr, 80), drive=3.0, mix=0.8)
        y = y + y_sub * ix * 1.0
        y = _vinyl(y, sr, amount=0.020*ix)
        bits = max(11, int(14 - ix*3))
        y = np.round(y * 2**bits) / 2**bits
        y = _lpf(y, sr, 10000 - ix*2500)
        return y


class Ambient(Style):
    TARGET_BPM = 70.0
    def run(self, y, sr, ix):
        y = _stretch(y, 1.0 / 0.70)
        y = _pitch(y, sr, ix*3.0)
        y = _lpf(y, sr, 6000 - ix*800)
        y = _hpf(y, sr, 200)
        y = _reverb(y, sr, room=0.88, wet=0.58*ix)
        y = _chorus(y, sr, depth_ms=14.0, rate_hz=0.22, wet=ix*0.45)
        n = len(y); fade = int(sr*2.0)
        if n > fade*2:
            y[:fade] *= np.linspace(0, 1, fade)
            y[-fade:] *= np.linspace(1, 0, fade)
        return y


# ══════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════

STYLES: Dict[str, Style] = {
    # Nhạc Sống
    "bolero":    Bolero(),
    "rumba":     Rumba(),
    "chachacha": ChaCha(),
    "slowrock":  SlowRockNS(),
    "tango":     Tango(),
    "valse":     Valse(),
    # Rock / Metal
    "hardrock":  HardRock(),
    "heavymetal":HeavyMetal(),
    "numetal":   NuMetal(),
    "punk":      Punk(),
    # Modern
    "edm":       EDM(),
    "trap":      Trap(),
    "lofi":      Lofi(),
    "rnb":       RnB(),
    "phonk":     Phonk(),
    "ambient":   Ambient(),
}

STYLE_IDS = list(STYLES.keys())


# ══════════════════════════════════════════════
#  Main converter
# ══════════════════════════════════════════════

class BeatConverter:
    def convert(
        self,
        input_path: str,
        output_path: str,
        style: str,
        intensity: float = 0.70,
    ) -> Dict[str, Any]:

        y, sr = _load(input_path)

        # ── Analyse ──
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

        # ── BPM normalise ──
        proc = STYLES[style]
        y, detected_bpm = _normalise_bpm(y, sr, proc.TARGET_BPM)

        # ── Style transform ──
        y = proc.run(y, sr, intensity)

        # ── Final master ──
        y = _normalize(y, db=-2.0)
        _save(y, sr, output_path)

        return {
            "original_bpm":        round(bpm, 1),
            "target_bpm":          proc.TARGET_BPM,
            "duration_sec":        round(duration, 2),
            "beat_count":          int(len(beats)),
            "spectral_centroid_hz": round(spectral_centroid, 1),
            "output_sr":           sr,
        }
