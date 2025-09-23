#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import time
import os
import sys

# Allow running this script directly via `python scripts/perft.py`
# by adding the repo root (which contains `src/`) to sys.path.
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.engine.board import Board, STARTPOS_FEN
from src.engine.perft import perft


def main() -> None:
    parser = argparse.ArgumentParser(description="Run perft on a given FEN and depth")
    parser.add_argument(
        "--fen", type=str, default=STARTPOS_FEN, help="FEN string (default: startpos)"
    )
    parser.add_argument("--depth", type=int, default=3, help="Perft depth (default: 3)")
    args = parser.parse_args()

    board = Board.from_fen(args.fen)
    start = time.perf_counter()
    nodes = perft(board, args.depth)
    dt = time.perf_counter() - start
    print(f"nodes={nodes} depth={args.depth} time_ms={int(dt*1000)} nps={int(nodes/max(dt,1e-9))}")


if __name__ == "__main__":
    main()
