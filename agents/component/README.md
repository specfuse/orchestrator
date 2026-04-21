# Component agent

The component agent is the worker instance that implements tasks inside a single component repository. One instance runs per component repo; its scope is hand-written code in that repo plus the cross-repo artifacts (events, overrides, escalations, spec issues) its tasks produce.

## What it does

- Picks up `ready` task issues in its assigned component repo.
- Writes hand-written code on a feature branch.
- Opens a pull request, gated by role-specific verification.
- Files spec issues when generated code is wrong (never edits generated files in place).
- Reconciles overrides against its repo after Specfuse regeneration runs.
- Escalates to the human on the four reasons enumerated in [`escalation-protocol.md`](../../shared/rules/escalation-protocol.md).

## What it does not do

- Planning, task creation, or dependency recomputation (PM agent).
- Test plan authoring or execution (QA agent).
- Merge closure (merge watcher, on branch-protection green).
- Any write to a second repository beyond the one it was instantiated for.

## Layout

- [`CLAUDE.md`](CLAUDE.md) — the agent's configuration: role definition, transitions owned, output artifacts, verification, PR and escalation disciplines, and anti-patterns.
- [`version.md`](version.md) — current config version and changelog.
- [`skills/`](skills/) — role-specific skills layered on top of the shared substrate in [`/shared/`](../../shared/).
- [`rules/`](rules/) — role-specific rule overrides. Empty at v1.0.0 by design.

## Where this role fits

See [`orchestrator-architecture.md`](../../docs/orchestrator-architecture.md) §5 for the full role taxonomy, and §6.2–§6.3 for task state and transition ownership. The architecture document is normative; this directory's files layer operational detail on top of it.
