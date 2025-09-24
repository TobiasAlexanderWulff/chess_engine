from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def test_see_prunes_losing_capture_at_shallow_depth() -> None:
    # White bishop on d4 can capture e5 pawn, but black pawn from d6 recaptures.
    # This is a net material loss for White (100 - 330), so SEE should prune it at depth 1.
    fen = "4k3/8/3p4/4p3/3B4/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=1)
    assert res.best_move is not None
    # Ensure engine does not choose the losing capture d4e5
    assert res.best_move.to_uci() != "d4e5"


def test_see_prefers_winning_capture_at_shallow_depth() -> None:
    # White bishop on d4 can capture an unprotected black knight on c5.
    # This is a clear material gain; SEE should allow it and search should pick it at depth 1.
    fen = "4k3/8/8/2n5/3B4/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=1)
    assert res.best_move is not None
    assert res.best_move.to_uci() == "d4c5"
