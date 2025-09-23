from __future__ import annotations

from src.engine.board import Board


def moves_set(b: Board) -> set[str]:
    return {m.to_uci() for m in b.generate_legal_moves()}


def test_rook_basic_moves() -> None:
    # White: rook a1, king e1; Black: king e8. Open a-file and rank 1 except e1.
    fen = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    # Rook from a1 can go to a2 and b1 (at least)
    assert {"a1a2", "a1b1"}.issubset(ms)


def test_bishop_basic_moves() -> None:
    # White bishop c1, kings e1/e8, open diagonals
    fen = "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    # Bishop from c1 can go to b2 and d2
    assert {"c1b2", "c1d2"}.issubset(ms)


def test_queen_basic_moves() -> None:
    # White queen d1, kings e1/e8, open board nearby
    fen = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    assert {"d1d2", "d1c1", "d1c2"}.issubset(ms)


def test_pinned_rook_move_filtered() -> None:
    # White king e1, rook e2; Black rook e8 pins e2 rook. Moving rook off the e-file exposes check.
    fen = "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1"
    # Put black rook on e8 via replacement: place at e8 in FEN: file e=5 → modify rank8
    fen = "4r3/8/8/8/8/8/4R3/4K3 w - - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    assert "e2d2" not in ms and "e2f2" not in ms
    # But moving along the e-file to block (e2e3) should be allowed
    assert "e2e3" in ms
