from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .board import Board
from .move import Move


@dataclass
class Game:
    """Game wrapper around a board with helper operations.

    Responsibility: track board state, expose legal moves, apply moves.
    """

    board: Board
    move_stack: List[Move] = field(default_factory=list)
    repetition: Dict[int, int] = field(default_factory=dict)

    @classmethod
    def new(cls) -> "Game":
        return cls(board=Board.startpos())

    @classmethod
    def from_fen(cls, fen: str) -> "Game":
        return cls(board=Board.from_fen(fen))

    def to_fen(self) -> str:
        return self.board.to_fen()

    def __post_init__(self) -> None:
        # Seed repetition with current position
        h = getattr(self.board, "zobrist_hash", None)
        if h is not None:
            self.repetition[h] = self.repetition.get(h, 0) + 1

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
        # Update repetition with new hash
        h = self.board.zobrist_hash
        self.repetition[h] = self.repetition.get(h, 0) + 1

    def undo_move(self) -> None:
        if not self.move_stack:
            raise ValueError("no moves to undo")
        # Decrement count for current position
        curr = self.board.zobrist_hash
        if curr in self.repetition:
            self.repetition[curr] -= 1
            if self.repetition[curr] <= 0:
                del self.repetition[curr]
        last = self.move_stack.pop()
        self.board.unmake_move(last)

    # --- State flags for protocol ---
    def in_check(self) -> bool:
        return self.board.in_check()

    def checkmate(self) -> bool:
        return (not self.board.has_legal_moves()) and self.board.in_check()

    def stalemate(self) -> bool:
        return (not self.board.has_legal_moves()) and (not self.board.in_check())

    def is_draw(self) -> bool:
        # Draw by 50-move rule, stalemate, or threefold repetition
        if self.board.halfmove_clock >= 100:
            return True
        if self.stalemate():
            return True
        count = self.repetition.get(self.board.zobrist_hash, 0)
        return count >= 3

    def move_history_uci(self) -> List[str]:
        return [m.to_uci() for m in self.move_stack]
