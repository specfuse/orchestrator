# Specfuse Orchestrator

Specfuse Orchestrator is a filesystem-based coordination layer for multi-agent software development workflows. It uses a directory structure of features, events, and an agent inbox — along with agent configurations, shared skills, rules, schemas, and templates — to let specs, PM, component, and QA agents collaborate on feature delivery without a central runtime. This repository holds the orchestrator scaffolding; downstream projects consume it via a template clone.

For background, goals, and design rationale, see [`docs/orchestrator-vision.md`](docs/orchestrator-vision.md). For the directory layout, protocols, and architectural decisions, see [`docs/orchestrator-architecture.md`](docs/orchestrator-architecture.md). A condensed overview is in [`docs/orchestrator-design-summary.md`](docs/orchestrator-design-summary.md). The phased build plan is in [`docs/orchestrator-implementation-plan.md`](docs/orchestrator-implementation-plan.md).

## Status

Phases 0–4 complete; Phase 4.5 (onboarding agent) added to support real-project adoption. The four operational agents are at frozen v1 baselines; the onboarding meta-role is at v0.1 draft.

| Role | Version | Frozen | Phase |
|---|---|---|---|
| [Specs](agents/specs/) | 1.0.1 | yes | Phase 4 |
| [PM](agents/pm/) | 1.6.3 | yes | Phase 2 |
| [Component](agents/component/) | 1.5.2 | yes | Phase 1 |
| [QA](agents/qa/) | 1.5.2 | yes | Phase 3 |
| [Onboarding](agents/onboarding/) | 0.1.0 | no (draft) | Phase 4.5 |

The idea → spec → plan → implement → QA → done pipeline is operational end-to-end. **Phase 5** (generator feedback loop, override-registry inversion, config-steward meta-agent) is the remaining build phase per the implementation plan.

## Getting started on a real project

The orchestration repo is the **process-state store for one product** (singleton per product). Template-clone this scaffolding to your own org as `<your-org>/<your-product>-orchestration`, strip upstream walkthrough artifacts, and start fresh — keep `/agents/`, `/shared/`, `/scripts/`, and `/docs/` (the operator runbook and pipeline reference).

The orchestrator engages **downstream of product discussion**. Brainstorming, business decisions, and feature ideation belong in your project's **product reference repo** (the `/product/` subtree); the orchestrator picks up at feature-intake when an idea crystallizes into a feature.

Two paths from here:

### Greenfield: new project, no existing code

You have a product idea but no repos yet.

1. Open a Claude Code session at the orchestration repo with [`agents/onboarding/CLAUDE.md`](agents/onboarding/CLAUDE.md) as the role prompt.
2. Run the [`bootstrap-greenfield`](agents/onboarding/skills/bootstrap-greenfield/SKILL.md) skill — produces `project/bootstrap-checklist.md` (environment prereqs, repo-creation order, initial conventions, first-feature scoping).
3. Execute the checklist: create the product reference repo, create component repos in dependency order, set up `.specfuse/templates.yaml` and root `CLAUDE.md` per repo.
4. As each component repo is created, run the onboarding agent's [`repo-inventory`](agents/onboarding/skills/repo-inventory/SKILL.md) skill against it.
5. Pick a small first feature and run it end-to-end via [`docs/operator-runbook.md`](docs/operator-runbook.md).

### Brownfield: existing project with code, specs, possibly in-flight features

You have repos and ongoing work; you want to bring it under orchestrator coordination without disrupting current delivery.

1. Open a Claude Code session at the orchestration repo with [`agents/onboarding/CLAUDE.md`](agents/onboarding/CLAUDE.md) as the role prompt.
2. Run the [`repo-inventory`](agents/onboarding/skills/repo-inventory/SKILL.md) skill — walks each involved repo and produces `project/repos/<repo-slug>.md` with purpose, tech surface, current state, and orchestrator-readiness gaps. Builds `project/manifest.md`.
3. Run the [`integration-plan`](agents/onboarding/skills/integration-plan/SKILL.md) skill — produces `project/integration-plan.md` with a phased rollout (pilot one feature on one repo first; expand component coverage; selectively import in-flight features at natural breakpoints; reach steady state).
4. Execute the integration plan. The pilot feature runs end-to-end via [`docs/operator-runbook.md`](docs/operator-runbook.md); subsequent features expand following the plan.

### Day-to-day operation (both paths converge here)

Once a project is wired:

- [`docs/operator-runbook.md`](docs/operator-runbook.md) — quickstart for driving a feature from idea through `planning` with the specs agent. Includes environment prerequisites.
- [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) — full-lifecycle operator reference covering PM, component, and QA sessions, inbox handling, spec-issue triage, and escalations.
