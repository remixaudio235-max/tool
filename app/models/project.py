from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models.ai_suggestion import AISuggestion
from app.models.arrangement_block import ArrangementBlock
from app.models.chord import ChordEvent
from app.models.phrase import Phrase
from app.models.reference_sample import ReferenceSample
from app.models.section import Section
from app.models.stem import StemSet


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Project:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Untitled Project"
    source_audio_path: str = ""
    source_audio_name: str = ""
    sample_rate: int = 0
    duration_sec: float = 0.0
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    bpm_detected: float | None = None
    bpm_user: float | None = None
    tempo_confidence: float = 0.0

    downbeat_offset_sec: float = 0.0
    beat_positions_sec: list[float] = field(default_factory=list)
    bar_positions_sec: list[float] = field(default_factory=list)
    bar_grid_confidence: float = 0.0

    key_detected: str | None = None
    key_user: str | None = None
    key_confidence: float = 0.0

    chord_events: list[ChordEvent] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    stems: StemSet = field(default_factory=StemSet)
    arrangement_blocks: list[ArrangementBlock] = field(default_factory=list)
    reference_samples: list[ReferenceSample] = field(default_factory=list)
    phrases: list[Phrase] = field(default_factory=list)
    ai_suggestions: list[AISuggestion] = field(default_factory=list)
    style_preset_name: str = "Bolero VN"
    user_notes: str = ""
    learning_tags: list[str] = field(default_factory=list)
    export_settings: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_bpm(self) -> float | None:
        return self.bpm_user or self.bpm_detected

    @classmethod
    def from_source(cls, file_path: str, sample_rate: int, duration_sec: float) -> "Project":
        path = Path(file_path)
        return cls(
            name=path.stem,
            source_audio_path=str(path),
            source_audio_name=path.name,
            sample_rate=sample_rate,
            duration_sec=duration_sec,
        )

    def mark_updated(self) -> None:
        self.updated_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "chord_events": [x.to_dict() for x in self.chord_events],
            "sections": [x.to_dict() for x in self.sections],
            "stems": self.stems.to_dict(),
            "arrangement_blocks": [x.to_dict() for x in self.arrangement_blocks],
            "reference_samples": [x.to_dict() for x in self.reference_samples],
            "phrases": [x.to_dict() for x in self.phrases],
            "ai_suggestions": [x.to_dict() for x in self.ai_suggestions],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Project":
        data = dict(payload)
        data["chord_events"] = [ChordEvent.from_dict(x) for x in data.get("chord_events", [])]
        data["sections"] = [Section.from_dict(x) for x in data.get("sections", [])]
        data["stems"] = StemSet.from_dict(data.get("stems", {}))
        data["arrangement_blocks"] = [
            ArrangementBlock.from_dict(x) for x in data.get("arrangement_blocks", [])
        ]
        data["reference_samples"] = [
            ReferenceSample.from_dict(x) for x in data.get("reference_samples", [])
        ]
        data["phrases"] = [Phrase.from_dict(x) for x in data.get("phrases", [])]
        data["ai_suggestions"] = [
            AISuggestion.from_dict(x) for x in data.get("ai_suggestions", [])
        ]
        return cls(**data)
