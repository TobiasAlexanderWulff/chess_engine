from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_white_rook_on_seventh_rank_is_rewarded() -> None:
    # White rook on a7 vs a6; other pieces: black king a8, white king h1
    fen_seventh = "k7/R7/8/8/8/8/8/7K w - - 0 1"
    fen_not = "k7/8/R7/8/8/8/8/7K w - - 0 1"
    g7 = Game.from_fen(fen_seventh)
    g6 = Game.from_fen(fen_not)
    sc7 = evaluate(g7.board)
    sc6 = evaluate(g6.board)
    assert sc7 > sc6


def test_black_rook_on_seventh_rank_is_penalized_for_white() -> None:
    # Black rook on a2 vs a3; other pieces: black king a8, white king h1
    fen_a2 = "k7/8/8/8/8/8/r7/7K w - - 0 1"
    fen_a3 = "k7/8/8/8/8/r7/8/7K w - - 0 1"
    g2 = Game.from_fen(fen_a2)
    g3 = Game.from_fen(fen_a3)
    sc2 = evaluate(g2.board)
    sc3 = evaluate(g3.board)
    # With black rook on seventh (a2), white's eval should be lower
    assert sc2 < sc3
