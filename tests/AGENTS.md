# Agent Rules for tests/

Scope: This file applies to the entire `tests/` tree and complements the repository’s root guidelines. A more deeply nested `AGENTS.md` may override these rules for its subtree.

## Structure & Naming

- Mirror `src/` paths (e.g., tests for `src/search/` live under `tests/search/`).
- Test files are named `test_*.py`. Keep tests small and focused on one behavior.
- Common fixtures live in `tests/conftest.py` (engine instances, canonical positions, temp dirs).

## Determinism & Isolation

- Tests must be deterministic: fix random seeds, avoid time‑based assertions, and do not rely on wall‑clock timing.
- No external I/O or network by default. Use `tmp_path` for any filesystem work and keep artifacts small and short‑lived.
- Avoid sleeps and flakiness. If timing is relevant, assert on logical signals rather than durations.

## Markers & Runtime Budget

- Mark long‑running tests with `@pytest.mark.slow` and micro‑benchmarks with `@pytest.mark.bench`.
- Default test run should exclude slow/bench. Example invocation: `python -m pytest -q -m "not slow and not bench"` (or configure equivalently in CI).

## Perft & Micro‑Bench Conventions

- Perft correctness tests must assert exact node counts for canonical positions. Store any position data under `assets/` and reference by name, not by ad‑hoc FEN literals spread across tests.
- Depth targets should keep default runs fast; push deeper checks under `@pytest.mark.slow`.
- Keep individual test assets under `assets/` small (e.g., max 1MB); justify any larger files in the Pull Request and prefer compressed or programmatically generated data when feasible.
- Micro‑bench tests are for local comparison only; they must be excluded from default runs and avoid noisy sources (GC, logging, cold caches). Document setup/warmup in the test or adjacent docstring, including key hardware specs and the exact command used for local comparison.

## Coverage & Quality

- Aim for ≥ 80% coverage on core engine modules (`engine/`, `search/`, `eval/`) and ≥ 60% on protocol and CLI modules, where full coverage is often less critical. Prefer unit tests over end‑to‑end for diagnosing regressions.
- Test public APIs first; add targeted tests for edge cases (checks, pins, promotions, castling, repetitions, underflows/overflows for counters, etc.).

## Execution (DO NOT EXECUTE TESTS BY YOURSELF FOR NOW! - SKIP THIS)

- ~~Preferred commands: `make test` or `python -m pytest -q`.~~
- Keep tests portable across platforms and Python versions supported by the project.

## Definition of Done (checklist)

- Tests mirror `src/` structure and naming; slow/bench are properly marked.
- Deterministic behavior verified; seeds fixed where randomness exists.
- Perft expectations updated when move generation/search change; numbers and rationale documented in PRs.
- No unintended I/O or network; uses `tmp_path` when needed.
 - When updating performance-sensitive code, bump project version in `pyproject.toml` and generate a new versioned benchmark baseline via `make bench` (baseline-<version>.json) to preserve historical comparison.
