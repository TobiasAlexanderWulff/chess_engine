from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .move import Move, square_to_str, str_to_square


STARTPOS_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


# Piece indices for bitboards
WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK = range(12)
PIECE_ORDER = [WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK]
PIECE_TO_CHAR = {
    WP: "P",
    WN: "N",
    WB: "B",
    WR: "R",
    WQ: "Q",
    WK: "K",
    BP: "p",
    BN: "n",
    BB: "b",
    BR: "r",
    BQ: "q",
    BK: "k",
}
CHAR_TO_PIECE = {v: k for k, v in PIECE_TO_CHAR.items()}


def _set_bit(bb: int, sq: int) -> int:
    return bb | (1 << sq)


def _get_bit(bb: int, sq: int) -> bool:
    return (bb >> sq) & 1 == 1


@dataclass
class Board:
    """Board state with bitboards and FEN I/O.

    Notes:
    - Squares are 0..63 (a1=0 .. h8=63), rank-major from white's perspective.
    - Core engine remains pure and deterministic.
    """

    # 12 piece bitboards, indexed by constants above
    bb: List[int]
    side_to_move: str  # 'w' or 'b'
    castling: str  # subset of 'KQkq' or ''
    ep_square: Optional[int]  # square index or None
    halfmove_clock: int
    fullmove_number: int

    @classmethod
    def startpos(cls) -> "Board":
        return cls.from_fen(STARTPOS_FEN)

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        if not fen or not isinstance(fen, str):
            raise ValueError("FEN must be a non-empty string")
        parts = fen.strip().split()
        if len(parts) != 6:
            raise ValueError("FEN must have 6 fields")
        placement, stm, castling, ep, halfmove, fullmove = parts

        # Parse piece placement
        ranks = placement.split("/")
        if len(ranks) != 8:
            raise ValueError("FEN board must have 8 ranks")
        bb = [0] * 12
        for rank_idx, rank in enumerate(ranks[::-1]):  # start from rank 1 (bottom)
            file_idx = 0
            for ch in rank:
                if ch.isdigit():
                    n = int(ch)
                    if n < 1 or n > 8:
                        raise ValueError("invalid empty count in FEN rank")
                    file_idx += n
                else:
                    if ch not in CHAR_TO_PIECE:
                        raise ValueError(f"invalid piece in FEN: {ch!r}")
                    if file_idx >= 8:
                        raise ValueError("too many squares in FEN rank")
                    sq = rank_idx * 8 + file_idx
                    p = CHAR_TO_PIECE[ch]
                    bb[p] = _set_bit(bb[p], sq)
                    file_idx += 1
            if file_idx != 8:
                raise ValueError("rank does not sum to 8 squares in FEN")

        # Side to move
        if stm not in ("w", "b"):
            raise ValueError("side to move must be 'w' or 'b'")

        # Castling rights
        if castling != "-":
            for ch in castling:
                if ch not in "KQkq":
                    raise ValueError("invalid castling rights")
            # normalize ordering KQkq
            order = "KQkq"
            castling = "".join([c for c in order if c in castling])
        else:
            castling = ""

        # En passant square
        ep_square: Optional[int]
        if ep == "-":
            ep_square = None
        else:
            try:
                ep_square = str_to_square(ep)
            except ValueError as e:
                raise ValueError("invalid en passant square") from e
            rank = ep_square // 8
            # Optional sanity: ep target must be on rank 2 (index 2) or 5 (index 5) (ranks 3 or 6)
            if rank not in (2, 5):
                raise ValueError("invalid en passant square rank")

        # Halfmove / fullmove
        try:
            halfmove_clock = int(halfmove)
            fullmove_number = int(fullmove)
        except ValueError as e:
            raise ValueError("invalid move counters in FEN") from e
        if halfmove_clock < 0 or fullmove_number <= 0:
            raise ValueError("invalid move counters in FEN")

        return cls(
            bb=bb,
            side_to_move=stm,
            castling=castling,
            ep_square=ep_square,
            halfmove_clock=halfmove_clock,
            fullmove_number=fullmove_number,
        )

    def to_fen(self) -> str:
        # Piece placement
        ranks_str: List[str] = []
        for rank_idx in range(7, -1, -1):  # 7..0 maps to ranks 8..1
            run = 0
            row = []
            for file_idx in range(8):
                sq = rank_idx * 8 + file_idx
                ch = self._piece_char_at(sq)
                if ch is None:
                    run += 1
                else:
                    if run > 0:
                        row.append(str(run))
                        run = 0
                    row.append(ch)
            if run > 0:
                row.append(str(run))
            ranks_str.append("".join(row))
        placement = "/".join(ranks_str)

        stm = self.side_to_move
        castling = self.castling if self.castling else "-"
        ep = square_to_str(self.ep_square) if self.ep_square is not None else "-"
        return f"{placement} {stm} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    def _piece_char_at(self, sq: int) -> Optional[str]:
        # White pieces first (uppercase), then black
        for idx in PIECE_ORDER:
            if _get_bit(self.bb[idx], sq):
                return PIECE_TO_CHAR[idx]
        return None

    def generate_legal_moves(self) -> List[Move]:
        """Return pseudo-legal moves (pawns, knights, king) with basic legality.

        Scaffolding for Plan 3: generate pawn pushes (single/double, promotions),
        pawn captures (promotions), knights, and king moves. Applies basic
        in-check filtering by rejecting moves that leave own king attacked.
        En passant, castling, and sliders are not implemented yet.
        """
        moves: List[Move] = []
        PROMOS = ("q", "r", "b", "n")

        # Occupancy helpers
        occ_all = 0
        for bb in self.bb:
            occ_all |= bb
        occ_white = (
            self.bb[WP] | self.bb[WN] | self.bb[WB] | self.bb[WR] | self.bb[WQ] | self.bb[WK]
        )
        occ_black = (
            self.bb[BP] | self.bb[BN] | self.bb[BB] | self.bb[BR] | self.bb[BQ] | self.bb[BK]
        )

        if self.side_to_move == "w":
            pawns = self.bb[WP]
            while pawns:
                lsb = pawns & -pawns
                from_sq = lsb.bit_length() - 1
                file_idx = from_sq % 8
                rank_idx = from_sq // 8

                # Single push (handle promotions from rank 7 → 8)
                to_sq = from_sq + 8
                if to_sq <= 63 and not ((occ_all >> to_sq) & 1):
                    if rank_idx == 6:  # promotion
                        for promo in PROMOS:
                            moves.append(Move(from_sq, to_sq, promotion=promo))
                    else:
                        moves.append(Move(from_sq, to_sq))
                        # Double push from rank 2 (rank_idx == 1)
                        if rank_idx == 1:
                            to2 = from_sq + 16
                            if not ((occ_all >> to2) & 1):
                                moves.append(Move(from_sq, to2))

                # Captures
                # Left capture (from White's perspective): +7 if not on file a
                if file_idx > 0:
                    cap = from_sq + 7
                    if cap <= 63 and ((occ_black >> cap) & 1):
                        if (cap // 8) == 7:
                            for promo in PROMOS:
                                moves.append(Move(from_sq, cap, promotion=promo))
                        else:
                            moves.append(Move(from_sq, cap))
                # Right capture: +9 if not on file h
                if file_idx < 7:
                    cap = from_sq + 9
                    if cap <= 63 and ((occ_black >> cap) & 1):
                        if (cap // 8) == 7:
                            for promo in PROMOS:
                                moves.append(Move(from_sq, cap, promotion=promo))
                        else:
                            moves.append(Move(from_sq, cap))

                pawns ^= lsb
            # Knights (no legality filtering yet)
            knights = self.bb[WN]
            while knights:
                lsb = knights & -knights
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, 2),
                    (1, 2),
                    (-2, 1),
                    (2, 1),
                    (-2, -1),
                    (2, -1),
                    (-1, -2),
                    (1, -2),
                ):
                    tf = f + df
                    tr = r + dr
                    if 0 <= tf < 8 and 0 <= tr < 8:
                        to_sq = tr * 8 + tf
                        if not ((occ_white >> to_sq) & 1):
                            moves.append(Move(from_sq, to_sq))
                knights ^= lsb
            # King moves: avoid moving into opponent attacks
            king_bb = self.bb[WK]
            if king_bb:
                from_sq = (king_bb & -king_bb).bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1),
                ):
                    tf = f + df
                    tr = r + dr
                    if 0 <= tf < 8 and 0 <= tr < 8:
                        to_sq = tr * 8 + tf
                        if not ((occ_white >> to_sq) & 1):
                            if not self._is_attacked(to_sq, by_white=False):
                                moves.append(Move(from_sq, to_sq))
        else:
            pawns = self.bb[BP]
            while pawns:
                lsb = pawns & -pawns
                from_sq = lsb.bit_length() - 1
                file_idx = from_sq % 8
                rank_idx = from_sq // 8

                # Single push (handle promotions from rank 2 → 1)
                to_sq = from_sq - 8
                if to_sq >= 0 and not ((occ_all >> to_sq) & 1):
                    if rank_idx == 1:  # promotion
                        for promo in PROMOS:
                            moves.append(Move(from_sq, to_sq, promotion=promo))
                    else:
                        moves.append(Move(from_sq, to_sq))
                        # Double push from rank 7 (rank_idx == 6)
                        if rank_idx == 6:
                            to2 = from_sq - 16
                            if not ((occ_all >> to2) & 1):
                                moves.append(Move(from_sq, to2))

                # Captures
                # Left capture from Black's perspective: -9 if not on file a
                if file_idx > 0:
                    cap = from_sq - 9
                    if cap >= 0 and ((occ_white >> cap) & 1):
                        if (cap // 8) == 0:
                            for promo in PROMOS:
                                moves.append(Move(from_sq, cap, promotion=promo))
                        else:
                            moves.append(Move(from_sq, cap))
                # Right capture: -7 if not on file h
                if file_idx < 7:
                    cap = from_sq - 7
                    if cap >= 0 and ((occ_white >> cap) & 1):
                        if (cap // 8) == 0:
                            for promo in PROMOS:
                                moves.append(Move(from_sq, cap, promotion=promo))
                        else:
                            moves.append(Move(from_sq, cap))

                pawns ^= lsb
            # Knights (no legality filtering yet)
            knights = self.bb[BN]
            while knights:
                lsb = knights & -knights
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, 2),
                    (1, 2),
                    (-2, 1),
                    (2, 1),
                    (-2, -1),
                    (2, -1),
                    (-1, -2),
                    (1, -2),
                ):
                    tf = f + df
                    tr = r + dr
                    if 0 <= tf < 8 and 0 <= tr < 8:
                        to_sq = tr * 8 + tf
                        if not ((occ_black >> to_sq) & 1):
                            moves.append(Move(from_sq, to_sq))
                knights ^= lsb
            # King moves: avoid moving into opponent attacks
            king_bb = self.bb[BK]
            if king_bb:
                from_sq = (king_bb & -king_bb).bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1),
                ):
                    tf = f + df
                    tr = r + dr
                    if 0 <= tf < 8 and 0 <= tr < 8:
                        to_sq = tr * 8 + tf
                        if not ((occ_black >> to_sq) & 1):
                            if not self._is_attacked(to_sq, by_white=True):
                                moves.append(Move(from_sq, to_sq))

        # Filter out moves that leave own king in check.
        legal: List[Move] = []
        for mv in moves:
            new_bb = self._apply_pseudo_to_bb(mv)
            if new_bb is None:
                continue
            if self.side_to_move == "w":
                king_bb = new_bb[WK]
                if king_bb == 0:
                    continue
                king_sq = (king_bb & -king_bb).bit_length() - 1
                if not self._is_attacked(king_sq, by_white=False, bb=new_bb):
                    legal.append(mv)
            else:
                king_bb = new_bb[BK]
                if king_bb == 0:
                    continue
                king_sq = (king_bb & -king_bb).bit_length() - 1
                if not self._is_attacked(king_sq, by_white=True, bb=new_bb):
                    legal.append(mv)

        return legal

    def apply(self, move: Move) -> "Board":
        # To be implemented in Plan 3
        raise NotImplementedError("move application not implemented yet")

    # --- Plan 3 scaffolding ---
    def make_move(self, move: Move) -> None:
        """Apply `move` to this board in-place.

        Scaffolding stub for Plan 3. To be implemented with full rules:
        - normal moves, captures, promotions, castling, en passant
        - update halfmove/fullmove counters, castling rights, ep square
        - maintain Zobrist hash incrementally (once stored on Board or via external state)
        """
        raise NotImplementedError("make_move not implemented yet")

    def unmake_move(self, move: Move) -> None:
        """Undo the last move in-place, restoring previous state.

        Scaffolding stub for Plan 3. Requires a move/state stack to restore:
        - moved/captured/promoted pieces, castling rights, ep square, counters
        - hash and any incremental caches
        """
        raise NotImplementedError("unmake_move not implemented yet")

    # --- Attack and simulation helpers (scaffolding) ---
    def _is_attacked(self, sq: int, *, by_white: bool, bb: Optional[List[int]] = None) -> bool:
        """Return True if square `sq` is attacked by given side on board `bb`.

        Covers: pawns, knights, king, and slider rays for bishops/rooks/queens.
        """
        if bb is None:
            bb = self.bb

        # Pawn attacks
        f = sq % 8
        r = sq // 8
        if by_white:
            # White pawns attack +7 and +9
            if f > 0:
                o = sq - 9
                if o >= 0 and ((bb[WP] >> o) & 1):
                    return True
            if f < 7:
                o = sq - 7
                if o >= 0 and ((bb[WP] >> o) & 1):
                    return True
        else:
            # Black pawns attack -7 and -9 relative to white's perspective
            if f < 7:
                o = sq + 9
                if o <= 63 and ((bb[BP] >> o) & 1):
                    return True
            if f > 0:
                o = sq + 7
                if o <= 63 and ((bb[BP] >> o) & 1):
                    return True

        # Knight attacks
        for df, dr in ((-1, 2), (1, 2), (-2, 1), (2, 1), (-2, -1), (2, -1), (-1, -2), (1, -2)):
            tf = f + df
            tr = r + dr
            if 0 <= tf < 8 and 0 <= tr < 8:
                o = tr * 8 + tf
                if by_white:
                    if (bb[WN] >> o) & 1:
                        return True
                else:
                    if (bb[BN] >> o) & 1:
                        return True

        # King attacks
        for df, dr in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            tf = f + df
            tr = r + dr
            if 0 <= tf < 8 and 0 <= tr < 8:
                o = tr * 8 + tf
                if by_white:
                    if (bb[WK] >> o) & 1:
                        return True
                else:
                    if (bb[BK] >> o) & 1:
                        return True

        # Slider attacks (bishop/rook/queen)
        occ = 0
        for b in bb:
            occ |= b

        # Bishop-like directions
        for df, dr in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            tf, tr = f, r
            while True:
                tf += df
                tr += dr
                if not (0 <= tf < 8 and 0 <= tr < 8):
                    break
                o = tr * 8 + tf
                if (occ >> o) & 1:
                    if by_white:
                        if ((bb[WB] >> o) & 1) or ((bb[WQ] >> o) & 1):
                            return True
                    else:
                        if ((bb[BB] >> o) & 1) or ((bb[BQ] >> o) & 1):
                            return True
                    break

        # Rook-like directions
        for df, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            tf, tr = f, r
            while True:
                tf += df
                tr += dr
                if not (0 <= tf < 8 and 0 <= tr < 8):
                    break
                o = tr * 8 + tf
                if (occ >> o) & 1:
                    if by_white:
                        if ((bb[WR] >> o) & 1) or ((bb[WQ] >> o) & 1):
                            return True
                    else:
                        if ((bb[BR] >> o) & 1) or ((bb[BQ] >> o) & 1):
                            return True
                    break

        return False

    def _apply_pseudo_to_bb(self, move: Move) -> Optional[List[int]]:
        """Apply a simple move to a copy of bitboards; return new bitboards.

        Supports: pawns (incl. promotions, no en passant), knights, king.
        """
        from_sq, to_sq = move.from_sq, move.to_sq
        is_white = self.side_to_move == "w"
        bb = list(self.bb)

        # Remove destination piece if any (capture)
        mask_to = ~(1 << to_sq)
        if is_white:
            bb[BP] &= mask_to
            bb[BN] &= mask_to
            bb[BB] &= mask_to
            bb[BR] &= mask_to
            bb[BQ] &= mask_to
            bb[BK] &= mask_to
        else:
            bb[WP] &= mask_to
            bb[WN] &= mask_to
            bb[WB] &= mask_to
            bb[WR] &= mask_to
            bb[WQ] &= mask_to
            bb[WK] &= mask_to

        moved = False
        if is_white:
            if (bb[WP] >> from_sq) & 1:
                bb[WP] &= ~(1 << from_sq)
                if move.promotion:
                    promo_map = {"q": WQ, "r": WR, "b": WB, "n": WN}
                    bb[promo_map[move.promotion]] |= 1 << to_sq
                else:
                    bb[WP] |= 1 << to_sq
                moved = True
            elif (bb[WN] >> from_sq) & 1:
                bb[WN] &= ~(1 << from_sq)
                bb[WN] |= 1 << to_sq
                moved = True
            elif (bb[WK] >> from_sq) & 1:
                bb[WK] &= ~(1 << from_sq)
                bb[WK] |= 1 << to_sq
                moved = True
        else:
            if (bb[BP] >> from_sq) & 1:
                bb[BP] &= ~(1 << from_sq)
                if move.promotion:
                    promo_map = {"q": BQ, "r": BR, "b": BB, "n": BN}
                    bb[promo_map[move.promotion]] |= 1 << to_sq
                else:
                    bb[BP] |= 1 << to_sq
                moved = True
            elif (bb[BN] >> from_sq) & 1:
                bb[BN] &= ~(1 << from_sq)
                bb[BN] |= 1 << to_sq
                moved = True
            elif (bb[BK] >> from_sq) & 1:
                bb[BK] &= ~(1 << from_sq)
                bb[BK] |= 1 << to_sq
                moved = True

        if not moved:
            return None
        return bb
