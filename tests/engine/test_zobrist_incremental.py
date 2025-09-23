from __future__ import annotations

from src.engine.board import Board, STARTPOS_FEN, WP, BP
from src.engine.move import str_to_square
from src.engine.zobrist import compute_hash_from_scratch, incremental_hash_update


def _clone_board(b: Board) -> Board:
    # Deep-ish copy sufficient for our tests: bitboards list and simple fields
    return Board(
        bb=list(b.bb),
        side_to_move=b.side_to_move,
        castling=b.castling,
        ep_square=b.ep_square,
        halfmove_clock=b.halfmove_clock,
        fullmove_number=b.fullmove_number,
    )


def test_incremental_equals_full_on_quiet_pawn_push_with_ep() -> None:
    b_before = Board.from_fen(STARTPOS_FEN)
    h_before = compute_hash_from_scratch(b_before)

    # e2e4: move white pawn, set EP target to e3, toggle side
    b_after = _clone_board(b_before)
    e2 = str_to_square("e2")
    e4 = str_to_square("e4")
    e3 = str_to_square("e3")
    # clear e2, set e4 in white pawn bitboard
    b_after.bb[WP] &= ~(1 << e2)
    b_after.bb[WP] |= 1 << e4
    b_after.side_to_move = "b"
    b_after.ep_square = e3

    h_inc = incremental_hash_update(h_before, b_before, b_after)
    h_full = compute_hash_from_scratch(b_after)
    assert h_inc == h_full


def test_incremental_equals_full_on_capture_and_side_toggle() -> None:
    # Minimal position: kings + white pawn e4, black pawn d5
    fen_before = "4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1"
    b_before = Board.from_fen(fen_before)
    h_before = compute_hash_from_scratch(b_before)

    # White captures: e4xd5 (remove BP on d5, move WP e4->d5), side to black
    b_after = _clone_board(b_before)
    e4 = str_to_square("e4")
    d5 = str_to_square("d5")
    b_after.bb[WP] &= ~(1 << e4)
    b_after.bb[WP] |= 1 << d5
    b_after.bb[BP] &= ~(1 << d5)
    b_after.side_to_move = "b"
    b_after.ep_square = None

    h_inc = incremental_hash_update(h_before, b_before, b_after)
    h_full = compute_hash_from_scratch(b_after)
    assert h_inc == h_full


def test_incremental_equals_full_on_castling_rights_change() -> None:
    b_before = Board.from_fen(STARTPOS_FEN)
    h_before = compute_hash_from_scratch(b_before)

    b_after = _clone_board(b_before)
    b_after.castling = ""  # remove all rights

    h_inc = incremental_hash_update(h_before, b_before, b_after)
    h_full = compute_hash_from_scratch(b_after)
    assert h_inc == h_full


def test_incremental_equals_full_on_en_passant_clear() -> None:
    fen_with_ep = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    b_before = Board.from_fen(fen_with_ep)
    h_before = compute_hash_from_scratch(b_before)

    b_after = _clone_board(b_before)
    b_after.ep_square = None

    h_inc = incremental_hash_update(h_before, b_before, b_after)
    h_full = compute_hash_from_scratch(b_after)
    assert h_inc == h_full
