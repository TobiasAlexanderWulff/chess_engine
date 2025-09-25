from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

from ...engine.game import Game
from ...engine.move import Move, parse_uci
from ...search.service import SearchService, SearchResult


Writer = Callable[[str], None]


@dataclass
class GoParams:
    depth: Optional[int] = None
    movetime_ms: Optional[int] = None
    wtime: Optional[int] = None
    btime: Optional[int] = None
    winc: Optional[int] = None
    binc: Optional[int] = None
    movestogo: Optional[int] = None


class UCIEngine:
    """UCI protocol adapter around the core engine.

    Notes:
    - Core remains pure; I/O is isolated here.
    - Minimal command set: uci, isready, ucinewgame, position, go (depth|movetime), quit.
    """

    def __init__(self) -> None:
        self.game: Game = Game.new()
        self.search = SearchService()
        # Async search state
        self._search_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._result_lock = threading.Lock()
        self._last_result: Optional[SearchResult] = None
        self._search_running = False
        self._gen = 0  # generation id to invalidate stale workers
        # Engine options
        self.hash_mb: int = 16
        self.multipv: int = 1

    # ---- Command handlers ----
    def cmd_uci(self, write: Writer) -> None:
        write("id name chess_engine")
        write("id author tobiasalexanderwulff")
        # Options for GUIs
        write("option name Hash type spin default 16 min 1 max 4096")
        write("option name MultiPV type spin default 1 min 1 max 10")
        write("uciok")

    def cmd_isready(self, write: Writer) -> None:
        write("readyok")

    def cmd_ucinewgame(self) -> None:
        self.game = Game.new()
        # Cancel any ongoing search
        self._cancel_running_search()

    def cmd_position(self, args: List[str]) -> None:
        # position [startpos | fen <FEN> ] [moves m1 m2 ...]
        if not args:
            return
        idx = 0
        if args[idx] == "startpos":
            self.game = Game.new()
            idx += 1
        elif args[idx] == "fen":
            idx += 1
            fen_tokens: List[str] = []
            while idx < len(args) and args[idx] != "moves":
                fen_tokens.append(args[idx])
                idx += 1
            if fen_tokens:
                try:
                    self.game = Game.from_fen(" ".join(fen_tokens))
                except ValueError:
                    # Ignore invalid FEN
                    return
        # Apply subsequent moves if present
        if idx < len(args) and args[idx] == "moves":
            idx += 1
            while idx < len(args):
                u = args[idx]
                idx += 1
                try:
                    mv: Move = parse_uci(u)
                    self.game.apply_move(mv)
                except Exception:
                    # Silently ignore invalid/illegal moves per typical UCI robustness
                    break

    def cmd_setoption(self, args: List[str]) -> None:
        # setoption name <name> [value <value>]
        if not args:
            return
        i = 0
        if args[i] == "name":
            i += 1
        name_tokens: List[str] = []
        while i < len(args) and args[i] != "value":
            name_tokens.append(args[i])
            i += 1
        value_tokens: List[str] = []
        if i < len(args) and args[i] == "value":
            i += 1
            while i < len(args):
                value_tokens.append(args[i])
                i += 1
        name = " ".join(name_tokens).strip().lower()
        value = " ".join(value_tokens).strip()
        if name == "hash":
            try:
                mb = int(value)
                if mb < 1:
                    mb = 1
                self.hash_mb = min(4096, mb)
            except ValueError:
                pass
        elif name == "multipv":
            try:
                k = int(value)
                if k < 1:
                    k = 1
                self.multipv = min(10, k)
            except ValueError:
                pass

    def cmd_go(self, args: List[str], write: Writer) -> None:
        params = self._parse_go_args(args)
        # Determine effective time/depth
        eff_depth, eff_movetime = self._select_time_and_depth(params)
        # If a search is already running, cancel and start fresh
        self._cancel_running_search()
        self._stop_event.clear()
        with self._result_lock:
            self._last_result = None
        self._search_running = True
        self._gen += 1
        gen = self._gen

        def worker() -> None:
            if self.multipv <= 1:
                # Run search (blocking) and publish result if still current
                res = self.search.search(
                    self.game,
                    depth=eff_depth,
                    movetime_ms=eff_movetime,
                    tt_max_entries=self._tt_entries_cap(),
                    on_iter=self._make_iter_callback(gen, write),
                )
                if self._stop_event.is_set() or gen != self._gen:
                    with self._result_lock:
                        self._last_result = res
                    self._search_running = False
                    return
                with self._result_lock:
                    self._last_result = res
                self._emit_info(res, write)
                best = res.best_move.to_uci() if res.best_move else "(none)"
                write(f"bestmove {best}")
                self._search_running = False
                return

            # MultiPV root-split: search each root move independently
            legal = self.game.legal_moves()
            if not legal:
                write("bestmove (none)")
                self._search_running = False
                return

            per_movetime = None
            if eff_movetime is not None:
                per_movetime = max(1, eff_movetime // max(1, self.multipv))

            lines = []
            for mv in legal:
                if self._stop_event.is_set() or gen != self._gen:
                    break
                # Apply root move
                try:
                    self.game.apply_move(mv)
                except Exception:
                    continue
                # Search child
                child = self.search.search(
                    self.game,
                    depth=max(1, eff_depth - 1),
                    movetime_ms=per_movetime,
                    tt_max_entries=self._tt_entries_cap(),
                    on_iter=None,
                )
                # Undo root move
                try:
                    self.game.undo_move()
                except Exception:
                    pass

                # Convert score to root perspective
                if child.mate_in is not None:
                    mate_root = -child.mate_in - 1
                    cp_root = None
                else:
                    mate_root = None
                    cp_root = -child.score_cp if child.score_cp is not None else None

                pv_full = [mv] + child.pv
                if mate_root is not None:
                    key = (
                        (1_000_000 - 2 * abs(mate_root))
                        if mate_root > 0
                        else (-1_000_000 + 2 * abs(mate_root))
                    )
                else:
                    key = cp_root if cp_root is not None else -10_000_000
                lines.append(
                    {
                        "pv": pv_full,
                        "mate_in": mate_root,
                        "score_cp": cp_root,
                        "depth": child.depth + 1,
                        "seldepth": child.seldepth + 1,
                        "nodes": child.nodes,
                        "tthits": child.tt_hits,
                        "hashfull": child.hashfull,
                        "key": key,
                    }
                )

            lines.sort(key=lambda x: x["key"], reverse=True)
            topk = lines[: min(self.multipv, len(lines))]

            if self._stop_event.is_set() or gen != self._gen:
                self._search_running = False
                return

            for idx, ln in enumerate(topk, start=1):
                nodes = ln["nodes"]
                depth = ln["depth"]
                seldepth = ln["seldepth"]
                tthits = ln["tthits"]
                hashfull = ln["hashfull"]
                if ln["mate_in"] is not None:
                    score = f"mate {ln['mate_in']}"
                else:
                    score = f"cp {ln['score_cp'] or 0}"
                pv_str = " ".join(m.to_uci() for m in ln["pv"])
                write(
                    f"info multipv {idx} depth {depth} seldepth {seldepth} nodes {nodes} tthits {tthits} hashfull {hashfull} "
                    f"score {score} pv {pv_str}"
                )

            bestmove = topk[0]["pv"][0].to_uci() if topk else "(none)"
            write(f"bestmove {bestmove}")
            self._search_running = False

        self._search_thread = threading.Thread(target=worker, name="uci-search", daemon=True)
        self._search_thread.start()

    def cmd_stop(self, write: Writer) -> None:
        # Signal stop; emit best known move immediately
        self._stop_event.set()
        self._gen += 1  # invalidate any current worker's output
        best_uci: str
        with self._result_lock:
            res = self._last_result
        if res is None:
            # Fall back to a quick legal move if no result yet
            legal = self.game.legal_moves()
            best_uci = legal[0].to_uci() if legal else "(none)"
        else:
            best_uci = res.best_move.to_uci() if res.best_move else "(none)"
        write(f"bestmove {best_uci}")
        # Leave background thread to finish silently (output suppressed by gen)

    # ---- Utilities ----
    def _parse_go_args(self, args: List[str]) -> GoParams:
        gp = GoParams()
        i = 0
        while i < len(args):
            tok = args[i]
            if tok == "depth" and i + 1 < len(args):
                try:
                    gp.depth = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "movetime" and i + 1 < len(args):
                try:
                    gp.movetime_ms = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "wtime" and i + 1 < len(args):
                try:
                    gp.wtime = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "btime" and i + 1 < len(args):
                try:
                    gp.btime = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "winc" and i + 1 < len(args):
                try:
                    gp.winc = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "binc" and i + 1 < len(args):
                try:
                    gp.binc = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            if tok == "movestogo" and i + 1 < len(args):
                try:
                    gp.movestogo = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            # Ignore unsupported time controls for now
            i += 1
        return gp

    def _select_time_and_depth(self, gp: GoParams) -> tuple[int, Optional[int]]:
        # Precedence: explicit movetime > (wtime/btime based) > depth fallback.
        if gp.movetime_ms is not None:
            depth = gp.depth or 64
            return depth, max(1, gp.movetime_ms)

        # Use clock-based allocation when any time field is provided
        if any(v is not None for v in (gp.wtime, gp.btime, gp.winc, gp.binc, gp.movestogo)):
            stm_white = self.game.board.side_to_move == "w"
            remaining = gp.wtime if stm_white else gp.btime
            inc = gp.winc if stm_white else gp.binc
            if remaining is None:
                # If missing for side to move, fall back to depth only
                return gp.depth or 8, None
            moves_left = gp.movestogo if (gp.movestogo and gp.movestogo > 0) else 30
            base = remaining // max(1, moves_left)
            bonus = int((inc or 0) * 0.5)
            alloc = base + bonus
            # Clamp allocation conservatively
            safety_margin = 50
            max_cap = min(int(remaining * 0.7), max(0, remaining - safety_margin))
            if max_cap <= 0:
                alloc = max(1, remaining - 1)
            else:
                alloc = max(10, min(alloc, max_cap))
            depth = gp.depth or 64  # let time primarily govern
            return depth, alloc

        # No time info: depth-only search
        return gp.depth or 1, None

    def _emit_info(self, res: SearchResult, write: Writer) -> None:
        # Compute UCI-style info line (single snapshot after search)
        depth = res.depth
        time_ms = max(0, res.time_ms)
        nodes = max(0, res.nodes)
        nps = int(nodes * 1000 / max(1, time_ms))
        seldepth = res.seldepth
        tthits = res.tt_hits
        hashfull = res.hashfull
        if res.mate_in is not None:
            score = f"mate {res.mate_in}"
        else:
            cp = res.score_cp if res.score_cp is not None else 0
            score = f"cp {cp}"
        pv = " ".join(m.to_uci() for m in res.pv)
        write(
            f"info depth {depth} seldepth {seldepth} time {time_ms} nodes {nodes} nps {nps} tthits {tthits} hashfull {hashfull} multipv 1 "
            f"score {score} pv {pv}"
        )

    def _make_iter_callback(self, gen: int, write: Writer):
        def _cb(
            depth: int,
            time_ms: int,
            nodes: int,
            qnodes: int,
            score_cp: Optional[int],
            mate_in: Optional[int],
            pv: List[Move],
            seldepth: int,
            tthits: int,
            hashfull: int,
        ) -> None:
            # Suppress if search was stopped or superseded
            if self._stop_event.is_set() or gen != self._gen:
                return
            # Build and emit UCI info line
            nps = int(nodes * 1000 / max(1, time_ms))
            if mate_in is not None:
                score = f"mate {mate_in}"
            else:
                score = f"cp {score_cp or 0}"
            pv_str = " ".join(m.to_uci() for m in pv)
            write(
                f"info depth {depth} seldepth {seldepth} time {time_ms} nodes {nodes} nps {nps} tthits {tthits} hashfull {hashfull} multipv 1 "
                f"score {score} pv {pv_str}"
            )

        return _cb

    def _cancel_running_search(self) -> None:
        if self._search_running:
            self._stop_event.set()
            self._gen += 1
        # Do not join; thread is daemonized and its output is suppressed via gen

    def _tt_entries_cap(self) -> Optional[int]:
        # Rough heuristic: 1 MiB -> ~16384 entries (assume ~64 bytes/entry)
        entries_per_mb = 16384
        mb = max(1, int(self.hash_mb))
        return mb * entries_per_mb


def _default_writer(line: str) -> None:
    # Ensure newline termination and immediate flush
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def run_uci() -> None:
    eng = UCIEngine()
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        cmd, args = parts[0], parts[1:]

        if cmd == "uci":
            eng.cmd_uci(_default_writer)
        elif cmd == "isready":
            eng.cmd_isready(_default_writer)
        elif cmd == "setoption":
            eng.cmd_setoption(args)
        elif cmd == "ucinewgame":
            eng.cmd_ucinewgame()
        elif cmd == "position":
            eng.cmd_position(args)
        elif cmd == "go":
            eng.cmd_go(args, _default_writer)
        elif cmd == "stop":
            eng.cmd_stop(_default_writer)
        elif cmd == "quit":
            break
        # Ignore unknown commands per UCI convention
