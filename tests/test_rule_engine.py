from app.arranger.rule_engine import RuleEngine
from app.models.project import Project
from app.models.section import Section


def test_rule_engine_generates_blocks() -> None:
    p = Project(style_preset_name="Bolero VN")
    p.sections = [Section(start_bar=1, end_bar=8, role="verse")]
    p.bar_positions_sec = [float(i) for i in range(16)]
    blocks = RuleEngine().generate(p)
    assert any(b.block_type == "Intro" for b in blocks)
    assert any(b.block_type == "Outro" for b in blocks)
