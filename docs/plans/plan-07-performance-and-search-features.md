# Plan 7: Performance & Search Features

## Goal
Increase playing strength and performance with classic engine features.

## Scope
- Transposition table (TT) with Zobrist hashing.
- Move ordering: TT move, killer moves, history heuristic, captures.
- Quiescence refinements and selective extensions/reductions where safe.
- Time management with nodes/time limits and aspiration windows (documented behavior and impacts).

## Deliverables
- TT module with replacement strategy and aging; instrumentation for hit/miss, cutoff reasons.
- Enhanced search with move ordering and quiescence improvements.
- Aspiration windows: documented window initialization, fail-high/low expansion logic, and observed impact (fail rate, re-search count).
- Benchmarks and metrics: nodes/s, average depth at fixed time, TT hit rate, tactical suite solve rate.

## Tasks
- Implement TT probe/store; integrate into alpha-beta and iterative deepening.
- Add killers/history; refine ordering and pruning.
- Add quiescence refinements (checks if beneficial) with safeguards.
- Implement iterative deepening with aspiration windows and time control; instrument fail-high/low statistics.
- Run baseline vs. optimized benchmarks and record deltas.

## Exit Criteria
- Demonstrated improvements with reproducible metrics:
  - +X% nodes/s on fixed suite (report actual measured delta).
  - Increased average reached depth at fixed time budget.
  - TT hit rate reported and improved over baseline.
  - Higher success rate on tactical test suite at fixed depth/time.

## Risks/Notes
- Avoid incorrect cutoffs; preserve correctness and determinism.
