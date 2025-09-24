from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time

from src.engine.game import Game
from src.engine.move import Move
from src.eval import evaluate


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

        def is_tt_equal(a: Optional[Move], b: Move) -> bool:
            return (
                a is not None
                and a.from_sq == b.from_sq
                and a.to_sq == b.to_sq
                and a.promotion == b.promotion
            )

        def negamax(d: int, alpha: int, beta: int, ply: int = 0) -> Tuple[int, List[Move]]:
            nonlocal nodes
            nodes += 1

            # Leaf or terminal
            if d == 0:
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

            def move_score(mv: Move) -> int:
                score = 0
                if is_tt_equal(tt_move, mv):
                    score += 1_000_000
                # capture detection: destination occupied by opponent or ep target
                is_capture = ((occ_opp >> mv.to_sq) & 1) == 1 or (
                    board.ep_square is not None and mv.to_sq == board.ep_square
                )
                if is_capture:
                    score += 500_000
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

        # Iterative deepening from 1..depth (simple stop after movetime if provided)
        start = time.perf_counter()
        last_score = 0
        last_pv: List[Move] = []
        completed_depth = 0
        for d in range(1, max(1, depth) + 1):
            score, pv = negamax(d, -INF, INF)
            last_score, last_pv, completed_depth = score, pv, d
            if movetime_ms is not None:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if elapsed_ms >= movetime_ms:
                    break

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
