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

    # ---- Command handlers ----
    def cmd_uci(self, write: Writer) -> None:
        write("id name chess_engine")
        write("id author tobiasalexanderwulff")
        # Options can be declared here later via 'option name ...'
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

    def cmd_go(self, args: List[str], write: Writer) -> None:
        params = self._parse_go_args(args)
        # If a search is already running, cancel and start fresh
        self._cancel_running_search()
        self._stop_event.clear()
        with self._result_lock:
            self._last_result = None
        self._search_running = True
        self._gen += 1
        gen = self._gen

        def worker() -> None:
            # Run search (blocking) and publish result if still current
            res = self.search.search(
                self.game,
                depth=params.depth or 1,
                movetime_ms=params.movetime_ms,
            )
            # If stop was requested and handled, or a newer gen started, skip output
            if self._stop_event.is_set() or gen != self._gen:
                # Preserve last_result for possible consumers but avoid emitting
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
            # Ignore unsupported time controls for now
            i += 1
        return gp

    def _emit_info(self, res: SearchResult, write: Writer) -> None:
        # Compute UCI-style info line (single snapshot after search)
        depth = res.depth
        time_ms = max(0, res.time_ms)
        nodes = max(0, res.nodes)
        nps = int(nodes * 1000 / max(1, time_ms))
        if res.mate_in is not None:
            score = f"mate {res.mate_in}"
        else:
            cp = res.score_cp if res.score_cp is not None else 0
            score = f"cp {cp}"
        pv = " ".join(m.to_uci() for m in res.pv)
        write(
            f"info depth {depth} time {time_ms} nodes {nodes} nps {nps} " f"score {score} pv {pv}"
        )

    def _cancel_running_search(self) -> None:
        if self._search_running:
            self._stop_event.set()
            self._gen += 1
        # Do not join; thread is daemonized and its output is suppressed via gen


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
