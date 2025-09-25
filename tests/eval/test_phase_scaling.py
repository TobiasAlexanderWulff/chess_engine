from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_king_centralization_better_in_endgame_than_middlegame() -> None:
    # Endgame: king centralized should be better than corner
    fen_end_center = "4k3/8/8/8/4K3/8/8/8 w - - 0 1"
    fen_end_corner = "4k3/8/8/8/8/8/8/K7 w - - 0 1"
    g_ec = Game.from_fen(fen_end_center)
    g_ea = Game.from_fen(fen_end_corner)
    sc_ec = evaluate(g_ec.board)
    sc_ea = evaluate(g_ea.board)
    assert sc_ec > sc_ea

    # Middlegame-ish: add heavy pieces for both sides, keep material equal.
    # Black: rooks a8/h8, queen d8, king e8. White: rooks a1/h1, queen d1.
    # Centralized white king on e4 should be worse than corner king on c1.
    fen_mid_center = "r2qk2r/8/8/8/4K3/8/8/R2Q3R w - - 0 1"
    fen_mid_corner = "r2qk2r/8/8/8/8/8/8/R1KQ3R w - - 0 1"
    g_mc = Game.from_fen(fen_mid_center)
    g_ma = Game.from_fen(fen_mid_corner)
    sc_mc = evaluate(g_mc.board)
    sc_ma = evaluate(g_ma.board)
    assert sc_mc < sc_ma
