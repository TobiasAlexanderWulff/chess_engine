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
        child = _apply_pseudo_move(board, m)
        if child is None:
            # Unsupported move type in scaffolding; skip for now.
            continue
        nodes += perft(child, depth - 1)
    return nodes


def _apply_pseudo_move(board: Board, move: Move) -> Board | None:
    """Return a new Board with a simple move applied (scaffolding).

    Supports:
    - Pawn pushes and captures (promotions supported; no EP)
    - Knight moves and captures
    - Bishop, Rook, Queen moves and captures
    - King moves and captures
    Updates: bb, side_to_move, ep_square (for pawn double pushes), half/fullmove.
    Leaves castling rights unchanged. Returns None for unsupported cases.
    """
    from_sq, to_sq = move.from_sq, move.to_sq
    is_white = board.side_to_move == "w"

    # Clone board minimal state
    bb = list(board.bb)
    ep_square = None

    # Occupancies
    occ_all = 0
    for b in bb:
        occ_all |= b

    # Determine if capture based on pre-move occupancy or en passant
    is_capture = (occ_all >> to_sq) & 1 == 1

    moved_is_pawn = False

    if is_white:
        if bb[WP] & (1 << from_sq):
            moved_is_pawn = True
            # Remove pawn and place at destination
            bb[WP] &= ~(1 << from_sq)
            # En passant capture: destination equals ep target; remove pawn behind
            is_ep = (
                board.ep_square is not None
                and to_sq == board.ep_square
                and (to_sq - from_sq) in (7, 9)
            )
            if is_ep:
                cap_sq = to_sq - 8
                bb[BP] &= ~(1 << cap_sq)
                is_capture = True
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            # Promotion handling
            if move.promotion:
                promo_map = {"q": WQ, "r": WR, "b": WB, "n": WN}
                target = promo_map.get(move.promotion)
                if target is None:
                    return None
                bb[target] |= 1 << to_sq
            else:
                bb[WP] |= 1 << to_sq
                # EP target on double push
                if to_sq - from_sq == 16:
                    ep_square = from_sq + 8
        elif bb[WN] & (1 << from_sq):
            bb[WN] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            bb[WN] |= 1 << to_sq
        elif bb[WB] & (1 << from_sq):
            bb[WB] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            bb[WB] |= 1 << to_sq
        elif bb[WR] & (1 << from_sq):
            bb[WR] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            bb[WR] |= 1 << to_sq
        elif bb[WQ] & (1 << from_sq):
            bb[WQ] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            bb[WQ] |= 1 << to_sq
        elif bb[WK] & (1 << from_sq):
            bb[WK] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[BP] &= mask
                bb[BN] &= mask
                bb[BB] &= mask
                bb[BR] &= mask
                bb[BQ] &= mask
                bb[BK] &= mask
            bb[WK] |= 1 << to_sq
        else:
            return None
    else:
        if bb[BP] & (1 << from_sq):
            moved_is_pawn = True
            bb[BP] &= ~(1 << from_sq)
            is_ep = (
                board.ep_square is not None
                and to_sq == board.ep_square
                and (from_sq - to_sq) in (7, 9)
            )
            if is_ep:
                cap_sq = to_sq + 8
                bb[WP] &= ~(1 << cap_sq)
                is_capture = True
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            if move.promotion:
                promo_map = {"q": BQ, "r": BR, "b": BB, "n": BN}
                target = promo_map.get(move.promotion)
                if target is None:
                    return None
                bb[target] |= 1 << to_sq
            else:
                bb[BP] |= 1 << to_sq
                if from_sq - to_sq == 16:
                    ep_square = from_sq - 8
        elif bb[BN] & (1 << from_sq):
            bb[BN] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            bb[BN] |= 1 << to_sq
        elif bb[BB] & (1 << from_sq):
            bb[BB] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            bb[BB] |= 1 << to_sq
        elif bb[BR] & (1 << from_sq):
            bb[BR] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            bb[BR] |= 1 << to_sq
        elif bb[BQ] & (1 << from_sq):
            bb[BQ] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            bb[BQ] |= 1 << to_sq
        elif bb[BK] & (1 << from_sq):
            bb[BK] &= ~(1 << from_sq)
            if is_capture:
                mask = ~(1 << to_sq)
                bb[WP] &= mask
                bb[WN] &= mask
                bb[WB] &= mask
                bb[WR] &= mask
                bb[WQ] &= mask
                bb[WK] &= mask
            bb[BK] |= 1 << to_sq
        else:
            return None

    # Halfmove clock: reset on pawn move or capture; else increment
    if moved_is_pawn or is_capture:
        halfmove_clock = 0
    else:
        halfmove_clock = board.halfmove_clock + 1
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
