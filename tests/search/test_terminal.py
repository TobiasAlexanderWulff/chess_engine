from __future__ import annotations

from src.engine.game import Game
from src.search.service import SearchService


def test_stalemate_root_returns_draw_and_no_move() -> None:
    # Black to move is stalemated (not in check, no legal moves)
    # Position: Kh6, Qf7 vs kh8 — black to move and stalemated
    fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=2)
    assert game.stalemate() is True
    assert res.best_move is None
    assert res.score_cp == 0
    assert res.mate_in is None


def test_checkmate_root_reports_mate() -> None:
    # Black to move is checkmated (in check, no legal moves)
    # Position: Kh8 vs Qg7, Kg6 — checkmate
    fen = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    res = service.search(game, depth=2)
    assert game.checkmate() is True
    assert res.best_move is None
    # Mate indicated via mate_in (negative means side to move is mated)
    assert res.mate_in is not None and res.mate_in <= 0
    # When mate is reported, cp score should be None
    assert res.score_cp is None
