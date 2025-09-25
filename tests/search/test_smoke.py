from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def _is_same_move(a, b) -> bool:
    return a.from_sq == b.from_sq and a.to_sq == b.to_sq and a.promotion == b.promotion


def test_search_returns_legal_move_at_depth_3_startpos() -> None:
    game = Game.new()
    service = SearchService()

    res = service.search(game, depth=3)
    assert res.best_move is not None

    legal = game.legal_moves()
    assert any(_is_same_move(res.best_move, m) for m in legal), "best move must be legal"
