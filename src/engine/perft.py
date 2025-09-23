from __future__ import annotations

from .board import Board, WP, WQ, WR, WB, WN, WK, BP, BQ, BR, BB, BN, BK
from .move import Move


def perft(board: Board, depth: int) -> int:
    """Compute perft node count for `board` at `depth`.

    Definition:
    - depth == 0 returns 1 (the current node).
    - depth > 0 returns the sum over all legal child positions' perft(depth-1).

    Note: This scaffolding relies on `Board.generate_legal_moves()` which is
    currently a stub; once legal move generation is implemented, results will
    be meaningful. The make/unmake workflow will replace copy-apply if needed.
    """
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if depth == 0:
        return 1

    nodes = 0
    for m in board.generate_legal_moves():
        child = _apply_pseudo_pawn_move(board, m)
        if child is None:
            # Unsupported move type in scaffolding; skip for now.
            continue
        nodes += perft(child, depth - 1)
    return nodes


def _apply_pseudo_pawn_move(board: Board, move: Move) -> Board | None:
    """Return a new Board with the pawn move applied (scaffolding).

    Supports only pawn pushes and captures without promotions or en passant.
    Updates: bb, side_to_move, ep_square (for double pushes), half/fullmove.
    Leaves castling rights unchanged. Returns None for unsupported cases.
    """
    from_sq, to_sq = move.from_sq, move.to_sq
    # Identify moving side: pawn must belong to side_to_move
    is_white = board.side_to_move == "w"
    wpawn = 1 << from_sq
    bpawn = 1 << from_sq
    if is_white:
        if not (board.bb[WP] & wpawn):
            return None
    else:
        if not (board.bb[BP] & bpawn):
            return None

    # Clone board minimal state
    bb = list(board.bb)
    ep_square = None

    # Occupancies
    occ_all = 0
    for b in bb:
        occ_all |= b

    # Determine if capture
    is_capture = (occ_all >> to_sq) & 1 == 1

    # Apply move to bitboards
    if is_white:
        # Remove pawn from from_sq
        bb[WP] &= ~(1 << from_sq)
        # If capture, remove black piece at to_sq (any type)
        if is_capture:
            mask = ~(1 << to_sq)
            bb[BP] &= mask
            bb[BN] &= mask
            bb[BB] &= mask
            bb[BR] &= mask
            bb[BQ] &= mask
            bb[BK] &= mask
        # Place pawn at to_sq
        bb[WP] |= 1 << to_sq

        # Set EP square for double push (from rank 2 to 4)
        if move.to_sq - move.from_sq == 16:
            ep_square = move.from_sq + 8
    else:
        # Remove pawn from from_sq
        bb[BP] &= ~(1 << from_sq)
        # If capture, remove white piece at to_sq (any type)
        if is_capture:
            mask = ~(1 << to_sq)
            bb[WP] &= mask
            bb[WN] &= mask
            bb[WB] &= mask
            bb[WR] &= mask
            bb[WQ] &= mask
            bb[WK] &= mask
        # Place pawn at to_sq
        bb[BP] |= 1 << to_sq

        # Set EP square for double push (from rank 7 to 5)
        if move.from_sq - move.to_sq == 16:
            ep_square = move.from_sq - 8

    # Halfmove clock: reset on pawn move or capture, else +1 (we reset)
    halfmove_clock = 0
    # Fullmove number: increment after black moves
    fullmove_number = board.fullmove_number + (1 if board.side_to_move == "b" else 0)

    return Board(
        bb=bb,
        side_to_move=("b" if is_white else "w"),
        castling=board.castling,
        ep_square=ep_square,
        halfmove_clock=halfmove_clock,
        fullmove_number=fullmove_number,
    )
