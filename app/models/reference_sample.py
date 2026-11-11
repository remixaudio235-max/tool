from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class ReferenceSample(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    file_path: str = ""
    display_name: str = ""
    tags: list[str] = field(default_factory=list)
    bpm: float | None = None
    key: str | None = None
    duration_sec: float = 0.0
    user_rating: int = 0
    notes: str = ""
    accepted_count: int = 0
    rejected_count: int = 0
