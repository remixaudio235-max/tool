import os
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from processor import BeatConverter, STYLE_IDS

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="BeatStyle Converter", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

converter = BeatConverter()


def cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass


# ─── Style metadata ───────────────────────────────────────────────────────────
STYLE_META = {
    # ── Nhạc Sống ──
    "bolero":     {"group": "nhac_song", "name": "Bolero",        "emoji": "💙", "bpm": 72,  "time": "4/4", "desc": "Trữ tình, sâu lắng — Yamaha organ"},
    "rumba":      {"group": "nhac_song", "name": "Rumba",         "emoji": "🌹", "bpm": 108, "time": "4/4", "desc": "Lãng mạn, Latin groove nhẹ nhàng"},
    "chachacha":  {"group": "nhac_song", "name": "Cha-cha-cha",   "emoji": "💃", "bpm": 124, "time": "4/4", "desc": "Vui tươi, Roland organ staccato"},
    "slowrock":   {"group": "nhac_song", "name": "Slow Rock",     "emoji": "🎹", "bpm": 76,  "time": "4/4", "desc": "Organ + nhẹ overdrive, cảm xúc"},
    "tango":      {"group": "nhac_song", "name": "Tango",         "emoji": "🌊", "bpm": 122, "time": "4/4", "desc": "Kịch tính, mạnh mẽ, Roland organ"},
    "valse":      {"group": "nhac_song", "name": "Valse",         "emoji": "🌸", "bpm": 172, "time": "3/4", "desc": "Nhịp 3/4 lả lướt, Yamaha ấm"},
    # ── Rock / Metal ──
    "hardrock":   {"group": "rock_metal", "name": "Hard Rock",    "emoji": "🎸", "bpm": 120, "time": "4/4", "desc": "Marshall amp, mid presence, punchy"},
    "heavymetal": {"group": "rock_metal", "name": "Heavy Metal",  "emoji": "💀", "bpm": 160, "time": "4/4", "desc": "High-gain, scooped mids, drop-tuned"},
    "numetal":    {"group": "rock_metal", "name": "Nu-Metal",     "emoji": "🔥", "bpm": 100, "time": "4/4", "desc": "Groove + heavy, thick low-end"},
    "punk":       {"group": "rock_metal", "name": "Punk Rock",    "emoji": "⚡", "bpm": 180, "time": "4/4", "desc": "Raw, fast, lo-fi distortion"},
    # ── Modern ──
    "edm":        {"group": "modern",    "name": "EDM",           "emoji": "🎧", "bpm": 128, "time": "4/4", "desc": "Sidechain, sub-bass, pumping"},
    "trap":       {"group": "modern",    "name": "Trap",          "emoji": "🔊", "bpm": 80,  "time": "4/4", "desc": "808 sub, hi-hat space, dark"},
    "lofi":       {"group": "modern",    "name": "Lo-fi Hip Hop", "emoji": "🎵", "bpm": 75,  "time": "4/4", "desc": "Vinyl crackle, warm, chilled"},
    "rnb":        {"group": "modern",    "name": "R&B / Soul",    "emoji": "💜", "bpm": 90,  "time": "4/4", "desc": "Smooth, tape warmth, lush reverb"},
    "phonk":      {"group": "modern",    "name": "Phonk",         "emoji": "🌑", "bpm": 130, "time": "4/4", "desc": "Memphis, distorted 808, vinyl grit"},
    "ambient":    {"group": "modern",    "name": "Ambient",       "emoji": "🌊", "bpm": 70,  "time": "4/4", "desc": "Dreamy, massive reverb, stretched"},
}

GROUP_LABELS = {
    "nhac_song":  "🎹 Nhạc Sống Việt Nam",
    "rock_metal": "🎸 Rock & Metal",
    "modern":     "🎧 Modern",
}


@app.get("/api/styles")
async def get_styles():
    groups = {}
    for sid, meta in STYLE_META.items():
        g = meta["group"]
        if g not in groups:
            groups[g] = {"label": GROUP_LABELS[g], "styles": []}
        groups[g]["styles"].append({
            "id":    sid,
            "name":  meta["name"],
            "emoji": meta["emoji"],
            "bpm":   meta["bpm"],
            "time":  meta["time"],
            "desc":  meta["desc"],
        })
    return {"groups": list(groups.values())}


@app.post("/api/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    style: str = Form(...),
    intensity: float = Form(0.70),
):
    if style not in STYLE_IDS:
        raise HTTPException(400, f"Style không hợp lệ: {style}")
    if not (0.0 <= intensity <= 1.0):
        raise HTTPException(400, "intensity phải 0.0–1.0")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}:
        raise HTTPException(400, f"Định dạng không hỗ trợ: {suffix}")

    job_id     = str(uuid.uuid4())
    in_path    = UPLOAD_DIR / f"{job_id}{suffix}"
    out_path   = OUTPUT_DIR / f"{job_id}_{style}.wav"

    async with aiofiles.open(in_path, "wb") as f:
        await f.write(await file.read())

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            lambda: converter.convert(str(in_path), str(out_path), style, intensity),
        )
    except Exception as e:
        background_tasks.add_task(cleanup, str(in_path))
        raise HTTPException(500, f"Lỗi xử lý: {e}")

    background_tasks.add_task(cleanup, str(in_path))
    meta = STYLE_META[style]

    return JSONResponse({
        "job_id":       job_id,
        "style":        style,
        "style_name":   meta["name"],
        "download_url": f"/api/download/{job_id}_{style}.wav",
        "info":         info,
    })


@app.get("/api/download/{filename}")
async def download(filename: str, background_tasks: BackgroundTasks):
    safe = Path(filename).name
    path = OUTPUT_DIR / safe
    if not path.exists():
        raise HTTPException(404, "File không tìm thấy")
    background_tasks.add_task(cleanup, str(path))
    return FileResponse(str(path), media_type="audio/wav", filename=safe)


# Serve frontend
for _d in [
    Path(__file__).parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "frontend" / "public",
]:
    if _d.exists():
        app.mount("/", StaticFiles(directory=str(_d), html=True), name="static")
        break
