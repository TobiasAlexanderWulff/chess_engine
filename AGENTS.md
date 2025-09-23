# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `src/` (engine, search, eval, protocol/uci, cli).
- Tests live in `tests/` and mirror `src/` paths (e.g., `tests/search/` for `src/search/`).
- Scripts and utilities go in `scripts/` (benchmarks, perft, tooling).
- Data/assets (opening books, test positions) go in `assets/`.

Example layout:
```
src/
  engine/    # board, moves, bitboards
  search/    # alpha-beta, TT, time mgmt
  eval/      # heuristics, phase weighting
  protocol/  # UCI I/O
  cli/       # local runner
tests/
scripts/
assets/
```

## Build, Test, and Development Commands
- Prefer Make targets if present: `make build`, `make test`, `make run`.
- Python: `python -m pytest -q`, `ruff check .`, `black .`.
- Rust: `cargo build --release`, `cargo test`, `cargo fmt -- --check`.
- C/C++: `cmake -S . -B build && cmake --build build`, `ctest --test-dir build`.

Use the project’s configured toolchain when available; otherwise follow the above equivalents.

## Coding Style & Naming Conventions
- Indentation: 4 spaces; max line length 100.
- Naming: `snake_case` for functions/vars, `PascalCase` for types, `SCREAMING_SNAKE_CASE` for constants.
- Keep modules small and acyclic; core engine code must be pure and deterministic.
- Run formatters before committing (`black`, `rustfmt`, or `clang-format`).
- Document non-obvious heuristics; link references for evaluation terms.

## Testing Guidelines
- Unit tests in `tests/` mirroring `src/`. Name tests `test_*.py`, `*_test.rs`, or `*_test.cpp`.
- Add perft tests for move generator correctness and micro-benchmarks for search.
- Target ≥ 80% coverage on core engine; avoid flakiness and time-based assertions.
- Run locally via `make test` or the language-specific commands above.

## Commit & Pull Request Guidelines
- Use Conventional Commits, e.g., `feat(search): add aspiration windows`.
- Small, focused commits. Include perft/bench diffs for perf-sensitive changes.
- PRs must include: summary, linked issues, test plan, and (if perf-related) before/after metrics.
- CI must pass: build, format, lint, and tests.

## Architecture Notes
- Layers: representation → move gen → search → evaluation → protocol (UCI) → CLI.
- Keep UCI/CLI isolated from engine; no I/O in core modules.

