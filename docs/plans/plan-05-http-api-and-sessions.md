# Plan 5: HTTP API & Game Session Management

## Goal
Expose engine functionality over HTTP with stable contracts and in-memory sessions.

## Scope
- FastAPI app with endpoints: games, position, move, state, search, perft.
- In-memory session store keyed by `game_id` with lifecycle management.
- Request validation and consistent error responses.

## Deliverables
- HTTP server in `src/protocol/http/` with routers and Pydantic schemas.
- Session manager: create, get, update, delete; TTL optional.
- Endpoint tests covering happy paths and validation errors.

## Tasks
- Implement schemas for move/state/score types.
- Wire engine functions into handlers; serialize deterministically.
- Add logging, health, and readiness endpoints.

## Exit Criteria (Gate B)
- Endpoint tests green; API responses match OpenAPI; contracts locked.

## Risks/Notes
- Concurrency: protect session mutations; consider async synchronization.

