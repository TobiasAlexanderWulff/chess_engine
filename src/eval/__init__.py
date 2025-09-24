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

    # King tables (middlegame-like)
    for sq in _iter_bits(board.bb[WK]):
        score += PSQT_K[sq]
    for sq in _iter_bits(board.bb[BK]):
        score -= PSQT_K[_mirror_sq(sq)]

    return score
