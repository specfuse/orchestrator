# Phase 3 walkthrough — Feature 1 log (happy path)

## Identity

- **Walkthrough:** Phase 3, WU 3.6
- **Feature:** `FEAT-2026-0006` — widget count endpoint (single-repo, happy path)
- **Shape chosen:** happy path (matches acceptance criterion 1 of WU 3.6 — one AC, one implementation task, one qa_authoring, one qa_execution, one qa_curation; no regression expected)
- **Started:** 2026-04-24 (prep committed 2026-04-23 via PRs [#36](https://github.com/clabonte/orchestrator/pull/36) + [#37](https://github.com/clabonte/orchestrator/pull/37))
- **Operator:** @Bontyyy (human)
- **Orchestration model:** Opus 4.7 (this session — note-taking, manual steps, subagent invocation)
- **QA / PM / component-agent model for subagent sessions:** Sonnet 4.6 (no per-session override — per WU 3.6 proposal §6 discipline: production-role model, even for contract-heavy sessions)
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
- **Specs repo:** [Bontyyy/orchestrator-specs-sample](https://github.com/Bontyyy/orchestrator-specs-sample) — stood up for this walkthrough (Phase 0 WU 0.8 deferral retrofit)
- **Agent versions at execution:** QA 1.4.0, PM 1.6.0 (frozen), component 1.5.0 (frozen)
- **Status:** ✅ complete — feature reached `state: done`

## Pre-walkthrough setup

Three setup actions performed before any agent session ran, all logged as WU 3.7 retrospective input on onboarding cost.

### Setup 1 — Stand up the product specs repo

[`Bontyyy/orchestrator-specs-sample`](https://github.com/Bontyyy/orchestrator-specs-sample) created — public, Apache 2.0, initial commit `397dfce`. Layout:

- `/product/features/FEAT-2026-0006.md` — narrative spec with single `AC-1` (GET /widgets/count returns `{"count": N}`).
- `/product/features/FEAT-2026-0007.md` — narrative spec for F2 (seeded ahead; F2 not started in this log).
- `/product/test-plans/.gitkeep` — qa-authoring writes here.
- `/business/.gitkeep` — never-touch boundary (empty).
- `LICENSE` + `README.md`.

Phase 0 WU 0.8 had deferred the product-specs-repo standup (per `orchestrator_overview` memory); retrofitted during prep. Deferral recorded as explicit WU 3.7 retrospective input.

### Setup 2 — Seed feature registry entries

Orchestrator PR [#36](https://github.com/clabonte/orchestrator/pull/36) merged (commit `7f1e805`) — `features/FEAT-2026-0006.md` and `features/FEAT-2026-0007.md` with `state: planning` + `task_graph: []`. Both point via `## Related specs` at specs-sample.

Prep artifacts PR [#37](https://github.com/clabonte/orchestrator/pull/37) merged (commit `ce0d805`) — `docs/walkthroughs/phase-3/feature-1-log.md`, `feature-2-log.md`, `notes-scratch.md`. notes-scratch holds the pre-computed task graphs, pre-findings, and ready-to-paste subagent prompts for F1 sessions 1–14.

### Setup 3 — Confirm frozen surfaces untouched

`git log` confirms no commits on `agents/pm/*`, `agents/component/*`, or `shared/rules/*` since Phase 2 freeze (commit `8125a86`). Phase 2 freeze contract upheld throughout F1.

## Skill invocations

### Step 1 — PM task-decomposition

- **Invoked by:** orchestration session (Opus 4.7) via `Agent` subagent, `subagent_type=general-purpose`, `model=sonnet`, fresh context. Subagent re-read `/shared/rules/*`, `agents/pm/CLAUDE.md` (v1.6.0 frozen), and `agents/pm/skills/task-decomposition/SKILL.md` per role-switch-hygiene.
- **Input:** `features/FEAT-2026-0006.md` (state=`planning`, task_graph=[]), related specs file via local clone at `/Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0006.md`.
- **Output:** task_graph written back to feature frontmatter (see table below) + `task_graph_drafted` event emitted to `events/FEAT-2026-0006.jsonl`. `state: planning` preserved (human owns transition).

  | id | type | depends_on | assigned_repo |
  |---|---|---|---|
  | T01 | implementation | [] | Bontyyy/orchestrator-api-sample |
  | T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample |
  | T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample |
  | T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample |

  Exact match to pre-computed expected graph in `notes-scratch.md §1`. No divergence.
- **Verification evidence:** `validate-frontmatter.py` exit 0; `validate-event.py` exit 0 (envelope only — no per-type schema for `task_graph_drafted`); source_version `1.6.0` from `read-agent-version.sh pm` at emission; re-read confirms event on disk.
- **Friction:** 6 items — see findings F3.17, F3.9, F3.15, F3.22, F3.23 in §Findings.
- **Duration:** ~10–12 min, 27 tool uses, 54k tokens.

### Step 2 — Human plan_review transition (manual, orchestration session)

- **Actor:** human (Opus 4.7 orchestration). Per WU 3.6 proposal, we skip the dedicated plan-review skill and simulate the Phase A edits inline.
- **Actions:**
  1. Edited `features/FEAT-2026-0006.md` frontmatter to add `required_templates` per task (T01: `[api-controller, api-response-serializer]`, T02: `[test-plan]`, T03/T04: `[]`).
  2. Changed `state: planning → state: generating` (skipping `plan_review` as a transient state in the frontmatter; emitted events cover the canonical trajectory).
  3. Emitted `feature_state_changed(planning → plan_review, trigger=plan_ready)` with `source: human`, `source_version: ce0d805` (short SHA per WU 2.14 F2.6 convention).
  4. Emitted `feature_state_changed(plan_review → generating, trigger=plan_approved)` 10s later.
- **Verification evidence:** both events validate (envelope + per-type payload via `feature_state_changed.schema.json`). Frontmatter re-validates. Event log: 3 lines total.
- **Friction:** minor — had to open `feature_state_changed.schema.json` to confirm `trigger` field shape (freeform string; used canonical values from the schema's examples).
- **Duration:** ~5 min.

### Step 3 — PM template-coverage-check

- **Invoked by:** fresh Sonnet 4.6 subagent with role-switch-hygiene re-read.
- **Input:** feature registry (now at `state=generating`, task_graph with `required_templates`) + `.specfuse/templates.yaml` on api-sample (declares `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`).
- **Output:** 1 `template_coverage_checked` event. Coverage clean on all 4 tasks (T01 and T02 have required tokens in provided set; T03/T04 have `required_templates: []`, trivially satisfy). Event payload: `{involved_repos: [...], task_count: 4}`.
- **Verification evidence:** `validate-event.py` exit 0 with per-type schema check (`template_coverage_checked.schema.json` exists). `source_version` 1.6.0.
- **Friction:** 5 items — see findings F3.10, F3.8 in §Findings. Notable: `/dev/stdin` pipe to `validate-event.py` failed on macOS with exit 2, subagent fell back to temp file.
- **Duration:** ~3–4 min, 23 tool uses.
- **Timestamp anomaly observation:** subagent emitted event at 01:14:03Z, chronologically between my session-2 events at 01:15:00Z / 01:15:10Z. File-append order ≠ timestamp order. Subagent chose real wall-clock over synthetic chronology. Documented as F3.13.

### Step 4 — PM issue-drafting

- **Invoked by:** fresh Sonnet 4.6 subagent with role-switch-hygiene re-read.
- **Input:** feature registry + work-unit-issue.md template v1.1 (optional `deliverable_repo` field + `## Deliverables` section added in WU 2.13) + issue-drafting-spec.md contract.
- **Output:** 4 GitHub issues opened on `Bontyyy/orchestrator-api-sample` ([#13 T01 impl ready](https://github.com/Bontyyy/orchestrator-api-sample/issues/13), [#14 T02 qa-authoring ready](https://github.com/Bontyyy/orchestrator-api-sample/issues/14), [#15 T03 qa-execution pending](https://github.com/Bontyyy/orchestrator-api-sample/issues/15), [#16 T04 qa-curation pending](https://github.com/Bontyyy/orchestrator-api-sample/issues/16)). 6 events emitted (4 `task_created` + 2 `task_ready` on T01, T02). `deliverable_repo: Bontyyy/orchestrator-specs-sample` correctly set on T02 + T04.
- **Verification evidence:** each issue confirmed via `gh issue view`: 5 mandatory `##` sections present, correct labels, `deliverable_repo` per per-task requirement, `## Deliverables` present iff `deliverable_repo` set.
- **Friction:** 5 items — see findings F3.7 (PF-3 confirmed: SKILL.md worked example still pointed at `clabonte/orchestrator`), F3.11 (SKILL.md exceeds 25k read limit), F3.24 (forward-looking T04 deliverable path).
- **Duration:** ~28 min, 65 tool uses, 83k tokens.
- **Timestamp anomaly:** subagent timestamped events at `2026-04-23T22:01Z – 22:07Z` — a day BEFORE other sessions (which used `2026-04-24`). Context-date synthesis, not wall-clock. F3.13.

### Step 5 — Component implementation on T01

- **Invoked by:** fresh Sonnet 4.6 subagent with role-switch-hygiene re-read. Component agent v1.5.0 frozen surface preserved.
- **Input:** [T01 issue #13](https://github.com/Bontyyy/orchestrator-api-sample/issues/13), api-sample local clone.
- **Output:** [PR #17 on api-sample](https://github.com/Bontyyy/orchestrator-api-sample/pull/17), branch `feat/FEAT-2026-0006-T01-widget-count-endpoint`, commit `5381310`. 4 source files modified + 2 test files. `task_started` + `task_completed` events emitted with wall-clock timestamps via `date -u`.
- **Verification gates — 6/6 PASS:**
  - tests: 33/33 pass, 0.7s
  - coverage: 100% (96/96 lines, threshold 0.90)
  - compiler_warnings: 0 warnings, 0 errors
  - lint: exit 0 (no formatting changes)
  - security_scan: 0 high/critical findings
  - build (Release): 0 warnings
- **Friction:** 5 items — see findings **F3.1 (Finding 8 live evidence — critical)**, F3.6 (task_started schema-discoverability), F3.20, F3.21, plus the positive P1 (date -u discipline frictionless).
- **Duration:** ~17 min, 68 tool uses, 80k tokens.

### Step 6 — Human merges T01 PR (manual, orchestration session)

- **Actor:** human operating as merge-watcher simulation.
- **Actions:** reviewed PR #17 (CI `verification gates` workflow SUCCESS in 51s); squash-merged via `gh pr merge 17 --squash --delete-branch`; api-sample main HEAD moved `aa7b639 → 6114339` (full SHA `611433970d8e7595e900f8b3c592bdfe1526faeb`); T01 issue auto-closed by "Closes #13" directive; manually flipped label `state:in-review → state:done` (auto-close doesn't flip labels).
- **Note:** the subagent already emitted `task_completed` for T01 in Step 5 at PR-open time. No second event emitted for merge. Convention: component agent task_completed at PR open is sufficient signal; merge watcher transitions are label-only.
- **Friction:** none.

### Step 7 — QA qa-authoring on T02

- **Invoked by:** fresh Sonnet 4.6 subagent with role-switch-hygiene re-read. First QA skill invocation in Phase 3.
- **Input:** [T02 issue #14](https://github.com/Bontyyy/orchestrator-api-sample/issues/14) + feature registry + specs-sample local clone.
- **Output:** test plan written at `/product/test-plans/FEAT-2026-0006.md` in specs-sample. Single test entry:
  - `test_id: widgets-count-returns-total`
  - `covers: "AC-1: GET /widgets/count returns HTTP 200 ..."` (AC-1 quoted verbatim)
  - `commands: ["curl -sS -o body.json -w '%{http_code}' http://localhost:5000/widgets/count"]`
  - `expected: "HTTP status is 200 and body.json parses as a JSON object with a single field 'count' ..."`
  - Coverage notes prose added (acknowledging the port-5000 assumption).
  - PR [specs-sample#1](https://github.com/Bontyyy/orchestrator-specs-sample/pull/1) opened on branch `qa-authoring/FEAT-2026-0006-T02`, commit `eb74eb9`.
- **Events emitted:** `task_started` (02:06:58Z) → `test_plan_authored` (02:09:52Z, payload `{plan_path, test_count: 1}`) → `task_completed` (02:12:36Z, payload with PR URL + verification evidence).
- **Verification evidence:** plan frontmatter round-trips `test-plan.schema.json`; unique test_id check trivially passes (1 test); coverage check passes (AC-1 covered). All 3 events validate. `source_version: 1.4.0` fresh per emission.
- **Friction:** 5 items — see findings **F3.2 (PF-1 confirmed: qa-authoring PR-based flow NOT specified in SKILL)**, F3.19 (port 5000 assumption in commands), F3.6 (task_started schema-discoverability — recurring), F3.11 (tooling), and observation on `## Coverage notes` optional-but-always-present-in-worked-example.
- **Duration:** ~25–30 min, 52 tool uses.

### Step 8 — Human merges qa-authoring PR + closes T02 (manual)

- **Actions:** squash-merged specs-sample PR #1, branch deleted. specs-sample main HEAD: `397dfce → 6ca7784`. Manually flipped T02 issue label `state:in-review → state:done`; **manually closed T02 issue via `gh issue close 14`** because cross-repo `Closes Bontyyy/orchestrator-api-sample#14` in the specs-sample PR body doesn't auto-close.
- **Friction:** F3.12 — cross-repo auto-close limitation. Anticipated by qa-curation SKILL §"Cross-repo linkage caveat", confirmed empirically here.

### Step 9 — PM dependency-recomputation (first invocation)

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Trigger:** T02 `task_completed` event (T01 was already done; T02 completing satisfies T03's deps `[T01, T02]`).
- **Output:** T03 flipped `state:pending → state:ready` on issue #15. `task_ready` event emitted with `trigger: "task_completed:T02"`.
- **Verification evidence:** `validate-event.py` exit 0; `source_version: 1.6.0`; `gh issue view 15` post-flip shows `state:ready` present, `state:pending` absent.
- **Friction:** 1 item — F3.16 ("done" derivation signal priority between label / issue.state / task_completed event — skill reads label, doesn't explicitly rank the 3 signals).
- **Duration:** ~6 min, 16 tool uses.

### Step 10 — QA qa-execution on T03

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** [T03 issue #15](https://github.com/Bontyyy/orchestrator-api-sample/issues/15) + plan at `/product/test-plans/FEAT-2026-0006.md` in specs-sample (post-merge state) + api-sample local clone + prescribed `commit_sha = 611433970d8e7595e900f8b3c592bdfe1526faeb`.
- **Output:** `qa_execution_completed` event emitted with payload `{task_correlation_id: FEAT-2026-0006/T03, commit_sha: 611433970d8e..., plan_path: /product/test-plans/FEAT-2026-0006.md, test_count: 1, total_duration_seconds: 0.047}`. Plus `task_started` + `task_completed` on T03. T03 flipped `state:in-progress → state:in-review`.
- **Test execution:**
  - Service started via `dotnet run --project src/OrchestratorApiSample.Api/ --urls "http://localhost:5000"` (PID tracked; explicit `--urls` override — see F3.3 below).
  - Startup: ~6s to first 200 response.
  - Command run verbatim: `curl -sS -o body.json -w '%{http_code}' http://localhost:5000/widgets/count`.
  - Result: HTTP 200, `body.json = {"count":0}`, exit 0, duration 47ms.
  - Predicate evaluation: HTTP=200 ✓, single-field JSON object ✓, `count: 0` non-negative integer ✓, equals store size on fresh start (0 widgets) ✓.
  - Verdict: **PASS**.
  - Service killed post-test; no process leak.
- **Verification evidence:** plan schema round-trip PASS; idempotence check scanned 16 lines, no prior event for (T03, prescribed SHA); `validate-event.py` exit 0 (envelope + per-type payload); re-read confirms all 3 events.
- **Friction:** 3 items — see **F3.3 (port mismatch: plan expects 5000, launchSettings.json declares 5083/7019 — subagent workaround via `--urls` flag)**, F3.18 (prescribed SHA ≠ local api-sample HEAD — walkthrough fidelity gap), observation on v1 prose predicate's weakness for stateful env (F3.19 cross-reference).
- **Duration:** ~10–11 min, 55 tool uses.

### Step 11 — Human closes T03 (manual)

- **Actions:** flipped T03 label `state:in-review → state:done` + closed issue via `gh issue close 15` (same cross-issue-close pattern as S8, since T03's "deliverable" is an event, not a PR).
- **Friction:** none.

### Step 12 — PM dependency-recomputation (second invocation)

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Trigger:** T03 `task_completed` event.
- **Output:** T04 flipped `state:pending → state:ready` on issue #16. `task_ready` event emitted with `trigger: "task_completed:T03"`.
- **Duration:** ~6 min, 30 tool uses. Smoother than Step 9 (muscle memory from first invocation).
- **Discovery during this session — critical:** the subagent noted that feature state is still `generating` but should have transitioned to `in_progress` after Step 4 (first round of task issues opened). **No `feature_state_changed(generating → in_progress)` event exists.** This is a gap: PM CLAUDE.md says the PM agent emits it "after the first round of task issues is opened," but no skill explicitly owns this transition — not task-decomposition, not issue-drafting, not dep-recomp. See F3.4.
- **Also discovered post-session:** the subagent made a local commit to orchestrator `main` (commit `4f57775`) to record the `task_ready` event append. Review of prior subagent outputs (S5, S7, S10) revealed 3 prior local commits — all subagent-authored, none pushed. See F3.5.

### Step 13 — QA qa-curation on T04

- **Invoked by:** fresh Sonnet 4.6 subagent, role-switch-hygiene re-read.
- **Input:** [T04 issue #16](https://github.com/Bontyyy/orchestrator-api-sample/issues/16) + specs-sample local clone (post-pull, HEAD `6ca7784`). Scan cohort = exactly 1 plan (FEAT-2026-0006.md).
- **Output:** **empty-curation branch taken** per SKILL §Step 7. No branch created, no PR opened. Comment posted on T04:
  > Curation pass complete. 0 accepted candidates, 0 refused. Scan covered 1 plan (FEAT-2026-0006.md). No dedup/orphan/consolidate/rename signals.
  
  T04 flipped `state:in-progress → state:in-review`. `task_started` + `task_completed` events emitted (`task_completed` with `empty_curation: true` additive payload field per SKILL convention). **No `regression_suite_curated` event** (correct: no PR merged, nothing to signal).
- **Candidate classification:**
  | Kind | Found | Reason |
  |---|---|---|
  | Dedup | 0 | Impossible — 1 plan, no pair |
  | Orphan | 0 | AC-1 still exists in feature registry |
  | Consolidation | 0 | No `qa_execution_failed` events exist |
  | Rename | 0 | No `rename-request:` line |
- **Friction:** 5 items — F3.6 recurring (task_started payload again), F3.14 (`issue` vs `issue_url` field name inconsistency), **F3.8 (T04 issue body AC contradicts qa-curation SKILL empty-curation path — issue body says "PR is opened", SKILL §Step 7 says "do NOT open a PR")**, discoverability of `empty_curation: true` additive field, `validate-event.py` invocation format (recurring).
- **Duration:** ~12 min, 47 tool uses.

### Step 14 — Human closes T04 + retro-emits missing transition + feature done (manual)

- **Actions:**
  1. Flipped T04 label `state:in-review → state:done`, closed issue #16.
  2. Retro-emitted `feature_state_changed(generating → in_progress, trigger=first_round_issues_opened_retroactive)` to close the gap identified in Step 12. Trigger string flags retroactive emission honestly; timestamp is wall-clock "now" (not back-dated — back-dating would sanitize). F3.4 is the finding; the retro emission is the honest documentation.
  3. Emitted `feature_state_changed(in_progress → done, trigger=all_tasks_done)`.
  4. Updated feature frontmatter `state: generating → state: done` + re-validated.
- **Verification evidence:** both events validate (envelope + per-type payload); full event log re-validates (24 events, all pass); frontmatter validates; all 4 issues CLOSED + `state:done`.

## Q4 invariant audit (for reference; audit is primary for F2)

F1 is a happy-path feature with no cross-task regression flow exercised, so the Q4 invariant's main stress surface (`qa-regression` filing artifacts without flipping foreign task state) is not tested here. That said, informally for F1: every QA-session write action was auditable against the QA-owned task type. Enumeration:

- qa-authoring (Step 7) wrote to: T02 labels (owned), plan file in specs-sample (authorized QA output surface), feature event log (authorized). Did NOT write to T01, T03, T04 labels/state or to api-sample code. ✅
- qa-execution (Step 10) wrote to: T03 labels (owned), feature event log (authorized). Did NOT write to T01 impl task's labels or state despite having the commit SHA of its PR; did NOT write to plan file, did NOT commit to api-sample. ✅
- qa-curation (Step 13) wrote to: T04 labels (owned), T04 issue comment, feature event log. Read-only scan of specs-sample. Did NOT write to T01/T02/T03 labels or state, did NOT open a branch or PR on specs-sample. ✅

Q4 invariant: **held** across all 3 QA sessions. The full enumeration table belongs to F2 log.

## Outcome

- **F1 happy-path acceptance:** ✅ met. All 4 tasks reached `done`. `qa_execution_completed` emitted on merge commit `6114339`. No regression filed. Feature reached `state: done`.
- **End state:**
  - Feature registry `state: done`, frontmatter schema-valid.
  - Event log: 24 events, all round-trip through `validate-event.py`.
  - 4 issues on api-sample CLOSED + `state:done`.
  - 2 merged PRs: api-sample#17 (impl), specs-sample#1 (test plan).
- **Findings captured:** 24 F3.x items + 4 positive observations (P1–P4). Triage input for WU 3.7.
- **Commit:** `chore(phase-3): walkthrough feature 1 complete` (per WU 3.6 AC #7).

## Findings summary

Findings are numbered F3.1 through F3.24 in rough severity/theme order. Severity scale: **High** = hard gate on Phase 4 / blocks retro close; **Medium** = likely Fix-in-Phase-3; **Low** = Defer / Observation. Final disposition is WU 3.7's triage.

### Critical / high severity

#### F3.1 — Finding 8 live empirical evidence on component verification gate order
**What.** api-sample's `.specfuse/verification.yml` declares `tests` and `coverage` gates using `--no-build`. The skill's gate sequence starts with `tests`, not `build`. A component agent running gates literally on a fresh checkout would hit the `--no-build` stale-artifact trap (Phase 1 Finding 8 scenario). The Step 5 subagent caught this proactively and ran `dotnet restore && dotnet build` before the gate sequence — but the `verification.yml` does not declare a pre-gate build step, and the verification skill does not mandate one explicitly. **Verbatim from subagent:** "A component agent that reads verification.yml literally and runs gates in listed order on a fresh branch will fail the tests gate for reasons unrelated to the code under test."
**Evidence.** Step 5 session report.
**Severity.** High. Live evidence updates the Phase 1 Finding 8 carry status (per `phase3_progress` memory, it was reaffirmed to Phase 5; this session argues for earlier absorption).
**Retrospective disposition candidate.** Fix-in-Phase-3 (WU 3.8+ amendment to `verification/SKILL.md` mandating `dotnet build` pre-step OR `verification.yml` schema change requiring a `build` gate before `--no-build` gates). Alternatively: reaffirm Phase 5 with stronger guard-rail documentation in the meantime.

#### F3.2 — qa-authoring SKILL.md does not specify the PR-based delivery convention
**What.** `qa-authoring/SKILL.md` §Step 7 says "Write the plan file to `/product/test-plans/<feature_correlation_id>.md` in the product specs repo" without specifying branch name, commit message, PR title, PR body format, or how the PR references the qa_authoring task issue for merge-watcher matching. Later prose says "The PR containing the plan file is the deliverable under review" — implying PR-based flow, but the mechanics are unspecified.
**Evidence.** Step 7 session — subagent quote: "two agents operating from SKILL.md alone would diverge: one might write directly to specs-sample main, the other might open a PR." My session-7 prompt pinned the full PR convention; without that pin, the skill is underspecified.
**Severity.** Medium/High (PF-1 confirmed). Directly affects reproducibility.
**Retrospective disposition candidate.** Fix-in-Phase-3. Add `## Delivery convention` section to `qa-authoring/SKILL.md` naming branch pattern (`qa-authoring/<task_correlation_id>`), commit message template, PR body format, and stop-at-open discipline.

#### F3.3 — Port mismatch between test plan command and component service launchSettings
**What.** The test plan's command expects `http://localhost:5000/widgets/count`. api-sample's `launchSettings.json` declares ports `5083` (http profile), `7019` (https profile), and `42317` (IIS Express) — none is 5000. Step 10 subagent worked around via `dotnet run --urls "http://localhost:5000"`. Test ran verbatim against the plan's command, but only because the startup was hacked.
**Contradictory conventions surface:** the plan's own `## Coverage notes` (authored by Step 7 subagent) says "T03 should adjust the command to match the actual host/port before running." The qa-execution SKILL + task-prompt say "use the plan's command verbatim OR escalate `spec_level_blocker`." These are mutually incompatible conventions.
**Evidence.** Step 10 session.
**Severity.** Medium (design gap between the two QA skills).
**Retrospective disposition candidate.** Fix-in-Phase-3. Options: (a) qa-authoring includes startup command in `commands[]` (e.g., `dotnet run --urls "http://localhost:5000" &` as command[0]); (b) test-plan.schema.json adds `preconditions` / `setup` field (acknowledged Phase 4 in current SKILL deferred integration); (c) qa-execution SKILL documents explicit "adapt to localhost:ANY_PORT" discipline. Option (a) is the least invasive for v1.

#### F3.4 — Feature state `generating → in_progress` transition has no clear skill owner
**What.** PM CLAUDE.md says "the PM agent emits `feature_state_changed` for `generating → in_progress` after the first round of task issues is opened across component repos." But no skill explicitly owns this transition — task-decomposition stops at `plan_review`, issue-drafting doesn't transition feature state, dep-recomputation is scoped to task states only. During F1, the transition was **skipped** — feature sat at `generating` from Step 2 through Step 13. Retro-emitted during Step 14 to close the event log gap.
**Evidence.** Step 12 subagent discovery; Step 14 retro emission.
**Severity.** Medium. Silent invariant violation; event log was never wrong in a way that blocked, but state machine integrity was compromised.
**Retrospective disposition candidate.** Fix-in-Phase-3. Likely home: issue-drafting SKILL.md — add a Step that emits `feature_state_changed(generating → in_progress)` after the first round of `task_created`/`task_ready` events.

#### F3.5 — Subagents auto-committed to orchestrator main without explicit authorization
**What.** Sessions 5, 7, 10, 12 each made a local commit to orchestrator repo `main` recording the `events/FEAT-2026-0006.jsonl` append. My prompts said "Do NOT push to GitHub" but did not say "Do NOT commit to the orchestrator repo." Subagents interpreted broadly: commit-but-don't-push = OK. Result: 4 unauthorized local commits ahead of origin before this log write began.
**Evidence.** `git log --oneline` post-S12 showed 4 commits ahead; none pushed; `git status` clean of uncommitted event changes (subagent committed everything).
**Severity.** Medium. Commits are factually correct but bypass the repo's PR-based convention (all prior commits on main are `(#N)` PR merges). Also creates commit-squash complexity for the walkthrough wrap commit.
**Retrospective disposition candidate.** Fix-in-Phase-3 — two angles: (a) Add explicit "Do NOT commit on orchestrator repo" clause to shared rules OR to every skill that writes events; (b) Update walkthrough operational guidance with stricter commit discipline. Plus: this session squashes the 4 commits back into a single walkthrough-complete commit.

### Schema discoverability (recurring pattern)

#### F3.6 — Per-type event payload schemas not cross-referenced from role CLAUDE.md or skills
**What.** `task_started`, `task_completed`, and others have per-type schemas at `shared/schemas/events/<name>.schema.json` that constrain payload shape (e.g., `task_started` requires `issue_url` + `branch`, forbids `additionalProperties`). But neither role CLAUDE.md nor the skill files cross-reference these schemas. Subagents construct payloads from intuition or by copying patterns from prior events on the log — which may themselves be non-conformant (no per-type schema exists for `task_completed`, so prior events use `issue` field; `task_started` requires `issue_url`; subagents conflate the two and fail validation on first attempt).
**Evidence.** Sessions 5, 7, 13 — each had one failed `validate-event.py` cycle on a `task_started` payload shape mismatch. Session 13 explicitly: "first `task_started` candidate used `issue` field inherited from `task_completed` convention in prior event log lines. The validator rejected it."
**Severity.** Medium. Recurring 3+ times across F1. Each time correctable in one cycle, but always costs a cycle.
**Retrospective disposition candidate.** Fix-in-Phase-3. Cross-reference per-type schema paths from each event type's name in the relevant CLAUDE.md / SKILL.md sections.

#### F3.14 — `task_completed` uses `issue` field; `task_started` uses `issue_url` — inconsistency
**What.** Across the event log, `task_created` payloads carry `issue` (bare `<owner>/<repo>#<N>`) while `task_started` payloads carry `issue_url` (full URL). Both refer to the same GitHub issue. Asymmetry confused Step 13 subagent (which initially used `issue` for `task_started`, rejected by per-type schema).
**Evidence.** Session 13 first-attempt failure.
**Severity.** Low/Medium (ergonomic).
**Retrospective disposition candidate.** Fix-in-Phase-3. Pick one convention across all task lifecycle events; update schemas + skills; migrate historical payloads is optional.

#### F3.15 — Several task lifecycle events have no per-type schema (envelope-only validation)
**What.** `task_graph_drafted`, `task_created`, `task_ready`, `task_completed`, `plan_approved`, `spec_issue_raised`, `override_applied`, `override_expired`, `dependency_recomputed` — all envelope-only at v1. `validate-event.py` silently skips per-type check. No affirmative signal to the agent that payload shape was (or wasn't) validated. Subagents in Step 1 and Step 3 both noted the silent skip.
**Evidence.** Sessions 1, 3, 9, 12 — all noted the silent pass.
**Severity.** Low. Doesn't break anything, but weakens agent trust in the verification chain.
**Retrospective disposition candidate.** Fix-in-Phase-3 light: update `validate-event.py` output to explicitly say "no per-type schema found for `<event_type>` — envelope-only validation". Adding per-type schemas for all 9 events is larger scope, may defer.

### SKILL / documentation gaps

#### F3.7 — issue-drafting SKILL.md worked example points at `clabonte/orchestrator` for `deliverable_repo` (Phase 2 convention)
**What.** The SKILL.md worked example (§"FEAT-2026-0004/T03") uses `deliverable_repo: clabonte/orchestrator` because Phase 2 had no specs repo yet (Phase 0 WU 0.8 was deferred). F1 is the first walkthrough with a live specs repo; Step 4 subagent correctly overrode to `Bontyyy/orchestrator-specs-sample` (on prompt guidance), but flagged the pause: without explicit guidance, the worked example's stickiness could mislead future agents.
**Evidence.** Step 4 session report. PF-3 confirmed.
**Severity.** Medium.
**Retrospective disposition candidate.** Fix-in-Phase-3. Update issue-drafting SKILL.md's worked example to use the specs-sample convention, OR add a note clarifying that the example's `clabonte/orchestrator` target is Phase-2-era and should be adapted to the actual product specs repo for each feature.

#### F3.8 — T04 qa_curation issue body `## Acceptance criteria` contradicts qa-curation SKILL empty-curation path
**What.** PM issue-drafting (Step 4) generated T04's issue body with ACs describing "A PR is opened against `main` on specs-sample". qa-curation SKILL §Step 7 explicitly says "Do NOT open a PR, do NOT create a branch" for the empty-curation case. Step 13 subagent had to re-read SKILL §Step 7 a second time to confirm SKILL governs over the issue ACs.
**Evidence.** Step 13 session report.
**Severity.** Medium. Documentation gap between two skills on the same transaction.
**Retrospective disposition candidate.** Fix-in-Phase-3. Either (a) issue-drafting generates AC-conditional language for qa_curation tasks ("A PR is opened ... UNLESS the pass produces zero candidates, in which case no PR is opened"), or (b) qa-curation's §Step 7 empty-curation branch gets explicit cross-reference note.

#### F3.9 — task-decomposition SKILL.md header says "7 steps" but body is numbered 1–8
**What.** Subagent in Step 1 noted: "SKILL.md has 7 steps in the header description, 8 in the procedure body. The task description's 'Step 6: validate' maps to SKILL.md's step 7, and 'Step 7: write' maps to SKILL.md's step 8." Not a blocker but caused momentary counting confusion.
**Severity.** Low (consistency).
**Retrospective disposition candidate.** Fix-in-Phase-3 (trivial one-line fix).

#### F3.11 — Long SKILL.md files exceed the 25k-token read limit
**What.** `issue-drafting/SKILL.md` and `qa-curation/SKILL.md` both exceed the Read tool's 25,000-token per-read limit. Subagents in Steps 4 and 13 had to read in 2–3 chunks via offset/limit. Mechanical friction, no content loss, but not free.
**Severity.** Low.
**Retrospective disposition candidate.** Defer / observation. Could trigger a SKILL.md prose trim in a later iteration; for v1, the content is load-bearing.

### Tooling / environmental

#### F3.10 — `validate-event.py` `/dev/stdin` pipe doesn't work on macOS
**What.** Subagents tried stdin-based validation (per SKILL instructions "pipe the constructed event..."), got exit 2 "setup error — file not found: /dev/stdin." Workaround: write to temp file and pass `--file`. Observed in Steps 3, 5, 7, 13.
**Evidence.** 4+ recurring sessions.
**Severity.** Low (workaround trivial), but recurring noise.
**Retrospective disposition candidate.** Fix-in-Phase-3 light. Either: (a) fix `validate-event.py` to handle `/dev/stdin` correctly on macOS, (b) update SKILL / docs to prescribe temp-file pattern as the canonical invocation.

#### F3.12 — GitHub cross-repo `Closes` directive doesn't auto-close
**What.** When a PR's `Closes` directive references an issue in a different repo (e.g., specs-sample PR #1 refers to api-sample#14), the auto-close machinery does NOT fire. The issue stays open after merge; manual `gh issue close` required.
**Evidence.** Step 8 (T02), Step 11 (T03, though T03's deliverable wasn't a PR so this was already manual).
**Severity.** Low (anticipated in qa-curation SKILL §"Cross-repo linkage caveat"; confirmed).
**Retrospective disposition candidate.** Observation → feeds into WU 3.6 retro's "merge-watcher agent scope" for Phase 5.

### State-vocabulary and lifecycle ambiguities

#### F3.13 — Early-session timestamp synthesis broke event log chronology
**What.** Sessions 1–4 subagents synthesized timestamps from context rather than wall-clock, producing a non-chronological event log. Notable: Session 4 timestamps at `2026-04-23T22:07Z` (one day BEFORE other sessions at `2026-04-24`). `date -u +%Y-%m-%dT%H:%M:%SZ` discipline prescribed from Step 5 onwards fixed the issue — all post-S5 timestamps are wall-clock fresh.
**Evidence.** Early session timestamps clearly diverge; later sessions are monotonic.
**Severity.** Medium (event log integrity), resolved by prompt discipline.
**Retrospective disposition candidate.** Fix-in-Phase-3. Add explicit clause to `verify-before-report.md` §3 or the relevant SKILL.md files: "timestamp produced via `date -u` at emission time, never synthesized from context."

#### F3.16 — "Done" derivation signal priority undocumented
**What.** Three potential signals for "task is done": `state:done` label, GitHub issue `state == CLOSED`, `task_completed` event on log. dep-recomputation SKILL §6b reads the label. In F1 happy path, all three signals always agreed; but in failure recovery (e.g., task manually closed without label update), the skill's priority ordering isn't documented. Step 9 subagent flagged as a latent ambiguity.
**Evidence.** Step 9 friction note.
**Severity.** Low at v1 (happy-path-safe), potential Medium for operational failure recovery.
**Retrospective disposition candidate.** Fix-in-Phase-3 OR defer — the skill could explicitly state "canonical signal is the GitHub label; divergence = escalation" in one sentence.

#### F3.17 — `## Scope` cardinality clause ambiguity
**What.** Step 1 subagent briefly confused the feature's `## Scope` clause "QA: one authored test plan covering AC-1, one execution run" with a cardinality override (which collapses behaviors). On re-read, it's redundant with default (one AC → one test → default cardinality applies) rather than an override. The confusion is unlikely to cause a real bug but indicates the scope-clause wording space is not perfectly disjoint from the cardinality-override wording space.
**Evidence.** Step 1 friction note.
**Severity.** Low (subagent resolved correctly).
**Retrospective disposition candidate.** Defer / observation.

### Walkthrough fidelity / procedural

#### F3.18 — Prescribed `commit_sha` in qa_execution event didn't match local api-sample HEAD
**What.** Step 10 task prompt specified `commit_sha = 611433970d8e7595e900f8b3c592bdfe1526faeb` (the squash-merge commit on api-sample main). Local api-sample HEAD at execution time was at the branch state `538131079e43...` (pre-squash). Subagent used the prescribed SHA per skill discipline; functionally equivalent (squashed vs. branch content is identical), but git-metadata misalignment. Walkthrough-procedure gap: Session 10 prompt should have directed the subagent to `git fetch + git checkout main + git pull` before service startup.
**Evidence.** Step 10 session report.
**Severity.** Low (functional pass). Walkthrough reproducibility concern for future sessions.
**Retrospective disposition candidate.** Observation / update walkthrough operational checklist.

#### F3.19 — v1 prose `expected` predicate is weak for stateful environments
**What.** The Step 7 test's `expected` predicate contained the clause "equal to the number of widgets in the persisted store." Step 10 handled it by leveraging the fresh-start-zero-widgets property of the in-memory store. In a stateful environment (seeded DB, pre-existing data), this predicate requires an external oracle; agent judgment alone wouldn't suffice.
**Evidence.** Step 10 friction note.
**Severity.** Low (v1 stub, acknowledged in SKILL §"Deferred integration" as Phase 4 machine-evaluable predicate target).
**Retrospective disposition candidate.** Observation → feeds Phase 4 predicate-language selection input.

### Minor / deferred

- **F3.20** — coverage report path is a directory, not a file; subagent used `find` to locate `coverage.cobertura.xml`. Observation.
- **F3.21** — lint gate on pass returns empty output; convention "exit 0 = pass, no stdout." Observation.
- **F3.22** — Rule 1 (`qa_execution never auto`) conditional parsing friction when `autonomy_default != auto`. Minor ergonomic.
- **F3.23** — `decomposition_pass` counting on missing file requires defensive fallback (`ls && grep || echo file_not_found`). Minor operational.
- **F3.24** — T04 `## Deliverables` section references test plan path that doesn't exist at issue-creation time (T02 hasn't run yet). Forward-looking assertion pattern. Deferred.

### Positive observations

- **P1 — `date -u` timestamp discipline is feasible and frictionless.** Introduced in Step 5, followed consistently through Step 14. Fixes F3.13 at the prompt level.
- **P2 — All 4 subagents correctly set `deliverable_repo: Bontyyy/orchestrator-specs-sample` on T02/T04 despite SKILL worked example pointing at `clabonte/orchestrator`.** PF-3 was a real friction point (F3.7) but subagents resolved correctly when prompt guidance was explicit.
- **P3 — Empty-curation branch handled cleanly** by qa-curation SKILL §Step 7. No PR opened, no `regression_suite_curated` emitted, appropriate comment on task issue. Clean fast-path.
- **P4 — Q4 invariant held across all 3 QA sessions.** No QA-originated write to any task the QA did not own. See §Q4 invariant audit above.

### Merge-watcher dependency

F1 simulated the merge watcher manually (human flipped `in-review → done` labels + closed issues after merging PRs). Any friction on this simulation feeds the future merge-watcher agent scope (Phase 5). Notable: cross-repo `Closes` limitation (F3.12) and "task_completed emitted at in-review vs at done" convention (architectural question — implicit at v1).
