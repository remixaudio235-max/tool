"""Common dataclass helpers for serialization."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(slots=True)
class SerializableModel:
    """Base model with typed dict serialization helpers."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]):
        return cls(**payload)
