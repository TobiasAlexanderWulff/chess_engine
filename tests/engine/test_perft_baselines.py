from __future__ import annotations

import pytest

from src.engine.board import Board, STARTPOS_FEN
from src.engine.perft import perft


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (1, 20),
        (2, 400),
        (3, 8902),
    ],
)
def test_startpos_perft(depth: int, expected: int) -> None:
    b = Board.from_fen(STARTPOS_FEN)
    assert perft(b, depth) == expected
