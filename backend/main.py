import os
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from processor import BeatConverter

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Music Beat Converter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = BeatConverter()

VALID_STYLES = [
    "lofi", "edm", "trap", "jazz", "rock",
    "reggaeton", "bossanova", "rnb", "phonk", "ambient"
]


def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass


@app.get("/api/styles")
async def get_styles():
    return {
        "styles": [
            {"id": "lofi",      "name": "Lo-fi Hip Hop",   "emoji": "🎵", "description": "Chill, warm, vinyl crackle"},
            {"id": "edm",       "name": "EDM / Electronic", "emoji": "⚡", "description": "High-energy, pumping bass"},
            {"id": "trap",      "name": "Trap",             "emoji": "🔥", "description": "808s, hi-hats, dark vibes"},
            {"id": "jazz",      "name": "Jazz",             "emoji": "🎷", "description": "Swing feel, warm tone"},
            {"id": "rock",      "name": "Rock",             "emoji": "🎸", "description": "Driven, punchy, loud"},
            {"id": "reggaeton", "name": "Reggaeton",        "emoji": "🌴", "description": "Dembow rhythm, dancehall"},
            {"id": "bossanova", "name": "Bossa Nova",       "emoji": "🌸", "description": "Smooth, Brazilian groove"},
            {"id": "rnb",       "name": "R&B / Soul",       "emoji": "💜", "description": "Soulful, smooth, groovy"},
            {"id": "phonk",     "name": "Phonk",            "emoji": "💀", "description": "Memphis rap, distorted 808"},
            {"id": "ambient",   "name": "Ambient",          "emoji": "🌊", "description": "Atmospheric, dreamy pads"},
        ]
    }


@app.post("/api/convert")
async def convert_beat(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    style: str = Form(...),
    intensity: float = Form(0.7),
):
    if style not in VALID_STYLES:
        raise HTTPException(400, f"Invalid style. Choose from: {', '.join(VALID_STYLES)}")

    if not (0.0 <= intensity <= 1.0):
        raise HTTPException(400, "Intensity must be between 0.0 and 1.0")

    allowed = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported file type: {suffix}. Allowed: {', '.join(allowed)}")

    job_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{job_id}{suffix}"
    output_path = OUTPUT_DIR / f"{job_id}_{style}.wav"

    async with aiofiles.open(input_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            converter.convert,
            str(input_path),
            str(output_path),
            style,
            intensity,
        )
    except Exception as e:
        background_tasks.add_task(cleanup_file, str(input_path))
        raise HTTPException(500, f"Processing failed: {str(e)}")

    background_tasks.add_task(cleanup_file, str(input_path))

    return JSONResponse({
        "job_id": job_id,
        "style": style,
        "download_url": f"/api/download/{job_id}_{style}.wav",
        "info": info,
    })


@app.get("/api/download/{filename}")
async def download_file(filename: str, background_tasks: BackgroundTasks):
    # Prevent path traversal
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    background_tasks.add_task(cleanup_file, str(file_path))
    return FileResponse(
        str(file_path),
        media_type="audio/wav",
        filename=safe_name,
    )


# Serve frontend
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
else:
    frontend_public = Path(__file__).parent.parent / "frontend" / "public"
    if frontend_public.exists():
        app.mount("/", StaticFiles(directory=str(frontend_public), html=True), name="static")
