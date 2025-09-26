# Chess Engine (API-First)

An API-first chess engine focused on clean separation between the core engine, search algorithms, and protocol layers. The project is being built in stages, guided by the planning documents under `docs/plans/`.

## Table of Contents
- [Overview](#overview)
- [Current Roadmap](#current-roadmap)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
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

