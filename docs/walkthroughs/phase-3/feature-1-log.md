# Phase 3 walkthrough — Feature 1 log (happy path)

## Identity

- **Walkthrough:** Phase 3, WU 3.6
- **Feature:** `FEAT-2026-0006` — widget count endpoint (single-repo, happy path)
- **Shape chosen:** happy path (matches acceptance criterion 1 of WU 3.6 — one AC, one implementation task, one qa_authoring, one qa_execution, one qa_curation; no regression expected)
- **Started:** TBD (walkthrough execution date)
- **Operator:** @Bontyyy (human, driving the walkthrough)
- **Orchestration model:** Opus 4.7 (this session — note-taking, commits, subagent invocation)
- **QA-agent model:** Sonnet 4.6 (instantiated per skill invocation via subagent)
- **PM-agent model:** Sonnet 4.6 (reused from Phase 2 v1.6.0, per frozen surface)
- **Component-agent model:** Sonnet 4.6 (reused from Phase 1 v1.5.0, per frozen surface)
- **Component repo:**
  - [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
- **Specs repo:**
  - [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample) — stood up for this walkthrough (WU 0.8 deferred retrofit)
- **QA agent version at execution:** 1.4.0
- **PM agent version at execution:** 1.6.0 (frozen)
- **Component agent version at execution:** 1.5.0 (frozen)
- **Status:** TBD

## Pre-walkthrough setup

Three setup actions performed before any agent skill ran, all logged as WU 3.7 retrospective input on onboarding cost.

### Setup 1 — Stand up the product specs repo

[`Bontyyy/orchestrator-specs-sample`](https://github.com/Bontyyy/orchestrator-specs-sample) created (PR history: initial commit `397dfce`). Public repo under Bontyyy org (neutral-org destination; open-source-bound). Layout:

- `/product/features/FEAT-2026-0006.md` — 1 AC (`GET /widgets/count` returns `{"count": N}`).
- `/product/features/FEAT-2026-0007.md` — 3 AC (pagination default / in-range / over-limit rejection).
- `/product/test-plans/.gitkeep` — target for qa-authoring's writes.
- `/business/.gitkeep` — never-touch boundary (empty).
- `README.md` + `LICENSE` (Apache 2.0).

Phase 0 WU 0.8 had deferred the product-specs-repo setup; retrofitted here. Deferral captured as a WU 3.7 retrospective input under "what Phase 0 skipped cost us".

### Setup 2 — Seed feature registry entries

Orchestrator PR [#36](https://github.com/clabonte/orchestrator/pull/36) merged (commit `7f1e805`) — seeded `features/FEAT-2026-0006.md` and `features/FEAT-2026-0007.md` with `state: planning` + `task_graph: []`. Both point via `## Related specs` at the specs-sample repo's feature files.

### Setup 3 — Confirm frozen surfaces untouched

Verified at walkthrough start: no commits on `agents/pm/*`, `agents/component/*`, or `shared/rules/*` since Phase 2 freeze (commit `8125a86`). Phase 2 freeze contract upheld.

## Skill invocations

### Step 1 — PM task-decomposition

- **Invoked by:** orchestration session (Opus 4.7) via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, [`agents/pm/CLAUDE.md`](../../../agents/pm/CLAUDE.md) (v1.6.0 frozen), and [`agents/pm/skills/task-decomposition/SKILL.md`](../../../agents/pm/skills/task-decomposition/SKILL.md) before acting, per [`/shared/rules/role-switch-hygiene.md`](../../../shared/rules/role-switch-hygiene.md).
- **Input:** [`features/FEAT-2026-0006.md`](../../../features/FEAT-2026-0006.md) (state=`planning`, `task_graph: []`), `## Related specs` points at `Bontyyy/orchestrator-specs-sample:product/features/FEAT-2026-0006.md`.
- **Output:** TBD (the task_graph written back to the feature registry + `task_graph_drafted` event appended to [`events/FEAT-2026-0006.jsonl`](../../../events/FEAT-2026-0006.jsonl)).
- **Verification evidence:** TBD (re-read of frontmatter post-write confirms schema validation; `validate-event.py` exit 0 on the emitted event).
- **Friction:** TBD.

### Step 2 — Human plan_review transition (manual)

- **Actor:** human. Post-session-1, the human reviews the drafted task_graph, optionally adds `required_templates` fields per task (plan-review Phase A simulated — WU 3.6 skipped the dedicated plan-review skill per the walkthrough shape), and flips feature state `plan_review → generating`. Alternative: if task-decomposition already transitioned to plan_review, the human transitions onward.
- **Output:** TBD.
- **Friction:** TBD.

### Step 3 — PM template-coverage-check

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, `agents/pm/CLAUDE.md`, and [`agents/pm/skills/template-coverage-check/SKILL.md`](../../../agents/pm/skills/template-coverage-check/SKILL.md).
- **Input:** feature registry (now with populated task_graph including `required_templates`), `.specfuse/templates.yaml` on `Bontyyy/orchestrator-api-sample` (declares `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]` per Phase 2 setup).
- **Output:** TBD (`template_coverage_checked` event appended).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 4 — PM issue-drafting

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, `agents/pm/CLAUDE.md`, [`agents/pm/skills/issue-drafting/SKILL.md`](../../../agents/pm/skills/issue-drafting/SKILL.md), and [`agents/pm/issue-drafting-spec.md`](../../../agents/pm/issue-drafting-spec.md).
- **Input:** feature registry (populated task_graph), work-unit-issue template at [`shared/templates/work-unit-issue.md`](../../../shared/templates/work-unit-issue.md).
- **Output:** TBD (N GitHub issues opened on `Bontyyy/orchestrator-api-sample`, one per task in the graph; `task_created` + `task_ready` events appended per task).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 5 — Component implementation on T01

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, [`agents/component/CLAUDE.md`](../../../agents/component/CLAUDE.md) (v1.5.0 frozen), and its skill(s) as pointed at by that CLAUDE.md.
- **Input:** GitHub issue for T01 on `Bontyyy/orchestrator-api-sample` (state=`ready`, implementation task, adds `GET /widgets/count` endpoint).
- **Output:** TBD (PR on api-sample against main; post-merge: `task_completed` event on T01).
- **Verification evidence:** TBD (all verification gates pass; coverage ≥ 0.90; zero warnings).
- **Friction:** TBD.

### Step 6 — Human merges T01 PR (manual)

- **Actor:** human operating as merge watcher simulation. Merges the T01 PR on api-sample, flips issue state `in-review → done`, appends `task_completed` event.
- **Output:** TBD.
- **Friction:** TBD.

### Step 7 — QA qa-authoring on T02

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, [`agents/qa/CLAUDE.md`](../../../agents/qa/CLAUDE.md), and [`agents/qa/skills/qa-authoring/SKILL.md`](../../../agents/qa/skills/qa-authoring/SKILL.md).
- **Input:** GitHub issue for T02 on `Bontyyy/orchestrator-api-sample` (state=`ready`, qa_authoring task). Feature registry + specs file fetched via gh or local specs-sample clone.
- **Output:** TBD (test plan written to `/product/test-plans/FEAT-2026-0006.md` in specs-sample repo; `test_plan_authored` event appended to `events/FEAT-2026-0006.jsonl` in orchestrator repo).
- **Verification evidence:** TBD (plan file round-trips through `test-plan.schema.json`; unique test_id; coverage check; event validates).
- **Friction:** TBD.

### Step 8 — Human merges qa-authoring deliverable (manual)

- **Actor:** human. Merges the qa-authoring PR on specs-sample, flips T02 issue state `in-review → done`, appends `task_completed` on T02.
- **Output:** TBD.
- **Friction:** TBD.

### Step 9 — PM dependency-recomputation

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read per hygiene.
- **Input:** feature event log now carrying `task_completed` on T01 and T02 → T03 qa_execution's dependencies satisfied.
- **Output:** TBD (T03 flipped `pending → ready`; `task_ready` event on T03).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 10 — QA qa-execution on T03

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, `agents/qa/CLAUDE.md`, [`agents/qa/skills/qa-execution/SKILL.md`](../../../agents/qa/skills/qa-execution/SKILL.md).
- **Input:** T03 qa_execution task (state=`ready`); plan at `/product/test-plans/FEAT-2026-0006.md` in specs-sample; `Bontyyy/orchestrator-api-sample` main HEAD commit SHA (the one that merged T01).
- **Output:** TBD (`qa_execution_completed` expected for happy path; `qa_execution_failed` would indicate F1 surprise outcome).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 11 — Human closes T03 (manual)

- **Actor:** human. Flips T03 issue state `in-review → done`, appends `task_completed` on T03.

### Step 12 — PM dependency-recomputation

- **Invoked by:** orchestration session via `Agent` subagent. T04 qa_curation dependencies satisfied.
- **Output:** TBD (T04 flipped `pending → ready`).

### Step 13 — QA qa-curation on T04

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, `agents/qa/CLAUDE.md`, [`agents/qa/skills/qa-curation/SKILL.md`](../../../agents/qa/skills/qa-curation/SKILL.md).
- **Input:** T04 qa_curation task (state=`ready`). Scan cohort = specs-sample `/product/test-plans/*.md` which at this point has exactly one plan (FEAT-2026-0006) — below the 50-plan scan budget, below the consolidation/dedup signal threshold.
- **Output:** TBD (expected: empty-curation path — 0 candidates surviving protection; `task_completed` with `empty_curation: true` additive payload; no `regression_suite_curated` event).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 14 — Human closes T04 + feature (manual)

- **Actor:** human. Flips T04 `in-review → done`, appends `task_completed`. Then flips feature state `in_progress → done`, appends `feature_state_changed`.

## Outcome

- **F1 happy path acceptance:** TBD (filled post-walkthrough — expected: all tasks reach `done`, qa_execution_completed emitted, no regression filed).
- **End state:** TBD.
- **Commit:** `chore(phase-3): walkthrough feature 1 complete` (per WU 3.6 AC #7).

## Findings summary

Findings numbered `F3.1`, `F3.2`, … consistent with Phase 2's convention. Placeholder — filled during and after the walkthrough.

### New / notable findings

- **F3.x — TBD**
  - **What.** TBD.
  - **Evidence.** TBD.
  - **Severity.** TBD.
  - **Retrospective disposition.** TBD (Fix-in-Phase-3 / Defer-Phase-4+ / Observation).

### Positive observations

- TBD (observations about things that worked cleanly without friction — Phase 2 tracked these separately because they inform the freeze declaration).

### Merge watcher dependency

The walkthrough simulates the merge watcher role manually (the human flips `in-review → done` labels after merging PRs). Any friction on this simulation is captured as a pre-finding for the future merge-watcher agent (Phase 5+).
