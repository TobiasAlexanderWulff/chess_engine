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

## Status
- ✅ Zobrist-based transposition table with replacement/aging, configurable size caps, and
  instrumentation (hits, lower/upper/exact counts, replacements).
- ✅ Iterative deepening with aspiration windows, fail-high/low expansion, and cumulative search
  telemetry (nodes, qnodes, seldepth, hashfull, TT stats, fail counts, re-searches).
- ✅ Killer moves, history heuristic, SEE-based move ordering, futility pruning, and TT move
  prioritization wired into the search loop.
- ✅ Time management via `movetime_ms`, repetition-aware draw detection, and TT-bound search
  status reporting exposed through the HTTP API.
- 🚧 Benchmark baseline, comparative metrics, and tuning narrative remain outstanding.
- 🚧 Additional pruning ideas (LMR/NMP toggles) exist in code but require documentation of
  heuristics and guardrails.

## Next Actions
- Capture benchmark suite results (nodes/s, depth vs. time, TT hit rate) before/after tweaks and
  record them under Plan 7.
- Document heuristics currently guarded by flags (`enable_pvs`, `enable_nmp`, `enable_lmr`,
  `enable_futility`) and define default policy.
- Evaluate remaining enhancements (e.g., late-move reductions tuning, singular extensions) and
  decide on scope.

## Benchmark Protocol
Use the repo’s benchmark harness to produce reproducible metrics and detect regressions.

- Command:
  - `make bench` (writes a dated JSON under `assets/benchmarks/`).
  - Overrides: `BENCH_MOVETIME_MS`, `BENCH_DEPTH`, `BENCH_HASH_MB`, `BENCH_ITERATIONS`, `BENCH_OUT`.
- Positions suite lives at `assets/benchmarks/positions.json`; add cases as needed with clear names.
- Archive baseline artifacts alongside PRs and summarize deltas (nodes/s, average depth at fixed
  time, TT hit rate, fail-high/low, re-searches) in this document.

## Changelog
- 2025-09-26: Updated scope to reflect shipped TT, ordering, aspiration, and telemetry; noted
  outstanding benchmarking/tuning work.
