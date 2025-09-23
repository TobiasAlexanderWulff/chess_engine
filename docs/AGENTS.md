# Docs Agent Guidelines

These instructions apply to the `docs/` directory and its subtree.
They clarify how and when to adjust planning documents, add new plans,
and keep documentation in sync with implementation.

## Purpose
- Keep the planning docs (`docs/plans/`) the single source of truth for scope, sequencing,
  stage gates, and quality bars.
- Make changes traceable, reviewable, and consistent with repository-wide conventions.

## Scope & Precedence
- Scope: Only files under `docs/`.
- Precedence: These rules complement the root `AGENTS.md`. If there is conflict, direct
  user/developer instructions win, then root `AGENTS.md`, then this file.

## When to Update Docs
- Before changing scope: If implementation deviates from the current plan (new features,
  removed deliverables, re-sequencing), update the relevant plan file first.
- On dependency changes: When a plan starts depending on new modules or tools, document it.
- On acceptance criteria changes: Adjust exit criteria and stage gates to stay testable.
- On API or contract changes: Update OpenAPI and the relevant plan(s) before code.
- After significant decisions: Record as an ADR if it impacts architecture (see “ADRs”).

## Plans: Structure and Conventions
- Location: `docs/plans/`.
- Naming: `plan-XX-kebab-topic.md` (two-digit index, descriptive topic). Examples:
  - `plan-01-api-contract-and-scaffolding.md`
  - `plan-07-performance-and-search-features.md`
- Sections (recommended): Goal, Scope, Deliverables, Tasks, Exit Criteria, Risks/Notes.
- Line width: ≤100 characters; use concise bullets; avoid deep nesting.

## Creating New Plans or Subplans
- New plan: Create when a chunk of work introduces a new domain (e.g., “endgame tablebases”),
  spans multiple iterations, or needs its own gate/metrics.
- Subplan: Create `plan-XXa-...`, `plan-XXb-...` when a plan grows beyond ~6–8 key tasks or
  has parallelizable tracks (e.g., “plan-07a-transposition-table.md”). Reference subplans from
  the parent plan’s “Deliverables”/“Tasks”.
- Cross-cutting notes: If a change affects multiple plans, add a short note to each impacted
  plan and link to a single source plan for details.

## Adjusting Existing Plans
- Minor edits (typos, clarifications): Inline update; no special callout needed.
- Scope changes: Add a short “Changelog” section at the end of the plan describing what changed
  and why (one or two bullets per change).
- Dependency changes: Update the “Dependencies” in `meta-plan.md` and the specific plan(s).
- Metrics changes: Replace vague goals with measurable metrics (e.g., NPS, TT hit rate, solve
  rate). Update the benchmark protocol if needed.

## Meta Plan
- Keep `docs/plans/meta-plan.md` authoritative for sequencing, dependencies, and conflicts
  (e.g., HTTP vs. UCI control/cancellation). Update it whenever any plan’s dependencies or
  stage gates change.

## Error Models and Logging (Docs Expectations)
- Plans that expose APIs must specify structured error shapes and logging/monitoring hooks.
- Include request IDs and error codes in examples to ensure consistent implementation.

## Benchmarks & Baselines
- When performance is discussed (Plan 6/7), specify the benchmark protocol: positions,
  warm-up, iterations, measurement units, and reporting format. Check in baseline artifacts
  under `assets/benchmarks/` and reference them from the plan.

## ADRs (Architecture Decision Records)
- Use `docs/adr/` for decisions with long-term impact (e.g., bitboards vs. mailbox,
  FastAPI vs. alternative, hash table replacement policy).
- ADR template should cover: Context, Decision, Status, Consequences, Alternatives.
- Reference ADRs from plans and README where relevant.

## Review Checklist (for Doc Changes)
- Does the change update all impacted plans and the meta plan?
- Are exit criteria testable and time-bounded where applicable?
- Are dependencies and conflicts clearly documented?
- Are metrics concrete and reproducible with the current benchmark protocol?
- Do API-related plans include structured error models and logging expectations?

## Coordination with Implementation
- If code changes are part of a multi-step effort, use the planning tool to reflect progress
  (e.g., mark steps completed and the next step in progress).
- Do not merge code that violates a plan’s stage gate (e.g., search features before perft
  parity) without explicitly updating the plan and stating rationale.

## Examples
- Adding quiescence search earlier than planned: Update Plan 4 scope/deliverables/exit criteria,
  add a brief Changelog note, and update meta-plan dependencies if sequencing changes.
- Introducing a new endpoint: Update Plan 1 (API contract), add error schema details, and add
  corresponding tests in Plan 5; reflect changes in OpenAPI.

