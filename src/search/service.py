from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time

from src.engine.game import Game
from src.engine.move import Move
from src.eval import evaluate
from src.engine.board import WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK


@dataclass
class SearchResult:
    best_move: Optional[Move]
    score_cp: Optional[int]
    mate_in: Optional[int]
    pv: List[Move]
    nodes: int
    depth: int
    time_ms: int


class SearchService:
    """Minimal search service interface.

    This stub will be implemented after legal move generation (Plan 4).
    """

    def search(self, game: Game, depth: int = 1, movetime_ms: Optional[int] = None) -> SearchResult:
        # Deterministic negamax alpha-beta with simple material evaluation and a transposition table.
        board = game.board
        nodes = 0

        @dataclass
        class TTEntry:
            key: int
            depth: int
            flag: str  # "EXACT", "LOWER", "UPPER"
            score: int
            best: Optional[Move]

        tt: Dict[int, TTEntry] = {}

        INF = 10_000_000

        def probe(alpha: int, beta: int, d: int) -> Optional[Tuple[int, Optional[Move]]]:
            e = tt.get(board.zobrist_hash)
            if e is None or e.depth < d:
                return None
            if e.flag == "EXACT":
                return e.score, e.best
            if e.flag == "LOWER" and e.score >= beta:
                return e.score, e.best
            if e.flag == "UPPER" and e.score <= alpha:
                return e.score, e.best
            return None

        def store(
            depth_left: int, score: int, alpha_orig: int, beta: int, best: Optional[Move]
        ) -> None:
            # Avoid polluting TT if we are out of time
            if movetime_ms is not None and time_up:
                return
            flag: str
            if score <= alpha_orig:
                flag = "UPPER"
            elif score >= beta:
                flag = "LOWER"
            else:
                flag = "EXACT"
            tt[board.zobrist_hash] = TTEntry(board.zobrist_hash, depth_left, flag, score, best)

        # Killer moves (two per ply) and history heuristic
        killers: Dict[int, List[Move]] = {}
        history: Dict[Tuple[str, int, int], int] = {}

        # Time control
        start = time.perf_counter()
        time_up = False

        def out_of_time() -> bool:
            nonlocal time_up
            if movetime_ms is None or time_up:
                return time_up
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if elapsed_ms >= movetime_ms:
                time_up = True
            return time_up

        def is_tt_equal(a: Optional[Move], b: Move) -> bool:
            return (
                a is not None
                and a.from_sq == b.from_sq
                and a.to_sq == b.to_sq
                and a.promotion == b.promotion
            )

        # --- SEE helpers ---
        def piece_on_square(sq: int) -> Optional[int]:
            for p in range(12):
                if (board.bb[p] >> sq) & 1:
                    return p
            return None

        def attackers_to_square(sq: int, occ: int, by_white: bool, removed_mask: int) -> int:
            attackers = 0
            f = sq % 8
            r = sq // 8
            # Pawns
            if by_white:
                if f > 0:
                    o = sq - 9
                    if o >= 0 and ((board.bb[WP] >> o) & 1) and not ((removed_mask >> o) & 1):
                        attackers |= 1 << o
                if f < 7:
                    o = sq - 7
                    if o >= 0 and ((board.bb[WP] >> o) & 1) and not ((removed_mask >> o) & 1):
                        attackers |= 1 << o
            else:
                if f < 7:
                    o = sq + 9
                    if o <= 63 and ((board.bb[BP] >> o) & 1) and not ((removed_mask >> o) & 1):
                        attackers |= 1 << o
                if f > 0:
                    o = sq + 7
                    if o <= 63 and ((board.bb[BP] >> o) & 1) and not ((removed_mask >> o) & 1):
                        attackers |= 1 << o
            # Knights
            for df, dr in ((-1, 2), (1, 2), (-2, 1), (2, 1), (-2, -1), (2, -1), (-1, -2), (1, -2)):
                tf = f + df
                tr = r + dr
                if 0 <= tf < 8 and 0 <= tr < 8:
                    o = tr * 8 + tf
                    if by_white:
                        if ((board.bb[WN] >> o) & 1) and not ((removed_mask >> o) & 1):
                            attackers |= 1 << o
                    else:
                        if ((board.bb[BN] >> o) & 1) and not ((removed_mask >> o) & 1):
                            attackers |= 1 << o
            # King
            for df, dr in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                tf = f + df
                tr = r + dr
                if 0 <= tf < 8 and 0 <= tr < 8:
                    o = tr * 8 + tf
                    if by_white:
                        if ((board.bb[WK] >> o) & 1) and not ((removed_mask >> o) & 1):
                            attackers |= 1 << o
                    else:
                        if ((board.bb[BK] >> o) & 1) and not ((removed_mask >> o) & 1):
                            attackers |= 1 << o

            # Sliders (bishops/rooks/queens)
            def ray_dirs(diagonals: bool) -> List[Tuple[int, int]]:
                return (
                    [(-1, -1), (1, -1), (-1, 1), (1, 1)]
                    if diagonals
                    else [(-1, 0), (1, 0), (0, -1), (0, 1)]
                )

            # Bishop-like
            for df, dr in ray_dirs(True):
                tf, tr = f, r
                while True:
                    tf += df
                    tr += dr
                    if not (0 <= tf < 8 and 0 <= tr < 8):
                        break
                    o = tr * 8 + tf
                    if (occ >> o) & 1:
                        if by_white:
                            if ((board.bb[WB] >> o) & 1 or (board.bb[WQ] >> o) & 1) and not (
                                (removed_mask >> o) & 1
                            ):
                                attackers |= 1 << o
                        else:
                            if ((board.bb[BB] >> o) & 1 or (board.bb[BQ] >> o) & 1) and not (
                                (removed_mask >> o) & 1
                            ):
                                attackers |= 1 << o
                        break
            # Rook-like
            for df, dr in ray_dirs(False):
                tf, tr = f, r
                while True:
                    tf += df
                    tr += dr
                    if not (0 <= tf < 8 and 0 <= tr < 8):
                        break
                    o = tr * 8 + tf
                    if (occ >> o) & 1:
                        if by_white:
                            if ((board.bb[WR] >> o) & 1 or (board.bb[WQ] >> o) & 1) and not (
                                (removed_mask >> o) & 1
                            ):
                                attackers |= 1 << o
                        else:
                            if ((board.bb[BR] >> o) & 1 or (board.bb[BQ] >> o) & 1) and not (
                                (removed_mask >> o) & 1
                            ):
                                attackers |= 1 << o
                        break
            return attackers

        def see(move: Move) -> int:
            # Only for captures; returns net material result (centipawns)
            to_sq = move.to_sq
            from_sq = move.from_sq
            side_white = board.side_to_move == "w"
            # Occupancy
            occ = 0
            for b in board.bb:
                occ |= b
            # Identify victim
            if board.ep_square is not None and move.to_sq == board.ep_square:
                victim_sq = to_sq - 8 if side_white else to_sq + 8
                victim_piece = BP if side_white else WP
            else:
                victim_sq = to_sq
                vp = piece_on_square(victim_sq)
                if vp is None:
                    return 0
                victim_piece = vp

            piece_vals = [100, 320, 330, 500, 900, 20000, 100, 320, 330, 500, 900, 20000]
            victim_value = piece_vals[victim_piece]

            # Determine initial attacker piece type (handle promotion)
            attacker_piece = piece_on_square(from_sq)
            if attacker_piece is None:
                return 0

            gain: List[int] = [victim_value]
            removed_mask = 0
            # Remove victim
            occ &= ~(1 << victim_sq)
            removed_mask |= 1 << victim_sq
            # Remove attacker from origin; occupy target
            occ &= ~(1 << from_sq)
            removed_mask |= 1 << from_sq
            occ |= 1 << to_sq

            curr_occ_val = piece_vals[attacker_piece]
            color_white = not side_white
            while True:
                atk_mask = attackers_to_square(to_sq, occ, color_white, removed_mask)
                if atk_mask == 0:
                    break
                # Choose least valuable attacker
                best_sq = -1
                best_piece = None
                best_val = 10**9
                mask = atk_mask
                while mask:
                    lsb = mask & -mask
                    sq = lsb.bit_length() - 1
                    p = piece_on_square(sq)
                    if p is not None:
                        val = piece_vals[p]
                        if val < best_val:
                            best_val = val
                            best_sq = sq
                            best_piece = p
                    mask ^= lsb
                if best_sq == -1 or best_piece is None:
                    break
                gain.append(curr_occ_val - gain[-1])
                # Remove attacker from its square
                occ &= ~(1 << best_sq)
                removed_mask |= 1 << best_sq
                # New occupant is this capturing piece
                curr_occ_val = piece_vals[best_piece]
                color_white = not color_white

            # Backward propagation (standard swap list recurrence)
            for i in range(len(gain) - 2, -1, -1):
                gain[i] = -max(-gain[i], gain[i + 1])
            return gain[0]

        def negamax(d: int, alpha: int, beta: int, ply: int = 0) -> Tuple[int, List[Move]]:
            nonlocal nodes
            nodes += 1

            # Leaf or terminal
            if d == 0 or out_of_time():
                base = evaluate(board)
                score = base if board.side_to_move == "w" else -base
                return score, []

            # TT probe
            hit = probe(alpha, beta, d)
            tt_move: Optional[Move] = None
            if hit is not None:
                score, m = hit
                # We cannot recover PV reliably from table; use cutoff only
                # If an EXACT value, return it directly
                if (
                    d > 0
                    and tt.get(board.zobrist_hash, None)
                    and tt[board.zobrist_hash].flag == "EXACT"
                ):
                    return score, ([m] if m else [])
                # Otherwise continue but prefer the stored move for ordering
                tt_move = m

            legal = board.generate_legal_moves()
            if not legal:
                # No moves: treat as draw (0). Mate/stalemate detection omitted for simplicity.
                return 0, []

            # Move ordering: TT, captures, killers, history
            # Precompute opponent occupancy to detect captures cheaply
            if board.side_to_move == "w":
                occ_opp = (
                    board.bb[6]
                    | board.bb[7]
                    | board.bb[8]
                    | board.bb[9]
                    | board.bb[10]
                    | board.bb[11]
                )
            else:
                occ_opp = (
                    board.bb[0]
                    | board.bb[1]
                    | board.bb[2]
                    | board.bb[3]
                    | board.bb[4]
                    | board.bb[5]
                )

            killer_list = killers.get(ply, [])

            # Piece values for MVV-LVA (centipawns)
            piece_vals = [
                100,
                320,
                330,
                500,
                900,
                20000,  # white P N B R Q K
                100,
                320,
                330,
                500,
                900,
                20000,  # black P N B R Q K
            ]

            def attacker_piece_index(mv: Move) -> Optional[int]:
                # Determine which piece is moving from the origin square
                if board.side_to_move == "w":
                    own = (WP, WN, WB, WR, WQ, WK)
                else:
                    own = (BP, BN, BB, BR, BQ, BK)
                for p in own:
                    if (board.bb[p] >> mv.from_sq) & 1:
                        return p
                return None

            def victim_piece_index(mv: Move) -> Optional[int]:
                # Determine captured piece on destination (or EP pawn)
                if board.ep_square is not None and mv.to_sq == board.ep_square:
                    return BP if board.side_to_move == "w" else WP
                if board.side_to_move == "w":
                    opp = (BP, BN, BB, BR, BQ, BK)
                else:
                    opp = (WP, WN, WB, WR, WQ, WK)
                for p in opp:
                    if (board.bb[p] >> mv.to_sq) & 1:
                        return p
                return None

            def move_score(mv: Move) -> int:
                score = 0
                if is_tt_equal(tt_move, mv):
                    score += 1_000_000
                # capture detection: destination occupied by opponent or ep target
                is_capture = ((occ_opp >> mv.to_sq) & 1) == 1 or (
                    board.ep_square is not None and mv.to_sq == board.ep_square
                )
                if is_capture:
                    # MVV-LVA: prioritize higher value victims and lower value attackers
                    att = attacker_piece_index(mv)
                    vic = victim_piece_index(mv)
                    v = piece_vals[vic] if vic is not None else 0
                    a = piece_vals[att] if att is not None else 0
                    score += 600_000 + (v * 10 - a)
                # killer moves (quiet only)
                if not is_capture:
                    for idx, km in enumerate(killer_list[:2]):
                        if is_tt_equal(km, mv):
                            score += 400_000 - idx * 1000
                            break
                    # history bonus
                    score += history.get((board.side_to_move, mv.from_sq, mv.to_sq), 0)
                return score

            legal.sort(key=move_score, reverse=True)

            best_score = -INF
            best_line: List[Move] = []
            alpha_orig = alpha
            best_move: Optional[Move] = None

            for m in legal:
                # Simple SEE gate: prune clearly losing captures at shallow depths
                # Only consider captures, and only when remaining depth is small
                is_capture = ((occ_opp >> m.to_sq) & 1) == 1 or (
                    board.ep_square is not None and m.to_sq == board.ep_square
                )
                if is_capture and d <= 2:
                    if see(m) < 0:
                        continue
                board.make_move(m)
                child_score, child_pv = negamax(d - 1, -beta, -alpha, ply + 1)
                score = -child_score
                board.unmake_move(m)

                if score > best_score:
                    best_score = score
                    best_line = [m] + child_pv
                    best_move = m
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    # Fail-high cutoff
                    store(d, best_score, alpha_orig, beta, best_move)
                    # Update killers/history for quiet cutoffs
                    # Re-detect capture on this move in current position context
                    is_capture = ((occ_opp >> m.to_sq) & 1) == 1 or (
                        board.ep_square is not None and m.to_sq == board.ep_square
                    )
                    if not is_capture:
                        kl = killers.get(ply, [])
                        # Insert as primary killer if new
                        if not any(is_tt_equal(km, m) for km in kl):
                            kl = [m] + kl
                            killers[ply] = kl[:2]
                        # History bonus scaled by depth
                        key = (board.side_to_move, m.from_sq, m.to_sq)
                        history[key] = history.get(key, 0) + d * d
                    return best_score, best_line

            store(d, best_score, alpha_orig, beta, best_move)
            return best_score, best_line

        # Iterative deepening from 1..depth with basic time control
        last_score = 0
        last_pv: List[Move] = []
        completed_depth = 0
        for d in range(1, max(1, depth) + 1):
            score, pv = negamax(d, -INF, INF)
            # If time ran out during this iteration, keep previous completed result
            if time_up:
                break
            last_score, last_pv, completed_depth = score, pv, d

        best_move = (
            last_pv[0] if last_pv else (game.legal_moves()[0] if game.legal_moves() else None)
        )
        return SearchResult(
            best_move=best_move,
            score_cp=last_score,
            mate_in=None,
            pv=last_pv,
            nodes=nodes,
            depth=completed_depth,
            time_ms=int((time.perf_counter() - start) * 1000),
        )
