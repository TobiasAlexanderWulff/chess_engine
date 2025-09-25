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


def test_search_returns_legal_move_at_depth_3_midgame() -> None:
    # Midgame with full castling rights and mixed pieces
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=3)
    assert res.best_move is not None

    legal = game.legal_moves()
    assert any(_is_same_move(res.best_move, m) for m in legal), "best move must be legal"
