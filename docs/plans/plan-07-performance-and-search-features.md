# Plan 7: Performance & Search Features

## Goal
Increase playing strength and performance with classic engine features.

## Scope
- Transposition table (TT) with Zobrist hashing.
- Move ordering: TT move, killer moves, history heuristic, captures.
- Quiescence search and selective extensions/reductions.
- Time management with nodes/time limits and aspiration windows.

## Deliverables
- TT module with replacement strategy and aging.
- Enhanced search with move ordering and quiescence.
- Benchmarks: nodes/s, depth vs. time; before/after metrics.

## Tasks
- Implement TT probe/store; integrate into alpha-beta.
- Add killers/history; refine ordering and pruning.
- Add quiescence (captures + checks if needed).
- Implement iterative deepening with aspiration windows and time control.

## Exit Criteria
- Demonstrated NPS and strength improvements with reproducible metrics.

## Risks/Notes
- Avoid incorrect cutoffs; preserve correctness and determinism.

