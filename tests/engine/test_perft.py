from __future__ import annotations

from src.engine.board import Board, STARTPOS_FEN
from src.engine.perft import perft


def test_perft_startpos_depths_1_3() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    assert perft(b, 1) == 20
    assert perft(b, 2) == 400
    assert perft(b, 3) == 8902


def test_perft_kiwipete_depth_2() -> None:
    # Classic Kiwipete position
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)
    assert perft(b, 1) == 48
    assert perft(b, 2) == 2039
