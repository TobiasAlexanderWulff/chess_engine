# Plan 1: API Contract & Repo Scaffolding

## Goal
Define a stable HTTP API contract and scaffold the repository to support API-first development.

## Scope
- Specify endpoints, request/response schemas, and error model.
- Define an internal engine API (interfaces for Board/Game/Search) that the HTTP layer calls.
- Choose initial stack (Python FastAPI for HTTP; engine in Python initially).
- Scaffold project structure per AGENTS.md.

## Deliverables
- OpenAPI spec (YAML) capturing endpoints and schemas.
- Internal engine API definition: module-level interfaces/types for Board, Move, Game, and SearchService; docstring contracts.
- Project layout: `src/`, `tests/`, `scripts/`, `assets/` (empty stubs OK).
- Make targets: `make build`, `make test`, `make run`, `make lint`, `make format`.
- Placeholder modules for `engine`, `search`, `eval`, `protocol/http`, `cli`.
- Logging/monitoring scaffolding: structured logging, request IDs, basic request/response logging with PII-safe redaction.

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
- Errors (structured): `{error: {code: string, message: string, type: string, request_id: string, field_errors?: [{field: string, code: string, message: string}]}}` with appropriate HTTP status.

## Tasks
- Decide stack: Python (FastAPI) for API, Python engine to start.
- Define internal engine API (interfaces and module boundaries) and example adapters for HTTP.
- Author OpenAPI spec and example payloads.
- Create repo structure and Make targets.
- Add minimal FastAPI app skeleton and health endpoint.
- Add structured logging middleware (request IDs) and basic counters/hooks for monitoring.

## Exit Criteria (Stage Gate)
- OpenAPI spec reviewed/frozen; skeleton app serves `/healthz`.
- Internal engine API documented and referenced by HTTP handlers.
- Structured logging present with request IDs; error schema implemented.
- Lint/format/test targets run successfully in CI locally.

## Risks/Notes
- Contract churn: mitigate with examples and schema review.
- Keep engine API behind internal interfaces to allow future Rust/C++ swap.
