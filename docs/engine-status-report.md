# Engine Status Report

## Current Capabilities
- **Board state & legality**: Bitboard-based `Board` supports FEN I/O, full move
  generation (including castling, en passant, promotions), in-place make/unmake,
  and Zobrist hashing for repetition tracking.【F:src/engine/board.py†L40-L53】【F:src/engine/board.py†L360-L445】【F:src/engine/board.py†L700-L906】
- **Game wrapper**: `Game` tracks move history, repetition counts, and exposes
  legality/draw helpers for protocol layers.【F:src/engine/game.py†L9-L104】
- **Evaluation**: `evaluate` blends material, piece-square tables, mobility,
  king safety, rook activity, knight outposts, and passed-pawn heuristics with
  a tapered game-phase model.【F:src/eval/__init__.py†L691-L874】
- **Search**: `SearchService` implements iterative deepening alpha-beta with
  aspiration windows, null-move pruning, LMR, futility pruning, SEE-based
  ordering, quiescence search, and a transposition table with statistics
  instrumentation.【F:src/search/service.py†L40-L985】
- **Plans alignment**: Plans 4 and 7 mark core evaluation/search deliverables as
  complete, while highlighting outstanding benchmarking and documentation
  follow-ups.【F:docs/plans/plan-04-evaluation-and-minimal-search.md†L31-L44】【F:docs/plans/plan-07-performance-and-search-features.md†L35-L54】

## Observed Flaws & Risks
- **Move generation cost**: Legal move generation clones bitboards for every
  candidate via `_apply_pseudo_to_bb`, which is correct but expensive in hot
  search paths; no specialized handling exists for pinned pieces or slider ray
  caching.【F:src/engine/board.py†L360-L445】【F:src/engine/board.py†L1088-L1167】
- **Quiescence breadth**: Quiescence uses full legal move generation before
  filtering captures, multiplying work at leaf nodes and risking search
  explosions in tactical positions.【F:src/search/service.py†L699-L799】
- **Static exchange evaluation (SEE) cost**: `see` repeatedly scans all 12
  bitboards to identify attackers for each capture, introducing significant
  overhead when ordering moves at shallow depths.【F:src/search/service.py†L222-L399】【F:src/search/service.py†L589-L677】
- **Null-move hashing**: Null-move pruning rebuilds the Zobrist hash from
  scratch instead of applying incremental toggles, negating hashing
  efficiencies and adding latency on every attempt.【F:src/search/service.py†L460-L487】
- **Protocol observability gap**: Plan 7 notes missing benchmark baselines and a
  tuning narrative, leaving search improvements without published performance
  evidence.【F:docs/plans/plan-07-performance-and-search-features.md†L35-L54】

## Improvement Opportunities
- **Targeted pseudo-legal generators**: Introduce capture-only generators for
  quiescence and SEE to avoid re-running full legality checks at leaves and
  during ordering.【F:src/search/service.py†L699-L799】
- **Incremental attack tables**: Cache directional attack masks or adopt
  bitboard sliding helpers to cut `_apply_pseudo_to_bb` cloning and SEE attack
  scans, especially for sliders and pinned-piece detection.【F:src/engine/board.py†L360-L445】【F:src/search/service.py†L222-L399】
- **Hash toggles for null moves**: Extend `Board` with explicit
  toggle/untoggle helpers so null-move pruning can update hash components
  without recomputation.【F:src/search/service.py†L460-L487】
- **Evaluation guards**: Add regression tests for tapered evaluation weights
  and pawn structure heuristics, as suggested in Plan 4 next actions, to protect
  against tuning regressions.【F:docs/plans/plan-04-evaluation-and-minimal-search.md†L41-L44】
- **Performance telemetry**: Capture nodes-per-second, TT hit rates, and PV
  depth benchmarks across standard suites to close the Plan 7 documentation
  gap.【F:docs/plans/plan-07-performance-and-search-features.md†L48-L54】

## Suggested Next Steps
1. **Profiling sprint**: Instrument move generation and SEE hot paths, then
   prototype capture-only generators to quantify branching-factor reductions.
2. **Hashing improvements**: Implement incremental null-move hashing and measure
   TT probe/store throughput before/after the change.
3. **Evaluation test harness**: Create mirrored-position and pawn-structure test
   cases to verify tapered scoring symmetry and passed-pawn bonuses.
4. **Benchmark documentation**: Establish a reproducible bench script, record
   baseline metrics, and update Plan 7 with results plus heuristic default
   rationales.【F:docs/plans/plan-07-performance-and-search-features.md†L48-L54】
