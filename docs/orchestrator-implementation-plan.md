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

### Addendum — post-retrospective Phase 1 fixes (WUs 1.7–1.11)

The WU 1.6 retrospective (merged 2026-04-22) deviated from this plan's original framing of WU 1.6 as both triage and fix-closure: the retrospective was scoped to triage alone, and the five "Fix in Phase 1" findings it surfaced are carried by five subsequent work units, any of which can be landed independently in any order before the Phase 1 freeze declared in WU 1.6 acceptance criterion #4.

See [`docs/walkthroughs/phase-1/retrospective.md`](walkthroughs/phase-1/retrospective.md) §"Fix-in-Phase-1 work plan" for the full per-finding rationale. Summary:

- **WU 1.7 — Event schema validation harness (Finding 1).** Ship `scripts/validate-event.py` (Draft 2020-12 validator against `shared/schemas/event.schema.json`) and tighten `shared/rules/verify-before-report.md` §3 plus the three component skills to require validator exit `0` before any `events/*.jsonl` append.
- **WU 1.8 — `source_version` runtime read (Finding 2).** Establish a shared convention (documented discipline, or a small helper script) that every event's `source_version` is read from `agents/<role>/version.md` at emission time, not eye-cached.
- **WU 1.9 — PM issue-drafting "verify against repo" requirement (Finding 3).** Add a specification note, under `/agents/pm/` or in a shared rule, that the PM agent's issue-drafting skill (Phase 2) must re-verify every claim about target-repo state against the repo at draft time and log the verification step in the drafting transcript.
- **WU 1.10 — Spec-issue routing for specs-less features (Finding 4).** Amend `agents/component/skills/escalation/SKILL.md` §2 (or the features registry README) so that features without a product specs repo route spec issues to the orchestrator repository.
- **WU 1.11 — `source: component:<name>` convention (Finding 7).** Clarify in `shared/schemas/event.schema.json` description fields (or a shared rule) that `<name>` is the bare component repo name, no owner prefix.

Phase 2 (PM agent automation) begins only after all five have landed and the Phase 1 freeze declaration of WU 1.6 acceptance criterion #4 is recorded.

---

## Phase 2 — PM agent automation

### Phase 2 objective

Automate task-graph generation and GitHub issue creation from an approved feature spec. The specs phase remains manual (the human drafts specs with chat-based Claude assistance). Once a feature spec is validated, the PM agent produces the task graph, collaborates with the human on work unit prompts, and opens issues once the plan is approved. Dependency recomputation on task completion is automated. The PM agent also performs template-coverage checks against the generator during planning.

### Phase 2 known prerequisites

- Phase 1 complete and component agent config frozen.
- Work unit issue body template at v1 (locked contract).
- Shared schemas for feature frontmatter, event log, and labels stable.
- Access to (and a protocol for querying) the Specfuse generator for template coverage checks.

### Phase 2 deliverables

- PM agent `CLAUDE.md`, skills, and rules at production quality.
- Plan-review UX: a diffable, editable markdown representation of the task graph that the human reviews and modifies before approval.
- Dependency recomputation logic — the PM agent listens for `task_completed` events and flips newly-unblocked tasks from `pending` to `ready`, updating the corresponding GitHub issue labels.
- Template coverage query integration with the generator.
- A Phase 2 walkthrough exercising the full specs-to-issues pipeline on a real feature.
- Phase 2 retrospective.

### Phase 2 acceptance criteria

- The PM agent, given a validated feature spec, produces a task graph that correctly identifies implementation and QA tasks, their dependencies, and their target component repos.
- The human can edit the task graph as a file (dependencies, prompts, autonomy overrides) and the PM agent re-ingests the edit as the new source of truth.
- Upon approval, the PM agent opens conforming GitHub issues in the correct repos, each with a work-unit-issue-template-compliant body.
- When a task reaches `done`, the PM agent recomputes dependencies and flips ready-tasks correctly, without duplicate issue creation.
- Template coverage gaps are identified at planning time, not discovered mid-implementation.

*Detailed work unit prompts deferred until Phase 1 completion, as they depend on lessons learned from running the component agent against real tasks. Key design decisions that Phase 1 will inform: the exact format of the task graph markdown; how the PM agent discovers the target component repo for each task; how the PM agent talks to the generator.*

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

*Detailed work unit prompts deferred until Phase 2 completion.*

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
