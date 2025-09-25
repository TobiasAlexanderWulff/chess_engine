from __future__ import annotations

from typing import List, Callable
import time

from src.protocol.uci.loop import UCIEngine


def capture_writer(buf: List[str]):
    def _w(line: str) -> None:
        buf.append(line)

    return _w


def test_basic_handshake():
    eng = UCIEngine()
    out: List[str] = []
    eng.cmd_uci(capture_writer(out))
    assert any(line.startswith("id name ") for line in out)
    assert any(line == "uciok" for line in out)


def test_isready():
    eng = UCIEngine()
    out: List[str] = []
    eng.cmd_isready(capture_writer(out))
    assert out == ["readyok"]


def test_position_and_go_depth():
    eng = UCIEngine()
    # Starting position and two opening moves
    eng.cmd_position(["startpos", "moves", "e2e4", "e7e5"])  # type: ignore[arg-type]
    # Depth-limited search should produce a bestmove and an info line
    out: List[str] = []
    eng.cmd_go(["depth", "1"], capture_writer(out))

    def has_bestmove() -> bool:
        return any(line.startswith("bestmove ") for line in out)

    _wait_until(has_bestmove, timeout_ms=2000)
    assert any(line.startswith("info depth ") for line in out)
    assert any(line.startswith("bestmove ") for line in out)


def test_position_fen_and_go_movetime():
    eng = UCIEngine()
    # Simple FEN: K vs K
    fen = "8/8/8/8/8/8/8/K6k w - - 0 1"
    eng.cmd_position(["fen", *fen.split()])
    out: List[str] = []
    eng.cmd_go(["movetime", "10"], capture_writer(out))

    def has_bestmove2() -> bool:
        return any(line.startswith("bestmove ") for line in out)

    _wait_until(has_bestmove2, timeout_ms=2000)
    assert any(line.startswith("info depth ") for line in out)
    assert any(line.startswith("bestmove ") for line in out)


def _wait_until(predicate: Callable[[], bool], timeout_ms: int = 1000) -> None:
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    # Allow final check for assertion to fail with test's own message
