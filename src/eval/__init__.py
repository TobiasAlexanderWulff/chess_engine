"""Evaluation heuristics and related utilities.

Pure, deterministic, and side-effect free.
"""

from __future__ import annotations

from typing import Final

from src.engine.board import (
    Board,
    WP,
    WN,
    WB,
    WR,
    WQ,
    BP,
    BN,
    BB,
    BR,
    BQ,
)


# Material values in centipawns
P_VAL: Final = 100
N_VAL: Final = 320
B_VAL: Final = 330
R_VAL: Final = 500
Q_VAL: Final = 900


def _popcount(x: int) -> int:
    return x.bit_count()


def evaluate(board: Board) -> int:
    """Return a simple material evaluation in centipawns.

    Positive means advantage for White. Side-to-move adjustment is done by
    the search (negamax) so this function is side-agnostic.
    """
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
    return material_white - material_black
