from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class Phrase(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Phrase"
    start_bar: int = 1
    end_bar: int = 1
    confidence: float = 0.0
    source: str = "detected"
    enabled: bool = True
