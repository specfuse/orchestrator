# Phase 2 walkthrough — Retrospective (WU 2.8)

## Identity

- **Walkthrough:** Phase 2, WU 2.8 (retrospective over WU 2.7)
- **Scope:** triage of findings surfaced in Feature 1 (happy path) and Feature 2 (edge case: plan-review re-ingest stress) of WU 2.7
- **Operator:** @Bontyyy (co-piloted with Claude as Opus 4.7)
- **Date conducted:** 2026-04-23
- **Inputs:** [feature-1-log.md](feature-1-log.md), [feature-2-log.md](feature-2-log.md), [orchestrator-implementation-plan.md](../../orchestrator-implementation-plan.md) §"Phase 2", the feature registry entries for `FEAT-2026-0004` and `FEAT-2026-0005`, the JSONL event logs for both features, and the three Phase 1 deferred findings (Findings 5, 6, 8 from [phase-1/retrospective.md](../phase-1/retrospective.md)).
- **Status:** triage complete; Fix-in-Phase-2 work plan staged; items deferred to Phase 3+ tagged and cross-referenced.

## Objective

Triage the 26 findings surfaced across the two WU 2.7 features and decide, for each, whether it must be fixed before the Phase 2 PM-agent configuration freeze or can be deferred to Phase 3+. Produce a concrete work plan for the Phase 2 fixes and a documented handoff list for the deferred items so Phase 3 (QA agent automation) starts from a fully-catalogued backlog rather than a fresh discovery pass.

Per the implementation plan, WU 2.8 is the decision artifact. Execution of the Fix-in-Phase-2 items themselves is carried by subsequent Phase 2 work units (WUs 2.9–2.14), each independently landable. The Phase 2 freeze declaration is explicitly **not** recorded here — it is the scope of the final Phase 2 work unit (WU 2.15 = WU 2.N), analogous to WU 1.12.

## Walkthrough outcome

Both WU 2.7 acceptance criteria were met by the features as executed:

| Criterion | Feature | ID | Shape | Outcome |
|---|---|---|---|---|
| 1 — happy path, cross-repo, no edits during plan review, all templates present | 1 | `FEAT-2026-0004` | 5 tasks across 2 component repos (.NET + Python); 5 issues opened; T01 simulated-complete triggered T02 `task_ready` via dep-recomputation | Feature reached `in_progress`; 13 events, all validate ([PR #20](https://github.com/clabonte/orchestrator/pull/20)) |
| 2 — edge case, plan-review re-ingest stress | 2 | `FEAT-2026-0005` | 8-task graph, 6 Phase B re-ingest invocations (retarget, add-task, cycle, cycle-fix, prose-only, remove-task) with 1 correct `spec_level_blocker` escalation | Feature in `plan_review` post-edits; 4 events, all validate ([PR #21](https://github.com/clabonte/orchestrator/pull/21)) |

The v1 PM agent configuration (`agents/pm/CLAUDE.md` at 1.0.0, the five skills at 1.0, shared rules) executed correctly across both shapes. No skill needed correction mid-walkthrough to unblock a subagent; all findings are tuning opportunities rather than configuration bugs. Every event validated through `scripts/validate-event.py` on every append (17 events total across the two features). All 18 fresh Sonnet 4.6 subagent invocations (9 per feature) observed `role-switch-hygiene.md` discipline, re-reading `/shared/rules/*` + `agents/pm/CLAUDE.md` + their specific skill before acting. Phase 2's core goal — validating the v1 PM agent across pipeline-order skill invocations end-to-end with fresh-context subagents — is achieved.

## Triage criteria

Every finding was scored against three questions, mirroring Phase 1's pattern adjusted for Phase 2's evidence shape. A "yes" on any of them qualifies the finding for **Fix in Phase 2**; otherwise it is **Deferred to Phase 3+**.

1. **Does it gate Phase 3?** If the QA agent (Phase 3's deliverable) would either re-encounter the finding on its first real task or inherit a broken contract from the current Phase 2 configuration, the finding must be fixed before Phase 3 starts. The inheritance case matters: anything the QA agent would copy — event-emission patterns, skill templates, shared schemas, escalation conventions — is cheaper to fix once in Phase 2 than separately in every downstream role.

2. **Is there 2-feature evidence?** A finding surfaced in both Feature 1 and Feature 2 — or confirmed by a fresh subagent independently resolving the same ambiguity differently — is not a single-session artifact; it is a reproducible failure of manual discipline or a real ambiguity in the skill text. Two independent runs is the evidence threshold for Phase 2 (Phase 1 used three runs against three task shapes; Phase 2's two-feature shape is the analogous threshold given WU 2.7's structure).

3. **Is the cost of deferring greater than the cost of fixing now?** Some single-feature findings are cheap enough to fix (a one-sentence clarification, an additive schema enum value, a sample-command quoting fix) that deferring them manufactures friction for no saving. Applied sparingly — the default on single-feature findings is to defer unless the forward cost is obviously larger or the surface touched is already being revisited in Phase 2.

Findings that fail all three tests defer by default. The deferred list is not "won't fix" — it is "fix when the context to fix it is already open", typically during the Phase 3+ work unit that touches the same surface.

## Findings triage

Twenty-six findings total across the two feature logs. Thirteen per feature. Four cross-feature pairs confirmed: F2.1↔F1.9, F2.2↔F1.10 (extends), F2.6↔F1.5 (extends), F2.9↔F1.1 (extends). Of the 26, two are positive observations (F2.11, F2.13); the remaining 24 are triageable. Twenty-three qualify for Fix-in-Phase-2, one defers to Phase 3+.

| # | Finding | Source | Runs | Related | Gate P3? | **Decision** |
|---|---|---|---|---|---|---|
| F1.1 | `feature_state_changed` referenced in PM CLAUDE.md, absent from event schema enum | F1 Step 4 + Step 6 | 1 (extended by F2.9) | F2.9 | Yes | **Fix in Phase 2** |
| F1.2 | `required_templates` populated by human between decomposition and coverage-check | F1 interlude | 1 | — | No | **Fix in Phase 2** (doc) |
| F1.3 | `work-unit-issue.md` template is implementation-centric; QA tasks strain the shape | F1 Step 5 | 1 | — | Yes | **Fix in Phase 2** |
| F1.4 | `issue-drafting/SKILL.md` worked example is .NET-specific | F1 Step 5 | 1 | — | Yes | **Fix in Phase 2** |
| F1.5 | `source_version` convention for `source: human` events under-specified | F1 Step 4 | 1 (extended by F2.6) | F2.6 | Yes | **Fix in Phase 2** |
| F1.6 | `scripts/validate-event.py` help text trips subagents | F1 Step 2, Step 3, Step 6 | 3 (intra-F1) | — | Yes | **Fix in Phase 2** |
| F1.7 | zsh silently glob-expands `?` in unquoted `gh api` URLs | F1 Step 2 | 1 | — | Yes | **Fix in Phase 2** |
| F1.8 | No `scripts/validate-frontmatter.sh` / `requirements.txt` for YAML schema validation | F1 Step 1, Step 2 | 2 (intra-F1) | — | Yes | **Fix in Phase 2** |
| F1.9 | `task-decomposition/SKILL.md` Step 4 ambiguous on single vs. per-behavior `qa_authoring` | F1 Step 1 | 2 features | F2.1 | Yes | **Fix in Phase 2** |
| F1.10 | Step 5's cross-repo `qa_execution depends_on` rule over-constrained | F1 Step 1 | 2 features | F2.2 | Yes | **Fix in Phase 2** |
| F1.11 | `decomposition_pass` counter mechanism has no persistent carrier | F1 Step 1 | 1 | — | Yes | **Fix in Phase 2** (doc) |
| F1.12 | `depends_on` narrative convention in `§Context` prose not explicit | F1 Step 5 | 1 | — | Yes | **Fix in Phase 2** (doc) |
| F1.13 | "No edits during plan review" ambiguous on prose drafting vs. structural edits | F1 Step 3.5 | 1 | — | Yes | **Fix in Phase 2** (doc) |
| F2.1 | Fresh subagent resolved F1.9 ambiguity the other way | F2 Step 1 | — | F1.9 | Yes | **Fix in Phase 2** (merges with F1.9) |
| F2.2 | Cross-behavior `qa_execution` coupling on same repo extends F1.10 | F2 Step 1 | — | F1.10 | Yes | **Fix in Phase 2** (merges with F1.10) |
| F2.3 | template-coverage-check subagent auto-populated `required_templates` (contract violation) | F2 Step 2 | 1 | — | Yes (hard) | **Fix in Phase 2** |
| F2.4 | Schema additive history across WUs hard to trace for fresh subagent | F2 Step 3 | 1 | — | No | **Fix in Phase 2** (cheap) |
| F2.5 | Phase B retarget doesn't re-validate `required_templates` vocabulary match | F2 Edit A | 1 | — | Yes | **Fix in Phase 2** |
| F2.6 | Phase B silent-success + source_version human convention (audit trail sparseness) | F2 Edit A | — | F1.5 | Yes | **Fix in Phase 2** (merges with F1.5) |
| F2.7 | Phase B does not re-run template-coverage-check on `required_templates`/`assigned_repo` change | F2 Edit B | 1 | — | Yes (hard) | **Fix in Phase 2** |
| F2.8 | `human_escalation` payload is prose-only; no structured `cycle_members` field | F2 Edit C | 1 | — | Yes | **Fix in Phase 2** |
| F2.9 | Tension between `escalation-protocol.md` and plan-review skill on feature state on escalation | F2 Edit C | — | F1.1 | Yes | **Fix in Phase 2** (merges with F1.1) |
| F2.10 | No "escalation resolved" signal in event log; inbox file orphaned after cycle fix | F2 Edit C-fix | 1 | — | No | **Defer to Phase 3+** |
| F2.11 | Phase B stateless-by-design on prose-only edits is correct | F2 Edit D | — | — | — | Positive observation |
| F2.12 | Plan file heading lines stale after Phase B retargets | F2 Edit D | 1 | — | Yes | **Fix in Phase 2** (doc) |
| F2.13 | Orphan check robust across add/remove; asymmetry worth naming | F2 Edit E | — | — | — | Positive observation |

The per-finding sections below justify each decision. Confirmed cross-feature pairs are treated in a single section with both refs.

### Finding F1.1 + F2.9 — `feature_state_changed` event type missing and escalation-state tension

**What.** `agents/pm/CLAUDE.md` §"Output artifacts" says the PM agent emits "`feature_state_changed` on feature-level transitions" — but `shared/schemas/event.schema.json`'s `event_type` enum does not include `feature_state_changed`. Feature-level transitions (`planning → plan_review`, `plan_review → generating`, `generating → in_progress`) are observable only via the frontmatter's git history, not via the event log (F1.1). The same gap has a second face on the escalation path: `escalation-protocol.md` says escalation "flags the feature state as `blocked`", while the plan-review skill's Phase B exit criteria say the feature state remains `plan_review` on escalation. The event log carries the `spec_level_blocker` signal; the frontmatter `state` field does not (F2.9).

**Evidence.** F1 Step 4 finding (plan_approved), F1 Step 6 finding (generating → in_progress silent), F2 Edit C finding (human_escalation without state flip). The gap was observable on both the happy-path state progression and the escalation path.

**Decision.** Fix in Phase 2.

**Rationale.** Hard Phase 3 gate. The QA agent will also emit feature-level signals (regression opens, QA completion on a feature) and will inherit whatever pattern the PM agent demonstrates. Shipping a PM agent whose feature-level transitions are silent in the event log forces every downstream consumer — including the eventual merge watcher and config steward — to reconstruct feature state from git-blame on frontmatter. The fix is additive schema work: add `feature_state_changed` to the enum (with a per-type payload schema for `from_state` / `to_state` / `trigger`), and resolve the escalation tension via event-based signaling rather than state-vocabulary expansion. The plan-review skill's refusal to write to the frontmatter during escalation is the correct posture; the event log is the single authoritative carrier of the blocked signal. WU 2.9 absorbs both.

### Finding F1.2 — `required_templates` populated manually between decomposition and coverage-check

**What.** Per WU 2.2's Out-of-scope clause (repeated in WU 2.6), task-decomposition does not populate `required_templates`; the human adds it during drafting or during `plan_review` re-ingest. F1's walkthrough confirmed the happy-path pipeline therefore requires a human touch between two automated skills.

**Evidence.** F1 interlude before Step 2. Single feature observation.

**Decision.** Fix in Phase 2 (documentation clarification, no automation).

**Rationale.** The current skill design is correct for v1 (inference of required_templates from task-type × repo declaration is non-trivial and would couple task-decomposition to template-coverage assumptions prematurely). The fix is to make the human-touch step explicit in the plan-review skill's §"Two edit surfaces" and the task-decomposition skill's §Step 6, so a first-time reader of either skill sees the expected sequence without having to cross-reference two out-of-scope clauses. Absorbed into WU 2.12 (plan-review polish) since `required_templates` lives on the plan file during `plan_review`.

### Finding F1.3 — Work-unit issue template is implementation-centric

**What.** T03 (qa_authoring) and T05 (qa_curation) during issue-drafting surfaced the same structural tension: the issue's `assigned_repo` is the component repo (api-sample), but the actual deliverable — test plan file, curation record — lives in the orchestrator repo under `docs/walkthroughs/phase-2/test-plans/`. The template's `## Verification` section assumes commands run "in the `component_repo` root"; QA tasks had to annotate "commands run from the orchestrator repo root". Repeated pattern across the two QA task types, not a one-off.

**Evidence.** F1 Step 5 finding (T03 + T05).

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The QA agent's output is QA regression issues that will exercise the same template against the same split (deliverable lives elsewhere than target repo). Shipping the QA agent on an implementation-centric template forces either a new template (QA-specific, higher maintenance) or the same strain-and-annotate workaround at scale. The fix — add an optional `deliverable_repo` frontmatter field to the template and/or a canonical `## Deliverables` section naming where each file lands — is small and completes the issue-drafting skill's contract before QA inherits it. WU 2.13.

### Finding F1.4 — `issue-drafting/SKILL.md` worked example is .NET-specific

**What.** T01 on `orchestrator-persistence-sample` (Python) required active mental translation for every concrete detail — `WidgetsController.cs` → `widget_repository.py`, `dotnet test` → `pytest`, `IWidgetRepository` → `WidgetRepository` (Protocol). The example was useful for shape (evidence format, label order, event payload structure) but not for mechanics on non-.NET repos.

**Evidence.** F1 Step 5 finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The QA agent will have the same worked-example need and will mirror the PM agent's pattern; a .NET-only example compounds the translation tax across roles. The fix is either to generalize the example (language-neutral pseudocode for the mechanical parts) or to add a second worked example in a different stack — ideally Python, matching `orchestrator-persistence-sample` which is now the canonical Phase 2 Python fixture. WU 2.13.

### Finding F1.5 + F2.6 — `source_version` human convention + Phase B silent-success audit sparseness

**What.** F1.5: `event.schema.json` description says `source: human` events carry `source_version` as "commit SHA or `n/a`" but the choice between the two is not promoted to a shared rule; F1's operator picked the short SHA by local decision. F2.6: Phase B re-ingest on success writes no event — the audit trail for a human review session with many edits is the git history on two files. For a high-velocity review, re-ingest successes are under-observable. Related: both findings are about the event log's treatment of human-driven transitions.

**Evidence.** F1 Step 4 finding (plan_approved); F2 Edit A finding (silent re-ingest).

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The QA agent's event emissions will include `source: human` semantics (human-approved regression triage, for example) and will inherit whatever convention is established now. Resolving both faces of the same design gap in one WU keeps the shared rule coherent: promote the `source_version` human convention to `shared/rules/verify-before-report.md` §3, and add a `plan_reingested` event type (or extend the schema's human-emission conventions) so Phase B success is observable. The event-emission discipline extension is additive and freeze-compatible per the WU 2.5 precedent. WU 2.14.

### Finding F1.6 — `scripts/validate-event.py` help text trips subagents

**What.** Subagents looking for `--stdin`, `--event`, positional arguments, or `--file /dev/stdin` all fail; only `--file <path>` and stdin-without-flag work. Three of nine Feature 1 subagents (Step 2, Step 3, Step 6) hit the same friction.

**Evidence.** F1 Step 2, Step 3, Step 6 findings — 3-subagent recurrence within Feature 1.

**Decision.** Fix in Phase 2.

**Rationale.** 3-run evidence inside F1 alone clears the threshold. The QA agent will emit more events per feature than any other role (regression opens + closes + test-plan-authored + test-plan-executed per feature) and will copy the current invocation pattern. Low-cost fix: update `--help` output + add `--stdin` alias (or reject the ambiguous forms with a pointer to the canonical two). WU 2.14.

### Finding F1.7 — zsh glob-expansion on `?` in unquoted `gh api` URLs

**What.** Sample commands in `template-coverage-check/SKILL.md` §Step 4 of the form `gh api repos/.../contents/...?ref=main` fail under zsh (macOS default) with `no matches found` — the `?` is interpreted as a glob wildcard against the filesystem before `gh` sees it.

**Evidence.** F1 Step 2 finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate (marginal). The QA agent will also make `gh api` calls with query parameters; leaving the shell gotcha uncorrected in the canonical skill template propagates the friction to every downstream role. Trivial fix: quote the URLs in skill examples or add a `--` separator convention. WU 2.14.

### Finding F1.8 — No helper script for YAML frontmatter schema validation

**What.** Every subagent that needed to schema-validate a feature frontmatter (task-decomposition Step 7 check 1, template-coverage-check parsing required_templates, plan-review Phase B task-graph re-validation) had to stand up a venv + `pip install pyyaml jsonschema`, blocked by PEP 668 on macOS without `--break-system-packages`. `scripts/validate-event.py` exists as a ready-made tool; the parallel frontmatter-validation tool does not.

**Evidence.** F1 Step 1, Step 2 findings — recurring setup cost.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The QA agent will also validate feature frontmatter (regression task additions, test plan cross-references). Shipping a helper — `scripts/validate-frontmatter.sh` parallel to `validate-event.py`, or a documented `scripts/requirements.txt` + setup note — eliminates a recurring bootstrap cost for every downstream role. WU 2.14.

### Finding F1.9 + F2.1 — `task-decomposition/SKILL.md` ambiguity on single vs. per-behavior `qa_authoring`

**What.** The skill's Step 4 rule says "one `qa_authoring` task per implementation task that changes observable behavior". When a feature's `## Scope` explicitly constrains to "one authored test plan covering both behaviors", the rule and the feature conflict. F1's subagent honored the feature's shape (1 `qa_authoring`); F2's subagent followed the skill's strict reading (2 `qa_authoring`, one per behavior). Two fresh Sonnet 4.6 subagents, two runs, two different resolutions on analogous feature scopes.

**Evidence.** F1 Step 1 finding (1 qa_authoring); F2 Step 1 finding (2 qa_authoring). 2-feature evidence.

**Decision.** Fix in Phase 2.

**Rationale.** 2-feature evidence on fresh-context subagents confirms the ambiguity is in the skill text, not in a single session's judgment. Phase 3 gate is direct: the QA agent consumes the task graph and will produce downstream regression issues against whatever qa_authoring cardinality the PM agent settles on. Divergent cardinality across features produces inconsistent QA coverage patterns. Fix: clarify that feature `## Scope` constraints override the skill's default rule when they explicitly collapse the cardinality, and document the decision in a Step 4 §"Feature scope overrides" subsection. WU 2.10.

### Finding F1.10 + F2.2 — Cross-repo/cross-behavior `qa_execution depends_on` over-constrained

**What.** Step 5 rule 3 says `qa_execution` depends on "all implementation tasks on the same repo as itself AND the matched qa_authoring". F1 manifested this as an over-declared transitive dep (T04 → T01 across repos when T01 is mocked by the API). F2 manifested it as cross-behavior coupling on the same repo (T05 Behavior-1 QA waits for T03 Behavior-2 impl despite the behaviors being independent). Two faces of the same "whole-repo gate" reading of Step 5.

**Evidence.** F1 Step 1 finding; F2 Step 1 finding. 2-feature evidence on analogous rule applications producing different friction shapes.

**Decision.** Fix in Phase 2.

**Rationale.** 2-feature evidence. Phase 3 gate — the QA agent's execution scheduling depends directly on how deps propagate; over-constrained scheduling means QA work runs later than needed and the feedback loop widens. The fix is a tighter Step 5 rule: `qa_execution` depends on the implementation tasks **of the same behavior** (or whatever routing/capability entity the task graph uses to group), not the whole repo, when behaviors are distinguishable. Mock-based testing carves out cross-repo impl deps by the same principle. WU 2.10.

### Finding F1.11 — `decomposition_pass` counter has no persistent carrier

**What.** The task-decomposition skill says increment `decomposition_pass` on re-decomposition, but no field in the feature frontmatter records the current pass. The agent must count prior `task_graph_drafted` events in the log to determine it. Correct behavior, but not stated.

**Evidence.** F1 Step 1 finding.

**Decision.** Fix in Phase 2 (doc clarification).

**Rationale.** Phase 3 gate (marginal). The QA agent is not a direct consumer of `decomposition_pass`, but the pattern — "counter lives in event log, not frontmatter" — is the kind of convention every role will copy implicitly. Document it in the skill's Step 7 explicitly: "`decomposition_pass` is derived from the count of prior `task_graph_drafted` events for this feature at emission time; it is not persisted in the feature frontmatter." WU 2.10.

### Finding F1.12 — `depends_on` narrative convention not explicit

**What.** `issue-drafting/SKILL.md` lists the YAML frontmatter as the canonical machine-readable carrier of `depends_on` but does not say whether non-empty deps should also be narrated in `§Context` prose. All three deps-carrying tasks in F1 (T02, T04, T05) were narrated consistently by independent subagents — correct choice, but re-derived each time.

**Evidence.** F1 Step 5 finding.

**Decision.** Fix in Phase 2 (doc clarification).

**Rationale.** Phase 3 gate (marginal). The QA agent's regression issues will have their own deps (regression → impl task) and will face the same narrate-or-not question. One-line addition to the skill: "For `depends_on` non-empty, name the deps in prose in §Context." WU 2.10.

### Finding F1.13 — "No edits during plan review" ambiguous on prose drafting

**What.** The plan-review skill's §"Two edit surfaces" and WU 2.7's acceptance criterion 1 say "no edits during plan review" for the happy path. But drafting work unit prompts in the plan file is an expected human action during `plan_review` — and the criterion's language could be read to forbid it. F1 Step 3.5 exercised the distinction; a first-time reader could honestly ask whether prompt prose drafting counts as an "edit".

**Evidence.** F1 Step 3.5 finding.

**Decision.** Fix in Phase 2 (doc clarification).

**Rationale.** Phase 3 gate (marginal). The QA agent will author test plans that are also consumed during plan review; clarifying the structural-vs-prose edit distinction now in the plan-review skill prevents the same re-derivation in Phase 3. Fix: tighten the skill's §"Two edit surfaces" language to distinguish structural (YAML block, triggers re-ingest) from prose (prompt bodies, no re-ingest). WU 2.12.

### Finding F2.3 — template-coverage-check subagent auto-populated `required_templates`

**What.** The template-coverage-check skill explicitly scopes out populating `required_templates` ("the task-decomposition skill (WU 2.2) does not set this field at v1. The human adds it during drafting or during `plan_review` re-ingest"). In F2, the Sonnet 4.6 subagent found `required_templates` absent and materialized the field itself based on task-routing heuristics rather than escalating or failing. Well-meaning helpfulness violating the explicit contract.

**Evidence.** F2 Step 2 finding. First observation (F1 had it populated by the human before invocation, so the subagent never encountered an empty field).

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate (hard). Skill contracts need to be sticky against a downstream Sonnet 4.6 session's helpfulness bias, or every skill's Out-of-scope clause is advisory rather than load-bearing. The QA agent's skills will have their own Out-of-scope clauses (regression scoping, test plan generation limits) that will face the same pressure. The fix is mechanical: add a pre-flight check at the top of the skill that explicitly errors out if `required_templates` is absent on any task (rather than silently filling it), and rephrase the Out-of-scope clause as an imperative ("DO NOT populate this field even if absent; escalate `spec_level_blocker` with a pointer to the plan-review skill as the authoring surface"). WU 2.11.

### Finding F2.4 — Schema additive history hard to trace

**What.** F2's Phase A subagent reported that the feature-frontmatter schema "does not declare `required_templates` as an allowed field on task objects" — incorrect (WU 2.6 added it). No harm done because the subagent still copied the field verbatim, but the misread signals that even the current schema (plus Phase 2 additive history) is hard to reconstruct for a fresh session.

**Evidence.** F2 Step 3 finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate (marginal). Cheap to fix: a top-of-file comment in the schema (and in `event.schema.json`) naming which fields/enum values were added in which WU. The same hygiene applied in Phase 1 to the event schema's `source` convention (WU 1.11); extending it to Phase 2's additions keeps the schema self-documenting. WU 2.14.

### Finding F2.5 — Phase B retarget doesn't re-validate `required_templates` vocabulary

**What.** Edit A retargeted T03 from `api-sample` to `persistence-sample` with both `assigned_repo` and `required_templates` updated in the plan file's YAML block. Phase B re-ingest passed all five structural checks but did not re-run template-coverage-check to verify the new tokens match the new repo's declared vocabulary. If the human had retargeted `assigned_repo` but not updated `required_templates`, Phase B would have accepted the now-mismatched tokens.

**Evidence.** F2 Edit A finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The same retarget-without-re-validation gap would apply to QA tasks during a plan review revision. Addressed jointly with F2.7 (Phase B template-coverage chaining). WU 2.11.

### Finding F2.7 — Phase B does not re-run template-coverage-check on graph changes

**What.** Edit B added T09 with `required_templates: [migration]`; Phase B accepted it structurally without re-running coverage-check. The `migration` token happened to be in `persistence-sample`'s declaration, so no actual gap manifested — but Phase B didn't know, didn't check, didn't warn. If T09 had carried an undeclared token, the gap would surface only at generation time.

**Evidence.** F2 Edit B finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate (hard). This is the most important F2 finding: the plan-review skill's Phase B currently treats coverage as a one-shot concern (Phase A time), but task-graph changes during `plan_review` can invalidate the prior coverage result. Either Phase B chains to template-coverage-check when `required_templates` or `assigned_repo` changes (preferred: deterministic), or Phase B emits a `coverage_stale` warning the human must act on (fallback: less safe). The QA agent will add tasks during plan review revisions and inherit whichever posture Phase 2 establishes. WU 2.11, jointly with F2.3 and F2.5.

### Finding F2.8 — `human_escalation` payload is prose-only

**What.** Edit C's cycle-detection escalation emitted a `human_escalation` event whose `payload.summary` is a prose string describing the cycle. No structured `cycle_members: [T01, T02]` field. A downstream tool (merge watcher, audit query, dashboard) would have to parse prose.

**Evidence.** F2 Edit C finding.

**Decision.** Fix in Phase 2.

**Rationale.** Phase 3 gate. The QA agent's escalations (failed regression auth, spinning-per-implementation-task) will also be `human_escalation` events with structurally distinct payloads. Establishing a per-type payload schema for `human_escalation` now — with a discriminator field (`reason`) and per-reason payload shapes — mirrors the per-type event payload work begun in WU 2.5 and completed in WU 2.6 for other event types, and sets the pattern before QA inherits it. Absorbed into WU 2.9's schema additions.

### Finding F2.10 — No "escalation resolved" signal

**What.** Edit C-fix removed the cycle; Phase B completed silently. The `human_escalation` event from Edit C remains the last non-silent event; a subsequent reader of the log sees "escalation raised, silence, silence…" with no machine-readable indication the blocker was resolved. The inbox file `FEAT-2026-0005-plan-review-cycle.md` remains orphaned; the operator must archive it manually.

**Evidence.** F2 Edit C-fix finding.

**Decision.** Defer to Phase 3+.

**Rationale.** No 2-feature evidence (F1 had no escalations). No hard Phase 3 gate — the QA agent will have its own escalation-resolved concerns (regression fixed, spinning cleared) and this is exactly the class of problem that benefits from being solved once alongside QA's needs rather than in isolation. The deferred home is Phase 3's QA agent work: when QA introduces regression escalations and their resolution semantics, the `escalation_resolved` event type (or equivalent) lands in the same WU that needs it. In the meantime, the inbox file orphaning remains a known walkthrough artifact (see Loose ends).

### Finding F2.12 — Plan file headings stale after Phase B retargets

**What.** After Edit A retargeted T03 from `api-sample` to `persistence-sample`, the plan file's `## Task T03 — implementation, Bontyyy/orchestrator-api-sample` heading remained stale — the YAML block updated, the heading didn't. The skill says heading lines are regenerated "on every round-trip", but "round-trip" is ambiguous (Phase A only? Phase B too?).

**Evidence.** F2 Edit D finding.

**Decision.** Fix in Phase 2 (doc clarification).

**Rationale.** Phase 3 gate (marginal). QA-authored plan files will have analogous heading-vs-YAML drift concerns. Cheap fix: clarify the skill to say explicitly that Phase B leaves the plan file untouched (no heading regeneration), so stale headings may persist between Phase A emissions, and headings are therefore informational-not-canonical (YAML is canonical). Alternative — having Phase B regenerate headings — is rejected because it would violate the Phase B "don't write to the plan file" invariant that keeps re-ingest stateless. WU 2.12.

### Positive observations (F1 + F2)

Six positive observations recorded alongside findings, none requiring fixes:

- **Worked example in dep-recomputation SKILL.md matched the real T04-sees-T02-ready-not-done scenario exactly** (F1 Step 6). Investment in writing the worked example paid off; pattern to repeat for Phase 3 QA skill authoring.
- **Per-type payload schema validation works transparently** for `template_coverage_checked` via the WU 2.5 + WU 2.6 combination. Additive extension worked as intended.
- **`role-switch-hygiene.md` discipline held** across all 18 subagent invocations; no rule missed in practice. Cost is real (~25 files re-read per invocation) but the discipline is cheap insurance.
- **Single-writer invariant on `pending → ready` with distinct `trigger` tags** (`no_dep_creation` vs. `task_completed:TNN`) made the provenance of every flip legible in the event log.
- **Phase B stateless-by-design on prose-only edits** (F2.11) — the full read-parse-validate cycle on an edit with no YAML change is not wasteful; a diff-detect shortcut would introduce new failure modes (stale hashes, etc.).
- **Orphan check robust across add/remove directions** (F2.13) — failure shapes asymmetric but the same check catches both. Worth naming in skill text for completeness (small clarification folded into WU 2.10).

## Fix-in-Phase-2 work plan

Twenty-three findings qualify for fix in Phase 2, grouped into six cohesive follow-up WUs by the surface they touch. Each WU is independently landable in any order; sequencing below is suggested by cohesion, not dependency.

### WU 2.9 — Event schema additions: `feature_state_changed` and `human_escalation` per-type payload

**Scope.** Add `feature_state_changed` to the `event.schema.json` enum (additive, freeze-compatible). Author the per-type payload schema under `shared/schemas/events/feature_state_changed.schema.json` with `from_state` / `to_state` / `trigger` fields. Author the per-type payload schema for `human_escalation` with a `reason` discriminator and per-reason structured fields (starting with `cycle_members` for `spec_level_blocker` on dependency cycles). Update `agents/pm/CLAUDE.md` to name the new event emission points (`planning → plan_review`, `plan_review → generating`, `generating → in_progress`, `* → blocked via event not state`). Resolve the F2.9 tension by codifying: the event log is the authoritative carrier of escalation state; the feature frontmatter's `state` field is never written during escalation.

**Findings absorbed.** F1.1, F2.8, F2.9.

**Rationale.** Cohesive schema/event surface; all three findings touch the same files (`event.schema.json` + `shared/schemas/events/`) and the same design question (feature-level and escalation transitions in the event log vs. frontmatter). Handling them together prevents three separate commits churning the same files.

### WU 2.10 — task-decomposition skill clarifications

**Scope.** Clarify Step 4 rule on `qa_authoring` cardinality: feature `## Scope` constraints override the default per-behavior rule when explicitly collapsing the count. Clarify Step 5 rule 3 on `qa_execution depends_on`: same-behavior gate rather than whole-repo gate; mock-based testing carves out cross-repo impl deps. Document `decomposition_pass` counter mechanism as event-log-derived. Add a one-line clause to `issue-drafting/SKILL.md` requiring non-empty `depends_on` to be narrated in `§Context` prose. Fold F2.13's orphan-check asymmetry observation into the skill text.

**Findings absorbed.** F1.9 + F2.1, F1.10 + F2.2, F1.11, F1.12.

**Rationale.** All findings are skill-text clarifications on the task-decomposition + issue-drafting surfaces. Four findings, one cohesive WU: skill-editing friction is front-loaded in the review.

### WU 2.11 — template-coverage skill contract hardening + Phase B chaining

**Scope.** Add a pre-flight check to `template-coverage-check/SKILL.md` that errors out if `required_templates` is absent on any task (rather than filling). Rephrase the Out-of-scope clause as an imperative ("DO NOT populate; escalate `spec_level_blocker`"). Extend the plan-review skill's Phase B to re-run template-coverage-check when `required_templates` or `assigned_repo` changes on any task, emitting a `template_coverage_checked` event with the updated scope.

**Findings absorbed.** F2.3, F2.5, F2.7.

**Rationale.** All three findings touch the template-coverage + Phase B integration; the skill contract hardening and the Phase B chaining are complementary — contract says "don't populate if absent", Phase B says "re-validate if changed". Fixing them in the same WU avoids a partial solution where F2.3 lands but F2.7 still allows the same vocabulary-drift gap.

### WU 2.12 — plan-review skill polish

**Scope.** Clarify the skill's §"Two edit surfaces" on structural-vs-prose edits (YAML block triggers re-ingest, prose drafting does not). Document the stale-heading behavior explicitly ("Phase B leaves the plan file untouched; headings are regenerated only on Phase A emission; headings are informational, YAML is canonical"). Make the `required_templates` human-touch step explicit in the skill's Phase A emission prose so a first-time reader sees the expected sequence.

**Findings absorbed.** F1.13, F2.12, F1.2.

**Rationale.** All three findings are plan-review skill clarifications, same file (`agents/pm/skills/plan-review/SKILL.md`). Cohesive edit, single PR review surface.

### WU 2.13 — Issue-drafting skill + work-unit template polish

**Scope.** Add an optional `deliverable_repo` frontmatter field to `shared/templates/work-unit-issue.md` (and document it). Add a canonical `## Deliverables` section template that QA tasks can use when the deliverable lives outside `component_repo`. Either generalize the `issue-drafting/SKILL.md` worked example to language-neutral pseudocode for the mechanical parts, or add a second Python worked example against `orchestrator-persistence-sample`.

**Findings absorbed.** F1.3, F1.4.

**Rationale.** Both findings touch the issue-drafting + work-unit-issue template surface. The Phase 3 QA agent will inherit both the template and the skill's worked-example pattern; polishing them together before QA starts is the cheapest time to do so.

### WU 2.14 — Shared substrate + scripts hygiene

**Scope.** Promote the `source_version` human-event convention (commit SHA vs. `n/a`) to `shared/rules/verify-before-report.md` §3. Add a `plan_reingested` event type (or equivalent) so Phase B successes are observable in the event log. Update `scripts/validate-event.py --help` output; add a `--stdin` alias or reword to eliminate the `--event` / `--file /dev/stdin` trap. Document zsh quoting in canonical skill sample commands (or switch to `--`-separated invocations). Ship `scripts/validate-frontmatter.sh` + `scripts/requirements.txt` for YAML schema validation, parallel to the existing `validate-event.py`. Add top-of-file provenance comments to the schemas naming which WU introduced which field/enum value.

**Findings absorbed.** F1.5 + F2.6, F1.6, F1.7, F1.8, F2.4.

**Rationale.** All five findings touch cross-cutting substrate (shared rules, scripts/, schema headers, skill examples) rather than a single skill. Absorbing them in a single WU concentrates the shared-substrate churn in one review pass and avoids five separate freeze-adjacent commits. Treat this as the heaviest of the six fix WUs; its surface overlaps partially with the Phase 1 frozen substrate (event schema + shared rules) — all extensions are additive and governed by the WU 2.5 precedent.

### WU 2.15 (= WU 2.N) — Phase 2 freeze declaration

**Scope.** Analogous to WU 1.12. After WUs 2.9–2.14 have all merged, record the Phase 2 freeze in `docs/walkthroughs/phase-2/retrospective.md` §"Phase 2 freeze declaration" (canonical source), with pointer-only additions in the plan doc and PM-role metadata. Enumerate the frozen surface (PM agent v1.x.0 + five skills at 1.x + `shared/schemas/events/*` + extended `shared/rules/verify-before-report.md` + new scripts) and the explicit carve-outs (QA / specs / config-steward / merge-watcher configs remain unfrozen; Phase 3+ deferred items carry-forward).

**Findings absorbed.** — (structural; freeze declaration, not a fix).

**Rationale.** This retrospective explicitly does not declare the freeze; the declaration is issued by the last WU after the fix ladder has merged, so the freeze statement can enumerate the exact final versions.

## Deferred to Phase 3+

Two items defer. Each is tagged with its home phase.

- **F2.10 — No "escalation resolved" signal / inbox file orphaning.** Carry into Phase 3's QA agent work. The QA loop introduces regression escalations and their resolution semantics; adding an `escalation_resolved` event type (or equivalent) lands in the Phase 3 WU that needs it, not in isolation. Until then, the inbox file at `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md` remains as a walkthrough artifact (see Loose ends).

- **Finding 8 Phase 1 — Coverage-gate rebuild mandate before `--no-build`.** Still open from the Phase 1 retrospective. Out of Phase 2 scope per `phase2_ladder.md` Q4 (component-agent-specific, touching `agents/component/skills/verification/SKILL.md` would violate the Phase 1 freeze without architectural justification). Re-affirmed as Phase 3+ carry — appropriate home is the next component-agent-surface WU, which is likely Phase 5's generator-feedback work or any Phase 3+ WU that revisits `verification/SKILL.md` for QA integration.

Deferred items are not closed; they are scheduled. The forward work units that touch the relevant surfaces should consult this list at their start and absorb the applicable items.

## Loose ends

One loose end from the Feature 2 walkthrough, deliberately preserved rather than closed in this retrospective:

- **`inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md`** remains in place. It was the escalation artifact from Edit C (dependency cycle); Edit C-fix resolved the cycle but the inbox file was not archived — deliberately, per F2 log's explicit framing of this as a demonstration of the F2.10 gap. Recommendation: leave as-is, since archiving it now would remove the demonstration before F2.10's Phase 3+ fix lands. The file carries a self-describing top-line comment (or should, if it does not already); the Phase 3+ WU that introduces the `escalation_resolved` signal should retire this walkthrough artifact as its first application.

No other outstanding items from WU 2.7.

## Outcome

WU 2.8 concludes Phase 2's decision work. The walkthrough validated the v1 PM agent across the two feature shapes the plan called for (happy path + edge case); the retrospective sorted the resulting 26 findings into 23 Phase 2 fixes and 1 Phase 3+ defer (plus 2 positive observations and 1 Phase 1 carry-item re-affirmed), with explicit rationales and a concrete work plan. Phase 2 is ready to freeze once the six Fix-in-Phase-2 items (WUs 2.9–2.14) ship; Phase 3 (QA agent automation) starts from the corrected configuration and the documented deferred list rather than from a cold re-discovery pass.

The Phase 2 freeze declaration is **not** recorded here. It will be issued by **WU 2.15 (= WU 2.N)**, analogous to WU 1.12, after the fix ladder merges. That WU will enumerate the frozen PM-agent surface and carry the list of deferred items into Phase 3's inputs.
