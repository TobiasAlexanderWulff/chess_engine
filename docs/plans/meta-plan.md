# Meta Plan: API-First Chess Engine

## Overview
- Build an API-first chess engine that any frontend can consume.
- Sequence work into gated phases to ensure correctness before strength.
- Keep engine core pure/deterministic; isolate I/O in protocol layers.

## Phases (7 Core + 1 Optional)
1. API Contract & Repo Scaffolding – ✅ Completed (repo layout, OpenAPI draft, Make targets).
2. Board Representation & FEN I/O – ✅ Completed (bitboards, Zobrist, FEN parser/serializer).
3. Move Generation & Legality (+ Perft) – ✅ Completed (legal generator, perft parity harness).
4. Evaluation & Minimal Search – ✅ Completed (material + PSQT eval, alpha-beta + quiescence).
5. HTTP API & Game Session Management – ✅ Completed (FastAPI app, session store, endpoints).
6. Tooling, Tests & CI – ⚠️ Partially complete (Make, pytest, lint, CI live; coverage/bench TBD).
7. Performance & Search Features – ⚙️ In progress (TT, ordering, aspiration done; metrics pending).
8. (Optional) UCI Protocol & CLI – ⏳ Not started beyond scaffolding.

## Stage Gates
- Gate A (after Plan 3): Perft parity on suites (depth ≥ 5). No search work proceeds until move generator is correct.
- Gate B (after Plan 5): API contracts are locked; future changes must be additive and backward compatible.

## Principles
- API-first: stable JSON contracts, FEN + UCI move strings.
- Purity: no I/O in `src/engine`, `src/search`, `src/eval`.
- Tests-first on core; ≥80% coverage target for engine modules.
- Determinism: reproducible searches and PVs; seed any randomness.

## Deliverables by Phase
- See individual plans:
  - Plan 1: docs/plans/plan-01-api-contract-and-scaffolding.md
  - Plan 2: docs/plans/plan-02-board-representation-and-fen.md
  - Plan 3: docs/plans/plan-03-move-generation-and-perft.md
  - Plan 4: docs/plans/plan-04-evaluation-and-minimal-search.md
  - Plan 5: docs/plans/plan-05-http-api-and-sessions.md
  - Plan 6: docs/plans/plan-06-tooling-tests-and-ci.md
  - Plan 7: docs/plans/plan-07-performance-and-search-features.md
  - Plan 8: docs/plans/plan-08-uci-and-cli.md

## Metrics
- Correctness: perft node counts vs. known values, checkmate/stalemate detection, legal move coverage.
- Quality: CI green on build/format/lint/tests; coverage ≥80% for core.
- Performance: nodes/s, best-move depth vs. time; Elo vs. baseline (later, Plan 7).

## Dependencies
- Plan 1 is foundational for external contracts (OpenAPI, repo skeleton).
- Plan 2 provides `Board` and FEN I/O used by Plans 3–5.
- Plan 3 provides legal move generation required by Plans 4, 5, and 7.
- Plan 4 depends on Plan 3 (legal moves) and Plan 2 (state representation).
- Plan 5 depends on Plan 1 (API contract), Plan 2 (FEN/state), and Plan 3 (moves).
- Plan 6 integrates tooling/tests for Plans 2–5 and prepares metrics for Plan 7.
- Plan 7 builds on Plans 3–6; Plan 8 is orthogonal to HTTP and can start after Plan 5.

## Conflicts & Interactions
- Unified control plane for search: both HTTP and UCI must route `go`, `stop`, and cancellation through a single search controller to avoid race conditions.
- Cancellation semantics: define cooperative cancellation points (node loop, quiescence entry) and ensure `stop` results in a best-known move and stats.
- Concurrency: serialize session-bound searches; document behavior when concurrent HTTP and UCI commands target the same game/session.

## Current Focus
- Finalize Plan 6 by codifying coverage thresholds and checking in benchmark artifacts.
- Complete Plan 7 metrics/benchmarking and document observed gains over the minimal search.
- Plan 8 remains optional; revisit once HTTP surface stabilizes and performance goals are met.
