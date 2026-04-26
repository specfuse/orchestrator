# Specfuse Orchestrator

Specfuse Orchestrator is a filesystem-based coordination layer for multi-agent software development workflows. It uses a directory structure of features, events, and an agent inbox — along with agent configurations, shared skills, rules, schemas, and templates — to let specs, PM, component, and QA agents collaborate on feature delivery without a central runtime. This repository holds the orchestrator scaffolding; downstream projects consume it via an overrides layer.

For background, goals, and design rationale, see [`docs/orchestrator-vision.md`](docs/orchestrator-vision.md). For the directory layout, protocols, and architectural decisions, see [`docs/orchestrator-architecture.md`](docs/orchestrator-architecture.md). A condensed overview is in [`docs/orchestrator-design-summary.md`](docs/orchestrator-design-summary.md). The phased build plan is in [`docs/orchestrator-implementation-plan.md`](docs/orchestrator-implementation-plan.md).

## Status

Phases 0–4 complete. The four operational agents are at frozen v1 baselines:

| Role | Version | Frozen at |
|---|---|---|
| [Specs](agents/specs/) | 1.0.1 | Phase 4 (WU 4.8) |
| [PM](agents/pm/) | 1.6.3 | Phase 2 (WU 2.15) |
| [Component](agents/component/) | 1.5.2 | Phase 1 (WU 1.12) |
| [QA](agents/qa/) | 1.5.2 | Phase 3 (WU 3.13) |

The idea → spec → plan → implement → QA → done pipeline is operational end-to-end. **Phase 5** (generator feedback loop, override-registry inversion, config-steward meta-agent) is the remaining build phase per the implementation plan.

## Getting started on a real project

- [`docs/operator-runbook.md`](docs/operator-runbook.md) — quickstart for driving a feature from idea through `planning` with the specs agent. Includes environment prerequisites.
- [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) — full-lifecycle operator reference covering PM, component, and QA sessions, inbox handling, spec-issue triage, and escalations.
