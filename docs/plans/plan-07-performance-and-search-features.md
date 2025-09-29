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

- Implement capture-only quiescence (generate_captures / generate_evasions) next, then re-benchmark
  and document observed deltas.

## Benchmark Protocol
Use the repo’s benchmark harness to produce reproducible metrics and detect regressions.

- Command:
  - `make bench` (writes a versioned JSON under `assets/benchmarks/`, e.g., `baseline-0.0.1.json`).
  - Overrides: `BENCH_MOVETIME_MS`, `BENCH_DEPTH`, `BENCH_HASH_MB`, `BENCH_ITERATIONS`, `BENCH_OUT`.
- Positions suite lives at `assets/benchmarks/positions.json`; add cases as needed with clear names.
- Archive baseline artifacts alongside PRs and summarize deltas (nodes/s, average depth at fixed
  time, TT hit rate, fail-high/low, re-searches) in this document.

Versioning requirement: bump the project version in `pyproject.toml` after each patch/minor/major change so new benchmark baselines are created per version instead of overwriting prior results.

## Benchmark Results (v0.0.2)

Context: Applied null-move hashing optimization to toggle Zobrist side/EP bits instead of full
recompute. Baselines generated with `make bench` and compared via `scripts/bench_diff.py`.

- Artifacts: `assets/benchmarks/baseline-0.0.1.json`, `assets/benchmarks/baseline-0.0.2.json`.
- Command: `python3 scripts/bench_diff.py --old assets/benchmarks/baseline-0.0.1.json --new assets/benchmarks/baseline-0.0.2.json`.

Overall summary:
- nodes: 216 → 216 (+0.0%)
- time_ms: 41 → 42 (+2.4%)
- nps: 5268 → 5142 (−2.4%)

Per-position highlights:
- tactics_knights: +20.0% nps (3500 → 4200), time 6 → 5 ms.
- open_midgame: −7.1% nps (4653 → 4321), time 26 → 28 ms.
- Others unchanged within measurement noise at very short budgets.

Notes:
- At small movetime/iteration counts, variance is expected. Re-run with larger budgets and
  iterations for stable measurements (e.g., `make bench BENCH_MOVETIME_MS=2000 BENCH_ITERATIONS=3`).

Next measurement step:
- Implement capture-only qsearch (with `generate_captures()` and `generate_evasions()`), then
  re-run the same suite and update this section with new deltas.

## Changelog
- 2025-09-26: Updated scope to reflect shipped TT, ordering, aspiration, and telemetry; noted
  outstanding benchmarking/tuning work.
