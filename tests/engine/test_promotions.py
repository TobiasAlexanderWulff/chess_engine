from __future__ import annotations

from src.engine.board import Board


def _uci_set(moves):
    return set(m.to_uci() for m in moves)


def test_white_pawn_push_promotions() -> None:
    # White pawn on e7 can promote to e8 (ensure e8 is empty)
    fen = "k7/4P3/8/8/8/8/8/4K3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = b.generate_legal_moves()
    assert _uci_set(ms) >= {"e7e8q", "e7e8r", "e7e8b", "e7e8n"}


def test_white_pawn_capture_promotion() -> None:
    # White pawn on e7 capturing d8 promotes
    fen = "3rk3/4P3/8/8/8/8/8/4K3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = b.generate_legal_moves()
    assert _uci_set(ms) >= {"e7d8q", "e7d8r", "e7d8b", "e7d8n"}


def test_black_pawn_push_promotions() -> None:
    # Black pawn on d2 can promote to d1
    fen = "4k3/8/8/8/8/8/3p4/4K3 b - - 0 1"
    b = Board.from_fen(fen)
    ms = b.generate_legal_moves()
    assert _uci_set(ms) >= {"d2d1q", "d2d1r", "d2d1b", "d2d1n"}
