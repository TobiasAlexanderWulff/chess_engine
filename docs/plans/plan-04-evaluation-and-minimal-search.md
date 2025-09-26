# Plan 4: Evaluation & Minimal Search

## Goal
Add a simple, deterministic search with a basic evaluation function.

## Scope
- Static eval: material + piece-square tables (phase-weighted optional) with hooks for mobility and king safety.
- Search: fixed-depth negamax with alpha-beta and a simple quiescence search (captures, with stand-pat and delta pruning guardrails).
- Accounting: nodes, time, depth, principal variation extraction.

## Deliverables
- `evaluate(Board) -> score_cp` deterministic.
- `search(position, depth) -> {best_move, score, pv, nodes, depth, time_ms}` including quiescence nodes in accounting.
- Mobility factor prepared (feature-flag/weight) and covered by unit tests.
- Unit tests for determinism and PV structure; tactical, mate/stalemate/draw scenarios; symmetry tests (mirrored positions yield negated scores).

## Tasks
- Implement material and PSQT tables; phase weighting if added.
- Implement negamax with alpha-beta; transposition-free initial version.
- Implement quiescence search over captures (and checks if necessary) with stand-pat evaluation.
- Add simple move ordering (captures first, MVV-LVA heuristic).
- Prepare tactical and endgame test suites (assets) and assertions.

## Exit Criteria
- Given seed positions and depth, search returns deterministic PV and score.
- Quiescence reduces horizon artifacts in tactical test positions; tests assert expected best moves at shallow depths.

## Risks/Notes
- Avoid premature optimization; keep code clear for later TT integration.

## Status
- ✅ Material and PSQT tables implemented with phase-aware weighting, mobility, king-safety,
  pawn structure, bishop pair, rook activity, and passed pawn heuristics.
- ✅ Deterministic alpha-beta search with quiescence, repetition detection, and PV extraction is
  live in `SearchService` along with tactical/endgame tests.
- ✅ Basic move ordering (captures, MVV-LVA) and SEE guardrails exist as part of the
  implementation.
- 🚧 Integration with transposition tables, killer/history ordering, and aspiration windows now
  lives in Plan 7 (implemented but tracked there for tuning/metrics).

## Next Actions
- Harden evaluation unit tests around phase weighting and pawn heuristics to protect against
  regressions introduced by Plan 7 tuning.
- Document representative evaluation scores for standard positions to inform future tuning.

## Changelog
- 2025-09-26: Marked deliverables complete, noted additional heuristics shipped, and linked
  advanced search enhancements to Plan 7 ownership.
