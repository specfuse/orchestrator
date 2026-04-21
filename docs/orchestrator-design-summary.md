# Specfuse Orchestrator — Design Summary

## Purpose of this document

This is a consolidated record of design decisions for the Specfuse Orchestrator, produced as grounding material for three downstream documents: a vision document, an architecture document, and an implementation plan. Each of those documents should be drafted in its own session using this summary as context.

This document is written to be generic to the orchestrator itself. References to specific consumer products are deliberately excluded so the content can be reused as-is when the project moves to the public Specfuse organization.

---

## Project positioning

Specfuse is an organization and methodology, not a single tool. Under the Specfuse umbrella live multiple companion projects, each with plain functional names:

- **specfuse/codegen** (informal: "the generator") — the existing deterministic code generator that consumes OpenAPI, AsyncAPI, and Arazzo specifications with vendor extensions, and emits extensible source code via Mustache templates into dedicated generated-code directories.
- **specfuse/orchestrator** (informal: "the orchestrator") — the subject of this document. An agent-driven workflow system that coordinates multiple Claude Code instances across multiple repositories to take a feature from spec through merged implementation.

Additional components may be added to the Specfuse suite as the methodology matures. Each project is independently adoptable; using the generator does not require adopting the orchestrator, and vice versa.

The orchestrator is initially developed in a private repository under a consumer organization while it stabilizes. Migration to `github.com/specfuse/orchestrator` as an open-source project is planned once the design is proven.

---

## Vision summary

The orchestrator automates collaboration between specialized AI agents that together implement features from specification to merged code. Humans remain in the loop at well-defined points: drafting specs, reviewing plans, approving PRs, and resolving escalations. Between those points, agents execute deterministic and generative work with appropriate guardrails.

The system is designed to run locally using a Claude Code Max subscription. An eventual migration to Anthropic API-based execution is possible but deferred until the design is proven.

The initial target throughput is 2–3 features per week. The design must support that load without rework, but should not over-engineer for scale that hasn't arrived.

## Non-goals

The orchestrator is not a general-purpose AI coding platform, not a replacement for human engineering judgment, and not a substitute for the Specfuse generator. It specifically does not attempt to replace deterministic codegen with agent-produced boilerplate.

---

## Core concepts and vocabulary

### Features and tasks

**Features** are spec-driven units of product value. They live above the repository layer; their canonical state is tracked in the orchestration repo.

**Tasks** are implementation work units inside a single component repository. They are represented as GitHub issues in the component repo, and their canonical state is the GitHub issue state (augmented by labels and metadata).

Tasks have types:
- `implementation` — code written by a component agent
- `qa_authoring` — test plan authoring by the QA agent
- `qa_execution` — test plan execution by the QA agent
- `qa_curation` — regression suite curation by the QA agent

All task types share the same state machine; type affects which agent handles it and what the work unit prompt looks like.

### Correlation IDs

Every feature receives a correlation ID of the form `FEAT-YYYY-NNNN` (e.g., `FEAT-2026-0042`). Every task within a feature receives a sub-ID of the form `FEAT-YYYY-NNNN/TNN` (e.g., `FEAT-2026-0042/T07`).

Correlation IDs appear in:
- Feature registry markdown file names
- Every event log entry
- GitHub issue titles
- Branch names
- Commit message trailers (`Feature: FEAT-YYYY-NNNN/TNN`)
- PR descriptions

One correlation ID threads the entire lifecycle of a unit of work across all repositories and agents.

### Autonomy levels

Three levels, set as a default during the specs phase and overridable per-task during plan review:

- `auto` — agent executes end to end, opens PR, merges on green CI (once enabled; see PR merging)
- `review` — agent executes, opens PR, human approves merge
- `supervised` — agent proposes plan in the issue as a comment; human says go before any code is written

Autonomy is a per-task property; a feature's tasks may have mixed levels.

---

## State machines

### Feature state machine

States (owned at the specs repo / feature registry level):

- `drafting` — human (with chat agents) writing specs
- `validating` — Specfuse validation running
- `planning` — PM agent building the task graph
- `plan_review` — human reviewing/editing the plan
- `generating` — Specfuse producing boilerplate across component repos
- `in_progress` — at least one task is active
- `blocked` — feature-level issue requires human attention (e.g., mid-implementation spec inconsistency)
- `done` — all tasks complete
- `abandoned` — explicitly killed

### Task state machine

States (owned at the GitHub issue level in component repos):

- `pending` — exists but dependencies unmet
- `ready` — dependencies met, boilerplate confirmed, work unit prompt attached, awaiting agent pickup
- `in_progress` — component agent actively working
- `in_review` — PR open, awaiting review
- `blocked_spec` — agent raised a spec-level issue; escalated to specs/generator
- `blocked_human` — spinning detected or autonomy flag requires human intervention
- `done` — merged
- `abandoned`

### Transition ownership

- **Specs agent**: `drafting → validating → planning`
- **PM agent**: `planning → plan_review` and `generating → in_progress`; also owns dependency recomputation — when any task hits `done`, the PM agent re-evaluates which `pending` tasks flip to `ready`
- **Human**: `plan_review → generating` (approval gate); all `blocked_* → *` unblock transitions
- **Component agent**: `ready → in_progress → in_review`
- **Merge watcher** (GitHub Action, not an agent): `in_review → done`

Dependency recomputation must be centralized in the PM agent. Component agents emit a structured `task_completed` event; they do not decide what to unblock.

### Spinning detection

A task auto-transitions to `blocked_human` when any of the following triggers:

- Three consecutive failed verification cycles
- Wall-clock time exceeded (threshold TBD; start conservative)
- Token budget exceeded (threshold TBD; tied to Max subscription rate-limit protection)

QA-execution failures use the same spinning rule, scoped per implementation task they exercise. A first failure opens a structured regression issue against the implementation task and flips it back to a regression state; a repeated failure escalates to human.

---

## Infrastructure and repository layout

### Repositories involved

Three categories of repo participate:

1. **The orchestration repo** — owned by the orchestrator itself. Contains feature registry, event log, inbox, agent configurations, overrides registry, orchestration scripts. This is process, not product.

2. **The product specs repo** — owned by the product team. Contains specifications (OpenAPI, AsyncAPI, Arazzo), the Specfuse project file, test plans, product documentation, brand assets, and business collateral.

3. **Component repositories** — one per component of the product being built (e.g., API, persistence, workers, frontend, mobile). These contain both generated code (under `_generated` or `gen-src` directories) and hand-written business logic. GitHub issues in these repos represent tasks.

### Product specs repo internal split

The product specs repo is split at the top level:

- `/product/` — specs, test plans, feature descriptions. Agent-accessible. All AI agents read only from here.
- `/business/` — brand guidelines, marketing collateral, sales assets, support documentation. Humans only; agents are configured to ignore this directory.

This prevents unrelated changes by non-technical teams from confusing agents.

### Orchestration repo contents

- `/features/` — one markdown file per feature with frontmatter (current state, correlation ID, involved repos, autonomy default, approved task graph). Source of truth for feature state.
- `/events/` — append-only JSONL event log, one file per feature named by correlation ID.
- `/inbox/` — structured event files dropped by agents (spec issues, task completions, escalations). Consumed by the polling loop.
- `/agents/<role>/` — per-agent configuration directories (see "Agent configuration layout").
- `/shared/` — cross-agent rules, schemas, protocols, and templates.
- `/overrides/` — registry of temporary overrides on generated code, each with an expiring condition tied to an open issue.
- `/scripts/` — polling loop, orchestration tooling.

### Test plans

Test plans live in the product specs repo under `/product/test-plans/`. The QA agent writes them during `qa_authoring`. Execution results do not live there — they are written to the orchestration event log. **Plan is product; execution history is process.**

---

## Coordination substrate

### Git as substrate

Git provides the audit log, diff tooling, and multi-agent-safe write semantics for free. The orchestration repo uses plain markdown files and JSONL event logs, versioned in git, as the primary coordination medium. No database is required at the initial target scale.

### Event-driven interface, polling-based execution

All agent invocations are defined through a single stateless interface conceptually shaped as `handle_event(event_type, correlation_id, payload)`. The initial implementation is a polling loop that the user starts/stops manually on their local machine; the loop reads the inbox and invokes the appropriate handler.

No business logic lives in the poller itself. Swapping in webhooks or GitHub Actions later is a configuration change, not a rewrite.

### Event log schema

Every significant action is appended to the event log as a JSONL entry. Required fields:

- `timestamp` (ISO 8601)
- `correlation_id`
- `event_type`
- `source` (agent role or `human`)
- `source_version` (agent config version)
- `payload` (event-specific)

Event types include at minimum: `feature_created`, `spec_validated`, `plan_generated`, `plan_approved`, `task_created`, `task_ready`, `task_started`, `task_completed`, `task_blocked`, `spec_issue_raised`, `override_applied`, `override_expired`, `human_escalation`.

### Inbox flow

When an agent needs to trigger action in a part of the system it cannot directly modify (e.g., a component agent needs to raise a spec issue that belongs to the specs agent), it writes a structured file to the appropriate `/inbox/<type>/` subdirectory. The polling loop reads the inbox, dispatches to the correct handler, and archives processed files.

The inbox/event flow is intentionally underspecified in detail at this stage. The principle is to keep the interface simple (file in, file out) and iterate based on real friction during Phase 0. Concurrency, idempotency, and failure handling will be refined as real issues surface — **this layer is the most likely source of early debugging time and should be treated with appropriate humility.**

---

## Plan review UX

The PM agent produces the task graph as a diffable, editable markdown file with embedded structured content (mermaid for the graph, YAML frontmatter for metadata). The human's review is not a binary approve/reject — it's a standard file edit. Dependencies, prompts, and autonomy overrides can all be tweaked before the plan is approved.

After editing, the human signals approval (via a committed change to the feature's state in the registry). The PM agent re-ingests the edited plan as the source of truth and proceeds.

---

## Work unit prompts

A work unit prompt is the content placed inside a GitHub issue's body that a component agent will consume to execute a task. Prompts are drafted by the PM agent collaboratively with the human during the planning phase — the interaction follows the same pattern as a human working with Claude in a planning session, arriving at prompts the human endorses.

Every work unit prompt, regardless of how it was generated, must include:

- Context preamble (what this task is part of, correlation ID, related specs)
- Explicit acceptance criteria
- Explicit "do not touch" boundaries (generated code paths, files owned by other tasks)
- Explicit verification commands the agent must run before declaring done
- Explicit escalation triggers (conditions under which the agent stops and raises a structured issue)

The issue body template for work units is defined in `/shared/templates/` and enforced at issue creation time.

---

## PR merge rules

Merge gates are enforced via GitHub branch protection, not agent discipline:

- All tests passing
- Code coverage ≥ 90%
- Zero compiler warnings
- OWASP security scan clean
- Linting clean
- Required reviewers satisfied

Initial operating state: all merges are human-performed regardless of task autonomy level. The `auto` autonomy level does not trigger auto-merge in early phases.

Future state: the PM agent applies an `auto-merge-enabled` label based on task autonomy, and a GitHub Action performs the merge once all required checks pass. This is deferred until the QA loop is trusted.

---

## Generated code safety

Generated code lives in dedicated directories (`_generated`, `gen-src`, or equivalent) that are:

- Never modified by agents other than the Specfuse generator
- Clearly separated from hand-written business logic
- Safe to regenerate without side effects on manual code

When a component agent finds a problem in generated code, it raises a structured issue (never modifies the generated file). A human may authorize a temporary override to unblock progress.

### Override registry

Every override is tracked in `/overrides/` as a structured record with:

- File(s) overridden
- Task that required the override
- Issue that must be closed for the override to expire
- Expiry condition (e.g., "on closure of issue #42")
- Timestamp

The registry is readable by the Specfuse generator so regeneration respects active overrides. Expired overrides are removed; files return to fully generated state on next regeneration.

---

## Agent configuration layout

### Directory structure

```
/agents/
  /specs/
    CLAUDE.md
    skills/
    rules/
    version.md
  /pm/
    CLAUDE.md
    skills/
    rules/
    version.md
  /component/
    CLAUDE.md
    skills/
    rules/
    version.md
  /qa/
    CLAUDE.md
    skills/
    rules/
    version.md
/shared/
  skills/
  rules/
  schemas/
  templates/
```

Each agent's `CLAUDE.md` begins by pulling in shared definitions, then layers role-specific behavior on top.

### Shared vs role-specific

**Shared:**
- Correlation ID scheme
- Event log format and schema
- Feature/task state vocabulary and transitions
- Issue body templates (work unit, spec issue, QA regression, human escalation)
- "Never touch" list (generated directories, branch protection, secrets, `/business/`)
- Override registry protocol
- Escalation-to-human protocol
- Verify-before-report discipline (every agent states intent, acts, verifies, reports structured output)
- Security boundaries

**Role-specific:**
- Core reasoning prompts for the role
- Tools/MCP servers available to the role
- Role-specific verification steps
- Role-specific output formats

The test: if two agents would behave differently on the same rule, it's role-specific; if they must behave identically, it's shared.

### Versioning

Every agent configuration carries a version. Every change to a `CLAUDE.md`, skill, or rule file requires a version bump and a changelog line. The event log records which agent version handled each event, so behavior changes can be traced post-hoc.

Because manual version-bump discipline is unreliable, a **config-steward agent** handles this automatically: on every commit to `/agents/` or `/shared/`, it reads the diff, proposes a version bump and changelog entry, and commits it alongside the original change. The human reviews this like any other PR.

---

## Phased implementation plan

Build **right-to-left**: automate the downstream steps first, so every upstream step has a working downstream to feed. Each phase delivers end-to-end value, even if "end-to-end" starts with the human doing everything except the last step.

### Phase 0 — Manual baseline with role separation

Before any orchestration, run one feature end-to-end manually using the role separation planned for the final system. Open discrete Claude Code sessions, each instructed to act as one role. No polling loop, no automation.

Deliverables: validated role definitions, initial drafts of shared artifacts (schemas, templates, protocols), a list of rules discovered to be missing.

### Phase 1 — Component agent automation

Write the component-agent `CLAUDE.md` and supporting rules. Manually create GitHub issues with work unit prompts; the component agent picks them up and executes. Iterate until component agents reliably produce mergeable PRs for simple tasks.

Deliverables: stable component-agent configuration, issue-body templates, verification discipline, basic trust in the issue-to-PR loop.

### Phase 2 — PM agent automation

Automate task-graph generation and issue creation from an approved feature spec. The specs phase remains manual. The PM agent takes a completed spec, collaborates with the human on work unit prompts, produces the task graph, and opens issues once approved.

Deliverables: PM agent configuration, plan-review UX, dependency recomputation logic.

### Phase 3 — QA agent automation

Plug the QA agent into the pipeline for test plan authoring, execution, and regression curation. Feature-level value begins here, not just per-task value.

Deliverables: QA agent configuration, test plan file conventions in the product specs repo, execution result logging to the event log.

### Phase 4 — Specs agent and chat front-end

Automate the conversational spec-drafting phase. This is deferred to near-last because the human is already heavily in the loop here and a poor prompt has the lowest blast radius.

### Phase 5 — Generator feedback loop automation

Automate the flow where agent-raised issues trigger generator template adjustments and regeneration. Deferred longest because of highest blast radius and lowest per-occurrence frequency once things stabilize.

---

## Open-source readiness discipline

Even while the orchestrator is developed privately, the following practices keep the eventual migration cheap:

- Documentation is written generically, with no consumer-product references. Product-specific mappings live in a separate configuration directory that never moves with the migration.
- License headers (Apache 2.0 or MIT; decide early) are applied from the first commit.
- Commit messages avoid product-specific leakage and are written as if eventually public.
- No secrets, customer data, or sensitive fixtures are ever committed.
- Migration when the time comes is a **fresh-cut** to `github.com/specfuse/orchestrator` with clean history, not a GitHub repo transfer.

Prompts, rules, and CLAUDE.md files are part of the public product on open-sourcing. They should be written from day one as artifacts comfortable to publish.

---

## Open items for downstream documents

The following decisions were acknowledged but not settled in the design conversation and should be revisited in the downstream documents or during Phase 0:

- Exact thresholds for spinning detection (iterations, wall-clock, token budget)
- License choice (Apache 2.0 vs MIT)
- Specific tech choices for the polling loop (shell script, Python, etc.)
- Concrete event types beyond the minimum listed
- Naming conventions for feature registry markdown files
- Specific labels/taxonomy for GitHub issues to encode task state and type

---

## How to use this document in downstream sessions

**Vision document session**: use the "Project positioning," "Vision summary," "Non-goals," and "Open-source readiness" sections as primary source material. The vision document is for humans; it should communicate why this exists, what it does at a high level, what it isn't, and who it's for.

**Architecture document session**: use the "Core concepts," "State machines," "Infrastructure and repository layout," "Coordination substrate," "Agent configuration layout," and "Generated code safety" sections as primary source material. The architecture document is read by both humans and agents; it should include a mermaid diagram showing repos, agents, and flow between them.

**Implementation plan session**: use the "Phased implementation plan" section as the skeleton, expanded with specifics. Per the earlier decision: produce detailed work unit prompts for Phases 0 and 1; for Phases 2–5, produce structured placeholders with clear acceptance criteria to be filled in later based on prior-phase learnings.
