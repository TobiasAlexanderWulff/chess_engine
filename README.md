# Chess Engine (API-First)

An API-first chess engine focused on clean separation between the core engine, search algorithms, and protocol layers. The project is being built in stages, guided by the planning documents under `docs/plans/`.

## Table of Contents
- [Overview](#overview)
- [Current Roadmap](#current-roadmap)
- [Quick Start](#quick-start)
- [HTTP API Reference](#http-api-reference)
- [UCI Input Guide](#uci-input-guide)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Benchmarks](#benchmarks)
- [Documentation](#documentation)
- [Community & Contributions](#community--contributions)

## Overview
This repository houses a chess engine designed to expose a robust API from day one. Core components such as board representation, move generation, evaluation, and search are implemented as deterministic modules, while any I/O (HTTP, CLI, UCI) lives in dedicated protocol layers. The staged roadmap enables incremental delivery, testing, and performance validation.

## Current Roadmap
Planning takes place through the staged plans in `docs/plans/`. Start with the meta plan, then follow the numbered plans sequentially.

| Stage | Focus |
|-------|-------|
| Meta  | Project principles, sequencing, and stage gates. |
| 01    | API contract and repository scaffolding. |
| 02    | Board representation and FEN input/output. |
| 03    | Legal move generation and perft validation. |
| 04    | Evaluation heuristics and minimal search loop. |
| 05    | HTTP API implementation and game sessions. |
| 06    | Tooling, automated tests, and CI integration. |
| 07    | Performance improvements and advanced search features. |
| 08    | Optional UCI protocol and local CLI tooling. |

## Quick Start
1. **Install dependencies**
   ```bash
   python -m pip install -e .[dev]
   ```
2. **Run the HTTP API locally**
   ```bash
   make run
   ```
   Visit [http://localhost:8000/healthz](http://localhost:8000/healthz) to verify the service.
3. **Execute the test suite**
   ```bash
   make test
   ```
4. **Lint and format the codebase**
   ```bash
   make lint
   make format
   ```

## HTTP API Reference

The engine ships with a RESTful HTTP interface, exposing endpoints for creating and
driving game sessions, launching searches, and running perft calculations. Unless
stated otherwise, responses are JSON and error conditions return `400 Bad Request`
with a descriptive `detail` message.

| Method | Path | Description | Request Body | Success Response |
|--------|------|-------------|--------------|------------------|
| GET | `/healthz` | Liveness probe confirming the service is reachable. | _None_ | `{ "status": "ok" }` |
| POST | `/api/games` | Creates a new in-memory game session and returns its identifier. | _None_ | `{ "game_id": str, "fen": str }` |
| GET | `/api/games/{game_id}/state` | Fetches the current game state, including legal moves and history. | _None_ | `GameState` payload with FEN, legal moves, and status flags. |
| POST | `/api/games/{game_id}/position` | Replaces the game state with a provided FEN position. | `{ "fen": str }` | Updated `GameState`. |
| POST | `/api/games/{game_id}/move` | Applies a UCI move string to the game. | `{ "move": str }` | Updated `GameState`. |
| POST | `/api/games/{game_id}/undo` | Reverts the most recent move in the session. | _None_ | Updated `GameState`. |
| POST | `/api/games/{game_id}/search` | Runs a search from the current position. | `{ "depth"?: int, "movetime_ms"?: int, "tt_max_entries"?: int }` | Search statistics, principal variation, and best move. |
| POST | `/api/perft` | Executes a perft calculation for the supplied FEN at a depth. | `{ "fen": str, "depth"?: int }` | `{ "nodes": int }` |

`GameState` responses contain:

- `game_id`: Session identifier.
- `fen`: Current board position in FEN notation.
- `legal_moves`: List of legal moves as UCI strings.
- `in_check`, `checkmate`, `stalemate`, `draw`: Status flags for the side to move.
- `last_move`: The most recent move in UCI format, if any.
- `move_history`: Chronological list of moves applied to the game.

## UCI Input Guide

The engine speaks the [Universal Chess Interface (UCI)](https://en.wikipedia.org/wiki/Universal_Chess_Interface) protocol, which
lets you drive it from any UCI-compatible GUI or from the command line. The snippets below demonstrate a simple, manual
interaction using `python -m chess_engine.cli.uci` (replace this command with the appropriate entry point for your build).

### 1. Start the Engine

```bash
python -m chess_engine.cli.uci
```

When the engine is ready it prints `uciok`, indicating that it understands the protocol.

### 2. Configure Options (Optional)

Use `setoption` commands to configure the engine. For example, to limit the search depth to 10 plies:

```
setoption name Depth value 10
```

Available option names depend on the current build; the engine will list them in response to the `uci` command.

### 3. Initialize a New Game

Before starting play, reset the internal state:

```
ucinewgame
isready
```

Wait for the engine to reply `readyok` before sending moves or search commands.

### 4. Provide the Position

Load a starting position using `position`. You can begin from the standard initial layout or a specific FEN string.

```
position startpos moves e2e4 e7e5 g1f3
```

The example above plays 1.e4 e5 2.Nf3, setting the engine to move on behalf of Black. Replace `startpos` with
`fen <FEN_STRING>` to continue from an arbitrary board state.

### 5. Ask the Engine to Search

The `go` command starts the search. Common parameters are `movetime` (milliseconds to think) and `depth` (maximum search depth).

```
go movetime 2000
```

The engine will analyze the position and eventually emit a `bestmove`, e.g. `bestmove b8c6`.

### 6. Iterate

After each `bestmove`, apply it to your GUI or continue the command-line session by appending it to the next `position ... moves`
sequence. Repeat the `go` command as needed.

### 7. Exit Cleanly

Send `quit` to terminate the session:

```
quit
```

This ensures the process shuts down gracefully.

## Project Structure
The repository layout follows the guidelines in `AGENTS.md`:

```
src/
  engine/     # Board state, move encoding, bitboards
  search/     # Alpha-beta, transposition tables, time management
  eval/       # Evaluation heuristics and weighting
  protocol/   # HTTP, UCI, and CLI interfaces
  cli/        # Local runner utilities
scripts/      # Benchmarks, tooling, automation
assets/       # Opening books, test positions, data files
tests/        # Mirrors src/ structure for unit and integration tests
```

## Development Workflow
- Keep core engine modules deterministic and free of I/O.
- Prefer `make` targets for common tasks (build, test, lint, format).
- Run formatting (`make format`) and linting (`make lint`) before committing.
- Add or update tests alongside any feature changes, targeting ≥ 80% coverage on critical engine modules.

## Benchmarks
The repository includes a simple, reproducible benchmark harness to track performance and search quality over time.

Purpose:
- Establish a baseline for Plan 7 (performance & search features) and detect regressions.
- Measure nodes/s, average reached depth at fixed time, TT utilization (hits/hashfull), fail-high/low rates, and PV stability across a mixed suite of positions.
- Produce JSON artifacts you can compare across commits or branches.

Run via Make:
- Default run (mixed suite, 16MB hash, 1 iteration/position) writes a versioned JSON under `assets/benchmarks/` (e.g., `baseline-0.0.1.json`):
  - `make bench`
- 1s per position, 64MB TT, two iterations, custom output path:
  - `make bench BENCH_MOVETIME_MS=1000 BENCH_HASH_MB=64 BENCH_ITERATIONS=2 BENCH_OUT=assets/benchmarks/baseline-custom.json`
- Depth-limited (no movetime):
  - `make bench BENCH_DEPTH=8 BENCH_MOVETIME_MS=`

Configuration variables (override per invocation):
- `BENCH_POSITIONS` file with FENs and optional per-position overrides (defaults to `assets/benchmarks/positions.json`).
- `BENCH_MOVETIME_MS` global movetime per position (omit to use per-position values).
- `BENCH_DEPTH` global depth cap (omit to allow time-based runs).
- `BENCH_HASH_MB` approximate transposition table size in MiB (default 16; ~16,384 entries/MiB).
- `BENCH_ITERATIONS` repeats per position; averages time/nodes/qnodes (default 1).
- `BENCH_OUT` output JSON path; default is a dated baseline under `assets/benchmarks/`.
- `BENCH_PRETTY` pretty-print JSON (default 1).
- `BENCH_PROGRESS` print progress to stderr (default 1).

Versioning and Output:
- Bump the project version in `pyproject.toml` after each patch/minor/major change. The benchmark baseline filename uses the project version to avoid overwriting prior baselines (e.g., `baseline-0.0.2.json`).
- A JSON document containing metadata (timestamp, commit, platform), per-position results (depth, time, nodes, qnodes, nps, score, PV, TT stats), and a summary across the suite.
- Use these artifacts to compare before/after changes in PRs and to populate Plan 7’s benchmark section.

Comparing baselines:
- Use the diff helper to compare two baselines and get per-position and overall deltas:
  - `python3 scripts/bench_diff.py --old assets/benchmarks/baseline-0.0.1.json --new assets/benchmarks/baseline-0.0.2.json`

## Documentation
All planning and design documents are located in `docs/plans/`:
- `meta-plan.md` – guiding principles and overall roadmap.
- `plan-01-api-contract-and-scaffolding.md`
- `plan-02-board-representation-and-fen.md`
- `plan-03-move-generation-and-perft.md`
- `plan-04-evaluation-and-minimal-search.md`
- `plan-05-http-api-and-sessions.md`
- `plan-06-tooling-tests-and-ci.md`
- `plan-07-performance-and-search-features.md`
- `plan-08-uci-and-cli.md`

Refer to these documents when implementing new features or planning contributions.

## Community & Contributions
Contributions are welcome! Please follow the repository coding standards, respect the staged roadmap, and provide clear tests and documentation for any changes. Conventional Commits are preferred (e.g., `feat(search): add aspiration windows`).
