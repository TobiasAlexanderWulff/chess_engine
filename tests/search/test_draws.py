from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def test_50_move_rule_draw_returns_zero() -> None:
    # Simple K vs K with 50-move counter exceeded
    fen = "8/8/8/8/8/8/8/4K2k w - - 100 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=3)
    assert res.mate_in is None
    assert res.score_cp == 0


def test_threefold_draw_at_root_returns_zero() -> None:
    # Force threefold by seeding repetition counts at root
    fen = "8/8/8/8/8/8/8/4K2k w - - 0 1"
    game = Game.from_fen(fen)
    # Seed repetition: simulate that this exact position has occurred twice already
    h = game.board.zobrist_hash
    game.repetition[h] = 3

    service = SearchService()
    res = service.search(game, depth=2)
    assert res.mate_in is None
    assert res.score_cp == 0
