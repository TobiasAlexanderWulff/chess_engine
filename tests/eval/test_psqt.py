from __future__ import annotations

from src.engine.game import Game
from src.eval import evaluate


def test_knight_centralization_scores_higher() -> None:
    # White knight on d4 should score higher than on a1 (material equal)
    fen_center = "4k3/8/8/8/3N4/8/8/4K3 w - - 0 1"
    fen_rim = "4k3/8/8/8/8/8/8/N3K3 w - - 0 1"

    g_center = Game.from_fen(fen_center)
    g_rim = Game.from_fen(fen_rim)

    sc_center = evaluate(g_center.board)
    sc_rim = evaluate(g_rim.board)
    assert sc_center > sc_rim


def _mirror_and_swap_colors(fen: str) -> str:
    # Mirror ranks and swap piece colors; keep castling/ep as '-' for simplicity
    parts = fen.split()
    board, stm, castling, ep, halfmove, fullmove = parts
    ranks = board.split("/")
    # Mirror vertically
    ranks = list(reversed(ranks))
    # Swap colors by flipping case
    swapped = []
    for r in ranks:
        row = []
        for ch in r:
            if ch.isalpha():
                row.append(ch.swapcase())
            else:
                row.append(ch)
        swapped.append("".join(row))
    new_board = "/".join(swapped)
    new_stm = "b" if stm == "w" else "w"
    return f"{new_board} {new_stm} - - {halfmove} {fullmove}"


def test_eval_mirror_swap_negates_score() -> None:
    # A modest imbalanced PSQT situation with equal material, kings included
    fen = "4k3/8/8/2n5/3B4/8/8/4K3 w - - 0 1"
    g = Game.from_fen(fen)
    sc = evaluate(g.board)

    fen_m = _mirror_and_swap_colors(fen)
    g_m = Game.from_fen(fen_m)
    sc_m = evaluate(g_m.board)

    assert sc_m == -sc
