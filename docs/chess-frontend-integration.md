# Chess Engine HTTP API Frontend Guide

## Purpose & Audience
- Summarize the HTTP contracts this engine exposes for a future web GUI.
- Highlight session lifecycle, payloads, and telemetry that the UI should surface.
- Capture engine strengths and current risks that influence UX decisions.

## Service Overview
- Base URL (local dev): `http://localhost:8000`.【F:docs/openapi.yaml†L5-L7】
- Health probe: `GET /healthz` → `{ "status": "ok" }` for readiness checks.
  【F:docs/openapi.yaml†L8-L21】【F:src/protocol/http/app.py†L73-L76】
- All endpoints speak JSON over HTTP; 4xx errors return FastAPI validation details or
  structured error envelopes with `error.code`, `error.message`, and `request_id` for
  correlation.【F:docs/openapi.yaml†L332-L363】【F:src/protocol/http/app.py†L63-L68】

## Session Model
- Games live in an in-memory, thread-safe store keyed by `game_id`; sessions
  persist until the service restarts or an explicit delete is added later.
  【F:src/protocol/http/session.py†L10-L50】
- Creating a game (`POST /api/games`) returns `{game_id, fen}` seeded with the standard
  start position.【F:docs/openapi.yaml†L22-L31】【F:src/protocol/http/app.py†L77-L82】
- _Important_: No TTL or eviction yet; multi-user deployments should plan
  external state or explicit cleanup once concurrency requirements are known
  (see Plan 5 backlog).【F:docs/plans/plan-05-http-api-and-sessions.md†L24-L47】

## Core Game Endpoints
- Fetch state: `GET /api/games/{game_id}/state`.
  - Returns FEN, legal UCI moves, checkmate/stalemate/draw flags, last move,
    and full move history for the UI to render clocks, move list, and
    highlights.【F:docs/openapi.yaml†L32-L49】【F:src/protocol/http/app.py†L83-L96】
- Set position: `POST /api/games/{game_id}/position` with `{ "fen": str }`.
  - Validates FEN; invalid strings emit `400 invalid FEN`. Use to resume saved games or
    load puzzles.【F:docs/openapi.yaml†L50-L79】【F:src/protocol/http/app.py†L98-L116】
- Make move: `POST /api/games/{game_id}/move` with `{ "move": "e2e4" }` in UCI
  format.
  - Illegal or malformed moves return `400` with either parser text or
    `illegal move`. UI should surface these messages to help users debug
    input.【F:docs/openapi.yaml†L80-L110】【F:src/protocol/http/app.py†L118-L141】
- Undo: `POST /api/games/{game_id}/undo` reverts a ply; returns the refreshed
  state.
  - Errors (e.g., empty history) surface as 400 with a descriptive `detail`
    string. Disable the control when `move_history` is empty.
    【F:docs/openapi.yaml†L146-L165】【F:src/protocol/http/app.py†L199-L216】

## Search Endpoint & Telemetry
- `POST /api/games/{game_id}/search` accepts optional `depth`, `movetime_ms`,
  and `tt_max_entries` to tune search effort.
  【F:docs/openapi.yaml†L111-L145】【F:src/protocol/http/app.py†L143-L182】
- Response fields to visualize:
  - `best_move`: next engine move (nullable when search aborts early).
  - `score`: either `{ "cp": centipawns }` or `{ "mate": plies }`; display both formats.
  - `pv`: principal variation list for move arrows/annotations.
  - `nodes`, `qnodes`, `seldepth`, `time_ms`: power any depth/time HUD.
  - TT telemetry (`tt_hits`, `tt_exact_hits`, `tt_lower_hits`, `tt_upper_hits`,
    `tt_probes`, `tt_stores`, `tt_replacements`, `tt_size`, `hashfull`) enables advanced
    inspector panels for engine enthusiasts.
  - `iters`: per-depth timing/node stats for iterative deepening progress
    bars.【F:docs/openapi.yaml†L234-L331】
- Frontend should offer presets (e.g., depth vs. movetime) and reflect
  outstanding performance work noted in the engine status report (profiling,
  telemetry). Highlight that scores may fluctuate due to known search cost
  issues.【F:docs/engine-status-report.md†L3-L64】

## Auxiliary Endpoint: Perft
- `POST /api/perft` with `{ "fen": str, "depth"?: int }` returns `{ "nodes": int }` for
  debugging move generation. Display as developer tooling or omit from
  user-facing UI.【F:docs/openapi.yaml†L166-L194】【F:src/protocol/http/app.py†L184-L197】

## Data Model Reference
- `GameState` schema is stable and mirrored in Pydantic models; rely on these
  fields for board rendering and status badges.
  【F:docs/openapi.yaml†L206-L233】【F:src/protocol/http/app.py†L83-L141】
- `SearchResult` schema includes nullable score semantics; handle `null`
  scores when the engine fails to produce an evaluation (rare but possible
  during aborts).【F:docs/openapi.yaml†L234-L331】
- README lists friendly summaries suitable for onboarding documentation in the frontend
  repo; reuse wording for quickstart sections.【F:README.md†L61-L79】

## Error Handling & Observability
- Expect 404 `game not found` when reusing stale IDs; redirect users to create a fresh
  session in that case.【F:src/protocol/http/app.py†L221-L225】
- Validation errors (missing body fields, out-of-range depth) automatically
  generate FastAPI 422 responses; show field-level hints if building
  forms.【F:docs/openapi.yaml†L111-L136】【F:src/protocol/http/app.py†L63-L151】
- Each request receives a `request_id` via middleware—log it in the UI console to help
  trace reports.【F:docs/openapi.yaml†L332-L363】【F:src/protocol/http/app.py†L63-L68】

## UX Recommendations
- Provide clear affordances for FEN import/export since FEN drives both
  set-position and perft operations.【F:docs/openapi.yaml†L50-L194】
- Surface move history with ability to step backward using the undo endpoint;
  disable undo when history is empty to avoid needless
  requests.【F:docs/openapi.yaml†L146-L165】【F:src/protocol/http/app.py†L199-L216】
- Consider exposing engine capabilities (quiescence, TT stats, evaluation
  heuristics) in an "Engine Insights" panel to communicate strengths and
  current focus areas.【F:docs/engine-status-report.md†L3-L64】
- Call out known performance and concurrency gaps from Plan 5 when planning
  hosted deployments; avoid assuming multi-user persistence without extra
  infrastructure.【F:docs/plans/plan-05-http-api-and-sessions.md†L24-L47】

