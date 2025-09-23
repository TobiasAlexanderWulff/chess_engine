# Plan 1: API Contract & Repo Scaffolding

## Goal
Define a stable HTTP API contract and scaffold the repository to support API-first development.

## Scope
- Specify endpoints, request/response schemas, and error model.
- Choose initial stack (Python FastAPI for HTTP; engine in Python initially).
- Scaffold project structure per AGENTS.md.

## Deliverables
- OpenAPI spec (YAML) capturing endpoints and schemas.
- Project layout: `src/`, `tests/`, `scripts/`, `assets/` (empty stubs OK).
- Make targets: `make build`, `make test`, `make run`, `make lint`, `make format`.
- Placeholder modules for `engine`, `search`, `eval`, `protocol/http`, `cli`.

## Endpoints (initial)
- POST `/api/games` → create game; returns `{game_id, fen}`.
- POST `/api/games/{id}/position` → set FEN; returns normalized state.
- POST `/api/games/{id}/move` → apply UCI move; returns new state and legality.
- GET `/api/games/{id}/state` → current state incl. legal moves.
- POST `/api/games/{id}/search` → `{depth?, movetime_ms?}` → `{best_move, score, pv, nodes, depth, time_ms}`.
- POST `/api/perft` → `{fen, depth}` → node counts.

## JSON Conventions
- Moves: UCI string, promotions like `e7e8q`.
- Scores: `{cp: int}` for centipawns or `{mate: int}` for mate in N.
- Errors: `{error: {code, message, details?}}` with HTTP status codes.

## Tasks
- Decide stack: Python (FastAPI) for API, Python engine to start.
- Author OpenAPI spec and example payloads.
- Create repo structure and Make targets.
- Add minimal FastAPI app skeleton and health endpoint.

## Exit Criteria (Stage Gate)
- OpenAPI spec reviewed/frozen; skeleton app serves `/healthz`.
- Lint/format/test targets run successfully in CI locally.

## Risks/Notes
- Contract churn: mitigate with examples and schema review.
- Keep engine API behind internal interfaces to allow future Rust/C++ swap.

