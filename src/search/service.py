from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.engine.game import Game
from src.engine.move import Move


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
        # Placeholder: return no-op result
        moves = game.legal_moves()
        best = moves[0] if moves else None
        return SearchResult(
            best_move=best,
            score_cp=None,
            mate_in=None,
            pv=[best] if best else [],
            nodes=0,
            depth=depth,
            time_ms=0,
        )
