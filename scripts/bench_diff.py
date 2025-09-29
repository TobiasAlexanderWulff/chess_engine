#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_by_id(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for r in results:
        rid = str(r.get("id") or r.get("name"))
        if not rid:
            continue
        idx[rid] = r
    return idx


def pct(old: int, new: int) -> str:
    if old == 0:
        if new == 0:
            return "0.0%"
        return "+inf"
    return f"{(new - old) * 100.0 / old:+.1f}%"


def format_row(cols: List[str], widths: List[int]) -> str:
    parts: List[str] = []
    for i, c in enumerate(cols):
        w = widths[i]
        parts.append(c.ljust(w))
    return "  ".join(parts)


def main() -> None:
    p = argparse.ArgumentParser(description="Diff two benchmark baselines (JSON)")
    p.add_argument("--old", required=True, help="Path to older baseline JSON")
    p.add_argument("--new", required=True, help="Path to newer baseline JSON")
    p.add_argument(
        "--sort",
        default="delta_nps",
        choices=["delta_nps", "delta_nodes", "delta_depth", "id"],
        help="Sort key for per-position rows",
    )
    p.add_argument("--limit", type=int, default=None, help="Limit number of rows shown")
    args = p.parse_args()

    old = load(args.old)
    new = load(args.new)

    old_results = old.get("results", [])
    new_results = new.get("results", [])
    if not old_results or not new_results:
        raise SystemExit("Both JSON files must contain a 'results' array")

    idx_old = index_by_id(old_results)
    idx_new = index_by_id(new_results)

    # Build per-position rows for ids present in both
    rows: List[Dict[str, Any]] = []
    missing: List[str] = []
    for rid, ro in idx_old.items():
        rn = idx_new.get(rid)
        if rn is None:
            missing.append(rid)
            continue
        row = {
            "id": rid,
            "name": ro.get("name", rid),
            "old_nps": int(ro.get("nps", 0)),
            "new_nps": int(rn.get("nps", 0)),
            "delta_nps": int(rn.get("nps", 0)) - int(ro.get("nps", 0)),
            "old_nodes": int(ro.get("nodes", 0)),
            "new_nodes": int(rn.get("nodes", 0)),
            "delta_nodes": int(rn.get("nodes", 0)) - int(ro.get("nodes", 0)),
            "old_time": int(ro.get("time_ms", 0)),
            "new_time": int(rn.get("time_ms", 0)),
            "old_depth": int(ro.get("depth", 0)),
            "new_depth": int(rn.get("depth", 0)),
            "delta_depth": int(rn.get("depth", 0)) - int(ro.get("depth", 0)),
        }
        rows.append(row)

    key_map = {
        "delta_nps": lambda r: r["delta_nps"],
        "delta_nodes": lambda r: r["delta_nodes"],
        "delta_depth": lambda r: r["delta_depth"],
        "id": lambda r: r["id"],
    }
    rows.sort(key=key_map[args.sort], reverse=(args.sort != "id"))
    if args.limit is not None and args.limit >= 0:
        rows = rows[: args.limit]

    # Overall summary (recompute to be robust)
    def totals(rs: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        total_nodes = sum(int(r.get("nodes", 0)) for r in rs)
        total_time = sum(int(r.get("time_ms", 0)) for r in rs)
        overall_nps = int(total_nodes * 1000 / total_time) if total_time > 0 else 0
        return total_nodes, total_time, overall_nps

    old_total_nodes, old_total_time, old_overall_nps = totals(old_results)
    new_total_nodes, new_total_time, new_overall_nps = totals(new_results)

    # Print summary
    print("Baseline Diff")
    print(f"old: {args.old}")
    print(f"new: {args.new}")
    print("-- overall --")
    print(
        f"nodes: {old_total_nodes} -> {new_total_nodes} ({pct(old_total_nodes, new_total_nodes)})"
    )
    print(f"time_ms: {old_total_time} -> {new_total_time} ({pct(old_total_time, new_total_time)})")
    print(f"nps: {old_overall_nps} -> {new_overall_nps} ({pct(old_overall_nps, new_overall_nps)})")

    # Print per-position table
    print("\n-- per-position --")
    headers = ["id", "nps(old)", "nps(new)", "Δnps(%)", "depth", "time_ms"]
    widths = [18, 10, 10, 10, 9, 10]
    print(format_row(headers, widths))
    print(format_row(["-" * w for w in widths], widths))
    for r in rows:
        id_col = r["id"]
        old_nps = r["old_nps"]
        new_nps = r["new_nps"]
        pct_nps = pct(old_nps, new_nps)
        depth_col = f"{r['old_depth']}->{r['new_depth']}"
        time_col = f"{r['old_time']}->{r['new_time']}"
        cols = [
            str(id_col),
            str(old_nps),
            str(new_nps),
            pct_nps,
            depth_col,
            time_col,
        ]
        print(format_row(cols, widths))

    if missing:
        sys.stderr.write(
            f"Warning: {len(missing)} position(s) present in old baseline not found in new: "
            + ", ".join(missing)
            + "\n"
        )


if __name__ == "__main__":
    main()
