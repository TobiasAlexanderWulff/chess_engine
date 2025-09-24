from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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

        def store(depth_left: int, score: int, alpha_orig: int, beta: int, best: Optional[Move]) -> None:
            flag: str
            if score <= alpha_orig:
                flag = "UPPER"
            elif score >= beta:
                flag = "LOWER"
            else:
                flag = "EXACT"
            tt[board.zobrist_hash] = TTEntry(board.zobrist_hash, depth_left, flag, score, best)

        def negamax(d: int, alpha: int, beta: int) -> Tuple[int, List[Move]]:
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
                if d > 0 and tt.get(board.zobrist_hash, None) and tt[board.zobrist_hash].flag == "EXACT":
                    return score, ([m] if m else [])
                # Otherwise continue but prefer the stored move for ordering
                tt_move = m

            legal = board.generate_legal_moves()
            if not legal:
                # No moves: treat as draw (0). Mate/stalemate detection omitted for simplicity.
                return 0, []

            # Move ordering: prefer hash move first if present
            if tt_move is not None:
                legal.sort(key=lambda mv: 0 if (mv == tt_move or (
                    mv.from_sq == tt_move.from_sq and mv.to_sq == tt_move.to_sq and mv.promotion == tt_move.promotion
                )) else 1)

            best_score = -INF
            best_line: List[Move] = []
            alpha_orig = alpha
            best_move: Optional[Move] = None

            for m in legal:
                board.make_move(m)
                child_score, child_pv = negamax(d - 1, -beta, -alpha)
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
                    return best_score, best_line

            store(d, best_score, alpha_orig, beta, best_move)
            return best_score, best_line

        score, pv = negamax(depth, -INF, INF)
        best_move = pv[0] if pv else (game.legal_moves()[0] if game.legal_moves() else None)
        return SearchResult(
            best_move=best_move,
            score_cp=score,
            mate_in=None,
            pv=pv,
            nodes=nodes,
            depth=depth,
            time_ms=0,
        )
