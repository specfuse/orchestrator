# Phase 2 walkthrough — Feature 1 log (happy path)

## Identity

- **Walkthrough:** Phase 2, WU 2.7
- **Feature:** `FEAT-2026-0004` — widget quantity-filtered listing (cross-repo)
- **Shape chosen:** happy path (matches acceptance criterion 1 of WU 2.7 — two component repos, one implementation task per repo, one `qa_authoring`, one `qa_execution`, no edits during plan review, all templates present)
- **Started:** 2026-04-22
- **Operator:** @Bontyyy (human, driving the walkthrough)
- **Orchestration model:** Opus 4.7 (this session — note-taking, commits, subagent invocation)
- **PM-agent model:** Sonnet 4.6 (instantiated per skill invocation via subagent)
- **Component repos:**
  - [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
  - [Bontyyy/orchestrator-persistence-sample](https://github.com/Bontyyy/orchestrator-persistence-sample) — Python (stood up for this walkthrough)
- **PM agent version at execution:** 1.0.0
- **Status:** in progress

## Pre-walkthrough setup

Two setup actions performed before any PM-agent skill ran, both logged for the WU 2.7 retrospective as input on "what does onboarding a new sample repo cost":

### Setup 1 — Stand up the 2nd sample repo

`Bontyyy/orchestrator-persistence-sample` created, Python-stack, minimal persistence skeleton:
- Domain object (`Widget`), repository Protocol, in-memory adapter.
- 5 pytest-asyncio tests, 100% coverage.
- `.specfuse/verification.yml` — six gates wired (tests, coverage ≥ 0.90, mypy-strict as "compiler_warnings", ruff lint, pip-audit, `python -m build`).
- `.specfuse/templates.yaml` — declares `[persistence-port, persistence-adapter, test-plan, migration]`.
- `.github/workflows/ci.yml` mirrors the six gates.
- 15 orchestrator labels provisioned via `gh label create`.
- All six gates passed locally on the initial commit before push.

### Setup 2 — `.specfuse/templates.yaml` on orchestrator-api-sample

The 1st sample repo was bootstrapped before WU 2.6 introduced the `templates.yaml` convention; it had no declaration. PR [Bontyyy/orchestrator-api-sample#8](https://github.com/Bontyyy/orchestrator-api-sample/pull/8) added `schema_version: 1` + `provided_templates: [api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]` and merged cleanly.

### Feature drafts

`features/FEAT-2026-0004.md` drafted with `state: planning`, `task_graph: []`, two `involved_repos`, five-behavior-minus-three-redundant narrative mapping capabilities to repos via the `## Task routing` section the task-decomposition skill consumes (§Step 3 rule 2 for multi-repo features).

## Skill invocations

Each subsection below is one invocation of one PM-agent skill, executed by a Sonnet 4.6 subagent with a fresh context (re-reading `/shared/rules/*`, `agents/pm/CLAUDE.md`, and the specific skill per `role-switch-hygiene.md`). Observations, outputs, and any friction are recorded per invocation.

### Step 1 — task-decomposition skill

- **Invoked by:** orchestration session (Opus 4.7, this session) via `Agent` subagent, `model=sonnet`. Fresh context; subagent re-read `/shared/rules/*`, `agents/pm/CLAUDE.md`, and `agents/pm/skills/task-decomposition/SKILL.md` per `role-switch-hygiene.md`.
- **Input:** `features/FEAT-2026-0004.md` (state=`planning`, `task_graph: []`, two `involved_repos`, `## Task routing` section mapping Behavior 1 → persistence-sample, Behavior 2 → api-sample).
- **Capabilities derived (Step 2):** 2 capabilities, one per `### Behavior N` heading, per the "feature narrative without a formal spec" rule.

#### Task graph produced

| ID | Type | Repo | `depends_on` | Autonomy |
|---|---|---|---|---|
| T01 | `implementation` | `Bontyyy/orchestrator-persistence-sample` | `[]` | (inherit `review`) |
| T02 | `implementation` | `Bontyyy/orchestrator-api-sample` | `[T01]` | (inherit `review`) |
| T03 | `qa_authoring` | `Bontyyy/orchestrator-api-sample` | `[]` | (inherit `review`) |
| T04 | `qa_execution` | `Bontyyy/orchestrator-api-sample` | `[T01, T02, T03]` | (inherit `review` — override rule 1 not triggered because `autonomy_default` is `review`, not `auto`) |
| T05 | `qa_curation` | `Bontyyy/orchestrator-api-sample` | `[T04]` | (inherit `review`) |

Shape matches the worked example in the skill, modulo: T01 is on the persistence repo (Python) rather than a `clabonte/persistence-sample` fiction.

#### Validation evidence (Step 7)

1. **Schema round-trip** (`feature-frontmatter.schema.json` via `jsonschema.Draft202012Validator`) → **PASSED**.
2. **Cycle check** (Kahn's topological sort) → order `T01 → T03 → T02 → T04 → T05`; no back-edges → **PASSED**.
3. **Orphan check** → `depends_on` refs `{T01, T02, T03, T04}` ⊆ task IDs `{T01..T05}` → **PASSED**.
4. **Assigned-repo check** → all 5 assigned to a repo in `involved_repos` → **PASSED**.
5. **QA pairing check** → T03 ↔ T04 on api-sample; T01 (persistence) has no paired QA, per "internal refactor / no observable behavior delta" branch of Step 4 → **PASSED**.

#### Emission

- `source_version` read via `scripts/read-agent-version.sh pm` at emission: **`1.0.0`**.
- Event (written to `/events/FEAT-2026-0004.jsonl`, verified via `scripts/validate-event.py --file …`, exit **0**):

```json
{"timestamp":"2026-04-22T19:48:29Z","correlation_id":"FEAT-2026-0004","event_type":"task_graph_drafted","source":"pm","source_version":"1.0.0","payload":{"task_count":5,"involved_repos":["Bontyyy/orchestrator-api-sample","Bontyyy/orchestrator-persistence-sample"],"decomposition_pass":1}}
```

#### Friction surfaced (honest, unsanitized — subagent-reported)

1. **No `pyyaml` or helper script for frontmatter schema validation.** Step 7 check 1 requires parsing YAML frontmatter to feed the schema validator. System Python on macOS lacks `pyyaml`; the subagent created a venv to proceed. `scripts/validate-event.py` exists as a ready-made tool for event validation; the parallel `scripts/validate-frontmatter.sh` (or equivalent) does not. The skill text implies the check is trivial; in practice it requires an ambient YAML toolchain that isn't guaranteed. **Retrospective input for WU 2.8** — either ship a helper script or drop `pyyaml` into a `scripts/requirements.txt`.

2. **T04 (qa_execution, api-sample) `depends_on` includes T01 (persistence-sample) despite API mocking the persistence port.** The skill's Step 5 rule 3 is literal: "qa_execution depends on all implementation tasks on the same repo as itself AND the matched qa_authoring". T01 is on a different repo, so the rule as written does not require the dep. But T04 has a cross-repo dep on T01 anyway because Step 5 rule 1 (implementation→implementation capability chain) put T02 → T01, and transitively T04 → T02 → T01 is inherent. The subagent added T01 explicitly to T04's `depends_on`; strictly-speaking redundant (transitive deps don't need to be listed), but not wrong. Worth flagging: the skill does not state whether transitive deps should be elided or declared explicitly. **Retrospective input.**

3. **Single `qa_authoring` task for a multi-repo feature vs. per-implementation rule.** The skill says "one `qa_authoring` task per implementation task that changes observable behavior." The spec's `## Scope` says "one authored test plan covering both behaviors". A strict skill reading would produce 2 qa_authoring tasks (one per impl); the feature's explicit scope constraint collapses to 1. The subagent honored the feature's shape. **Ambiguity in the skill — retrospective input.** Either the skill should say "feature scope overrides the default" explicitly, or the scope constraint should not be accepted.

4. **`decomposition_pass` counter mechanism is implicit.** The skill says increment on re-decomposition, but no field in the feature frontmatter records the current pass. The agent must count prior `task_graph_drafted` events in the log to determine it. Correct behavior, but not stated. **Minor — retrospective input.**

5. **`never-touch.md` + unauthorized-transition checks pass.** `/features/FEAT-2026-0004.md` (frontmatter-only) and `/events/FEAT-2026-0004.jsonl` (append) are both authorized surfaces. State stays `planning`. No violation.

#### Outcome

Skill completed cleanly on cycle 1. Task graph is in the feature frontmatter; `task_graph_drafted` is in the event log and validates against the schema. Feature stays in `planning`. Next skill: template-coverage-check.

---

### Interlude — human populates `required_templates`

Per the task-decomposition skill's Step 6 scope note and the template-coverage-check skill's Out-of-scope #3 ("populating `required_templates` on task graph entries — the task-decomposition skill (WU 2.2) does not set this field at v1. The human adds it during drafting or during `plan_review` re-ingest"), the field was NOT populated by the decomposition skill. To give template-coverage-check a real demand to work against (otherwise the check passes trivially with an empty demand and we don't test anything), the human operator (this session) populated `required_templates` per task via direct frontmatter edit before invoking template-coverage-check:

| Task | `required_templates` |
|---|---|
| T01 (impl, persistence) | `[persistence-port, persistence-adapter]` |
| T02 (impl, api) | `[api-controller, api-request-validator]` |
| T03 (qa_authoring, api) | `[test-plan]` |
| T04 (qa_execution) | `[]` (skill convention: execution doesn't generate code via template) |
| T05 (qa_curation) | `[]` (same) |

Frontmatter re-validated against the schema after the edit.

**Retrospective input:** the split — decomposition does not populate `required_templates`, but template-coverage-check requires it — means any realistic happy-path pipeline needs a human touch between the two skills. Flagging whether this should be automated (decomposition infers conservative required_templates from task type × repo declaration) or accepted as a deliberate human-in-the-loop step. The current skill Out-of-scope clause chose the latter; the walkthrough confirms it works but costs a step.

### Step 2 — template-coverage-check skill

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context.
- **Input:** `features/FEAT-2026-0004.md` with task graph + `required_templates` populated.
- **Declarations fetched live** (`gh api repos/<owner>/<repo>/contents/.specfuse/templates.yaml?ref=main`):
  - `Bontyyy/orchestrator-api-sample`: `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`, `schema_version: 1`, schema-valid.
  - `Bontyyy/orchestrator-persistence-sample`: `[persistence-port, persistence-adapter, test-plan, migration]`, `schema_version: 1`, schema-valid.

#### Cross-reference result

| Task | Token | Match |
|---|---|---|
| T01 | `persistence-port` | ✓ |
| T01 | `persistence-adapter` | ✓ |
| T02 | `api-controller` | ✓ |
| T02 | `api-request-validator` | ✓ |
| T03 | `test-plan` | ✓ |

Zero gaps. Success path.

#### Emission

Event appended, validator exit **0** (now 2 events in the log, both validate top-level + per-type where applicable):

```json
{"timestamp": "2026-04-22T19:55:27Z", "correlation_id": "FEAT-2026-0004", "event_type": "template_coverage_checked", "source": "pm", "source_version": "1.0.0", "payload": {"involved_repos": ["Bontyyy/orchestrator-api-sample", "Bontyyy/orchestrator-persistence-sample"], "task_count": 5}}
```

#### Friction surfaced (unsanitized)

1. **zsh glob expansion on `?ref=main`.** The sample `gh api repos/.../?ref=main` command in SKILL.md §Step 4 fails under zsh (macOS default) with `no matches found` — the `?` is interpreted as a glob wildcard against the filesystem before `gh` sees it. Fix: single-quote the full API path. **Retrospective input for WU 2.8** — document this shell gotcha in the skill's sample or use `--` separator. Not a correctness bug but a real bootstrap friction.

2. **Default Python environment gaps.** System Python on macOS lacks `pyyaml` and `jsonschema` by default, and `pip install` was blocked by PEP 668 (externally-managed-environment). Subagent resolved with `--break-system-packages`. `scripts/validate-event.py` works without these; declaration schema validation (`template-coverage.schema.json`) requires them and has no shipped helper. **Retrospective input** — either ship `scripts/validate-declaration.py` (parallel to validate-event.py) or document a `scripts/requirements.txt` + venv setup in the repo root. Same friction as Step 1's YAML-parsing gap.

3. **`validate-event.py --file /dev/stdin` silently unsupported.** `exit=2`, "file not found". Stdin-without-`--file` works. A natural pre-append validation pattern (pipe candidate event through stdin with `--file /dev/stdin`) fails. Minor. **Retrospective input** — update script's help text.

4. **`task_count` semantics confirmed.** The skill counts all tasks including trivially-satisfied ones (T04, T05 with empty required_templates). `task_count: 5` reflects "feature size at check time", not "number of tasks that contributed to the demand". Clear from skill text, no ambiguity here — noting for the record.

5. **Feature state unchanged** (`planning`), confirming the skill respects the "no state transition" output contract. Invoker is now unblocked to run plan-review Phase A.

#### Outcome

Skill completed cleanly on cycle 1. Both event log entries now present; both validate. Next skill: plan-review Phase A.

---

### Step 3 — plan-review skill, Phase A (plan-file emission)

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context.
- **Pre-conditions verified:** feature exists, `state: planning`, `task_graph` non-empty (5 tasks), no prior `/features/FEAT-2026-0004-plan.md` → all green.

#### Plan file emitted

`/features/FEAT-2026-0004-plan.md`:
- Frontmatter: `feature_correlation_id: FEAT-2026-0004`, `plan_pass: 1`
- One-paragraph reminder of edit conventions (structural edits inside YAML block, prose edits inside `### Work unit prompt`)
- `## Task graph` fenced YAML block — **preserves `required_templates` verbatim** on T01/T02/T03; T04/T05 omit the field (as decomposition + human-edit left them)
- Five `### Task TNN — <type>, <repo>` sections, each with placeholder `<draft the work unit prompt for this task>` — intended to be populated by the human-operator next

#### State flip + event

Feature frontmatter `state: planning → plan_review` (single-field update, prose body untouched). `plan_ready` appended (validator exit 0, 3 events total now):

```json
{"timestamp":"2026-04-22T20:15:00Z","correlation_id":"FEAT-2026-0004","event_type":"plan_ready","source":"pm","source_version":"1.0.0","payload":{"plan_file_path":"features/FEAT-2026-0004-plan.md","task_count":5,"plan_pass":1}}
```

#### Friction surfaced

1. **`required_templates` shape inconsistency after decomposition + human edit.** T01/T02/T03 carry the field (populated by the human); T04/T05 do not carry the field at all (decomposition never wrote it because they inherited the skill's "skip" default). Both are schema-valid — `required_templates` is optional — but the plan file mirrors the inconsistency. Whether absence should normalize to `required_templates: []` or stay absent is undefined. Minor stylistic drift; **retrospective input** for a future normalization pass (or leave as-is if we accept "absent means empty" equivalence).

2. **`validate-event.py` help text surprise (repeat).** Subagent initially tried `--event` (doesn't exist); only `--file` + stdin are supported. Same friction as Step 2 point #3 — confirmed as a low-signal repeating friction worth a one-line help-text update in WU 2.8.

#### Outcome

Phase A completed cleanly on cycle 1. Feature is in `plan_review`; plan file on disk; event log consistent. The skill does NOT loop waiting for edits — per its §"Phase A exit criteria", control returns to the invoker. Re-invocation for re-ingest (Phase B) is event-triggered and external to this skill.

### Step 3.5 — Human-operator drafts the 5 work unit prompts

Per the plan-review skill §"Two edit surfaces", work unit prompts are the prose content the human co-authors with the PM agent during `plan_review`. They live in the plan file only and are consumed by the issue-drafting skill at drafting time. Filling them in is an **expected human action during `plan_review`**, not an "edit" in the structural-re-ingest sense — the acceptance criterion "no edits during plan review" (WU 2.7 §1) applies to the YAML block, not to prompt prose.

The operator (this session, playing the human role) drafted each of the 5 prompts directly in `/features/FEAT-2026-0004-plan.md`. No re-ingest of Phase B is triggered because no structural fields changed.

**Retrospective input:** the skill text should clarify — or the WU 2.7 happy-path acceptance criterion should clarify — that "no edits during plan review" refers to structural edits, not prose drafting. The tension is small but a first-time reader of the plan doc could honestly ask "is drafting the prompt itself an edit?"

### Step 4 — Human plan approval

Approval signal per the plan-review skill §"Approval signaling": the operator writes `/inbox/plan-approved/FEAT-2026-0004.md`. No polling loop exists in the walkthrough (we are not running the production runtime); the file is written by this session and serves as the ledger of the approval decision. The corresponding `plan_approved` event would, in production, be emitted by the polling loop with `source: human`; here, the operator writes it manually to keep the event log complete.

Approval artifact: `inbox/plan-approved/FEAT-2026-0004.md`. `plan_approved` event appended (`source: human`, `source_version: 42feb0d` — the orchestration repo's short SHA at emission, per the event schema description). State flipped `plan_review → generating` in the feature frontmatter. Event log: 4 events, all valid.

#### Friction surfaced in the human-approval step

1. **`source_version` for `source: human` events is under-specified in practice.** The event schema description says: "`human` events use the orchestration repo commit SHA or `n/a`". The subagent earlier in Step 2 used `source_version: "1.0.0"` for its PM event (correct) — but a human-emitted event needs to pick between "SHA of orchestration repo at emission" and `n/a`. No shared rule states the preference; I picked the short SHA for informational value. **Retrospective input** — add a convention note to `shared/rules/verify-before-report.md` §3 on which of the two human-event fields to use.

2. **No `feature_state_changed` event in the schema.** `agents/pm/CLAUDE.md` §"Output artifacts" says the PM agent emits "`feature_state_changed` on feature-level transitions" — but `shared/schemas/event.schema.json`'s `event_type` enum does NOT include `feature_state_changed`. The enum has 16 values, none matching. The feature's state flip from `plan_review → generating` (and later `generating → in_progress`) is therefore observable only via the feature frontmatter's git history, not via the event log. **This is a critical finding for the retrospective** — either `feature_state_changed` must be added to the enum (additive, Phase 1 freeze-compatible if the schema's additivity clause holds) or the PM CLAUDE.md reference must be removed / reworded. The current state: CLAUDE.md promises something the schema doesn't support.

### Step 5 — issue-drafting × 5 tasks, sequential

Each of the 5 tasks was drafted via its own fresh Sonnet 4.6 subagent invocation, re-reading shared rules + CLAUDE.md + issue-drafting-spec.md + issue-drafting SKILL.md + work-unit-issue.md template per `role-switch-hygiene.md`. Sequential execution (not parallel) to avoid race conditions on the event log append — a deliberate walkthrough choice given no production polling loop is mediating.

#### Results (per task)

| Task | Repo | Issue | Labels on creation | Events emitted | Validator exit |
|---|---|---|---|---|---|
| T01 (impl, no-dep) | persistence-sample | [#1](https://github.com/Bontyyy/orchestrator-persistence-sample/issues/1) | `state:ready`, `type:implementation`, `autonomy:review` | `task_created` + `task_ready` (trigger `no_dep_creation`) | 0 |
| T02 (impl, deps [T01]) | api-sample | [#9](https://github.com/Bontyyy/orchestrator-api-sample/issues/9) | `state:pending`, `type:implementation`, `autonomy:review` | `task_created` only | 0 |
| T03 (qa_authoring, no-dep) | api-sample | [#10](https://github.com/Bontyyy/orchestrator-api-sample/issues/10) | `state:ready`, `type:qa-authoring`, `autonomy:review` | `task_created` + `task_ready` (trigger `no_dep_creation`) | 0 |
| T04 (qa_execution, deps [T01,T02,T03]) | api-sample | [#11](https://github.com/Bontyyy/orchestrator-api-sample/issues/11) | `state:pending`, `type:qa-execution`, `autonomy:review` | `task_created` only | 0 |
| T05 (qa_curation, deps [T04]) | api-sample | [#12](https://github.com/Bontyyy/orchestrator-api-sample/issues/12) | `state:pending`, `type:qa-curation`, `autonomy:review` | `task_created` only | 0 |

Per-claim verification counts across the 5 passes: 6 (T01), 8 (T02), 4 (T03), 4 (T04), 4 (T05). The skill's designated evidence surface (`## Context` inline block with numbered verification items) was used consistently across all 5 bodies. No reformulations, no `spec_level_blocker` escalations.

Event log: 11 events, all validate on every per-task append. Order: task_graph_drafted → template_coverage_checked → plan_ready → plan_approved → T01(task_created, task_ready) → T02(task_created) → T03(task_created, task_ready) → T04(task_created) → T05(task_created).

#### Friction surfaced (aggregated across 5 passes; unique insights named)

1. **Template v1 is implementation-centric; QA tasks strain the shape.** T03 (qa_authoring) and T05 (qa_curation) surfaced the same structural tension: the issue's `assigned_repo` is the component repo (api-sample), but the actual deliverable (test plan file, curation record) lives in the orchestrator repo under `docs/walkthroughs/phase-2/test-plans/`. The template's `## Verification` section assumes commands "in the `component_repo` root"; for QA tasks we had to annotate "commands run from the orchestrator repo root". This is a repeated pattern, not a one-off. **Retrospective input for WU 2.8:** consider a `deliverable_repo` optional frontmatter field, or a canonical §Deliverables section in the template. The per-claim verification discipline remained load-bearing despite thinner claim surfaces on QA tasks — scope-informing claims about "what regression entries currently exist" on the target repo were genuinely repo-state, not orchestrator-internal.

2. **Worked example in `issue-drafting/SKILL.md` is C# / .NET-specific.** T01 on `orchestrator-persistence-sample` (Python) required active mental translation for every concrete detail — `WidgetsController.cs` → `widget_repository.py`, `dotnet test` → `pytest`, `IWidgetRepository` → `WidgetRepository` (Protocol). The example was useful for shape (evidence format, label order, event payload structure) but Python/Java/Go target repos will need their own localized patterns. **Retrospective input** — either generalize the example (language-neutral), add a Python example as a second worked example, or call out that the example is .NET-specific.

3. **`depends_on` narrative convention not explicitly spelled out.** Three of the five tasks have non-empty `depends_on`. The skill SKILL.md lists the YAML frontmatter as the canonical machine-readable carrier, but does not say whether the deps should also be narrated in §Context prose. All three subagents chose to narrate them (correctly, given a cold-read component agent would benefit). **Retrospective input** — add a one-line clause: "For `depends_on` non-empty, name the deps in prose in §Context." Not a correctness bug, but currently every PM-agent session re-derives the same choice.

4. **`min_quantity` defaulting + .NET `int?` binding edge case** (T02-specific). The plan prompt says "blank or missing `min_quantity` defaults to `0`"; ASP.NET's model-binding distinction between missing and empty-string may require explicit handling. T02's body added an escalation trigger for this edge. Not a skill bug — good example of the reformulate-or-escalate discipline catching a real ambiguity instead of papering over it. Noting as a positive observation.

5. **`conftest.py` emptiness + `asyncio_mode = "auto"`** (T01-specific). The Python repo's `conftest.py` is empty but `asyncio_mode = "auto"` is set in `pyproject.toml`. This is relevant context for the component agent implementing T01 (no redundant `@pytest.mark.asyncio` decorators needed), but was not explicitly named in T01's body. Minor — flagging as an observation, not a reformulation trigger.

6. **Tiny skill ambiguity on `depends_on` in the task_created payload.** The subagent for T02 emitted `depends_on: ["T01"]` in the `task_created` payload per the skill's specified shape; for T04 it emitted `depends_on: ["T01", "T02", "T03"]`; for T05 it emitted `depends_on: ["T04"]`. All three match the skill. No issue — noting that the transitive-vs-declared question raised in Step 1 (task-decomposition) does not reappear here because issue-drafting copies the `depends_on` verbatim from the task graph, not re-deriving it.

#### Outcome

All 5 issues open on their respective repos, labels correct per task shape. 2 tasks are `state:ready` (T01, T03) and can be picked up immediately by their target-repo agents; 3 tasks are `state:pending` (T02, T04, T05) and await dependency recomputation. Event log is consistent. Feature state remains `generating` awaiting the first-round-of-issues flip to `in_progress`.

### Step 6 — Feature state flip `generating → in_progress` + simulated `task_completed` + dependency-recomputation

#### Feature state flip

Per `agents/pm/CLAUDE.md` §"Entry transitions owned": "generating → in_progress — after the human approves the plan and Specfuse generates boilerplate across component repos, the PM agent opens the first round of issues and transitions the feature into in_progress." All 5 issues are now opened; the feature frontmatter flipped `state: generating → in_progress`. **No `feature_state_changed` event emitted** — see Step 4 Finding #2 (that event type is referenced in CLAUDE.md but is not in the schema enum).

#### Simulated T01 `task_completed`

A merge watcher does not yet exist (Phase 1 retrospective deferred item; WU 2.7 is PM-scope). To drive dep-recomputation through its first live trigger, the operator simulated T01's full lifecycle collapse:

1. Manually rotated `state:ready → state:done` on `Bontyyy/orchestrator-persistence-sample#1` via `gh issue edit` — this is the step the merge watcher will own when built (Phase 2+ component).
2. Manually emitted `task_completed` with `source: component:orchestrator-persistence-sample`, `source_version: 1.5.0` (the frozen component agent version, per `scripts/read-agent-version.sh component`). Event validated via `scripts/validate-event.py --file …` (exit 0). Appended as line 12 of the event log.
3. Invoked the dep-recomputation skill via a fresh Sonnet 4.6 subagent with the triggering event's feature ID and TNN.

This mirrors the "Phase 1 Task A Gap 3" pattern — manual label rotation + manual event emission where the merge watcher will eventually act. Logged as an observation, not a finding (a Phase 2+ carry item).

#### Dependency-recomputation subagent execution

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context.
- **Inputs:** feature-level correlation ID `FEAT-2026-0004`, triggering task `FEAT-2026-0004/T01`.
- **Walk trace (deterministic, task-ID sort order):**
  - **Candidates:** T02 (deps `[T01]`), T04 (deps `[T01, T02, T03]`). T03's deps are empty → not a candidate. T05's deps are `[T04]` → T04 is not the triggering task → not a candidate.
  - **T02 (api-sample#9)**: 6a live-read → `state:pending` ✓. 6b live-read T01 → `state:done` ✓. 6c flip `pending → ready` via `gh issue edit`; re-read confirms. 6d emit `task_ready` event, trigger `"task_completed:T01"`. Validator exit 0, appended.
  - **T04 (api-sample#11)**: 6a live-read → `state:pending` ✓. 6b live-read T01 → `state:done` ✓; live-read T02 → `state:ready` (just flipped in this same invocation, not `state:done`). **Break** (correct per skill §Step 6b). T04 stays pending, no flip, no event.
  - No more candidates.

Event appended (line 13 of the log):

```json
{"timestamp":"2026-04-22T20:55:00Z","correlation_id":"FEAT-2026-0004/T02","event_type":"task_ready","source":"pm","source_version":"1.0.0","payload":{"issue":"Bontyyy/orchestrator-api-sample#9","trigger":"task_completed:T01"}}
```

The triggering task (T01) is in the event correlation of line 12; the flipped task (T02) is in the event correlation of line 13. The single-writer invariant for `pending → ready` is respected: T02's flip was owned by dep-recomputation with `trigger: "task_completed:T01"`, distinguishing its provenance from T03's flip earlier (owned by issue-drafting with `trigger: "no_dep_creation"`). A consumer of the event log can tell at a glance which skill owned which flip.

#### Friction surfaced in Step 6

1. **Live-reading T01 twice in one invocation.** During T04's 6b walk, T01's label was re-read even though it had just been read during T02's 6b walk seconds earlier. The subagent called this "load-bearing, not redundant" — a concurrent actor could in principle regress T01 between the two reads, and the skill's idempotence contract makes the fresh read the only safe posture. O(candidates × deps) GitHub API calls scales sublinearly for 5-task features; for 30-task features this could be worth flagging but is not a Phase 2 problem today. **Noting, not a finding.**

2. **The T02-just-flipped case is the skill's worked example made real.** SKILL.md §Worked example 1 describes the exact scenario we hit (T02 flipped, T04 sees T02 as ready-not-done and breaks). The walkthrough confirms the skill behaves as documented. **Positive observation** — the worked example proved load-bearing, justifying the investment in writing it alongside the procedure.

3. **`validate-event.py` help-text friction recurred.** Third instance of the same friction (subagent looking for `--stdin` or `--event`, finding only `--file` or stdin-without-flag). Conclusively worth a retrospective fix: either add `--stdin` as an explicit alias or reword the help text to make the stdin-without-flag pattern obvious.

4. **`feature_state_changed` gap is real.** The feature flipped `plan_review → generating` and `generating → in_progress` during this walkthrough, but neither transition is observable via the event log — both were silent frontmatter edits. A downstream consumer reconstructing feature state from the event log alone cannot see when these transitions happened. This is a real gap with two candidate fixes: (a) add `feature_state_changed` to the enum (additive schema change), (b) remove the CLAUDE.md reference. **Retrospective decision point.**

## Outcome — Feature 1 happy path

All six WU 2.7 acceptance criteria for Feature 1 (happy path) met:

| # | Acceptance criterion | Status |
|---|---|---|
| 1 | Validated spec, straightforward task graph (2 component repos, 1 impl/repo, 1 qa_authoring, 1 qa_execution), no edits during plan review, all templates present | ✓ (graph: T01 impl persistence, T02 impl api, T03 qa_authoring api, T04 qa_execution api, T05 qa_curation api; `required_templates` all matched by both repos' `.specfuse/templates.yaml`; no structural edits during `plan_review`) |
| 2 | Plan drafted, approved without edit, issues opened in both component repos | ✓ (plan file at `features/FEAT-2026-0004-plan.md`, approved via `inbox/plan-approved/FEAT-2026-0004.md`, issues `persistence-sample#1` + `api-sample#9,10,11,12`) |
| 3 | First `task_completed` triggers `task_ready` on the next task | ✓ (T01's simulated `task_completed` → dep-recomputation → T02 `task_ready` with `trigger: "task_completed:T01"`) |
| 4 | Feature reaches `in_progress` cleanly | ✓ (feature state `in_progress`; T01 `done`, T02 `ready`, T03 `ready`, T04 `pending`, T05 `pending`) |
| 5 | Log at `docs/walkthroughs/phase-2/feature-1-log.md` | ✓ (this file) |
| 6 | Every event validates through `scripts/validate-event.py` | ✓ (13 events, `ok: 13 event(s) validated`, exit 0) |

Also met (implicitly from the skills' disciplines):
- **Single-writer invariant** on `pending → ready`: T01 + T03 owned by issue-drafting (trigger `no_dep_creation`), T02 owned by dep-recomputation (trigger `task_completed:T01`). No writer violation across 3 distinct flips.
- **Role-switch hygiene:** every subagent (task-decomposition, template-coverage-check, plan-review Phase A, 5× issue-drafting, 1× dep-recomputation — 9 total) re-read `/shared/rules/*`, `agents/pm/CLAUDE.md`, and its own SKILL.md before acting. None re-used prior-subagent context.
- **Per-claim verification** discipline applied across 5 issue-drafting passes: total of 26 verifications recorded in §Context evidence blocks across the 5 issue bodies. Zero reformulations, zero escalations.

## Findings summary (Retrospective input for WU 2.8)

Consolidated findings from across the 6 steps. Each is a candidate input for the Phase 2 retrospective triage (Fix-in-Phase-2 vs. Defer-to-Phase-3+).

### New or notable findings

- **F1.1** — `feature_state_changed` event type referenced in `agents/pm/CLAUDE.md` but absent from `shared/schemas/event.schema.json` enum. Feature-level transitions (`plan_review → generating`, `generating → in_progress`, `in_progress → done`) have no audit surface in the event log. Decide: add to enum, or remove from CLAUDE.md.
- **F1.2** — `required_templates` is populated by the human between decomposition and template-coverage-check. The skill Out-of-scope clause justifies this (decomposition does not infer) but the walkthrough confirms it's a necessary human-touch step in every happy path. Decide: automate a conservative inference, or accept the step.
- **F1.3** — `work-unit-issue.md` template v1 is implementation-centric. QA tasks (qa_authoring, qa_execution, qa_curation) whose deliverables live in the orchestrator repo (not the target component repo) strain the `component_repo` field and the §Verification section's "commands run in the component_repo root" convention. Decide: add `deliverable_repo` optional field, or add a canonical `§Deliverables` section, or accept the strain.
- **F1.4** — `issue-drafting/SKILL.md`'s worked example is .NET-specific. Python / non-.NET target repos require active mental translation at every step. Decide: generalize example, add second Python example, or call out as .NET-specific.
- **F1.5** — `source_version` convention for `source: human` events is documented only in the schema description (`commit SHA or n/a`). Not referenced in any shared rule. Decide: promote to `shared/rules/verify-before-report.md` §3.
- **F1.6** — `scripts/validate-event.py` help text / invocation pattern tripped 3 of 9 subagents. The script accepts `--file <path>` or stdin-without-flag; other intuitively-tried forms (`--stdin`, `--event`, `--file /dev/stdin`, positional argument) fail. Update help text / add aliases.
- **F1.7** — zsh (macOS default) silently expands `?` in unquoted `gh api` URLs. SKILL.md sample commands show `gh api repos/.../contents/...?ref=main` without quotes; this fails under zsh. Document the quoting requirement or use `--` separator in examples.
- **F1.8** — No `scripts/validate-frontmatter.sh` / `scripts/requirements.txt`. Every subagent that needed to schema-validate YAML frontmatter had to stand up a venv + `pip install pyyaml jsonschema` (blocked by PEP 668 on macOS without `--break-system-packages`). Ship a helper script or document the setup prerequisite.
- **F1.9** — `task-decomposition/SKILL.md` Step 4 is ambiguous on "single `qa_authoring` vs one-per-implementation-task" when the feature scope explicitly collapses to a single test plan. The subagent followed the feature's explicit shape; the skill rule reads the other way. Clarify.
- **F1.10** — `task-decomposition/SKILL.md` Step 5's `depends_on` rule for cross-repo qa_execution does not carve out mock-based testing. Cross-repo QA deps end up transitively declared even when the API-side mocks the persistence call. Clarify.
- **F1.11** — `decomposition_pass` counter has no persistent carrier in the feature frontmatter. The agent must count prior `task_graph_drafted` events in the log to compute it. Correct behavior but not explicitly stated. Document.
- **F1.12** — `issue-drafting/SKILL.md` does not explicitly say whether `depends_on` should be narrated in `§Context` prose in addition to the YAML frontmatter carrier. All 3 deps-carrying tasks in the walkthrough (T02, T04, T05) were narrated consistently; add the one-line clause.
- **F1.13** — `plan-review/SKILL.md` + WU 2.7 acceptance criterion 1's "no edits during plan review" is ambiguous on whether drafting work unit prompts counts as an edit. Clarify that structural edits (YAML block) are what triggers re-ingest, not prose drafting.

### Positive observations (not findings)

- The worked example in dep-recomputation SKILL.md matched the T04-sees-T02-ready-not-done scenario exactly. Investment in writing the worked example paid off.
- The single-writer invariant on `pending → ready` with distinct `trigger` tags (`no_dep_creation` vs. `task_completed:TNN`) made the provenance of every flip instantly legible in the event log.
- The per-type payload schema for `template_coverage_checked` (introduced in WU 2.6) validated automatically via the additive `scripts/validate-event.py` extension (introduced in WU 2.5). Both skills' Finding 5 absorption is working as intended.
- Role-switch hygiene (re-read `/shared/rules/*` + `CLAUDE.md` + skill before every invocation) did not cause any subagent to miss a rule in practice. Cost is real (each subagent re-reads ~25 files per invocation) but the discipline is cheap insurance — noting for the retrospective whether this cost is acceptable long-term or warrants a more efficient mechanism.

### Merge watcher dependency

Re-confirmed: the `state:in-review → state:done` flip on task issues, and the associated `task_completed` event emission, have no owner yet — they are the merge watcher's future responsibility. Phase 1 Task A Gap 3 carries forward. For the walkthrough this was handled by manual label rotation + manual event emission from the orchestration session. Phase 2+ will need a concrete merge-watcher component. **Noting, not a finding of Feature 1 per se.**

-->
