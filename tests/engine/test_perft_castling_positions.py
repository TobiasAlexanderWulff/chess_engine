from __future__ import annotations

import pytest

from src.engine.board import Board
from src.engine.perft import perft


# Kiwipete (castling, EP, promotions rich position)
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (1, 48),
        (2, 2039),
        (3, 97862),
    ],
)
def test_kiwipete_perft_shallow(depth: int, expected: int) -> None:
    b = Board.from_fen(KIWIPETE)
    assert perft(b, depth) == expected


@pytest.mark.slow
def test_kiwipete_perft_depth3() -> None:
    b = Board.from_fen(KIWIPETE)
    assert perft(b, 3) == 97862
