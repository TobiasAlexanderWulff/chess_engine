from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_white_passed_pawn_detected_and_bonused() -> None:
    # White pawn on e6 with no black pawns on d/e/f files ahead -> passed
    fen_passed = "4k3/8/4P3/8/8/8/8/4K3 w - - 0 1"
    # Add a black pawn on f7 (ahead on adjacent file) -> not passed
    fen_not = "4k3/5p2/4P3/8/8/8/8/4K3 w - - 0 1"
    gp = Game.from_fen(fen_passed)
    gn = Game.from_fen(fen_not)
    sc_p = evaluate(gp.board)
    sc_n = evaluate(gn.board)
    assert sc_p > sc_n


def test_black_passed_pawn_detected_and_penalized_for_white() -> None:
    # Black pawn on e3 with no white pawns on d/e/f files ahead -> passed for black
    fen_passed = "4k3/8/8/8/8/4p3/8/4K3 w - - 0 1"
    # Add a white pawn on d2 (ahead on adjacent file for black) -> not passed
    fen_not = "4k3/8/8/8/8/4p3/3P4/4K3 w - - 0 1"
    gp = Game.from_fen(fen_passed)
    gn = Game.from_fen(fen_not)
    sc_p = evaluate(gp.board)
    sc_n = evaluate(gn.board)
    assert sc_p < sc_n


def test_passed_pawn_bonus_grows_with_advancement() -> None:
    # Compare white passed pawn on e4 vs e6
    fen_e4 = "4k3/8/8/8/4P3/8/8/4K3 w - - 0 1"
    fen_e6 = "4k3/8/4P3/8/8/8/8/4K3 w - - 0 1"
    g4 = Game.from_fen(fen_e4)
    g6 = Game.from_fen(fen_e6)
    sc4 = evaluate(g4.board)
    sc6 = evaluate(g6.board)
    assert sc6 > sc4
