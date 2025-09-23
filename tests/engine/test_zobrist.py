from __future__ import annotations

from src.engine.board import Board, STARTPOS_FEN
from src.engine.zobrist import compute_hash_from_scratch


def test_zobrist_deterministic_same_position() -> None:
    b1 = Board.from_fen(STARTPOS_FEN)
    b2 = Board.from_fen(STARTPOS_FEN)
    h1 = compute_hash_from_scratch(b1)
    h2 = compute_hash_from_scratch(b2)
    assert h1 == h2

    # Round-trip FEN keeps same hash
    b3 = Board.from_fen(b1.to_fen())
    h3 = compute_hash_from_scratch(b3)
    assert h1 == h3


def test_zobrist_side_to_move_bit_differs() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    h_w = compute_hash_from_scratch(b)
    b.side_to_move = "b"
    h_b = compute_hash_from_scratch(b)
    assert h_w != h_b


def test_zobrist_castling_affects_hash() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    h_all = compute_hash_from_scratch(b)
    b.castling = ""  # remove all rights
    h_none = compute_hash_from_scratch(b)
    assert h_all != h_none


def test_zobrist_en_passant_affects_hash() -> None:
    fen_with_ep = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    b = Board.from_fen(fen_with_ep)
    h_ep = compute_hash_from_scratch(b)
    b.ep_square = None
    h_no_ep = compute_hash_from_scratch(b)
    assert h_ep != h_no_ep
