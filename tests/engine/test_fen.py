from __future__ import annotations

import pytest

from src.engine.board import Board, STARTPOS_FEN


def test_startpos_round_trip() -> None:
    b = Board.from_fen(STARTPOS_FEN)
    assert b.to_fen() == STARTPOS_FEN


@pytest.mark.parametrize(
    "fen",
    [
        # Mixed pieces and empty squares, some castling rights
        "r1bqkbnr/pppp1ppp/2n5/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R b KQ - 2 3",
        # No castling rights, ep target present on rank 3 or 6
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b - e3 0 1",
        # All castling rights
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    ],
)
def test_round_trip_various_positions(fen: str) -> None:  # type: ignore[no-redef]
    b = Board.from_fen(fen)
    assert b.to_fen() == fen


@pytest.mark.parametrize(
    "fen",
    [
        "",  # empty
        "8/8/8/8/8/8/8 w - - 0 1",  # not enough ranks
        "8/8/8/8/8/8/8/8 w - - 0",  # missing fields
        "8/8/8/8/8/8/8/8 x - - 0 1",  # bad side to move
        "8/8/8/8/8/8/8/8 w A - 0 1",  # bad castling
        "8/8/8/8/8/8/8/8 w - z9 0 1",  # bad ep square
        "8/8/8/8/8/8/8/8 w - a1 -1 1",  # bad halfmove
        "8/8/8/8/8/8/8/8 w - a1 0 0",  # bad fullmove
        "9/8/8/8/8/8/8/8 w - - 0 1",  # too many squares
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNX w KQkq - 0 1",  # bad piece
    ],
)
def test_invalid_fen_raises(fen: str) -> None:
    with pytest.raises(ValueError):
        Board.from_fen(fen)
