from __future__ import annotations

from app.arranger.pattern_library import PATTERNS


class StyleResolver:
    def resolve(self, style_name: str) -> dict:
        return PATTERNS.get(style_name, PATTERNS["Bolero VN"])
