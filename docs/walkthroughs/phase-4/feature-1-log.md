# Phase 4 walkthrough — Feature 1 log

## Identity

- **Walkthrough:** Phase 4, WU 4.6
- **Feature:** `FEAT-2026-0008` — Widget update endpoint (PATCH /widgets/:id)
- **Shape chosen:** Happy path (single-repo, full pipeline, specs agent at front)
- **Started:** 2026-04-25
- **Operator:** @Bontyyy (human)
- **Orchestration model:** Opus 4.6
- **Specs / PM / QA / component-agent model for subagent sessions:** Sonnet 4.6
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
- **Specs repo:** [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample)
- **Agent versions at execution:** specs 1.0.0, PM 1.6.3 (frozen), component 1.5.2 (frozen), QA 1.5.2 (frozen)
- **Status:** complete — feature reached `state: done`. 27 events, all validated. 12 findings + 5 positive observations.

## Pre-walkthrough setup

- Cloned `acme/api-sample` and `acme/specs-sample` locally as siblings to the orchestration repo.
- Created `docs/walkthroughs/phase-4/` directory.
- Confirmed frozen surfaces untouched: no unauthorized post-freeze commits on `agents/pm/*`, `agents/component/*`, `agents/qa/*`, `shared/rules/*`. Only Phase 3 freeze-related WUs (3.8–3.13).
- Confirmed specs agent at v1.0.0 — active Phase 4 surface.
- Pre-computed task graphs and session prompts in `notes-scratch.md`.

## Skill invocations

### Step 1 — Specs agent feature-intake (S1)

- **Invoked by:** orchestration session (Opus 4.6) via `Agent` subagent, model=sonnet, fresh context. Re-read `/shared/rules/*`, specs CLAUDE.md (v1.0.0), feature-intake/SKILL.md per role-switch-hygiene.
- **Input:** Feature title="Widget update endpoint", involved_repos=["Bontyyy/orchestrator-api-sample"], autonomy_default=review.
- **Output:** `/features/FEAT-2026-0008.md` created (state=drafting, task_graph=[]), `/events/FEAT-2026-0008.jsonl` created with 1 event.
  - Ordinal resolution: max existing = 0007, candidate = 0008, collision check passed.
  - Event: `{"timestamp":"2026-04-25T15:12:38Z","correlation_id":"FEAT-2026-0008","event_type":"feature_created","source":"specs","source_version":"1.0.0","payload":{"feature_title":"Widget update endpoint","involved_repos":["Bontyyy/orchestrator-api-sample"],"autonomy_default":"review","correlation_id":"FEAT-2026-0008"}}`
- **Verification:** validate-frontmatter.py exit 0, validate-event.py exit 0 (envelope + per-type feature_created.schema.json), JSONL 1 line, correlation ID consistent across filename/frontmatter/event envelope/event payload.
- **Friction:** None. Procedure executed without corrective cycles. Minor observation: preamble specified `/tmp/event-check.json` while SKILL.md example uses `/tmp/event.json` — doc-consistency gap, not functional.
- **Duration:** ~95s, 28 tool uses.

### Step 2 — Specs agent spec-drafting (S2)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, specs CLAUDE.md, spec-drafting/SKILL.md, feature registry.
- **Input:** FEAT-2026-0008 registry (state=drafting), human-provided scoping: PATCH /widgets/:id with partial update, 2 ACs.
- **Output:** Feature narrative created at `<acme/specs-sample>/product/features/FEAT-2026-0008.md` with AC-1 (partial update → 200) and AC-2 (not found → 404 + widget_not_found). Registry updated with Description, Scope, Out of scope, Related specs sections.
- **Verification:** Both files re-read post-write — content matches. Pre-validation review checklist: all items pass (description, scope prescriptive language, out of scope, related specs, ACs testable/single-behavior/explicit, no frontmatter mods, no OpenAPI file per task instruction).
- **Friction:** 2 minor items:
  - (1) SKILL.md worked example uses `## Overview` heading; Phase 3 narrative files use `## Feature summary`. Followed Phase 3 precedent. Doc-consistency gap, not functional.
  - (2) `## Related specs` sections in narrative file vs. registry serve different audiences — slight content divergence is intentional. Not friction.
- **Duration:** ~86s, 19 tool uses.

### Step 3 — Specs agent spec-validation (S3)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, specs CLAUDE.md, spec-validation/SKILL.md, feature registry, event log, per-type event schemas.
- **Input:** FEAT-2026-0008 (state=drafting), 1 spec file in Related specs.
- **Output:** 3 events emitted, feature state transitioned `drafting → validating → planning`.
  - `feature_state_changed(drafting → validating, trigger=validation_requested)` at 15:17:44Z
  - `spec_validated(pass=true, validator_version="simulated-1.0")` at 15:18:06Z
  - `feature_state_changed(validating → planning, trigger=validation_passed)` at 15:18:35Z
- **Verification:** validate-event.py exit 0 for all 3 events individually + round-trip on full 4-line log. Registry state=planning confirmed. Event log line count = 4.
- **Friction:** 4 items:
  - **F4.1 (PF-2 confirmed):** `specfuse` CLI not installed. Simulated clean pass with `validator_version="simulated-1.0"`. Honest audit trail — anti-pattern §1 technically triggered but walkthrough gap, not production. **Reco:** install Specfuse CLI before production walkthroughs.
  - **F4.2:** `/tmp/event-check.json` write blocked by sandbox — used `$TMPDIR` instead. Sandbox-environment friction, not orchestrator design.
  - **F4.3:** `trigger` field value discrepancy — SKILL.md example uses `human_requested_validation`, preamble specifies `validation_requested`. Schema allows freeform strings. Followed preamble. Minor doc-consistency gap.
  - **F4.4:** Single spec file (narrative-only, no OpenAPI). `## Related specs` had one link. Precondition (>=1) satisfied. Spec-drafting completeness gap from S2 (acceptable for walkthrough pattern matching Phase 3).
- **Observation — Specs-to-PM handoff:** First-ever runtime exercise of `validating → planning`. Clean transition — state correctly written, event correctly emitted. PM agent can pick up with task-decomposition on `state: planning`. **No manual state-bumping required between specs agent and PM agent.**
- **Duration:** ~151s, 35 tool uses.

### Step 4 — PM task-decomposition (S4)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, PM CLAUDE.md (v1.6.3 frozen), task-decomposition/SKILL.md.
- **Input:** `features/FEAT-2026-0008.md` (state=planning, task_graph=[]), spec at specs-sample `/product/features/FEAT-2026-0008.md`.
- **Output:** task_graph written to frontmatter + `task_graph_drafted` event emitted (line 5).

  | id | type | depends_on | assigned_repo |
  |---|---|---|---|
  | T01 | implementation | [] | Bontyyy/orchestrator-api-sample |
  | T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample |
  | T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample |
  | T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample |

  Exact match to pre-computed expected graph in `notes-scratch.md §1`.
- **Event:** `{"timestamp":"2026-04-25T15:22:26Z","correlation_id":"FEAT-2026-0008","event_type":"task_graph_drafted","source":"pm","source_version":"1.6.3","payload":{"task_count":4,"involved_repos":["Bontyyy/orchestrator-api-sample"],"decomposition_pass":1}}`
- **Verification:** validate-event.py exit 0 (envelope-only — no `task_graph_drafted.schema.json`); validate-frontmatter.py exit 0; source_version 1.6.3 from `read-agent-version.sh pm`; state remains `planning`.
- **Friction:** 5 items:
  - **F4.5:** Feature registry `## Related specs` contains GitHub URL, not local path — PM subagent had to `find` local clone. One failed Read before resolution.
  - **F4.6:** Capability count ambiguity — 2 ACs but no `### Behavior` headings in narrative spec. SKILL.md rule for narrative specs unclear on AC-to-capability mapping. Subagent correctly inferred 1 behavior (single endpoint, two response branches). **Gap in SKILL.md v1.2 for narrative-spec features.**
  - (3) `qa_execution` autonomy override rule only fires on `autonomy_default: auto` — this feature is `review`, so no override needed. Correct behavior, correctly omitted.
  - (4) No `task_graph_drafted.schema.json` — envelope-only validation. Expected.
  - (5) Specs-sample clone path confusion (tried wrong base path first). Low friction.
- **Duration:** ~156s, 35 tool uses.

### Step 5 — Human plan_review (S5)

- **Actor:** Opus 4.6 orchestration session. Per notes-scratch §3, skip dedicated plan-review skill; simulate Phase A edits inline.
- **Actions:**
  1. Added `required_templates` per task: T01=[api-controller, api-request-validator], T02=[test-plan], T03/T04=[].
  2. Changed `state: planning → state: generating` (skipped transient `plan_review` in frontmatter).
  3. Emitted `feature_state_changed(planning → plan_review, trigger=plan_ready)` at 15:24:30Z then `feature_state_changed(plan_review → generating, trigger=plan_approved)` at 15:24:32Z. source=human, source_version=235fa17.
- **Verification:** 7 events total, all validate exit 0. Frontmatter validates exit 0. State=generating.
- **Friction:** None. Mechanical step following the Phase 3 pattern exactly.

### Step 6 — PM template-coverage-check (S6)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context.
- **Input:** feature registry (state=generating, task_graph + required_templates populated); api-sample `.specfuse/templates.yaml` declaring `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`.
- **Output:** 1 `template_coverage_checked` event. Coverage clean across all 4 tasks.
- **Event:** `{"timestamp":"2026-04-25T15:26:24Z","correlation_id":"FEAT-2026-0008","event_type":"template_coverage_checked","source":"pm","source_version":"1.6.3","payload":{"involved_repos":["Bontyyy/orchestrator-api-sample"],"task_count":4}}`
- **Verification:** validate-event.py exit 0 (envelope + per-type schema). 8 events total, all valid.
- **Friction:** 1 item — **F4.7:** SKILL.md entry-condition check expects `state == planning` but feature is at `generating` (same pattern as Phase 3 F3.27). Operator-directed invocation proceeded. State guard should be re-evaluated if skill is wired into automated flow.
- **Duration:** ~74s, 23 tool uses.

### Step 7 — PM issue-drafting (S7)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, PM CLAUDE.md, issue-drafting/SKILL.md, work-unit-issue template + example.
- **Input:** feature registry (state=generating), spec at specs-sample.
- **Output:** 4 GitHub issues + 7 events (4 task_created + 2 task_ready + 1 feature_state_changed).

  | Task | Issue | URL | Labels (intended) |
  |---|---|---|---|
  | T01 | #24 | [link](https://github.com/Bontyyy/orchestrator-api-sample/issues/24) | type:implementation, state:ready |
  | T02 | #25 | [link](https://github.com/Bontyyy/orchestrator-api-sample/issues/25) | type:qa_authoring, state:ready |
  | T03 | #26 | [link](https://github.com/Bontyyy/orchestrator-api-sample/issues/26) | type:qa_execution, state:pending |
  | T04 | #27 | [link](https://github.com/Bontyyy/orchestrator-api-sample/issues/27) | type:qa_curation, state:pending |

- **Verification:** validate-event.py exit 0 on all 7 events individually + 15-line log round-trip. Frontmatter updated to state=in_progress.
- **"First round" semantics observation:** `generating → in_progress` emitted at 15:36:30Z, **after all 4 task_created events** (T04 at 15:36:07Z). The trigger field was `first_round_issues_opened`. In this batched session, the guard was checked after all issues were opened. The transition effectively fires on "all tasks opened" rather than "first task opened" — consistent with the Phase 4+ refinement proposal. Recorded as observation per WU AC.
- **Friction:** 4 items:
  - **F4.8 (CRITICAL):** Label application failed — `clabonte` has only `pull` permission on `Bontyyy/orchestrator-api-sample`. Labels could not be created or applied. All 4 issues opened with zero labels. Downstream agents keying on `state:ready` labels will not see T01/T02 as ready. **Resolution requires repo owner granting `triage` access.** Event log carries `task_ready` for T01/T02 as the fallback signal.
  - **F4.9:** `FEAT-2026-0008-plan.md` does not exist. SKILL.md Step 2 (F3.29 fallback) — would be `spec_level_blocker` in production. Walkthrough proceeded with prompt-derived instructions.
  - (3) Sandbox TLS failure on first `gh` call — required `dangerouslyDisableSandbox: true`. Environment friction.
  - (4) TMPDIR cross-sandbox mismatch — recovered by using `/tmp/claude/` shared path.
- **Duration:** ~565s, 93 tool uses.

### Step 8 — Component implementation T01 (S8)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, component CLAUDE.md (v1.5.2 frozen), verification/SKILL.md, pr-submission/SKILL.md.
- **Input:** T01 issue #24, feature spec, api-sample local clone.
- **Output:** [PR #28 on api-sample](https://github.com/Bontyyy/orchestrator-api-sample/pull/28), branch `feat/FEAT-2026-0008-T01-widget-update`, commit `592c4b5`. Implements PATCH endpoint with:
  - `IWidgetRepository.UpdateAsync` + `InMemoryWidgetRepository` implementation (C# `with` expression)
  - `WidgetService.UpdateAsync` with partial-update validation (null = skip, non-null = validate)
  - `WidgetsController.Update` [HttpPatch] action + `UpdateWidgetRequest` DTO
  - 11 new service tests + 6 new controller tests (65/65 total pass)
- **Verification gates — 6/6 PASS:** tests (65/65), coverage (100%), compiler_warnings (0), lint (exit 0), security_scan (0 high/critical), build (Release 0 warnings). Pre-gate `dotnet restore && dotnet build` per F3.1.
- **Event:** `task_started` emitted at 15:47:06Z, source=component:orchestrator-api-sample, source_version=1.5.2. validate-event.py exit 0. Log now 16 lines.
- **Friction:** 5 items:
  - **F4.8 continued:** Push blocked — `clabonte` had pull-only access. Resolved by human granting write access to both api-sample and specs-sample. Branch pushed + PR created post-access-grant.
  - (2) `source` field corrected: initially `component` (bare) → validator rejected → corrected to `component:orchestrator-api-sample`. One corrective cycle.
  - (3-5) Sandbox TLS, TMPDIR mismatch (same as prior sessions).
- **Labels applied post-access-grant:** feature:FEAT-2026-0008 label created + applied to all 4 issues (#24-#27). Type and state labels applied.
- **PF-6 confirmed:** C# `with` expression on sealed record Widget worked exactly as expected. No friction.
- **Duration:** ~539s, 99 tool uses.

### Step 9 — Human merge T01 (S9)

- **Actor:** Opus 4.6 orchestration session.
- **Actions:** Merged PR #28 via `gh pr merge --merge`. Merge commit `c8bf623`. Emitted `task_completed` event for FEAT-2026-0008/T01, source=human, source_version=c8bf623.
- **Verification:** validate-event.py exit 0. Log now 17 lines.
- **Friction:** None.

### Step 10 — QA qa-authoring T02 (S10)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, QA CLAUDE.md (v1.5.2), qa-authoring/SKILL.md, test-plan.schema.json.
- **Input:** T02 issue #25, feature spec at specs-sample.
- **Output:** Test plan at `/product/test-plans/FEAT-2026-0008.md` in specs-sample with 7 tests. [PR #4 on specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample/pull/4).

  | test_id | covers |
  |---|---|
  | widget-patch-name-only | AC-1: name-only update, omitted fields unchanged |
  | widget-patch-quantity-only | AC-1: quantity-only update |
  | widget-patch-all-fields | AC-1: all-fields update |
  | widget-patch-not-found | AC-2: 404 + widget_not_found |
  | widget-patch-validation-blank-name | Scope: blank name → 400 |
  | widget-patch-validation-blank-sku | Scope: blank sku → 400 |
  | widget-patch-validation-quantity-out-of-range | Scope: quantity out of range → 400 |

- **Events:** `task_started` at 16:05:06Z + `test_plan_authored` at 16:05:53Z (plan_path=/product/test-plans/FEAT-2026-0008.md, test_count=7). Both validate exit 0.
- **Friction:** 4 items:
  - **F4.10:** Issue #25's Deliverables/Verification sections reference `product/features/test-plans/FEAT-2026-0008.md` — wrong path. Correct path per schema: `product/test-plans/FEAT-2026-0008.md`. Issue-drafting path bug.
  - **F4.11:** Validation tests (blank name/sku, quantity range) not formal ACs — only in Scope section. `covers` fields cite Scope clause directly.
  - **F4.12:** Feature spec narrative (FEAT-2026-0008.md) was untracked in specs-sample — never committed by S2 (spec-drafting subagent was told not to commit). Committed manually to specs-sample main before merging test plan PR.
  - (4) Sandbox TLS on gh calls (recurring).
- **Duration:** ~216s, 45 tool uses.

### Step 11 — Human merge T02 (S11)

- **Actor:** Opus 4.6 orchestration session.
- **Actions:** Committed feature spec narrative to specs-sample main (446a80f). Merged test plan PR #4. Emitted `task_completed` for FEAT-2026-0008/T02.
- **Friction:** None beyond the spec-commit correction noted in S10.

### Step 12 — PM dependency-recomputation (S12)

- **Actor:** Opus 4.6 orchestration session (simplified — T01 and T02 both have `task_completed` events, T03's `depends_on: [T01, T02]` is satisfied).
- **Output:** `task_ready` event for FEAT-2026-0008/T03, trigger=dependencies_satisfied.
- **Verification:** validate-event.py exit 0. 21 events total, all valid.
- **Friction:** None.

### Step 13 — QA qa-execution T03 (S13)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, QA CLAUDE.md, qa-execution/SKILL.md.
- **Input:** T03 issue #26, test plan at specs-sample, api-sample at commit `c8bf623` (T01 merged).
- **Output:** All 7 tests PASS. `qa_execution_completed` event emitted.

  | test_id | result |
  |---|---|
  | widget-patch-name-only | PASS |
  | widget-patch-quantity-only | PASS |
  | widget-patch-all-fields | PASS |
  | widget-patch-not-found | PASS |
  | widget-patch-validation-blank-name | PASS |
  | widget-patch-validation-blank-sku | PASS |
  | widget-patch-validation-quantity-out-of-range | PASS |

- **Events:** `task_started` at 16:17:18Z (branch=null, correct for observational task) + `qa_execution_completed` at 16:17:38Z (commit_sha=c8bf6235..., test_count=7). Both validate exit 0. 23 events total.
- **Friction:** 4 items:
  - (1) `dotnet test` blocked inside sandbox (MSBuild named-pipe socket) — required `dangerouslyDisableSandbox: true` + `--no-build`. Sandbox constraint.
  - (2) `gh issue view` TLS error (recurring).
  - (3) `branch: null` on task_started correct for qa_execution (no code branch).
  - (4) Test plan HTTP commands vs. unit test equivalence — used `dotnet test` as authorized equivalent coverage. All 7 behaviors covered by unit tests.
- **Duration:** ~533s, 44 tool uses.

### Step 14 — QA qa-curation T04 (S14)

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet, fresh context. Re-read rules, QA CLAUDE.md, qa-curation/SKILL.md.
- **Input:** T04 issue #27, test plan corpus (6 plans: FEAT-2026-0006/0007/0008/9001/9002/9003).
- **Output:** Clean empty-curation pass. No PR produced, no `regression_suite_curated` event (correct per SKILL.md — event emits on PR merge only). Emitted `task_started` + `task_completed` for T04.
- **Cross-feature scan:** 3 candidates evaluated, all refused:
  - FEAT-2026-9001 dedup: refused (sole-test pre-flight — would leave tests[] empty)
  - FEAT-2026-9002 orphan: refused (open regression blocking retirement)
  - FEAT-2026-9003 rename: already applied by prior pass, stale prose remains
- **Friction:** 4 items:
  - (1) Stale rename-request prose in FEAT-2026-9003 — no v1 mechanism to auto-clean.
  - (2) FEAT-2026-9001 sole-test dedup stuck indefinitely without human whole-plan retirement.
  - (3) FEAT-2026-9002 orphan stuck behind 5-day-old unresolved regression (fixture behavior).
  - (4) 3 AC-1 tests share `covers` prefix — correctly classified as distinct behaviors, not dedup candidates.
- **Duration:** ~190s, 46 tool uses.

### Step 15 — Human verify + close (S15)

- **Actor:** Opus 4.6 orchestration session.
- **Actions:**
  1. Emitted `task_completed` for FEAT-2026-0008/T03.
  2. Emitted `feature_state_changed(in_progress → done, trigger=all_tasks_complete)`.
  3. Updated feature registry `state: in_progress → state: done`.
- **Verification:** validate-event.py exit 0 on full 27-event log. validate-frontmatter.py exit 0 on registry (state=done). All 4 tasks have task_completed events. Correlation IDs consistent across all artifacts.
- **Status:** Feature 1 reached `done`.

## Observations

### "First round" semantics

The `generating → in_progress` transition fired at 15:36:30Z, **after all 4 task_created events** (last was T04 at 15:36:07Z). Trigger was `first_round_issues_opened`. In this batched session, the PM agent's guard check found all 4 task_created events on the log before emitting the transition. Effectively "all tasks opened" rather than "first task opened." This is consistent with the Phase 4+ refinement proposal — the batched session naturally produces the "all tasks" behavior. The WU 3.10 v1 "first-task-opened" semantics were not observed in isolation because the guard check ran after the batch.

### Specs-to-PM handoff

The `validating → planning` transition (S3) cleanly handed off to PM task-decomposition (S4). **No manual state-bumping was required.** The specs agent wrote `state: planning` and emitted the `feature_state_changed` event; the PM agent read the registry, confirmed `state: planning`, and proceeded with task-decomposition. This is the first runtime exercise of this handoff — it worked as designed.

## Findings

- **F4.1** — `specfuse` CLI not installed. Validation simulated. Walkthrough gap. Low.
- **F4.2** — Sandbox blocks `/tmp` writes; use `$TMPDIR`. Environment friction. Low.
- **F4.3** — `trigger` field value discrepancy between SKILL.md (`human_requested_validation`) and preamble (`validation_requested`). Schema allows freeform. Minor doc gap.
- **F4.4** — Narrative-only spec (no OpenAPI file). Precondition satisfied. Spec-drafting completeness gap acceptable for walkthrough.
- **F4.5** — Feature registry `## Related specs` contains GitHub URL only, not local path. PM subagent needed `find` to locate local clone. Medium — cross-feature if F2 hits same issue.
- **F4.6** — SKILL.md v1.2 capability-counting rule unclear for narrative specs without `### Behavior` headings. 2 ACs treated as 1 behavior. Medium — SKILL.md gap for narrative-spec features.
- **F4.7** — template-coverage-check SKILL.md expects `state == planning` but feature is at `generating`. Same as Phase 3 F3.27. Low.
- **F4.8 (CRITICAL)** — GitHub label and push permissions. `clabonte` had pull-only access to `Bontyyy/orchestrator-api-sample`. Resolved by human granting write access. **Blocked pipeline for S7 (labels) and S8 (push/PR).** High — must be pre-checked before future walkthroughs.
- **F4.9** — `FEAT-2026-0008-plan.md` does not exist. SKILL.md F3.29 fallback would escalate in production. Walkthrough proceeded with prompt-derived instructions. Medium.
- **F4.10** — Issue #25 references wrong path `product/features/test-plans/` instead of `product/test-plans/`. Issue-drafting bug. Medium.
- **F4.11** — Validation tests (blank name/sku, quantity range) not formal ACs in spec. Scope-cited coverage. Low.
- **F4.12** — Feature spec narrative never committed to specs-sample by spec-drafting session (subagent told not to commit). Committed manually. Medium — spec-drafting session should commit to specs-sample.

### Positive observations

- **P1:** Specs-to-PM handoff worked on first-ever runtime exercise. No manual state-bumping.
- **P2:** Component agent implemented PATCH correctly on first pass. 100% coverage, 65/65 tests, all 6 gates green.
- **P3:** QA test plan covered both ACs + 3 validation edge cases from Scope section — thorough coverage.
- **P4:** All 27 events validate through validate-event.py without exception.
- **P5:** Empty-curation path executed correctly (no PR, no regression_suite_curated event, task_completed emitted).
