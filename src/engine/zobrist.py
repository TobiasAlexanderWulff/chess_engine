from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .board import Board


MASK64 = 0xFFFFFFFFFFFFFFFF


class _SplitMix64:
    def __init__(self, seed: int) -> None:
        self.state = seed & MASK64

    def next(self) -> int:
        # Deterministic 64-bit SplitMix64
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        z = self.state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & MASK64
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & MASK64
        z = z ^ (z >> 31)
        return z & MASK64


class Zobrist:
    """Zobrist hashing seeds and utilities.

    Table layout:
    - piece_square[12][64]: indices follow Board piece order (WP..BK)
    - side_to_move: toggle for black side to move
    - castling[4]: K, Q, k, q
    - ep_file[8]: files a..h
    """

    piece_square: List[List[int]]
    side_to_move: int
    castling: List[int]
    ep_file: List[int]

    def __init__(self, seed: int = 0xC0FFEE_F00D_DEAD) -> None:
        prng = _SplitMix64(seed)
        self.piece_square = [[0] * 64 for _ in range(12)]
        for p in range(12):
            for sq in range(64):
                self.piece_square[p][sq] = prng.next()
        self.side_to_move = prng.next()
        self.castling = [prng.next() for _ in range(4)]  # K, Q, k, q
        self.ep_file = [prng.next() for _ in range(8)]  # a..h


# Global deterministic table
ZOBRIST = Zobrist()


def compute_hash_from_scratch(board: "Board") -> int:
    """Compute 64-bit Zobrist hash from a Board.

    Deterministic across runs given fixed ZOBRIST table.
    """
    h = 0
    # Pieces
    for p in range(12):
        bb = board.bb[p]
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            h ^= ZOBRIST.piece_square[p][sq]
            bb ^= lsb
    # Side to move
    if board.side_to_move == "b":
        h ^= ZOBRIST.side_to_move
    # Castling rights in fixed order KQkq
    if board.castling:
        order = "KQkq"
        for i, ch in enumerate(order):
            if ch in board.castling:
                h ^= ZOBRIST.castling[i]
    # En passant file (if any)
    if board.ep_square is not None:
        file_idx = board.ep_square % 8
        h ^= ZOBRIST.ep_file[file_idx]
    return h & MASK64


def incremental_hash_update(current_hash: int, board_before: "Board", board_after: "Board") -> int:
    """Incrementally update a hash given before/after boards (placeholder).

    For now, compute-from-scratch to validate parity; replace with true
    incremental updates after make/unmake implementation.
    """
    return compute_hash_from_scratch(board_after)
