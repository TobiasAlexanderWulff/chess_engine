from __future__ import annotations

from src.engine.board import Board


def moves_set(b: Board) -> set[str]:
    return {m.to_uci() for m in b.generate_legal_moves()}


def test_white_castling_available_when_clear_and_not_in_check() -> None:
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    assert "e1g1" in ms
    assert "e1c1" in ms


def test_white_castling_blocked_when_in_check() -> None:
    # Same as above but a black rook on e8 gives check on e1
    fen = "4r2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)
    ms = moves_set(b)
    assert "e1g1" not in ms
    assert "e1c1" not in ms


def test_castling_moves_rook_correctly() -> None:
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    b = Board.from_fen(fen)
    # Choose king-side castle
    mv = next(m for m in b.generate_legal_moves() if m.to_uci() == "e1g1")
    b.make_move(mv)
    # After e1g1, rook must be on f1 (and h1 cleared)
    from src.engine.move import str_to_square

    f1 = str_to_square("f1")
    h1 = str_to_square("h1")
    # White rooks are tracked implicitly via move application; verify via FEN
    fen_after = b.to_fen().split()[0]
    assert fen_after.count("R") >= 1
    # Spot-check: square f1 should contain a white piece in piece placement
    # Use internal bitboards to assert rook moved
    from src.engine.board import WR

    assert (b.bb[WR] >> f1) & 1
    assert ((b.bb[WR] >> h1) & 1) == 0
