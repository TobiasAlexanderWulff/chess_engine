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

## Status
- ✅ FastAPI app factory registered with health, create game, state, set position, move, undo,
  search, and perft endpoints mirroring the OpenAPI contract.
- ✅ In-memory session store with create/get/set semantics powers HTTP flows; request ID logging
  and structured error envelopes are active.
- ✅ Pydantic models encode GameState (legal moves, status flags, history), search requests, and
  responses with detailed statistics.
- ✅ Test suites cover happy paths, invalid FEN/move handling, undo edge cases, and perft errors.
- 🚧 Session TTL/concurrency coordination remains on the backlog pending multi-user requirements.

## Next Actions
- Decide on session eviction/TTL policy before introducing external storage.
- Capture example request/response payloads for docs consumers.
- Evaluate concurrency requirements for multi-search scenarios (locking vs. optimistic updates)
  before moving beyond the in-memory store.
- Keep OpenAPI examples synchronized with implementation changes (search telemetry, undo,
  structured errors) as the API evolves.

## Changelog
- 2025-09-26: Marked HTTP endpoints delivered, highlighted remaining TTL/concurrency questions,
  and flagged documentation follow-ups for examples and concurrency policy.

