# Phase 4 walkthrough — Feature 2 log

## Identity

- **Walkthrough:** Phase 4, WU 4.6
- **Feature:** `FEAT-2026-0009` — Bulk widget creation endpoint (POST /widgets/bulk)
- **Shape chosen:** Regression cycle + qa-regression runtime validation (primary path). Exercises Phase 3 negative-result carry items.
- **Started:** 2026-04-25
- **Operator:** @Bontyyy (human)
- **Orchestration model:** Opus 4.6
- **Specs / PM / QA / component-agent model for subagent sessions:** Sonnet 4.6
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
- **Specs repo:** [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample)
- **Agent versions at execution:** specs 1.0.0, PM 1.6.3 (frozen), component 1.5.2 (frozen), QA 1.5.2 (frozen)
- **Status:** complete — feature reached `state: done`. 34 events, all validated. Regression cycle exercised via fallback. Q4 invariant held. Phase 3 carry items resolved.

## Pre-walkthrough setup

Inputs from Feature 1 — F1 artifacts present in repos.

## Skill invocations — happy-path block (S1–S9)

### Step 1 — Specs agent feature-intake (S1)

- **Output:** `/features/FEAT-2026-0009.md` (state=drafting), `feature_created` event. Ordinal resolution: max=0008, candidate=0009, collision check passed.
- **Friction:** SKILL.md worked example stale (still shows max=0007). Temp path naming discrepancy (minor). No core-path friction.
- **Duration:** ~105s, 31 tool uses.

### Step 2 — Specs agent spec-drafting (S2)

- **Output:** Feature narrative at specs-sample `/product/features/FEAT-2026-0009.md` with AC-1 (bulk create → 201), AC-2 (>50 items → 400 + batch_size_exceeded), AC-3 (any validation failure → 422 + batch_validation_failure + failures[] with index+reason, zero persisted). Registry body populated.
- **Friction:** No `specs/` subdirectory in product repo (would be needed for OpenAPI files). Registry vs narrative compression guidance absent in SKILL.md. Heading naming inconsistency (Feature summary vs Overview).
- **Duration:** ~92s, 21 tool uses.

### Step 3 — Specs agent spec-validation (S3)

- **Output:** 3 events emitted, state transitioned `drafting → validating → planning`. Specfuse CLI not installed (simulated pass, same as F1).
- **Friction:** trigger value discrepancy (SKILL.md uses `human_requested_validation`/`validation_clean`, preamble uses `validation_requested`/`validation_passed`). Cross-feature evidence with F1 F4.3 — **confirms this is a real doc gap, not a one-off.**
- **Duration:** ~141s, 33 tool uses.

### Step 4 — PM task-decomposition (S4)

- **Output:** 4-task graph matching pre-computed expected. `task_graph_drafted` event emitted. State remains planning.
- **Friction:** Capability count ambiguity (3 ACs, 1 endpoint = 1 capability). Cross-feature with F1 F4.6.
- **Duration:** ~144s, 28 tool uses.

### Step 5 — Human plan_review (S5)

- **Actions:** Added required_templates, transitioned planning → plan_review → generating, emitted 2 events. 7 events total.
- **Friction:** None.

### Step 6 — PM template-coverage-check (S6)

- **Skipped for walkthrough efficiency** — same clean result as F1 (identical template surface). Noted as abbreviation, not a finding.

### Step 7 — PM issue-drafting (S7)

- **Output:** 4 issues (#29 T01, #30 T02, #31 T03, #32 T04) + 7 events. State → in_progress.

  | Task | Issue | Labels |
  |---|---|---|
  | T01 | [#29](https://github.com/Bontyyy/orchestrator-api-sample/issues/29) | type:implementation, state:ready, feature:FEAT-2026-0009 |
  | T02 | [#30](https://github.com/Bontyyy/orchestrator-api-sample/issues/30) | type:qa_authoring, state:ready |
  | T03 | [#31](https://github.com/Bontyyy/orchestrator-api-sample/issues/31) | type:qa_execution, state:pending |
  | T04 | [#32](https://github.com/Bontyyy/orchestrator-api-sample/issues/32) | type:qa_curation, state:pending |

- **"First round" semantics:** `generating → in_progress` emitted at 16:42:31Z, **after T01's task_created (16:42:29Z) + task_ready (16:42:30Z) but BEFORE T02/T03/T04 task_created events**. This is "first task opened" semantics — different from F1 where the transition fired after all 4 tasks. The SKILL.md §Step 12 guard ("first invocation to successfully append a task_created") explains this: the guard was checked after T01 was appended and satisfied immediately, so the transition fired before the remaining issues were opened.
- **AC-3 in issue body:** Confirmed T01 issue #29 body contains full AC-3 text with atomicity + failures[] requirements. The trap is set.
- **Friction:** Same as F1 — plan file absent, TLS sandbox, spec path search.
- **Duration:** ~456s, 100 tool uses.

### Step 8 — Component implementation T01 (S8)

- **Output:** [PR #33](https://github.com/Bontyyy/orchestrator-api-sample/pull/33), branch `feat/FEAT-2026-0009-T01-bulk-creation`. Implements POST /widgets/bulk with **correct atomicity** (validate-all-before-persist) and correct failures[] array. 91/91 tests pass, 99.6% coverage, all 6 gates green.
- **REGRESSION TRAP OUTCOME:** Component agent implemented AC-3 correctly on first pass — **same outcome as Phase 3**. Atomicity + per-item failures[] both correct. The two-layer trap did not trigger a natural regression.
- **Duration:** ~434s, 75 tool uses.

### Step 9 — Human merge T01 + fallback regression (S9)

- **Actions:**
  1. Merged PR #33 (commit `2bd471d`).
  2. **FALLBACK PATH EXERCISED:** Manually introduced regression commit `bba7afa` to main. Changed `BulkCreateAsync` from validate-all-first to interleaved validate+persist — valid items before an invalid one are now persisted, breaking atomicity. Branch protection temporarily disabled to push directly.
  3. Emitted `task_completed` event for FEAT-2026-0009/T01 (emitted by component agent during S8).
- **Regression details:** The regression interleaves validation and persistence in a single loop. Items that pass validation are persisted immediately. When an invalid item is encountered, the failure is recorded but previously-valid items are already in the repository. The `failures[]` array is still correct (index + reason), but the zero-persistence guarantee of AC-3 is violated.
- **Honest documentation:** This is the fallback path. The component agent (Sonnet 4.6) implemented AC-3's atomicity correctly on the first pass — it separated validation from persistence with an explicit comment "// Validate all items first — atomicity requires no persistence on any failure." The walkthrough operator introduced the regression to exercise the qa-regression runtime path per the WU AC.

## Skill invocations — QA + regression block (S10–S20)

### Step 10 — QA qa-authoring T02 (S10)

- **Output:** Test plan at specs-sample `/product/test-plans/FEAT-2026-0009.md` with 5 tests. [PR #5 on specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample/pull/5). Events emitted: task_started + test_plan_authored (test_count=5).
- **Critical test:** `widgets-bulk-create-atomicity` — verifies GET /widgets/count unchanged after mixed batch. This is the test that catches the regression.
- **Friction:** None.

### Step 11 — Human merge T02 (S11)

- **Actions:** Merged PR #5 on specs-sample. Emitted task_completed for T02.

### Step 12 — PM dependency-recomputation (S12)

- **Actions:** Emitted task_ready for T03. 20 events total, all valid.

### Step 13 — QA qa-execution T03 (S13) — FAILURE

- **Input:** Test plan with 5 tests, api-sample at commit `bba7afa` (regression commit).
- **Results:** 4 PASS, 1 FAIL.

  | test_id | result | AC |
  |---|---|---|
  | widgets-bulk-create-single | PASS | AC-1 |
  | widgets-bulk-create-multiple | PASS | AC-1 |
  | widgets-bulk-create-batch-size-exceeded | PASS | AC-2 |
  | widgets-bulk-create-validation-failure-response | PASS | AC-3 (response shape) |
  | **widgets-bulk-create-atomicity** | **FAIL** | **AC-3 (atomicity)** |

- **Failure detail:** `BulkCreateAsync` interleaves validation and persistence. Valid item at index 0 persisted before invalid item at index 1 detected. GET /widgets/count changed from 5 to 6 after mixed batch — atomicity violated.
- **Events:** `task_started` + `qa_execution_failed` (failed_tests: [{test_id: "widgets-bulk-create-atomicity", first_signal: "AssertionError: Atomicity violated: count changed from 5 to 6"}]). 22 events total.
- **Regression path status:** `qa_execution_failed` emitted. **qa-regression skill can now be invoked.**
- **F4.13 finding:** `dotnet test --no-build` produced false-green (91/91 pass) due to stale binary from pre-regression build. HTTP-based atomicity test caught the regression correctly. Finding 8 from Phase 1 manifested in qa-execution context.

### Step 14 — QA qa-regression (S14) — FIRST-EVER RUNTIME EXERCISE

- **Invoked by:** orchestration session via `Agent` subagent, model=sonnet. Re-read rules, QA CLAUDE.md (Q4 invariant section), qa-regression/SKILL.md (full procedure).
- **Input:** `qa_execution_failed` event from S13, feature registry task_graph, event log (22 lines prior).
- **Q4 algorithm:** T03 depends_on=[T01,T02] → filter type=implementation → T01 sole target. Unambiguous case.
- **Idempotence check:** No prior `qa_regression_filed` for (FEAT-2026-0009/T01, widgets-bulk-create-atomicity). First-failure path.
- **Output:**
  - Inbox artifact: `/inbox/qa-regression/FEAT-2026-0009-widgets-bulk-create-atomicity.md` — contains test_id, first_signal, reproduction steps, regression context.
  - Event: `qa_regression_filed` — implementation_task_correlation_id=FEAT-2026-0009/T01, test_id=widgets-bulk-create-atomicity, failing_commit_sha=bba7afa..., regression_inbox_file=inbox/qa-regression/FEAT-2026-0009-widgets-bulk-create-atomicity.md
- **Q4 compliance:** CONFIRMED — zero writes to T01's issue (#29). Only outputs: inbox file + event. No labels, no comments, no state changes on original implementation task.
- **Verification:** validate-event.py exit 0 (envelope + per-type qa_regression_filed.schema.json). 23 events total.
- **Friction:** 2 items:
  - (1) `/tmp` blocked by sandbox — used $TMPDIR. SKILL.md should use $TMPDIR.
  - (2) Test plan location required filesystem search — no repo-path artifact in feature registry.
- **Phase 3 carry item resolved:** qa-regression skill exercised at runtime. The skill executed cleanly on first invocation.
- **Duration:** ~297s, 39 tool uses.

### Step 15 — Human Q4 audit + spawn fix task (S15)

- **Q4 audit:**
  - T01 issue #29: 0 comments, labels unchanged (state:in-review, type:implementation, autonomy:review, feature:FEAT-2026-0009). **No unauthorized writes by qa-regression session.**
  - Only outputs from S14: inbox file + event. Q4 invariant HELD.
- **Fix task spawned:** [Issue #34](https://github.com/Bontyyy/orchestrator-api-sample/issues/34) — FEAT-2026-0009/T05 (type:implementation, state:ready).
- **Events:** task_created + task_ready for T05. 25 events total, all valid.

### Step 16 — Component implementation T05 regression fix (S16)

- **Output:** [PR #35](https://github.com/Bontyyy/orchestrator-api-sample/pull/35), branch `fix/FEAT-2026-0009-T05-bulk-atomicity`. Restores two-pass validate-then-persist pattern. 91/91 tests pass, all 6 gates green.
- **Duration:** ~344s, 48 tool uses.

### Step 17 — Human merge T05 fix (S17)

- **Actions:** Merged PR #35 (commit `c6a9138`). Emitted task_completed for T05. 28 events total.

### Step 18 — QA qa-execution re-run T03 (S18)

- **Output:** All 5 tests PASS including `widgets-bulk-create-atomicity`. `qa_execution_completed` emitted with commit_sha=c6a91380... (post-fix). Atomicity confirmed: GET /widgets/count unchanged after mixed batch.
- **Duration:** ~903s, 43 tool uses.

### Step 19 — QA qa-regression resolution (S19)

- **Output:** `qa_regression_resolved` emitted. Links filed event (17:33:07Z) → resolving qa_execution_completed (17:58:33Z). `escalation_resolved` correctly omitted (no prior human_escalation).
- **Phase 3 carry item resolved:** Q4 cross-attribution resolution path exercised for the first time.
- **Duration:** ~72s, 16 tool uses.

### Step 20 — QA qa-curation + human close (S20)

- **Actions:** Emitted task_completed for T03, task_started + task_completed for T04 (empty curation), feature_state_changed(in_progress → done). Registry state=done.
- **Final validation:** 34 events, all validate exit 0. Frontmatter validates exit 0.

## Regression path documentation

### Was qa-regression exercised naturally or via fallback?

**Fallback path exercised.** Sonnet 4.6 implemented AC-3's atomicity correctly on first pass (same as Phase 3). The walkthrough operator manually introduced a regression (commit `bba7afa`) by refactoring `BulkCreateAsync` to interleave validation and persistence. Branch protection was temporarily disabled to push the regression. Documented honestly.

**Design observation:** Explicit ACs with error codes and response structure details are implemented faithfully by Sonnet 4.6. Future regression traps should target IMPLICIT behavior (ordering, concurrency, resource cleanup) rather than explicitly described edge cases.

### Q4 cross-attribution audit

| Artifact | Location | Wrote to T01 issue #29? | Q4 compliant? |
|----------|----------|---------------------|---------------|
| Inbox artifact | `/inbox/qa-regression/FEAT-2026-0009-widgets-bulk-create-atomicity.md` | NO | YES |
| qa_regression_filed event | `events/FEAT-2026-0009.jsonl` line 23 | NO | YES |
| qa_regression_resolved event | `events/FEAT-2026-0009.jsonl` line 30 | NO | YES |
| T05 issue #34 | `Bontyyy/orchestrator-api-sample#34` | NO (human-created) | YES |
| T05 fix PR #35 | `Bontyyy/orchestrator-api-sample#35` | NO (component agent) | YES |

**T01 issue #29:** 0 comments, labels unchanged. Zero QA-originated writes during the entire regression cycle.

### qa-regression runtime validation

The qa-regression skill produced correct artifacts on its first-ever runtime invocation:
1. Correct inbox artifact with test_id, first_signal, reproduction steps, regression context
2. Correct `qa_regression_filed` event (validates against per-type schema)
3. Correct `qa_regression_resolved` event (validates against per-type schema, chronological post-dating confirmed)
4. Correct omission of `escalation_resolved` (no prior human_escalation)

### Q4 cross-attribution resolution path

The QA agent filed a NEW implementation task (T05) via the inbox mechanism — wrote to `/inbox/qa-regression/`, human spawned issue #34. The QA agent did NOT write labels or state to the original T01 implementation task (#29). The Q4 invariant held throughout.

## Observations

### "First round" semantics

F2: `generating → in_progress` fired after T01's task_created only (16:42:31Z, before T02-T04). This is "first task opened" per WU 3.10 v1.
F1: fired after all 4 task_created events (coincidental batching).
**Conclusion:** The v1 "first-task-opened" semantics is what the SKILL.md specifies and F2 demonstrates. F1's "all tasks opened" was coincidental timing, not a different semantic.

### Specs-to-PM handoff

Clean in both features. `validating → planning` produced correct state + event; PM picked up without manual state-bumping. Cross-feature confirmation.

## Findings

- **F4.13:** `dotnet test --no-build` false-green against stale binary. Phase 1 Finding 8 in qa-execution context. Medium.
- **F4.14:** Sonnet 4.6 implements explicit ACs correctly. Regression trap must target implicit behavior. Design observation.
- **F4.15:** Branch protection + comprehensive tests blocked regression fallback. Admin override required. Medium.
- **F4.16:** trigger field value discrepancy confirmed cross-feature (F4.3). Doc gap.

### Positive observations

- **P6:** qa-regression skill clean on first-ever runtime invocation.
- **P7:** Q4 invariant held across full regression cycle.
- **P8:** Component agent fixed atomicity correctly.
- **P9:** qa_regression_resolved links correctly.
- **P10:** escalation_resolved correctly omitted.
