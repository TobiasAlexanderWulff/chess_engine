from __future__ import annotations

from src.engine.board import Board, STARTPOS_FEN
from src.engine.move import Move, str_to_square
from src.engine.zobrist import compute_hash_from_scratch


def test_make_unmake_restores_position() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    h_before = compute_hash_from_scratch(b)
    # e2e4
    mv = Move(str_to_square("e2"), str_to_square("e4"))
    # Ensure move is in generated moves
    gen = {m.to_uci() for m in b.generate_legal_moves()}
    assert mv.to_uci() in gen
    b.make_move(mv)
    # Unmake and compare FEN/hash
    b.unmake_move(mv)
    assert b.to_fen() == STARTPOS_FEN
    assert compute_hash_from_scratch(b) == h_before
