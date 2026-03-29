"""
NhacSong Beat Processor – Karaoke beat converter for Vietnamese live music.

Pipeline for each track:
  1. Load audio (stereo-aware)
  2. Vocal removal  →  karaoke instrumental
  3. BPM normalisation  →  target rhythm tempo
  4. Organ simulation  →  Roland / Yamaha tone
  5. Style-specific rhythm feel (EQ, dynamics, texture)
  6. Normalize & export
"""

from __future__ import annotations

import numpy as np
import soundfile as sf
import librosa
from scipy import signal as scipy_signal
from typing import Dict, Any, Tuple


# ─────────────────────────────────────────────
#  I/O helpers
# ─────────────────────────────────────────────

def _load_stereo(path: str) -> Tuple[np.ndarray, np.ndarray, int]:
    """Return (left, right, sr) as float32 arrays. Falls back to mono duplication."""
    data, sr = sf.read(path, always_2d=True)
    data = data.T.astype(np.float32)          # shape: (channels, samples)
    if data.shape[0] >= 2:
        return data[0], data[1], int(sr)
    return data[0], data[0].copy(), int(sr)


def _to_mono(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return ((left + right) * 0.5).astype(np.float32)


def _save(y: np.ndarray, sr: int, path: str):
    sf.write(path, np.clip(y, -1.0, 1.0), sr, subtype="PCM_16")


def _normalize(y: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    peak = np.max(np.abs(y))
    if peak < 1e-9:
        return y
    return y * (10 ** (target_db / 20.0)) / peak


# ─────────────────────────────────────────────
#  DSP primitives
# ─────────────────────────────────────────────

def _lpf(y: np.ndarray, sr: int, cutoff: float, order: int = 2) -> np.ndarray:
    nyq = sr / 2.0
    b, a = scipy_signal.butter(order, min(cutoff, nyq * 0.99) / nyq, btype="low")
    return scipy_signal.lfilter(b, a, y).astype(np.float32)


def _hpf(y: np.ndarray, sr: int, cutoff: float, order: int = 2) -> np.ndarray:
    nyq = sr / 2.0
    b, a = scipy_signal.butter(order, max(cutoff, 20) / nyq, btype="high")
    return scipy_signal.lfilter(b, a, y).astype(np.float32)


def _peak_eq(y: np.ndarray, sr: int, freq: float, gain_db: float, Q: float = 1.4) -> np.ndarray:
    """Parametric peak/notch EQ."""
    nyq = sr / 2.0
    w0 = min(freq / nyq, 0.99)
    A = 10 ** (gain_db / 40.0)
    alpha = np.sin(np.arccos(w0)) / (2 * Q)
    b0 =  1 + alpha * A
    b1 = -2 * np.cos(np.arccos(w0))
    b2 =  1 - alpha * A
    a0 =  1 + alpha / A
    a1 = -2 * np.cos(np.arccos(w0))
    a2 =  1 - alpha / A
    b = np.array([b0/a0, b1/a0, b2/a0])
    a = np.array([1.0,   a1/a0, a2/a0])
    return scipy_signal.lfilter(b, a, y).astype(np.float32)


def _reverb(y: np.ndarray, sr: int, room: float = 0.4, wet: float = 0.25) -> np.ndarray:
    ir_len = int(room * 3.0 * sr)
    t = np.linspace(0, room * 3.0, ir_len)
    ir = np.random.default_rng(42).standard_normal(ir_len).astype(np.float32)
    ir *= np.exp(-6.0 * t / (room * 3.0)).astype(np.float32)
    ir /= np.max(np.abs(ir) + 1e-9)
    wet_sig = np.convolve(y, ir, mode="full")[: len(y)]
    return (1 - wet) * y + wet * wet_sig.astype(np.float32)


def _tape_sat(y: np.ndarray, drive: float = 0.4) -> np.ndarray:
    return (np.tanh(y * (1.0 + drive * 3.0)) / (1.0 + drive * 0.5)).astype(np.float32)


def _time_stretch(y: np.ndarray, rate: float) -> np.ndarray:
    if abs(rate - 1.0) < 0.005:
        return y
    try:
        return librosa.effects.time_stretch(y, rate=rate).astype(np.float32)
    except Exception:
        return y


# ─────────────────────────────────────────────
#  Vocal Removal
# ─────────────────────────────────────────────

def remove_vocals(left: np.ndarray, right: np.ndarray, sr: int,
                  strength: float = 1.0) -> np.ndarray:
    """
    Karaoke vocal removal using two complementary techniques:

    1. Center-channel cancellation (L - R):
       Works well on commercial stereo masters where lead vocal is panned center.

    2. HPSS-based vocal suppression on mono:
       Decomposes into harmonic (melody/vocal) + percussive (drums/bass),
       then attenuates the harmonic component that contains mid-range vocals.

    The two results are mixed; the balance depends on how different L and R are.
    """
    # --- Technique 1: stereo mid/side ---
    mid  = (left + right) * 0.5          # M  (everything)
    side = (left - right) * 0.5          # S  (everything NOT in center)

    # Blend: full side + partial mid (keeps bass/drum which is also centered)
    # Remove only vocal frequency range from mid (300 Hz – 4 kHz)
    mid_lf   = _lpf(mid, sr, 250)         # bass stays
    mid_hf   = _hpf(mid, sr, 4500)        # air stays
    mid_keep = mid_lf + mid_hf * 0.5

    vocal_canceled = mid_keep + side       # mid-range mostly gone

    # --- Technique 2: HPSS harmonic suppression ---
    D = librosa.stft(mid)
    H, P = librosa.decompose.hpss(D, margin=(1.0, 5.0))
    # Keep percussive fully, attenuate harmonic (where vocals live)
    scale = 1.0 - strength * 0.75
    D_noVocal = H * scale + P
    hpss_result = librosa.istft(D_noVocal, length=len(mid)).astype(np.float32)

    # Blend the two approaches
    stereo_diff = float(np.mean(np.abs(left - right)))
    # If stereo_diff is large → strong stereo → trust center-cancel more
    blend = min(stereo_diff / 0.15, 1.0)
    result = blend * vocal_canceled + (1.0 - blend) * hpss_result

    # Restore low-end body (bass guitar/kick lost in cancellation)
    bass_restore = _lpf(mid, sr, 180) * 0.8
    result = result + bass_restore

    return result.astype(np.float32)


# ─────────────────────────────────────────────
#  Roland / Yamaha Organ Simulation
# ─────────────────────────────────────────────

def _leslie_effect(y: np.ndarray, sr: int,
                   speed: str = "slow",
                   depth: float = 0.35) -> np.ndarray:
    """
    Leslie rotary speaker cabinet simulation.

    The Leslie cabinet has two rotors:
      - Treble horn  (fast: ~400 RPM / slow: ~50 RPM)
      - Bass drum    (fast: ~300 RPM / slow: ~40 RPM)

    Simulated via dual-rate AM (tremolo) + FM (Doppler pitch wobble).
    """
    rate_hz = 6.5 if speed == "fast" else 0.85
    bass_rate = rate_hz * 0.75

    t = np.arange(len(y), dtype=np.float32) / sr

    # ── Treble section (AM + slight pitch mod) ──
    am_treble = 1.0 - depth * 0.55 * (np.sin(2 * np.pi * rate_hz * t).astype(np.float32))
    y_hi  = _hpf(y, sr, 800)
    y_lo  = _lpf(y, sr, 800)
    y_hi  = y_hi * am_treble

    # Doppler: variable-delay approximated by short chorus
    max_delay_s = 0.003                     # 3 ms max
    delay_curve = (max_delay_s * sr *
                   (0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t))).astype(int)
    y_hi_dop = np.zeros_like(y_hi)
    for i in range(len(y_hi)):
        src = i - int(delay_curve[i])
        y_hi_dop[i] = y_hi[src] if 0 <= src < len(y_hi) else 0.0

    # ── Bass section (slower AM) ──
    am_bass = 1.0 - depth * 0.3 * (np.sin(2 * np.pi * bass_rate * t).astype(np.float32))
    y_lo = y_lo * am_bass

    return (y_lo + y_hi_dop).astype(np.float32)


def _organ_vibrato(y: np.ndarray, sr: int,
                   rate_hz: float = 5.5, depth_cents: float = 20.0) -> np.ndarray:
    """
    Yamaha organ vibrato scanner simulation.
    Modulates pitch at ~5–6 Hz (similar to drawbar organ scanner vibrato).
    """
    depth_s = (depth_cents / 1200.0) / rate_hz   # convert cents to seconds of delay
    max_delay = int(depth_s * sr * 12)
    if max_delay < 1:
        return y
    t = np.arange(len(y), dtype=np.float32) / sr
    delay_curve = (max_delay * 0.5 *
                   (1 + np.sin(2 * np.pi * rate_hz * t))).astype(int)
    out = np.zeros_like(y)
    for i in range(len(y)):
        src = i - int(delay_curve[i])
        out[i] = y[src] if 0 <= src < len(y) else 0.0
    return out.astype(np.float32)


def _roland_eq(y: np.ndarray, sr: int) -> np.ndarray:
    """Roland VK-series drawbar organ EQ signature: bright, punchy, clear attack."""
    y = _hpf(y, sr, 55)                        # remove sub rumble
    y = _peak_eq(y, sr, 300,  -2.0, Q=0.9)     # tame mud
    y = _peak_eq(y, sr, 800,  +3.5, Q=1.2)     # punch / body
    y = _peak_eq(y, sr, 2500, +4.0, Q=1.5)     # presence / attack
    y = _peak_eq(y, sr, 6000, +2.0, Q=1.0)     # brightness
    y = _lpf(y, sr, 12000)                      # smooth air (organ speaker roll-off)
    return y


def _yamaha_eq(y: np.ndarray, sr: int) -> np.ndarray:
    """Yamaha EL/AR electone organ EQ: warm, round, lush — classic nhạc sống tone."""
    y = _hpf(y, sr, 45)
    y = _peak_eq(y, sr, 200,  +2.0, Q=0.8)     # warmth
    y = _peak_eq(y, sr, 500,  +2.5, Q=1.1)     # fullness
    y = _peak_eq(y, sr, 1200, +1.5, Q=1.2)     # midrange
    y = _peak_eq(y, sr, 3500, -1.5, Q=1.3)     # reduce harshness
    y = _peak_eq(y, sr, 7000, +1.0, Q=1.0)     # subtle air
    y = _lpf(y, sr, 10000)                      # warm roll-off
    return y


def _apply_organ(y: np.ndarray, sr: int,
                 brand: str = "yamaha",
                 leslie_speed: str = "slow",
                 leslie_depth: float = 0.30,
                 vibrato: bool = True) -> np.ndarray:
    """Full organ simulation chain."""
    # 1. Tone EQ
    if brand == "roland":
        y = _roland_eq(y, sr)
    else:
        y = _yamaha_eq(y, sr)

    # 2. Tape saturation (tube pre-amp feel)
    y = _tape_sat(y, drive=0.25)

    # 3. Leslie rotary cabinet
    y = _leslie_effect(y, sr, speed=leslie_speed, depth=leslie_depth)

    # 4. Organ vibrato (Yamaha-style scanner vibrato)
    if vibrato:
        y = _organ_vibrato(y, sr, rate_hz=5.5, depth_cents=18.0)

    # 5. Short spring/hall reverb (amp cabinet ambience)
    y = _reverb(y, sr, room=0.3, wet=0.18)

    return y


# ─────────────────────────────────────────────
#  BPM Normalisation
# ─────────────────────────────────────────────

def _normalise_bpm(y: np.ndarray, sr: int, target_bpm: float) -> Tuple[np.ndarray, float]:
    """Stretch audio to match a target BPM (±40% guard)."""
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    detected = float(np.atleast_1d(tempo)[0])
    if detected < 20:
        return y, detected           # couldn't detect; skip

    ratio = detected / target_bpm
    ratio = max(0.60, min(1.70, ratio))    # guard: don't stretch beyond ±40%
    if abs(ratio - 1.0) < 0.03:
        return y, detected

    stretched = _time_stretch(y, rate=ratio)
    return stretched, detected


# ─────────────────────────────────────────────
#  Vietnamese Nhạc Sống Style Processors
# ─────────────────────────────────────────────

class StyleProcessor:
    TARGET_BPM: float = 100.0
    ORGAN_BRAND: str  = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        raise NotImplementedError

    def _organ(self, y: np.ndarray, sr: int, intensity: float,
               leslie_speed: str = "slow") -> np.ndarray:
        depth = 0.20 + intensity * 0.25
        return _apply_organ(y, sr, brand=self.ORGAN_BRAND,
                            leslie_speed=leslie_speed,
                            leslie_depth=depth,
                            vibrato=True)


class BoleroProcessor(StyleProcessor):
    """
    Bolero – Điệu buồn nhất, chậm rãi (~70 BPM, 4/4).
    Đặc trưng: organ ấm, sustain dài, bass nhẹ nhàng, reverb lớn.
    """
    TARGET_BPM = 72.0
    ORGAN_BRAND = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Warm low-mids
        y = _peak_eq(y, sr, 400, +2.5 * intensity, Q=0.9)
        # Cut harsh mids
        y = _peak_eq(y, sr, 1500, -3.0 * intensity, Q=1.2)
        # Organ simulation
        y = self._organ(y, sr, intensity, leslie_speed="slow")
        # Long sustain reverb (hall)
        y = _reverb(y, sr, room=0.65, wet=0.30 * intensity)
        # Subtle high-frequency softening
        y = _lpf(y, sr, 9000 + (1 - intensity) * 3000)
        return y


class RumbaProcessor(StyleProcessor):
    """
    Rumba – Latin groove (~110 BPM, 4/4).
    Đặc trưng: organ nhịp nhàng, bass syncopated, nhẹ nhàng.
    """
    TARGET_BPM = 108.0
    ORGAN_BRAND = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Bright Latin top-end
        y = _peak_eq(y, sr, 3000, +2.0 * intensity, Q=1.2)
        y = _peak_eq(y, sr, 200,  +1.5 * intensity, Q=0.9)
        # Organ
        y = self._organ(y, sr, intensity, leslie_speed="slow")
        # Medium room
        y = _reverb(y, sr, room=0.35, wet=0.18 * intensity)
        return y


class ChaChaChaProcessor(StyleProcessor):
    """
    Cha-cha-cha – Vui tươi (~125 BPM, 4/4).
    Đặc trưng: organ nhanh, staccato feel, bright.
    """
    TARGET_BPM = 124.0
    ORGAN_BRAND = "roland"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Bright & punchy
        y = _peak_eq(y, sr, 800,  +3.0 * intensity, Q=1.3)
        y = _peak_eq(y, sr, 4000, +2.5 * intensity, Q=1.2)
        y = _hpf(y, sr, 100)
        # Roland organ – bright
        y = self._organ(y, sr, intensity, leslie_speed="fast")
        # Short bright reverb
        y = _reverb(y, sr, room=0.2, wet=0.12 * intensity)
        return y


class SlowRockProcessor(StyleProcessor):
    """
    Slow Rock – ~75 BPM, 4/4. Ballad rock cảm xúc.
    Đặc trưng: organ dày, distortion nhẹ, reverb lớn.
    """
    TARGET_BPM = 76.0
    ORGAN_BRAND = "roland"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Drive (light overdrive)
        driven = np.tanh(y * (1.5 + intensity * 2.0)) / (1.5 + intensity * 0.5)
        y = (1 - intensity * 0.45) * y + intensity * 0.45 * driven.astype(np.float32)
        # High-pass tighten
        y = _hpf(y, sr, 100)
        # Upper-mid presence
        y = _peak_eq(y, sr, 2500, +3.5 * intensity, Q=1.3)
        # Roland organ
        y = self._organ(y, sr, intensity, leslie_speed="fast")
        # Plate reverb
        y = _reverb(y, sr, room=0.5, wet=0.25 * intensity)
        return y


class TangoProcessor(StyleProcessor):
    """
    Tango – Mạnh mẽ, kịch tính (~120 BPM, 2/4 or 4/4).
    Đặc trưng: organ sắc bén, staccato, bass chắc.
    """
    TARGET_BPM = 122.0
    ORGAN_BRAND = "roland"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Sharp attack boost
        y = _peak_eq(y, sr, 1000, +4.0 * intensity, Q=1.5)
        y = _peak_eq(y, sr, 300,  +2.0 * intensity, Q=1.0)
        y = _peak_eq(y, sr, 5000, -1.5 * intensity, Q=1.2)
        # Roland – bright & cutting
        y = self._organ(y, sr, intensity, leslie_speed="fast")
        # Hard limiting for drama
        y = np.clip(y * (1.0 + intensity * 0.3), -1.0, 1.0)
        # Tight room
        y = _reverb(y, sr, room=0.25, wet=0.12 * intensity)
        return y


class DiscoProcessor(StyleProcessor):
    """
    Disco – Sôi động (~120–126 BPM, 4/4).
    Đặc trưng: organ funky, bass pumping, bright highs.
    """
    TARGET_BPM = 122.0
    ORGAN_BRAND = "roland"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Sidechain-like ducking on beats
        try:
            _, beats = librosa.beat.beat_track(y=y, sr=sr)
            beat_samples = librosa.frames_to_samples(beats)
            env = np.ones(len(y), dtype=np.float32)
            atk = int(0.005 * sr)
            rel = int(0.07 * sr)
            for b in beat_samples:
                e = min(b + atk, len(y)); env[b:e] = np.linspace(1, 0.35, e - b)
                e2 = min(e + rel, len(y)); env[e:e2] = np.linspace(0.35, 1, e2 - e)
            y = y * env
        except Exception:
            pass
        # Funky mid boost
        y = _peak_eq(y, sr, 700,  +3.0 * intensity, Q=1.2)
        y = _peak_eq(y, sr, 8000, +2.5 * intensity, Q=1.0)
        # Roland organ
        y = self._organ(y, sr, intensity, leslie_speed="fast")
        return y


class ValseProcessor(StyleProcessor):
    """
    Valse (Waltz) – Nhẹ nhàng, lãng mạn (~170 BPM, 3/4).
    Đặc trưng: organ lả lướt, reverb lớn, ấm áp.
    """
    TARGET_BPM = 172.0
    ORGAN_BRAND = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Flowing mid-high
        y = _peak_eq(y, sr, 600,  +2.0 * intensity, Q=0.9)
        y = _peak_eq(y, sr, 3500, +1.5 * intensity, Q=1.2)
        # Yamaha – warm & lush
        y = self._organ(y, sr, intensity, leslie_speed="slow")
        # Big hall reverb (ballroom feel)
        y = _reverb(y, sr, room=0.7, wet=0.35 * intensity)
        # Smooth highs
        y = _lpf(y, sr, 10000)
        return y


class FoxProcessor(StyleProcessor):
    """
    Fox Trot – Nhẹ nhàng, duyên dáng (~135 BPM, 4/4).
    """
    TARGET_BPM = 135.0
    ORGAN_BRAND = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        y = _peak_eq(y, sr, 500,  +2.0 * intensity, Q=1.0)
        y = _peak_eq(y, sr, 2500, +2.0 * intensity, Q=1.2)
        y = self._organ(y, sr, intensity, leslie_speed="slow")
        y = _reverb(y, sr, room=0.3, wet=0.20 * intensity)
        return y


class TwistProcessor(StyleProcessor):
    """
    Twist – Vui nhộn, retro (~130 BPM, 4/4).
    Đặc trưng: organ vintage, lo-fi nhẹ, bright treble.
    """
    TARGET_BPM = 130.0
    ORGAN_BRAND = "roland"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Retro bite
        y = _peak_eq(y, sr, 1200, +4.0 * intensity, Q=1.5)
        y = _peak_eq(y, sr, 5000, +3.0 * intensity, Q=1.2)
        # Vintage tape sat
        y = _tape_sat(y, drive=intensity * 0.5)
        # Roland fast leslie
        y = self._organ(y, sr, intensity, leslie_speed="fast")
        # Tight room
        y = _reverb(y, sr, room=0.2, wet=0.12 * intensity)
        return y


class BalladeProcessor(StyleProcessor):
    """
    Ballade – Chậm rãi, sâu lắng (~55 BPM, 4/4 or 6/8).
    Đặc trưng: organ sâu lắng, sustain rất dài, bass ấm.
    """
    TARGET_BPM = 56.0
    ORGAN_BRAND = "yamaha"

    def process(self, y: np.ndarray, sr: int, intensity: float) -> np.ndarray:
        # Very warm low-mids
        y = _peak_eq(y, sr, 300,  +3.0 * intensity, Q=0.8)
        y = _peak_eq(y, sr, 2000, -2.0 * intensity, Q=1.0)   # cut harshness
        # Ultra-warm Yamaha organ
        y = self._organ(y, sr, intensity, leslie_speed="slow")
        # Cathedral reverb
        y = _reverb(y, sr, room=0.85, wet=0.40 * intensity)
        # Fade in/out edges
        fade = int(sr * 1.5)
        if len(y) > fade * 2:
            y[:fade]  *= np.linspace(0, 1, fade)
            y[-fade:] *= np.linspace(1, 0, fade)
        return y


# ─────────────────────────────────────────────
#  Registry
# ─────────────────────────────────────────────

PROCESSORS: Dict[str, StyleProcessor] = {
    "bolero":    BoleroProcessor(),
    "rumba":     RumbaProcessor(),
    "chachacha": ChaChaChaProcessor(),
    "slowrock":  SlowRockProcessor(),
    "tango":     TangoProcessor(),
    "disco":     DiscoProcessor(),
    "valse":     ValseProcessor(),
    "fox":       FoxProcessor(),
    "twist":     TwistProcessor(),
    "ballade":   BalladeProcessor(),
}


# ─────────────────────────────────────────────
#  Main Converter
# ─────────────────────────────────────────────

class BeatConverter:
    def convert(
        self,
        input_path: str,
        output_path: str,
        style: str,
        intensity: float = 0.7,
        vocal_removal: bool = True,
        vocal_strength: float = 0.85,
        organ_brand: str = "auto",       # "auto" | "roland" | "yamaha"
    ) -> Dict[str, Any]:

        left, right, sr = _load_stereo(input_path)
        y_mono = _to_mono(left, right)

        # ── Analysis (pre-processing) ──
        duration = len(y_mono) / sr
        try:
            tempo, beats = librosa.beat.beat_track(y=y_mono, sr=sr)
            bpm = float(np.atleast_1d(tempo)[0])
        except Exception:
            bpm = 0.0
            beats = np.array([])

        # ── Step 1: Vocal removal ──
        if vocal_removal:
            y = remove_vocals(left, right, sr, strength=vocal_strength)
        else:
            y = y_mono.copy()

        # ── Step 2: BPM normalisation ──
        proc = PROCESSORS[style]
        # Override organ brand if user specified
        if organ_brand != "auto":
            proc.ORGAN_BRAND = organ_brand

        y, detected_bpm = _normalise_bpm(y, sr, proc.TARGET_BPM)

        # ── Step 3: Style transformation + organ ──
        y = proc.process(y, sr, intensity)

        # ── Step 4: Final normalise ──
        y = _normalize(y, target_db=-3.0)
        _save(y, sr, output_path)

        return {
            "original_bpm":    round(bpm, 1),
            "target_bpm":      proc.TARGET_BPM,
            "duration_sec":    round(duration, 2),
            "beat_count":      int(len(beats)),
            "output_sr":       sr,
            "vocal_removed":   vocal_removal,
            "organ_brand":     proc.ORGAN_BRAND,
        }
