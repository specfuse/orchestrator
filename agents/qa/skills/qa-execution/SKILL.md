# QA agent — qa-execution skill (v1.0)

## Purpose

This skill reads a test plan authored by `qa-authoring` (WU 3.2), runs the declared `commands` against the component repo(s) under test, evaluates each test's `expected` predicate, and emits one structured event summarizing the run — `qa_execution_completed` on all-pass, `qa_execution_failed` with a `failed_tests[]` array otherwise. It is the engine that turns authored plans into empirical signal.

The skill does not build the component under test, does not file regression artifacts on failure, and does not curate the suite. It executes only; its siblings take it from there.

## Scope

In scope:

- Picking up a `ready` `qa_execution` task.
- Resolving the plan file via the task's feature correlation ID.
- Enforcing idempotence on `(task_correlation_id, commit_sha)` before emitting any event.
- Running each test's `commands` sequentially, capturing stdout, stderr, and exit codes.
- Evaluating each test's `expected` predicate against the captured output (at v1, via agent judgment against a prose predicate — see §"Deferred integration" for the Phase 4 machine-evaluable predicate language).
- Emitting the aggregated event (`qa_execution_completed` or `qa_execution_failed`) through [`scripts/validate-event.py`](../../../../scripts/validate-event.py).
- Transitioning the `qa_execution` task through `ready → in_progress → in_review`.

Out of scope (each belongs to a sibling skill, a later phase, or another role):

- **Filing regression artifacts on failure** — [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md), WU 3.4. This skill's only responsibility on failure is emitting `qa_execution_failed`; the regression pipeline consumes that event.
- **Curating the regression suite** — [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md), WU 3.5.
- **Building the component under test.** The component agent's verification skill (frozen at v1.1) produced buildable artifacts before any qa_execution task became `ready`. See §"Finding 8 disposition" for the Q6 check result.
- **Machine-evaluable `expected` predicates.** Phase 4 replaces the v1 prose predicates with a structured predicate language; see §"Deferred integration".
- **Modifying the plan file.** Plan modifications are `qa-curation`'s concern, not `qa-execution`'s.

## Inputs

The skill reads, in order:

1. The `qa_execution` task issue assigned to it. The issue title's task-level correlation ID (`FEAT-YYYY-NNNN/TNN`) carries the feature correlation ID.
2. The feature registry at `/features/<feature_correlation_id>.md` — its frontmatter (task graph, `involved_repos`, `assigned_repo` of the qa_execution task).
3. The feature's event log at `/events/<feature_correlation_id>.jsonl` — scanned end-to-end for prior `qa_execution_completed` or `qa_execution_failed` entries matching `(task_correlation_id, commit_sha)` (step 3 below).
4. The test plan at `/product/test-plans/<feature_correlation_id>.md` in the product specs repo — its YAML frontmatter validated against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) before the per-test loop begins.
5. The assigned component repo — its `main` HEAD commit SHA (for the idempotence key and the emitted event), and its current working state (for running the plan's `commands`).
6. This skill's own file and [`../../CLAUDE.md`](../../CLAUDE.md) — reloaded per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

The skill does **not** read or rebuild cached test binaries. `commands` run against the running system, not against precomputed artifacts — see §"Finding 8 disposition" below.

## Outputs

- One event appended to `/events/<feature_correlation_id>.jsonl`: either `qa_execution_completed` (all-pass) or `qa_execution_failed` (≥1 failure). Payload shape per [`events/qa_execution_completed.schema.json`](../../../../shared/schemas/events/qa_execution_completed.schema.json) or [`events/qa_execution_failed.schema.json`](../../../../shared/schemas/events/qa_execution_failed.schema.json).
- Standard QA-task-lifecycle events on the `qa_execution` task: `task_started` on pickup, `task_completed` on successful skill termination (which includes the failed-tests case — the QA *task* completed even though the system under test failed; see [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification" — the distinction is deliberate).
- No writes to the plan file, no writes to the component repo, no writes to any task issue other than the `qa_execution` task this instance owns.

## The execution procedure

### Step 1 — State intent and pick up the task

State the intent (per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1): "I will execute the test plan for `<feature_correlation_id>` against `<assigned_repo>` at commit `<commit_sha>`."

Flip the `qa_execution` task's label `state:ready → state:in-progress`. Emit `task_started`.

### Step 2 — Resolve the plan file and the commit SHA

Read the feature registry. Locate the qa_execution task's `assigned_repo` field in the task graph — that is the repo under test.

Determine `commit_sha`: the `main` HEAD SHA of `<assigned_repo>` at execution time. Use the 40-character full SHA; short SHAs are rejected by the event schemas. On a cross-repo feature, each `qa_execution` task resolves its own `commit_sha` independently (the SHA of its assigned repo only).

Derive the plan path: `/product/test-plans/<feature_correlation_id>.md` in the product specs repo.

Read the plan file. Parse the YAML frontmatter and round-trip it against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) using `ajv`, Python `jsonschema`, or equivalent. A plan that fails validation is a skill-level contract break — escalate `spec_level_blocker` with reason "plan file at `<plan_path>` fails `test-plan.schema.json` validation"; do **not** attempt to run a malformed plan.

### Step 3 — Idempotence check

Read `/events/<feature_correlation_id>.jsonl` end-to-end. Search for any entry where:

- `event_type` is `qa_execution_completed` or `qa_execution_failed`, **and**
- `payload.task_correlation_id` equals this task's correlation ID, **and**
- `payload.commit_sha` equals the resolved `commit_sha`.

If a match is found, the qa-execution for this `(task_correlation_id, commit_sha)` pair has already been recorded. **Do not emit a second event.** Report "idempotent skip: existing event at line `<N>` of events log for `(task_correlation_id, commit_sha)` pair" and proceed directly to step 7's task-completion path. The prior event remains the authoritative signal; re-emitting would corrupt the audit trail and risk cascading duplicate regression artifacts downstream.

If no match is found, proceed to step 4. The event-log read must be **fresh** — do not cache a prior snapshot across pickups; concurrent emissions elsewhere on the feature may have appended after a cached read, and an idempotence decision based on stale data can miss a collision.

### Step 4 — Per-test execution loop

Initialize an empty `per_test_results` array. Record the loop's start timestamp.

For each test entry in `plan.tests` (in order — the plan's sequence is preserved in the failed-tests array on emission):

1. For each command in the test's `commands` array (sequentially, not in parallel):
   - Invoke the command with the assigned repo's root as the working directory, unless the command itself changes directory.
   - Capture exit code, stdout, stderr, and wall-clock duration.
   - Redact any secret-looking values from stdout/stderr per [`/shared/rules/security-boundaries.md`](../../../../shared/rules/security-boundaries.md) §"Log hygiene" before any excerpt is retained for the event payload.
2. Evaluate the test's `expected` predicate against the captured outputs:
   - At v1, the predicate is free-form prose (e.g., "HTTP status is 200 and body.json parses as a JSON array of exactly 50 widget objects"). The QA agent's judgment is the evaluator — read the prose, read the outputs, decide pass/fail.
   - A predicate mismatch on a command that returned exit `0` is still a fail. A predicate match on a command that returned non-zero exit is still a fail (the command failed to execute cleanly). Both paths record the failure.
3. Append a `{test_id, status, evidence, exit_code, stderr_excerpt?}` record to `per_test_results` (internal skill state; not directly the emitted payload).

Record the loop's end timestamp; `total_duration_seconds` is the difference.

### Step 5 — Aggregate and construct the event

Partition `per_test_results` into passing and failing sets.

**If every test passed** — construct a `qa_execution_completed` event:

- `timestamp`: ISO-8601 at construction time.
- `correlation_id`: the feature-level ID (no task suffix).
- `event_type`: `qa_execution_completed`.
- `source`: `qa`.
- `source_version`: produced by [`scripts/read-agent-version.sh qa`](../../../../scripts/read-agent-version.sh) at emission time — never eye-cached from [`version.md`](../../version.md).
- `payload`:
  - `task_correlation_id`: this task's full task-level ID (e.g., `FEAT-2026-0061/T04`).
  - `commit_sha`: the 40-char SHA resolved in step 2.
  - `plan_path`: the plan path resolved in step 2.
  - `test_count`: `len(plan.tests)`.
  - `total_duration_seconds`: optional — include if the loop's duration was captured cleanly.

**If any test failed** — construct a `qa_execution_failed` event with the same envelope fields and a payload that additionally carries:

- `failed_tests`: an array of `{test_id, first_signal, exit_code?, stderr_excerpt?}` — one entry per failed test, in plan order (not severity order). Each entry's `first_signal` is the single most load-bearing line from the captured outputs — a failing assertion's line, a non-zero exit's summary, the predicate-mismatch evidence. Long outputs are truncated; the full trail remains in the task verification log the skill maintains off-event, but does not bloat the payload.

The `implementation_task_correlation_id` being regressed against is **not** carried in the payload — qa-regression (WU 3.4) resolves it from the feature task graph when it consumes the event. Decision rationale: the test→implementation mapping is not 1:1 under the feature-scope `qa_authoring` cardinality override (WU 2.10), so the authoritative mapping lives in the feature registry; duplicating a derived value into the event payload would risk drift.

### Step 6 — Validate the event and append

Pipe the constructed event through [`scripts/validate-event.py`](../../../../scripts/validate-event.py). The script applies the top-level envelope schema and — because `qa_execution_completed.schema.json` and `qa_execution_failed.schema.json` exist under [`/shared/schemas/events/`](../../../../shared/schemas/events/) — the per-type payload schema as well. Require exit `0` before appending.

Append the event to `/events/<feature_correlation_id>.jsonl` in the orchestration repo. Re-read the appended line and confirm it matches what was constructed, per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3.

### Step 7 — Close the QA task

Regardless of whether the run was `qa_execution_completed` or `qa_execution_failed`:

- Flip the `qa_execution` task's label `state:in-progress → state:in-review`.
- Emit `task_completed` on the qa_execution task's correlation ID. **This is the QA task's completion — not a statement about the system under test.** A `qa_execution_failed` event is a valid outcome of a qa_execution task; the QA work was to run the plan, capture evidence, and emit the aggregated event. Whether the system under test passed is a separate signal, consumed by qa-regression (WU 3.4).

On the idempotent-skip path from step 3, close the task the same way (without re-emitting the qa_execution_* event, but still flipping labels and emitting `task_completed` — the task itself still needs to reach a terminal state).

## Verification

Before emitting any `qa_execution_*` event, the skill confirms:

- The plan file validated cleanly against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) in step 2.
- The idempotence check in step 3 produced a fresh read of the event log (not a cached snapshot) and returned no match for the `(task_correlation_id, commit_sha)` pair.
- Every declared command in every test was invoked — no test was skipped for convenience.
- Each test in `per_test_results` has a definite `status` of `pass` or `fail` — no `unknown` or `indeterminate` entries. A command whose output the skill cannot interpret against the `expected` predicate is a failure, not a skipped test; when in doubt, the skill escalates `spec_level_blocker` with reason "predicate ambiguity on test_id `<id>`" rather than silently passing.
- The aggregated event round-trips through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) with exit `0` (envelope + per-type payload).

The universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) apply in addition:

- Re-read the appended event line from `/events/<feature_correlation_id>.jsonl` after writing.
- Confirm `source_version` was produced by `scripts/read-agent-version.sh qa` at emission time.
- Confirm the correlation IDs in the payload and envelope match the patterns in [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md).
- Confirm no secret-looking value appears anywhere in `failed_tests[].first_signal` or `stderr_excerpt` per [`/shared/rules/security-boundaries.md`](../../../../shared/rules/security-boundaries.md).
- Confirm every state transition performed is one this role owns on the qa_execution task (ready → in-progress → in-review); confirm no label or state was written to any other task — especially not to the implementation task(s) the qa_execution depends on (cross-task regression invariant, [`../../CLAUDE.md`](../../CLAUDE.md) §"Cross-task regression semantics").

**Verifying the QA work is not the same as verifying the system under test.** A `qa_execution_failed` event is a valid completion of a qa-execution task — the QA agent's contract is to run the plan and report; whether the system passed is consumed by qa-regression. This distinction is carried over from [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification".

Failure handling follows [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable (e.g., event failed its own schema validation) → retry; three failed cycles → escalate `spinning_detected` on the **qa_execution task itself** (authoring/curation-style spinning, [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific escalation" first `spinning_detected` clause); spec-level blocker → escalate accordingly. A `qa_execution_failed` event is **not** a spinning signal — it is a normal outcome on the regression path.

## Worked example — three tests, three runs

Fictional feature `FEAT-2026-0061 — Widgets export rate-limit`, used for illustration. One `qa_execution` task `FEAT-2026-0061/T04` assigned to `clabonte/api-sample`. Plan at `/product/test-plans/FEAT-2026-0061.md` with three tests:

- `widgets-export-happy-path-200ok` — covers AC-1 (endpoint responds 200 under normal load).
- `widgets-export-rate-limit-enforced-429` — covers AC-2 (returns 429 after 100 req/min).
- `widgets-export-retry-after-header-present` — covers AC-3 (429 response carries `Retry-After` header).

### Run 1 — clean execution against commit `abc12345…`

1. Task flipped `ready → in-progress`. `task_started` emitted.
2. Plan file resolved, round-trips cleanly against `test-plan.schema.json`. `commit_sha = abc1234567890abcdef1234567890abcdef12345` (main HEAD of `clabonte/api-sample`).
3. Idempotence check: no prior `qa_execution_*` event in `/events/FEAT-2026-0061.jsonl` with matching `(task_correlation_id, commit_sha)`. Proceed.
4. Per-test loop:
   - `widgets-export-happy-path-200ok`: `curl` returns HTTP 200, body parses as 50 widgets. `expected` matches. → pass.
   - `widgets-export-rate-limit-enforced-429`: 100 requests succeed, 101st returns HTTP 429. `expected` matches. → pass.
   - `widgets-export-retry-after-header-present`: 429 response carries `Retry-After: 60`. `expected` matches. → pass.
5. Aggregate: all pass. Construct `qa_execution_completed`:
   ```json
   {
     "timestamp": "2026-04-23T18:10:00Z",
     "correlation_id": "FEAT-2026-0061",
     "event_type": "qa_execution_completed",
     "source": "qa",
     "source_version": "1.2.0",
     "payload": {
       "task_correlation_id": "FEAT-2026-0061/T04",
       "commit_sha": "abc1234567890abcdef1234567890abcdef12345",
       "plan_path": "/product/test-plans/FEAT-2026-0061.md",
       "test_count": 3,
       "total_duration_seconds": 4.2
     }
   }
   ```
6. Validate via `scripts/validate-event.py` (exit `0`), append to `/events/FEAT-2026-0061.jsonl`.
7. Task flipped `in-progress → in-review`. `task_completed` emitted. Stop.

Fixture: [`/shared/schemas/examples/qa_execution_completed.json`](../../../../shared/schemas/examples/qa_execution_completed.json).

### Run 2 — regression introduced, execution against commit `def56789…`

A hypothetical merge on `main` weakened the rate-limit check. `commit_sha = def56789abcdef0123456789abcdef0123456789`. A new `qa_execution` task `FEAT-2026-0061/T08` was opened via the WU 3.4 regression pipeline after T04 closed; T08 is the one picking up here. (Alternatively — and in the worked example the WU 3.3 run prototypes — the same T04 task can be re-opened as a new cycle if the PM agent's lifecycle supports it; WU 3.4 formalizes the spawning contract.)

1. Task flipped `ready → in-progress`. `task_started` emitted.
2. Plan resolved (unchanged). `commit_sha` = new SHA.
3. Idempotence check: no prior event for `(task_correlation_id, def567…)` — proceed. (The completed event from Run 1 carries `commit_sha = abc1234…`, which does not match.)
4. Per-test loop:
   - `widgets-export-happy-path-200ok`: → pass.
   - `widgets-export-rate-limit-enforced-429`: 100 requests succeed, 101st **also returns HTTP 200** (regression). `expected` does not match. → **fail**. Capture `first_signal = "HTTP 200 returned on 101st request; expected 429 Too Many Requests."`; command exit code was `0`.
   - `widgets-export-retry-after-header-present`: 429 never triggered in step 2, so no `Retry-After` to check. The test can either be skipped by its own precondition or recorded as a predicate-ambiguity failure. At v1, the skill treats it as a **fail with evidence** "preceding test did not elicit a 429 response; Retry-After header could not be verified" rather than silently passing.
     - *Decision rule for cascading failures at v1:* when a test's precondition implicitly depends on another test's outcome (as happens here — AC-3 depends on AC-2 having produced a 429), record the dependent test as a fail with evidence naming the upstream failure, not a skip. Tracking the independent failure forward is qa-regression's concern; silently skipping would hide data.
5. Aggregate: 2 failures. Construct `qa_execution_failed`:
   ```json
   {
     "payload": {
       "task_correlation_id": "FEAT-2026-0061/T04",
       "commit_sha": "def56789abcdef0123456789abcdef0123456789",
       "plan_path": "/product/test-plans/FEAT-2026-0061.md",
       "test_count": 3,
       "failed_tests": [
         {"test_id": "widgets-export-rate-limit-enforced-429", "first_signal": "HTTP 200 returned on 101st request; expected 429 Too Many Requests.", "exit_code": 0}
       ]
     }
   }
   ```
   *(In the fixture at [`/shared/schemas/examples/qa_execution_failed.json`](../../../../shared/schemas/examples/qa_execution_failed.json) only the load-bearing failure is inlined; a full example with both cascading failures would carry two entries in `failed_tests`.)*
6. Validate, append.
7. Task flipped `in-progress → in-review`. `task_completed` emitted — the QA task itself completed, even though the system under test failed.

Downstream: the `qa_execution_failed` event is what WU 3.4 (qa-regression) consumes to file a `/inbox/qa-regression/FEAT-2026-0061-widgets-export-rate-limit-enforced-429.md` artifact against the implementation repo. This skill stops at the event.

### Run 3 — replay against the same commit `def56789…` (idempotence)

A poller picks up the task again before the first run's close has propagated. Same `commit_sha`, same `task_correlation_id`.

1. Task flip attempted `ready → in-progress`, but the task is already `in-review` from Run 2 — the pickup itself is the idempotence guard at the task level. If the task *is* still `ready` (e.g. the Run 2 flip was rolled back by a concurrent action), proceed to step 3.
2. Plan resolved.
3. Idempotence check: **match found** on line `N` of `/events/FEAT-2026-0061.jsonl` — the `qa_execution_failed` from Run 2 carries the same `(task_correlation_id, commit_sha)`. **Do not emit a second event.** Report "idempotent skip: existing `qa_execution_failed` at line `N` for `(FEAT-2026-0061/T04, def56789abcdef0123456789abcdef0123456789)`".
4–6. Skipped.
7. Close the task (flip label, emit `task_completed`) if not already closed. Stop.

No duplicate event is written. The audit trail remains `task_started`, `qa_execution_failed`, `task_completed` for this `(task, commit)` pair — the idempotence guarantee the schema key encodes.

## Deferred integration — Phase 4 + Phase 5 brief

The v1 skill is a **stub** on two dimensions: predicate evaluation is prose-driven (agent judgment), and `commands` are free-form shell strings. Phase 4 and Phase 5 replace each dimension additively.

### What Phase 4 changes — machine-evaluable predicates

The `expected` field on each test moves from a prose predicate to a structured, machine-evaluable shape. Candidate languages:

- **JSONPath + assertion DSL** — e.g., `[{"path": "$.status", "op": "eq", "value": 200}, {"path": "$.items", "op": "len_eq", "value": 50}]`. Simple; covers 80% of HTTP-response assertions.
- **CEL (Common Expression Language)** — e.g., `response.status == 200 && size(response.body.items) == 50`. More expressive, widely deployed (Kubernetes, gRPC).
- **Custom mini-DSL** — tailored to the orchestrator's needs; maximally expressive but highest maintenance burden.

The Phase 4 WU picks one based on the Phase 3 walkthrough (WU 3.6) evidence — which `expected` prose patterns recurred, which edge cases made the agent stretch.

Additional Phase 4 structural changes (all additive — the v1 stub remains valid):

- **Arazzo-backed `commands`** — commands gain structure (operation refs, input bindings, output capture), shared with qa-authoring's Phase 4 evolution. See [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) §"Deferred integration".
- **Explicit `preconditions`** — a test can declare state it requires (fixtures, seed data, feature flags). Phase 3 treats precondition failures as cascading fails with evidence (see Run 2 decision rule); Phase 4 structures it.
- **Cascade semantics formalized** — the informal "cascading fail with evidence" rule from Run 2 becomes an explicit `depends_on_test` field on test entries, and execution records cascaded failures with a `kind: cascaded` marker in `failed_tests[].first_signal`.

### What Phase 5 changes — generator-emitted skeletons

When the Specfuse generator emits test-plan skeletons (Phase 5, see [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) §"Deferred integration"), qa-execution stays largely unchanged — the skeleton-based plans produced by the generator are still authored by qa-authoring (in completion+verification mode) before reaching qa-execution. What changes is that the `commands` are more uniform (generator conventions), which simplifies predicate evaluation and opens the door to tighter structural assertions (e.g. auto-generated response-schema conformance).

### What persists across Phase 4 and Phase 5

- **Idempotence key `(task_correlation_id, commit_sha)`** — load-bearing across every future phase. Any Phase 4+ evolution of this skill **must** preserve the pair as the emission guard.
- **`(qa_execution_completed, qa_execution_failed)` event pair** — the envelope is the contract qa-regression (WU 3.4) consumes. Payload fields are additive; removal or rename would be a breaking migration.
- **`failed_tests[]` shape** — `test_id` + `first_signal` remain the minimum. Phase 4 adds optional fields (cascade marker, predicate evaluator trace); the minimum set does not shrink.
- **Verifying-QA-work vs. verifying-system-under-test distinction** — `qa_execution_failed` is always a valid QA-task completion signal. Phase 4 and Phase 5 inherit this posture unchanged.

## Finding 8 disposition (Q6 check)

**Decision: Finding 8 does NOT apply to qa-execution at v1. The carry to Phase 5 is reaffirmed.**

Phase 1 retrospective Finding 8 ([`docs/walkthroughs/phase-1/retrospective.md`](../../../../docs/walkthroughs/phase-1/retrospective.md) §"Finding 8"): the component agent's coverage gate can produce a misleading coverage value when `dotnet test --no-build` runs against stale `bin/`/`obj/` artifacts from earlier edits. Disposition at Phase 1 close: defer to Phase 2+, opportunistic carry to the next edit of [`/agents/component/skills/verification/SKILL.md`](../../../../agents/component/skills/verification/SKILL.md).

The Q6 check for this WU asks: does the `--no-build` stale-artifact risk extend to qa-execution correctness? Analysis:

1. **qa-execution never invokes `--no-build` or any equivalent.** Its `commands` are black-box — HTTP calls, CLI invocations, shell probes against a running system. They observe the system's behavior, not cached compilation artifacts.
2. **qa-execution runs after the component agent's verification has passed.** The qa_execution task's `depends_on` includes the implementation tasks per WU 2.10's task-decomposition rules; a qa_execution task becomes `ready` only after its implementation dependencies are `done` (merged). A Finding 8 false-positive on the upstream coverage gate would incorrectly release the qa_execution task, but qa-execution itself would then observe the actual running system — either (a) producing a correct `qa_execution_completed` or `qa_execution_failed` based on reality, or (b) failing due to an inconsistent build that Finding 8's fix would have caught earlier.
3. **The indirect risk: `commands` that target a pre-started service built from stale source.** If a plan's `commands` assume a background service whose build provenance is stale, qa-execution could test the wrong binary. This skill mitigates the risk in two ways:
   - **Stateless command discipline.** The skill does not cache build artifacts or service state between tests; every command is invoked fresh against the system at `commit_sha`.
   - **Provenance escalation.** If a plan's `commands` require a pre-started service whose provenance is not documented in the feature's `## Scope` or the repo's `.specfuse/verification.yml`, the skill escalates `spec_level_blocker` rather than executing with ambiguous provenance. This is covered by the step-4 predicate-ambiguity escalation rule — a command whose environment cannot be reconciled with `commit_sha` is not runnable at v1.

The Finding 8 risk is therefore **localized** to the component agent's coverage gate. qa-execution does not re-introduce the risk, does not depend on the coverage gate's output for its own correctness, and does not need a fix at this WU.

**No follow-on Phase 3 fix WU is surfaced by this WU.** Finding 8 remains on the Phase 1-retrospective carry list with Phase 5 (or the next opportunistic edit of `verification/SKILL.md`) as its named home. The commit message records this disposition explicitly per WU 3.3 AC #2.

## What this skill does not do

- It does **not** file regression artifacts on failure. The `qa_execution_failed` event is the signal; qa-regression (WU 3.4) consumes it.
- It does **not** flip labels or state on any task other than the `qa_execution` task this instance owns. In particular, it never writes to the implementation task(s) this qa_execution depends on, even when the system under test fails (cross-task regression invariant — [`../../CLAUDE.md`](../../CLAUDE.md) §"Cross-task regression semantics").
- It does **not** build the component under test. The component agent's verification has produced buildable artifacts before qa_execution runs.
- It does **not** modify the test plan. Plan changes are qa-curation's concern (WU 3.5).
- It does **not** cache build artifacts, plan files, or the event log between invocations. Every pickup re-reads fresh.
- It does **not** skip a test for convenience. Every declared command is run; every test has a definite pass/fail verdict.
- It does **not** re-emit an event when the idempotence check finds a match. A duplicate would cascade into duplicate regression signals downstream.
- It does **not** swallow unexpected command outputs. Predicate ambiguity escalates `spec_level_blocker` rather than silently passing the test.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §4.3 (test plan location), §6.2 (task types), §6.3 (transition ownership), §6.4 (regression-vs-escalation rule — which `qa_execution_failed` is NOT an instance of), §7.3 (event log), §10 (branch-protection gates, which produced the artifacts qa-execution runs against).
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 3.3" — the work unit that authored this skill.
- [`/docs/walkthroughs/phase-1/retrospective.md`](../../../../docs/walkthroughs/phase-1/retrospective.md) §"Finding 8" — the Q6 check input.
- [`/shared/schemas/test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — the plan contract this skill consumes.
- [`/shared/schemas/events/qa_execution_completed.schema.json`](../../../../shared/schemas/events/qa_execution_completed.schema.json) — success-event payload contract.
- [`/shared/schemas/events/qa_execution_failed.schema.json`](../../../../shared/schemas/events/qa_execution_failed.schema.json) — failure-event payload contract.
- [`/shared/schemas/examples/qa_execution_completed.json`](../../../../shared/schemas/examples/qa_execution_completed.json) — worked-example fixture (Run 1).
- [`/shared/schemas/examples/qa_execution_failed.json`](../../../../shared/schemas/examples/qa_execution_failed.json) — worked-example fixture (Run 2).
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — envelope; `qa_execution_completed` and `qa_execution_failed` added to the enum in this WU.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 — universal discipline; per-type payload validation applies to both emitted events automatically.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally per invocation.
- [`/shared/rules/security-boundaries.md`](../../../../shared/rules/security-boundaries.md) §"Log hygiene" — redaction discipline for `first_signal` and `stderr_excerpt`.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — escalation surface (`spec_level_blocker`, `spinning_detected` on the qa_execution task).
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — applies the per-type payload schemas.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
- [`../../CLAUDE.md`](../../CLAUDE.md) — the QA role config; §"Role-specific verification" enshrines the verifying-QA-work vs. verifying-SUT distinction this skill honors, and §"Cross-task regression semantics" fixes the cross-task invariant.
- [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) — upstream skill (WU 3.2) that writes the plan this one consumes.
- [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) — downstream skill (WU 3.4) that consumes `qa_execution_failed` events.
- [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) — further downstream (WU 3.5) handling plan-level structural changes.
- [`/agents/component/skills/verification/SKILL.md`](../../../../agents/component/skills/verification/SKILL.md) — frozen at v1.1; this skill depends on its output (buildable artifacts) but does not modify it (Finding 8 disposition).
