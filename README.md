# Chess Engine (API-First)

This repository will host an API-first chess engine. Planning documents are in `docs/plans/`:

- `docs/plans/meta-plan.md` – overall sequencing, stage gates, and principles.
- `docs/plans/plan-01-api-contract-and-scaffolding.md` – API contract and repo scaffolding.
- `docs/plans/plan-02-board-representation-and-fen.md` – board + FEN I/O.
- `docs/plans/plan-03-move-generation-and-perft.md` – legal move gen + perft.
- `docs/plans/plan-04-evaluation-and-minimal-search.md` – eval + minimal search.
- `docs/plans/plan-05-http-api-and-sessions.md` – HTTP API + sessions.
- `docs/plans/plan-06-tooling-tests-and-ci.md` – tooling, tests, and CI.
- `docs/plans/plan-07-performance-and-search-features.md` – performance + features.
- `docs/plans/plan-08-uci-and-cli.md` – optional UCI + CLI.

Follow the meta plan to proceed with implementation.

## Quick Start (Dev)
- Install deps: `python -m pip install -e .[dev]`
- Run API: `make run` then open `http://localhost:8000/healthz`
- Tests: `make test`
- Lint/format: `make lint` / `make format`

Project structure follows `AGENTS.md` with core engine in `src/engine`, search in `src/search`, and the HTTP layer in `src/protocol/http`. Core modules are pure/deterministic; all I/O stays in protocol/CLI layers.
