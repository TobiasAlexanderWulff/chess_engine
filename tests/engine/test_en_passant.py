from __future__ import annotations

from src.engine.board import Board, WP, BP
from src.engine.move import Move, str_to_square


def test_white_en_passant_generation_and_apply() -> None:
    # Black just played e7e5 → ep target e6; white pawn on d5 can capture e6 ep
    fen = "4k3/8/8/3Pp3/8/8/8/4K3 w - e6 0 1"
    b = Board.from_fen(fen)
    moves = {m.to_uci() for m in b.generate_legal_moves()}
    assert "d5e6" in moves

    # Simulate application on bitboards: white pawn moves to e6, black pawn on e5 removed
    mv = Move(b"d5".decode() if False else 27, 28)  # placeholder to keep type; not used
    # Find the actual Move object
    mv = next(m for m in b.generate_legal_moves() if m.to_uci() == "d5e6")
    new_bb = b._apply_pseudo_to_bb(mv)
    assert new_bb is not None
    e6 = str_to_square("e6")
    d5 = str_to_square("d5")
    e5 = str_to_square("e5")
    assert (new_bb[WP] >> e6) & 1
    assert ((new_bb[WP] >> d5) & 1) == 0
    assert ((new_bb[BP] >> e5) & 1) == 0


def test_black_en_passant_generation_and_apply() -> None:
    # White just played e2e4 → ep target e3; black pawn on d4 can capture e3 ep
    fen = "4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1"
    b = Board.from_fen(fen)
    moves = {m.to_uci() for m in b.generate_legal_moves()}
    assert "d4e3" in moves

    mv = next(m for m in b.generate_legal_moves() if m.to_uci() == "d4e3")
    new_bb = b._apply_pseudo_to_bb(mv)
    assert new_bb is not None
    d4 = str_to_square("d4")
    e3 = str_to_square("e3")
    e4 = str_to_square("e4")
    assert (new_bb[BP] >> e3) & 1
    assert ((new_bb[BP] >> d4) & 1) == 0
    assert ((new_bb[WP] >> e4) & 1) == 0
