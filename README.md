# NhạcSống Beat – Phần mềm chuyển bài hát thành Beat Karaoke Nhạc Sống

Chuyển bất kỳ bài hát nào thành **beat karaoke nhạc sống Việt Nam** với âm thanh Organ Roland / Yamaha.

---

## Tính năng

### 🎤 Tách Vocal (Karaoke)
Hai kỹ thuật kết hợp:
- **Center-channel cancellation** (L − R): Xoá giọng hát ở kênh center trong bản stereo thương mại
- **HPSS suppression**: Phân tách harmonic (giọng) vs percussive (trống/bass), rồi giảm thành phần harmonic
- Phục hồi bass/kick sau khi tách để giữ âm thanh đầy đặn

### 🎹 Giả lập Organ Roland / Yamaha
| Organ | Đặc điểm |
|---|---|
| **Yamaha** (EL/AR Electone) | Ấm, mượt, tròn — tone nhạc sống cổ điển |
| **Roland** (VK series) | Sáng, mạnh, hiện đại, attack rõ |

**Chuỗi xử lý Organ:**
1. EQ signature (Roland: bright 2.5 kHz · Yamaha: warm 500 Hz)
2. Tape saturation (tube pre-amp)
3. **Leslie rotary speaker** (Doppler AM + FM, tốc độ slow/fast)
4. **Scanner vibrato** (5.5 Hz, 18 cents — đặc trưng Yamaha)
5. Spring/hall reverb (amp cabinet ambience)

### 🎵 10 Điệu Nhạc Sống Việt Nam

| Điệu | BPM | Nhịp | Cảm xúc |
|---|---|---|---|
| 💙 **Bolero** | 72 | 4/4 | Trữ tình, buồn — điệu nhạc Việt đặc trưng |
| 🌹 **Rumba** | 108 | 4/4 | Lãng mạn, nhẹ nhàng |
| 💃 **Cha-cha-cha** | 124 | 4/4 | Vui tươi, sôi động |
| 🎸 **Slow Rock** | 76 | 4/4 | Cảm xúc, ballad rock |
| 🌊 **Tango** | 122 | 4/4 | Kịch tính, mạnh mẽ |
| 🪩 **Disco** | 122 | 4/4 | Sôi động, funky |
| 🌸 **Valse** | 172 | 3/4 | Lãng mạn, nhẹ nhàng |
| 🦊 **Fox Trot** | 135 | 4/4 | Duyên dáng |
| 🕺 **Twist** | 130 | 4/4 | Vui nhộn, retro |
| 🌙 **Ballade** | 56 | 4/4 | Sâu lắng, cô đơn nhất |

---

## Cài đặt & Chạy

```bash
./run.sh
# Mở trình duyệt: http://localhost:8000
```

Yêu cầu Python 3.9+. Tất cả dependency tự động cài lần đầu.

---

## Cách sử dụng

1. **Tải lên bài hát** (MP3/WAV/FLAC/OGG/M4A, tối đa 50 MB)
2. **Cài đặt Beat**:
   - Bật/tắt tách vocal (karaoke mode)
   - Điều chỉnh mức độ tách (0–100%)
   - Chọn âm thanh Organ: Yamaha / Roland / Tự động
   - Cường độ hiệu ứng (0–100%)
3. **Chọn điệu nhạc sống** (10 điệu)
4. **Tạo Beat** → Nghe thử → Tải về WAV

---

## Kiến trúc

```
nhacsonbeat/
├── backend/
│   ├── main.py        # FastAPI server — REST API
│   └── processor.py   # DSP engine
│       ├── remove_vocals()         # Tách vocal (stereo + HPSS)
│       ├── _leslie_effect()        # Leslie rotary cabinet
│       ├── _organ_vibrato()        # Yamaha scanner vibrato
│       ├── _roland_eq() / _yamaha_eq()
│       └── BoleroProcessor, RumbaProcessor, …  (10 styles)
├── frontend/
│   └── public/
│       ├── index.html   # UI tiếng Việt
│       ├── style.css    # Dark-mode design
│       └── app.js       # Upload + convert flow
├── requirements.txt
└── run.sh
```

### API

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/styles` | Danh sách các điệu |
| `POST` | `/api/convert` | Upload + chuyển đổi |
| `GET` | `/api/download/{file}` | Tải về file WAV |

**POST `/api/convert`** — Form fields:

| Field | Type | Default | Mô tả |
|---|---|---|---|
| `file` | File | — | File âm thanh |
| `style` | string | — | `bolero`, `rumba`, `chachacha`… |
| `intensity` | float 0–1 | 0.7 | Cường độ hiệu ứng |
| `vocal_removal` | bool | true | Bật tách vocal |
| `vocal_strength` | float 0–1 | 0.85 | Mức độ tách vocal |
| `organ_brand` | string | `auto` | `yamaha` / `roland` / `auto` |

---

## Kỹ thuật DSP sử dụng

- **Vocal removal**: Mid/Side processing + librosa HPSS (harmonic-percussive source separation)
- **Leslie rotary**: AM (amplitude modulation) + FM (Doppler delay modulation), dual-rate treble/bass rotors
- **Scanner vibrato**: Variable delay với LFO ~5.5 Hz
- **EQ**: IIR biquad filters (Butterworth LP/HP + parametric peak/notch)
- **BPM normalisation**: librosa beat tracking + phase vocoder time-stretch
- **Reverb**: Exponential-decay impulse response convolution
- **Tape saturation**: `tanh` soft-clip transfer function

---

## Dependencies

```
fastapi · uvicorn · librosa · soundfile · scipy · numpy · pydub · aiofiles
```
