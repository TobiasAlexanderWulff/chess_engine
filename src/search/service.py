from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import time

from src.engine.game import Game
from src.engine.move import Move
from src.eval import evaluate
from src.engine.board import WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK
from src.engine.zobrist import compute_hash_from_scratch


@dataclass
class SearchResult:
    best_move: Optional[Move]
    score_cp: Optional[int]
    mate_in: Optional[int]
    pv: List[Move]
    nodes: int
    qnodes: int
    tt_hits: int
    fail_high: int
    fail_low: int
    tt_probes: int
    re_searches: int
    iters: List[Dict[str, int]]
    tt_exact_hits: int
    tt_lower_hits: int
    tt_upper_hits: int
    tt_stores: int
    tt_replacements: int
    tt_size: int
    depth: int
    time_ms: int
    seldepth: int
    hashfull: int


class SearchService:
    """Minimal search service interface.

    This stub will be implemented after legal move generation (Plan 4).
    """

    def search(
        self,
        game: Game,
        depth: int = 1,
        movetime_ms: Optional[int] = None,
        tt_max_entries: Optional[int] = None,
        *,
        enable_pvs: bool = True,
        enable_nmp: bool = True,
        enable_lmr: bool = True,
        enable_futility: bool = True,
        on_iter: Optional[
            Callable[
                [
                    int,  # depth
                    int,  # time_ms since start
                    int,  # nodes (cumulative)
                    int,  # qnodes (cumulative)
                    Optional[int],  # score_cp
                    Optional[int],  # mate_in
                    List[Move],  # pv
                    int,  # seldepth
                    int,  # tt_hits (cumulative)
                    int,  # hashfull (permille)
                ],
                None,
            ]
        ] = None,
    ) -> SearchResult:
        # Deterministic negamax alpha-beta with quiescence, simple material evaluation,
        # and a transposition table. Includes terminal scoring (mate/stalemate/draw).
        board = game.board
        nodes = 0
        qnodes = 0
        # Repetition tracking: seed counts from the game so threefold inside search is detected
        rep_counts: Dict[int, int] = dict(getattr(game, "repetition", {}))
        tt_probes = 0
        tt_hits = 0
        tt_exact_hits = 0
        tt_lower_hits = 0
        tt_upper_hits = 0
        tt_stores = 0
        tt_replacements = 0

        @dataclass
        class TTEntry:
            key: int
            depth: int
            flag: str  # "EXACT", "LOWER", "UPPER"
            score: int
            best: Optional[Move]
            gen: int

        tt: Dict[int, TTEntry] = {}
        generation = 0

        INF = 10_000_000
        MATE_SCORE = 1_000_000  # mate scores are within +/- MATE_SCORE window
        seldepth_iter = 0
        seldepth_global = 0

        def probe(alpha: int, beta: int, d: int) -> Optional[Tuple[int, Optional[Move]]]:
            nonlocal tt_probes, tt_hits, tt_exact_hits, tt_lower_hits, tt_upper_hits
            tt_probes += 1
            e = tt.get(board.zobrist_hash)
            if e is None or e.depth < d:
                return None
            if e.flag == "EXACT":
                tt_hits += 1
                tt_exact_hits += 1
                return e.score, e.best
            if e.flag == "LOWER" and e.score >= beta:
                tt_hits += 1
                tt_lower_hits += 1
                return e.score, e.best
            if e.flag == "UPPER" and e.score <= alpha:
                tt_hits += 1
                tt_upper_hits += 1
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
            nonlocal tt_stores, tt_replacements
            key = board.zobrist_hash
            new_entry = TTEntry(key, depth_left, flag, score, best, generation)
            existing = tt.get(key)
            if existing is None:
                tt[key] = new_entry
                tt_stores += 1
            else:
                if depth_left > existing.depth or existing.gen + 2 <= generation:
                    tt[key] = new_entry
                    tt_replacements += 1
                else:
                    # keep existing
                    pass

            # Enforce optional TT size limit by evicting oldest/shallowest entries
            if tt_max_entries is not None and tt_max_entries > 0 and len(tt) > tt_max_entries:
                # Build a list of (gen, depth, key) and evict the worst until size fits
                victims = sorted(((e.gen, e.depth, k) for k, e in tt.items()))
                # Number to evict to get at or under the cap
                to_evict = len(tt) - tt_max_entries
                for _ in range(to_evict):
                    if not victims:
                        break
                    _, _, k = victims.pop(0)
                    # Avoid evicting the just-stored key if possible
                    if k == key and victims:
                        _, _, k = victims.pop(0)
                    tt.pop(k, None)

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
            nonlocal nodes, seldepth_iter, seldepth_global
            if ply > seldepth_iter:
                seldepth_iter = ply
            if ply > seldepth_global:
                seldepth_global = ply
            nodes += 1

            # Leaf or terminal
            if out_of_time():
                base = evaluate(board)
                score = base if board.side_to_move == "w" else -base
                return score, []

            # 50-move rule
            if board.halfmove_clock >= 100:
                return 0, []

            # Threefold repetition (counts include current game history)
            if rep_counts.get(board.zobrist_hash, 0) >= 3:
                return 0, []

            # In-check extension: extend search by 1 ply when side to move is in check
            in_check_now = board.in_check()
            if d > 0 and in_check_now:
                d += 1

            # No legal moves: mate or stalemate
            legal_precheck = board.generate_legal_moves()
            if not legal_precheck:
                if in_check_now:
                    # Checkmated: distance-to-mate scores prefer quicker mates
                    return -MATE_SCORE + ply, []
                # Stalemate
                return 0, []

            # Depth horizon: switch to quiescence
            if d == 0:
                return qsearch(alpha, beta, ply)

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

            # Null-move pruning (conservative): when not in check, try a null move
            # to prove a cutoff. Skip near-mate scores and zugzwang-like material.
            if enable_nmp and d >= 3 and not in_check_now and beta < MATE_SCORE - 1024:
                # Zugzwang guard: require at least one non-pawn piece for side to move
                if board.side_to_move == "w":
                    non_pawn = board.bb[WN] | board.bb[WB] | board.bb[WR] | board.bb[WQ]
                else:
                    non_pawn = board.bb[BN] | board.bb[BB] | board.bb[BR] | board.bb[BQ]
                if non_pawn != 0:
                    prev_stm = board.side_to_move
                    prev_ep = board.ep_square
                    prev_hash = board.zobrist_hash
                    # Make null move: swap side, clear ep square, recompute hash
                    board.side_to_move = "b" if board.side_to_move == "w" else "w"
                    board.ep_square = None
                    board.zobrist_hash = compute_hash_from_scratch(board)

                    R = 2
                    null_score, _ = negamax(d - 1 - R, -beta, -beta + 1, ply + 1)
                    score_nm = -null_score

                    # Undo null move
                    board.side_to_move = prev_stm
                    board.ep_square = prev_ep
                    board.zobrist_hash = prev_hash

                    if score_nm >= beta:
                        return beta, []

            legal = legal_precheck

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
            # Stand-pat for futility thresholds (side to move perspective)
            base_eval = evaluate(board)
            stand_pat = base_eval if board.side_to_move == "w" else -base_eval

            for idx, m in enumerate(legal):
                # Simple SEE gate: prune clearly losing captures at shallow depths
                # Only consider captures, and only when remaining depth is small
                is_capture = ((occ_opp >> m.to_sq) & 1) == 1 or (
                    board.ep_square is not None and m.to_sq == board.ep_square
                )
                if is_capture and d <= 2:
                    if see(m) < 0:
                        continue
                # Futility pruning at the horizon (very conservative)
                # Skip quiet moves unlikely to raise alpha at depth 1
                if (
                    enable_futility
                    and d == 1
                    and not in_check_now
                    and not is_capture
                    and m.promotion is None
                    and (stand_pat + 100) <= alpha
                ):
                    # Guard: if the move gives check, do not prune
                    board.make_move(m)
                    gives_check = board.in_check()
                    board.unmake_move(m)
                    if not gives_check:
                        continue

                board.make_move(m)
                # Increment repetition count for child position
                child_hash = board.zobrist_hash
                rep_counts[child_hash] = rep_counts.get(child_hash, 0) + 1

                # Principal Variation Search (PVS)
                if not enable_pvs or idx == 0:
                    # Full window for the first move
                    child_score, child_pv = negamax(d - 1, -beta, -alpha, ply + 1)
                    score = -child_score
                else:
                    # Zero-window probe for subsequent moves
                    search_depth = d - 1
                    # Apply a conservative LMR reduction on the probe for late quiet moves
                    if (
                        enable_lmr
                        and d >= 3
                        and not in_check_now
                        and not is_capture
                        and m.promotion is None
                        and idx >= 4
                    ):
                        search_depth -= 1
                    zw_score, child_pv = negamax(search_depth, -alpha - 1, -alpha, ply + 1)
                    score = -zw_score
                    if score > alpha:
                        # Re-search at full depth, full window
                        child_score, child_pv = negamax(d - 1, -beta, -alpha, ply + 1)
                        score = -child_score
                board.unmake_move(m)
                # Decrement repetition count for child
                cnt = rep_counts.get(child_hash, 0)
                if cnt <= 1:
                    rep_counts.pop(child_hash, None)
                else:
                    rep_counts[child_hash] = cnt - 1

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

        def qsearch(alpha: int, beta: int, ply: int) -> Tuple[int, List[Move]]:
            nonlocal nodes, qnodes, seldepth_iter, seldepth_global
            if ply > seldepth_iter:
                seldepth_iter = ply
            if ply > seldepth_global:
                seldepth_global = ply
            nodes += 1
            qnodes += 1

            # Stand-pat evaluation
            stand_pat = evaluate(board)
            stand_pat = stand_pat if board.side_to_move == "w" else -stand_pat

            # 50-move rule and repetition draw checks at quiescence entry
            if board.halfmove_clock >= 100:
                return 0, []
            if rep_counts.get(board.zobrist_hash, 0) >= 3:
                return 0, []

            # Immediate terminal states (no legal moves)
            legal = board.generate_legal_moves()
            if not legal:
                if board.in_check():
                    return -MATE_SCORE + ply, []
                return 0, []

            # If not in check, we can consider stand-pat cutoff
            if not board.in_check():
                if stand_pat >= beta:
                    return stand_pat, []
                if stand_pat > alpha:
                    alpha = stand_pat

            # Precompute opponent occupancy to filter captures
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

            # Filter to captures (and en passant)
            captures: List[Move] = []
            for m in legal:
                is_capture = ((occ_opp >> m.to_sq) & 1) == 1 or (
                    board.ep_square is not None and m.to_sq == board.ep_square
                )
                if is_capture or board.in_check():
                    captures.append(m)

            if not captures:
                return alpha, []

            # Use simple MVV-LVA ordering for captures
            piece_vals = [100, 320, 330, 500, 900, 20000] * 2

            def attacker_piece_index(mv: Move) -> Optional[int]:
                if board.side_to_move == "w":
                    own = (WP, WN, WB, WR, WQ, WK)
                else:
                    own = (BP, BN, BB, BR, BQ, BK)
                for p in own:
                    if (board.bb[p] >> mv.from_sq) & 1:
                        return p
                return None

            def victim_piece_index(mv: Move) -> Optional[int]:
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

            def cap_score(mv: Move) -> int:
                att = attacker_piece_index(mv)
                vic = victim_piece_index(mv)
                v = piece_vals[vic] if vic is not None else 0
                a = piece_vals[att] if att is not None else 0
                return v * 10 - a

            captures.sort(key=cap_score, reverse=True)

            best_line: List[Move] = []
            for m in captures:
                board.make_move(m)
                # repetition accounting
                child_hash = board.zobrist_hash
                rep_counts[child_hash] = rep_counts.get(child_hash, 0) + 1
                score, pv = qsearch(-beta, -alpha, ply + 1)
                score = -score
                board.unmake_move(m)
                # decrement
                cnt = rep_counts.get(child_hash, 0)
                if cnt <= 1:
                    rep_counts.pop(child_hash, None)
                else:
                    rep_counts[child_hash] = cnt - 1
                if score > alpha:
                    alpha = score
                    best_line = [m] + pv
                    if alpha >= beta:
                        break
            return alpha, best_line

        # Iterative deepening from 1..depth with basic time control
        last_score = 0
        last_pv: List[Move] = []
        completed_depth = 0
        fail_high = 0
        fail_low = 0
        re_searches = 0
        iters: List[Dict[str, int]] = []

        prev_nodes = 0
        prev_qnodes = 0
        prev_fail_high = 0
        prev_fail_low = 0

        BASE_WINDOW = 50  # aspiration window in centipawns

        def in_mate_window(sc: int) -> bool:
            return abs(sc) >= MATE_SCORE - 512

        for d in range(1, max(1, depth) + 1):
            generation += 1
            seldepth_iter = 0
            iter_start = time.perf_counter()
            if d == 1 or in_mate_window(last_score):
                score, pv = negamax(d, -INF, INF)
                # Record iteration stats even if time ran out during this iteration
                iters.append(
                    {
                        "depth": d,
                        "time_ms": int((time.perf_counter() - iter_start) * 1000),
                        "nodes": nodes - prev_nodes,
                        "qnodes": qnodes - prev_qnodes,
                        "fail_high": fail_high - prev_fail_high,
                        "fail_low": fail_low - prev_fail_low,
                    }
                )
                # Streaming callback with cumulative metrics
                if on_iter is not None:
                    elapsed_ms_total = int((time.perf_counter() - start) * 1000)
                    # Derive mate_in if within mate window
                    mate_in_cb: Optional[int] = None
                    if abs(score) >= MATE_SCORE - 128:
                        mate_in_cb = (
                            (MATE_SCORE - score + 1) // 2
                            if score > 0
                            else -((MATE_SCORE + score + 1) // 2)
                        )
                    score_cp_cb: Optional[int] = None if mate_in_cb is not None else score
                    # Compute hashfull in permille if capacity known
                    if tt_max_entries is not None and tt_max_entries > 0:
                        hashfull = int(min(1000, (len(tt) * 1000) / tt_max_entries))
                    else:
                        hashfull = 0
                    try:
                        on_iter(
                            d,
                            elapsed_ms_total,
                            nodes,
                            qnodes,
                            score_cp_cb,
                            mate_in_cb,
                            pv,
                            seldepth_iter,
                            tt_hits,
                            hashfull,
                        )
                    except Exception:
                        pass
                prev_nodes, prev_qnodes = nodes, qnodes
                prev_fail_high, prev_fail_low = fail_high, fail_low
                if time_up:
                    last_score, last_pv, completed_depth = score, pv, d
                    break
                last_score, last_pv, completed_depth = score, pv, d
                continue

            window = BASE_WINDOW
            alpha = last_score - window
            beta = last_score + window

            while True:
                score, pv = negamax(d, alpha, beta)
                if time_up:
                    break
                if score <= alpha:
                    fail_low += 1
                    re_searches += 1
                    window *= 2
                    alpha = max(score - window, -INF)
                elif score >= beta:
                    fail_high += 1
                    re_searches += 1
                    window *= 2
                    beta = min(score + window, INF)
                else:
                    break

            # Record iteration stats even if time_up
            iters.append(
                {
                    "depth": d,
                    "time_ms": int((time.perf_counter() - iter_start) * 1000),
                    "nodes": nodes - prev_nodes,
                    "qnodes": qnodes - prev_qnodes,
                    "fail_high": fail_high - prev_fail_high,
                    "fail_low": fail_low - prev_fail_low,
                }
            )
            # Streaming callback with cumulative metrics
            if on_iter is not None:
                elapsed_ms_total = int((time.perf_counter() - start) * 1000)
                mate_in_cb2: Optional[int] = None
                if abs(score) >= MATE_SCORE - 128:
                    mate_in_cb2 = (
                        (MATE_SCORE - score + 1) // 2
                        if score > 0
                        else -((MATE_SCORE + score + 1) // 2)
                    )
                score_cp_cb2: Optional[int] = None if mate_in_cb2 is not None else score
                if tt_max_entries is not None and tt_max_entries > 0:
                    hashfull2 = int(min(1000, (len(tt) * 1000) / tt_max_entries))
                else:
                    hashfull2 = 0
                try:
                    on_iter(
                        d,
                        elapsed_ms_total,
                        nodes,
                        qnodes,
                        score_cp_cb2,
                        mate_in_cb2,
                        pv,
                        seldepth_iter,
                        tt_hits,
                        hashfull2,
                    )
                except Exception:
                    pass
            prev_nodes, prev_qnodes = nodes, qnodes
            prev_fail_high, prev_fail_low = fail_high, fail_low
            if time_up:
                last_score, last_pv, completed_depth = score, pv, d
                break
            last_score, last_pv, completed_depth = score, pv, d

        best_move = (
            last_pv[0] if last_pv else (game.legal_moves()[0] if game.legal_moves() else None)
        )

        # Mate distance extraction
        mate_in: Optional[int] = None
        if abs(last_score) >= MATE_SCORE - 128:  # within mate window
            # Convert to plies to mate from root.
            if last_score > 0:
                mate_in = (MATE_SCORE - last_score + 1) // 2
            else:
                mate_in = -((MATE_SCORE + last_score + 1) // 2)

        return SearchResult(
            best_move=best_move,
            score_cp=last_score if mate_in is None else None,
            mate_in=mate_in,
            pv=last_pv,
            nodes=nodes,
            qnodes=qnodes,
            tt_hits=tt_hits,
            fail_high=fail_high,
            fail_low=fail_low,
            tt_probes=tt_probes,
            re_searches=re_searches,
            iters=iters,
            tt_exact_hits=tt_exact_hits,
            tt_lower_hits=tt_lower_hits,
            tt_upper_hits=tt_upper_hits,
            tt_stores=tt_stores,
            tt_replacements=tt_replacements,
            tt_size=len(tt),
            depth=completed_depth,
            time_ms=int((time.perf_counter() - start) * 1000),
            seldepth=seldepth_global,
            hashfull=(
                int(min(1000, (len(tt) * 1000) / tt_max_entries))
                if (tt_max_entries is not None and tt_max_entries > 0)
                else 0
            ),
        )
