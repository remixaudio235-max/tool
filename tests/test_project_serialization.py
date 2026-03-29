from app.models.project import Project


def test_project_roundtrip() -> None:
    project = Project(name="Demo", bpm_detected=90.0)
    restored = Project.from_dict(project.to_dict())
    assert restored.name == "Demo"
    assert restored.bpm_detected == 90.0
