# Plan 6: Tooling, Tests & CI

## Goal
Establish robust developer tooling, tests, and CI to maintain quality.

## Scope
- Linting (`ruff`), formatting (`black`), and type checks (optional `mypy`).
- Pytest test harness with coverage reporting.
- CI workflow running build/format/lint/tests on pushes and PRs.

## Deliverables
- Make targets for build/test/lint/format.
- Pytest config and coverage thresholds for core engine.
- GitHub Actions (or equivalent) workflow file.

## Tasks
- Configure `ruff` and `black` with repo conventions.
- Add test suites mirroring `src/` structure; perft and API tests included.
- Wire CI to run on matrix of Python versions if desired.

## Exit Criteria
- CI green; coverage ≥80% for `src/engine`, `src/search`, `src/eval`.

## Risks/Notes
- Keep tests deterministic and time-bounded; avoid flaky timeouts.

