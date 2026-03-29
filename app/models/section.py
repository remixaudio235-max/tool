from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class Section(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Section"
    role: str = "verse"
    start_time_sec: float = 0.0
    end_time_sec: float = 0.0
    start_bar: int = 1
    end_bar: int = 1
    confidence: float = 0.0
    locked: bool = False
    notes: str = ""
