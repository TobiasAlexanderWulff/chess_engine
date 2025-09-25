from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_bishop_mobility_open_vs_blocked() -> None:
    # Open diagonal for white bishop vs blocked by own pawn; pawns mirrored to balance
    fen_open = "4k3/8/3p4/8/8/3P4/8/2B1K3 w - - 0 1"
    fen_blocked = "4k3/3p4/8/8/8/8/3P4/2B1K3 w - - 0 1"
    g_open = Game.from_fen(fen_open)
    g_blocked = Game.from_fen(fen_blocked)

    sc_open = evaluate(g_open.board)
    sc_blocked = evaluate(g_blocked.board)
    assert sc_open > sc_blocked


def test_king_pawn_shield_increases_score() -> None:
    # White king with a pawn shield vs none for black
    fen = "6k1/8/8/8/8/8/5PPP/6K1 w - - 0 1"
    g = Game.from_fen(fen)
    sc = evaluate(g.board)
    # Mirror and swap colors: black gets shield, white none
    fen_m = "6k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"
    g_m = Game.from_fen(fen_m)
    sc_m = evaluate(g_m.board)
    assert sc > 0
    assert sc_m < 0
