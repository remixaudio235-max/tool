# BeatShift – Music Beat Converter

Transform any song into a different musical style using signal processing.
Inspired by Suno, built with Python + FastAPI + vanilla JS.

---

## Features

| Style | Effect |
|---|---|
| 🎵 Lo-fi Hip Hop | Vinyl crackle, tape saturation, bit-crush, warm low-pass |
| ⚡ EDM / Electronic | Sidechain compression, sub-bass boost, chorus |
| 🔥 Trap | 808 sub-bass, hi-hat space, reverb tail |
| 🎷 Jazz | Swing quantization, tube warmth, room reverb |
| 🎸 Rock | Guitar amp distortion, cabinet sim, punch |
| 🌴 Reggaeton | Dembow sidechain, bass boost, crispy highs |
| 🌸 Bossa Nova | Swing, nylon-string chorus, hall reverb |
| 💜 R&B / Soul | Deep reverb, tape warmth, lush chorus |
| 💀 Phonk | Memphis slow-down, pitch shift, vinyl + bit crush |
| 🌊 Ambient | Dramatic stretch, massive reverb, dreamy pads |

**Effect Intensity** slider (0–100%) controls how strongly the style is applied.

---

## Quick Start

```bash
./run.sh
```

Then open **http://localhost:8000** in your browser.

Requires Python 3.9+. All dependencies are installed automatically on first run.

---

## Architecture

```
beatshift/
├── backend/
│   ├── main.py          # FastAPI server, REST API endpoints
│   └── processor.py     # Audio style engine (DSP pipeline)
├── frontend/
│   └── public/
│       ├── index.html   # Single-page UI
│       ├── style.css    # Dark-mode design system
│       └── app.js       # Upload, style selection, conversion flow
├── requirements.txt
└── run.sh               # One-command launcher
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/styles` | List all available styles |
| `POST` | `/api/convert` | Upload + convert audio file |
| `GET` | `/api/download/{filename}` | Download converted file |

### POST `/api/convert`

Form fields:
- `file` – audio file (MP3/WAV/OGG/FLAC/M4A, max 50 MB)
- `style` – style ID (e.g. `lofi`, `trap`, `jazz`)
- `intensity` – float 0.0–1.0 (default 0.7)

Response:
```json
{
  "job_id": "uuid",
  "style": "lofi",
  "download_url": "/api/download/uuid_lofi.wav",
  "info": {
    "original_bpm": 128.0,
    "duration_sec": 180.5,
    "spectral_centroid_hz": 2400.0,
    "beat_count": 384
  }
}
```

---

## How It Works

No AI or ML models are used. Each style applies a signal-processing chain:

- **EQ filters** (low-pass, high-pass, band-pass, peak) using IIR biquads
- **Time stretching & pitch shifting** via librosa STFT phase vocoder
- **Reverb** via exponential-decay impulse response convolution
- **Sidechain compression** beat-tracking with librosa + envelope ducking
- **Tape saturation** soft-clip via `tanh` transfer function
- **Bit crushing** for vintage lo-fi texture
- **Vinyl noise** – procedural hiss + sparse crackles
- **Swing quantization** – stretching/squeezing alternating beat pairs
- **Distortion** – soft-clip with gain staging

---

## Dependencies

- `fastapi` + `uvicorn` – web framework
- `librosa` – audio analysis (BPM, beats, spectral)
- `soundfile` – audio I/O
- `scipy` – IIR filter design
- `numpy` – signal processing arrays
- `pydub` – format conversion
- `aiofiles` – async file I/O
