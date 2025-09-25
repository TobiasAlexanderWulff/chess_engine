from __future__ import annotations

from typing import List
import time

from src.protocol.uci.loop import UCIEngine


def capture_writer(buf: List[str]):
    def _w(line: str) -> None:
        buf.append(line)

    return _w


def _wait_until(predicate, timeout_ms: int = 3000):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_multipv_two_lines_and_bestmove():
    eng = UCIEngine()
    eng.cmd_setoption(["name", "MultiPV", "value", "2"])  # type: ignore[arg-type]
    eng.cmd_position(["startpos", "moves", "e2e4", "e7e5"])  # type: ignore[arg-type]
    out: List[str] = []
    eng.cmd_go(["depth", "2"], capture_writer(out))

    assert _wait_until(lambda: any(s.startswith("bestmove ") for s in out), 5000)
    # Expect info lines with multipv 1 and multipv 2
    assert any("multipv 1" in s for s in out)
    assert any("multipv 2" in s for s in out)
