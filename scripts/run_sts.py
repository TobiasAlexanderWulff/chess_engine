#!/usr/bin/env python3
import argparse
import csv
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import chess
except ImportError:
    print(
        "Missing dependency: python-chess. Please install it (e.g., pip install python-chess)",
        file=sys.stderr,
    )
    raise


UCI_MOVE_RE = re.compile(r"^[a-h][1-8][a-h][1-8][qrbnQRBN]?$")


@dataclass
class EPDRecord:
    fen: str
    bm: List[str]
    am: List[str]
    meta: Dict[str, str]
    line_no: int


def looks_like_uci(move: str) -> bool:
    return bool(UCI_MOVE_RE.match(move))


def parse_epd_line(line: str, line_no: int) -> Optional[EPDRecord]:
    s = line.strip()
    if not s or s.startswith("#") or s.startswith(";"):
        return None
    # Tokenize by spaces while preserving quoted values for EPD ops
    parts = s.split()
    if len(parts) < 4:
        return None
    # FEN base: 4 or 6 fields
    fen_fields = parts[:6]
    # Some EPDs omit halfmove/fullmove, fallback to 4 fields
    if not all(ch in "KkQqRrBbNnPp1/2-3abcdefghABCDEFGH0123456789" for ch in fen_fields[0]):
        # crude sanity; proceed anyway
        pass
    # Determine whether we have 6-field FEN; if not, use 4
    if parts[4] in ("-",) or ":" not in parts[4]:
        # likely 6-field FEN
        fen_end = 6
    else:
        fen_end = 4
    fen = " ".join(parts[:fen_end])
    ops_str = " ".join(parts[fen_end:])

    bm: List[str] = []
    am: List[str] = []
    meta: Dict[str, str] = {}

    # Parse EPD ops: key value; key value; ... values may be quoted
    tokens = shlex.split(ops_str, posix=True)
    # Reconstruct into key/value pairs terminated by ';'
    k = None
    v_acc: List[str] = []
    for tok in tokens:
        if tok.endswith(";"):
            frag = tok[:-1]
            if k is None:
                k = frag
                v = ""
            else:
                v_acc.append(frag)
                v = " ".join(v_acc).strip()
            if k:
                key = k
                val = v
                if key == "bm":
                    bm.extend([t.strip() for t in val.replace(",", " ").split() if t.strip()])
                elif key == "am":
                    am.extend([t.strip() for t in val.replace(",", " ").split() if t.strip()])
                else:
                    meta[key] = val
            k = None
            v_acc = []
        else:
            if k is None:
                k = tok
            else:
                v_acc.append(tok)

    return EPDRecord(fen=fen, bm=bm, am=am, meta=meta, line_no=line_no)


def parse_epd_file(path: str) -> List[EPDRecord]:
    records: List[EPDRecord] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            rec = parse_epd_line(line, i)
            if rec is not None:
                records.append(rec)
    return records


def normalize_solutions_with_python_chess(fen: str, bm_tokens: List[str]) -> List[str]:
    board = chess.Board(fen)
    res: List[str] = []
    for tok in bm_tokens:
        t = tok.strip()
        if not t:
            continue
        if looks_like_uci(t):
            res.append(t.lower())
            continue
        # Try SAN parse
        try:
            move = board.parse_san(t)
            res.append(move.uci())
        except Exception:
            # If SAN parsing fails, skip; it's safer to not count than to mislabel
            continue
    return res


class UCIEngine:
    def __init__(self, path: str):
        self.path = path
        self.proc: Optional[subprocess.Popen] = None

    def start(
        self, threads: Optional[int] = None, hash_mb: Optional[int] = None, timeout: float = 5.0
    ):
        self.proc = subprocess.Popen(
            [self.path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.send("uci")
        if not self._read_until(lambda line: line.strip() == "uciok", timeout):
            raise RuntimeError("Engine did not respond to 'uci'")
        if threads is not None:
            self.set_option("Threads", str(threads))
        if hash_mb is not None:
            self.set_option("Hash", str(hash_mb))
        self.send("isready")
        if not self._read_until(lambda line: line.strip() == "readyok", timeout):
            raise RuntimeError("Engine not ready after options")

    def send(self, cmd: str):
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def set_option(self, name: str, value: str):
        self.send(f"setoption name {name} value {value}")

    def _read_until(self, predicate, timeout: float) -> bool:
        assert self.proc and self.proc.stdout
        end = time.time() + timeout
        while time.time() < end:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.01)
                continue
            if predicate(line):
                return True
        return False

    def go(
        self,
        fen: str,
        movetime_ms: Optional[int] = None,
        depth: Optional[int] = None,
        nodes: Optional[int] = None,
        timeout_factor: float = 2.5,
    ) -> Tuple[Optional[str], Dict[str, str]]:
        assert self.proc and self.proc.stdout
        self.send("ucinewgame")
        self.send(f"position fen {fen}")
        self.send("isready")
        if not self._read_until(lambda line: line.strip() == "readyok", timeout=5.0):
            raise RuntimeError("Engine not ready for position")

        if depth is not None:
            self.send(f"go depth {depth}")
            timeout_s = 10.0
        elif nodes is not None:
            self.send(f"go nodes {nodes}")
            timeout_s = 10.0
        else:
            mt = movetime_ms or 2000
            self.send(f"go movetime {mt}")
            timeout_s = max(2.0, (mt / 1000.0) * timeout_factor)

        bestmove: Optional[str] = None
        end = time.time() + timeout_s
        while time.time() < end:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.005)
                continue
            if line.startswith("bestmove"):
                parts = line.strip().split()
                if len(parts) >= 2:
                    bestmove = parts[1].lower()
                break
        return bestmove, {}

    def quit(self):
        if self.proc:
            try:
                self.send("quit")
                try:
                    self.proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.proc.terminate()
            except Exception:
                pass


def compare_moves(
    engine_move: Optional[str], solutions_uci: List[str], strict: bool = False
) -> bool:
    if engine_move is None:
        return False
    if strict:
        return engine_move in solutions_uci
    return engine_move.lower().strip() in {s.lower().strip() for s in solutions_uci}


def run_suite(
    records: List[EPDRecord],
    engine_path: str,
    movetime: int,
    depth: Optional[int],
    nodes: Optional[int],
    threads: Optional[int],
    hash_mb: Optional[int],
    limit: Optional[int],
    strict: bool,
    csv_path: Optional[str],
) -> int:
    engine = UCIEngine(engine_path)
    engine.start(threads=threads, hash_mb=hash_mb)

    total = 0
    with_solutions = 0
    correct = 0

    csv_file = open(csv_path, "w", newline="", encoding="utf-8") if csv_path else sys.stdout
    writer = csv.writer(csv_file)
    writer.writerow(
        ["id", "line_no", "correct", "engine_move", "solutions", "fen", "time_ms", "depth", "nodes"]
    )

    try:
        for rec in records:
            if limit is not None and total >= limit:
                break
            total += 1
            # Normalize solutions using python-chess
            solutions_uci = normalize_solutions_with_python_chess(rec.fen, rec.bm)
            if solutions_uci:
                with_solutions += 1

            start = time.time()
            bestmove, _meta = engine.go(rec.fen, movetime_ms=movetime, depth=depth, nodes=nodes)
            elapsed_ms = int((time.time() - start) * 1000)

            is_correct = (
                compare_moves(bestmove, solutions_uci, strict=strict) if solutions_uci else False
            )
            if is_correct:
                correct += 1

            writer.writerow(
                [
                    rec.meta.get("id", ""),
                    rec.line_no,
                    1 if is_correct else 0,
                    bestmove or "",
                    " ".join(solutions_uci),
                    rec.fen,
                    elapsed_ms,
                    depth or "",
                    nodes or "",
                ]
            )
    finally:
        if csv_file is not sys.stdout:
            csv_file.close()
        engine.quit()

    if with_solutions > 0:
        rate = 100.0 * correct / with_solutions
        print(f"Summary: Correct {correct} / {with_solutions} ({rate:.1f}%)", file=sys.stderr)
    else:
        print("Summary: No positions with solutions parsed.", file=sys.stderr)

    return 0


def main():
    ap = argparse.ArgumentParser(description="Run Strategic Test Suite (STS) against a UCI engine")
    ap.add_argument("--engine", required=True, help="Path to UCI engine executable")
    ap.add_argument("--epd", required=True, help="Path to STS EPD file")
    ap.add_argument(
        "--movetime", type=int, default=2000, help="Movetime per position in ms (default: 2000)"
    )
    ap.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Depth limit (mutually exclusive with movetime/nodes)",
    )
    ap.add_argument(
        "--nodes",
        type=int,
        default=None,
        help="Node limit (mutually exclusive with movetime/depth)",
    )
    ap.add_argument("--threads", type=int, default=None, help="Set UCI Threads option if supported")
    ap.add_argument(
        "--hash", dest="hash_mb", type=int, default=None, help="Set UCI Hash size (MB) if supported"
    )
    ap.add_argument("--limit", type=int, default=None, help="Limit number of positions")
    ap.add_argument("--strict", action="store_true", help="Strict match (exact UCI string)")
    ap.add_argument(
        "--report", dest="csv_path", default=None, help="Path to CSV report (default: stdout)"
    )

    args = ap.parse_args()

    if not os.path.exists(args.engine):
        print(f"Engine not found: {args.engine}", file=sys.stderr)
        return 2
    if not os.path.exists(args.epd):
        print(f"EPD not found: {args.epd}", file=sys.stderr)
        return 2
    # Mutual exclusivity basic check
    set_limits = sum(1 for v in (args.depth, args.nodes) if v is not None)
    if set_limits > 1:
        print("Only one of --depth or --nodes may be set (movetime is default)", file=sys.stderr)
        return 2

    records = parse_epd_file(args.epd)
    if not records:
        print("No EPD records parsed.", file=sys.stderr)
        return 1

    return run_suite(
        records=records,
        engine_path=args.engine,
        movetime=args.movetime,
        depth=args.depth,
        nodes=args.nodes,
        threads=args.threads,
        hash_mb=args.hash_mb,
        limit=args.limit,
        strict=args.strict,
        csv_path=args.csv_path,
    )


if __name__ == "__main__":
    sys.exit(main())
