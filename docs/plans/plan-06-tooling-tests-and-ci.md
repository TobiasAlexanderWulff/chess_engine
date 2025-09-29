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

## Status
- ✅ Make targets for build/test/lint/format committed and used by CI.
- ✅ Ruff + Black configured; pytest harness runs engine, protocol, and search suites within CI.
- ✅ GitHub Actions workflow (`ci.yml`) runs lint + tests on Python 3.10/3.11 matrix.
- 🚧 Coverage thresholds not yet enforced; coverage reporting and per-module targets remain open.
- 🚧 Benchmark protocol and baseline artifact still need to be formalized and checked in.

## Next Actions
- Introduce coverage tooling (`pytest --cov` or `coverage.py`) and enforce thresholds per plan
  (100% for FEN/move gen, ≥80% elsewhere).
- Land benchmark script/results (e.g., tactical suite nodes/s) under `assets/benchmarks/` and wire
  into documentation for Plan 7 comparisons.
- Evaluate type-checking needs (`pyright`/`mypy`) and document decision.

Versioning policy for baselines:
- After each patch/minor/major change, bump the project version in `pyproject.toml`. The `make bench` target names baseline files using the project version (e.g., `baseline-0.0.2.json`) to preserve historical baselines.

## Changelog
- 2025-09-26: Recorded existing tooling/CI state and called out outstanding coverage + benchmark
  deliverables.
