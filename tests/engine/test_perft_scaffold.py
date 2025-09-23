from __future__ import annotations

from src.engine.board import Board, STARTPOS_FEN
from src.engine.perft import perft


def test_perft_depth0_is_one() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    assert perft(b, 0) == 1
