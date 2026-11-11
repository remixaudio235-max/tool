from __future__ import annotations

from pathlib import Path

from app.models.project import Project
from app.utils.json_io import read_json, write_json


class ProjectService:
    def save_project(self, project: Project, path: Path) -> None:
        project.mark_updated()
        write_json(path, project.to_dict())

    def load_project(self, path: Path) -> Project:
        return Project.from_dict(read_json(path))
