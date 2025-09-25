from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_bishop_pair_bonus_positive() -> None:
    # Endgame: compare BB vs BN for white; material is +10cp for BB already, bonus should add
    fen_bb = "4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1"
    fen_bn = "4k3/8/8/8/8/8/8/2B1KN2 w - - 0 1"
    g_bb = Game.from_fen(fen_bb)
    g_bn = Game.from_fen(fen_bn)
    sc_bb = evaluate(g_bb.board)
    sc_bn = evaluate(g_bn.board)
    assert sc_bb > sc_bn


def test_bishop_pair_scaled_higher_in_endgame_than_middlegame() -> None:
    # Middlegame: both sides have heavy pieces; white has BB vs BN
    fen_bb_mg = "r2qk2r/8/8/8/8/8/8/R1BQKB1R w - - 0 1"
    fen_bn_mg = "r2qk2r/8/8/8/8/8/8/R1BQKN1R w - - 0 1"
    g_bb_mg = Game.from_fen(fen_bb_mg)
    g_bn_mg = Game.from_fen(fen_bn_mg)
    d_mg = evaluate(g_bb_mg.board) - evaluate(g_bn_mg.board)

    # Endgame: remove heavy pieces; same BB vs BN
    fen_bb_eg = "4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1"
    fen_bn_eg = "4k3/8/8/8/8/8/8/2B1KN2 w - - 0 1"
    g_bb_eg = Game.from_fen(fen_bb_eg)
    g_bn_eg = Game.from_fen(fen_bn_eg)
    d_eg = evaluate(g_bb_eg.board) - evaluate(g_bn_eg.board)

    assert d_eg > d_mg
