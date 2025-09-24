from __future__ import annotations

import pytest

from src.engine.board import Board, STARTPOS_FEN, WR
from src.engine.move import Move, str_to_square


def test_apply_returns_new_board_and_does_not_mutate() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    mv = Move(str_to_square("e2"), str_to_square("e4"))

    # Sanity: move must be legal
    legal = {m.to_uci() for m in b.generate_legal_moves()}
    assert mv.to_uci() in legal

    b2 = b.apply(mv)

    # Original board unchanged
    assert b.to_fen() == STARTPOS_FEN

    # New board reflects move; halfmove reset, ep square set, side toggled
    expected_fen_prefix = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    assert b2.to_fen() == expected_fen_prefix


def test_apply_rejects_illegal_move() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    # e2e5 is illegal from the start position
    bad = Move(str_to_square("e2"), str_to_square("e5"))
    with pytest.raises(ValueError):
        _ = b.apply(bad)


def test_apply_handles_castling_rook_motion() -> None:
    # Position with castling allowed for both sides; test white king-side castle
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)
    mv = next(m for m in b.generate_legal_moves() if m.to_uci() == "e1g1")
    b2 = b.apply(mv)

    f1 = str_to_square("f1")
    h1 = str_to_square("h1")
    # Rook moved from h1 to f1 on the new board only
    assert (b2.bb[WR] >> f1) & 1
    assert ((b2.bb[WR] >> h1) & 1) == 0
    # Original unchanged
    assert ((b.bb[WR] >> h1) & 1) == 1
