from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class ChordEvent(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    start_bar: int = 1
    end_bar: int = 1
    chord_name: str = "N.C."
    confidence: float = 0.0
    source: str = "detected"
    notes: str = ""
