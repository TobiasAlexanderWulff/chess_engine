"""Evaluation heuristics and related utilities.

Pure, deterministic, and side-effect free.
"""

from __future__ import annotations

from typing import Final, Iterable

from src.engine.board import (
    Board,
    WP,
    WN,
    WB,
    WR,
    WQ,
    WK,
    BP,
    BN,
    BB,
    BR,
    BQ,
    BK,
)


# Material values in centipawns
P_VAL: Final = 100
N_VAL: Final = 320
B_VAL: Final = 330
R_VAL: Final = 500
Q_VAL: Final = 900

# Heuristic weights (centipawns)
# Mobility weights (middlegame / endgame)
MOB_N_MG: Final = 2
MOB_N_EG: Final = 1
MOB_B_MG: Final = 2
MOB_B_EG: Final = 3
MOB_R_MG: Final = 2
MOB_R_EG: Final = 2
MOB_Q_MG: Final = 1
MOB_Q_EG: Final = 1
BISHOP_PAIR_MG: Final = 20
BISHOP_PAIR_EG: Final = 40
ROOK_SEMIOPEN_BONUS: Final = 8
ROOK_OPEN_BONUS: Final = 14
KING_SHIELD_BONUS: Final = 6  # per pawn in king shield ring
ROOK_SEVENTH_BONUS: Final = 20
OUTPOST_N_BONUS: Final = 25


def _popcount(x: int) -> int:
    return x.bit_count()


def _iter_bits(bb: int) -> Iterable[int]:
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        yield sq
        bb ^= lsb


def _mirror_sq(sq: int) -> int:
    # Flip vertically (rank mirror)
    f = sq % 8
    r = sq // 8
    return (7 - r) * 8 + f


def _file_mask(file_idx: int) -> int:
    mask = 0
    for r in range(8):
        mask |= 1 << (r * 8 + file_idx)
    return mask


FILE_MASKS: Final = tuple(_file_mask(f) for f in range(8))


def _count_knight_moves(sq: int, own_occ: int) -> int:
    f = sq % 8
    r = sq // 8
    cnt = 0
    for df, dr in ((-1, 2), (1, 2), (-2, 1), (2, 1), (-2, -1), (2, -1), (-1, -2), (1, -2)):
        tf, tr = f + df, r + dr
        if 0 <= tf < 8 and 0 <= tr < 8:
            to = tr * 8 + tf
            if ((own_occ >> to) & 1) == 0:
                cnt += 1
    return cnt


def _count_slider_moves(
    sq: int, own_occ: int, occ_all: int, dirs: Iterable[tuple[int, int]]
) -> int:
    f = sq % 8
    r = sq // 8
    cnt = 0
    for df, dr in dirs:
        tf, tr = f, r
        while True:
            tf += df
            tr += dr
            if not (0 <= tf < 8 and 0 <= tr < 8):
                break
            to = tr * 8 + tf
            if ((own_occ >> to) & 1) != 0:
                break
            cnt += 1
            if ((occ_all >> to) & 1) != 0:
                break
    return cnt


def _king_shield_pawns(board: Board, white: bool) -> int:
    # Count friendly pawns in two-rank ring in front of king on files f-1..f+1
    king_bb = board.bb[WK] if white else board.bb[BK]
    if king_bb == 0:
        return 0
    ksq = (king_bb & -king_bb).bit_length() - 1
    kf = ksq % 8
    kr = ksq // 8
    pawns = board.bb[WP] if white else board.bb[BP]
    total = 0
    for df in (-1, 0, 1):
        ff = kf + df
        if not (0 <= ff < 8):
            continue
        for dr in (1, 2):
            rr = kr + (dr if white else -dr)
            if 0 <= rr < 8:
                sq = rr * 8 + ff
                if ((pawns >> sq) & 1) != 0:
                    total += 1
    return total


def _pawn_attacks_square(board: Board, sq: int, by_white: bool) -> bool:
    f = sq % 8
    if by_white:
        # White pawns attack from behind (downwards relative to sq): sq-7 and sq-9
        if f > 0:
            o = sq - 9
            if o >= 0 and ((board.bb[WP] >> o) & 1):
                return True
        if f < 7:
            o = sq - 7
            if o >= 0 and ((board.bb[WP] >> o) & 1):
                return True
    else:
        # Black pawns attack from ahead (upwards relative to sq): sq+7 and sq+9
        if f < 7:
            o = sq + 9
            if o <= 63 and ((board.bb[BP] >> o) & 1):
                return True
        if f > 0:
            o = sq + 7
            if o <= 63 and ((board.bb[BP] >> o) & 1):
                return True
    return False


def _pawn_supports_square(board: Board, sq: int, white: bool) -> bool:
    f = sq % 8
    if white:
        if f > 0:
            o = sq - 9
            if o >= 0 and ((board.bb[WP] >> o) & 1):
                return True
        if f < 7:
            o = sq - 7
            if o >= 0 and ((board.bb[WP] >> o) & 1):
                return True
    else:
        if f < 7:
            o = sq + 9
            if o <= 63 and ((board.bb[BP] >> o) & 1):
                return True
        if f > 0:
            o = sq + 7
            if o <= 63 and ((board.bb[BP] >> o) & 1):
                return True
    return False


# Simple piece-square tables (white perspective), centipawns
# Source-inspired but simplified; tuned for clarity not strength.
PSQT_P: Final = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    5,
    10,
    10,
    -20,
    -20,
    10,
    10,
    5,
    5,
    -5,
    -10,
    0,
    0,
    -10,
    -5,
    5,
    0,
    0,
    0,
    20,
    20,
    0,
    0,
    0,
    5,
    5,
    10,
    25,
    25,
    10,
    5,
    5,
    10,
    10,
    20,
    30,
    30,
    20,
    10,
    10,
    50,
    50,
    50,
    50,
    50,
    50,
    50,
    50,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]

PSQT_N: Final = [
    -50,
    -40,
    -30,
    -30,
    -30,
    -30,
    -40,
    -50,
    -40,
    -20,
    0,
    0,
    0,
    0,
    -20,
    -40,
    -30,
    0,
    10,
    15,
    15,
    10,
    0,
    -30,
    -30,
    5,
    15,
    20,
    20,
    15,
    5,
    -30,
    -30,
    0,
    15,
    20,
    20,
    15,
    0,
    -30,
    -30,
    5,
    10,
    15,
    15,
    10,
    5,
    -30,
    -40,
    -20,
    0,
    5,
    5,
    0,
    -20,
    -40,
    -50,
    -40,
    -30,
    -30,
    -30,
    -30,
    -40,
    -50,
]

PSQT_B: Final = [
    -20,
    -10,
    -10,
    -10,
    -10,
    -10,
    -10,
    -20,
    -10,
    5,
    0,
    0,
    0,
    0,
    5,
    -10,
    -10,
    10,
    10,
    10,
    10,
    10,
    10,
    -10,
    -10,
    0,
    10,
    10,
    10,
    10,
    0,
    -10,
    -10,
    5,
    5,
    10,
    10,
    5,
    5,
    -10,
    -10,
    0,
    5,
    10,
    10,
    5,
    0,
    -10,
    -10,
    0,
    0,
    0,
    0,
    0,
    0,
    -10,
    -20,
    -10,
    -10,
    -10,
    -10,
    -10,
    -10,
    -20,
]

PSQT_R: Final = [
    0,
    0,
    5,
    10,
    10,
    5,
    0,
    0,
    -5,
    0,
    0,
    0,
    0,
    0,
    0,
    -5,
    -5,
    0,
    0,
    0,
    0,
    0,
    0,
    -5,
    -5,
    0,
    0,
    0,
    0,
    0,
    0,
    -5,
    -5,
    0,
    0,
    0,
    0,
    0,
    0,
    -5,
    -5,
    0,
    0,
    0,
    0,
    0,
    0,
    -5,
    5,
    10,
    10,
    10,
    10,
    10,
    10,
    5,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]

PSQT_Q: Final = [
    -20,
    -10,
    -10,
    -5,
    -5,
    -10,
    -10,
    -20,
    -10,
    0,
    0,
    0,
    0,
    0,
    0,
    -10,
    -10,
    0,
    5,
    5,
    5,
    5,
    0,
    -10,
    -5,
    0,
    5,
    5,
    5,
    5,
    0,
    -5,
    -5,
    0,
    5,
    5,
    5,
    5,
    0,
    -5,
    -10,
    0,
    5,
    5,
    5,
    5,
    0,
    -10,
    -10,
    0,
    0,
    0,
    0,
    0,
    0,
    -10,
    -20,
    -10,
    -10,
    -5,
    -5,
    -10,
    -10,
    -20,
]

PSQT_K: Final = [
    20,
    30,
    10,
    0,
    0,
    10,
    30,
    20,
    20,
    20,
    0,
    0,
    0,
    0,
    20,
    20,
    -10,
    -20,
    -20,
    -20,
    -20,
    -20,
    -20,
    -10,
    -20,
    -30,
    -30,
    -40,
    -40,
    -30,
    -30,
    -20,
    -30,
    -40,
    -40,
    -50,
    -50,
    -40,
    -40,
    -30,
    -30,
    -40,
    -40,
    -50,
    -50,
    -40,
    -40,
    -30,
    -30,
    -40,
    -40,
    -50,
    -50,
    -40,
    -40,
    -30,
    -30,
    -40,
    -40,
    -50,
    -50,
    -40,
    -40,
    -30,
]

PSQT_K_EG: Final = [
    -50,
    -30,
    -30,
    -30,
    -30,
    -30,
    -30,
    -50,
    -30,
    -10,
    0,
    0,
    0,
    0,
    -10,
    -30,
    -30,
    0,
    10,
    15,
    15,
    10,
    0,
    -30,
    -30,
    0,
    15,
    20,
    20,
    15,
    0,
    -30,
    -30,
    0,
    15,
    20,
    20,
    15,
    0,
    -30,
    -30,
    0,
    10,
    15,
    15,
    10,
    0,
    -30,
    -30,
    -10,
    0,
    0,
    0,
    0,
    -10,
    -30,
    -50,
    -30,
    -30,
    -30,
    -30,
    -30,
    -30,
    -50,
]


def evaluate(board: Board) -> int:
    """Return a material + PSQT evaluation in centipawns.

    Positive means advantage for White. Side-to-move adjustment is done by
    the search (negamax) so this function is side-agnostic.
    """
    # Material
    wp = _popcount(board.bb[WP]) * P_VAL
    wn = _popcount(board.bb[WN]) * N_VAL
    wb = _popcount(board.bb[WB]) * B_VAL
    wr = _popcount(board.bb[WR]) * R_VAL
    wq = _popcount(board.bb[WQ]) * Q_VAL

    bp = _popcount(board.bb[BP]) * P_VAL
    bn = _popcount(board.bb[BN]) * N_VAL
    bb_ = _popcount(board.bb[BB]) * B_VAL
    br = _popcount(board.bb[BR]) * R_VAL
    bq = _popcount(board.bb[BQ]) * Q_VAL

    material_white = wp + wn + wb + wr + wq
    material_black = bp + bn + bb_ + br + bq

    score = material_white - material_black

    # Piece-square terms
    for sq in _iter_bits(board.bb[WP]):
        score += PSQT_P[sq]
    for sq in _iter_bits(board.bb[WN]):
        score += PSQT_N[sq]
    for sq in _iter_bits(board.bb[WB]):
        score += PSQT_B[sq]
    for sq in _iter_bits(board.bb[WR]):
        score += PSQT_R[sq]
    for sq in _iter_bits(board.bb[WQ]):
        score += PSQT_Q[sq]
    for sq in _iter_bits(board.bb[BP]):
        score -= PSQT_P[_mirror_sq(sq)]
    for sq in _iter_bits(board.bb[BN]):
        score -= PSQT_N[_mirror_sq(sq)]
    for sq in _iter_bits(board.bb[BB]):
        score -= PSQT_B[_mirror_sq(sq)]
    for sq in _iter_bits(board.bb[BR]):
        score -= PSQT_R[_mirror_sq(sq)]
    for sq in _iter_bits(board.bb[BQ]):
        score -= PSQT_Q[_mirror_sq(sq)]

    # Game phase blending (0..128 scale)
    knights = (board.bb[WN] | board.bb[BN]).bit_count()
    bishops = (board.bb[WB] | board.bb[BB]).bit_count()
    rooks = (board.bb[WR] | board.bb[BR]).bit_count()
    queens = (board.bb[WQ] | board.bb[BQ]).bit_count()
    phase_units = knights + bishops + 2 * rooks + 4 * queens
    PHASE_TOTAL = 24
    mg_scaled = max(0, min(128, (phase_units * 128) // PHASE_TOTAL))
    eg_scaled = 128 - mg_scaled

    # King tables: blend MG/EG
    for sq in _iter_bits(board.bb[WK]):
        score += (mg_scaled * PSQT_K[sq] + eg_scaled * PSQT_K_EG[sq]) // 128
    for sq in _iter_bits(board.bb[BK]):
        idx = _mirror_sq(sq)
        score -= (mg_scaled * PSQT_K[idx] + eg_scaled * PSQT_K_EG[idx]) // 128

    # Mobility (simple pseudo-legal without self-occupancy)
    occ_all = 0
    for bb in board.bb:
        occ_all |= bb
    occ_w = board.bb[WP] | board.bb[WN] | board.bb[WB] | board.bb[WR] | board.bb[WQ] | board.bb[WK]
    occ_b = board.bb[BP] | board.bb[BN] | board.bb[BB] | board.bb[BR] | board.bb[BQ] | board.bb[BK]

    # Knights
    w_mob = 0
    b_mob = 0
    for sq in _iter_bits(board.bb[WN]):
        w_mob += _count_knight_moves(sq, occ_w)
    for sq in _iter_bits(board.bb[BN]):
        b_mob += _count_knight_moves(sq, occ_b)
    mob_n = (mg_scaled * MOB_N_MG + eg_scaled * MOB_N_EG) // 128
    score += (w_mob - b_mob) * mob_n

    # Bishops
    dirs_b = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    w_mob = 0
    b_mob = 0
    for sq in _iter_bits(board.bb[WB]):
        w_mob += _count_slider_moves(sq, occ_w, occ_all, dirs_b)
    for sq in _iter_bits(board.bb[BB]):
        b_mob += _count_slider_moves(sq, occ_b, occ_all, dirs_b)
    mob_b = (mg_scaled * MOB_B_MG + eg_scaled * MOB_B_EG) // 128
    score += (w_mob - b_mob) * mob_b

    # Rooks
    dirs_r = ((-1, 0), (1, 0), (0, -1), (0, 1))
    w_mob = 0
    b_mob = 0
    for sq in _iter_bits(board.bb[WR]):
        w_mob += _count_slider_moves(sq, occ_w, occ_all, dirs_r)
    for sq in _iter_bits(board.bb[BR]):
        b_mob += _count_slider_moves(sq, occ_b, occ_all, dirs_r)
    mob_r = (mg_scaled * MOB_R_MG + eg_scaled * MOB_R_EG) // 128
    score += (w_mob - b_mob) * mob_r

    # Queens
    dirs_q = dirs_b + dirs_r
    w_mob = 0
    b_mob = 0
    for sq in _iter_bits(board.bb[WQ]):
        w_mob += _count_slider_moves(sq, occ_w, occ_all, dirs_q)
    for sq in _iter_bits(board.bb[BQ]):
        b_mob += _count_slider_moves(sq, occ_b, occ_all, dirs_q)
    mob_q = (mg_scaled * MOB_Q_MG + eg_scaled * MOB_Q_EG) // 128
    score += (w_mob - b_mob) * mob_q

    # Bishop pair (phase-scaled)
    bp = (mg_scaled * BISHOP_PAIR_MG + eg_scaled * BISHOP_PAIR_EG) // 128
    if board.bb[WB].bit_count() >= 2:
        score += bp
    if board.bb[BB].bit_count() >= 2:
        score -= bp

    # Rook file bonuses
    wpawns = board.bb[WP]
    bpawns = board.bb[BP]
    for sq in _iter_bits(board.bb[WR]):
        f = sq % 8
        file_mask = FILE_MASKS[f]
        own_pawn = (wpawns & file_mask) != 0
        opp_pawn = (bpawns & file_mask) != 0
        if not own_pawn and not opp_pawn:
            score += ROOK_OPEN_BONUS
        elif not own_pawn and opp_pawn:
            score += ROOK_SEMIOPEN_BONUS
    for sq in _iter_bits(board.bb[BR]):
        f = sq % 8
        file_mask = FILE_MASKS[f]
        own_pawn = (bpawns & file_mask) != 0
        opp_pawn = (wpawns & file_mask) != 0
        if not own_pawn and not opp_pawn:
            score -= ROOK_OPEN_BONUS
        elif not own_pawn and opp_pawn:
            score -= ROOK_SEMIOPEN_BONUS

    # Rooks on seventh rank (from own perspective): white on rank 7 (index 6), black on rank 2 (index 1)
    for sq in _iter_bits(board.bb[WR]):
        if (sq // 8) == 6:
            score += ROOK_SEVENTH_BONUS
    for sq in _iter_bits(board.bb[BR]):
        if (sq // 8) == 1:
            score -= ROOK_SEVENTH_BONUS

    # Knight outposts: in opponent half, supported by own pawn, not attackable by enemy pawns
    for sq in _iter_bits(board.bb[WN]):
        r = sq // 8
        if 3 <= r <= 5:
            if _pawn_supports_square(board, sq, True) and not _pawn_attacks_square(
                board, sq, by_white=False
            ):
                score += OUTPOST_N_BONUS
    for sq in _iter_bits(board.bb[BN]):
        r = sq // 8
        if 2 <= r <= 4:
            if _pawn_supports_square(board, sq, False) and not _pawn_attacks_square(
                board, sq, by_white=True
            ):
                score -= OUTPOST_N_BONUS

    # King safety: pawn shield in front of the king
    score += _king_shield_pawns(board, True) * KING_SHIELD_BONUS
    score -= _king_shield_pawns(board, False) * KING_SHIELD_BONUS

    return score
