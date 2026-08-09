# Specfuse Orchestrator

Specfuse Orchestrator is a filesystem-based coordination layer for multi-agent software development workflows. It uses a directory structure of features, events, and an agent inbox — along with agent configurations, shared skills, rules, schemas, and templates — to let specs, PM, component, and QA agents collaborate on feature delivery without a central runtime. This repository is the source for the `specfuse-orchestrator` pip package; it ships as part of the `specfuse` suite and scaffolds a project's orchestration repo with `specfuse pm init`.

For background, goals, and design rationale, see [`docs/orchestrator-vision.md`](docs/orchestrator-vision.md). For the directory layout, protocols, and architectural decisions, see [`docs/orchestrator-architecture.md`](docs/orchestrator-architecture.md). A condensed overview is in [`docs/orchestrator-design-summary.md`](docs/orchestrator-design-summary.md). The phased build plan is in [`docs/orchestrator-implementation-plan.md`](docs/orchestrator-implementation-plan.md).

## Status

Phases 0–4 complete; Phase 4.5 (onboarding agent) added to support real-project adoption. The four operational agents are at frozen v1 baselines; the onboarding meta-role is at v0.1 draft.

| Role | Version | Frozen | Phase |
|---|---|---|---|
| [Specs](agents/specs/) | 1.0.1 | yes | Phase 4 |
| [PM](agents/pm/) | 1.6.5 | yes | Phase 2 |
| [Component](agents/component/) | 1.5.4 | yes | Phase 1 |
| [QA](agents/qa/) | 1.6.1 | yes | Phase 3 |
| [Onboarding](agents/onboarding/) | 0.1.1 | no (draft) | Phase 4.5 |

The idea → spec → plan → implement → QA → done pipeline is operational end-to-end. **Phase 5** (generator feedback loop, override-registry inversion, config-steward meta-agent) is the remaining build phase per the implementation plan.

## Getting started on a real project

**Five-minute path:** see [`GETTING_STARTED.md`](GETTING_STARTED.md). `uv tool install specfuse` (or `pipx install specfuse`) then `specfuse pm init my-product-orchestration` scaffolds a fresh, git-initialized orchestration repo (state directories, a starter `roadmap.md`, `.claude` plugin wiring, and a personalized next-steps doc). You then create and push the GitHub repo yourself (a manual `gh repo create` step — `init` does not do it). Then `/onboard` in a Claude Code session walks you through the rest.

The orchestration repo is the **process-state store for one product** (singleton per product), created in your own org as `<your-org>/<your-product>-orchestration`. It's your own new git repo. To pull in future improvements, `specfuse upgrade` then `specfuse pm upgrade <dir>` re-syncs the substrate from the newly-installed wheel and refreshes the `.claude` wiring.

The orchestrator engages **downstream of product discussion**. Brainstorming, business decisions, and feature ideation belong in your project's **product reference repo** (the `/product/` subtree); the orchestrator picks up at feature-intake when an idea crystallizes into a feature.

Two project shapes are supported, both via the same `init` flow:

- **Greenfield:** new project, no repos yet. The onboarding agent's `bootstrap-greenfield` skill produces a setup checklist covering environment prereqs, repo-creation order, per-repo conventions, and first-feature scoping.
- **Brownfield:** existing project with code, specs, and possibly in-flight features. The onboarding agent's `repo-inventory` skill walks each repo and produces readiness assessments; `integration-plan` then drafts a phased rollout (pilot → expand → import in-flight → steady state) that brings the project under orchestrator coordination without disrupting current delivery.

The exact sequence — including the literal commands — is in [`GETTING_STARTED.md`](GETTING_STARTED.md). The onboarding agent detects your project state and chooses the right skill for you.

### Day-to-day operation

Once a project is wired:

- [`docs/operator-runbook.md`](docs/operator-runbook.md) — quickstart for driving a feature from idea through `planning` with the specs agent. Includes environment prerequisites.
- [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) — full-lifecycle operator reference covering PM, component, and QA sessions, inbox handling, spec-issue triage, and escalations.

### Licensing

This repository — the `specfuse-orchestrator` package source — is licensed under [Apache 2.0](LICENSE). You can incorporate the scaffolding into your own work, including proprietary work, with attribution.

The **orchestration repo you create with `specfuse pm init`** is your own new git repo. It holds your project's coordination state (`/features/`, `/events/`, `/inbox/`, `/project/`), and you license it however you want. `init` no longer swaps in a proprietary LICENSE or generates any attribution machinery — the frozen substrate lives inside the installed wheel, not copied into your repo, so there's nothing to relicense.

### Slash commands (in a Claude Code session)

Install the plugin with `/plugin install specfuse-orchestrator@specfuse` (already in the `specfuse/specfuse` marketplace). It provides the five agents plus one slash command:

- `/onboard` — switch into the onboarding-agent role; runs `repo-inventory`, `integration-plan`, or `bootstrap-greenfield` depending on project state.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to contribute to this package.
