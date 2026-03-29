from __future__ import annotations

from pathlib import Path

from app.utils.json_io import read_json, write_json


class LearningMemoryService:
    def append_case(self, db_path: Path, payload: dict) -> None:
        existing = []
        if db_path.exists():
            existing = read_json(db_path).get("cases", [])
        existing.append(payload)
        write_json(db_path, {"cases": existing})
