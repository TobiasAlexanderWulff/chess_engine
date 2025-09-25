from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def test_in_check_best_move_resolves_check_at_depth_1() -> None:
    # White to move, in check from a rook on h1
    fen = "4k3/8/8/8/8/8/8/4K2r w - - 0 1"
    game = Game.from_fen(fen)
    assert game.in_check() is True

    service = SearchService()
    res = service.search(game, depth=1)
    assert res.best_move is not None

    # Apply on a fresh copy to validate check is resolved
    game2 = Game.from_fen(fen)
    game2.apply_move(res.best_move)
    assert game2.in_check() is False
