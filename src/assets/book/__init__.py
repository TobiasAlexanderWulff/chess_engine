from __future__ import annotations

from typing import Optional

from .json_book import JSONBook
from .polyglot import PolyglotBook


def open_book(path: Optional[str]):
    if not path:
        return None
    lower = path.lower()
    if lower.endswith(".json"):
        return JSONBook(path)
    if lower.endswith(".bin"):
        return PolyglotBook(path)
    # Try JSON, then Polyglot
    try:
        return JSONBook(path)
    except Exception:
        return PolyglotBook(path)
