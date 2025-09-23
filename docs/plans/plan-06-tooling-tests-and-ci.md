# Plan 6: Tooling, Tests & CI

## Goal
Establish robust developer tooling, tests, and CI to maintain quality.

## Scope
- Linting (`ruff`), formatting (`black`), and type checks (optional `mypy`).
- Pytest test harness with coverage reporting and runtime budget for core tests (< 5 seconds).
- CI workflow running build/format/lint/tests on pushes and PRs.
- Benchmark protocol to establish a baseline for Plan 7.

## Deliverables
- Make targets for build/test/lint/format.
- Pytest config and differentiated coverage thresholds: 100% for FEN and move generation; ≥80% for other core modules.
- CI workflow file (GitHub Actions or equivalent).
- Benchmark script and protocol (fixed seeds/positions, warm-up, iterations); baseline metrics artifact committed under `assets/benchmarks/`.

## Tasks
- Configure `ruff` and `black` with repo conventions.
- Add test suites mirroring `src/` structure; perft and API tests included.
- Add timing marks to core tests and ensure runtime < 5s on CI runners.
- Wire CI to run on matrix of Python versions if desired.
- Create benchmark positions and scripts; document how to reproduce baseline.

## Exit Criteria
- CI green; 100% coverage for FEN and move generation; ≥80% for other core.
- Core test runtime < 5 seconds on CI runners.
- Baseline benchmark produced and checked in for Plan 7 comparisons.

## Risks/Notes
- Keep tests deterministic and time-bounded; avoid flaky timeouts.
