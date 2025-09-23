# Plan 8 (Optional): UCI Protocol & CLI

## Goal
Provide a UCI-compatible adapter and local CLI runner for GUIs/tools.

## Scope
- UCI protocol handler in `src/protocol/uci/`.
- CLI to run engine locally and interact via stdin/stdout.

## Deliverables
- UCI loop supporting required commands (uci, isready, ucinewgame, position, go, stop, quit).
- Integration tests using EPD suites and sample GUI interaction.

## Tasks
- Map UCI commands to engine APIs and search controls.
- Ensure deterministic output; parse/format PV lines.

## Exit Criteria
- Plays via common GUIs; passes basic UCI conformance scenarios.

## Risks/Notes
- Keep isolated from engine core; no direct I/O in core modules.

