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

app = FastAPI(title="NhacSong Beat Converter", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = BeatConverter()

VALID_STYLES = [
    "bolero", "rumba", "chachacha", "slowrock", "tango",
    "disco", "valse", "fox", "twist", "ballade",
]

VALID_BRANDS = ["auto", "roland", "yamaha"]


def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass


@app.get("/api/styles")
async def get_styles():
    return {
        "styles": [
            {
                "id": "bolero",
                "name": "Bolero",
                "bpm": 72,
                "time_sig": "4/4",
                "mood": "Trữ tình, buồn",
                "emoji": "💙",
                "description": "Chậm rãi, sâu lắng — điệu nhạc trữ tình Việt Nam",
            },
            {
                "id": "rumba",
                "name": "Rumba",
                "bpm": 108,
                "time_sig": "4/4",
                "mood": "Lãng mạn, nhẹ nhàng",
                "emoji": "🌹",
                "description": "Latin groove nhẹ nhàng, nhịp nhàng",
            },
            {
                "id": "chachacha",
                "name": "Cha-cha-cha",
                "bpm": 124,
                "time_sig": "4/4",
                "mood": "Vui tươi, sôi động",
                "emoji": "💃",
                "description": "Nhịp vui tươi, staccato, dễ nhảy",
            },
            {
                "id": "slowrock",
                "name": "Slow Rock",
                "bpm": 76,
                "time_sig": "4/4",
                "mood": "Cảm xúc, mạnh mẽ",
                "emoji": "🎸",
                "description": "Ballad rock, organ dày, cảm xúc sâu",
            },
            {
                "id": "tango",
                "name": "Tango",
                "bpm": 122,
                "time_sig": "4/4",
                "mood": "Kịch tính, mạnh mẽ",
                "emoji": "🌊",
                "description": "Nhịp mạnh, kịch tính, staccato sắc nét",
            },
            {
                "id": "disco",
                "name": "Disco",
                "bpm": 122,
                "time_sig": "4/4",
                "mood": "Sôi động, vui nhộn",
                "emoji": "🪩",
                "description": "Beat pumping, funky organ, four-on-the-floor",
            },
            {
                "id": "valse",
                "name": "Valse",
                "bpm": 172,
                "time_sig": "3/4",
                "mood": "Lãng mạn, nhẹ nhàng",
                "emoji": "🌸",
                "description": "Nhịp 3/4 lả lướt, organ ấm, ballroom",
            },
            {
                "id": "fox",
                "name": "Fox Trot",
                "bpm": 135,
                "time_sig": "4/4",
                "mood": "Duyên dáng, nhẹ nhàng",
                "emoji": "🦊",
                "description": "Nhẹ nhàng, duyên dáng, organ mượt",
            },
            {
                "id": "twist",
                "name": "Twist",
                "bpm": 130,
                "time_sig": "4/4",
                "mood": "Vui nhộn, retro",
                "emoji": "🕺",
                "description": "Retro fun, organ vintage, bright treble",
            },
            {
                "id": "ballade",
                "name": "Ballade",
                "bpm": 56,
                "time_sig": "4/4",
                "mood": "Sâu lắng, cô đơn",
                "emoji": "🌙",
                "description": "Chậm nhất, reverb lớn, cực kỳ cảm xúc",
            },
        ]
    }


@app.post("/api/convert")
async def convert_beat(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    style: str = Form(...),
    intensity: float = Form(0.7),
    vocal_removal: bool = Form(True),
    vocal_strength: float = Form(0.85),
    organ_brand: str = Form("auto"),
):
    if style not in VALID_STYLES:
        raise HTTPException(400, f"Điệu không hợp lệ. Chọn một trong: {', '.join(VALID_STYLES)}")

    if not (0.0 <= intensity <= 1.0):
        raise HTTPException(400, "Intensity phải từ 0.0 đến 1.0")

    if organ_brand not in VALID_BRANDS:
        raise HTTPException(400, f"Organ brand phải là: {', '.join(VALID_BRANDS)}")

    allowed_ext = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(400, f"Định dạng không được hỗ trợ: {suffix}")

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
            lambda: converter.convert(
                str(input_path),
                str(output_path),
                style=style,
                intensity=intensity,
                vocal_removal=vocal_removal,
                vocal_strength=vocal_strength,
                organ_brand=organ_brand,
            ),
        )
    except Exception as e:
        background_tasks.add_task(cleanup_file, str(input_path))
        raise HTTPException(500, f"Lỗi xử lý: {str(e)}")

    background_tasks.add_task(cleanup_file, str(input_path))

    return JSONResponse({
        "job_id": job_id,
        "style": style,
        "download_url": f"/api/download/{job_id}_{style}.wav",
        "info": info,
    })


@app.get("/api/download/{filename}")
async def download_file(filename: str, background_tasks: BackgroundTasks):
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại")
    background_tasks.add_task(cleanup_file, str(file_path))
    return FileResponse(str(file_path), media_type="audio/wav", filename=safe_name)


# Serve frontend
for _d in [
    Path(__file__).parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "frontend" / "public",
]:
    if _d.exists():
        app.mount("/", StaticFiles(directory=str(_d), html=True), name="static")
        break
