from __future__ import annotations

from app.arranger.style_resolver import StyleResolver
from app.models.arrangement_block import ArrangementBlock
from app.models.project import Project


class RuleEngine:
    def __init__(self) -> None:
        self.style_resolver = StyleResolver()

    def generate(self, project: Project, density: str = "medium") -> list[ArrangementBlock]:
        style = self.style_resolver.resolve(project.style_preset_name)
        blocks: list[ArrangementBlock] = [ArrangementBlock(block_type="Intro", start_bar=1, end_bar=4)]
        for section in project.sections:
            intensity = style["chorus_intensity"] if section.role == "chorus" else style["verse_intensity"]
            if density == "full":
                intensity = "full"
            blocks.append(
                ArrangementBlock(
                    block_type="Main B" if section.role == "chorus" else "Main A",
                    start_bar=max(section.start_bar, 1),
                    end_bar=max(section.end_bar, section.start_bar),
                    source_section_ids=[section.id],
                    intensity=intensity,
                    instrumentation=style["instruments"],
                )
            )
        blocks.append(ArrangementBlock(block_type="Outro", start_bar=max(len(project.bar_positions_sec) - 3, 1), end_bar=max(len(project.bar_positions_sec), 4)))
        return blocks
