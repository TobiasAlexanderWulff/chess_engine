# Agent Rules for src/

Scope: This file applies to the entire `src/` tree and refines (but does not contradict) the repository’s root guidelines. A more deeply nested `AGENTS.md` may override these rules for its subtree.

## Architecture & Layering
- Respect layers: representation → move gen → search → evaluation → protocol (UCI/HTTP) → CLI.
- Core engine code (representation, move gen, search, eval) must be pure and deterministic: no I/O, no logging, no randomness, no wall‑clock queries. Example: a function like `evaluate()` must always return the same value for the same position across runs and must not use non‑deterministic inputs like `time.time()`.
- Enforce acyclic dependencies across modules. If a shared type is needed, introduce it in the lowest reasonable layer (e.g., `engine/`) to avoid cycles.
- Keep modules small and focused. Prefer explicit imports over dynamic/module‑level side effects.

## Dependencies & Boundaries
- Core engine (`engine/`, `search/`, `eval/`) may depend on the standard library only.
- External libraries (web, CLI, serialization) are allowed only in `protocol/` and `cli/` (and their subtrees such as `protocol/http`).
- Feature flags and integration points must be injected via parameters/config objects rather than read from globals or environment.

## State, Errors, and Logging
- No global mutable state. Pass state explicitly; prefer immutable data where practical.
- Core modules raise exceptions; they do not print or log. Logging belongs in `protocol/` and `cli/` layers.
- Define module‑specific error types close to where they are raised. Provide a common base exception (e.g., `ChessEngineError`) that all specific engine errors inherit from.

## Performance Guidelines (hot paths matter)
- Avoid allocations and object churn in move generation and search loops; preallocate and reuse buffers.
- Minimize indirection in hot paths: prefer local variables, avoid extra call layers and dynamic dispatch in tight loops.
- Keep critical structures compact (e.g., bitboards, packed structs). Favor simple data layouts over deep class hierarchies.
- Avoid hidden work: comprehensions/itertools are fine if they do not allocate excessively; measure when unsure.
- Add optional profiling hooks only via dependency injection and ensure they are no‑ops in default builds (no I/O in core).

## Concurrency & Thread-Safety
- Shared resources (e.g., transposition tables, history counters, killer moves) must be safe under parallel search. Prefer thread‑local or sharded designs; if sharing, use proven concurrency primitives and avoid fine‑grained contention in hot paths. Data races are not allowed; document memory ordering assumptions when applicable.

## Concurrency & Timing
- Time management and parallelism belong to search/time‑mgmt modules; they must remain deterministic under fixed seeds/config.
- Do not read wall‑clock time directly in core evaluation or move generation.

## Coding Style & Types
- Follow repo conventions: 4 spaces, max line length 100, `snake_case` for functions/vars, `PascalCase` for types, constants SCREAMING_SNAKE_CASE.
- Provide type hints for public APIs and performance‑sensitive internal functions. Docstrings for complex algorithms (e.g., in `search/`) should briefly outline the algorithm; docstrings for heuristics (in `eval/`) should link to the source (e.g., academic paper or article) of the heuristic.

## Testing & Bench Expectations
- Every new engine feature must have unit tests mirroring paths under `tests/`.
- For move generation/search changes, include or update perft baselines and micro‑bench notes (numbers, hardware, command used) in PR description or adjacent docs.
- Core behavior must be reproducible: no reliance on unordered dict iteration, random seeds, or platform‑specific UB.
- Versioning for baselines: bump `project.version` in `pyproject.toml` after each patch/minor/major change. Benchmark baselines are stored as `assets/benchmarks/baseline-<version>.json`; do not overwrite prior versions.

## Protocol & CLI Isolation
- `protocol/` (UCI/HTTP) adapts the engine for I/O; it may handle logging, serialization, and environment access. Do not leak I/O concerns back into core modules.

## Definition of Done (checklist)
- API surface documented (docstrings) and type‑annotated where meaningful.
- Tests added/updated under `tests/` with deterministic expectations.
- For hot‑path changes: note perft/bench impact and rationale; ensure no new I/O or globals in core.
- Code formatted (`black`), linted (`ruff`), and adheres to layering rules above.
