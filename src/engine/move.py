from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


PROMOTION_PIECES = {"q", "r", "b", "n"}


@dataclass(frozen=True)
class Move:
    """Engine-internal move type.

    - Squares are 0..63 (a1 = 0, h8 = 63) or use algebraic via helpers.
    - Promotion uses lowercase piece letter (q, r, b, n) when present.
    """

    from_sq: int
    to_sq: int
    promotion: Optional[str] = None

    def to_uci(self) -> str:
        return square_to_str(self.from_sq) + square_to_str(self.to_sq) + (self.promotion or "")


def parse_uci(uci: str) -> Move:
    """Parse UCI move string like 'e2e4' or 'e7e8q'."""
    if len(uci) not in (4, 5):
        raise ValueError(f"invalid UCI move length: {uci!r}")
    from_sq = str_to_square(uci[0:2])
    to_sq = str_to_square(uci[2:4])
    promo: Optional[str] = None
    if len(uci) == 5:
        promo = uci[4].lower()
        if promo not in PROMOTION_PIECES:
            raise ValueError(f"invalid promotion piece: {promo!r}")
    return Move(from_sq, to_sq, promo)


def str_to_square(s: str) -> int:
    if len(s) != 2 or s[0] < "a" or s[0] > "h" or s[1] < "1" or s[1] > "8":
        raise ValueError(f"invalid square: {s!r}")
    file = ord(s[0]) - ord("a")
    rank = int(s[1]) - 1
    return rank * 8 + file


def square_to_str(idx: int) -> str:
    if idx < 0 or idx > 63:
        raise ValueError(f"invalid square index: {idx}")
    file = idx % 8
    rank = idx // 8
    return chr(ord("a") + file) + str(rank + 1)
