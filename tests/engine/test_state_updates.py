from __future__ import annotations

from src.engine.board import Board
from src.engine.move import Move


def _find(b: Board, uci: str) -> Move:
    return next(m for m in b.generate_legal_moves() if m.to_uci() == uci)


def test_halfmove_and_fullmove_counters_and_ep_clearing() -> None:
    b = Board.startpos()
    assert b.halfmove_clock == 0 and b.fullmove_number == 1

    # e2e4: pawn move resets halfmove, sets ep to e3, side -> black
    b.make_move(_find(b, "e2e4"))
    assert b.halfmove_clock == 0
    assert b.side_to_move == "b"
    assert " e3 " in b.to_fen()
    assert b.fullmove_number == 1  # increments after black moves

    # g8f6: knight move increments halfmove, clears ep, side -> white, fullmove -> 2
    b.make_move(_find(b, "g8f6"))
    assert b.halfmove_clock == 1
    assert b.side_to_move == "w"
    assert " - " in b.to_fen()  # ep cleared
    assert b.fullmove_number == 2

    # e4e5: pawn move resets halfmove
    b.make_move(_find(b, "e4e5"))
    assert b.halfmove_clock == 0


def test_castling_rights_update_on_king_and_rook_moves_and_captures() -> None:
    # Open-castling position
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)

    # White rook moves h1h2: remove white 'K' right only
    b.make_move(_find(b, "h1h2"))
    assert "K" not in b.castling and ("Q" in b.castling)

    # Black rook captures a1: removes black 'q' (moved from a8) and white 'Q' (captured on a1)
    b.make_move(_find(b, "a8a1"))
    assert "q" not in b.castling
    assert "Q" not in b.castling

    # Move white king: remove remaining white castling rights entirely
    # First, make a quiet move for white king if legal (e1e2)
    wking_move = _find(b, "e1e2")
    b.make_move(wking_move)
    assert ("K" not in b.castling) and ("Q" not in b.castling)
