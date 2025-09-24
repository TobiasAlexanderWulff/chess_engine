from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

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
    # internal move history for make/unmake (Plan 3)
    _history: List[Tuple] = field(default_factory=list, repr=False)

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
            # Bishops
            bishops = self.bb[WB]
            while bishops:
                lsb = bishops & -bishops
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_white >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_black >> to_sq) & 1:
                            break
                bishops ^= lsb
            # Rooks
            rooks = self.bb[WR]
            while rooks:
                lsb = rooks & -rooks
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_white >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_black >> to_sq) & 1:
                            break
                rooks ^= lsb
            # Queens
            queens = self.bb[WQ]
            while queens:
                lsb = queens & -queens
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, -1),
                    (1, -1),
                    (-1, 1),
                    (1, 1),
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_white >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_black >> to_sq) & 1:
                            break
                queens ^= lsb
            # En passant captures (destination is ep target)
            if self.ep_square is not None:
                ep = self.ep_square
                ep_file = ep % 8
                # Origins that could capture onto ep square
                if ep_file > 0:
                    o = ep - 9
                    if o >= 0 and ((self.bb[WP] >> o) & 1):
                        moves.append(Move(o, ep))
                if ep_file < 7:
                    o = ep - 7
                    if o >= 0 and ((self.bb[WP] >> o) & 1):
                        moves.append(Move(o, ep))
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
                # Castling (white)
                # Precondition: king on e1 (square 4) and not in check
                if from_sq == 4 and not self._is_attacked(4, by_white=False):
                    # Kingside: rights K, squares f1(5) and g1(6) empty and not attacked
                    if (
                        "K" in self.castling
                        and not ((occ_all >> 5) & 1)
                        and not ((occ_all >> 6) & 1)
                    ):
                        if not self._is_attacked(5, by_white=False) and not self._is_attacked(
                            6, by_white=False
                        ):
                            moves.append(Move(4, 6))
                    # Queenside: rights Q, squares d1(3), c1(2), b1(1) empty; d1 and c1 not attacked
                    if (
                        "Q" in self.castling
                        and not ((occ_all >> 3) & 1)
                        and not ((occ_all >> 2) & 1)
                        and not ((occ_all >> 1) & 1)
                    ):
                        if not self._is_attacked(3, by_white=False) and not self._is_attacked(
                            2, by_white=False
                        ):
                            moves.append(Move(4, 2))
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
            # Bishops
            bishops = self.bb[BB]
            while bishops:
                lsb = bishops & -bishops
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_black >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_white >> to_sq) & 1:
                            break
                bishops ^= lsb
            # Rooks
            rooks = self.bb[BR]
            while rooks:
                lsb = rooks & -rooks
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_black >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_white >> to_sq) & 1:
                            break
                rooks ^= lsb
            # Queens
            queens = self.bb[BQ]
            while queens:
                lsb = queens & -queens
                from_sq = lsb.bit_length() - 1
                f = from_sq % 8
                r = from_sq // 8
                for df, dr in (
                    (-1, -1),
                    (1, -1),
                    (-1, 1),
                    (1, 1),
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    tf, tr = f, r
                    while True:
                        tf += df
                        tr += dr
                        if not (0 <= tf < 8 and 0 <= tr < 8):
                            break
                        to_sq = tr * 8 + tf
                        if (occ_black >> to_sq) & 1:
                            break
                        moves.append(Move(from_sq, to_sq))
                        if (occ_white >> to_sq) & 1:
                            break
                queens ^= lsb
            # En passant captures (destination is ep target)
            if self.ep_square is not None:
                ep = self.ep_square
                ep_file = ep % 8
                if ep_file < 7:
                    o = ep + 9
                    if o <= 63 and ((self.bb[BP] >> o) & 1):
                        moves.append(Move(o, ep))
                if ep_file > 0:
                    o = ep + 7
                    if o <= 63 and ((self.bb[BP] >> o) & 1):
                        moves.append(Move(o, ep))
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
                # Castling (black) if king on e8 (60) and not in check
                if from_sq == 60 and not self._is_attacked(60, by_white=True):
                    # Kingside: rights k, squares f8(61), g8(62) empty and not attacked
                    if (
                        "k" in self.castling
                        and not ((occ_all >> 61) & 1)
                        and not ((occ_all >> 62) & 1)
                    ):
                        if not self._is_attacked(61, by_white=True) and not self._is_attacked(
                            62, by_white=True
                        ):
                            moves.append(Move(60, 62))
                    # Queenside: rights q, squares d8(59), c8(58), b8(57) empty; d8 and c8 not attacked
                    if (
                        "q" in self.castling
                        and not ((occ_all >> 59) & 1)
                        and not ((occ_all >> 58) & 1)
                        and not ((occ_all >> 57) & 1)
                    ):
                        if not self._is_attacked(59, by_white=True) and not self._is_attacked(
                            58, by_white=True
                        ):
                            moves.append(Move(60, 58))

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
        """Return a new Board with `move` applied if legal.

        - Validates the move against generated legal moves.
        - Applies move using in-place mechanics on a cloned board.
        - Keeps the original board unchanged (immutable API surface).
        """
        legal = self.generate_legal_moves()
        # Compare by structural equality (from, to, promotion)
        if not any(
            (m.from_sq == move.from_sq and m.to_sq == move.to_sq and m.promotion == move.promotion)
            for m in legal
        ):
            raise ValueError("illegal move")

        # Clone board state
        new_board = Board(
            bb=list(self.bb),
            side_to_move=self.side_to_move,
            castling=self.castling,
            ep_square=self.ep_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        )
        # Apply move in-place on the clone
        new_board.make_move(move)
        return new_board

    # --- Plan 3 scaffolding ---
    def make_move(self, move: Move) -> None:
        """Apply `move` to this board in-place with reversible state.

        Supports: normal moves, captures, promotions, en passant, and castling.
        """
        from_sq, to_sq = move.from_sq, move.to_sq
        is_white = self.side_to_move == "w"

        # Determine moved piece type
        moved_piece = None
        own_indices = (WP, WN, WB, WR, WQ, WK) if is_white else (BP, BN, BB, BR, BQ, BK)
        for p in own_indices:
            if (self.bb[p] >> from_sq) & 1:
                moved_piece = p
                break
        if moved_piece is None:
            raise ValueError("no piece to move from from_sq")

        # Determine capture (including en passant)
        captured_piece = None
        ep_capture_sq: Optional[int] = None
        if moved_piece in (WP, BP) and self.ep_square is not None and to_sq == self.ep_square:
            # en passant
            if is_white and (to_sq - from_sq) in (7, 9):
                ep_capture_sq = to_sq - 8
                captured_piece = BP
            elif (not is_white) and (from_sq - to_sq) in (7, 9):
                ep_capture_sq = to_sq + 8
                captured_piece = WP
        else:
            # normal capture: detect which opponent piece is on to_sq
            opp_indices = (BP, BN, BB, BR, BQ, BK) if is_white else (WP, WN, WB, WR, WQ, WK)
            for p in opp_indices:
                if (self.bb[p] >> to_sq) & 1:
                    captured_piece = p
                    break

        # Save previous state for unmake
        prev_state = (
            move,
            moved_piece,
            captured_piece,
            ep_capture_sq,
            self.ep_square,
            self.castling,
            self.halfmove_clock,
            self.fullmove_number,
        )
        self._history.append(prev_state)

        # Update halfmove clock
        if moved_piece in (WP, BP) or captured_piece is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Update fullmove number after black moves
        if not is_white:
            self.fullmove_number += 1

        # Update castling rights if king or rook moves/captured
        self._update_castling_rights_on_move(moved_piece, from_sq, to_sq, captured_piece)

        # Clear en passant by default; set only on double pawn pushes
        self.ep_square = None

        # Bitboard updates: move piece, handle captures and promotion/en passant
        # Clear from square on moved piece
        self.bb[moved_piece] &= ~(1 << from_sq)

        # Remove captured piece
        if captured_piece is not None:
            if ep_capture_sq is not None:
                self.bb[captured_piece] &= ~(1 << ep_capture_sq)
            else:
                self.bb[captured_piece] &= ~(1 << to_sq)

        # Place moved piece (or promoted piece); handle castling rook move
        if moved_piece == WP:
            if move.promotion:
                promo_map = {"q": WQ, "r": WR, "b": WB, "n": WN}
                self.bb[promo_map[move.promotion]] |= 1 << to_sq
            else:
                self.bb[WP] |= 1 << to_sq
                # Double push sets ep target
                if to_sq - from_sq == 16:
                    self.ep_square = from_sq + 8
        elif moved_piece == BP:
            if move.promotion:
                promo_map = {"q": BQ, "r": BR, "b": BB, "n": BN}
                self.bb[promo_map[move.promotion]] |= 1 << to_sq
            else:
                self.bb[BP] |= 1 << to_sq
                if from_sq - to_sq == 16:
                    self.ep_square = from_sq - 8
        else:
            # King including castling rook movement
            if moved_piece == WK and abs(to_sq - from_sq) == 2:
                # Move rook as well
                if to_sq == 6:  # e1->g1, h1->f1
                    self.bb[WR] &= ~(1 << 7)
                    self.bb[WR] |= 1 << 5
                else:  # e1->c1, a1->d1
                    self.bb[WR] &= ~(1 << 0)
                    self.bb[WR] |= 1 << 3
            elif moved_piece == BK and abs(to_sq - from_sq) == 2:
                if to_sq == 62:  # e8->g8, h8->f8
                    self.bb[BR] &= ~(1 << 63)
                    self.bb[BR] |= 1 << 61
                else:  # e8->c8, a8->d8
                    self.bb[BR] &= ~(1 << 56)
                    self.bb[BR] |= 1 << 59
            self.bb[moved_piece] |= 1 << to_sq

        # Toggle side to move
        self.side_to_move = "b" if is_white else "w"

    def unmake_move(self, move: Move) -> None:
        """Undo the last move in-place, restoring previous state.

        Scaffolding stub for Plan 3. Requires a move/state stack to restore:
        - moved/captured/promoted pieces, castling rights, ep square, counters
        - hash and any incremental caches
        """
        if not self._history:
            raise ValueError("no move to unmake")
        (
            _mv,
            moved_piece,
            captured_piece,
            ep_capture_sq,
            prev_ep,
            prev_castling,
            prev_halfmove,
            prev_fullmove,
        ) = self._history.pop()

        from_sq, to_sq = move.from_sq, move.to_sq

        # Toggle side back
        self.side_to_move = "w" if self.side_to_move == "b" else "b"

        # Restore counters and rights
        self.ep_square = prev_ep
        self.castling = prev_castling
        self.halfmove_clock = prev_halfmove
        self.fullmove_number = prev_fullmove

        # Undo piece placement
        # Remove piece from destination (or promoted piece) and place back on from_sq
        if moved_piece == WP:
            if move.promotion:
                promo_map = {"q": WQ, "r": WR, "b": WB, "n": WN}
                self.bb[promo_map[move.promotion]] &= ~(1 << to_sq)
                self.bb[WP] |= 1 << from_sq
            else:
                self.bb[WP] &= ~(1 << to_sq)
                self.bb[WP] |= 1 << from_sq
        elif moved_piece == BP:
            if move.promotion:
                promo_map = {"q": BQ, "r": BR, "b": BB, "n": BN}
                self.bb[promo_map[move.promotion]] &= ~(1 << to_sq)
                self.bb[BP] |= 1 << from_sq
            else:
                self.bb[BP] &= ~(1 << to_sq)
                self.bb[BP] |= 1 << from_sq
        else:
            # Handle castling rook rollback
            if moved_piece == WK and abs(to_sq - from_sq) == 2:
                if to_sq == 6:  # undo rook f1->h1
                    self.bb[WR] &= ~(1 << 5)
                    self.bb[WR] |= 1 << 7
                else:  # to_sq == 2: undo rook d1->a1
                    self.bb[WR] &= ~(1 << 3)
                    self.bb[WR] |= 1 << 0
            elif moved_piece == BK and abs(to_sq - from_sq) == 2:
                if to_sq == 62:  # undo rook f8->h8
                    self.bb[BR] &= ~(1 << 61)
                    self.bb[BR] |= 1 << 63
                else:  # to_sq == 58: undo rook d8->a8
                    self.bb[BR] &= ~(1 << 59)
                    self.bb[BR] |= 1 << 56
            self.bb[moved_piece] &= ~(1 << to_sq)
            self.bb[moved_piece] |= 1 << from_sq

        # Restore captured piece
        if captured_piece is not None:
            if ep_capture_sq is not None:
                self.bb[captured_piece] |= 1 << ep_capture_sq
            else:
                self.bb[captured_piece] |= 1 << to_sq

    def _update_castling_rights_on_move(
        self, moved_piece: int, from_sq: int, to_sq: int, captured_piece: Optional[int]
    ) -> None:
        """Update castling string based on king/rook moves and rook captures."""
        rights = set(self.castling)
        # White king/rook moves
        if moved_piece == WK:
            rights.discard("K")
            rights.discard("Q")
        elif moved_piece == WR:
            if from_sq == 0:
                rights.discard("Q")
            elif from_sq == 7:
                rights.discard("K")
        # Black king/rook moves
        if moved_piece == BK:
            rights.discard("k")
            rights.discard("q")
        elif moved_piece == BR:
            if from_sq == 56:
                rights.discard("q")
            elif from_sq == 63:
                rights.discard("k")
        # Rook captured on original squares
        if captured_piece == WR and to_sq in (0, 7):
            if to_sq == 0:
                rights.discard("Q")
            else:
                rights.discard("K")
        if captured_piece == BR and to_sq in (56, 63):
            if to_sq == 56:
                rights.discard("q")
            else:
                rights.discard("k")
        self.castling = "".join(c for c in "KQkq" if c in rights)

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

        Supports: pawns (incl. promotions and en passant), knights, king,
        bishops, rooks, and queens.
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
                # En passant capture (destination equals ep target): remove pawn behind target
                if (
                    self.ep_square is not None
                    and to_sq == self.ep_square
                    and (to_sq - from_sq) in (7, 9)
                ):
                    cap_sq = to_sq - 8
                    bb[BP] &= ~(1 << cap_sq)
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
                # Handle rook relocation for castling in simulation
                if abs(to_sq - from_sq) == 2:
                    if to_sq == 6:  # white kingside e1->g1, rook h1->f1
                        bb[WR] &= ~(1 << 7)
                        bb[WR] |= 1 << 5
                    elif to_sq == 2:  # white queenside e1->c1, rook a1->d1
                        bb[WR] &= ~(1 << 0)
                        bb[WR] |= 1 << 3
                moved = True
            elif (bb[WB] >> from_sq) & 1:
                bb[WB] &= ~(1 << from_sq)
                bb[WB] |= 1 << to_sq
                moved = True
            elif (bb[WR] >> from_sq) & 1:
                bb[WR] &= ~(1 << from_sq)
                bb[WR] |= 1 << to_sq
                moved = True
            elif (bb[WQ] >> from_sq) & 1:
                bb[WQ] &= ~(1 << from_sq)
                bb[WQ] |= 1 << to_sq
                moved = True
        else:
            if (bb[BP] >> from_sq) & 1:
                bb[BP] &= ~(1 << from_sq)
                if (
                    self.ep_square is not None
                    and to_sq == self.ep_square
                    and (from_sq - to_sq) in (7, 9)
                ):
                    cap_sq = to_sq + 8
                    bb[WP] &= ~(1 << cap_sq)
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
                if abs(to_sq - from_sq) == 2:
                    if to_sq == 62:  # black kingside e8->g8, rook h8->f8
                        bb[BR] &= ~(1 << 63)
                        bb[BR] |= 1 << 61
                    elif to_sq == 58:  # black queenside e8->c8, rook a8->d8
                        bb[BR] &= ~(1 << 56)
                        bb[BR] |= 1 << 59
                moved = True
            elif (bb[BB] >> from_sq) & 1:
                bb[BB] &= ~(1 << from_sq)
                bb[BB] |= 1 << to_sq
                moved = True
            elif (bb[BR] >> from_sq) & 1:
                bb[BR] &= ~(1 << from_sq)
                bb[BR] |= 1 << to_sq
                moved = True
            elif (bb[BQ] >> from_sq) & 1:
                bb[BQ] &= ~(1 << from_sq)
                bb[BQ] |= 1 << to_sq
                moved = True

        if not moved:
            return None
        return bb

    # --- Status helpers ---
    def in_check(self, side: Optional[str] = None) -> bool:
        """Return True if `side` (default: current side to move) is in check."""
        s = self.side_to_move if side is None else side
        if s not in ("w", "b"):
            raise ValueError("side must be 'w' or 'b'")
        if s == "w":
            king_bb = self.bb[WK]
            if king_bb == 0:
                return False
            ksq = (king_bb & -king_bb).bit_length() - 1
            return self._is_attacked(ksq, by_white=False)
        else:
            king_bb = self.bb[BK]
            if king_bb == 0:
                return False
            ksq = (king_bb & -king_bb).bit_length() - 1
            return self._is_attacked(ksq, by_white=True)

    def has_legal_moves(self) -> bool:
        """Return True if the side to move has at least one legal move."""
        return bool(self.generate_legal_moves())
