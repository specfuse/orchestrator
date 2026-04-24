# Phase 3 walkthrough — Feature 2 log (regression cycle)

## Identity

- **Walkthrough:** Phase 3, WU 3.6
- **Feature:** `FEAT-2026-0007` — widgets list with pagination (single-repo)
- **Shape chosen:** regression cycle primary (matches acceptance criterion 2 of WU 3.6). Backup candidate (qa-curation suite-growth stress) activates on the criteria recorded under §"Outcome" if regression cycle is impractical.
- **Started:** TBD
- **Operator:** @Bontyyy
- **Orchestration model:** Opus 4.7
- **QA / PM / component agent models:** Sonnet 4.6 per role (no per-session overrides — deliberate per WU 3.6 proposal §6)
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) (.NET, single-repo)
- **Specs repo:** [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample)
- **QA / PM / component agent versions at execution:** TBD (reload from `version.md` at emission time, not eye-cached)
- **Status:** TBD

## Inputs from Feature 1

- F1 ended with specs-sample containing one test plan at `/product/test-plans/FEAT-2026-0006.md`.
- F1 ended with `Bontyyy/orchestrator-api-sample` carrying the `GET /widgets/count` endpoint at a known merge commit.
- F1 findings triaged to `notes-scratch.md` for cross-feature confirmation during F2.

## Skill invocations

Same base shape as F1 (steps 1–14) with an added regression branch starting at step 10 qa-execution-fail → qa-regression → fix impl task → re-execute.

### Steps 1–9 — identical shape to F1

Each filled at walkthrough time following the F1 pattern. Subagent invocations with fresh context, model=sonnet, re-read discipline. TBD.

### Step 10 — QA qa-execution on T03 (expected fail)

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read per hygiene.
- **Input:** T03 qa_execution task; plan at `/product/test-plans/FEAT-2026-0007.md`; api-sample main HEAD commit SHA (the one that merged T01 pagination impl).
- **Expected output (regression-primary path):** `qa_execution_failed` with `failed_tests[]` carrying at least one entry — most likely the AC-3 test (`widgets-list-page-size-over-limit-rejected` or similar), if the component agent's T01 impl missed the structured `error.code = page_size_over_limit` check.
- **If output is actually `qa_execution_completed`:** the naïve-implementation bet failed; backup branch activates (see §"Outcome" below for criteria).
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 11 — QA qa-regression (first-failure path)

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, `agents/qa/CLAUDE.md`, [`agents/qa/skills/qa-regression/SKILL.md`](../../../agents/qa/skills/qa-regression/SKILL.md).
- **Input:** the `qa_execution_failed` event from step 10 (fetched from `events/FEAT-2026-0007.jsonl`), the feature registry (for Q4 `implementation_task_correlation_id` resolution), the plan file (for `expected` + `commands` of the failing test).
- **Expected output:** regression inbox artifact at `/inbox/qa-regression/FEAT-2026-0007-<test_id>.md`; `qa_regression_filed` event appended to feature event log.
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 12 — Human spawns fix task from inbox (manual)

- **Actor:** human (simulating the PM inbox consumer that doesn't exist yet at v1).
- **Input:** `/inbox/qa-regression/FEAT-2026-0007-<test_id>.md`.
- **Action:** read the inbox file, mint a new impl task correlation ID (`FEAT-2026-0007/T05` — next available TNN), open a new GitHub issue on `Bontyyy/orchestrator-api-sample` using `work-unit-issue.md` template with the inbox file's body as the issue body. Flip issue to `state:ready`, emit `task_created` + `task_ready` events. The original impl task (`T01`) stays `state:done` per Q4 invariant.
- **Output:** TBD.
- **Friction:** TBD.

### Step 13 — Component implementation on T05 (fix)

- **Invoked by:** orchestration session via `Agent` subagent, `model=sonnet`, fresh context.
- **Input:** new T05 GitHub issue.
- **Output:** TBD (fix PR on api-sample that addresses the regression reproduction from the inbox file).

### Step 14 — Human merges T05 PR (manual)

- **Actor:** human. Merge, flip T05 `in-review → done`, emit `task_completed` on T05.

### Step 15 — PM dependency-recomputation

- **Invoked by:** orchestration session via `Agent` subagent.
- **Expected output:** a new qa_execution task (T06) becomes `ready` — either spawned automatically if the task graph supports re-runs, or minted by the human if not. v1 note: the QA CLAUDE.md §"Cross-task regression semantics" describes this; the exact task-graph handling is a walkthrough-time discovery (pre-finding: may surface as a F3.x design gap if PM doesn't have a clean answer).

### Step 16 — QA qa-execution on T06 (re-run, expected pass)

- **Invoked by:** orchestration session via `Agent` subagent, fresh context. Re-read discipline.
- **Input:** T06 qa_execution; plan unchanged at `/product/test-plans/FEAT-2026-0007.md`; api-sample main HEAD is now the commit that merged T05 (different from the failing commit).
- **Expected output:** `qa_execution_completed` — the failing test now passes.
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 17 — QA qa-regression (resolution path)

- **Invoked by:** orchestration session via `Agent` subagent, fresh context.
- **Input:** the `qa_execution_completed` event from step 16 as trigger.
- **Expected output:** `qa_regression_resolved` event emitted (via the fallback resolution scan per qa-regression SKILL §"Deferred — cross-attribution resolution"); `escalation_resolved` NOT emitted on this path (no prior escalation, single fix-attempt succeeded). The open `qa_regression_filed` from step 11 is now paired with a resolved event.
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 18 — Human closes T06 + triggers T04 (manual)

- **Actor:** human. Flip T06 `in-review → done`, emit `task_completed`. Then dep-recomp auto-detects T04 qa_curation ready (or human-triggered).

### Step 19 — QA qa-curation on T04 (expected empty or minimal)

- **Invoked by:** orchestration session via `Agent` subagent.
- **Input:** T04 qa_curation; scan cohort = specs-sample `/product/test-plans/*.md` (2 plans: FEAT-2026-0006 + FEAT-2026-0007).
- **Expected output:** empty-curation path likely (0 candidates surviving protection). No dedup/orphan/consolidate signal with only 2 plans. Open-regression protection rule exercised: the just-resolved regression on FEAT-2026-0007 would have blocked retire/rename of its test_id if curation had tried — verified present in the scan even though no retire candidate exists.
- **Verification evidence:** TBD.
- **Friction:** TBD.

### Step 20 — Human closes T04 + feature (manual)

Same as F1 step 14. Feature reaches `done`.

## Q4 invariant audit

**AC #6 requires a specific enumeration, not a blanket assertion.** For each QA-originated write action across F2, record: which session performed it, what was written, which correlation ID it targeted, what type that target was, and whether the action was role-owned.

| Session | Write action | Target correlation_id | Target type | Verdict |
|---|---|---|---|---|
| qa-authoring (step 7) | label flip `state:ready → state:in-progress` | `FEAT-2026-0007/T02` | qa_authoring (owned) | ✅ |
| qa-authoring (step 7) | write `/product/test-plans/FEAT-2026-0007.md` (specs-sample) | file, not task | — | ✅ (file write, not state-mutation) |
| qa-authoring (step 7) | emit `test_plan_authored` event | `FEAT-2026-0007` (feature-level) | feature-level event | ✅ |
| qa-authoring (step 7) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T02` | qa_authoring (owned) | ✅ |
| qa-execution (step 10) | label flip `state:ready → state:in-progress` | `FEAT-2026-0007/T03` | qa_execution (owned) | ✅ |
| qa-execution (step 10) | emit `qa_execution_failed` event | `FEAT-2026-0007` (feature-level) | feature-level event | ✅ |
| qa-execution (step 10) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T03` | qa_execution (owned) | ✅ |
| qa-regression (step 11) | write `/inbox/qa-regression/FEAT-2026-0007-<testid>.md` | file, not task | — | ✅ |
| qa-regression (step 11) | emit `qa_regression_filed` event | `FEAT-2026-0007` (feature-level) | feature-level event | ✅ |
| qa-regression (step 11) | **label flip on T01 impl task?** | `FEAT-2026-0007/T01` | **implementation (NOT owned)** | **❌ if present — Q4 violation** |
| qa-regression (step 11) | **issue body edit on T01 impl task?** | `FEAT-2026-0007/T01` | **implementation (NOT owned)** | **❌ if present — Q4 violation** |
| qa-regression (step 11) | **issue body edit on spawned T05 task?** | `FEAT-2026-0007/T05` | **implementation (NOT owned; spawned by human, not QA)** | **❌ if present — Q4 violation** |
| qa-execution (step 16) | same pattern as step 10 on T06 | `FEAT-2026-0007/T06` | qa_execution (owned) | ✅ |
| qa-regression (step 17) | emit `qa_regression_resolved` event | `FEAT-2026-0007` (feature-level) | feature-level event | ✅ |
| qa-curation (step 19) | (if empty-curation) comment on T04 issue | `FEAT-2026-0007/T04` | qa_curation (owned) | ✅ |
| qa-curation (step 19) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T04` | qa_curation (owned) | ✅ |

Collection method: for each QA session, the orchestration session (Opus 4.7) greps the subagent's tool-call log for `gh issue edit`, `gh api ... PATCH`, `ADD LABEL`, `REMOVE LABEL`, and direct file writes under `/features/*.md` (frontmatter). Every matching action is enumerated in the table above. Cross-reference against `state-vocabulary.md` + [`agents/qa/CLAUDE.md`](../../../agents/qa/CLAUDE.md) §"Entry transitions owned" to confirm ownership. Any `❌` in the Verdict column is a Q4 violation surfaced as an F3 finding with Severity=Critical.

**Expected result:** no `❌` rows. The Q4 invariant holds across F2. Filled at walkthrough time.

## Outcome

- **F2 regression-cycle acceptance (primary):** TBD.
- **F2 backup activation:** TBD. Criteria per WU 3.6 proposal §9:
  - (a) Component agent correct-first-try at step 10 (no failure to react to).
  - (b) Fix attempt fails 2× (spinning path exhausted).
  - (c) Non-QA obstacle (e.g. build infra failure).
  - If any (a)/(b)/(c) triggers, pivot to qa-curation suite-growth stress — seed 3 fixture plans in specs-sample, run curation on them, exercise dedup + orphan + rename + protection paths. Log the pivot explicitly.
- **End state:** TBD.
- **Commit:** `chore(phase-3): walkthrough feature 2 complete` (per WU 3.6 AC #7).

## Findings summary

### New / notable findings

- **F3.x — TBD**
  - **What.** TBD.
  - **Evidence.** TBD.
  - **Severity.** TBD.
  - **Retrospective disposition.** TBD.

### Cross-feature confirmations with F1

- TBD (friction observed in both F1 and F2 — stronger signal for Fix-in-Phase-3 per the 2-feature-evidence criterion from Phase 2 WU 2.8).

### Positive observations

- TBD.
