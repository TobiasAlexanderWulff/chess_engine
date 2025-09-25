from __future__ import annotations

from typing import List, Callable
import time

from src.protocol.uci.loop import UCIEngine


def capture_writer(buf: List[str]):
    def _w(line: str) -> None:
        buf.append(line)

    return _w


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 1500) -> None:
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.01)


def test_go_with_time_controls():
    eng = UCIEngine()
    eng.cmd_position(["startpos"])  # type: ignore[arg-type]
    out: List[str] = []
    # Give small but non-zero times; include increments
    eng.cmd_go(["wtime", "300", "btime", "300", "winc", "50", "binc", "50"], capture_writer(out))

    _wait_until(lambda: any(line.startswith("bestmove ") for line in out), timeout_ms=3000)
    assert any(line.startswith("bestmove ") for line in out)
    assert any(line.startswith("info depth ") for line in out)
