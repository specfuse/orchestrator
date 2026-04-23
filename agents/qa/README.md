# QA agent

The QA agent authors test plans from validated acceptance criteria, executes them against the implementation once it lands, files structured regression artifacts when execution fails, and curates the growing regression suite. Its cadence is longitudinal — a single feature traverses qa-authoring → qa-execution → (possibly regression → re-execution) → curation over multiple cycles. One agent instance runs per active QA task; its scope spans the product specs repo (test plans), the component repo(s) under test (indirectly, through regression artifacts), and the orchestration repo (events, inbox, escalations).

## What it does

- Reads a validated feature's acceptance criteria and authors a test plan into `/product/test-plans/FEAT-YYYY-NNNN.md` in the product specs repo.
- Executes the plan idempotently against the component repo(s) under test and emits structured `qa_execution_completed` or `qa_execution_failed` events keyed on `(task_correlation_id, commit_sha)`.
- On a qa-execution failure, files a regression artifact via `/inbox/qa-regression/` that spawns a new implementation task — without writing labels or state to the task under test.
- On a qa-execution repeat failure, escalates `spinning_detected` on the original implementation task via an event, again without any label write.
- Curates the regression suite within a bounded scan budget: dedups overlaps, retires spec-removed orphans, consolidates failure-clustered tests. All curation changes land through a reviewable PR.

## What it does not do

- Hand-written code or test harness implementation (component agent).
- Specification authoring outside `/product/test-plans/` (specs agent).
- Task creation, dependency recomputation, or feature-level state transitions (PM agent).
- Merge closure (merge watcher, on branch-protection green).
- Any label or state write on a task the QA agent does not own — including the implementation task under test, even when qa-execution reveals a regression.

## Layout

- [`CLAUDE.md`](CLAUDE.md) — the agent's configuration: role definition, transitions owned, output artifacts, the cross-task regression invariant, verification, escalation, and anti-patterns.
- [`version.md`](version.md) — current config version and changelog.
- [`skills/`](skills/) — role-specific skills layered on top of the shared substrate in [`/shared/`](../../shared/). Populated by Phase 3 WUs 3.2–3.5.
- [`rules/`](rules/) — role-specific rule overrides. Empty at v1.0.0 by design.

## Where this role fits

See [`orchestrator-architecture.md`](../../docs/orchestrator-architecture.md) §5 for the full role taxonomy, §6.2–§6.3 for task state and transition ownership, §6.4 for the spinning-detection / regression-vs-escalation rule the QA agent applies on qa-execution failures, and §4.3 for the canonical test plan location. The architecture document is normative; this directory's files layer operational detail on top of it.
