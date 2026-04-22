# PM agent

The PM agent turns a validated product specification into an executable task graph: it decomposes the feature into implementation and QA tasks, assigns each to the correct component repo, collaborates with the human on work unit prompts, opens GitHub issues, and recomputes task dependencies on every completion. One instance runs per active feature.

## What it does

- Reads a validated feature spec and drafts the task graph into the feature registry frontmatter.
- Materializes the task graph as a human-editable plan for the `plan_review` stage, and re-ingests the edits as the new source of truth.
- Opens `work-unit-issue.md`-compliant GitHub issues in the assigned component repos, re-verifying every factual claim about target-repo state at drafting time.
- Recomputes dependencies on every `task_completed` event and flips newly-unblocked tasks from `pending` to `ready`.
- Checks Specfuse template coverage at planning time via a stub protocol; escalates gaps rather than discovering them mid-implementation.
- Closes the feature when its last task reaches `done`.

## What it does not do

- Specification authoring or validation (specs agent).
- Code or test writing (component and QA agents).
- Approval of a plan (human owns `plan_review → generating`).
- Merge closure (merge watcher, gated on branch protection).
- Writing to `/product/`, `/overrides/`, or any component-repo code path.

## Layout

- [`CLAUDE.md`](CLAUDE.md) — the agent's configuration: role definition, transitions owned, output artifacts, verification, escalation, and anti-patterns.
- [`version.md`](version.md) — current config version and changelog.
- [`issue-drafting-spec.md`](issue-drafting-spec.md) — inherited forward specification the issue-drafting skill must honor on day one (authored in WU 1.9).
- [`skills/`](skills/) — role-specific skills layered on top of the shared substrate in [`/shared/`](../../shared/). Populated by Phase 2 WUs 2.2–2.6.
- [`rules/`](rules/) — role-specific rule overrides. Empty at v1.0.0 by design.

## Where this role fits

See [`orchestrator-architecture.md`](../../docs/orchestrator-architecture.md) §5 for the full role taxonomy and §6.2–§6.3 for task state and transition ownership. The PM agent is the **sole writer of `pending → ready` task transitions** and the **sole owner of dependency recomputation** — centralizing both is what keeps the dependency graph auditable and race-free. The architecture document is normative; this directory's files layer operational detail on top of it.
