from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def _is_same_move(a, b) -> bool:
    return a.from_sq == b.from_sq and a.to_sq == b.to_sq and a.promotion == b.promotion


def test_nmp_guard_in_pawn_endgame_returns_legal_move() -> None:
    # Pawn-only endgame (zugzwang-prone). NMP is guarded and should not trigger.
    # Position: White to move, only kings and pawns on board.
    fen = "8/8/8/8/4k3/8/4P3/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=3)
    assert res.best_move is not None
    legal = game.legal_moves()
    assert any(_is_same_move(res.best_move, m) for m in legal)


def test_nmp_disabled_while_in_check_returns_legal_evasion() -> None:
    # When in check, NMP must not run; ensure a legal evasion is selected.
    fen = "4k3/8/8/8/8/8/8/4K2r w - - 0 1"
    game = Game.from_fen(fen)
    assert game.in_check() is True

    service = SearchService()
    res = service.search(game, depth=3)
    assert res.best_move is not None
    game2 = Game.from_fen(fen)
    game2.apply_move(res.best_move)
    assert game2.in_check() is False
