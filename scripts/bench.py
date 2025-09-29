#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Ensure repo root (which contains `src/`) is importable when running directly
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.engine.game import Game
from src.search.service import SearchService, SearchResult


DEFAULT_POSITIONS = os.path.join("assets", "benchmarks", "positions.json")


def _git_info() -> Dict[str, Optional[str]]:
    def run(cmd: List[str]) -> Optional[str]:
        try:
            out = subprocess.check_output(cmd, cwd=REPO_ROOT, stderr=subprocess.DEVNULL)
            return out.decode().strip()
        except Exception:
            return None

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "describe": run(["git", "describe", "--dirty", "--tags", "--always"]),
    }


def _entries_from_hash_mb(mb: int) -> int:
    # Match UCI loop heuristic: ~16,384 entries per MiB (~64 bytes/entry)
    mb = max(1, int(mb))
    return mb * 16384


@dataclass
class BenchItem:
    id: str
    name: str
    fen: str
    movetime_ms: Optional[int] = None
    depth: Optional[int] = None


def load_positions(path: str) -> List[BenchItem]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items: List[BenchItem] = []
    for obj in data.get("positions", []):
        items.append(
            BenchItem(
                id=str(obj.get("id", obj.get("name", "pos"))),
                name=str(obj.get("name", "Unnamed")),
                fen=str(obj["fen"]),
                movetime_ms=(
                    int(obj["movetime_ms"]) if obj.get("movetime_ms") is not None else None
                ),
                depth=(int(obj["depth"]) if obj.get("depth") is not None else None),
            )
        )
    return items


def bench_position(
    svc: SearchService,
    item: BenchItem,
    *,
    movetime_ms: Optional[int],
    depth: Optional[int],
    tt_max_entries: Optional[int],
    iterations: int,
) -> Dict[str, Any]:
    # Resolve effective params (per-item override > global)
    eff_movetime = item.movetime_ms if item.movetime_ms is not None else movetime_ms
    eff_depth = item.depth if item.depth is not None else depth
    # If neither provided, default to 1000ms
    if eff_movetime is None and eff_depth is None:
        eff_movetime = 1000

    # Prepare game
    try:
        game = Game.from_fen(item.fen)
    except Exception as e:
        raise ValueError(f"Invalid FEN for {item.id}: {e}")

    # Accumulators for iterations
    total_time = 0
    total_nodes = 0
    total_qnodes = 0
    last: Optional[SearchResult] = None

    for _ in range(max(1, iterations)):
        res = svc.search(
            game,
            depth=eff_depth or 1,
            movetime_ms=eff_movetime,
            tt_max_entries=tt_max_entries,
        )
        total_time += max(0, res.time_ms)
        total_nodes += max(0, res.nodes)
        total_qnodes += max(0, res.qnodes)
        last = res

    assert last is not None

    avg_time = int(total_time / max(1, iterations))
    avg_nodes = int(total_nodes / max(1, iterations))
    avg_qnodes = int(total_qnodes / max(1, iterations))
    nps = int(avg_nodes * 1000 / max(1, avg_time)) if avg_time > 0 else 0

    score_obj: Optional[Dict[str, int]]
    if last.mate_in is not None:
        score_obj = {"mate": last.mate_in}
    else:
        score_obj = {"cp": last.score_cp or 0}

    return {
        "id": item.id,
        "name": item.name,
        "fen": item.fen,
        "movetime_ms": eff_movetime,
        "depth": last.depth,
        "best_move": (last.best_move.to_uci() if last.best_move else None),
        "score": score_obj,
        "pv": [m.to_uci() for m in last.pv],
        "time_ms": avg_time,
        "nodes": avg_nodes,
        "qnodes": avg_qnodes,
        "nps": nps,
        "seldepth": last.seldepth,
        "tt_hits": last.tt_hits,
        "tt_probes": last.tt_probes,
        "tt_stores": last.tt_stores,
        "tt_replacements": last.tt_replacements,
        "tt_size": last.tt_size,
        "hashfull": last.hashfull,
        "fail_high": last.fail_high,
        "fail_low": last.fail_low,
        "re_searches": last.re_searches,
        "iters": last.iters,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run engine benchmarks over a positions suite")
    parser.add_argument("--positions", default=DEFAULT_POSITIONS, help="Path to positions.json")
    parser.add_argument(
        "--movetime-ms", type=int, default=None, help="Global movetime per position"
    )
    parser.add_argument("--depth", type=int, default=None, help="Global depth per position")
    parser.add_argument("--hash-mb", type=int, default=16, help="Approximate TT size in MiB")
    parser.add_argument("--tt-max-entries", type=int, default=None, help="Override TT entry cap")
    parser.add_argument(
        "--iterations", type=int, default=1, help="Repeat runs per position and average"
    )
    parser.add_argument("--out", type=str, default=None, help="Write JSON results to file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--progress", action="store_true", help="Print per-position progress to stderr"
    )
    args = parser.parse_args()

    items = load_positions(args.positions)
    if not items:
        raise SystemExit("No positions found in positions file")

    # Resolve TT entries
    tt_entries = (
        int(args.tt_max_entries)
        if args.tt_max_entries is not None
        else _entries_from_hash_mb(args.hash_mb)
    )

    svc = SearchService()

    results: List[Dict[str, Any]] = []
    t0 = time.perf_counter()
    for idx, it in enumerate(items, start=1):
        if args.progress:
            sys.stderr.write(f"[{idx}/{len(items)}] {it.id}: running...\n")
            sys.stderr.flush()
        res = bench_position(
            svc,
            it,
            movetime_ms=args.movetime_ms,
            depth=args.depth,
            tt_max_entries=tt_entries,
            iterations=max(1, args.iterations),
        )
        results.append(res)
        if args.progress:
            sys.stderr.write(
                f"    depth={res['depth']} time={res['time_ms']}ms nodes={res['nodes']} nps={res['nps']} best={res['best_move']}\n"
            )
            sys.stderr.flush()

    dt_ms = int((time.perf_counter() - t0) * 1000)
    total_nodes = sum(r["nodes"] for r in results)
    total_qnodes = sum(r["qnodes"] for r in results)
    overall_nps = int(total_nodes * 1000 / max(1, dt_ms)) if dt_ms > 0 else 0

    payload = {
        "meta": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "git": _git_info(),
            "engine": {"version": "0.0.1"},
            "config": {
                "positions_file": os.path.relpath(args.positions, REPO_ROOT),
                "iterations": max(1, args.iterations),
                "global_movetime_ms": args.movetime_ms,
                "global_depth": args.depth,
                "hash_mb": args.hash_mb,
                "tt_max_entries": tt_entries,
            },
        },
        "results": results,
        "summary": {
            "positions": len(results),
            "total_time_ms": dt_ms,
            "total_nodes": total_nodes,
            "total_qnodes": total_qnodes,
            "overall_nps": overall_nps,
        },
    }

    if args.out:
        out_path = args.out
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2 if args.pretty else None)
        print(out_path)
    else:
        print(json.dumps(payload, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
