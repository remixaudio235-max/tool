from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class ArrangementBlock(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    block_type: str = "Main A"
    start_bar: int = 1
    end_bar: int = 4
    source_section_ids: list[str] = field(default_factory=list)
    intensity: str = "medium"
    instrumentation: list[str] = field(default_factory=list)
    phrase_ids: list[str] = field(default_factory=list)
    enabled: bool = True
    notes: str = ""
