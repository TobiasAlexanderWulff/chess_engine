# Plan 2: Board Representation & FEN I/O

## Goal
Implement deterministic board state, FEN parse/print, and invariants.

## Scope
- Board model with side to move, castling rights, en passant, half/fullmove.
- Piece representation (bitboards or arrays), mailbox optional.
- FEN parsing/printing round-trip correctness.

## Deliverables
- `Board` type and supporting structures.
- FEN parser/printer with validation and helpful errors.
- Unit tests for round-trip and edge cases (castling, EP, promotions).

## Tasks
- Choose representation (bitboards recommended for performance).
- Define Zobrist hashing seeds (allocated, not yet used by TT).
- Implement FEN → Board and Board → FEN; verify against known positions.

## Exit Criteria
- FEN round-trip tests pass for a suite of positions.
- Deterministic hashing across identical positions.

## Risks/Notes
- Correct en passant rules and halfmove counters are subtle; test carefully.

