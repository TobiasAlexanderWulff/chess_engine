from __future__ import annotations

from .board import Board


def perft(board: Board, depth: int) -> int:
    """Compute perft node count for `board` at `depth`.

    Definition:
    - depth == 0 returns 1 (the current node).
    - depth > 0 returns the sum over all legal child positions' perft(depth-1).

    Note: This scaffolding relies on `Board.generate_legal_moves()` which is
    currently a stub; once legal move generation is implemented, results will
    be meaningful. The make/unmake workflow will replace copy-apply if needed.
    """
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if depth == 0:
        return 1

    nodes = 0
    for _m in board.generate_legal_moves():
        # Until make/unmake and apply are implemented, we can't advance the
        # position meaningfully. Once available, switch to:
        #   board.make_move(m); nodes += perft(board, depth-1); board.unmake_move(m)
        # or use an immutable apply that returns a new Board.
        # For now, this will sum zero because move gen returns empty.
        pass
    return nodes
