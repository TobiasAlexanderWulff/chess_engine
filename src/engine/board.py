from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .move import Move


STARTPOS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass
class Board:
    """Minimal placeholder for board state and FEN I/O.

    This is a stub; legality and move generation are implemented in later plans.
    """

    fen: str = STARTPOS_FEN

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        # TODO: Implement proper FEN parsing/validation (Plan 2)
        if not fen or not isinstance(fen, str):
            raise ValueError("FEN must be a non-empty string")
        return cls(fen=fen)

    def to_fen(self) -> str:
        # TODO: Generate FEN from internal state (Plan 2)
        return self.fen

    def generate_legal_moves(self) -> List[Move]:
        # TODO: Implement legal move generation (Plan 3)
        return []

    def apply(self, move: Move) -> "Board":
        # TODO: Apply move to internal state and return new board (Plan 3)
        raise NotImplementedError("move application not implemented yet")
