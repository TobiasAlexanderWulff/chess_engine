# Meta Plan: API-First Chess Engine

## Overview
- Build an API-first chess engine that any frontend can consume.
- Sequence work into gated phases to ensure correctness before strength.
- Keep engine core pure/deterministic; isolate I/O in protocol layers.

## Phases (7 Core + 1 Optional)
1. API Contract & Repo Scaffolding
2. Board Representation & FEN I/O
3. Move Generation & Legality (+ Perft)
4. Evaluation & Minimal Search
5. HTTP API & Game Session Management
6. Tooling, Tests & CI
7. Performance & Search Features
8. (Optional) UCI Protocol & CLI

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
- Plan 4 depends on Plan 3 (legal move generation).
- Plan 5 depends on Plan 1 (API contract) and Plan 2/3 (state + moves).
- Plan 7 builds on Plans 3–6; Plan 8 is orthogonal to HTTP and can be done after Plan 5.

## Next Step
- Execute Plan 1 to lock API schemas and scaffold the repository layout.

