# Plan 2: Board Representation & FEN I/O

## Goal
Implement deterministic board state, FEN parse/print, and invariants.

## Scope
- Board model with side to move, castling rights, en passant, half/fullmove.
- Piece representation (bitboards or arrays), mailbox optional.
- FEN parsing/printing round-trip correctness.
- Full Zobrist hashing implementation: initial hash computation and incremental updates for all state changes (piece moves, captures, promotions, castling, EP, side-to-move, castling/EP rights).

## Deliverables
- `Board` type and supporting structures.
- FEN parser/printer with validation and helpful errors.
- Zobrist keys (piece-square, side, castling, ep-file) and hashing utilities; `hash_init(board)` and `hash_update(board, move)`.
- Unit tests for round-trip and edge cases (castling, EP, promotions).
- Hash consistency tests across known positions and after make/unmake sequences.

## Tasks
- Choose representation (bitboards recommended for performance).
- Define and persist Zobrist hashing seeds; expose deterministic seed generation for tests.
- Implement FEN → Board and Board → FEN; verify against known positions.
- Implement `compute_hash_from_scratch` and `incremental_hash_update` and validate parity.

## Exit Criteria
- FEN round-trip tests pass for a suite of positions.
- Deterministic hashing across identical positions.
- Zobrist hashes remain stable under make/unmake; full recompute matches incremental updates.

## Risks/Notes
- Correct en passant rules and halfmove counters are subtle; test carefully.
