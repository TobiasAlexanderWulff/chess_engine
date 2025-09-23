# Plan 3: Move Generation & Perft

## Goal
Implement complete legal move generation with make/unmake and validate via perft.

## Scope
- Pseudo-legal generation for all pieces, promotions, castling, en passant.
- Legality filtering (king safety), in-check detection.
- Make/unmake with incremental state updates and hash updates.
- Perft driver and known reference positions.

## Deliverables
- `generate_legal_moves(Board) -> [Move]` and `make_move/unmake_move`.
- Perft CLI entry and HTTP endpoint (`/api/perft`).
- Test suite comparing node counts up to depth 5.

## Tasks
- Implement piece-specific generators with bitboards.
- Add pinned piece detection and check evasions.
- Implement state stack for unmake correctness.
- Build perft harness and add standard test positions.

## Exit Criteria (Gate A)
- Perft matches known nodes (depth ≥ 5) on suite; zero mismatches.

## Risks/Notes
- EP capture + pinned EP edge cases; castling through check; underpromotions.

