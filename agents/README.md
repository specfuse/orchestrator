# Agents

Role configurations for the orchestrator's agents. Four **operational** agents drive per-feature work (specs, PM, component, QA); one **meta-role** (onboarding) operates project-wide to prepare a project for orchestrator coordination. Each role has its own directory with the layout fixed by architecture §5.2:

```
/agents/<role>/
    CLAUDE.md       — role prompt and entry point
    version.md      — current version and changelog
    skills/         — role-specific skills
    rules/          — role-specific rule overrides (empty at v1 by design)
```

Every `CLAUDE.md` opens by pulling in the full [`/shared/rules/`](../shared/rules/README.md) set, then layers its own role-specific behavior on top. The partitioning test is architecture §5.3: **if every role must behave identically under a rule, it belongs in `/shared/`; if two roles would diverge, it belongs under `/agents/<role>/rules/`.** At v1 no role overrides a shared rule; per-role `rules/` directories exist but are intentionally empty.

## Operational roles (per-feature)

| Role | Version | Frozen | Skills |
|---|---|---|---|
| [`specs/`](specs/CLAUDE.md) | 1.0.1 | Phase 4 (2026-04-26) | feature-intake, spec-drafting, spec-validation, spec-issue-triage |
| [`pm/`](pm/CLAUDE.md) | 1.6.3 | Phase 2 (2026-04-23) | task-decomposition, plan-review, issue-drafting, dependency-recomputation, template-coverage-check |
| [`component/`](component/CLAUDE.md) | 1.5.2 | Phase 1 (2026-04-22) | verification, pr-submission, escalation |
| [`qa/`](qa/CLAUDE.md) | 1.5.2 | Phase 3 (2026-04-24) | qa-authoring, qa-execution, qa-regression, qa-curation |

- [`specs/`](specs/CLAUDE.md) — partners with the human in an interactive session to draft specifications, run Specfuse validation, and usher a feature from `drafting` through `validating` into `planning`. Reads and writes `/product/`; writes the feature registry during its phase of the lifecycle. Session-driven (the human is the primary driver), unlike the three task-driven downstream agents.
- [`pm/`](pm/CLAUDE.md) — converts a validated spec into a task graph, co-authors work unit prompts with the human, creates GitHub issues in component repos, and owns dependency recomputation. Sole writer of task-level `pending → ready` transitions.
- [`component/`](component/CLAUDE.md) — one instance per component repo; picks up `ready` task issues, writes hand-written code, opens PRs, and reconciles overrides for its repo. Does not cross repo boundaries.
- [`qa/`](qa/CLAUDE.md) — authors test plans, executes them, curates the regression suite. Owns `qa_authoring`, `qa_execution`, `qa_curation`, and `qa_regression` task types; files regression issues against implementation tasks and spec issues when ambiguities surface.

## Meta-roles (project-wide)

| Role | Version | Frozen | Skills |
|---|---|---|---|
| [`onboarding/`](onboarding/CLAUDE.md) | 0.1.0 | no (Phase 4.5 draft) | repo-inventory, integration-plan, bootstrap-greenfield |

- [`onboarding/`](onboarding/CLAUDE.md) — prepares a project for orchestrator coordination at integration time. Inventories repos, drafts integration or bootstrap plans, identifies orchestrator-readiness gaps. Operates project-wide rather than per-feature; runs once at integration and rarely thereafter. Artifacts land in [`/project/`](../project/). v0.1 draft, intended to be exercised on a real project and hardened.

A second meta-role (config-steward) is named in architecture §5.1 and §5.4 and lands in **Phase 5** alongside the generator feedback loop. It will watch commits to `/agents/` and `/shared/` and steward version bumps. See [`docs/orchestrator-implementation-plan.md`](../docs/orchestrator-implementation-plan.md) §"Phase 5".

## Versioning and change process

Each role carries a semantic version in `version.md`. Any change to a role's `CLAUDE.md`, skills, or rules requires a version bump and a changelog line. The event log records which agent version handled each event, so behavior changes can be reconstructed after the fact.

The frozen baselines above are the contract Phase 5+ inherits: changes to a frozen surface require architectural justification. Each role's `version.md` cites the freezing work unit and retrospective.

The full change-management protocol — including how version bumps are proposed, reviewed, and applied alongside role-config changes — lives in the config-steward agent's future specification (Phase 5; see architecture §5.4). Until that agent exists, version bumps are made by hand by the committer: bump the version in `version.md`, add a changelog entry describing the change, and commit the bump alongside the underlying change in the same commit.

Role configs are produced and revised in coordination with `/shared/` — the shared substrate every role depends on. When a shared rule, schema, or template changes, re-read every role's `CLAUDE.md` to confirm nothing drifts; when a role config changes, confirm it still reads coherently against the current `/shared/`.
