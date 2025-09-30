# Chess Web GUI Vision

## Purpose
The `chess_web_gui` repository hosts a standalone web client that can run in any
browser, connect to remote chess engines over HTTP, or drive local engines via
UCI. This document captures the minimum product and technical direction required
to ship a dependable first release without assuming knowledge of the engine
codebase.

## Product Goals
- Provide a clean board experience that supports three match types: Human vs
  Human, Human vs Engine, and Engine vs Engine.
- Allow players to choose between connecting to a hosted HTTP engine or loading
  a local UCI executable, with a consistent UX for both connectors.
- Surface the engine’s analysis (scores, principal variation, telemetry) in a
  way that is understandable for casual players yet powerful for advanced users.
- Keep the architecture modular so future features (puzzles, training modes,
  accounts) can be layered without rewriting the core game loop.

## Core Experience
1. **Board & Move Entry** – responsive board with drag, tap, or keyboard move
   entry, legal move highlights, and history.
2. **Match Controller** – orchestrates the selected matchup:
   - Human vs Human: local turn-taking with optional clocks.
   - Human vs Engine: pushes player moves to the selected engine connector and
     plays engine replies automatically.
   - Engine vs Engine: alternates two connectors (any mix of HTTP and UCI) while
     streaming evaluations.
3. **Analysis Panel** – displays engine scores, PV, depth, nodes, and time for
   whichever engine is active.
4. **Session Persistence** – local storage (e.g., IndexedDB) retains the latest
   session configuration and last `game_id` when using the HTTP API.

## System Overview
- **UI Layer** – component library (React/Vue/Svelte) implementing board,
  controls, telemetry panels, and dialogs.
- **State Store** – centralized state (Redux Toolkit, Zustand, Pinia, etc.) to
  track board state, clocks, connectors, pending analysis, and configuration.
- **Engine Connectors** – interchangeable adapters:
  - `ApiEngineConnector` handles HTTP requests against the hosted engine.
  - `UciEngineConnector` manages a spawned UCI process via WebAssembly/bridge or
    desktop host (Electron/Tauri) if the browser cannot spawn processes.
- **Persistence** – lightweight storage for UI preferences, last engine
  selection, and saved positions.

## HTTP Engine Integration
Configure the base URL at runtime (environment variables or settings panel).
Every request is JSON over HTTPS. Auth is currently out of scope; plan for API
keys once introduced.

### Session Lifecycle Endpoints
| Method | Path | Purpose | Request Body | Key Response Fields |
| --- | --- | --- | --- | --- |
| `POST` | `/api/games` | Create a new engine-backed game session. | _None_ | `game_id`, `fen` (start position). |
| `GET` | `/api/games/{game_id}/state` | Fetch current board state. | _None_ | `fen`, `turn`, `legal_moves` (UCI), `move_history`, `status` (`in_progress`, `checkmate`, `stalemate`, `draw`), `last_move`, optional clocks. |
| `POST` | `/api/games/{game_id}/move` | Submit a UCI move. | `{ "move": "e2e4" }` | Updated state payload; `error` when illegal. |
| `POST` | `/api/games/{game_id}/undo` | Revert the last ply. | _None_ | Updated state payload. |
| `POST` | `/api/games/{game_id}/position` | Load an arbitrary position. | `{ "fen": "FEN string" }` | Updated state payload or `error` for invalid FEN. |

### Search Endpoint
`POST /api/games/{game_id}/search`
- **Request body**: any combination of `depth` (plies), `movetime_ms` (time per
  search), `tt_max_entries` (transposition table size hint).
- **Response fields**: `best_move`, `ponder`, `score` (`{ "cp": int }` or
  `{ "mate": plies }`), `pv` (array of UCI moves), `nodes`, `qnodes`,
  `seldepth`, `time_ms`, `iters` (array of per-depth stats), `tt_*` telemetry
  (`hits`, `stores`, `replacements`, `size`, `hashfull`). Surface nulls
  gracefully when searches abort early.

### Perft Endpoint (Developer Tooling)
`POST /api/perft`
- **Request body**: `{ "fen": "...", "depth": int }`.
- **Response**: `{ "nodes": int }`. Use in an advanced diagnostics screen.

### Error Model & Telemetry
- Responses include either a `detail` string (FastAPI validation) or a structured
  `{ "error": { "code": str, "message": str }, "request_id": str }` envelope.
  Display the message to the user and log the request ID for debugging.
- Expect `404` when a `game_id` is stale; prompt the user to create a new
  session. Retry idempotent requests on network failure with exponential backoff.

## UCI Engine Integration
Support loading a local engine binary provided by the user. The connector must
follow the Universal Chess Interface handshake and command set below.

### Startup Sequence
1. Launch the engine process.
2. Send `uci` and wait for `uciok` while recording declared `option` lines for
   configuration UI.
3. Send `isready` and wait for `readyok` before issuing further commands.
4. Use `setoption name <Name> value <Value>` for any user-selected options.
5. Call `ucinewgame` when starting a new match.

### Position & Search Commands
- `position [startpos | fen <FEN>] [moves <move1> <move2> ...]` – set the board.
- `go` variants to support:
  - `go movetime <ms>`
  - `go depth <plies>`
  - `go wtime <ms> btime <ms> winc <ms> binc <ms>` for clock-based games.
- `stop` – request the best move immediately.
- `ponderhit` – resume from ponder mode (optional for MVP).
- `quit` – terminate the engine when the connector shuts down.

### Parsing Responses
- Handle `bestmove <move> [ponder <move>]` and intermediate `info` lines. Map
  `info` tokens (`depth`, `seldepth`, `score cp`, `score mate`, `nodes`, `time`,
  `pv`, `hashfull`, etc.) into the shared analysis panel schema used by the HTTP
  connector so the UI can reuse components.

## Match Flow Scenarios
- **Human vs Human**: maintain board state locally; optionally run analysis in
  the background using either connector without affecting the move log.
- **Human vs Engine**: after a human move, submit it via the active connector.
  When using HTTP, call `/move` then `/search` (if auto-analysis is enabled).
  For UCI, send `position` + `go` and await `bestmove`.
- **Engine vs Engine**: instantiate two connectors (any mix of HTTP and UCI) and
  alternate `go` commands. Record both evaluations for spectators and allow
  pausing/resuming.

## Configuration UX
- Engine selection dialog with two tabs: **Hosted Engine** (base URL input,
  optional API key) and **Local Engine** (file picker for executable, list of
  UCI options). Persist choices for quick relaunches.
- Match setup screen selects players (Human or specific engine connector), time
  control, starting position/FEN, and optional analysis presets.

## Observability & Quality
- Log every engine interaction with timestamps, payloads, and outcomes to aid
  support.
- Instrument frontend metrics for move latency, engine response time, and error
  rates.
- Provide a developer console overlay that surfaces raw engine messages for
  troubleshooting while keeping the main UI focused on players.

## Delivery Checklist
- [ ] Implement responsive board supporting drag/tap/keyboard.
- [ ] Complete HTTP connector covering all endpoints above with retries and
      error handling.
- [ ] Complete UCI connector supporting the command set above with configurable
      options.
- [ ] Build configuration UI for selecting match type and engines.
- [ ] Render analysis telemetry consistently across connectors.
- [ ] Add Playwright/Cypress flows for each match scenario.
