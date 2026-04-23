# Specfuse Orchestrator — Implementation Plan

## How this document is organized

This is the operational plan for building the Specfuse Orchestrator. It divides the work into six phases and, within each phase, into discrete work units. Phases 0 and 1 contain fully-specified work unit prompts intended for direct use in Claude Code sessions. Phases 2 through 5 contain structured placeholders: objectives, prerequisites, deliverables, and acceptance criteria are present, but detailed work unit prompts are deliberately deferred until the prior phase has completed and its lessons are available.

The phasing follows the right-to-left principle from the design summary: automate downstream steps first, so every upstream automation has a working downstream to feed. Phase 0 validates role separation by doing everything manually. Phase 1 automates the last link in the chain — the component agent — because that's the narrowest, most testable surface. Each subsequent phase adds one more automated link upstream.

The vision document (`orchestrator-vision.md`) and architecture document (`orchestrator-architecture.md`) are normative references throughout. When a work unit prompt says "per the architecture," the session must read the architecture document; when it says "per the vision," the vision document is authoritative. The design summary (`orchestrator-design-summary.md`) is the source both downstream documents were derived from and serves as the tiebreaker when they disagree.

### Model selection

**Default for all work units in this project: Claude Opus 4.7.** The artifacts produced here — shared schemas, templates, protocols, `CLAUDE.md` files, skills, rules — are the substrate every future agent session executes against. Quality compounds: a subtle ambiguity in a shared protocol gets paid back in every task that ever touches that rule. For foundational work of this shape, using the strongest model is an easy call.

Deviations are called out per work unit. Broadly:

- **Mechanical scaffolding** (`mkdir`, boilerplate, `.gitignore`): Sonnet 4.6 is sufficient.
- **Walkthrough execution** (Phase 0 and Phase 1 end-to-end exercises): run with whichever model the *production* role config targets. Validating an Opus config by running it against Opus tells you nothing if production will use Sonnet.
- **Retrospectives**: Sonnet 4.6 is sufficient — the work is synthesis against a concrete log, not novel design.

### License decision

The design summary leaves the license choice open between Apache 2.0 and MIT. This plan resolves that in work unit 0.1 by applying **Apache 2.0** from the first commit: the patent grant protects both contributors and downstream adopters, and the added friction over MIT is negligible for a project intended for open release. If you want MIT instead, raise it before 0.1 runs and the work unit adjusts trivially.

---

## Phase 0 — Manual baseline with role separation

### Phase 0 objective

Run one real feature end-to-end across discrete Claude Code sessions, each playing one of the four operational roles, with no automation between them. Produce a validated set of foundational artifacts (schemas, templates, protocols, role configs v0.1) and a catalogue of every friction point, missing rule, and ambiguous handoff observed during the walkthrough.

### Phase 0 acceptance criteria

- The orchestration repo exists with the full directory structure from architecture §4.2.
- Shared schemas for event log entries, feature frontmatter, override records, and GitHub issue labels exist in `/shared/schemas/`.
- Shared templates for work unit issues, spec issues, QA regression issues, human escalations, and feature registry markdown exist in `/shared/templates/`.
- Shared protocols (correlation IDs, state vocabulary, never-touch list, override registry, escalation, verify-before-report, security) exist in `/shared/rules/`.
- Minimum-viable `CLAUDE.md` plus `version.md` exists for each of the four operational roles.
- One feature has been walked through end-to-end manually using the role separation, and a written retrospective exists identifying all observed gaps and prioritizing follow-up work.

### Work unit 0.1 — Bootstrap the orchestration repo

**Objective.** Create the orchestration repository skeleton with the full directory structure, license, and initial documentation, ready for subsequent work units to populate.

**Context preamble.** This is the first work unit of Phase 0 of the Specfuse Orchestrator implementation. Nothing precedes it. Subsequent Phase 0 units will populate the directories you create. The orchestrator is intended for eventual open-sourcing at `github.com/specfuse/orchestrator`, so nothing in this commit should reference any specific consumer product or private organization.

**Inputs.** `orchestrator-vision.md`, `orchestrator-architecture.md`, `orchestrator-design-summary.md`.

**Acceptance criteria.**

1. A new git repository exists at a path you are told to create it at (ask the operator if not specified).
2. The top-level directory layout matches architecture §4.2 exactly: `/features/`, `/events/`, `/inbox/`, `/agents/{specs,pm,component,qa}/`, `/shared/{skills,rules,schemas,templates}/`, `/overrides/`, `/scripts/`. Empty directories carry a `.gitkeep` file.
3. An Apache 2.0 `LICENSE` file is at the repo root, with current year and "Specfuse contributors" as the copyright holder.
4. A `NOTICE` file at the repo root names the project and references the license.
5. A root `README.md` explains what the repo is (one paragraph), points readers to the vision and architecture documents, and states the current phase (Phase 0). It does not attempt to be comprehensive documentation.
6. A `.gitignore` excludes typical noise (`.DS_Store`, editor swap files, log files under `/events/*.tmp`, archived inbox files under `/inbox/*.processed/`).
7. A single initial commit with message `chore: bootstrap orchestration repository skeleton` contains all of the above.

**Do not touch.** Do not create any agent configuration files (that's 0.5). Do not create any schemas, templates, or protocols (those are 0.2–0.4). Do not create any scripts (deferred). Do not commit anything that references a specific consumer product, private organization, or business context.

**Verification steps.**

1. Run `git status` and confirm a clean tree.
2. Run `find . -type d -not -path './.git*'` and confirm every directory from architecture §4.2 is present.
3. Run `cat LICENSE | head -5` and confirm it's the Apache 2.0 text.
4. Run `git log --oneline` and confirm exactly one commit exists.

**Suggested model.** Sonnet 4.6. Mechanical scaffolding; Opus would be overkill.

### Work unit 0.2 — Draft shared schemas

**Objective.** Produce the initial JSON schema definitions for event log entries, feature frontmatter, override records, and GitHub issue labels, so every downstream work unit has a stable contract to write against.

**Context preamble.** This is the second Phase 0 work unit. The orchestration repo skeleton from 0.1 exists. Schemas defined here are the machine-readable contracts referenced by every role's `CLAUDE.md`; getting them wrong cascades. Write them precisely but do not over-specify — gaps discovered in the Phase 0 walkthrough will inform a v0.2 revision during the retrospective.

**Inputs.** `orchestrator-architecture.md` (especially §3, §6, §7.3, §9.3), `orchestrator-design-summary.md`, the bootstrapped orchestration repo from 0.1.

**Acceptance criteria.**

1. `/shared/schemas/event.schema.json` defines the JSON Schema for a single event log entry, with all six required fields from architecture §7.3 (`timestamp`, `correlation_id`, `event_type`, `source`, `source_version`, `payload`) and the minimum event type enumeration from §7.3. Timestamp format is ISO 8601 with timezone. Correlation ID pattern matches both feature-level (`FEAT-YYYY-NNNN`) and task-level (`FEAT-YYYY-NNNN/TNN`) forms.
2. `/shared/schemas/feature-frontmatter.schema.json` defines the YAML frontmatter schema for feature registry markdown files: current state (from the feature state machine in §6.1), correlation ID, involved repos (array of strings), autonomy default (`auto` | `review` | `supervised`), and approved task graph (structure may be minimal initially — a list of task objects with id, type, depends_on, and assigned repo).
3. `/shared/schemas/override.schema.json` defines the override record structure per architecture §9.3: files overridden (array of paths), task correlation ID, tracking issue reference (owner/repo#number), expiry condition (string description), timestamp, and override status (`active` | `expired`).
4. `/shared/schemas/labels.md` (not JSON Schema — documents label taxonomy for GitHub issues) enumerates the labels that encode task state and task type, with color suggestions. States: `state:pending`, `state:ready`, `state:in-progress`, `state:in-review`, `state:blocked-spec`, `state:blocked-human`, `state:done`, `state:abandoned`. Types: `type:implementation`, `type:qa-authoring`, `type:qa-execution`, `type:qa-curation`. Autonomy: `autonomy:auto`, `autonomy:review`, `autonomy:supervised`.
5. A brief `/shared/schemas/README.md` explains the purpose of each file and notes that schemas are versioned with the orchestration repo itself (no independent version field).
6. Every schema file validates as syntactically correct JSON Schema (draft 2020-12 or later) or documented markdown.
7. Commit message: `feat(schemas): initial shared schemas for events, features, overrides, and labels`.

**Do not touch.** Do not create templates (that's 0.3). Do not write the event log format into protocol prose (that's 0.4 — schemas are the machine contract, protocols explain the human rules around them). Do not add schema fields not motivated by the architecture document; over-specification before the walkthrough wastes effort.

**Verification steps.**

1. Validate each `.schema.json` file against its declared meta-schema using `ajv` or equivalent: `npx ajv-cli compile -s <file>`.
2. Write one example event, one example feature frontmatter block, and one example override record that each validate against their schema. Include these as `/shared/schemas/examples/` for reference.
3. Run `git diff --stat` and confirm only expected files were touched.

**Suggested model.** Opus 4.7. These are foundational contracts; precision matters.

### Work unit 0.3 — Draft shared templates

**Objective.** Produce the initial markdown templates for the five document types every role produces or consumes: work unit issues, spec issues, QA regression issues, human escalations, and feature registry entries.

**Context preamble.** Third Phase 0 work unit. Schemas exist from 0.2; templates reference those schemas where appropriate. Templates are the human-readable shapes that ride on top of the machine contracts. The work unit issue template, specifically, is the contract defined in architecture §8 — it must enforce the five mandatory sections.

**Inputs.** `orchestrator-architecture.md` (especially §8), `orchestrator-design-summary.md` (especially "Work unit prompts" and "Shared vs role-specific"), `/shared/schemas/` from 0.2.

**Acceptance criteria.**

1. `/shared/templates/work-unit-issue.md` — the issue body template for implementation and QA tasks. Contains exactly the five sections from architecture §8 as top-level headings: `## Context`, `## Acceptance criteria`, `## Do not touch`, `## Verification`, `## Escalation triggers`. Each section includes a one-sentence explanation of what belongs there. The template opens with a frontmatter-style block recording correlation ID, task type, autonomy level, and dependencies.
2. `/shared/templates/spec-issue.md` — template for an issue raised against the product specs repo (or the generator project) when a component or QA agent discovers a spec-level problem. Fields: what was observed, where (file/line), which task triggered the observation, correlation ID of the triggering task, and suggested resolution.
3. `/shared/templates/qa-regression-issue.md` — template for a regression issue opened against an implementation task when QA execution fails. Fields: failed test reference, expected behavior, observed behavior, reproduction steps, correlation ID of the implementation task, and regression count (first failure or repeat).
4. `/shared/templates/human-escalation.md` — template for the inbox file written when an agent needs human attention. Fields: correlation ID, reason for escalation (from enumerated list: spinning detected, autonomy requires approval, spec-level blocker, override expiry needs review), agent's current state, what the human is expected to decide.
5. `/shared/templates/feature-registry.md` — template for a feature markdown file under `/features/`, with YAML frontmatter matching the `feature-frontmatter.schema.json` from 0.2 and a body containing sections for feature description, scope, out-of-scope, and links to relevant specs in the product specs repo.
6. A brief `/shared/templates/README.md` explains each template and notes that templates are the v0.1 revision.
7. Commit message: `feat(templates): initial shared templates for issues, escalations, and feature registry`.

**Do not touch.** Do not create protocols (that's 0.4). Do not create role-specific templates inside `/agents/<role>/` — all templates in this unit are shared. Do not include any product-specific examples.

**Verification steps.**

1. For each template, manually verify the five-section structure (for work-unit-issue.md) or complete field list (for all others) matches the architecture and schemas.
2. Render each template file in a markdown previewer to confirm it formats cleanly.
3. Cross-reference the feature registry template's frontmatter block against `feature-frontmatter.schema.json` and confirm every required field appears.

**Suggested model.** Opus 4.7. Templates are the visible face of the system; wording quality matters.

### Work unit 0.4 — Draft shared protocols and rules

**Objective.** Write the prose-form rules that every agent's `CLAUDE.md` pulls in: correlation IDs, state vocabulary and transitions, the never-touch list, override registry protocol, escalation protocol, verify-before-report discipline, and security boundaries.

**Context preamble.** Fourth Phase 0 work unit. Schemas (0.2) and templates (0.3) exist. This work unit captures the *rules* — the prose that tells an agent how to behave around those artifacts. These files are pulled into every role's `CLAUDE.md` via include directives.

**Inputs.** `orchestrator-architecture.md` (especially §3, §5.3, §6, §9), `orchestrator-design-summary.md` (especially "Shared vs role-specific"), `/shared/schemas/` and `/shared/templates/` from prior units.

**Acceptance criteria.**

1. `/shared/rules/correlation-ids.md` — explains the correlation ID scheme (format, where they appear, how to generate the next one), with concrete examples and failure modes (what happens if an agent generates a malformed ID).
2. `/shared/rules/state-vocabulary.md` — enumerates both state machines (feature and task), lists every state, its meaning, and which role owns the transition *into* that state. Mirrors architecture §6.3 exactly; architecture is normative, this is the pulled-in reference.
3. `/shared/rules/never-touch.md` — the prohibition list: generated directories (any path matching `_generated/` or `gen-src/` or equivalent as declared in the component repo), branch protection configuration, secrets and credentials, anything under the product specs repo's `/business/` subtree, and `.git/` contents.
4. `/shared/rules/override-registry.md` — the protocol for applying, recording, reconciling, and retiring overrides, per architecture §9.3. Covers who writes what and when, and the fact that reconciliation is the component agent's responsibility in the initial model.
5. `/shared/rules/escalation-protocol.md` — how agents raise inbox files for human attention, including the exact escalation reasons and the expected human response loop. References `human-escalation.md` template from 0.3.
6. `/shared/rules/verify-before-report.md` — the discipline every agent must follow: state intent, act, verify, report structured output. Explains what "verify" means for the generic case (re-read produced artifact, run declared verification commands, confirm success) and forbids reporting success without verification.
7. `/shared/rules/security-boundaries.md` — what agents may and may not read/write, how secrets are handled (never read, never logged, never echoed), and how to respond if a task's verification steps would require privileged access.
8. A `/shared/rules/README.md` indexes the above files and explains that each role's `CLAUDE.md` pulls in the full set unless explicitly overriding one (overrides must be justified).
9. Commit message: `feat(rules): initial shared protocols and rules`.

**Do not touch.** Do not modify schemas or templates from prior units. Do not write role-specific rules — those belong in `/agents/<role>/rules/` and are 0.5's concern. Do not write anything that would be false for any of the four roles (if a statement wouldn't apply to all four, it's role-specific).

**Verification steps.**

1. For each file, apply the §5.3 test: would every operational role behave identically under this rule? If not, the content is misplaced.
2. Cross-reference every state transition in `state-vocabulary.md` against architecture §6.3 and confirm one-to-one correspondence.
3. Confirm `never-touch.md` includes all five prohibitions from the architecture and design summary.

**Suggested model.** Opus 4.7. Protocol prose is where ambiguity is most costly; use the strongest model.

### Work unit 0.5 — Draft role configs v0.1

**Objective.** Produce minimum-viable `CLAUDE.md`, `version.md`, and any role-specific skills or rules for each of the four operational roles (specs, PM, component, QA) — "enough to paste into a Claude Code session and have the model behave recognizably as that role."

**Context preamble.** Fifth Phase 0 work unit. Shared schemas, templates, and rules exist. This work unit produces the role layer on top. The quality bar is explicitly "minimum viable" — not production-ready. The Phase 0 walkthrough (0.7) will reveal every gap, and 0.8 codifies the revisions. Do not overbuild here; the walkthrough is where the design gets tested, not this document.

**Inputs.** `orchestrator-vision.md`, `orchestrator-architecture.md` (especially §5), `orchestrator-design-summary.md`, everything in `/shared/` from 0.1–0.4.

**Acceptance criteria.**

1. For each role in `{specs, pm, component, qa}`, `/agents/<role>/CLAUDE.md` exists and contains:
   - An opening section that includes (by reference) the full `/shared/rules/` set.
   - A one-paragraph role definition (what this agent is responsible for).
   - A bullet list of entry transitions this role owns (from architecture §6.3).
   - A bullet list of output artifacts this role produces and where they go.
   - A role-specific verification clause (e.g., the component agent's verification list will be expanded in 1.2; in this unit a placeholder paragraph is acceptable).
   - A role-specific escalation clause citing which conditions the role escalates on.
2. For each role, `/agents/<role>/version.md` exists with initial version `0.1.0` and a changelog entry `0.1.0 — Initial Phase 0 draft`.
3. Role-specific skills or rules directories (`/agents/<role>/skills/`, `/agents/<role>/rules/`) exist and carry `.gitkeep` files. Do not populate them unless a specific need is obvious from the architecture.
4. A `/agents/README.md` indexes the four roles and states the versioning and change process (full protocol lives in config-steward agent's future specification — here, a pointer suffices).
5. Commit message: `feat(agents): initial v0.1 role configurations`.

**Do not touch.** Do not create a config-steward agent (deferred to a later phase — it's a meta-agent and the operational roles must stabilize first). Do not add role-specific content that belongs in `/shared/` (apply the §5.3 test). Do not write production-grade prompts; Phase 1 is where the component agent reaches production quality.

**Verification steps.**

1. For each role, open `CLAUDE.md` and check it reads as internally consistent — no contradictions between the role definition and the transitions/artifacts sections.
2. Confirm every role pulls in the full shared rule set. If any role legitimately overrides a shared rule, the override must be called out explicitly.
3. Confirm `version.md` files are present and correctly initialized.

**Suggested model.** Opus 4.7. Role prompts are the most-reread artifacts in the project.

### Work unit 0.6 — Select and stage the walkthrough feature

**Objective.** Choose a small, concretely-scoped feature that touches exactly two component repositories; stand up (or reuse) a neutrally-owned product specs repo and two neutrally-owned component repos; write the feature's specifications in the specs repo's `/product/` subtree; create the feature registry entry in the orchestration repo's `/features/`; and document the expected happy path in a Phase 0 instrumentation file outside `/features/`.

**Context preamble.** Sixth Phase 0 work unit. This is where the system moves from "configured" to "about to be exercised." The feature's scope must be small enough to walk through in a single day but large enough to genuinely exercise cross-repo coordination. Two components is the right number — one would not test coordination; three or more risks turning the walkthrough into a slog that masks the signal. This is the first work unit that touches more than one repository, so the commit discipline (one commit per repo) and the open-source hygiene rule from 0.1 (no private-org or consumer-product names anywhere) both apply for the first time in tension with each other, and must be resolved by staging every repo under a neutral org.

**Inputs.** The fully-bootstrapped orchestration repo from 0.1–0.5. GitHub access under a neutral org — `specfuse-examples` is the suggested default; any public, non-consumer-product org owned by the operator is acceptable. If the product specs repo and the two component repos under the chosen org don't already exist, create them as part of this unit.

**Acceptance criteria.**

1. A product specs repository exists on GitHub under the chosen neutral org (e.g. `specfuse-examples/product-specs`), with the `/product/` and `/business/` top-level split per architecture §4.1. `/business/` may be empty (a `.gitkeep` suffices), but must exist so the never-touch boundary is meaningful.
2. Under `/product/`, the feature's specification exists at these paths:
   - `/product/specs/<feature-slug>.yaml` — an OpenAPI (or AsyncAPI/Arazzo, whichever fits) fragment describing the feature's contract. If the feature is too shallow for a spec fragment to be meaningful, a placeholder `# intentionally minimal — see feature description` is acceptable but must be called out.
   - `/product/features/<feature-slug>.md` — prose feature description plus a numbered acceptance-criteria list phrased so a QA agent could later author a test plan against each item. These paths are Phase 0 conventions, not yet normative; 0.8 may codify or revise them based on walkthrough findings.
3. Two component repositories exist on GitHub under the same neutral org (e.g. `specfuse-examples/sample-api`, `specfuse-examples/sample-persistence`). Each has: a README identifying the repo as a Phase 0 staged component, a clearly-named `_generated/` directory (with a `.gitkeep` and a `README.md` declaring it as the generated surface), a hand-written code area, and a root-level convention file (e.g. `specfuse.yaml`) declaring `_generated/` as the generated directory per `shared/rules/never-touch.md`.
4. In the orchestration repo, `/features/FEAT-2026-0001.md` exists, populated from the `feature-registry.md` template. Frontmatter values: `correlation_id: FEAT-2026-0001`, `state: drafting`, `involved_repos` listing the two neutral-org component repo slugs from AC#3, `autonomy_default` chosen by the operator, and `task_graph: []`. The body sections (`Description`, `Scope`, `Out of scope`, `Related specs`) are filled in, with `Related specs` linking to the files created in AC#2. If any `/features/FEAT-2026-*.md` file already exists, resolve the collision before proceeding — do not skip forward in the ordinal space.
5. `/events/FEAT-2026-0001.jsonl` exists with exactly one `feature_created` event. Field values: `source: human`, `source_version: n/a` (the event is hand-authored before the polling loop or any agent session exists), `correlation_id: FEAT-2026-0001`, ISO 8601 timestamp with timezone, and a `payload` containing at minimum the feature title and the feature-slug.
6. A walkthrough plan exists at `/docs/walkthroughs/phase-0/FEAT-2026-0001-walkthrough-plan.md` (a Phase 0 instrumentation artifact, deliberately kept outside `/features/` so tooling that globs the registry does not trip over it). The plan documents the expected happy path in enough detail that 0.7 does not have to reinvent it mid-session:
   - Per step: which role acts, what artifacts they produce, which event types they emit, which state transition they own (cite §6.1 or §6.2).
   - For every task in the expected graph: the assigned component repo, the task type, the autonomy level, the dependencies, and the expected verification commands.
   - Explicit statements about whether the walkthrough expects to exercise any of: an `_generated/` override (§9.3), a spec issue, a QA regression, or a spinning self-detection. If none are expected, say so — "no edge cases exercised in this feature" is a valid choice and a useful signal.
7. Commits are one per repo, each with its own message:
   - Orchestration repo: `feat(phase-0): stage walkthrough feature FEAT-2026-0001`.
   - Product specs repo: `chore: initialize product specs repo and FEAT-2026-0001 specs`.
   - Each component repo: `chore: initialize Phase 0 sample component repo`.

**Do not touch.** Do not populate `task_graph` — it stays `[]` until the PM role walks it through `planning` during 0.7. Do not begin the walkthrough itself. Do not run Specfuse validation yet — that belongs to 0.7. Do not use any real consumer-product name or private-org slug anywhere in any of the four repos (involved_repos, filenames, prose, commit trailers, event payloads). Do not place Phase 0 instrumentation files (this walkthrough plan, and by the same convention 0.7's notes and 0.8's retrospective) under `/features/` — that directory is reserved for registry files that validate against `feature-frontmatter.schema.json`; use `/docs/walkthroughs/phase-0/` for instrumentation.

**Verification steps.**

1. Validate the feature frontmatter against the schema using the same approach 0.2 established:
   ```sh
   npx ajv-cli validate \
     -s shared/schemas/feature-frontmatter.schema.json \
     -d <(yq -o=json '.' features/FEAT-2026-0001.md)
   ```
   (or equivalent — the point is schema-round-trip, not the exact command.)
2. Validate the initial event against the event schema:
   ```sh
   npx ajv-cli validate \
     -s shared/schemas/event.schema.json \
     -d events/FEAT-2026-0001.jsonl
   ```
3. Re-read the walkthrough plan and confirm every *feature* state transition from architecture §6.1 that the expected happy path traverses **and** every *task* state transition from §6.2 that the expected happy path traverses is represented at least once. A plan that touches only §6.1 without reaching the task-level loop has skipped the component agent's work and is incomplete.
4. Grep all four repos for any real consumer-product or private-org name and confirm none appear. The chosen neutral-org slug is the only org-scoped string that should show up.

**Suggested model.** Opus 4.7. Feature selection has outsized impact on what Phase 0 teaches you; the strongest model's judgment is worth it.

### Work unit 0.7 — Execute the Phase 0 walkthrough

**Objective.** Walk the staged feature from `drafting` through `done` using discrete Claude Code sessions — one per role — with no automation between them. Record every friction point, missing rule, ambiguous handoff, and template gap encountered.

**Context preamble.** Seventh Phase 0 work unit. This is the first work unit that is *not* a single Claude Code session producing artifacts. It is a human-driven exercise across many sessions, with heavy note-taking. The prompt below is instructions to you, the human operator, not to an agent.

**Inputs.** Everything produced in 0.1–0.6.

**Acceptance criteria.**

1. The staged feature reaches `done` state across all its tasks, or reaches a state where further progress requires design changes you can articulate.
2. Each role (specs, PM, component × 2, QA) has been enacted in at least one discrete Claude Code session, each session initialized with that role's `CLAUDE.md` plus shared rules.
3. For every session, a log exists in `/events/FEAT-2026-0001.jsonl` capturing at least `task_started`, `task_completed` (or `task_blocked`), and any `human_escalation` events. Logs may be written by the human, not the session — the goal is the log, not automation.
4. A `/features/FEAT-2026-0001-walkthrough-notes.md` file captures, per role: what worked, what didn't, what rules were missing, what templates were awkward, what handoffs were ambiguous. Be specific — "the component agent didn't know when to raise a spec issue vs. just asking clarification" is useful; "it was confusing" is not.
5. Commit messages during the walkthrough carry correlation IDs in trailers (`Feature: FEAT-2026-0001/T01`) where applicable.

**Do not touch.** Do not modify `/shared/` artifacts during the walkthrough, even if you notice bugs. Record the gaps and fix them in 0.8. Exception: if an artifact is so wrong it blocks the walkthrough from proceeding at all, fix the minimum necessary and log the fix in the notes.

**Verification steps.**

1. Confirm the event log file is syntactically valid JSONL (`while read line; do echo "$line" | jq .; done < events/FEAT-2026-0001.jsonl`).
2. Confirm the walkthrough notes file has per-role sections, each with concrete observations.
3. Confirm that the design summary's phased plan held up — if not, the ways in which it didn't are themselves primary output.

**Suggested model.** For sessions playing the production roles, use whichever model the role's `CLAUDE.md` targets for production (default: Sonnet 4.6, with Opus available for planning-heavy subtasks). For the human's own orchestration and note-taking session (if Claude is used for it), Opus 4.7 — the synthesis is the whole point.

### Work unit 0.8 — Phase 0 retrospective and artifact refinement

**Objective.** Ingest the walkthrough notes from 0.7, produce a prioritized gap list, update the shared artifacts to close every gap that's a v0.2 concern, and decide whether Phase 0 is done or whether a second walkthrough is required.

**Context preamble.** Eighth and final Phase 0 work unit. The walkthrough produced a friction log; this unit converts that log into artifact revisions. Bias toward addressing gaps that would compound in Phase 1 or later; defer cosmetic or narrowly-scoped issues to the phase that needs them.

**Inputs.** `/features/FEAT-2026-0001-walkthrough-notes.md`, all existing `/shared/` and `/agents/` artifacts.

**Acceptance criteria.**

1. A `/features/FEAT-2026-0001-retrospective.md` file exists, containing: a summary of what went well, a categorized list of gaps (shared-rule gaps, template gaps, role-config gaps, process gaps), and a prioritization (fix now, fix in Phase 1, defer).
2. Every "fix now" gap has been addressed by a corresponding commit to `/shared/` or `/agents/`. Each fix is scoped to a single commit with a descriptive message.
3. Every modified file under `/agents/` has a version bumped in its `version.md` with a changelog line referencing the retrospective.
4. A Phase 0 exit decision is recorded in the retrospective: either "Phase 0 complete, proceed to Phase 1," or "Second walkthrough required, because [reason]." If the latter, outline the second walkthrough scope.
5. Final commit message: `chore(phase-0): close out Phase 0 retrospective`.

**Do not touch.** Do not begin Phase 1 work units — even if the retrospective's conclusion is "proceed." Phase 1 starts in its own session.

**Verification steps.**

1. Confirm every item in the retrospective's "fix now" list has a corresponding commit.
2. Confirm all `version.md` files bumped since 0.5 are at `0.2.0` or higher with matching changelog entries.
3. Re-read the retrospective's exit decision and confirm the reasoning is defensible.

**Suggested model.** Sonnet 4.6. Retrospective synthesis against a concrete log does not need Opus.

---

## Phase 1 — Component agent automation

### Phase 1 objective

Automate the component agent role. PM, specs, and QA remain human-driven. The human manually creates GitHub issues using the work unit template; the component agent picks them up, executes, and produces mergeable pull requests. Iterate until component agents reliably produce mergeable PRs for realistic tasks in real component repositories.

### Phase 1 acceptance criteria

- Component agent `CLAUDE.md` and rules are at v1 quality: production-ready for the narrow range of tasks the agent handles.
- A component agent verification skill exists and is rigorous: the agent runs tests, coverage, linting, compiler warnings, and security scans before declaring done, and reports verifiable evidence.
- A component agent PR and escalation skill exists: branch naming, commit trailer discipline, PR template usage, structured spec-issue raising, self-detecting spinning.
- The work unit issue body template is at v1 and is the locked contract for the PM side going forward.
- At least three progressively realistic tasks have been walked through the component agent end-to-end, with iteration between runs, and the final run produced a mergeable PR with no human intervention inside the agent's loop.
- A Phase 1 retrospective exists identifying remaining gaps and explicitly unblocking Phase 2.

### Work unit 1.1 — Component agent config v1

**Objective.** Elevate the Phase 0 v0.1 component agent `CLAUDE.md` to production v1 quality, incorporating Phase 0 learnings and all constraints from the architecture document.

**Context preamble.** First Phase 1 work unit. The v0.1 config from 0.5 exists and has been stress-tested by the Phase 0 walkthrough. This unit is the rewrite. Every Phase 0 friction point attributable to the component role should be resolved here.

**Inputs.** `/agents/component/CLAUDE.md` v0.1, Phase 0 retrospective, `orchestrator-architecture.md`, all shared rules and templates.

**Acceptance criteria.**

1. `/agents/component/CLAUDE.md` rewritten to v1.0.0 quality. Includes: role definition, exact entry transitions owned (`ready → in_progress → in_review`, plus `in_progress → blocked_spec` and `in_progress → blocked_human`), exact artifact outputs (branch, commits, PR, event log entries), role-specific verification placeholder (filled in 1.2), role-specific PR and escalation placeholder (filled in 1.3), and explicit anti-patterns (e.g., "never modify files under `_generated/` — raise a spec issue instead").
2. Any role-specific rules identified by the Phase 0 retrospective are added to `/agents/component/rules/` as individual files.
3. `version.md` bumped to `1.0.0` with a meaningful changelog entry.
4. A `/agents/component/README.md` exists summarizing the role for someone opening the directory cold.
5. Commit message: `feat(component): v1 component agent configuration`.

**Do not touch.** Do not write the verification skill or PR/escalation skill (1.2 and 1.3). Do not modify shared rules unless the Phase 0 retrospective explicitly assigned that change to this unit.

**Verification steps.**

1. Check `CLAUDE.md` against the architecture §5 requirements: role definition, shared-rules include, transitions, outputs — all present.
2. Confirm no shared content was accidentally duplicated into the role config.
3. Confirm `version.md` bump and changelog entry.

**Suggested model.** Opus 4.7. This config is reread hundreds of times in subsequent phases.

### Work unit 1.2 — Component agent verification skill

**Objective.** Produce a detailed, rigorous verification skill for the component agent that operationalizes the verify-before-report discipline: running tests, coverage, linting, compiler warnings, and security scans, and reporting verifiable evidence.

**Context preamble.** Second Phase 1 work unit. The component agent config v1 from 1.1 exists but references this skill as a placeholder. This unit writes the skill. The verification gates here must match the branch protection checks from architecture §10, because an agent that passes its own verification but fails branch protection is doing the wrong thing.

**Inputs.** `/agents/component/CLAUDE.md` v1, `orchestrator-architecture.md` (especially §10), `/shared/rules/verify-before-report.md`.

**Acceptance criteria.**

1. `/agents/component/skills/verification/SKILL.md` exists and describes, step by step: how the agent determines which verification commands apply to the current component repo (reading a convention file — propose a name, e.g., `.specfuse/verification.yml` — in the component repo that declares test commands, coverage thresholds, linter commands, security scan commands), how to run each, how to interpret output, and how to report results in the `task_completed` event payload.
2. The skill explicitly handles failure: if any gate fails, the agent does *not* report `task_completed`; it iterates (up to the spinning threshold) or escalates via `blocked_human`.
3. The skill includes a worked example of a clean verification run and a worked example of a failing run that gets retried.
4. The skill's output format is strict: every verification result is a structured object with `gate_name`, `status` (`pass` | `fail`), `evidence` (command output excerpt or artifact reference), and `duration_seconds`.
5. Coverage threshold (≥ 90% per architecture §10), zero compiler warnings, clean lint, clean OWASP scan, and all tests passing are all listed as mandatory gates.
6. Commit message: `feat(component): verification skill v1`.

**Do not touch.** Do not modify `CLAUDE.md` beyond replacing the 1.1 placeholder with a reference to the new skill. Do not write the PR/escalation skill (1.3). Do not propose new branch protection checks — those are architectural and changing them requires updating the architecture document first.

**Verification steps.**

1. For a chosen real component repo, manually follow the skill on a trivial task and confirm every gate can actually be run using the declared command set.
2. Confirm the `task_completed` payload structure matches the event schema from `/shared/schemas/event.schema.json`.
3. Confirm the failure path is clearly distinguishable from the success path in the skill.

**Suggested model.** Opus 4.7. Verification rigor is the difference between trusted and untrusted agent output.

### Work unit 1.3 — Component agent PR and escalation skills

**Objective.** Produce two tightly-related skills: one for outgoing work (branch naming, commit trailers, PR creation, PR description format) and one for outgoing communication (raising spec issues, self-detecting spinning, writing human-escalation inbox files).

**Context preamble.** Third Phase 1 work unit. These are bundled because both are outgoing communication — the agent producing artifacts for other parts of the system to consume. Keeping them in one work unit avoids ping-pong between skill files.

**Inputs.** Component agent config v1, verification skill v1, all shared templates, `orchestrator-architecture.md` (§6, §7, §8, §9, §10).

**Acceptance criteria.**

1. `/agents/component/skills/pr-submission/SKILL.md` describes: branch naming (format `feat/FEAT-YYYY-NNNN-TNN-slug` or similar — propose and justify the format), commit message structure including the correlation ID trailer (`Feature: FEAT-YYYY-NNNN/TNN`), PR title format, PR description template (summarizing the task, linking to the issue, linking to any spec issues raised during execution), and the exact moment at which the PR transitions the task to `in_review` (event emission and label change).
2. `/agents/component/skills/escalation/SKILL.md` describes: the exact conditions that trigger each escalation type (spec issue, human escalation, spinning self-detection), how to write the issue or inbox file, and what the agent does *after* escalation (stop, do not continue).
3. The spinning self-detection logic is explicit: the agent tracks consecutive failed verification cycles internally and transitions to `blocked_human` at three. Wall-clock and token budget thresholds are marked as "configured at runtime — check environment."
4. The escalation skill cross-references the shared templates (`spec-issue.md`, `qa-regression-issue.md`, `human-escalation.md`) rather than duplicating their structure.
5. Both skills include worked examples.
6. Commit message: `feat(component): PR submission and escalation skills v1`.

**Do not touch.** Do not modify verification skill from 1.2. Do not write QA regression detection — that's QA agent territory in Phase 3.

**Verification steps.**

1. Walk through the PR submission skill mentally for a trivial task and confirm the branch name, commit format, and PR description all thread the correlation ID correctly.
2. Walk through each escalation type and confirm the agent has clear exit criteria (spinning → `blocked_human` and stop; spec issue → file created and stop; etc.).
3. Confirm the skills cite the shared templates rather than redefining them.

**Suggested model.** Opus 4.7. Outgoing communication quality is a trust multiplier.

### Work unit 1.4 — Work unit issue body template v1

**Objective.** Lock down the work unit issue body template as the contract between the (future) PM agent and the component agent, incorporating Phase 0 and early Phase 1 learnings.

**Context preamble.** Fourth Phase 1 work unit. The template from 0.3 is v0.1. Phase 0 stress-tested the five-section shape; Phase 1 iterations 1.1–1.3 have produced concrete patterns the component agent expects. This unit hardens the template to v1. Going forward, every work unit issue must conform; the PM agent in Phase 2 will produce to this contract and fail its self-check if it doesn't.

**Inputs.** `/shared/templates/work-unit-issue.md` v0.1, Phase 0 retrospective, component agent skills v1.

**Acceptance criteria.**

1. `/shared/templates/work-unit-issue.md` rewritten to v1.0 quality. The five sections from architecture §8 are preserved as the top-level structure. Each section's description is tightened — worked examples may be added inline as comments.
2. Frontmatter block is finalized: correlation ID (required), task type (required), autonomy level (required), dependencies (array, possibly empty), component repo (required for implementation and QA tasks), and a `generated_surfaces` field listing any `_generated/` files this task's acceptance depends on (so the PM agent can cross-check template coverage in Phase 2).
3. A companion `/shared/templates/work-unit-issue.example.md` shows a fully-filled template for a realistic fictional task.
4. The template's introduction references architecture §8 and marks this contract as "hard — malformed issues are rejected."
5. Commit message: `feat(templates): work unit issue body v1`.

**Do not touch.** Do not change the five-section structure — it is architecturally fixed. Do not modify other templates.

**Verification steps.**

1. Re-read architecture §8 and confirm every named requirement appears.
2. Cross-check the frontmatter block against what the component agent skills actually consume.
3. Confirm the example renders as a valid issue body.

**Suggested model.** Opus 4.7. Contracts are expensive to change.

### Work unit 1.5 — Phase 1 walkthrough

**Objective.** Run three progressively more realistic tasks through the component agent end-to-end: a trivial task, a moderately complex task, and a task designed to exercise edge cases (a generated-code override, a spec issue, a spinning scenario). Iterate the config and skills between runs.

**Context preamble.** Fifth Phase 1 work unit. This is the empirical validation of everything 1.1–1.4 produced. It is a multi-session exercise like 0.7 — the prompt here is instructions to the human operator.

**Inputs.** Full component agent config and skills v1; two or more real component repos; a collaborator who plays the PM role manually (writing work unit issues that conform to the template).

**Acceptance criteria.**

1. Task A (trivial): something a component agent should handle with zero human intervention. Produces a mergeable PR. If it doesn't, iterate on config and re-run. Stop iterating after three unsuccessful cycles and escalate to a design discussion.
2. Task B (moderate): spans two files, requires writing a new test, involves some genuine design judgment within tight constraints. Produces a mergeable PR possibly requiring one round of human PR review feedback.
3. Task C (edge-case-stressing): one of — a task where an `_generated/` file must be overridden (exercise 9.3), a task where a spec ambiguity forces a `blocked_spec` escalation, or a task that should trigger spinning self-detection. Pick based on which edge cases feel most under-tested.
4. For each task, a `walkthrough-log.md` file records: issue content, agent actions, verification results, PR outcome, and any config changes prompted by the run.
5. Any config or skill changes prompted by the walkthrough are committed as they happen, with `version.md` bumps.
6. Final commit message per run: `chore(phase-1): walkthrough task N complete`.

**Do not touch.** Do not change architectural decisions during the walkthrough. If an architectural problem surfaces, log it and continue with a workaround; it's a retrospective input.

**Verification steps.**

1. Each task produces either a merged PR or a well-documented reason it couldn't.
2. Each task's correlation ID appears in branch name, commits, PR, and event log.
3. The walkthrough log file is honest — if something was hard or hacky, that's more valuable than a sanitized account.

**Suggested model.** For agent sessions: whatever the production config targets (default Sonnet 4.6). For the human's orchestration/note-taking: Opus 4.7.

### Work unit 1.6 — Phase 1 retrospective

**Objective.** Codify discovered gaps from 1.5, freeze the component agent config at its current version as the dependency baseline for Phase 2, and explicitly unblock Phase 2.

**Context preamble.** Sixth and final Phase 1 work unit. Analogous to 0.8 but scoped narrowly to the component agent.

**Inputs.** Phase 1 walkthrough logs, current state of `/agents/component/`.

**Acceptance criteria.**

1. `/agents/component/retrospective-phase-1.md` exists, documenting: tasks run, outcomes, identified strengths, identified weaknesses, remaining gaps.
2. Gaps are categorized: "fix in Phase 1 before freeze," "defer to Phase 2 (because they require PM automation to surface)," "defer indefinitely with documented rationale."
3. All "fix in Phase 1" gaps are closed with commits. `version.md` is at the final v1.x version.
4. An explicit statement declares the component agent config frozen for Phase 2 consumption: "Component agent v1.X is the baseline Phase 2 depends on. Changes to this config during Phase 2 require architectural justification."
5. The retrospective names which task type (implementation vs. QA variants) the agent is considered production-ready for. If QA task types are not yet well-supported, that's acceptable — state it.
6. Commit message: `chore(phase-1): close out Phase 1 retrospective and freeze component agent baseline`.

**Do not touch.** Do not begin Phase 2 work. Do not retroactively edit Phase 0 artifacts.

**Verification steps.**

1. Confirm all "fix in Phase 1" gaps are closed.
2. Confirm the baseline declaration is unambiguous.
3. Confirm `version.md` reflects the final Phase 1 state.

**Suggested model.** Sonnet 4.6. Retrospective synthesis.

### Addendum — post-retrospective Phase 1 fixes (WUs 1.7–1.12)

The WU 1.6 retrospective (merged 2026-04-22) deviated from this plan's original framing of WU 1.6 as both triage and fix-closure: the retrospective was scoped to triage alone, and the five "Fix in Phase 1" findings it surfaced were carried by five subsequent work units, independently landable in any order. A sixth work unit (WU 1.12) records the freeze declaration required by WU 1.6 acceptance criterion #4 once the five fixes are merged.

See [`docs/walkthroughs/phase-1/retrospective.md`](walkthroughs/phase-1/retrospective.md) §"Fix-in-Phase-1 work plan" for the full per-finding rationale, and §"Phase 1 freeze declaration" for the freeze itself. Summary:

- ✅ **WU 1.7 — Event schema validation harness (Finding 1).** Shipped `scripts/validate-event.py` (Draft 2020-12 validator against `shared/schemas/event.schema.json`) and tightened `shared/rules/verify-before-report.md` §3 plus the three component skills to require validator exit `0` before any `events/*.jsonl` append. PR #8.
- ✅ **WU 1.8 — `source_version` runtime read (Finding 2).** Shipped `scripts/read-agent-version.sh` and tightened `shared/rules/verify-before-report.md` §3 to require every event's `source_version` be read from `agents/<role>/version.md` at emission time. PR #9.
- ✅ **WU 1.9 — PM issue-drafting "verify against repo" requirement (Finding 3).** Added `agents/pm/issue-drafting-spec.md` as a forward specification constraining the Phase 2 PM issue-drafting skill. PR #11.
- ✅ **WU 1.10 — Spec-issue routing for specs-less features (Finding 4).** Amended `agents/component/skills/escalation/SKILL.md` §2 to route specs-less features' spec issues against the orchestrator repository. PR #10.
- ✅ **WU 1.11 — `source: component:<name>` convention (Finding 7).** Clarified in `shared/schemas/event.schema.json` that `<name>` is the bare component repo name, no owner prefix. PR #10.
- ✅ **WU 1.12 — Phase 1 freeze declaration.** Recorded in `docs/walkthroughs/phase-1/retrospective.md` §"Phase 1 freeze declaration"; cross-referenced from `agents/component/CLAUDE.md` header and `agents/component/version.md` subtitle. Component agent v1.5.0 is the Phase 2 baseline.

**Phase 1 frozen as of 2026-04-22.** Phase 2 (PM agent automation) can now begin from the corrected configuration and the documented deferred list.

---

## Phase 2 — PM agent automation

### Phase 2 objective

Automate task-graph generation and GitHub issue creation from an approved feature spec. The specs phase remains manual (the human drafts specs with chat-based Claude assistance). Once a feature spec is validated, the PM agent produces the task graph, collaborates with the human on work unit prompts, and opens issues once the plan is approved. Dependency recomputation on task completion is automated. The PM agent performs template-coverage checks at planning time via a stub protocol (real generator integration is deferred to Phase 5 per the right-to-left phasing).

### Phase 2 known prerequisites

- Phase 1 complete and component agent config frozen at v1.5.0 (declared 2026-04-22).
- Work unit issue body template at v1 (locked contract).
- Shared schemas for feature frontmatter, event log, and labels stable.
- `scripts/validate-event.py` and `scripts/read-agent-version.sh` available as part of the frozen baseline — the PM agent reuses them verbatim on the emission path.
- `agents/pm/issue-drafting-spec.md` (from WU 1.9) — the inherited forward contract WU 2.4 must honor on day one.
- A stub template-coverage protocol is acceptable; the real generator-query integration is deferred to Phase 5.

### Phase 2 deliverables

- PM agent `CLAUDE.md`, skills, and rules at production v1 quality.
- A task-decomposition skill that turns a validated feature spec into a task graph in `/features/FEAT-YYYY-NNNN.md` frontmatter.
- A plan-review UX skill producing a diffable, editable markdown representation of the task graph for the human to review and modify before approval.
- An issue-drafting skill that honors `agents/pm/issue-drafting-spec.md` on day one — every claim about target-repo state re-verified at draft time.
- A dependency-recomputation skill that listens for `task_completed` events and flips newly-unblocked tasks from `pending` to `ready`, updating GitHub labels and emitting `task_ready`. Absorbs Phase 1 deferred Finding 5 (per-type `task_started` payload schema with `branch: string | null`, establishing the pattern under `/shared/schemas/events/`).
- A template-coverage-check skill implementing a stub protocol (component repos declare their template needs in a convention file; PM reads at planning time and escalates on gaps). Real generator integration scoped to Phase 5.
- A Phase 2 walkthrough exercising the full specs-to-issues pipeline on two features (happy-path + edge-case).
- A Phase 2 retrospective and post-retrospective fix ladder analogous to WU 1.6–1.12.
- Phase 1 deferred Finding 6 (shared-rules re-read discipline at role-switch) absorbed into WU 2.1.

### Phase 2 acceptance criteria

- The PM agent, given a validated feature spec, produces a task graph that correctly identifies implementation and QA tasks, their dependencies, and their target component repos.
- The human can edit the task graph as a file (dependencies, prompts, autonomy overrides) and the PM agent re-ingests the edit as the new source of truth.
- Upon approval, the PM agent opens conforming GitHub issues in the correct repos, each with a work-unit-issue-template-compliant body whose every claim about repo state was verified at drafting time per `issue-drafting-spec.md`.
- When a task reaches `done`, the PM agent recomputes dependencies and flips ready-tasks correctly, without duplicate issue creation and without trusting any cached view of GitHub labels.
- Template coverage gaps are identified at planning time via the stub protocol, not discovered mid-implementation.

### Work unit 2.1 — PM agent config v1

**Objective.** Elevate the Phase 0 v0.2.0 PM agent `CLAUDE.md` to production v1 quality, incorporating Phase 1 learnings, the inherited forward contract from WU 1.9, and the Phase 1 deferred Finding 6 (shared-rules re-read discipline at role-switch).

**Context preamble.** First Phase 2 work unit. The v0.2.0 config in `agents/pm/CLAUDE.md` is a Phase 0 draft plus the WU 1.9 "Phase 2 specification inputs" pointer. This unit is the rewrite — the placeholder sections filled in, the skills referenced by name, and the verification/escalation clauses tightened against Phase 2's actual surface. The PM agent is the role most likely to follow or precede another agent role in the same human session (planning → issue creation → component review), making it the natural home for the Finding 6 absorption.

**Inputs.** `agents/pm/CLAUDE.md` v0.2.0, `agents/pm/issue-drafting-spec.md`, `docs/walkthroughs/phase-1/retrospective.md` (especially Finding 6 and the freeze declaration), `orchestrator-architecture.md` §5 and §6.3, every file under `/shared/rules/`.

**Acceptance criteria.**

1. `agents/pm/CLAUDE.md` rewritten to v1.0.0 quality, with: one-paragraph role definition; bullet list of every entry transition the role owns (feature-level and task-level per architecture §6.3); explicit artifact outputs (task graph in feature frontmatter, task issues in component repos, work unit prompts co-authored with the human, event log entries, dependency recomputation discipline, human-escalation inbox files); a role-specific verification clause that references the four Phase 2 skills; and a role-specific escalation clause enumerating the PM-relevant conditions.
2. Finding 6 absorbed. The fix is a clause in `agents/pm/CLAUDE.md` stating that `/shared/rules/*` must be re-read unconditionally at the start of every task, including after role-switches within the same session. The clause names the failure mode it prevents. If the author judges the shared surface (`shared/rules/verify-before-report.md` or a new `shared/rules/role-switch-hygiene.md`) to be a better home, the shared-surface edit must be justified in the commit message against the Phase 1 freeze — the retrospective's explicit carve-out for Finding 6 provides that justification.
3. `agents/pm/rules/` populated with any role-specific rules surfaced by Phase 1 walkthroughs or by the design of the Phase 2 skills. If no role-specific rules are needed at v1, leave the `.gitkeep` and justify the decision in the commit message rather than creating empty placeholders.
4. `agents/pm/README.md` exists, summarizing the role for a cold reader (one paragraph + pointer to `CLAUDE.md` + current version).
5. `agents/pm/version.md` bumped to `1.0.0` with a meaningful changelog entry citing this work unit, the Finding 6 absorption, and the Phase 2 skill set the config now references.
6. The "Phase 2 specification inputs" section in `CLAUDE.md` is preserved. It points to `agents/pm/issue-drafting-spec.md` and is structured as an extensible list so subsequent Phase 2 WUs can append additional inherited specs if any emerge.
7. Commit message: `feat(pm): v1 PM agent configuration`.

**Do not touch.** Do not write the Phase 2 skills themselves (they are 2.2–2.6). Do not modify the frozen component agent surface. Do not edit `agents/pm/issue-drafting-spec.md` — it is an inherited contract and any change to it requires the same level of architectural justification as a shared-rule amendment. Do not create empty skill files under `agents/pm/skills/` — those land in their own WUs.

**Verification steps.**

1. Open `agents/pm/CLAUDE.md` and verify every architecture §6.3 transition the PM agent owns appears exactly once, with no contradictions against shared rules.
2. Re-read `docs/walkthroughs/phase-1/retrospective.md` §Finding 6 and confirm the absorbed clause addresses the failure mode as described.
3. Run `scripts/read-agent-version.sh pm` and confirm output is `1.0.0`.
4. Confirm no shared rules were silently duplicated into the role config (the §5.3 test applied in reverse).

**Suggested model.** Opus 4.7. This config is re-read on every PM-agent invocation across Phase 2+.

### Work unit 2.2 — Task decomposition skill

**Objective.** Produce the skill that turns a validated feature spec into a complete task graph persisted in the feature registry frontmatter — the first skill in the PM pipeline.

**Context preamble.** Second Phase 2 work unit. The PM config v1 from 2.1 references this skill as a placeholder. The skill is the entry point for every feature after specs validation: it reads the product specs, identifies implementation and QA tasks (QA subtypes per architecture §6.2), assigns each to a component repo, infers dependencies, and sets autonomy levels. The output task graph is the load-bearing internal contract of Phase 2 — every downstream skill (plan-review, issue-drafting, dependency-recomputation, template-coverage) consumes it.

**Inputs.** PM config v1 from 2.1, `shared/schemas/feature-frontmatter.schema.json`, `shared/schemas/labels.md`, `shared/templates/work-unit-issue.md`, `shared/templates/feature-registry.md`, example product specs from the Phase 0/1 neutral-org repos.

**Acceptance criteria.**

1. `agents/pm/skills/task-decomposition/SKILL.md` v1.0 exists, describing step by step: how the agent reads the feature's spec files from the product specs repo; how it identifies implementation vs. QA tasks and assigns QA subtypes; how it infers the target component repo for each task (the inference rules are documented explicitly — the skill does not guess); how it sets autonomy levels (feature-level default plus per-task override); and how it constructs the `depends_on` edges.
2. The output task graph is written to the feature frontmatter at `/features/FEAT-YYYY-NNNN.md` and validates against `shared/schemas/feature-frontmatter.schema.json` with no orphan `depends_on` references and no cycles. The skill's verification section mandates a cycle check and an orphan check before writing.
3. The skill emits a `task_graph_drafted` event on completion. The `shared/schemas/event.schema.json` enum is extended in this WU to include the new type (additive change — no existing events are affected). Events are validated via `scripts/validate-event.py` before appending.
4. A worked example in the skill shows a task graph for a small realistic feature (two component repos, one implementation task per repo, one `qa-authoring` task, one `qa-execution` task, dependencies correctly wired).
5. The skill does not validate template coverage — that is WU 2.6's concern, called as a subsequent pipeline step by the PM `CLAUDE.md` orchestration. The skill also does not draft issue bodies — that is WU 2.4.
6. Commit message: `feat(pm): task decomposition skill v1`.

**Do not touch.** Do not draft issue bodies (2.4). Do not implement the plan-review UX (2.3). Do not modify `shared/schemas/feature-frontmatter.schema.json` beyond what is strictly needed to support the task graph output — over-specification risks breaking existing Phase 1 consumers.

**Verification steps.**

1. Round-trip the worked example's task graph through `shared/schemas/feature-frontmatter.schema.json` using `ajv` or equivalent.
2. Run a cycle-detection check on the worked example and confirm it passes.
3. Confirm `task_graph_drafted` events validate through `scripts/validate-event.py`.
4. Read the inference rules for target-repo assignment and autonomy level: can a PM agent given an arbitrary spec produce a reproducible answer? If two reasonable readings of the rules yield different graphs, tighten the rules.

**Suggested model.** Opus 4.7. The task graph shape is a hard contract for every downstream skill in Phase 2.

### Work unit 2.3 — Plan-review UX skill

**Objective.** Produce the skill that materializes the task graph as a human-editable markdown document for the `planning → plan_review` stage, and re-ingests any edits the human commits back into the feature frontmatter as the new source of truth.

**Context preamble.** Third Phase 2 work unit. The plan-review step is the human's primary decision point on a feature. The design constraint: the human must be able to edit one file to adjust the task graph (dependencies, autonomy overrides, work unit prompts) and have the PM agent faithfully ingest the edit. The state transition `plan_review → generating` is owned by the human (per the single-owner invariants in `shared/rules/state-vocabulary.md`); this skill prepares the diffable surface the human operates on and handles the round-trip, but it does not itself flip state into `generating`.

**Inputs.** Task decomposition skill from 2.2, `shared/schemas/feature-frontmatter.schema.json`, `shared/templates/feature-registry.md`.

**Acceptance criteria.**

1. `agents/pm/skills/plan-review/SKILL.md` v1.0 exists, describing: the canonical markdown representation of a task graph as a human reviews it (propose and document a format — e.g. a summary table plus per-task prose sections, with machine-parseable fenced YAML blocks where needed); how the skill emits it from the feature frontmatter into a review file under `/features/FEAT-YYYY-NNNN-plan.md` (or equivalent — propose and justify the path); how the skill detects and re-ingests human edits; and how the skill emits `plan_ready` on entry to `plan_review`.
2. Re-ingest discipline: the skill does not cache any portion of the plan across edits — it re-reads the plan file, re-validates the resulting graph against `feature-frontmatter.schema.json`, and either updates the feature frontmatter or escalates `spec_level_blocker` if the edit is malformed (unresolvable cycle, orphan dep, unknown repo, unknown autonomy level).
3. The skill explicitly does not own `plan_review → generating` — that transition is the human's. The skill emits `plan_ready`, updates the feature state to `plan_review`, and waits for an external trigger (a `plan_approved` event emitted when the human signals via label or a separate file). The trigger-detection loop itself is outside this skill's scope.
4. A worked example shows a draft plan, a non-trivial human edit that adjusts one dependency, retargets a task to a different repo, and tightens a work unit prompt, and the skill's re-ingest output with the resulting feature frontmatter re-validating cleanly.
5. Events (`plan_ready`, and any others the skill introduces) validate through `scripts/validate-event.py`; the event schema enum is extended in this WU if needed.
6. Commit message: `feat(pm): plan review UX skill v1`.

**Do not touch.** Do not flip feature state to `generating` from within the skill (the human owns that transition). Do not modify the task decomposition skill output shape — consume it as the upstream contract. Do not draft issue bodies (2.4).

**Verification steps.**

1. Walk through the worked example and confirm the re-ingested feature frontmatter re-validates against the schema.
2. Confirm the plan markdown format is diffable — `git diff` on a realistic edit produces readable output, not a wholesale replacement.
3. Confirm the skill has clear exit criteria: `plan_ready` emitted, feature state flipped to `plan_review`, wait for external trigger, do not loop.

**Suggested model.** Opus 4.7. The plan-review surface is the human's primary feature-level interaction; format clarity is a UX-quality decision that compounds across every feature.

### Work unit 2.4 — Issue-drafting skill

**Objective.** Produce the skill that drafts GitHub issue bodies for every task in an approved plan and opens them against the correct component repos — the Phase 2 WU with the heaviest inherited contract from Phase 1 (WU 1.9 forward spec `agents/pm/issue-drafting-spec.md`).

**Context preamble.** Fourth Phase 2 work unit — the hardest in the phase. The inherited contract is not optional: every factual claim about target-repo state in an issue body must be re-verified at draft time, not from any earlier observation in the session or from the feature registry. The failure mode this prevents (WU 1.5 Task B, symmetry-assertion proved false mid-execution) is a first-class escalation cost if reintroduced. The skill is the PM agent's outgoing contract with every downstream component agent; quality here compounds across every task in every feature.

**Inputs.** PM config v1, task decomposition skill v1, plan-review UX skill v1, `agents/pm/issue-drafting-spec.md` (inherited contract — read in full before writing), `shared/templates/work-unit-issue.md` v1, `shared/schemas/labels.md`, `shared/schemas/event.schema.json`.

**Acceptance criteria.**

1. `agents/pm/skills/issue-drafting/SKILL.md` v1.0 exists and implements every clause of `agents/pm/issue-drafting-spec.md` §Discipline:
   - **Per-claim verification**: every assertion in the issue body about target-repo state is paired with a verification action (command, file read, grep) taken at draft time. The skill's format makes the verification log visible.
   - **No transitive trust**: the skill explicitly forbids inferring "X is still true" from an earlier observation in the same session or from the feature registry.
   - **Reformulate-or-escalate**: when a claim cannot be verified, the skill either reformulates to what *is* verifiable, or escalates `spec_level_blocker`. The skill does not ship hedged claims.
2. Evidence logging per `issue-drafting-spec.md` §Evidence logging: the skill designates the durable surface where verifications are recorded (transcript, Context paragraph, or event payload). The choice is explicit, documented in the skill, and used consistently for every issue the skill produces. Silent drafting is forbidden.
3. The skill opens GitHub issues against the correct component repo, title `[FEAT-YYYY-NNNN/TNN] <summary>`, body conforming to `shared/templates/work-unit-issue.md` v1, labels `state:pending` plus the applicable `type:*` and `autonomy:*` entries per `shared/schemas/labels.md`.
4. The skill emits a `task_created` event per issue (new event type — extend `shared/schemas/event.schema.json` enum) referencing the issue's `owner/repo#number`, title, task-level correlation ID, autonomy, and target repo. For tasks whose `depends_on` array is empty, the skill additionally flips `state:pending → state:ready` and emits `task_ready` in the same pass (no-dep tasks are the only case the issue-drafting skill itself owns the ready-flip; all other ready-flips are WU 2.5's responsibility). Events validate through `scripts/validate-event.py`.
5. A worked example in the skill shows: a draft issue body with three claims about repo state; three verification actions taken at draft time; the resulting issue body with the verification evidence recorded on the chosen surface; and the resulting `task_created` (and, for the no-dep task, `task_ready`) event emissions.
6. Commit message: `feat(pm): issue drafting skill v1`.

**Do not touch.** Do not modify `agents/pm/issue-drafting-spec.md` — it is an inherited contract. Do not modify `shared/templates/work-unit-issue.md` (any template adjustment emerging from this WU's design process is deferred to the retrospective 2.8). Do not write the dependency-recomputation skill (that is 2.5). Do not re-verify claims that `issue-drafting-spec.md` scopes out (orchestrator-internal state — event log, feature registry, labels — has its own verification disciplines).

**Verification steps.**

1. Read the skill against `agents/pm/issue-drafting-spec.md` clause by clause and confirm every requirement is implemented, not paraphrased-away. If any clause is implicit, make it explicit.
2. Walk the worked example against a real component repo (the Phase 1 sample repo is acceptable) and confirm every verification command actually runs and produces the cited output.
3. Confirm the evidence-logging surface is the same across all three claims in the example — if the skill mixes surfaces, tighten.
4. Round-trip the `task_created` and `task_ready` event payloads through `scripts/validate-event.py`.
5. Confirm issue bodies produced by the worked example round-trip against `shared/templates/work-unit-issue.md` v1 — every mandatory section present, frontmatter complete.

**Suggested model.** Opus 4.7 — mandatory. This is the highest-stakes skill in Phase 2; the contract it honors prevents the dominant Phase 1 PM failure mode.

### Work unit 2.5 — Dependency recomputation skill (absorbs Finding 5)

**Objective.** Produce the skill that listens for `task_completed` events and flips newly-unblocked `pending` tasks to `ready`, updating GitHub labels and emitting `task_ready` events. Absorb Phase 1 deferred Finding 5 by formalizing a per-type payload schema for `task_started` with `branch: string | null`, establishing the pattern under `/shared/schemas/events/`.

**Context preamble.** Fifth Phase 2 work unit. This is the one skill that operates outside the initial feature-planning flow — it runs continuously (or via a polling trigger) as tasks complete and unblocks downstream ones. The correctness bar is idempotence: re-running the skill against the same event log must not produce duplicate `task_ready` events or duplicate GitHub label flips. The skill reads labels from GitHub directly (not a local cache) per the single-owner state-transition invariant. Finding 5 is absorbed here because per-type event payload schemas are the relevant territory, and the PM agent is the first role that both consumes (`task_completed`) and emits (`task_ready`) events at scale.

**Inputs.** PM config v1, issue-drafting skill v1 (for the shape of `task_created` and the no-dep `task_ready`), `shared/schemas/event.schema.json`, `scripts/validate-event.py`, `shared/rules/verify-before-report.md` §3, `docs/walkthroughs/phase-1/retrospective.md` §Finding 5.

**Acceptance criteria.**

1. `agents/pm/skills/dependency-recomputation/SKILL.md` v1.0 exists describing: the trigger (a new `task_completed` event on any feature's event log); the recomputation algorithm (walk every `pending` task on the feature, read GitHub labels of every `depends_on` target via a live query — not a cache — and if all are `state:done` flip the task to `state:ready` and emit `task_ready`); the idempotence discipline (before flipping, confirm the task is still `state:pending` on GitHub — if already `state:ready`, skip; if in any other state, escalate `spec_level_blocker`); and the label-write discipline (remove `state:pending`, add `state:ready`, verify the result via re-read before emitting `task_ready`).
2. Finding 5 absorbed. `shared/schemas/events/` directory created. `shared/schemas/events/task_started.schema.json` defines the `task_started` payload shape with `branch` typed as `string | null`. `shared/rules/verify-before-report.md` §3 extended to describe the per-type payload validation discipline: agents validate events against the top-level event schema *and* against the per-type payload schema when one exists at `shared/schemas/events/<event_type>.schema.json`. The `shared/rules/verify-before-report.md` edit is architecturally authorized by the Phase 1 retrospective's carve-out for Finding 5 — the commit message states this.
3. `scripts/validate-event.py` extended to apply the per-type payload schema when one exists, without altering its behavior for event types that have no per-type schema. The additive extension preserves the Phase 1 freeze contract for the component agent's existing emissions — no component-agent event shape changes, no component `version.md` bump required.
4. A worked example in the skill shows a three-task feature (T01, T02 depending on T01, T03 depending on T01 and T02): T01 completes, T02 flips from `pending` to `ready` with a `task_ready` emission, T03 stays `pending`.
5. A second worked example exercises idempotence: the same `task_completed` event replayed produces no duplicate `task_ready` and no duplicate label flip.
6. The skill escalates `spec_level_blocker` on malformed dependency state — a `depends_on` target that no longer exists on GitHub, a cycle appearing post-hoc, labels in an unexpected state. The escalation is on the feature, not on the individual task, because the graph itself is incoherent.
7. Commit message: `feat(pm): dependency recomputation skill v1; refactor(schemas): per-type event payload schemas with task_started precedent (closes Finding 5)`.

**Do not touch.** Do not alter `scripts/validate-event.py` behavior for event types without a per-type schema — the Phase 1 freeze contract for the component agent depends on this. Do not modify component agent emission patterns (frozen). Do not bump `agents/component/version.md` — the component role's emissions are additively still valid.

**Verification steps.**

1. Run `scripts/validate-event.py` against a Phase 1 `task_started` event and confirm it still passes (additive extension preserved).
2. Run `scripts/validate-event.py` against a new `task_started` event with `branch: null` and confirm it passes the new per-type schema.
3. Run `scripts/validate-event.py` against a malformed `task_started` event (e.g. `branch: 42`) and confirm it fails with a useful message.
4. Replay the idempotence worked example end-to-end and confirm no duplicate events and no duplicate labels.
5. Re-read `shared/rules/verify-before-report.md` §3 and confirm the per-type discipline is described in terms the PM, QA, and specs roles can absorb when their phases arrive.

**Suggested model.** Opus 4.7. Idempotence under replay is a subtle invariant; the per-type schema pattern set here governs every future event type across every future role.

### Work unit 2.6 — Template-coverage check skill (stub protocol)

**Objective.** Produce the skill that checks, at planning time, whether the Specfuse generator has templates for every surface the feature's task graph requires — using a stub protocol until the real generator-query integration is built in Phase 5.

**Context preamble.** Sixth Phase 2 work unit. The Phase 2 acceptance criterion "template coverage gaps identified at planning time" is satisfiable without a real generator query: a stub in which each involved component repo declares its own template coverage in a convention file is sufficient to catch the "discovered mid-implementation" failure mode. The right-to-left phasing places the real generator feedback loop in Phase 5; this stub is the Phase 2 expedient. The declaration-file convention established here will likely persist even after Phase 5 replaces the query mechanism, so the choice is made carefully.

**Inputs.** PM config v1, task decomposition skill v1, `agents/component/skills/verification/SKILL.md` v1.1 (for the existing `.specfuse/verification.yml` convention — informs the path choice without modifying the frozen file).

**Acceptance criteria.**

1. `agents/pm/skills/template-coverage-check/SKILL.md` v1.0 exists, describing: the stub protocol (where and how component repos declare their template coverage); the schema of the declaration file; how the skill cross-references the task graph against the declarations; and the escalation clause (`spec_level_blocker` on any unresolved gap — including missing declaration files).
2. The chosen declaration path is documented with a brief rationale (a new file such as `.specfuse/templates.yaml`, or an additive section in `.specfuse/verification.yml`). Whichever path is chosen, it must not require editing the frozen `agents/component/skills/verification/SKILL.md` — additive only.
3. `shared/schemas/template-coverage.schema.json` exists and defines the declaration-file structure. A worked example declaration validates against it.
4. The skill has a `## Deferred integration` section naming Phase 5 as the place where the stub is replaced by a real generator query, and describing the expected shape of that future integration in enough detail that the Phase 5 WU inherits a concrete brief (not a re-discovery pass).
5. Two worked examples: a feature that passes coverage (all templates declared across all involved repos), and a feature that fails (one declared-missing template in one repo; skill produces the `spec_level_blocker` escalation with a clear message).
6. Events (`template_coverage_checked`, `template_coverage_gap`, or equivalent — extend `shared/schemas/event.schema.json` enum as needed) validate through `scripts/validate-event.py`.
7. Commit message: `feat(pm): template coverage check skill v1 (stub protocol)`.

**Do not touch.** Do not modify the frozen `agents/component/skills/verification/SKILL.md` or rename the `.specfuse/verification.yml` convention — additive only. Do not implement a real generator query — that is Phase 5. Do not silently treat absence of a declaration file as coverage — absence is a `spec_level_blocker` so the human either adds the declaration or abandons the task.

**Verification steps.**

1. Validate the worked declaration file against `shared/schemas/template-coverage.schema.json`.
2. Walk both worked examples and confirm the gap-case produces a well-formed escalation with an actionable message.
3. Re-read the `## Deferred integration` section and confirm the Phase 5 WU brief is concrete enough that the Phase 5 author does not have to re-derive it.

**Suggested model.** Opus 4.7. The declaration-file convention established here will outlast the stub itself — precision in the convention pays back in Phase 5.

### Work unit 2.7 — Phase 2 walkthrough

**Objective.** Exercise the PM agent end-to-end on two real features — one happy-path, one edge-case — validating that the Phase 2 skills 2.2–2.6 compose into a working specs-to-issues pipeline. Analogous to WU 1.5.

**Context preamble.** Seventh Phase 2 work unit. This is the empirical validation of everything 2.1–2.6 produced. Like WU 1.5, it is a multi-session human-driven exercise; the prompt here is instructions to the human operator. The two-features shape was chosen deliberately — one feature would not stress the pipeline, three would turn the walkthrough into a slog that masks the signal. The edge case deliberately targets one of the high-risk surfaces (plan re-ingest, template coverage gap, dependency recomputation replay) based on which feels most under-tested at walkthrough time.

**Inputs.** Full PM agent config and skills v1. Phase 1 sample component repos (`Bontyyy/orchestrator-api-sample` and a second staged repo — stand up one under the neutral org if none exists). The neutral-org product specs repo from Phase 0. Two feature specs drafted by the human ahead of the walkthrough.

**Acceptance criteria.**

1. **Feature 1 (happy path)** — validated spec, straightforward task graph (two component repos, one implementation task per repo, one `qa-authoring` and one `qa-execution` task), no edits during plan review, all templates present in the coverage declaration. Expected end state: plan drafted, human approves without edit, issues opened in both component repos, first `task_completed` triggers `task_ready` on the next task, feature reaches `in_progress` cleanly. Produces `docs/walkthroughs/phase-2/feature-1-log.md`.
2. **Feature 2 (edge case)** — pick ONE at walkthrough time:
   - **Plan-review re-ingest stress**: human edits the plan non-trivially (adds a task, retargets a dependency, tightens a work unit prompt); skill re-ingests faithfully.
   - **Template coverage gap**: one component repo missing a required template; stub escalates `spec_level_blocker` at planning time, not mid-implementation.
   - **Dependency recomputation replay**: a `task_completed` event is re-delivered; skill is idempotent (no duplicate `task_ready`, no duplicate label flip).
   Produces `docs/walkthroughs/phase-2/feature-2-log.md`.
3. Logs are honest — friction, workarounds, surprises are recorded, not sanitized. Per-section: what worked, what did not, what was ambiguous, what config or skill needed a tweak.
4. Any config or skill changes prompted by the walkthrough are committed as they happen, with `agents/pm/version.md` bumps and changelog entries.
5. Every event emitted across both features validates through `scripts/validate-event.py` without exception.
6. Commit messages per feature: `chore(phase-2): walkthrough feature 1 complete` and `chore(phase-2): walkthrough feature 2 complete`.

**Do not touch.** Do not change architectural decisions during the walkthrough; if an architectural problem surfaces, log it and proceed with a workaround — it is a retrospective input. Do not modify the frozen component agent surface. Do not silently edit shared rules to make an issue go away — if a shared rule needs adjusting, surface it as a retrospective finding.

**Verification steps.**

1. Each feature reaches either the expected end state or a clearly documented stop with a rationale.
2. Both feature event logs are syntactically valid JSONL (`while read line; do echo "$line" | jq .; done`) and pass `scripts/validate-event.py` line by line.
3. Both walkthrough logs have concrete per-section observations, not generic prose.
4. Correlation IDs thread through: feature registry, event log, issue titles, branch names (for downstream component-agent work), commits, PRs.

**Suggested model.** For agent sessions playing the production PM role: whichever model the `agents/pm/CLAUDE.md` v1 targets for production (default: Sonnet 4.6). For the human's orchestration and note-taking session: Opus 4.7.

### Work unit 2.8 — Phase 2 retrospective

**Objective.** Triage findings from the Phase 2 walkthrough into Fix-in-Phase-2, Defer-to-Phase-3+, and (where applicable) Won't-fix-with-rationale categories. Produce the concrete fix work plan for the Phase 2 fixes. Do not execute the fixes here — each becomes its own post-retrospective WU per the WU 1.6–1.12 pattern.

**Context preamble.** Eighth Phase 2 work unit. Structurally identical to WU 1.6: the retrospective is the decision artifact; fixes land as independent post-retrospective WUs. A freeze declaration is not issued here — it is issued by the last Phase 2 WU after the fix ladder merges, analogous to WU 1.12.

**Inputs.** Both walkthrough logs from 2.7, current state of `/agents/pm/`, the three Phase 1 deferred findings (Finding 5 closed by WU 2.5, Finding 6 by WU 2.1; Finding 8 is a Phase 3+ carry independent of this retrospective).

**Acceptance criteria.**

1. `docs/walkthroughs/phase-2/retrospective.md` exists, structured like `docs/walkthroughs/phase-1/retrospective.md`: identity, objective, walkthrough outcome, triage criteria, findings table, per-finding sections, Fix-in-Phase-2 work plan, Deferred-to-Phase-3+ list with named homes, loose ends, outcome.
2. The triage criteria explicitly mirror the Phase 1 pattern: does it gate Phase 3? is there 2-feature evidence? does the cost of deferring exceed the cost of fixing now? A finding qualifies for Fix-in-Phase-2 if any of these holds.
3. The Fix-in-Phase-2 work plan names each follow-up WU (2.9, 2.10, …, 2.N-1) with its scope and a one-sentence rationale. Each fix is independently landable.
4. The deferred list records any new Phase 2 carry-items with an explicit home phase. Finding 8 from Phase 1 is also listed if still open, with its Phase 3+ home reaffirmed.
5. The Phase 2 freeze declaration is explicitly *not* recorded here — it is the scope of the last WU in the fix ladder. The retrospective ends with a pointer to that future WU.
6. Commit message: `chore(phase-2): retrospective and fix plan`.

**Do not touch.** Do not execute the fix items here — the retrospective is triage only. Do not retroactively edit Phase 1 artifacts. Do not declare the freeze.

**Verification steps.**

1. Open `docs/walkthroughs/phase-1/retrospective.md` and confirm the Phase 2 retro follows the same section structure — a reader familiar with Phase 1 should recognize the shape.
2. Confirm every Fix-in-Phase-2 finding has a named follow-up WU with scope.
3. Confirm the deferred list has explicit carry-forward homes.

**Suggested model.** Sonnet 4.6. Retrospective synthesis against a concrete log; Opus is overkill.

### Addendum — post-retrospective Phase 2 fixes (WUs 2.9–2.15)

The WU 2.8 retrospective (merged 2026-04-23) triaged 26 findings from the WU 2.7 walkthrough into 23 Fix-in-Phase-2 items and 1 Phase 3+ defer. The fixes were carried by six subsequent work units (WUs 2.9–2.14), each independently landable in any order. A seventh work unit (WU 2.15) records the freeze declaration once the fix ladder is merged.

See [`docs/walkthroughs/phase-2/retrospective.md`](walkthroughs/phase-2/retrospective.md) §"Fix-in-Phase-2 work plan" for the full per-finding rationale, and §"Phase 2 freeze declaration" for the freeze itself. Summary:

- ✅ **WU 2.9 — Event schema additions.** `feature_state_changed` added to enum; per-type payload schemas for `feature_state_changed` and `human_escalation`; PM CLAUDE.md §"Output artifacts" enumerates feature-state emission points and codifies F2.9 escalation resolution (event log authoritative, frontmatter `state` never written during escalation). Closes F1.1, F2.8, F2.9. PR #23.
- ✅ **WU 2.10 — task-decomposition skill clarifications.** Feature-scope overrides on qa_authoring cardinality; same-behavior gate on qa_execution deps (narrative-based identification); decomposition_pass counter documented as event-log-derived; depends_on prose narration in issue-drafting; orphan-check asymmetry folded into skill text. Closes F1.9+F2.1, F1.10+F2.2, F1.11, F1.12; folds F2.13. PR #24.
- ✅ **WU 2.11 — template-coverage contract + plan-review Phase B chaining.** Out-of-scope rephrased as imperative prohibition + pre-flight check on absent `required_templates` (distinct from empty `[]`); plan-review Phase B extended with unconditional template-coverage re-chain emitting `template_coverage_checked` on every success. Closes F2.3, F2.5, F2.7. PR #25.
- ✅ **WU 2.12 — plan-review skill polish.** Structural-vs-prose edit distinction clarified; stale-heading behavior documented explicitly; 5-step human-authoring sequence added. Closes F1.13, F2.12, F1.2. PR #26.
- ✅ **WU 2.13 — issue-drafting + work-unit template polish.** Optional `deliverable_repo` frontmatter field + optional `## Deliverables` section added to `shared/templates/work-unit-issue.md` (backwards-compatible per WU 2.5 precedent); Python second worked example added to issue-drafting SKILL. Closes F1.3, F1.4. PR #27.
- ✅ **WU 2.14 — Shared substrate + scripts hygiene.** `source_version` human convention promoted to `shared/rules/verify-before-report.md` §3; `validate-event.py` help text + `--stdin` alias + error on unsupported forms; zsh quoting fix in skill samples; new `validate-frontmatter.py` + `scripts/README.md`; schema provenance `$comment`s. `plan_reingested` event explicitly NOT added (WU 2.11's `template_coverage_checked` re-chain already covers Phase B audit trail). Closes F1.5+F2.6, F1.6, F1.7, F1.8, F2.4. PR #28.
- ✅ **WU 2.15 — Phase 2 freeze declaration.** Recorded in [`docs/walkthroughs/phase-2/retrospective.md`](walkthroughs/phase-2/retrospective.md) §"Phase 2 freeze declaration"; cross-referenced from [`agents/pm/CLAUDE.md`](../agents/pm/CLAUDE.md) header and [`agents/pm/version.md`](../agents/pm/version.md) subtitle. PM agent v1.6.0 is the Phase 3 baseline.

**Phase 2 frozen as of 2026-04-23.** Phase 3 (QA agent automation) can now begin from the corrected PM configuration and the documented Phase 3+ carry list (F2.10 and Phase 1 retrospective Finding 8).

---

## Phase 3 — QA agent automation

### Phase 3 objective

Plug the QA agent into the pipeline for test plan authoring, execution, and regression curation. Feature-level value — meaning a feature demonstrably exercising its acceptance criteria against the implementation — begins here, not just per-task value.

### Phase 3 known prerequisites

- Phase 2 complete: PM agent producing issues for QA task types.
- Shared templates for QA regression issues stable.
- Test plan location convention finalized (`/product/test-plans/` in the product specs repo).

### Phase 3 deliverables

- QA agent `CLAUDE.md`, skills, and rules at production quality.
- Test plan file conventions and schemas in the product specs repo.
- Execution result logging to the event log (plan is product; execution history is process).
- Regression issue creation against implementation tasks, with the spinning-per-implementation-task rule enforced.
- Phase 3 walkthrough and retrospective.

### Phase 3 acceptance criteria

- The QA agent authors test plans against feature acceptance criteria, producing files under `/product/test-plans/` that validate against the agreed schema.
- The QA agent executes plans and emits `task_completed` or regression events with structured evidence.
- On first QA execution failure, a structured regression issue is opened against the implementation task; on repeat failure, escalation to human occurs.
- QA regression curation — maintaining a growing suite of passing tests — is handled and does not grow unbounded.

### Work unit 3.1 — QA agent config v1

**Objective.** Elevate the Phase 0 v0.1.0 QA agent `CLAUDE.md` to production v1 quality, incorporating Phase 1 and Phase 2 learnings, the QA role's longitudinal cadence, and the cross-task regression semantics (Q4 of the Phase 3 ladder).

**Context preamble.** First Phase 3 work unit. The v0.1.0 config in `agents/qa/CLAUDE.md` is a Phase 0 draft — role definition, entry transitions, output artifacts, and a v0.1 verification/escalation stub are all present but unreviewed against production requirements. The QA agent differs from the component and PM agents in three ways that shape this rewrite: (a) its work is longitudinal — a feature traverses qa-authoring → qa-execution → regression → curation over multiple cycles, not one shot; (b) it fans out to three repos (test plans to specs repo, regression issues to component repos, events to orchestration repo); (c) it introduces cross-task coordination — a qa-execution failure produces follow-on work on an implementation task without violating single-owner state transitions. WU 3.1 codifies (a)–(c) so the four skill WUs 3.2–3.5 inherit a stable role surface.

**Inputs.** `agents/qa/CLAUDE.md` v0.1.0, `agents/pm/CLAUDE.md` v1.6.0 (reference for production-quality role config shape), `agents/component/CLAUDE.md` v1.5.0 (second reference for frozen role config shape), `shared/rules/role-switch-hygiene.md`, `shared/rules/escalation-protocol.md`, `shared/rules/state-vocabulary.md`, architecture §6.3 (transition ownership) and §6.4 (spinning detection / regression semantics), `docs/walkthroughs/phase-2/retrospective.md` §"Phase 2 freeze declaration" (carry-items F2.10 + P1 Finding 8).

**Acceptance criteria.**

1. `agents/qa/CLAUDE.md` rewritten to v1.0.0 quality, with: one-paragraph role definition; bullet list of every entry transition the role owns (per architecture §6.3); explicit artifact outputs across the three output surfaces; a role-specific verification clause that references the four Phase 3 skills by name (the skill names are fixed here as part of the config surface); and a role-specific escalation clause enumerating QA-relevant conditions including the qa-execution repeat-failure escalation from architecture §6.4.
2. **Cross-task regression semantics clause (Q4).** The config documents, in its own top-level section `## Cross-task regression semantics`, that on a qa-execution failure the QA agent **does not** transition the implementation task under test — it files a structured regression artifact and a NEW `implementation` task is created through the inbox (see WU 3.4 for the specific mechanism). The config states this as an invariant: QA never writes labels or state to a task it does not own, even when QA-detected failures imply follow-on implementation work.
3. **Role-switch hygiene inherited.** The config references `shared/rules/role-switch-hygiene.md` explicitly (the shared rule was added in WU 2.1 and is already load-bearing — no QA-specific override).
4. `agents/qa/rules/` populated with any role-specific rules surfaced by the design of Phase 3 skills, or left empty with `.gitkeep` + justification in the commit message. No speculative rules.
5. `agents/qa/README.md` exists, summarizing the role for a cold reader (one paragraph + pointer to `CLAUDE.md` + current version).
6. `agents/qa/version.md` bumped to `1.0.0` with a meaningful changelog entry citing this work unit, the Q4 semantics commitment, and the Phase 3 skill set the config references.
7. Commit message: `feat(qa): v1 QA agent configuration`.

**Do not touch.** Do not write the Phase 3 skills themselves (they are 3.2–3.5). Do not modify the frozen component agent surface (v1.5.0) or frozen PM agent surface (v1.6.0). Do not create skill stubs under `agents/qa/skills/` — those land in their own WUs. Do not edit `shared/templates/qa-regression-issue.md` — v0.1 is deliberate; any adjustment emerging from this config work is deferred to WU 3.4 where the regression skill defines its contract.

**Verification steps.**

1. Open `agents/qa/CLAUDE.md` and verify every architecture §6.3 transition the QA agent owns appears exactly once, with no contradictions against shared rules.
2. Confirm the `## Cross-task regression semantics` section states the invariant unambiguously — a reader who has not yet read WU 3.4 understands that QA does not flip implementation task state.
3. Run `scripts/read-agent-version.sh qa` and confirm output is `1.0.0`.
4. Confirm no shared rules were silently duplicated into the role config.

**Suggested model.** Opus 4.7. This config is re-read on every QA-agent invocation across Phase 3+.

### Work unit 3.2 — QA authoring skill + test-plan stub schema

**Objective.** Produce the skill that turns a validated feature spec into an executable test plan file under `/product/test-plans/`, paired with a stub schema defining the minimum machine-readable test plan shape — the first skill in the QA pipeline.

**Context preamble.** Second Phase 3 work unit. The QA config v1 from 3.1 references this skill as a placeholder. The skill reads a feature's product specs (acceptance criteria, OpenAPI operations if applicable), emits a test plan file under `/product/test-plans/FEAT-YYYY-NNNN.md` with a test ID for each covered behavior, and validates the file against a **stub schema** at `shared/schemas/test-plan.schema.json`. Real integration with Arazzo / OpenAPI Step and the Specfuse generator is deferred to Phase 4+ (specs-agent-driven plan authoring) and Phase 5 (generator-emitted skeletons) per right-to-left phasing. The stub is what Phase 3 can validate concretely; the `## Deferred integration` section makes the Phase 4/5 brief concrete.

**Inputs.** QA config v1 from 3.1, architecture §4.3 (test plan location), `shared/schemas/feature-frontmatter.schema.json` (acceptance-criteria fields where present), example product specs from the Phase 1/2 neutral-org repos, `shared/schemas/template-coverage.schema.json` (pattern reference for a Phase 2 stub schema).

**Acceptance criteria.**

1. `agents/qa/skills/qa-authoring/SKILL.md` v1.0 exists, describing step by step: how the agent reads the feature's acceptance criteria from the product specs repo; how it enumerates the behaviors a test plan must cover (one test per behavior by default, per the WU 2.10 same-behavior gate precedent); how it emits a plan file to `/product/test-plans/FEAT-YYYY-NNNN.md`; how it validates the file against the stub schema before reporting; and how it emits a `test_plan_authored` event on completion.
2. `shared/schemas/test-plan.schema.json` defines the stub structure: a plan has a `feature_correlation_id`, a `tests` array with per-test objects having at minimum `test_id` (stable string, used by `qa-regression` to point at the failing test), `covers` (reference to the acceptance-criteria fragment it validates), `commands` (the executable step list), and `expected` (the success predicate). Additional fields may be added additively in later phases.
3. A `## Deferred integration` section names Phase 4 (specs-agent-driven richer plans, likely Arazzo-backed) and Phase 5 (generator-emitted skeletons) as the places where the stub is extended or replaced. The section describes the expected shape of the Phase 4/5 integration in enough detail that the future WU inherits a concrete brief.
4. The `shared/schemas/event.schema.json` enum is extended additively with `test_plan_authored`. Per-type payload schema under `shared/schemas/events/test_plan_authored.schema.json` — even if minimal — because WU 2.5 established the per-type precedent.
5. A worked example in the skill: a small feature with two acceptance criteria → a test plan file with two tests covering them, validating cleanly against the stub schema.
6. Commit message: `feat(qa): qa-authoring skill v1 + test-plan stub schema`.

**Do not touch.** Do not implement qa-execution (3.3), regression (3.4), or curation (3.5). Do not reach into the Specfuse generator or Arazzo tooling — stub only. Do not emit test plans into any path other than `/product/test-plans/` — architecture §4.3 is the canonical location.

**Verification steps.**

1. Round-trip the worked example's plan file through `shared/schemas/test-plan.schema.json` using `ajv` or equivalent.
2. Confirm `test_plan_authored` events validate through `scripts/validate-event.py`.
3. Read the `## Deferred integration` section and confirm the Phase 4/5 brief is concrete enough that the Phase 4/5 author does not have to re-derive it.

**Suggested model.** Opus 4.7. The test-plan schema shape outlives the stub — precision here pays back across Phase 4+5.

### Work unit 3.3 — QA execution skill

**Objective.** Produce the skill that reads a test plan, runs the declared commands against the component repo(s) under test, and emits structured per-test events (`qa_execution_completed` on all-pass, `qa_execution_failed` with failing-test details otherwise) — the engine that turns authored plans into empirical signal.

**Context preamble.** Third Phase 3 work unit. The skill operates on a pickup cadence — a ready `qa_execution` task — but its output (failing events) triggers the WU 3.4 regression pipeline. The correctness bar is idempotence under replay: running the same plan against the same commit twice must not produce contradictory events or duplicate regression signals downstream. The skill does not build the component under test — it assumes the component agent's verification has already produced buildable artifacts. **Q6 check (Phase 1 Finding 8):** if, during this WU's authoring, the author determines that `--no-build` stales in `agents/component/skills/verification/SKILL.md` v1.1 create a risk of QA executing against stale artifacts, surface the finding as a new Phase 3 fix-ladder item (authorized carve-out from the Phase 1 freeze, analogous to WU 2.5's carve-out for Finding 5). If no risk surfaces, Finding 8 remains on the carry list for Phase 5.

**Inputs.** QA config v1 from 3.1, qa-authoring skill + test-plan schema from 3.2, `shared/schemas/event.schema.json`, `scripts/validate-event.py`, `shared/rules/verify-before-report.md`, architecture §6.4 (regression-vs-escalation rule).

**Acceptance criteria.**

1. `agents/qa/skills/qa-execution/SKILL.md` v1.0 exists describing: the pickup trigger (a `ready` qa_execution task); plan file resolution (locate the plan in the product specs repo using the feature correlation ID); per-test execution loop (run `commands`, evaluate against `expected`, record stdout/stderr/exit status); the aggregation rules (all-pass → `qa_execution_completed`; any failure → `qa_execution_failed` with a `failed_tests` array naming each `test_id` and its first-signal evidence); and the idempotence discipline (before emitting, confirm no prior completed/failed event for the same `(task_correlation_id, commit_sha)` exists — if it does, skip and report).
2. **Q6 finding check.** The WU explicitly inspects `agents/component/skills/verification/SKILL.md` v1.1 and records in the commit message whether Finding 8's `--no-build` stale-artifact risk applies to qa-execution. If it applies, the scope is documented as a follow-on Phase 3 fix WU (do not fix in 3.3 itself); if it does not, the carry decision is reaffirmed.
3. Per-type payload schemas: `shared/schemas/events/qa_execution_completed.schema.json` and `shared/schemas/events/qa_execution_failed.schema.json` define the payload contracts. The `event_type` enum is extended additively.
4. A worked example: a test plan with three tests; first execution all-pass → `qa_execution_completed` with commit SHA; second execution after a hypothetical code regression → `qa_execution_failed` with one entry in `failed_tests` naming the failing test's `test_id` and its first-signal output; third execution replayed against the same commit → no new event, skill reports idempotent-skip.
5. The skill explicitly does not file the regression issue on failure — that is WU 3.4's concern, triggered by the `qa_execution_failed` event.
6. Events validate through `scripts/validate-event.py`.
7. Commit message: `feat(qa): qa-execution skill v1 (+ Finding 8 disposition)`.

**Do not touch.** Do not file regression issues (3.4). Do not curate the regression suite (3.5). Do not modify the frozen component agent verification skill — the Q6 outcome is either "carried further" or "surfaced for a follow-on authorized WU", never silently edited here. Do not cache plan files or build artifacts — always resolve fresh from the specs repo at execution time.

**Verification steps.**

1. Walk the worked example end-to-end and confirm the event shapes validate per-type.
2. Replay the idempotence case and confirm no duplicate events.
3. Confirm the `failed_tests` array's structure is consumable by WU 3.4's regression-filing logic as-is — the skill author prototypes the shape with WU 3.4's upcoming contract in mind.
4. Re-read the Q6 disposition in the commit message and confirm it is a concrete statement, not a hedge.

**Suggested model.** Opus 4.7. Idempotence under replay plus cross-WU contract shape with 3.4 are both subtle invariants.

### Work unit 3.4 — QA regression skill + `escalation_resolved` event (closes F2.10)

**Objective.** Produce the skill that reacts to `qa_execution_failed` events by filing a structured regression artifact that spawns a new `implementation` task on the component repo under test (Q4 semantics), handles first-failure vs. repeat-failure per architecture §6.4, and introduces the `escalation_resolved` event type as the Phase 3 absorption of carry-item F2.10.

**Context preamble.** Fourth Phase 3 work unit — the contract-heaviest WU in the phase. Two contracts are established simultaneously: (a) Q4 cross-task semantics (a QA-detected failure on a `done` implementation task produces a NEW `implementation` task, not a flip of the original's state — preserving the single-owner invariant); (b) F2.10 `escalation_resolved` event, which retires the orphan inbox file from the Phase 2 walkthrough as its first application. Getting either wrong regresses Phase 2's design (Q4 breaks state ownership, F2.10 leaves inbox files orphaned indefinitely). Both land in one WU because they are cohesive — Q4 creates the occasion for escalation resolution, and F2.10 formalizes it.

**Inputs.** QA config v1 from 3.1 (esp. the `## Cross-task regression semantics` section), qa-execution skill from 3.3 (for the shape of `qa_execution_failed`), `shared/templates/qa-regression-issue.md` v0.1 (v0.2 may emerge here), `shared/rules/escalation-protocol.md`, `shared/rules/state-vocabulary.md`, architecture §6.4, `docs/walkthroughs/phase-2/retrospective.md` §"Finding F2.10" + §"Loose ends", `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md` (the orphan this WU retires).

**Acceptance criteria.**

1. `agents/qa/skills/qa-regression/SKILL.md` v1.0 exists describing: the trigger (a new `qa_execution_failed` event on any feature's event log); the first-failure path — **file a new `implementation` task via `inbox/qa-regression/<FEAT>-<TESTID>.md`** (new inbox type, convention documented in the skill) referencing the failing `test_id`, the failing execution event, the implementation task correlation ID it regresses against, and a reproduction brief; emit `qa_regression_filed`; the repeat-failure path — if an open regression-fix task for the same `(implementation_task_correlation_id, test_id)` already exists and has had a linked fix attempt (signaled by a `task_completed` event), **escalate `spinning_detected` on the original implementation task** per architecture §6.4; the resolution path — on a subsequent `qa_execution_completed` whose commit SHA post-dates an outstanding regression-fix task for the same test, emit `qa_regression_resolved` and `escalation_resolved` (if the regression had been escalated).
2. **Q4 invariant.** The skill never writes labels or state to the implementation task under test. All follow-on implementation work flows through a new task via the inbox. The skill's verification step confirms this invariant every run.
3. **F2.10 absorption.** `escalation_resolved` added to the `event.schema.json` enum. Per-type payload schema at `shared/schemas/events/escalation_resolved.schema.json` with fields linking back to the original escalation event (`resolved_escalation_event_ts`, `resolution_kind` discriminator covering at least `qa_regression_resolved` and `human_resolved`). The event is designed as substrate — the `human_resolved` variant retires the Phase 2 orphan inbox file (`FEAT-2026-0005-plan-review-cycle.md`) in this WU's commit as the first application, with the retirement itself recorded as an `escalation_resolved` entry on that feature's event log. Commit message states the F2.10 absorption explicitly.
4. Per-type payload schemas for `qa_regression_filed` and `qa_regression_resolved` land additively alongside.
5. `shared/templates/qa-regression-issue.md` bumped to v0.2 if and only if fields are required that v0.1 lacks. Version bump justified in the commit message against the Phase 3 scope (the template is not yet frozen, so adjustments here do not violate any freeze).
6. A worked example covering the full loop: qa_execution_failed → regression-fix task filed via inbox → component agent fixes → qa_execution_completed (new commit) → qa_regression_resolved + escalation_resolved emitted.
7. A second worked example covering the repeat-failure path: qa_execution_failed → regression-fix task filed → component agent's fix attempt records task_completed → re-execution fails → `spinning_detected` escalation on the original implementation task, NOT a second regression-fix task.
8. Commit message: `feat(qa): qa-regression skill v1 + escalation_resolved event (closes F2.10)`.

**Do not touch.** Do not flip labels or state on the implementation task under test (Q4 invariant). Do not modify `shared/rules/escalation-protocol.md` in ways that regress Phase 2's escalation contract — additions are additive only. Do not implement curation (3.5). Do not retroactively edit event logs older than the orphan-retirement application — the orphan is retired by emitting a new event, not by rewriting history.

**Verification steps.**

1. Walk both worked examples end-to-end and confirm every emitted event validates per-type through `scripts/validate-event.py`.
2. Confirm the orphan inbox file `FEAT-2026-0005-plan-review-cycle.md` is retired in this WU's commit with a corresponding `escalation_resolved` event appended to `events/FEAT-2026-0005.jsonl`.
3. Confirm the Q4 invariant: grep the skill for any mention of writing labels or state to the implementation task under test — there should be none.
4. Re-read `docs/walkthroughs/phase-2/retrospective.md` §"Finding F2.10" and confirm the absorbed clause addresses the failure mode as described (no machine-readable resolution signal, inbox file orphaned).

**Suggested model.** Opus 4.7 — mandatory. The Q4 invariant and the F2.10 substrate are both load-bearing across every future phase.

### Work unit 3.5 — QA curation skill

**Objective.** Produce the skill that maintains the regression suite against unbounded growth — deduplicating overlapping tests, consolidating coverage across features, retiring obsolete tests whose covered behavior has been spec-removed — emitted via a structured `regression_suite_curated` event.

**Context preamble.** Fifth Phase 3 work unit. The Phase 3 acceptance criterion "QA regression curation — maintaining a growing suite of passing tests — is handled and does not grow unbounded" is satisfiable with an explicit curation cadence: on each `qa_curation` task pickup, the skill scans the suite for dedup candidates, spec-removal orphans, and failure-clustered consolidation opportunities, and proposes structural changes the human approves in review. Unlike 3.2–3.4, this skill operates on the suite as a whole, not on a single feature — its task-correlation scope is the repo or suite directory it targets.

**Inputs.** QA config v1 from 3.1, qa-authoring skill from 3.2 (for the test-plan schema it operates over), qa-regression skill from 3.4 (for the regression-filed events whose spawned tests contribute to suite growth), architecture §4.3, examples of realistic regression suites from Phase 0/1/2 repos where available.

**Acceptance criteria.**

1. `agents/qa/skills/qa-curation/SKILL.md` v1.0 exists describing: the pickup trigger (a ready `qa_curation` task); the scan passes (dedup detection by `covers` overlap, orphan detection by spec removal, consolidation candidates by failure-pattern clustering over the event log); the proposal format (a markdown curation report attached to the task's PR, not direct destructive edits — human reviews before merge); the verification step (the curation PR's diff does not alter test plan files in ways that make any open regression-fix task unresolvable); and the `regression_suite_curated` event emitted on PR merge.
2. **Bounded-growth discipline.** The skill documents an explicit scan budget — one curation pass per `qa_curation` task pickup is not expected to traverse the entire suite if the suite exceeds a threshold (threshold TBD in this WU; propose and justify). The skill's verification confirms the task terminates in bounded time.
3. Per-type payload schema at `shared/schemas/events/regression_suite_curated.schema.json`.
4. A worked example: a suite with two overlapping tests covering the same acceptance criterion → the skill produces a consolidation PR merging them into one, emits the curated event on merge.
5. A second worked example: a suite with one orphan test whose covered criterion was removed from the spec → retirement PR, curated event, no open-regression conflict.
6. Commit message: `feat(qa): qa-curation skill v1`.

**Do not touch.** Do not destructively edit test plan files inline — all curation changes flow through a reviewable PR. Do not retire a test whose `test_id` is referenced by any open `qa_regression_filed` event that has no matching `qa_regression_resolved` — that would hide an in-flight regression. Do not modify the test-plan stub schema from 3.2 — any structural change is deferred to Phase 4+.

**Verification steps.**

1. Walk both worked examples end-to-end and confirm the curated events validate.
2. Confirm the "open regression protection" rule is exercised — attempt to retire a test with an open regression-filed event in the worked example, confirm the skill refuses.
3. Re-read the bounded-growth scan-budget justification and confirm it is defensible, not hand-waved.

**Suggested model.** Opus 4.7. The bounded-growth discipline affects every future QA pass.

### Work unit 3.6 — Phase 3 walkthrough

**Objective.** Exercise the QA agent end-to-end on two real features, validating that the Phase 3 skills 3.2–3.5 compose into a working authoring → execution → regression → curation loop. Analogous to WU 2.7.

**Context preamble.** Sixth Phase 3 work unit. This is the empirical validation of everything 3.1–3.5 produced. Like WU 2.7, it is a multi-session human-driven exercise; the prompt here is instructions to the human operator. The two-features shape is deliberately inherited from Phase 2 — one would not stress the longitudinal cadence, three would turn the walkthrough into noise. Feature 2 exercises the full regression loop, which is the highest-contract path in Phase 3.

**Inputs.** Full QA agent config and skills v1. Phase 1/2 sample component repos (`Bontyyy/orchestrator-api-sample` plus any additional repo used in Phase 2). The neutral-org product specs repo from Phase 0, extended with two features' acceptance criteria drafted by the human ahead of the walkthrough. The full set of frozen PM and component agent surfaces — Phase 3 produces QA tasks those roles consume and whose events QA reacts to.

**Acceptance criteria.**

1. **Feature 1 (happy path)** — validated spec, qa-authoring produces a test plan cleanly, qa-execution passes first-try against the merged implementation, feature reaches `done` with no regression filed. Produces `docs/walkthroughs/phase-3/feature-1-log.md`.
2. **Feature 2 (regression cycle)** — primary candidate: qa-execution fails first-try, qa-regression files a new implementation task via the inbox, component agent picks it up and fixes, re-execution passes, `qa_regression_resolved` + `escalation_resolved` events emitted, qa-curation consolidates if the regression exposed a consolidation opportunity. Backup candidate (only if regression cycle is impractical): qa-curation stress — a suite growing past threshold with dedup/orphan opportunities. Chosen at walkthrough time. Produces `docs/walkthroughs/phase-3/feature-2-log.md`.
3. Logs are honest — friction, workarounds, surprises are recorded, not sanitized.
4. Any config or skill changes prompted by the walkthrough are committed as they happen, with `agents/qa/version.md` bumps and changelog entries.
5. Every event emitted across both features validates through `scripts/validate-event.py` without exception.
6. **Cross-task-flow audit.** The walkthrough explicitly verifies that the Q4 invariant held across Feature 2 — no implementation task the QA did not own had its state or labels mutated by QA actions.
7. Commit messages per feature: `chore(phase-3): walkthrough feature 1 complete` and `chore(phase-3): walkthrough feature 2 complete`.

**Do not touch.** Do not change architectural decisions during the walkthrough; if an architectural problem surfaces, log it and proceed with a workaround — it is a retrospective input. Do not modify the frozen component or PM agent surfaces. Do not silently edit shared rules to make an issue go away — if a shared rule needs adjusting, surface it as a retrospective finding.

**Verification steps.**

1. Each feature reaches either its expected end state or a clearly documented stop with a rationale.
2. Both feature event logs are syntactically valid JSONL and pass `scripts/validate-event.py` line by line.
3. Both walkthrough logs have concrete per-section observations, not generic prose.
4. The Q4 audit in Feature 2's log is a specific enumeration, not a blanket assertion.

**Suggested model.** For agent sessions playing the production QA role: whichever model `agents/qa/CLAUDE.md` v1 targets for production (default: Sonnet 4.6). For the human's orchestration and note-taking session: Opus 4.7.

### Work unit 3.7 — Phase 3 retrospective

**Objective.** Triage findings from the Phase 3 walkthrough into Fix-in-Phase-3, Defer-to-Phase-4+, and Won't-fix-with-rationale categories. Produce the concrete fix work plan. Do not execute fixes here — each becomes its own post-retrospective WU per the WU 1.6–1.12 / 2.8 pattern.

**Context preamble.** Seventh Phase 3 work unit. Structurally identical to WU 1.6 and WU 2.8: the retrospective is the decision artifact; fixes land as independent post-retrospective WUs. A freeze declaration is not issued here — it is issued by the last Phase 3 WU after the fix ladder merges, analogous to WU 1.12 and WU 2.15.

**Inputs.** Both walkthrough logs from 3.6, current state of `/agents/qa/`, the two Phase 2+ carry-items (F2.10 closed by WU 3.4; Phase 1 Finding 8 conditional-closed or carried-further by WU 3.3 per its Q6 disposition).

**Acceptance criteria.**

1. `docs/walkthroughs/phase-3/retrospective.md` exists, structured like Phase 2's retrospective: identity, objective, walkthrough outcome, triage criteria, findings table, per-finding sections, Fix-in-Phase-3 work plan, Deferred-to-Phase-4+ list with named homes, loose ends, outcome.
2. Triage criteria mirror Phase 2's: does it gate Phase 4? is there 2-feature evidence (or a 1-feature finding elevated by cost-of-defer reasoning)? does the cost of deferring exceed the cost of fixing now? A finding qualifies for Fix-in-Phase-3 if any of these holds.
3. The Fix-in-Phase-3 work plan names each follow-up WU (3.8, 3.9, …, 3.N-1) with its scope and a one-sentence rationale. Each fix is independently landable.
4. The deferred list records any new Phase 3 carry-items with an explicit home phase. Phase 1 Finding 8 is listed either as closed-in-this-phase (via the WU 3.3 conditional absorption if triggered) or re-affirmed as Phase 4+/5 carry.
5. The Phase 3 freeze declaration is explicitly *not* recorded here — it is the scope of the last WU in the fix ladder. The retrospective ends with a pointer to that future WU.
6. Commit message: `chore(phase-3): retrospective and fix plan`.

**Do not touch.** Do not execute fix items here — the retrospective is triage only. Do not retroactively edit Phase 1 or Phase 2 artifacts. Do not declare the freeze.

**Verification steps.**

1. Open `docs/walkthroughs/phase-2/retrospective.md` and confirm Phase 3's retro follows the same section structure — a reader familiar with Phase 2 should recognize the shape.
2. Confirm every Fix-in-Phase-3 finding has a named follow-up WU with scope.
3. Confirm the deferred list has explicit carry-forward homes.

**Suggested model.** Sonnet 4.6. Retrospective synthesis against a concrete log; Opus is overkill.

---

## Phase 4 — Specs agent and chat front-end

### Phase 4 objective

Automate the conversational spec-drafting phase. This is deferred to near-last because the human is already heavily in the loop during specs, and a poor spec prompt has the lowest blast radius — mistakes here produce bad specs, which a human reads and corrects, rather than bad merged code.

### Phase 4 known prerequisites

- Phase 3 complete.
- Specfuse spec validation tooling stable and well-understood.

### Phase 4 deliverables

- Specs agent `CLAUDE.md`, skills, and rules.
- A chat-oriented interaction pattern for drafting OpenAPI / AsyncAPI / Arazzo specifications collaboratively with the human.
- Automated invocation of Specfuse validation at the `drafting → validating` transition.
- Handoff to the PM agent on successful validation.
- Phase 4 walkthrough and retrospective.

### Phase 4 acceptance criteria

- The specs agent produces valid, reviewable specs for realistic features with demonstrably less human effort than pre-Phase-4 drafting.
- Validation failures produce actionable feedback to the human.
- Handoff to the PM agent is clean: no manual state-bumping required.

*Detailed work unit prompts deferred until Phase 3 completion.*

---

## Phase 5 — Generator feedback loop automation

### Phase 5 objective

Automate the flow whereby agent-raised spec issues trigger generator template adjustments and regeneration, and migrate the override registry from an agent-consulted artifact to a generator-authoritative input per architecture §9.3's future model.

### Phase 5 known prerequisites

- Phase 4 complete.
- A meaningful history of spec issues raised by component and QA agents across Phases 1–4, to inform what the feedback loop must handle.
- Generator maintainer tooling and (optionally) a generator-maintainer agent role.

### Phase 5 deliverables

- Feedback loop: spec issues route to the generator project, trigger template work, and, on resolution, signal regeneration across affected component repos.
- Generator respects the override registry during regeneration (inversion of control from the initial model).
- Config-steward agent (the meta-agent covered in architecture §5.4) implemented and operating on the orchestration repo.
- Phase 5 walkthrough and retrospective.

### Phase 5 acceptance criteria

- A spec issue raised during implementation in Phase 1–4 that, under the initial model, required human routing, now routes automatically to the generator project and produces a template fix.
- Regeneration no longer clobbers active overrides.
- `version.md` discipline across `/agents/` and `/shared/` is reliably maintained by the config-steward agent with no manual intervention.
- Auto-merge is considered for enablement — not required, but the QA loop should be trusted enough by this point that the conversation is live.

*Detailed work unit prompts deferred until Phase 4 completion.*

---

## Executing this plan

A plan of this shape is only useful if it's executed with discipline. A few practices keep the plan honest.

**Track progress at phase granularity in the plan itself.** When a work unit completes, add a one-line status block under its heading in this document — date completed, any deviations from the acceptance criteria, the commit that ended the unit. When a phase completes, add a phase-level status entry referencing the retrospective. Do not track progress outside this document; distributing the truth across issue trackers and notes files is exactly the kind of coordination loss the orchestrator is being built to prevent, and it would be ironic to suffer from it while building it.

**Pause and update the plan when reality diverges.** If a work unit turns out to require splitting, split it in the plan before splitting it in execution. If a phase's acceptance criteria need to change based on what a prior phase taught, change them explicitly with a dated note. If a work unit becomes unnecessary, mark it skipped with a rationale rather than silently dropping it. The plan is not a prediction; it's the shared record of what we decided to do, updated as we learn.

**Escalate when you hit architectural ambiguity.** The work units are written assuming the architecture document is authoritative. If executing a work unit requires you to resolve an architectural ambiguity — not a tactical choice, but an actual design question — stop, document the ambiguity, and resolve it in the architecture document before continuing. The orchestrator's whole value proposition is traceable, intentional decision-making; retrofitting architectural decisions after the fact erodes that.

**Resist scope creep between phases.** Each phase has explicit deliverables and acceptance criteria. If a phase is going long, the right response is almost always "cut scope, finish the phase, capture the cut scope as Phase N+0.5 or as inputs to a later phase" — not "extend the phase." The right-to-left build order relies on earlier phases reaching stability; indefinite earlier-phase extensions starve the downstream.

**Keep the open-source hygiene discipline from day one.** Every commit message, every file comment, every example: written as if a stranger will read it after the migration to the public org. This is cheaper to maintain than to retrofit. Specifically: no consumer-product names, no private-org names, no internal URLs, no fixtures with sensitive data, Apache 2.0 license headers where applicable.

**Retrospectives are work units, not optional ceremony.** 0.8 and 1.6 are gated on real retrospectives. The temptation after a walkthrough is to skip forward to the next phase. Don't. The retrospective's output is what makes the next phase's work units writeable at all.

The goal at the end of Phase 5 is a system that lets a small team ship 2–3 spec-driven, cross-repo features per week with human attention concentrated at the decisions that matter. Every work unit in this plan earns its place by moving that goal closer. Cut anything that doesn't.
