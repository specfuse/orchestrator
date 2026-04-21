# Agents

Role configurations for the four operational agents that drive the orchestrator. Each role has its own directory with the layout fixed by architecture §5.2:

```
/agents/<role>/
    CLAUDE.md       — role prompt and entry point
    version.md      — current version and changelog
    skills/         — role-specific skills (v0.1: empty)
    rules/          — role-specific rules (v0.1: empty)
```

Every `CLAUDE.md` opens by pulling in the full [`/shared/rules/`](../shared/rules/README.md) set, then layers its own role-specific behavior on top. The partitioning test is architecture §5.3: **if every role must behave identically under a rule, it belongs in `/shared/`; if two roles would diverge, it belongs under `/agents/<role>/rules/`.** In the v0.1 draft no role overrides a shared rule; per-role `rules/` directories exist but are empty.

## Roles

- [`specs/`](specs/CLAUDE.md) — helps the human draft specifications, runs Specfuse validation, ushers a feature from `drafting` through `validating` into `planning`. Reads and writes `/product/`; writes the feature registry during its phase of the lifecycle.
- [`pm/`](pm/CLAUDE.md) — converts a validated spec into a task graph, co-authors work unit prompts with the human, creates GitHub issues in component repos, and owns dependency recomputation. Sole writer of task-level `pending → ready` transitions.
- [`component/`](component/CLAUDE.md) — one instance per component repo; picks up `ready` task issues, writes hand-written code, opens PRs, and reconciles overrides for its repo. Does not cross repo boundaries.
- [`qa/`](qa/CLAUDE.md) — authors test plans, executes them, curates the regression suite. Owns `qa_authoring`, `qa_execution`, and `qa_curation` task types; files regression issues against implementation tasks and spec issues when ambiguities surface.

A fifth meta-agent (config-steward) is named in architecture §5.1 and §5.4. It is **not** created in this Phase 0 draft — the operational roles must stabilize before a meta-role that watches them makes sense. See the implementation plan's later phases.

## Versioning and change process

Each role carries a semantic version in `version.md`. Any change to a role's `CLAUDE.md`, skills, or rules requires a version bump and a changelog line. The event log records which agent version handled each event, so behavior changes can be reconstructed after the fact.

The full change-management protocol — including how version bumps are proposed, reviewed, and applied alongside role-config changes — lives in the config-steward agent's future specification (deferred; see architecture §5.4). Until that agent exists, version bumps are made by hand by the committer: bump the version in `version.md`, add a changelog entry describing the change, and commit the bump alongside the underlying change in the same commit.

Role configs are produced and revised in coordination with `/shared/` — the shared substrate every role depends on. When a shared rule, schema, or template changes, re-read every role's `CLAUDE.md` to confirm nothing drifts; when a role config changes, confirm it still reads coherently against the current `/shared/`.
