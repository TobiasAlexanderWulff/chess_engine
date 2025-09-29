from __future__ import annotations

import os
import struct
from typing import Dict, List, Optional, Tuple

# Import the precomputed Polyglot random numbers
from .polyglot_randoms import POLYGLOT_RANDOM_ARRAY

from ...engine.game import Game
from ...engine.move import Move


# Polyglot random arrays (abridged shown as assignment; full constants required)
# The following arrays are taken from the Polyglot specification/reference.
# piece-square randoms: [12][64]
PG_RANDOM_PSQ: List[List[int]] = []
PG_RANDOM_CASTLE: List[int] = []
PG_RANDOM_EP: List[int] = []
PG_RANDOM_TURN: int = 0


def _init_polyglot_randoms() -> None:
    # Constants as per Polyglot book spec (781 64-bit values). To keep patch size reasonable,
    # we import them lazily from a compact representation.
    # Source reference values can be embedded here. For brevity, we include the minimal loader.
    # NOTE: In real usage, fill PG_RANDOM_* with the standard tables.
    global PG_RANDOM_PSQ, PG_RANDOM_CASTLE, PG_RANDOM_EP, PG_RANDOM_TURN
    if PG_RANDOM_PSQ:
        return
    # Precomputed values (truncated not allowed); raise if not provided.
    arr = list(POLYGLOT_RANDOM_ARRAY)
    if len(arr) < 12 * 64 + 4 + 8 + 1:
        raise ValueError("POLYGLOT_RANDOM_ARRAY is too short")

    # piece-square tables
    psq_flat = arr[: 12 * 64]
    PG_RANDOM_PSQ = [psq_flat[i * 64 : (i + 1) * 64] for i in range(12)]
    idx = 12 * 64

    # castling base (K,Q,k,q): 4 base values
    cK, cQ, ck, cq = arr[idx : idx + 4]
    idx += 4
    # build 16 entries for bitmask index (K=1, Q=2, k=4, q=8)
    table = [0] * 16
    for mask in range(16):
        v = 0
        if mask & 1:
            v ^= cK
        if mask & 2:
            v ^= cQ
        if mask & 4:
            v ^= ck
        if mask & 8:
            v ^= cq
        table[mask] = v
    PG_RANDOM_CASTLE = table

    # en-passant files (8)
    PG_RANDOM_EP = arr[idx : idx + 8]
    idx += 8

    # side to move
    PG_RANDOM_TURN = arr[idx]


def _polyglot_castle_index(castling: str) -> int:
    idx = 0
    if "K" in castling:
        idx |= 1
    if "Q" in castling:
        idx |= 2
    if "k" in castling:
        idx |= 4
    if "q" in castling:
        idx |= 8
    return idx


def _polyglot_hash(game: Game) -> int:
    _init_polyglot_randoms()
    board = game.board
    h = 0
    # piece mapping: our indices WP..BK map to polyglot piece codes 0..11
    # Our order is WP,WN,WB,WR,WQ,WK, BP,BN,BB,BR,BQ,BK — matches polyglot order.
    for p in range(12):
        bb = board.bb[p]
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            h ^= PG_RANDOM_PSQ[p][sq]
            bb ^= lsb
    # castling
    h ^= PG_RANDOM_CASTLE[_polyglot_castle_index(board.castling)]
    # en passant file (only if capture possible)
    if board.ep_square is not None:
        file_idx = board.ep_square % 8
        if board.side_to_move == "w":
            # white to move, check if any white pawn can capture ep square
            r = board.ep_square // 8
            if r == 5:
                # white pawn on rank 5 (index 4) could capture to ep square
                left = board.ep_square - 1
                right = board.ep_square + 1
                ok = False
                if left >= 0 and (left % 8) != 7:
                    if (board.bb[0] >> (left - 8)) & 1:
                        ok = True
                if right <= 63 and (right % 8) != 0:
                    if (board.bb[0] >> (right - 8)) & 1:
                        ok = True
                if ok:
                    h ^= PG_RANDOM_EP[file_idx]
        else:
            # black to move; ep file valid if black pawn could capture
            r = board.ep_square // 8
            if r == 2:
                left = board.ep_square - 1
                right = board.ep_square + 1
                ok = False
                if left >= 0 and (left % 8) != 7:
                    if (board.bb[6] >> (left + 8)) & 1:
                        ok = True
                if right <= 63 and (right % 8) != 0:
                    if (board.bb[6] >> (right + 8)) & 1:
                        ok = True
                if ok:
                    h ^= PG_RANDOM_EP[file_idx]
    # side to move
    if board.side_to_move == "b":
        h ^= PG_RANDOM_TURN
    return h & 0xFFFFFFFFFFFFFFFF


def _decode_polyglot_move(mv16: int) -> Tuple[int, int, Optional[str]]:
    from_sq = mv16 & 0x3F
    to_sq = (mv16 >> 6) & 0x3F
    prom = (mv16 >> 12) & 0x7
    promo_map = {1: "n", 2: "b", 3: "r", 4: "q"}
    return from_sq, to_sq, promo_map.get(prom)


class PolyglotBook:
    def __init__(self, path: str) -> None:
        self.path = path
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        self._index: Dict[int, List[Tuple[int, int]]] = {}
        self._load()

    def _load(self) -> None:
        with open(self.path, "rb") as f:
            data = f.read()
        n = len(data)
        if n % 16 != 0:
            raise ValueError("invalid polyglot file size")
        idx: Dict[int, List[Tuple[int, int]]] = {}
        for i in range(0, n, 16):
            key, mv, weight, learn = struct.unpack(">QHHI", data[i : i + 16])
            idx.setdefault(key, []).append((mv, weight))
        self._index = idx

    def find_move(self, game: Game, *, randomize: bool = False) -> Optional[Move]:
        key = _polyglot_hash(game)
        items = self._index.get(key)
        if not items:
            return None
        # Filter to legal set
        legal = game.legal_moves()
        legal_set = {(m.from_sq, m.to_sq, m.promotion) for m in legal}
        cand: List[Tuple[Move, int]] = []
        for mv16, w in items:
            fr, to, promo = _decode_polyglot_move(mv16)
            key3 = (fr, to, promo)
            if key3 in legal_set:
                # Rebuild actual Move from legal list to preserve internal fields
                for m in legal:
                    if (m.from_sq, m.to_sq, m.promotion) == key3:
                        cand.append((m, int(w)))
                        break
        if not cand:
            return None
        if not randomize:
            cand.sort(key=lambda x: (x[1], x[0].to_uci()))
            return cand[-1][0]
        total = sum(w for _, w in cand)
        r = (hash(key) & 0x7FFFFFFF) % max(1, total)
        acc = 0
        for m, w in cand:
            acc += w
            if r < acc:
                return m
        return cand[-1][0]
