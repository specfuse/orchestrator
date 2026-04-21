# Specfuse Orchestrator — Vision

## Why this exists

AI coding agents are good at narrow, well-scoped work. They struggle when the work spans multiple repositories, multiple specifications, multiple review cycles, and multiple weeks of wall-clock time. The glue between agents — knowing who does what, who hands off to whom, when a human should step in, and how to keep everything traceable — is currently done ad hoc, in chat windows, by the person running the agents.

The Specfuse Orchestrator replaces that ad hoc glue with a structured workflow. It coordinates specialized agents across the repositories that make up a real product. It puts humans in the loop at the moments that matter — drafting specifications, reviewing plans, approving merges, resolving escalations — and keeps them out of the loop the rest of the time.

It is deliberately small. It is not a platform. It is a set of conventions, prompts, and lightweight automation that turns multi-agent coding from an experiment into something you can rely on.

## What it does

The orchestrator takes a feature from its specification all the way to merged code across the repositories that implement it. Along the way:

- A **specs agent** helps draft and validate the feature's specifications.
- A **planning agent** breaks the feature into tasks, arranges their dependencies, and produces a plan the human can edit before anything is built.
- **Component agents** pick up tasks in the individual repositories they own and produce pull requests.
- A **QA agent** authors test plans, executes them, and curates regression suites.

Every unit of work — feature, task, event — carries a single correlation ID that threads its lifecycle across repositories and agents. Every action is recorded in an append-only event log. Every generated artifact lives in a clearly marked, never-touched-by-humans directory, and anything an agent needs to override is tracked with a known expiry.

The coordination substrate is git. Features live as markdown files. Events live as JSONL. Tasks live as GitHub issues. The orchestrator's internals are boring on purpose: plain text, versioned, diffable, reviewable.

Humans keep the judgment calls. Agents handle the mechanical work between them.

## Where it fits

Specfuse is an organization and a methodology. Under its umbrella live several companion projects, each independently adoptable:

- **specfuse/codegen** produces deterministic source code from OpenAPI, AsyncAPI, and Arazzo specifications. It handles the boilerplate no one should be writing by hand and no agent should be hallucinating.
- **specfuse/orchestrator** — this project — coordinates the agents and humans who handle the work that *isn't* boilerplate: the business logic, the tests, the reviews, the decisions.

The two fit together. Codegen gives agents a stable, regenerable foundation so they can focus on what only humans-and-agents can do. The orchestrator gives that work structure so it doesn't collapse into chaos when the number of agents and repositories grows.

You can use either project without the other. They share vocabulary where it helps, and stay out of each other's way otherwise.

## Who it's for

The orchestrator is for small teams — including teams of one — building products across multiple repositories who:

- Write specifications before they write code, and treat those specifications as source of truth.
- Use AI coding agents as serious collaborators, not novelties.
- Want repeatable, auditable workflows rather than one-off chat sessions.
- Are comfortable with a local-first, git-native, script-light approach.

It is designed for the scale a small team actually operates at: a couple of features a week, a handful of repositories, a single operator kicking off a polling loop on their laptop. If you need horizontal scaling and a hosted control plane, you will need more than this project provides — and that's fine. We'd rather ship something useful for the common case than something architecturally impressive for nobody in particular.

## What it isn't

The orchestrator is **not a general-purpose AI coding platform.** It does one shape of work: spec-driven, multi-repo, multi-agent feature delivery. It does not try to be anything else.

The orchestrator is **not a replacement for human engineering judgment.** Every high-consequence decision — what to build, what the plan should look like, whether a PR should merge, what to do when something goes wrong — passes through a human. The agents are capable, but the orchestrator exists to keep them *inside* a loop, not to remove the loop.

The orchestrator is **not a replacement for deterministic codegen.** Boilerplate produced by specfuse/codegen is not rewritten by agents. Generated directories are off-limits. When generated code is wrong, the fix is a generator change, not an agent working around it.

The orchestrator is **not a hosted service, a SaaS product, or a dashboard.** It runs on your machine, against your repositories, under your accounts. There is no control plane to lose access to.

## Principles

A few commitments shape everything else:

**Open from the first commit.** This project is written to be read by people who don't work where you work. Prompts, rules, and configuration files are part of the public product. Nothing that leaks a specific consumer, product, or business context belongs in the shared layer.

**Boring beats clever.** Git, markdown, JSONL, GitHub issues, a polling loop. Every piece is replaceable individually. Nothing is load-bearing that shouldn't be.

**Humility about the hard parts.** The coordination layer — who picks up what, when, and how failure is handled — is the most likely source of early debugging pain. The design assumes this and keeps that layer small and iterative rather than prematurely elaborate.

**Traceability by default.** Every action carries a correlation ID. Every agent configuration change is versioned. Every event is logged. If something goes wrong six weeks from now, you should be able to reconstruct what happened and who — human, agent, or script — did it.

**Humans at the edges, agents in the middle.** Not the reverse.
