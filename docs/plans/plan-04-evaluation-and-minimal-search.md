# Plan 4: Evaluation & Minimal Search

## Goal
Add a simple, deterministic search with a basic evaluation function.

## Scope
- Static eval: material + piece-square tables (phase-weighted optional).
- Search: fixed-depth negamax with alpha-beta; optional quiescence later.
- Accounting: nodes, time, depth, principal variation extraction.

## Deliverables
- `evaluate(Board) -> score_cp` deterministic.
- `search(position, depth) -> {best_move, score, pv, nodes, depth, time_ms}`.
- Unit tests for determinism and PV structure.

## Tasks
- Implement material and PSQT tables; phase weighting if added.
- Implement negamax with alpha-beta; transposition-free initial version.
- Add simple move ordering (captures first, MVV-LVA heuristic).

## Exit Criteria
- Given seed positions and depth, search returns deterministic PV and score.
- Basic tactical motifs solvable at shallow depth in tests.

## Risks/Notes
- Avoid premature optimization; keep code clear for later TT integration.

