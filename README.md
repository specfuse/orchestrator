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

**Five-minute path:** see [`GETTING_STARTED.md`](GETTING_STARTED.md). One `git clone` + `./scripts/setup.sh` does the entire one-time setup (strip, git re-init, private GitHub repo creation, upstream remote configuration, personalized next-steps doc). Then `/onboard` in a Claude Code session walks you through the rest.

The orchestration repo is the **process-state store for one product** (singleton per product). Template-cloned to your own org as `<your-org>/<your-product>-orchestration`. Full workflow — including how to **pull upstream improvements** into your downstream over time and how to **contribute fixes back upstream** — is documented in [`docs/upstream-downstream-sync.md`](docs/upstream-downstream-sync.md).

The orchestrator engages **downstream of product discussion**. Brainstorming, business decisions, and feature ideation belong in your project's **product reference repo** (the `/product/` subtree); the orchestrator picks up at feature-intake when an idea crystallizes into a feature.

Two project shapes are supported, both via the same setup script:

- **Greenfield:** new project, no repos yet. The onboarding agent's `bootstrap-greenfield` skill produces a setup checklist covering environment prereqs, repo-creation order, per-repo conventions, and first-feature scoping.
- **Brownfield:** existing project with code, specs, and possibly in-flight features. The onboarding agent's `repo-inventory` skill walks each repo and produces readiness assessments; `integration-plan` then drafts a phased rollout (pilot → expand → import in-flight → steady state) that brings the project under orchestrator coordination without disrupting current delivery.

The exact sequence — including the literal commands — is in [`GETTING_STARTED.md`](GETTING_STARTED.md). The `setup.sh` script asks for your project type and chooses the right onboarding skill for you.

### Day-to-day operation

Once a project is wired:

- [`docs/operator-runbook.md`](docs/operator-runbook.md) — quickstart for driving a feature from idea through `planning` with the specs agent. Includes environment prerequisites.
- [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) — full-lifecycle operator reference covering PM, component, and QA sessions, inbox handling, spec-issue triage, and escalations.

### Slash commands (in a Claude Code session)

Project-scoped slash commands wrap the most common operations and become available via `/` autocomplete when you open a Claude Code session at the orchestration repo:

- `/onboard` — switch into the onboarding-agent role; runs `repo-inventory`, `integration-plan`, or `bootstrap-greenfield` depending on project state.
- `/sync-upstream` — periodic upstream sync; reviews and cherry-picks upstream commits since the `UPSTREAM` anchor.
- `/contribute-upstream` — extract scaffolding-only patches from downstream commits for an upstream PR.

The commands wrap the equivalent shell scripts under [`scripts/`](scripts/) and are documented in [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/upstream-downstream-sync.md`](docs/upstream-downstream-sync.md).
