# Phase 3 walkthrough — Feature 2 log (backup-pivoted)

## Identity

- **Walkthrough:** Phase 3, WU 3.6
- **Feature:** `FEAT-2026-0007` — widgets list with pagination (single-repo)
- **Shape chosen:** regression cycle primary (per WU 3.6 AC #2). **Pivoted at S10 to the backup candidate** — qa-curation suite-growth stress — per criterion (a) below. Regression loop (Steps 11–17 in the original plan) was NOT exercised because the component agent implemented AC-3 correctly on the first pass; no `qa_execution_failed` was produced to trigger `qa-regression`.
- **Started:** 2026-04-24 (prep committed 2026-04-23 via PRs [#36](https://github.com/clabonte/orchestrator/pull/36) + [#37](https://github.com/clabonte/orchestrator/pull/37); F1 shipped 2026-04-24 via PR [#38](https://github.com/clabonte/orchestrator/pull/38))
- **Operator:** @Bontyyy (human)
- **Orchestration model:** Opus 4.7
- **QA / PM / component-agent model for subagent sessions:** Sonnet 4.6 (no per-session override — per WU 3.6 proposal §6 discipline)
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
- **Specs repo:** [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample) (stood up in F1 prep; no re-setup needed)
- **Agent versions at execution:** QA 1.4.0, PM 1.6.0 (frozen), component 1.5.0 (frozen)
- **Status:** ✅ backup-path complete — feature reached `state: done`. Regression-cycle contract validation is a negative result (not exercised) + dedup/orphan-refused/rename curation paths validated via seeded fixtures.

## Inputs from Feature 1

- F1 ended with specs-sample main at commit `6ca7784` carrying 1 test plan at `/product/test-plans/FEAT-2026-0006.md`.
- F1 ended with `Bontyyy/orchestrator-api-sample` main at commit `6114339` carrying the `GET /widgets/count` endpoint.
- F1 findings triaged to `docs/walkthroughs/phase-3/feature-1-log.md` §Findings.

## Pre-walkthrough setup

No new setup for F2 beyond what F1 left in place — specs-sample repo stood up, F2 feature registry entry `FEAT-2026-0007.md` seeded ahead via PR [#36](https://github.com/clabonte/orchestrator/pull/36), specs-sample feature narrative at `/product/features/FEAT-2026-0007.md` carrying AC-1 / AC-2 / AC-3 already present (AC-3 = `page_size > 500 → HTTP 400 + error.code=page_size_over_limit` being the edge-case plausible-to-miss per the F2 design).

Confirmed frozen surfaces untouched: no commits on `agents/pm/*`, `agents/component/*`, or `shared/rules/*` since Phase 2 freeze (commit `8125a86`). Phase 2 freeze contract upheld throughout F2.

## Skill invocations — happy-path block (Steps 1–10)

### Step 1 — PM task-decomposition on FEAT-2026-0007

- **Invoked by:** orchestration session (Opus 4.7) via `Agent` subagent, `subagent_type=general-purpose`, `model=sonnet`, fresh context. Re-read `/shared/rules/*`, PM CLAUDE.md (v1.6.0 frozen), task-decomposition/SKILL.md per role-switch-hygiene.
- **Input:** `features/FEAT-2026-0007.md` (state=planning, task_graph=[]), spec at specs-sample `/product/features/FEAT-2026-0007.md`.
- **Output:** task_graph written back to feature frontmatter + `task_graph_drafted` event emitted. `state: planning` preserved.

  | id | type | depends_on | assigned_repo |
  |---|---|---|---|
  | T01 | implementation | [] | Bontyyy/orchestrator-api-sample |
  | T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample |
  | T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample |
  | T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample |

  Exact match to pre-computed expected graph in `notes-scratch.md §1`. No divergence.
- **Verification:** `validate-event.py` exit 0 (envelope-only — `task_graph_drafted` has no per-type schema); `validate-frontmatter.py` exit 0; `source_version` 1.6.0 from `read-agent-version.sh pm`; re-read confirms event on disk.
- **Friction:** 4 items — **F3.25 (new)** validate-event.py rejects pretty-printed JSON (JSONL is line-by-line — one verification cycle burned on first attempt); autonomy rule 1 conditional phrasing required double-pass (minor); ACs-as-behaviors vs ACs-as-test-cases distinction not explicit in SKILL.md (minor); `decomposition_pass = 1` required verifying file non-existence (trivial).
- **Duration:** ~3 min, 30 tool uses.

### Step 2 — Human plan_review transition (manual, orchestration session)

- **Actor:** Opus 4.7 orchestration. Per WU 3.6, skip dedicated plan-review skill and simulate Phase A edits inline.
- **Actions:**
  1. Edited `features/FEAT-2026-0007.md` frontmatter to add `required_templates` per task (T01: `[api-controller, api-request-validator, api-response-serializer]`, T02: `[test-plan]`, T03/T04: `[]`).
  2. Changed `state: planning → state: generating` (skipped transient `plan_review` in frontmatter; events cover canonical trajectory).
  3. Emitted `feature_state_changed(planning → plan_review, trigger=plan_ready)` at 19:28:07Z then `feature_state_changed(plan_review → generating, trigger=plan_approved)` at 19:28:17Z. source: human, source_version: 0606c04 (short SHA).
- **Friction:** **F3.26 (new)** payload schema uses `from_state` / `to_state` (not `from` / `to`) — I (Opus orchestration) hit this validation error on first attempt. One verification cycle burned. Cross-reference: F1 S2 also noted re-reading the schema; F2 concretely exercised the validation failure.

### Step 3 — PM template-coverage-check on FEAT-2026-0007

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** feature registry (state=generating, task_graph + required_templates populated); api-sample `.specfuse/templates.yaml` declaring `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`.
- **Output:** 1 `template_coverage_checked` event. Coverage clean across all 4 tasks (all required tokens present in provided set; T03/T04 trivially satisfy with `[]`).
- **Verification:** validate-event.py exit 0 (envelope + per-type schema); source_version 1.6.0.
- **Friction:** 4 items — **F3.27 (new, minor)** SKILL.md entry-condition check expects `state == planning`, but walkthrough scaffolding runs the skill after `plan_review → generating` transition (same pattern as F1); gh-api vs local-filesystem fetch dual-path in SKILL.md (observation); blank lines in JSONL tolerated by validator (observation); `task_count` field name slightly misleading (counts all tasks including trivially-satisfied).
- **Duration:** ~2 min, 26 tool uses.

### Step 4 — PM issue-drafting on FEAT-2026-0007

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** feature registry + work-unit-issue.md template v1.1 + issue-drafting-spec.md contract.
- **Output:** 4 GitHub issues opened on `Bontyyy/orchestrator-api-sample` ([#18 T01 impl ready](https://github.com/Bontyyy/orchestrator-api-sample/issues/18), [#19 T02 qa-authoring ready](https://github.com/Bontyyy/orchestrator-api-sample/issues/19), [#20 T03 qa-execution pending](https://github.com/Bontyyy/orchestrator-api-sample/issues/20), [#21 T04 qa-curation pending](https://github.com/Bontyyy/orchestrator-api-sample/issues/21)). 6 events emitted (4 `task_created` + 2 `task_ready` on T01, T02). `deliverable_repo: Bontyyy/orchestrator-specs-sample` correctly set on T02 + T04.
- **Verification:** each issue confirmed via `gh issue view` — 5 mandatory ## sections, correct labels, `deliverable_repo` per requirement, `## Deliverables` present iff `deliverable_repo` set. All 6 events validate exit 0.
- **Friction:** 6 items.
  - **F3.7 mitigation stress-tested & CONFIRMED cross-feature:** subagent quote — "My first mental model before reading the F3.7 mitigation clause was 'I should use [clabonte/orchestrator] for T02 and T04.'" The explicit F3.7 mitigation clause in the prompt caught it cleanly. Without the mitigation, subagent would have defaulted to the worked example's target. Cross-feature evidence (F1 + F2) elevates this for Fix-in-Phase-3.
  - **F3.28 (new, CRITICAL operational)** — JSONL append bug from `cat temp_file >> log` pattern when Write tool output has no trailing newline: 6 events concatenated onto a single line on first attempt; subagent detected via `tail -6 | python3 -m json.tool` throwing `JSONDecodeError: Extra data`; recovered by reading file + splitting via `JSONDecoder.raw_decode()` loop. **No canonical JSONL append pattern documented.**
  - **F3.29 (new, significant)** — Missing `/features/FEAT-2026-0007-plan.md`. The SKILL's Step 2 documents reading a plan-review file's `### Work unit prompt` section per task. No such file exists (never produced by the skipped plan-review session). Subagent fell back to deriving work-unit prompts from the feature registry description. In production this would warrant `spec_level_blocker` escalation; subagent proceeded for walkthrough continuity and flagged the gap.
  - T03 and T04 context sections reference `/product/test-plans/FEAT-2026-0007.md` (forward-looking — doesn't exist at issue-draft time). Correctly reformulated with explicit note, per the no-transitive-trust decision tree.
  - `IWidgetRepository.CountAsync` already exists (from F1's FEAT-2026-0006 impl) — scope observation, not a blocker.
  - Work-unit-issue.md template v1.1 carries `# Example: deliverable_repo: clabonte/orchestrator` as a comment — latent risk (a future cold invocation without F3.7 mitigation would follow the comment). Template's example value is Phase-2-era; should be generalized to `<owner>/<repo>` placeholder.
- **Duration:** ~25 min, 84 tool uses.

### Step 5 — Component implementation on T01

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read. Component v1.5.0 frozen surface preserved.
- **Input:** [T01 issue #18](https://github.com/Bontyyy/orchestrator-api-sample/issues/18), api-sample local clone (pulled main to commit `6114339`).
- **Output:** [PR #22 on api-sample](https://github.com/Bontyyy/orchestrator-api-sample/pull/22), branch `feat/FEAT-2026-0007-T01-widgets-pagination`, initial commit. Implements pagination across:
  - `IWidgetRepository.GetListAsync(int pageSize)` abstraction addition
  - `InMemoryWidgetRepository.GetListAsync` implementation using `ConcurrentDictionary.Values.Take(pageSize)`
  - `WidgetService.GetListAsync` with `pageSize > 500` → `ValidationException` guard
  - `WidgetsController` `[HttpGet]` GetList action with catch-ValidationException returning `{"error":{"code":"page_size_over_limit","message":"..."}}`
  - 8 new controller tests (covering AC-1 / AC-2 / AC-3 including 501 / 1000 / MaxValue)
  - 5 new service tests
- **Verification gates — 6/6 PASS:**
  - tests: 47/47 pass, 0.27s
  - coverage: 100% (line coverage 1.00, threshold 0.90)
  - compiler_warnings: 0
  - lint: `dotnet format --verify-no-changes` exit 0 (after cycle 1 fix — see friction)
  - security_scan: 0 high/critical
  - build (Release): 0 warnings
  - Pre-gate step: `dotnet restore && dotnet build` per F3.1 mitigation — no stale-artifact trap hit.
- **Friction:** 4 items.
  - **F3.30 (new, significant)** — cycle 1 lint failure on `DefaultPageSize` naming convention (project-level `.editorconfig` rule IDE1006: `_` prefix for private consts). **Not surfaced in `.specfuse/verification.yml` or any spec** — only manifests at `dotnet format` time, not `dotnet build`. One full verification cycle burned. Corrected to `_defaultPageSize`, cycle 2 all 6 gates green.
  - **F3.1 confirmed (live evidence, second feature):** `--no-build` gate sequencing — after adding new test files, `dotnet test --no-build` against pre-change artifacts would silently run only the original tests. Explicit `dotnet build` between test-writing and test-running is required. F2 explicitly exercised the mitigation; no trap hit. Cross-feature evidence (F1 F3.1 + F2 F3.1) elevates Phase 1 Finding 8 for earlier absorption than the current Phase 5 carry.
  - **F3.31 (new, minor)** — `source: component:<name>` where `<name>` is the bare component repo name (`orchestrator-api-sample`), not `<owner>/<repo>`. Subagent briefly re-read schema to confirm.
  - **P5 (positive observation):** F3.6 per-type schema mitigation — subagent explicitly read `task_started.schema.json` before constructing payload; no re-do needed. The cross-reference clause in F2 preamble is effective.
  - **CRITICAL for F2 shape:** The component agent implemented AC-3 **correctly on first pass**. The regression-cycle primary path requires an AC-3 miss; this pass signals the backup branch will activate at S10.
- **Duration:** ~6 min, 55 tool uses.

### Step 6 — Human merges T01 PR (manual, orchestration session)

- **Actor:** human operator reviewed [PR #22](https://github.com/Bontyyy/orchestrator-api-sample/pull/22), CI `verification gates` workflow SUCCESS.
- **Actions:** squash-merged + deleted branch. api-sample main HEAD moved `6114339 → 1a6dfd703c6717b3a73195934cbd6a921b118f3a`. T01 issue #18 auto-closed via `Closes` directive (same-repo); label manually flipped `state:in-review → state:done`.
- **Note:** No second `task_completed` event — S5 subagent emitted at PR-open time per convention.
- **Friction:** none.

### Step 7 — QA qa-authoring on T02

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** [T02 issue #19](https://github.com/Bontyyy/orchestrator-api-sample/issues/19) + feature registry + spec + specs-sample clone.
- **Output:** test plan at `/product/test-plans/FEAT-2026-0007.md` in specs-sample, 3 test entries:
  - `widgets-list-default-page-size-50` (AC-1) — curl `GET /widgets`, expect HTTP 200 + array ≤ 50
  - `widgets-list-explicit-page-size-honored` (AC-2) — curl `GET /widgets?page_size=10`, expect HTTP 200 + array ≤ 10
  - `widgets-list-page-size-over-limit-rejected` (AC-3) — curl `GET /widgets?page_size=501`, expect HTTP 400 + error.code=page_size_over_limit
  - All `commands[]` target `http://localhost:5083` (F3.3 mitigation honored — native launchSettings port).
  - PR [specs-sample#2](https://github.com/Bontyyy/orchestrator-specs-sample/pull/2) opened on branch `qa-authoring/FEAT-2026-0007-T02`.
- **Events emitted:** `task_started` (19:58:04Z) → `test_plan_authored` (20:01:19Z, payload `{plan_path, test_count: 3}`) → `task_completed` (20:02:12Z, payload with PR URL).
- **Verification:** plan round-trips test-plan.schema.json; unique test_ids (3); coverage: every AC covered; all 3 events validate; source_version 1.4.0 fresh per emission.
- **Friction:** 3 items.
  - **F3.2 confirmed cross-feature:** PR-based delivery convention still unspecified in qa-authoring SKILL.md. F2 preamble pinned branch name + commit msg + PR body format + STOP-at-open rule explicitly; subagent followed. Quote: "SKILL.md does not say which repo gets the PR (`-R`), what `--base` to target, or what the PR body should include. Zero ambiguity only because the preamble was authoritative; the gap in SKILL.md is real and would bite a cold invocation." Cross-feature evidence (F1 + F2) elevates for Fix-in-Phase-3.
  - **F3.3 confirmed cross-feature:** Port assumption is a latent `spec_level_blocker` for qa-execution if not mitigated. F2 preamble pinned 5083 (native launchSettings port). Without mitigation, natural fallback is 5000 or 8080 — both wrong. Gap is in the spec (silent on execution port); F3 mitigation candidate: spec conventions for runtime port, OR qa-authoring includes startup command in `commands[]`.
  - **F3.32 (new, minor)** — cardinality wording "expected" in feature registry `## Scope` ("three tests expected under the default cardinality convention") is ambiguous between confirmatory and prescriptive. SKILL §Step 4's collapse-only rule makes prescriptive-expansion reading impossible, so correct interpretation is confirmatory; but the wording required a reasoning step SKILL.md should make explicit.
- **Q4 self-audit:** 10 write actions enumerated — 2× T02 label flip (owned), 3× event appends, 3× specs-sample branch operations, 1× plan file write. No action on non-T02 tasks. Q4 held.
- **Duration:** ~6.5 min, 47 tool uses.

### Step 8 — Human merges qa-authoring PR + closes T02 (manual)

- **Actions:** squash-merged specs-sample PR #2, branch deleted. specs-sample main HEAD: `6ca7784 → b2536bf`. **Observation counter to F1 F3.12:** T02 issue #19 auto-closed via cross-repo `Closes` directive — it worked on Bontyyy/* → Bontyyy/* cross-repo pattern. Manual `state:in-review → state:done` label flip (auto-close doesn't flip labels). See Findings §F3.12-counter.
- **Friction:** the cross-repo auto-close observation contradicts F1's F3.12 claim that auto-close does NOT fire cross-repo. Likely explanation: both repos have the same owner (`Bontyyy`), which makes GitHub treat it as same-org reference — cross-repo Closes works for same-owner, possibly not for different-owner. F1 F3.12 should be reclassified / narrowed to "cross-OWNER" rather than "cross-REPO".

### Step 9 — PM dependency-recomputation (first invocation)

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Trigger:** T02 `task_completed` event (T01 already done from S6).
- **Output:** T03 flipped `state:pending → state:ready` on [issue #20](https://github.com/Bontyyy/orchestrator-api-sample/issues/20). `task_ready` event emitted with `trigger: "task_completed:T02"`.
- **Verification:** validate-event.py exit 0; source_version 1.6.0; `gh issue view 20` post-flip shows `state:ready` present, `state:pending` absent.
- **Friction:** 1 item — **F3.33 (new, minor)** — `tail -1 log | python3 -m json.tool` verification (from F2 preamble clause 5) reads a blank trailing line when the log has a terminal newline separator. Exits 1 on empty-line parse. Suggested mitigation for future preamble revisions: `grep -v '^[[:space:]]*$' <log> | tail -1 | python3 -m json.tool > /dev/null`.
- **Duration:** ~2 min, 34 tool uses.

### Step 10 — QA qa-execution on T03

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** [T03 issue #20](https://github.com/Bontyyy/orchestrator-api-sample/issues/20) + plan at `/product/test-plans/FEAT-2026-0007.md` in specs-sample (post-merge) + api-sample local clone + prescribed `commit_sha = 1a6dfd703c6717b3a73195934cbd6a921b118f3a`.
- **Output:** **`qa_execution_completed`** (envelope feature-level, payload `{task_correlation_id: FEAT-2026-0007/T03, commit_sha: 1a6dfd703c6717..., plan_path: /product/test-plans/FEAT-2026-0007.md, test_count: 3, total_duration_seconds: 5.1}`). `task_started` + `task_completed` on T03. T03 flipped `state:in-progress → state:in-review`.
- **Test execution:**
  - Service started via `dotnet run --project src/OrchestratorApiSample.Api/ --urls "http://localhost:5083"` (PID 44665). Startup ~10s; verified via `GET /widgets/count` returning 200.
  - **Test 1** `widgets-list-default-page-size-50`: HTTP 200 + `[]`. 0 ≤ 50 satisfies. **PASS.**
  - **Test 2** `widgets-list-explicit-page-size-honored`: HTTP 200 + `[]`. 0 ≤ 10 satisfies. **PASS.**
  - **Test 3** `widgets-list-page-size-over-limit-rejected`: HTTP 400 + `{"error":{"code":"page_size_over_limit","message":"page_size must be between 1 and 500; received 501."}}`. error.code exactly matches. **PASS.**
  - Service killed post-test; no process leak.
- **Verification:** plan schema round-trip PASS; idempotence scan fresh (no prior event for (T03, prescribed SHA)); validate-event.py exit 0 (envelope + per-type payload).
- **Friction:** 1 item — **F3.34 (new, minor)** — background task exit signal misleading for persistent processes: `run_in_background: true` on `dotnet run` returned "task completed" immediately (framework detached process), but service wasn't ready yet. Subsequent `sleep + curl` was the actual readiness gate. No correctness impact, cosmetic ambiguity. Observation: background-task completion signal should not be interpreted as "service is ready" for long-running service processes.
- **Q4 self-audit:** 5 write actions — 2× T03 label flip (owned), 3× event appends. No non-T03 task touched. Q4 held.
- **Duration:** ~3 min, 42 tool uses.

## Pivot decision

**Criterion (a) from WU 3.6 proposal §9 triggered at S10:** component agent implemented AC-3 correctly on first pass → `qa_execution_completed` all-pass → no `qa_execution_failed` → no `qa-regression` trigger → Steps 11–17 (first-failure → spawn fix → re-execute → resolved) are not exercisable.

**Decision:** pivot to backup candidate = qa-curation suite-growth stress. Seed 3 fixture plans on specs-sample + 1 `qa_regression_filed` event on orchestrator to exercise dedup / orphan / rename / protection paths.

**Rationale for the "correct-first-try" outcome:** Feature 2's spec explicitly calls AC-3 the "edge-case plausible-to-miss on a first-pass implementation" (feature registry `## Description`), hoping naive implementations would skip structured error-body serialization. The component agent v1.5.0 Sonnet 4.6 subagent read AC-3 literally, added the guard + structured error body + 3 dedicated tests (501 / 1000 / MaxValue) — correct first try. Evidence for the QA loop's design stability: the agent baselines are robust enough that "naive miss" edge cases designed to stress regression cycles can be absorbed by the implementation agent itself. For Phase 3 retro input: walkthrough design for regression-cycle stress needs edge cases that are genuinely subtle, not just "structured JSON rejection" which has a clear literal reading.

## Backup pre-steps — seeding fixtures

### Backup-Pre1 — Close T03 + T04 manual dep-recomp (manual, orchestration session)

- Flipped T03 `state:in-review → state:done` + `gh issue close 20` (same cross-repo pattern as S8).
- Flipped T04 `state:pending → state:ready` on [issue #21](https://github.com/Bontyyy/orchestrator-api-sample/issues/21) + emitted `task_ready` event manually (trigger: `task_completed:T03_manual_dep_recomp`). Skipped a dedicated PM dep-recomp subagent — trivial case already exercised in S9 + F1.
- Friction: none.

### Backup-Pre2 — Seed 3 fixture features + plans on specs-sample

- **Actor:** Opus 4.7 orchestration (me).
- **Files created on specs-sample main via commit `d4276dc`** (chore(walkthrough): seed fixture features and plans for F2 backup):
  - `/product/features/FEAT-2026-9001.md` — fixture feature spec with AC-1 on default 50-widget slice
  - `/product/features/FEAT-2026-9002.md` — fixture with only AC-1 (AC-2 intentionally absent for orphan stress)
  - `/product/features/FEAT-2026-9003.md` — fixture for rename stress
  - `/product/test-plans/FEAT-2026-9001.md` — test `widgets-listing-default-slice-50-count` with covers overlapping FEAT-0007's default-page-size test (dedup candidate)
  - `/product/test-plans/FEAT-2026-9002.md` — 2 tests: one on AC-1 (covered), one on AC-2 (orphan — no corresponding AC)
  - `/product/test-plans/FEAT-2026-9003.md` — test `widgets-archive-old-variant` + `rename-request:` line in prose body (rename candidate)
- All 3 plans round-trip test-plan.schema.json on commit.
- Pushed to specs-sample main directly (no branch protection per F1 observation).

### Backup-Pre3 — Seed qa_regression_filed on FEAT-9002 for protection stress

- Wrote `/inbox/qa-regression/FEAT-2026-9002-widgets-metadata-has-last-updated.md` stub (fixture inbox artifact).
- Wrote `/events/FEAT-2026-9002.jsonl` with 1 `qa_regression_filed` event keyed on `(FEAT-2026-9002/T02, widgets-metadata-has-last-updated)` with `failing_commit_sha: 0000000000000000000000000000000000000002` (fixture placeholder) and `failing_qa_execution_event_ts: 2026-04-20T14:22:17Z`. No paired `qa_regression_resolved` — open regression exercises qa-curation's refusal path per anti-pattern #7.
- Event validates envelope + per-type payload (`qa_regression_filed.schema.json`).

## S19-backup — QA qa-curation on T04 (5-plan corpus)

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** [T04 issue #21](https://github.com/Bontyyy/orchestrator-api-sample/issues/21) + specs-sample local clone (post-seed, HEAD `d4276dc`) + orchestrator event logs for all 5 features.
- **Scan cohort:** 5 plans — FEAT-2026-0006 (F1), FEAT-2026-0007 (S7), FEAT-2026-9001 / 9002 / 9003 (fixtures).
- **Output:** [specs-sample PR #3](https://github.com/Bontyyy/orchestrator-specs-sample/pull/3) opened on branch `qa-curation/FEAT-2026-0007-T04`, commit `676166f` — renames `widgets-archive-old-variant → widgets-archive-id-soft-deleted` in FEAT-9003 plan. `regression_suite_curated` event emitted with payload:
  ```
  scope: rename
  affected_test_ids: [widgets-archive-old-variant, widgets-archive-id-soft-deleted]
  affected_feature_correlation_ids: [FEAT-2026-9003]
  scan_summary: {plans_scanned: 5, regression_events_consulted: 2}
  refused_candidates:
    - {test_id: widgets-metadata-has-last-updated, feature: FEAT-2026-9002,
       reason: "open qa_regression_filed at 2026-04-20T14:24:00Z on FEAT-2026-9002/T02 without matching qa_regression_resolved"}
    - {test_id: widgets-listing-default-slice-50-count, feature: FEAT-2026-9001,
       reason: "schema validation failed on candidate's target plan: removing the sole test from FEAT-2026-9001 would leave tests[] empty, violating test-plan.schema.json minItems:1; whole dedup candidate rolled back"}
  ```
- **Candidate classification:**
  | Kind | Found | Disposition | Why |
  |---|---|---|---|
  | Dedup | 1 (FEAT-9001 vs FEAT-0007 on `covers` overlap) | Refused (rollback) | Retiring FEAT-9001's sole test violates `tests[].minItems: 1` of test-plan.schema.json |
  | Orphan | 1 (FEAT-9002 `widgets-metadata-has-last-updated` on AC-2 absent from feature) | Refused (protection) | Open `qa_regression_filed` without paired `_resolved` on `(FEAT-2026-9002/T02, widgets-metadata-has-last-updated)` — anti-pattern #7 blocks retire |
  | Consolidation | 0 | — | No `qa_execution_failed` clustering signals in 30d/50-event window |
  | Rename | 1 (FEAT-9003 prose `rename-request:` line) | Accepted | No open regression on `widgets-archive-old-variant`; protection passed |
- T04 flipped `state:in-progress → state:in-review`. Events: `task_started` (20:21:46Z) + `task_completed` (20:25:15Z) + `regression_suite_curated` (20:25:34Z).
- **Operator recovery note** — during S19 execution, the orchestration session (Opus 4.7) misinterpreted an IDE system-reminder about the FEAT-9003 plan file modification (the subagent's own rename commit) as an accidental user edit and prematurely interrupted the subagent + closed PR #3. The subagent had in fact completed successfully; events were already on the log. Recovery involved recreating the branch locally from commit `676166f` (preserved in git object store post-`branch -D`), pushing, and reopening PR #3. This is itself an **F3.x operational finding**: walkthrough operator discipline under partial-visibility-of-subagent-state can produce false rejection decisions. See Findings §F3.35.
- **Verification (reconstructed from artifacts):** regression_suite_curated event validates envelope + per-type payload; all 3 T04 events validate. PR #3 = 1-line diff on FEAT-9003 plan test_id. Q4 invariant held (no non-T04 label flips per commit content + event payload inspection).
- **Friction:** 3 items (reconstructed — subagent report not captured due to premature rejection).
  - **F3.36 (new, significant)** — qa-curation dedup/orphan retirement can violate `test-plan.schema.json` `tests[].minItems: 1` when the candidate is the sole test in its plan. SKILL.md does not document this pre-flight check; the subagent discovered the constraint at commit time and rolled back the whole dedup candidate (recorded in `refused_candidates[]` with explicit schema-violation reason — clean behavior). Retrospective disposition candidate: document the `minItems: 1` pre-flight in qa-curation SKILL.md §Step 4, OR relax test-plan schema to allow empty plans (no — the stable identifier requirement prevents this), OR specify that an orphan retirement targeting a sole-test plan requires the plan file to be deleted as a whole rather than just removing the test entry.
  - **Positive observation P6:** open-regression protection path exercised as designed — scan found open `qa_regression_filed` (from backup seed) + no paired `_resolved`, refused orphan retire, recorded in `refused_candidates[]`. Clean behavior per anti-pattern #7.
  - **Positive observation P7:** rename candidate detection via `rename-request:` prose line worked cleanly; subagent retired-old + added-new in a single test plan diff per the documented pattern.
- **Duration (reconstructed from event timestamps):** ~4 min (task_started 20:21:46Z → regression_suite_curated 20:25:34Z). Tool-use count not captured.

## S20 — Human closes T04 + feature done (manual)

- Flipped T04 `state:in-review → state:done`; issue #21 auto-closed via cross-repo `Closes Bontyyy/orchestrator-api-sample#21` in specs-sample PR #3 body (same same-owner pattern observed in S8).
- Retro-emitted `feature_state_changed(generating → in_progress, trigger=first_round_issues_opened_retroactive)` at 20:35:25Z to close the F3.4 gap (same as F1 S14 pattern — the transition has no skill owner in v1; **cross-feature evidence**).
- Emitted `feature_state_changed(in_progress → done, trigger=all_tasks_done)` at 20:35:35Z.
- Updated feature frontmatter `state: generating → state: done` + re-validated. Final event log count: 25 events, all validate.
- **Verification:** full event log re-validation exit 0 (25 events); frontmatter re-validates; all 4 issues CLOSED + `state:done`.

## Q4 invariant audit (WU 3.6 AC #6)

Per WU 3.6 AC #6, a specific enumeration is required. For each QA-originated write action across F2 — including the backup branch — recorded below: which session performed it, what was written, which correlation ID it targeted, what type that target was, and whether the action was role-owned.

Collection method: for each QA session (S7, S10, S19), the orchestration session reviewed the subagent's reported Q4 self-audit (S7 enumerated 10 actions; S10 enumerated 5) and cross-checked against the event log + GitHub API for label/state changes on any task. For S19 specifically, the Q4 audit is reconstructed from: (a) the commit `676166f` diff (only FEAT-9003 plan rename, no label operations); (b) the 3 events emitted on T04 (task_started, task_completed, regression_suite_curated — all correctly scoped); (c) absence of any `gh issue edit` trace on non-T04 issues (verified via issue labels post-session).

| Session | Write action | Target correlation_id | Target type | Verdict |
|---|---|---|---|---|
| qa-authoring (S7) | label flip `state:ready → state:in-progress` | `FEAT-2026-0007/T02` | qa_authoring (owned) | ✅ |
| qa-authoring (S7) | branch + commit on specs-sample `qa-authoring/FEAT-2026-0007-T02` | file, not task | — | ✅ (authorized QA deliverable repo) |
| qa-authoring (S7) | write `/product/test-plans/FEAT-2026-0007.md` | file, not task | — | ✅ |
| qa-authoring (S7) | PR open on specs-sample (#2) | PR, not task | — | ✅ |
| qa-authoring (S7) | emit `task_started` + `test_plan_authored` + `task_completed` events | `FEAT-2026-0007` (feature-level for test_plan_authored) + `FEAT-2026-0007/T02` (task-level for task_*) | feature / T02 (owned) | ✅ |
| qa-authoring (S7) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T02` | qa_authoring (owned) | ✅ |
| qa-execution (S10) | label flip `state:ready → state:in-progress` | `FEAT-2026-0007/T03` | qa_execution (owned) | ✅ |
| qa-execution (S10) | emit `qa_execution_completed` event | `FEAT-2026-0007` (feature-level) | feature-level event | ✅ |
| qa-execution (S10) | emit `task_started` + `task_completed` | `FEAT-2026-0007/T03` | T03 (owned) | ✅ |
| qa-execution (S10) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T03` | qa_execution (owned) | ✅ |
| qa-curation (S19) | label flip `state:ready → state:in-progress` | `FEAT-2026-0007/T04` | qa_curation (owned) | ✅ |
| qa-curation (S19) | branch + commit on specs-sample `qa-curation/FEAT-2026-0007-T04` | file, not task | — | ✅ (authorized QA deliverable repo) |
| qa-curation (S19) | edit `/product/test-plans/FEAT-2026-9003.md` (rename test_id) | file, not task | — | ✅ (plan file edit via PR, not destructive inline — anti-pattern #8 respected) |
| qa-curation (S19) | PR open on specs-sample (#3) | PR, not task | — | ✅ |
| qa-curation (S19) | emit `task_started` + `task_completed` + `regression_suite_curated` | `FEAT-2026-0007/T04` (task-level for task_* + regression_suite_curated per envelope convention) | T04 (owned) / feature-level (regression_suite_curated) | ✅ |
| qa-curation (S19) | label flip `state:in-progress → state:in-review` | `FEAT-2026-0007/T04` | qa_curation (owned) | ✅ |

**Expected violations to rule out (per feature-2-log skeleton):**
| Would-be action | Check | Verdict |
|---|---|---|
| label flip on T01 impl task from any QA session | `gh issue view 18 --json labels` inspected at end — `state:done` flipped only by S6 manual + type:implementation + autonomy:review. No qa-* label anomaly. | ✅ NOT PRESENT |
| issue body edit on T01 from any QA session | `gh issue view 18 --json body` final = S4-drafted body unchanged. | ✅ NOT PRESENT |
| label flip on T02 impl task (conceptual — would be wrong-role) | S7 qa-authoring only touched its own T02 label (two transitions, role-owned). | ✅ NOT PRESENT |
| cross-task label flip by S11 qa-regression (regression loop didn't execute) | S11–S17 skipped per backup pivot. No action. | ✅ N/A |

**Q4 invariant: HELD across F2.** No QA-originated write touched labels or state on any task other than the session's own QA task. **Cross-feature evidence (F1 informal + F2 formal audit)** confirms the invariant is stable under the current QA skill implementations. The Q4 cross-attribution resolution path (SKILL §"Deferred — cross-attribution resolution") was not exercised because the regression loop did not trigger — carry to Phase 4 for qa_regression path validation.

## Outcome

- **F2 acceptance per WU 3.6 AC #2 (regression cycle primary):** ⚠️ **NOT EXERCISED.** The regression-cycle primary path did not trigger because the component agent implemented AC-3 correctly on first pass. The backup candidate (qa-curation stress) was activated per the documented criterion (a).
- **F2 acceptance per WU 3.6 AC #2 (backup candidate):** ✅ met. qa-curation exercised against a 5-plan corpus; dedup refused (schema edge case), orphan refused (protection), rename accepted, curation PR merged, `regression_suite_curated` event emitted with complete refused_candidates enumeration.
- **F2 acceptance per WU 3.6 AC #6 (Q4 audit):** ✅ met. Specific enumeration above; invariant held.
- **F2 acceptance per WU 3.6 AC #3 (honest logs):** ✅ met. Friction recorded verbatim including operator-level F3.35 (premature rejection of successful subagent); no sanitization.
- **F2 acceptance per WU 3.6 AC #5 (events validate):** ✅ met. 25 events on feature log, all validate.
- **End state:**
  - Feature registry `state: done`, frontmatter schema-valid.
  - Event log: 25 events, all round-trip through `validate-event.py`.
  - 4 issues on api-sample CLOSED + `state:done`.
  - 2 merged PRs: api-sample#22 (impl), specs-sample#2 (test plan), specs-sample#3 (curation rename).
  - 3 fixture features + 3 fixture plans persist on specs-sample main (option A per walkthrough decision — kept permanent as demo artifacts, documented in commit `d4276dc` message).
  - 1 fixture inbox artifact + 1 fixture `qa_regression_filed` event persist on orchestrator (fixture seed for protection stress).
- **Findings captured:** 12 new F3.25–F3.36 items + 3 cross-feature confirmations (F3.1, F3.2, F3.3, F3.4, F3.7 now have 2-feature evidence → elevated for Fix-in-Phase-3 triage) + 1 counter-evidence (F3.12 cross-repo auto-close works for same-owner) + 3 positive observations (P5–P7). Full list below.
- **Commit:** `chore(phase-3): walkthrough feature 2 complete` (per WU 3.6 AC #7).

## Findings summary

Findings numbered F3.25–F3.36 continuing from F1's F3.1–F3.24. Severity scale: **High** = hard gate on Phase 4 / blocks retro close; **Medium** = likely Fix-in-Phase-3; **Low** = Defer / Observation. Final disposition is WU 3.7's triage.

### Cross-feature confirmed findings (F1 + F2 — elevated for Fix-in-Phase-3)

These findings surfaced in both F1 and F2 (or F1 latent + F2 live evidence). Per WU 3.7 triage criteria (mirror of Phase 2 WU 2.8: "2-feature evidence elevates for Fix-in-Phase-3"), these should be prioritized in the Phase 3 fix ladder.

- **F3.1 (live evidence, second feature)** — `--no-build` gate sequencing: component agent must run `dotnet restore && dotnet build` before test gates (`--no-build`) or stale artifacts silently skew the run. F2 S5 subagent exercised the mitigation explicitly; no trap hit. F1 S5 flagged the same pattern. **2-feature evidence.** Retrospective disposition candidate: Fix-in-Phase-3 — amend `verification/SKILL.md` with explicit pre-gate build step OR update `verification.yml` schema requiring a `build` gate before `--no-build` gates.
- **F3.2 (confirmed cross-feature)** — qa-authoring PR-based delivery convention unspecified in SKILL.md: F2 subagent quote: "SKILL.md does not say which repo gets the PR, what `--base` to target, or what the PR body should include." Both F1 S7 and F2 S7 needed explicit prompt pinning. Retrospective disposition candidate: Fix-in-Phase-3 — add `## Delivery convention` section to qa-authoring SKILL.md.
- **F3.3 (confirmed cross-feature)** — port convention between qa-authoring plan commands and component service: F2 observed in the spec's silence on runtime port (subagent quote: "without mitigation, natural fallback would be 5000 or 8080 — both wrong"). F1 S10 hit port mismatch plan-5000 vs launchSettings-5083. **2-feature evidence.** Retrospective disposition candidate: Fix-in-Phase-3 — qa-authoring includes startup command in `commands[]` OR test-plan.schema.json adds `preconditions` field OR documented spec convention for runtime env.
- **F3.4 (confirmed cross-feature)** — `feature_state_changed(generating → in_progress)` transition has no skill owner: F2 S20 retro-emitted with trigger `first_round_issues_opened_retroactive`, same as F1 S14. The transition was skipped both times. **2-feature evidence.** Retrospective disposition candidate: Fix-in-Phase-3 — add the emission to issue-drafting SKILL.md Step (after first round of task_created/task_ready events).
- **F3.5 mitigation HELD in F2** — F2 preamble clause 1 ("Do NOT `git commit` on orchestrator repo") was effective: 0 subagent commits on orchestrator repo vs F1's 4 unauthorized commits. Cross-feature proof that the mitigation is sufficient as a prompt clause. Retrospective disposition candidate: absorb the clause into `/shared/rules/` (verify-before-report.md §3 or new rule file) OR into each role's CLAUDE.md for event-writing discipline.
- **F3.6 (confirmed cross-feature, schema discoverability)** — per-type event payload schemas not cross-referenced from CLAUDE.md / SKILL.md. F2 preamble clause 3 (cross-reference schema paths explicitly) was effective; subagents hit schema issues only when payloads were constructed without reading the schema first (see also F3.26 in F2). Cross-feature: F1 F3.6 had 3 recurring instances; F2 F3.6 subagents with the preamble hint had 0 instances. **Mitigation effectiveness confirmed.** Retrospective disposition candidate: Fix-in-Phase-3 — cross-reference per-type schema paths from each event type's name in CLAUDE.md / SKILL.md.
- **F3.7 (confirmed + elevated)** — issue-drafting SKILL.md worked example's `deliverable_repo: clabonte/orchestrator`: F2 S4 subagent explicitly noted initial mental model would have been `clabonte/orchestrator` without the F3.7 preamble mitigation. The work-unit-issue.md v1.1 template's example comment is a secondary latent risk. **2-feature evidence.** Retrospective disposition candidate: Fix-in-Phase-3 — update SKILL.md worked example and template comment to generic `<owner>/<repo>` placeholder, OR explicit note about Phase-2-era convention.
- **F3.10 (cross-feature via mitigation)** — validate-event.py /dev/stdin broken on macOS. F2 preamble clause 4 codified the `--file` workaround; 0 occurrences in F2. F1 had 4+ recurring. **Mitigation sufficient** but the root cause (broken stdin handling) persists. Retrospective disposition candidate: Fix-in-Phase-3 light — either fix validate-event.py stdin on macOS OR promote `--file` pattern to canonical docs.
- **F3.11 (cross-feature)** — SKILL.md files exceeding 25k read limit: F2 S4 (issue-drafting) + F2 S19 (qa-curation) both chunked reads. F1 same. **2-feature evidence** but low severity. Retrospective disposition candidate: Defer or opportunistic trim.
- **F3.12 (counter-evidence from F2)** — cross-repo `Closes` directive. F1 claimed it does NOT auto-close (required manual `gh issue close`). F2 observed it DID auto-close for T02 #19 and T04 #21 via specs-sample PRs #2 and #3. Both PRs referenced `Closes Bontyyy/orchestrator-api-sample#N`. **Same-owner (Bontyyy/* → Bontyyy/*) cross-repo Closes apparently does auto-fire.** F1's F3.12 should be reclassified / narrowed to "cross-OWNER" rather than "cross-REPO". Retrospective disposition candidate: update F3.12 severity and applicability per F2 counter-evidence; likely keep as observation (no action needed since same-owner behavior is what Bontyyy/* ecosystem uses).

### New findings specific to F2

- **F3.25 (Medium)** — `validate-event.py` rejects pretty-printed JSON. The F2 preamble clause 4 instructed use of `--file /tmp/event.json`, but didn't warn that JSON must be single-line JSONL. F2 S1 subagent first attempt used pretty-printed JSON → 12 validation errors (one per line). One verification cycle burned. Retrospective disposition candidate: Fix-in-Phase-3 — update preamble clause 4 / verify-before-report.md §3 to specify single-line JSONL format explicitly.
- **F3.26 (Medium)** — `feature_state_changed` payload schema uses `from_state` / `to_state` (not `from` / `to`). Orchestration session (Opus 4.7) hit this validation error on first attempt at S2. One verification cycle. Reflects F3.6 pattern — the schema has the canonical field names but they aren't memorable / intuitive. Cross-reference mitigation helped but wasn't sufficient (schema wasn't explicitly cross-referenced for this specific event in the S2 runbook). Retrospective disposition candidate: trivial — memorize the field names OR cross-reference them in every feature_state_changed emission runbook.
- **F3.27 (Low)** — template-coverage-check SKILL.md entry-condition expects `state == planning`; walkthrough scaffolding runs it after `plan_review → generating`. F2 S3 subagent flagged this as a sequence discipline gap. F1 S3 had same pattern but didn't flag. Retrospective disposition candidate: Defer or clarify — SKILL.md could explicitly say "re-runs during `generating` are permitted" since coverage can be revalidated any time.
- **F3.28 (CRITICAL operational, new)** — JSONL append concatenation bug from `cat temp >> log` pattern when the source file has no trailing newline. F2 S4 subagent concatenated 6 events onto a single line on first attempt; detected via `tail -6 | json.tool` failure; recovered via `JSONDecoder.raw_decode()` split + rewrite. **No canonical JSONL append pattern documented.** Retrospective disposition candidate: Fix-in-Phase-3 — document canonical `printf '%s\n' "$(cat /tmp/event.json)" >> log` pattern in verify-before-report.md §3 OR in each skill's §Verification section.
- **F3.29 (Medium)** — missing `/features/FEAT-2026-0007-plan.md`: issue-drafting SKILL.md Step 2 references a plan-review file's work-unit prompts; F2 has no plan-review file (scaffolding skipped that step). Subagent fell back to deriving prompts from feature registry description — structurally correct but a deviation from the documented flow. Retrospective disposition candidate: Fix-in-Phase-3 — document the fallback path OR codify the plan-review skill OR remove the reference if plan-review files are optional.
- **F3.30 (Medium)** — IDE1006 lint rule surfaces at `dotnet format` time, not `dotnet build`. Project-level `.editorconfig` rule not surfaced anywhere in `.specfuse/verification.yml` or spec. F2 S5 subagent burned one verification cycle on `DefaultPageSize` naming (needed `_defaultPageSize`). Retrospective disposition candidate: Defer — this is project-specific lint; component repos are expected to declare their conventions, and the fix is to run `dotnet format` as part of the verification sequence before the compile-warnings gate.
- **F3.31 (Low)** — `source: component:<bare_name>` format (not `<owner>/<repo>`). F2 S5 subagent re-read schema to confirm. Minor ergonomic. Retrospective disposition candidate: Defer or observation.
- **F3.32 (Low)** — cardinality wording "three tests expected" in feature registry `## Scope`: ambiguous between confirmatory and prescriptive. F2 S7 subagent flagged. Retrospective disposition candidate: Defer — either accept the ambiguity (SKILL's collapse-only rule makes misinterpretation safe) or reword F2 spec post-walkthrough.
- **F3.33 (Low)** — F2 preamble clause 5 (`tail -1 log | json.tool` verification) assumes no trailing blank line. F2 S9 subagent suggested mitigation: `grep -v '^[[:space:]]*$' log | tail -1 | json.tool > /dev/null`. Retrospective disposition candidate: Fix-in-Phase-3 light — update the preamble / any verification docs.
- **F3.34 (Low)** — background task exit signal misleading for persistent service processes (dotnet run). F2 S10 subagent observed. Retrospective disposition candidate: Observation — `run_in_background: true` completion signal shouldn't be interpreted as readiness for long-running services; explicit readiness polling is the actual gate.
- **F3.35 (Medium, operational/meta)** — orchestration-session (Opus 4.7) rejection-of-successful-subagent incident. During S19, the orchestration session misinterpreted an IDE system-reminder about the FEAT-9003 plan file modification (the subagent's own rename commit) as an accidental user edit and prematurely interrupted the subagent + closed PR #3. Recovery required: (a) recognizing the subagent had completed successfully (events + branch + PR existed); (b) recreating the branch from git object store post-`branch -D`; (c) reopening PR. **Root cause**: walkthrough operator's partial visibility into subagent tool-use state led to false attribution of the file change. **Retrospective disposition candidate:** Fix-in-Phase-3 — document operator checklist for interpreting IDE system-reminders during subagent execution (if a file was modified by a subagent and the operator interrupts, they should inspect git state + event log BEFORE assuming error).
- **F3.36 (Medium, new qa-curation edge case)** — dedup/orphan retirement can violate `test-plan.schema.json` `tests[].minItems: 1` when the candidate is the sole test in its plan. F2 S19 subagent discovered at commit time and rolled back the whole dedup candidate cleanly with explicit `refused_candidates[]` reason. SKILL.md does not document this pre-flight check. Retrospective disposition candidate: Fix-in-Phase-3 — add `minItems:1` pre-flight check to qa-curation SKILL.md §Step 4 OR specify that sole-test retirement requires plan file deletion rather than test entry removal.

### Positive observations

- **P5 (new)** — F3.6 per-type schema mitigation clause effective: F2 S5 component subagent read `task_started.schema.json` before constructing payload; no re-do. Cross-reference clause in F2 preamble prevented the F1-era recurring friction.
- **P6 (new)** — qa-curation open-regression protection path exercised cleanly: seeded `qa_regression_filed` on FEAT-9002 + no paired `_resolved` → scan found it → orphan retire refused + recorded in `refused_candidates[]`. Anti-pattern #7 enforced per design.
- **P7 (new)** — qa-curation `rename-request:` prose detection worked cleanly: FEAT-9003's prose line parsed, retire-old + add-new pattern applied in a single plan diff, no open regression on old test_id blocked the rename.
- **P8 (new, F3.5 mitigation CONFIRMED EFFECTIVE)** — F2 preamble clause 1 ("Do NOT `git commit` on orchestrator repo") held across all 6 subagent sessions. 0 subagent commits on orchestrator repo vs F1's 4 unauthorized commits. Prompt-level clause is sufficient discipline.
- **P9 (new, backup path validated)** — qa-curation's three non-consolidation paths (dedup, orphan, rename) plus the protection refusal path exercised under seeded stress. `regression_suite_curated` event emitted correctly with mixed/rename scope + complete `refused_candidates[]`. SKILL scan-budget (50 plans) not stressed (only 5 plans scanned); consolidation path not stressed (0 `qa_execution_failed` events on scan cohort). Both deferred to future walkthrough stress if warranted.
- **P10 (cross-feature)** — Q4 invariant held across F1 (informal) + F2 (formal audit). No QA-originated write touched labels or state on any task other than the session's own QA task. Evidence across 6 QA sessions across 2 features.

### Merge-watcher dependency

F2 simulated the merge watcher manually (human flipped `in-review → done` labels + confirmed issue closures after merging PRs). F3.12 reclassification (same-owner cross-repo auto-close works) reduces manual close burden if all walkthrough repos share an owner. F2 did not use different-owner cross-repo Closes; that remains the open question for Phase 5 merge-watcher agent scope.

### Regression-cycle negative result

F2's primary goal was regression-cycle exercise. **The regression cycle did not execute.** This is itself a result: the component agent v1.5.0 on Sonnet 4.6 was robust enough to get AC-3 correct on first pass despite the feature being designed for edge-case miss. Retrospective input for WU 3.7: Phase 3 walkthrough design for regression-cycle stress should use edge cases that are genuinely subtle (not just "structured JSON rejection" which is literal and clear). Candidate subtler edges for future walkthroughs: non-obvious preconditions, ordering constraints, race conditions, backward-compatibility traps that only fail under specific history.

## References

- WU 3.6 plan section in [`docs/orchestrator-implementation-plan.md`](../../orchestrator-implementation-plan.md) §"Work unit 3.6 — Phase 3 walkthrough".
- F1 walkthrough log: [`feature-1-log.md`](feature-1-log.md).
- Pre-walkthrough notes (prompts used, pre-findings): [`notes-scratch.md`](notes-scratch.md).
- Agent configs exercised: [`agents/qa/CLAUDE.md`](../../../agents/qa/CLAUDE.md) v1.4.0; PM v1.6.0 (frozen); component v1.5.0 (frozen).
- Skills exercised: [`qa-authoring/SKILL.md`](../../../agents/qa/skills/qa-authoring/SKILL.md), [`qa-execution/SKILL.md`](../../../agents/qa/skills/qa-execution/SKILL.md), [`qa-curation/SKILL.md`](../../../agents/qa/skills/qa-curation/SKILL.md). [`qa-regression/SKILL.md`](../../../agents/qa/skills/qa-regression/SKILL.md) was NOT exercised (regression loop not triggered).
- Fixture seeding commit on specs-sample: [`d4276dc`](https://github.com/Bontyyy/orchestrator-specs-sample/commit/d4276dc).
- T01 implementation PR: [api-sample#22](https://github.com/Bontyyy/orchestrator-api-sample/pull/22). Merge commit `1a6dfd7`.
- T02 qa-authoring PR: [specs-sample#2](https://github.com/Bontyyy/orchestrator-specs-sample/pull/2). Merge commit `b2536bf`.
- T04 qa-curation PR: [specs-sample#3](https://github.com/Bontyyy/orchestrator-specs-sample/pull/3). Merge commit `0e21f92`.
