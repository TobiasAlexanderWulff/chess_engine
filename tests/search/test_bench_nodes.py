from __future__ import annotations

import pytest

from src.engine.game import Game
from src.search.service import SearchService


@pytest.mark.bench
def test_pvs_and_heuristics_reduce_nodes_vs_baseline() -> None:
    # Use a middlegame FEN with reasonable branching
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    game = Game.from_fen(fen)
    service = SearchService()

    # Baseline: disable PVS, NMP, LMR, and futility
    res_base = service.search(
        game,
        depth=3,
        enable_pvs=False,
        enable_nmp=False,
        enable_lmr=False,
        enable_futility=False,
    )

    # Heuristics on (defaults)
    res_opt = service.search(game, depth=3)

    # Expect optimized search to visit fewer or equal nodes
    assert res_opt.nodes <= res_base.nodes
