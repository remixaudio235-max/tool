from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.models.common import SerializableModel


@dataclass(slots=True)
class AISuggestion(SerializableModel):
    id: str = field(default_factory=lambda: str(uuid4()))
    suggestion_type: str = "texture"
    related_block_id: str | None = None
    description: str = ""
    confidence: float = 0.0
    accepted: bool = False
    rejected: bool = False
    editable_payload: dict[str, Any] = field(default_factory=dict)
