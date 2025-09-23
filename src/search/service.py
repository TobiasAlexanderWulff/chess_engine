from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

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
        # Deterministic negamax alpha-beta with simple material evaluation.
        board = game.board
        nodes = 0

        def negamax(d: int, alpha: int, beta: int, pv: List[Move]) -> Tuple[int, List[Move], int]:
            nonlocal nodes
            nodes += 1
            if d == 0:
                # Side to move perspective
                base = evaluate(board)
                score = base if board.side_to_move == "w" else -base
                return score, [], nodes

            legal = board.generate_legal_moves()
            if not legal:
                # No moves: treat as draw (0). Mate/stalemate detection omitted for simplicity.
                return 0, [], nodes

            best_score = -10_000_000
            best_pv: List[Move] = []
            for m in legal:
                board.make_move(m)
                child_pv: List[Move] = []
                score, child_pv, _ = negamax(d - 1, -beta, -alpha, child_pv)
                score = -score
                board.unmake_move(m)
                if score > best_score:
                    best_score = score
                    best_pv = [m] + child_pv
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            return best_score, best_pv, nodes

        score, pv, nodes = negamax(depth, -10_000_000, 10_000_000, [])
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
