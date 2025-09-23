from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .board import Board
from .move import Move


@dataclass
class Game:
    """Game wrapper around a board with helper operations.

    Responsibility: track board state, expose legal moves, apply moves.
    """

    board: Board

    @classmethod
    def new(cls) -> "Game":
        return cls(board=Board.startpos())

    @classmethod
    def from_fen(cls, fen: str) -> "Game":
        return cls(board=Board.from_fen(fen))

    def to_fen(self) -> str:
        return self.board.to_fen()

    def legal_moves(self) -> List[Move]:
        return self.board.generate_legal_moves()

    def apply_move(self, move: Move) -> None:
        # TODO: Update board with move (Plan 3)
        self.board = self.board.apply(move)
