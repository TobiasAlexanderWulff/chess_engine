from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .board import Board
from .move import Move


@dataclass
class Game:
    """Game wrapper around a board with helper operations.

    Responsibility: track board state, expose legal moves, apply moves.
    """

    board: Board
    move_stack: List[Move] = field(default_factory=list)

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
        # Validate legality
        legal = self.board.generate_legal_moves()
        if not any(
            (m.from_sq == move.from_sq and m.to_sq == move.to_sq and m.promotion == move.promotion)
            for m in legal
        ):
            raise ValueError("illegal move")
        # Make move in-place and record for undo
        self.board.make_move(move)
        self.move_stack.append(move)

    def undo_move(self) -> None:
        if not self.move_stack:
            raise ValueError("no moves to undo")
        last = self.move_stack.pop()
        self.board.unmake_move(last)
