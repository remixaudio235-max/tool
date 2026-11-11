from __future__ import annotations


def format_seconds(value: float) -> str:
    minutes = int(value // 60)
    seconds = int(value % 60)
    return f"{minutes:02d}:{seconds:02d}"
