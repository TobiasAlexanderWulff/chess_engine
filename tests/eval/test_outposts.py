from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_white_knight_outpost_supported_and_not_attacked_scores_higher() -> None:
    # White knight on d6 supported by pawns c5/e5, no black pawns that can attack d6
    fen_outpost = "4k3/8/3N4/2P1P3/8/8/8/4K3 w - - 0 1"
    # Add a black pawn on e7, which can attack d6, breaking the outpost
    fen_attacked = "4k3/4p3/3N4/2P1P3/8/8/8/4K3 w - - 0 1"
    g_o = Game.from_fen(fen_outpost)
    g_a = Game.from_fen(fen_attacked)
    sc_o = evaluate(g_o.board)
    sc_a = evaluate(g_a.board)
    assert sc_o > sc_a
