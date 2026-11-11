from __future__ import annotations

from dataclasses import dataclass, field

from app.models.common import SerializableModel


@dataclass(slots=True)
class StemSet(SerializableModel):
    drums_path: str | None = None
    bass_path: str | None = None
    vocal_path: str | None = None
    music_path: str | None = None
    backend: str = "unavailable"
    status: str = "not_started"
    errors: list[str] = field(default_factory=list)
