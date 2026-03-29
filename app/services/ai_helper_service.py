from __future__ import annotations

from app.models.ai_suggestion import AISuggestion


class AIHelperService:
    """Provider interface placeholder. Current implementation returns mock suggestions."""

    def suggest_texture(self, style_name: str) -> list[AISuggestion]:
        return [
            AISuggestion(
                suggestion_type="texture",
                description=f"Try {style_name} warm-pad layer on chorus only.",
                confidence=0.62,
                editable_payload={"target": "chorus", "layer": "warm_pad"},
            )
        ]
