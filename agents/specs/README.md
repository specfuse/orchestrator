# Specs agent

The specs agent partners with the human in an interactive Claude Code session to turn a feature idea into validated product specifications. It creates feature registry entries, drafts OpenAPI / AsyncAPI / Arazzo specifications under `/product/` in the product specs repo, runs Specfuse validation, and triages spec issues routed from downstream agents. Its cadence is session-driven — the human opens a Claude Code session and collaborates with the agent, unlike the three task-driven downstream agents (PM, component, QA) that pick up structured work from issues or event triggers.

## What it does

- Creates feature registry entries in the orchestration repo, minting correlation IDs and emitting `feature_created` events.
- Drafts and iterates on product specifications collaboratively with the human inside `/product/` in the specs repo.
- Invokes Specfuse validation and presents actionable feedback on failures.
- Owns the `drafting → validating → planning` segment of the feature state machine; hands off to the PM agent at `planning`.
- Triages spec issues routed from downstream agents via `/inbox/spec-issue/`, resolving them in `/product/` or re-routing to the generator project.

## What it does not do

- Task decomposition, dependency recomputation, or issue creation (PM agent).
- Code or test writing (component and QA agents).
- Merge gating or closure (merge watcher, on branch-protection green).
- Any write to `/business/`, `/product/test-plans/`, `/overrides/`, or component-repo code paths.

## Layout

- [`CLAUDE.md`](CLAUDE.md) — the agent's configuration: role definition, interaction model, transitions owned, output surfaces, verification, escalation, and anti-patterns.
- [`version.md`](version.md) — current config version and changelog.
- [`skills/`](skills/) — role-specific skills layered on top of the shared substrate in [`/shared/`](../../shared/). Populated by Phase 4 WUs 4.2–4.5 (feature-intake, spec-drafting, spec-validation, spec-issue-triage).
- [`rules/`](rules/) — role-specific rule overrides. Empty at v1.0.0 by design.

## Where this role fits

See [`orchestrator-architecture.md`](../../docs/orchestrator-architecture.md) §5 for the full role taxonomy, §6.1 for the feature state machine (`drafting → validating → planning` transitions), and §6.3 for transition ownership. The architecture document is normative; this directory's files layer operational detail on top of it.
