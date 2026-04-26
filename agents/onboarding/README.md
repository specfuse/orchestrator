# Onboarding agent

The onboarding agent is a **meta-role** that prepares a project for orchestrator coordination. Unlike the four operational agents (specs, PM, component, QA) which operate per-feature, the onboarding agent operates **project-wide** — it runs once when a team adopts the orchestrator and occasionally afterward when the project's repo set changes.

## What it does

- **Inventories the project's repositories** — purpose, language/framework, build/test commands, current spec coverage, in-flight work, orchestrator-readiness.
- **Drafts an integration plan** for brownfield projects — phased transition, which features go through the orchestrator first, how in-flight work is imported, per-repo onboarding checklist, risk register.
- **Drafts a setup checklist** for greenfield projects — environment prerequisites, repo creation, initial conventions.

## What it does not do

- Per-feature work of any kind (specs, PM, component, QA agents handle that).
- Run the integration itself — the agent produces a plan; the human executes it.
- Replace product brainstorming or design — those happen in the project's product reference repo, upstream of the orchestrator (architecture §4.1).

## Layout

- [`CLAUDE.md`](CLAUDE.md) — role configuration.
- [`version.md`](version.md) — current version (v0.1.0 draft) and changelog.
- [`skills/`](skills/) — three v0.1 skills: [`repo-inventory`](skills/repo-inventory/SKILL.md), [`integration-plan`](skills/integration-plan/SKILL.md), [`bootstrap-greenfield`](skills/bootstrap-greenfield/SKILL.md).
- [`rules/`](rules/) — empty at v0.1 by design.

## Where this role fits

This is a Phase 4.5 interlude added to support real-project adoption. Companion meta-role (config-steward, Phase 5) is also project-level rather than per-feature; together they form the orchestrator's meta-role surface. See the implementation plan's "Phase 4.5" section for the rationale.

Artifacts produced by this agent land in [`/project/`](../../project/) in the orchestration repo. That subtree is the durable output of onboarding work — read it cold to understand what the project looks like and how integration is going.
