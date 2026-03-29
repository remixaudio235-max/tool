from __future__ import annotations

from dataclasses import dataclass, field

from app.models.common import SerializableModel


@dataclass(slots=True)
class StylePreset(SerializableModel):
    name: str
    tempo_range: tuple[int, int]
    feel: str
    drum_groove_templates: list[str] = field(default_factory=list)
    fill_templates: list[str] = field(default_factory=list)
    bass_movement_rules: list[str] = field(default_factory=list)
    comping_patterns: list[str] = field(default_factory=list)
    instrumentation_layers: list[str] = field(default_factory=list)
    transition_rules: list[str] = field(default_factory=list)
    intro_rules: list[str] = field(default_factory=list)
    outro_cadence_rules: list[str] = field(default_factory=list)
    solo_density_guidelines: dict[str, str] = field(default_factory=dict)
