# BeatStyle – Chuyển Beat sang Style Khác

**Input:** Beat gốc đã tách vocal (từ AI tool bên ngoài như Spleeter, Demucs, etc.)
**Output:** WAV với sonic style hoàn toàn mới

---

## 16 Styles

### 🎹 Nhạc Sống Việt Nam
| Style | BPM | Nhịp | Organ | Đặc điểm |
|---|---|---|---|---|
| 💙 **Bolero** | 72 | 4/4 | Yamaha | Warm, sustain dài, reverb lớn |
| 🌹 **Rumba** | 108 | 4/4 | Yamaha | Latin groove, nhẹ nhàng |
| 💃 **Cha-cha-cha** | 124 | 4/4 | Roland | Staccato, bright, vui tươi |
| 🎹 **Slow Rock** | 76 | 4/4 | Roland | Organ + light overdrive |
| 🌊 **Tango** | 122 | 4/4 | Roland | Kịch tính, sắc bén |
| 🌸 **Valse** | 172 | 3/4 | Yamaha | Lả lướt, ballroom reverb |

### 🎸 Rock & Metal
| Style | BPM | Đặc điểm DSP |
|---|---|---|
| 🎸 **Hard Rock** | 120 | Marshall asymm clip, presence boost, plate reverb |
| 💀 **Heavy Metal** | 160 | High-gain 2-stage dist, scooped mids, drop-tune -2st |
| 🔥 **Nu-Metal** | 100 | Moderate gain, thick low-mid, drop-tune -1.5st |
| ⚡ **Punk Rock** | 180 | Hard clip, raw mid punch, minimal reverb |

### 🎧 Modern
| Style | BPM | Đặc điểm DSP |
|---|---|---|
| 🎧 **EDM** | 128 | Sidechain compress, sub-bass boost, chorus |
| 🔊 **Trap** | 80 | 808 sub distortion, hi-hat boost |
| 🎵 **Lo-fi** | 75 | Bit-crush, vinyl noise, warm LP |
| 💜 **R&B** | 90 | Tape sat, deep reverb, lush chorus |
| 🌑 **Phonk** | 130 | Pitch -2st, 808 dist, vinyl grit |
| 🌊 **Ambient** | 70 | Stretch ×1.4, massive reverb, dreamy chorus |

---

## Cách chạy

```bash
./run.sh
# Truy cập: http://localhost:8000
```

Yêu cầu Python 3.9+. Dependencies tự cài lần đầu.

---

## Workflow

```
Beat gốc (MP3/WAV/FLAC)
    │
    ▼
[1] Phân tích BPM + spectral
    │
    ▼
[2] BPM normalise (time-stretch về target của style)
    │
    ▼
[3] Style DSP chain:
    ├─ Nhạc Sống  → EQ → Tube sat → Leslie rotary → Vibrato → Reverb
    ├─ Metal      → Pre-EQ → Multi-stage distortion → Scooped EQ → Cabinet LP
    └─ Modern     → Style-specific chain
    │
    ▼
[4] Master normalize → WAV 16-bit
```

---

## Kiến trúc

```
beatstyle/
├── backend/
│   ├── main.py       # FastAPI: /api/styles · /api/convert · /api/download
│   └── processor.py
│       ├── DSP primitives (_lpf, _hpf, _peak, _compress, _reverb, _distortion …)
│       ├── Organ: _roland_eq / _yamaha_eq / _leslie / _organ_vibrato
│       ├── Style classes: Bolero, Rumba, ChaCha, HardRock, HeavyMetal, NuMetal …
│       └── BeatConverter.convert()
├── frontend/
│   └── public/ (index.html · style.css · app.js)
├── requirements.txt
└── run.sh
```

---

## API

| Method | Path | Body |
|---|---|---|
| `GET` | `/api/styles` | — |
| `POST` | `/api/convert` | `file`, `style`, `intensity` (0–1) |
| `GET` | `/api/download/{file}` | — |

---

## DSP kỹ thuật

| Kỹ thuật | Mô tả |
|---|---|
| **IIR Biquad EQ** | LP/HP Butterworth + parametric peak/notch + low-shelf |
| **Leslie rotary** | AM tremolo (dual-rate treble/bass) + Doppler delay FM |
| **Distortion** | tanh soft-clip · hard clip · asymmetric (tube feel) |
| **Scooped mids** | -5 dB @ 400 Hz, +4 dB sub, +3.5 dB @ 3 kHz (Metal zone) |
| **Compressor** | Feed-forward RMS envelope, attack/release configurable |
| **Time-stretch** | librosa STFT phase vocoder |
| **Pitch shift** | librosa phase vocoder pitch shift |
| **Reverb** | Exponential-decay IR convolution |
| **Bit-crush** | Quantize to N bits |
| **Vinyl noise** | Procedural hiss + sparse crackle bursts |
