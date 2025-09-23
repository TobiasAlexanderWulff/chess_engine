# Plan 8 (Optional): UCI Protocol & CLI

## Goal
Provide a UCI-compatible adapter and local CLI runner for GUIs/tools.

## Scope
- UCI protocol handler in `src/protocol/uci/`.
- CLI to run engine locally and interact via stdin/stdout.
- Feature choices documented explicitly (e.g., pondering initially disabled unless enabled via config).

## Deliverables
- UCI loop supporting required commands (uci, isready, ucinewgame, position, go, stop, quit).
- Explicit handling policy for pondering: off by default; configuration flag `uci.ponder` to enable; documented behavior for `ponderhit` and `stop`.
- Integration tests using EPD suites and sample GUI interaction.

## Tasks
- Map UCI commands to engine APIs and search controls via the unified search controller (shared with HTTP).
- Ensure deterministic output; parse/format PV lines.
- If pondering enabled, implement background search tied to `ponderhit` with safe cancellation.

## Exit Criteria
- Plays via common GUIs; passes basic UCI conformance scenarios.
- If pondering disabled (default), `ponderhit` is gracefully ignored and documented; if enabled, correctness verified in tests.

## Risks/Notes
- Keep isolated from engine core; no direct I/O in core modules.
