from __future__ import annotations

from app.models.phrase import Phrase


class PhraseExtractor:
    def extract(self) -> list[Phrase]:
        return [Phrase(name="Detected phrase", start_bar=1, end_bar=2, confidence=0.4)]
