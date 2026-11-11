from __future__ import annotations

from app.arranger.rule_engine import RuleEngine
from app.models.project import Project


class ArrangementBuilder:
    def __init__(self) -> None:
        self.engine = RuleEngine()

    def build(self, project: Project, density: str = "medium") -> Project:
        project.arrangement_blocks = self.engine.generate(project, density=density)
        project.mark_updated()
        return project
