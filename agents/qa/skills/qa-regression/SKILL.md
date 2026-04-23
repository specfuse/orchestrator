# QA agent — qa-regression skill (v1.0)

## Purpose

This skill reacts to `qa_execution_failed` and `qa_execution_completed` events on any feature's event log. On a first failure for a given `(implementation_task_correlation_id, test_id)` pair, it files a regression artifact at `/inbox/qa-regression/<FEAT>-<TESTID>.md` — the substrate from which a NEW `implementation` task is spawned against the component repo under test — and emits `qa_regression_filed`. On a repeat failure after a linked fix attempt, it escalates `spinning_detected` on the ORIGINAL implementation task via a `human_escalation` event, without filing a second regression artifact. On a subsequent `qa_execution_completed` that certifies the failing test now passes at a post-dating commit, it emits `qa_regression_resolved`, and — if the regression had been escalated — additionally emits `escalation_resolved` (`resolution_kind: qa_regression_resolved`).

The skill is the machine-readable implementation of the **Q4 cross-task regression invariant** codified in [`../../CLAUDE.md`](../../CLAUDE.md) §"Cross-task regression semantics": the QA agent never writes labels or state to a task it does not own. The implementation task under test is untouched by every path below; follow-on implementation work flows through the inbox artifact; follow-on escalations flow through the human-escalation inbox.

## Scope

In scope:

- Consuming one `qa_execution_failed` or `qa_execution_completed` event per invocation as the trigger.
- Resolving the `implementation_task_correlation_id` being regressed against from the feature task graph (Q4 algorithm; see §"Step 3 — Resolve implementation_task_correlation_id from the task graph").
- Writing the regression inbox artifact on first failure, using the [`qa-regression-issue.md`](../../../../shared/templates/qa-regression-issue.md) template (v0.2).
- Emitting `qa_regression_filed`, `qa_regression_resolved`, and `escalation_resolved` events through [`scripts/validate-event.py`](../../../../scripts/validate-event.py).
- Escalating `spinning_detected` on the original implementation task on the repeat-failure path, via a `human_escalation` event and an inbox file under `/inbox/human-escalation/`.
- Enforcing the idempotence key `(implementation_task_correlation_id, test_id)` across first-failure, repeat-failure, and resolution paths.

Out of scope (each belongs to a sibling skill, a later phase, or another role):

- **Running test plans** — [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md), WU 3.3. This skill consumes its events; it never runs a plan itself.
- **Spawning the regression-fix implementation task.** The inbox artifact is the handoff; the PM inbox consumer (future WU) or the human picks the file up, mints the new task's correlation ID, opens the issue against the target repo, and transitions it through its lifecycle. This skill stops at the inbox write.
- **Curating the regression suite** — [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md), WU 3.5. The curation skill's "open-regression protection" rule reads this skill's `qa_regression_filed` / `qa_regression_resolved` event pairs; the matching discipline is defined here, the protection check lives there.
- **Feature-level state transitions.** The PM agent owns feature state. A regression does not change feature state — the feature stays `in_progress` while QA and the component agent iterate.
- **Writes to the implementation task under test, to component-repo code paths, or to `/product/`.** The single-owner invariant and the "Output artifacts" section of [`../../CLAUDE.md`](../../CLAUDE.md) forbid all three.

## Inputs

Per invocation:

1. The **triggering event** — either a `qa_execution_failed` or a `qa_execution_completed` line on some feature's event log (object or file pointer, deployment-dependent). Same "skill is a function, trigger is external" posture as [`../../../pm/skills/dependency-recomputation/SKILL.md`](../../../pm/skills/dependency-recomputation/SKILL.md); see §"Trigger — external invocation" below.
2. The **feature registry** at `/features/<feature_correlation_id>.md` in the orchestration repo — its frontmatter (`correlation_id`, `task_graph`, `involved_repos`) carries the authoritative `depends_on` / `assigned_repo` mapping this skill resolves `implementation_task_correlation_id` against.
3. The **feature event log** at `/events/<feature_correlation_id>.jsonl` — read end-to-end each invocation (no caching) to perform the idempotence and linked-fix-attempt checks.
4. The **failing test plan** at `/product/test-plans/<feature_correlation_id>.md` in the product specs repo — read on the first-failure path to extract the test's `expected` predicate and `commands` for inclusion in the inbox artifact body.
5. [`../../CLAUDE.md`](../../CLAUDE.md), this skill, and [`/shared/rules/`](../../../../shared/rules/) — reloaded per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

The skill does **not** read or write to the component repo(s) under test, does **not** open a GitHub issue against the implementation task, and does **not** modify any existing inbox file outside its own writes under `/inbox/qa-regression/` and (on the repeat-failure path) `/inbox/human-escalation/`.

## Outputs

Per invocation, depending on path:

- **First-failure path** — one regression inbox artifact written to `/inbox/qa-regression/<feature_correlation_id>-<test_id>.md`, one `qa_regression_filed` event appended to the feature event log.
- **Repeat-failure path** — one `human_escalation` inbox file written to `/inbox/human-escalation/<feature_correlation_id>-<TNN>-qa-regression-spinning.md`, one `human_escalation` event (reason `spinning_detected`, correlation_id task-level on the original implementation task) appended.
- **Resolution path** — one `qa_regression_resolved` event appended. If the paired regression had been escalated, additionally one `escalation_resolved` event (`resolution_kind: qa_regression_resolved`) appended.
- **Idempotent-skip paths** — zero writes; the invocation returns cleanly.

No writes to the implementation task under test. No writes to feature frontmatter. No writes to component-repo code paths, to `/product/`, or to `/overrides/`. Every event round-trips through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) before append; every file write is re-read afterward per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3.

## Trigger — external invocation

The trigger-detection mechanism is deliberately **outside this skill**, same posture as [`../../../pm/skills/dependency-recomputation/SKILL.md`](../../../pm/skills/dependency-recomputation/SKILL.md) §"Trigger — external invocation". The skill exposes a procedure that some invoking actor calls with the feature-level correlation ID and a reference to the triggering event. Candidate invokers (any acceptable, deployment choice):

- A polling loop that tails every `/events/FEAT-*.jsonl` file and runs the skill on each new `qa_execution_failed` or `qa_execution_completed` line detected since the last cursor position.
- A CLI (`scripts/run-qa-regression.sh <feature_correlation_id> <event_line>`) the human runs manually after acknowledging a qa-execution run.
- A GitHub webhook on `workflow_run.completed` that emits the `qa_execution_*` event and invokes this skill in the same handler.
- A file-watcher on the event log during local development.

The skill takes the feature-level correlation ID and the triggering event (as parsed object or line pointer) from the invoker. It does not poll, does not schedule itself, and does not persist state across invocations — every invocation reads the feature registry, the event log, and the plan file fresh.

## The regression procedure

The skill dispatches on the triggering event type. Steps 1–3 are common to every path; steps 4–6 are the per-path branches.

### Step 1 — State intent and reload hygiene

Per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1, state the intent in one line. For a failure trigger: "I will process a qa-regression signal for `<feature_correlation_id>` in response to `<event_type>` at `<event_ts>`." For a completion trigger: "I will scan open regressions on `<feature_correlation_id>` for resolution against `qa_execution_completed` at `<event_ts>`."

Reload [`/shared/rules/*`](../../../../shared/rules/), this skill file, and [`../../CLAUDE.md`](../../CLAUDE.md) per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — unconditional, including on back-to-back invocations in the same session.

### Step 2 — Read the feature context

Read the feature registry at `/features/<feature_correlation_id>.md`. Parse the frontmatter and confirm:

- `correlation_id` matches the invoker-supplied feature ID.
- `task_graph` is non-empty.
- The triggering event's `payload.task_correlation_id` matches a task ID in the graph (feature prefix + `/TNN`).

If any check fails, the triggering event is malformed relative to the feature registry — escalate `spec_level_blocker` with reason "qa-regression triggered by `<event_type>` whose `payload.task_correlation_id` `<X>` is not in the task graph of `<feature>`" and stop.

Read the feature event log `/events/<feature_correlation_id>.jsonl` end-to-end. The read must be **fresh** on every invocation — no cached snapshots, no stored cursors — because idempotence and linked-fix-attempt checks depend on the log's current tail (see [`../../CLAUDE.md`](../../CLAUDE.md) §"Anti-patterns" #12).

### Step 3 — Resolve `implementation_task_correlation_id` from the task graph

Given the triggering event's `payload.task_correlation_id` (the qa_execution task that produced the signal), resolve the original implementation task being regressed against via the Q4 algorithm:

1. Find the qa_execution task in `task_graph` by its TNN.
2. Collect its `depends_on` list and filter to entries whose `type` is `implementation`.
3. Branch on the filtered set's size:
   - **Exactly 1 implementation task** — that is the `implementation_task_correlation_id`. Return `<feature>/<impl_TNN>`. This is the common case under the WU 2.10 same-behavior grouping convention (each qa_execution covers one cohesive implementation-task group; cross-repo features typically produce one qa_execution per repo with a single impl dependency).
   - **More than 1 implementation task** — the test→implementation mapping is ambiguous from the task graph alone at v1. Escalate `spec_level_blocker` with reason "ambiguous implementation-task attribution for failing test_id `<X>`: qa_execution `<T>` depends_on carries implementation tasks `[T02, T03, …]`; the feature task graph does not record which test_id maps onto which implementation task". **The skill does not guess.** Phase 4 can resolve this by enriching the task graph with a per-test `covers` linkage; until then, ambiguity routes through the human via a spec issue.
   - **Zero implementation tasks** — malformed graph (a qa_execution with no implementation dependency cannot regression-attribute). Escalate `spec_level_blocker` with reason "qa_execution task `<T>` has no implementation tasks in depends_on — cannot attribute regression".

On a `qa_execution_completed` trigger, step 3 still runs (the resolution path needs the attribution to key the resolution against prior `qa_regression_filed` events), but the failure modes are the same: ambiguity or zero impl tasks → `spec_level_blocker`.

### Step 4A — First-failure path (triggered by `qa_execution_failed`)

Entered when the triggering event is a `qa_execution_failed`. For each entry in its `payload.failed_tests[]` (there may be multiple in one execution event; each is handled independently):

**4A.1 — Idempotence check.** Scan the feature event log for any prior `qa_regression_filed` entry where `payload.implementation_task_correlation_id` equals the resolved impl task ID and `payload.test_id` equals the failed test's `test_id`.

- **No prior filing** — proceed to 4A.2 (first-failure write).
- **Prior filing exists** — this is a repeat failure candidate. Jump to Step 4B (repeat-failure path) for this test_id.

**4A.2 — Read the plan file.** Read `/product/test-plans/<feature_correlation_id>.md` in the product specs repo. Parse the YAML frontmatter (the plan schema is governed by [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json); the skill relies on that validation having already been performed by qa-authoring and qa-execution). Locate the test entry whose `test_id` matches the failing one. Capture its `expected`, `commands`, and `covers` fields for the inbox artifact body.

**4A.3 — Resolve the target repo.** From the feature registry's `task_graph`, read the original implementation task's `assigned_repo` field. That is the repo the spawned regression-fix task will target.

**4A.4 — Write the inbox artifact.** Compose the file at `/inbox/qa-regression/<feature_correlation_id>-<test_id>.md` using the [`qa-regression-issue.md`](../../../../shared/templates/qa-regression-issue.md) template (v0.2). Frontmatter fields:

```yaml
---
correlation_id_feature: <feature_correlation_id>
test_id: <test_id>
regressed_implementation_task_correlation_id: <feature>/<impl_TNN>
failing_qa_execution_event_ts: <triggering event's timestamp>
failing_commit_sha: <triggering event's payload.commit_sha>
test_plan_path: /product/test-plans/<feature_correlation_id>.md
target_repo: <assigned_repo from the original impl task>
---
```

Body: the test plan's `expected` as "Expected behavior", the failed entry's `first_signal` (from the triggering event's `payload.failed_tests[]`) as "Observed behavior", the plan's `commands` expanded as numbered "Reproduction steps", and a "Regression context" block mirroring the frontmatter for the human reader of the spawned task issue.

Re-read the written file and confirm the frontmatter and body match what was composed, per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3.

**4A.5 — Emit `qa_regression_filed`.** Construct:

```json
{
  "timestamp": "<ISO-8601 now>",
  "correlation_id": "<feature_correlation_id>",
  "event_type": "qa_regression_filed",
  "source": "qa",
  "source_version": "<from scripts/read-agent-version.sh qa>",
  "payload": {
    "implementation_task_correlation_id": "<feature>/<impl_TNN>",
    "test_id": "<test_id>",
    "failing_qa_execution_event_ts": "<triggering event ts>",
    "failing_commit_sha": "<triggering event payload.commit_sha>",
    "regression_inbox_file": "inbox/qa-regression/<feature>-<test_id>.md"
  }
}
```

Pipe through [`scripts/validate-event.py`](../../../../scripts/validate-event.py); require exit `0`. Append to `/events/<feature_correlation_id>.jsonl`. Re-read the appended line.

### Step 4B — Repeat-failure path (triggered by `qa_execution_failed`, prior filing exists)

Entered from 4A.1 when a prior `qa_regression_filed` exists for the `(impl_task, test_id)` pair.

**4B.1 — Linked fix attempt check.** Walk the feature event log for a `task_completed` event whose:

- timestamp is strictly greater than the prior `qa_regression_filed` event's timestamp, **and**
- `correlation_id` is task-level (`FEAT-YYYY-NNNN/TNN` shape) on the SAME feature, **and**
- `correlation_id` is **not** the original implementation task's correlation ID (a `task_completed` on the original impl task is the completion that predates the first failure; a fix attempt is a `task_completed` on a DIFFERENT task — specifically the regression-fix task spawned from the inbox artifact).

Branch:

- **No matching `task_completed` found** — no fix attempt has landed yet. The qa-execution re-ran (or was replayed) against the same failing code. **Do not escalate, do not file a second artifact.** Log "idempotent skip: prior qa_regression_filed at `<ts>` still open, no linked fix attempt detected" and return. The prior artifact and the prior `qa_regression_filed` event remain the authoritative signal.
- **Matching `task_completed` found** — a fix attempt has completed but the failure reproduces. Proceed to 4B.2.

**4B.2 — Idempotence guard on the escalation.** Scan the feature event log for any prior `human_escalation` event where `correlation_id` is the ORIGINAL implementation task's correlation ID AND `payload.reason` is `spinning_detected` AND timestamp is newer than the most recent `qa_regression_filed` for the pair. If such an escalation already exists, **do not re-escalate** — the prior escalation is still outstanding. Log "idempotent skip: spinning_detected already escalated on `<impl_task>` at `<ts>`" and return.

**4B.3 — Write the human-escalation inbox file.** Compose `/inbox/human-escalation/<feature>-<impl_TNN>-qa-regression-spinning.md` using [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md) per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md). Correlation ID in the file: task-level on the ORIGINAL implementation task. Reason: `spinning_detected`. "Agent state" section: name the failing test_id, the prior qa_regression_filed ts, the linked fix attempt's task correlation ID and ts, the current qa_execution_failed ts. "Decision requested" section: enumerate the human's options (re-plan the implementation task; abandon the test; re-open the spec for the failing behavior).

**4B.4 — Emit `human_escalation`.** Correlation ID task-level (original impl task). Payload per [`human_escalation.schema.json`](../../../../shared/schemas/events/human_escalation.schema.json): `{"reason": "spinning_detected", "inbox_file": "inbox/human-escalation/<feature>-<impl_TNN>-qa-regression-spinning.md", "summary": "<one sentence: test_id `<X>` re-failed after a linked fix attempt on `<spawned task>`; spinning on original implementation task `<impl_TNN>`>"}`.

Validate via `scripts/validate-event.py`, append, re-read. Do **not** file a second `qa_regression_filed` (anti-pattern #6 in [`../../CLAUDE.md`](../../CLAUDE.md)).

**4B.5 — Stop.** No state transition on the original implementation task: the QA agent does not flip its label (per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"State machine effects of raising an escalation" — that section governs the escalating agent's OWN task's transition; the QA task here is the qa_execution task which already reached `in_review` when the failed event was emitted; the original implementation task is NOT a QA-owned task and is therefore not transitioned by this skill. If the human decides the spinning warrants a `blocked_human` label on the implementation task, the human applies it; QA does not).

### Step 4C — Resolution path (triggered by `qa_execution_completed`)

Entered when the triggering event is a `qa_execution_completed`. For each `test_id` in the plan file (read it fresh — see 4A.2 for parse conventions), run the following:

**4C.1 — Open regression check.** Scan the feature event log for `qa_regression_filed` events where `payload.implementation_task_correlation_id` equals the resolved impl task ID and `payload.test_id` equals the current test's `test_id`. For each, check whether a matching `qa_regression_resolved` (same impl task + test_id, with `filed_event_ts` equal to the filed event's timestamp) already exists. Discard any `qa_regression_filed` that is already resolved. The remainder is the **open regression set** for this test_id (typically at most one; more than one would indicate a prior skill bug — log and escalate `spec_level_blocker` if seen).

- **Open set empty** — no outstanding regression for this test_id. Skip to the next test_id.
- **Open set non-empty** — proceed to 4C.2.

**4C.2 — Resolution eligibility.** For each open `qa_regression_filed`:

- Confirm the triggering `qa_execution_completed`'s `payload.commit_sha` is **different** from the filed event's `payload.failing_commit_sha`. A match means the completed execution ran against the same code as the failure — a contradictory signal (the qa-execution skill's idempotence should have prevented this; if it occurs, log and skip without emitting — do not fabricate a resolution from a contradiction).
- Confirm the triggering event's timestamp is strictly greater than the filed event's timestamp (chronological post-dating).

If both conditions hold, proceed to 4C.3. Otherwise skip.

**4C.3 — Emit `qa_regression_resolved`.** Construct:

```json
{
  "timestamp": "<ISO-8601 now>",
  "correlation_id": "<feature_correlation_id>",
  "event_type": "qa_regression_resolved",
  "source": "qa",
  "source_version": "<from scripts/read-agent-version.sh qa>",
  "payload": {
    "implementation_task_correlation_id": "<feature>/<impl_TNN>",
    "test_id": "<test_id>",
    "filed_event_ts": "<filed event timestamp>",
    "resolving_qa_execution_event_ts": "<triggering event timestamp>",
    "resolving_commit_sha": "<triggering event payload.commit_sha>"
  }
}
```

Validate, append, re-read.

**4C.4 — Emit `escalation_resolved` if escalation outstanding.** Scan the feature event log for a `human_escalation` event with `correlation_id` equal to the ORIGINAL implementation task's correlation ID, `payload.reason` equal to `spinning_detected`, timestamp between the filed event and the triggering `qa_execution_completed`, and no subsequent `escalation_resolved` already matching it. If found:

```json
{
  "timestamp": "<ISO-8601 now>",
  "correlation_id": "<impl_task correlation_id>",
  "event_type": "escalation_resolved",
  "source": "qa",
  "source_version": "<from scripts/read-agent-version.sh qa>",
  "payload": {
    "resolution_kind": "qa_regression_resolved",
    "resolved_escalation_event_ts": "<human_escalation ts>",
    "resolved_escalation_inbox_file": "<human_escalation's payload.inbox_file>",
    "summary": "qa-execution at commit <resolving_sha> passes test_id <X>; prior spinning_detected escalation on <impl_task> retired."
  }
}
```

The envelope `correlation_id` is **task-level** here — it matches the `human_escalation` being resolved. Validate, append, re-read.

If no matching human_escalation is found, 4C.4 is a no-op for this test_id.

### Step 5 — Return

When every test_id from the triggering event's payload has been processed (one per entry in `failed_tests[]` on the failure path; every plan test on the completion path), the invocation is complete. The skill returns to its invoker. No summary event (`regression_pass_complete` or similar) is emitted — the filed/resolved/escalation events are the complete record.

## Idempotence discipline

Idempotence under replay is a load-bearing correctness bar. Three mechanisms make a replayed `qa_execution_*` event a no-op:

### Fresh event-log scan before every write

Steps 4A.1, 4B.1, 4B.2, 4C.1, and 4C.4 all read the feature event log end-to-end on the current invocation — no cached snapshots. A replay finds the prior filed / resolved / escalated event in the log and branches to the skip path. This is the primary guard.

### Idempotence key `(implementation_task_correlation_id, test_id)`

Every write path keys off this pair. A second `qa_regression_filed` for the same pair is forbidden by the repeat-failure branch at 4A.1; a second `qa_regression_resolved` is forbidden by the "already resolved" check at 4C.1; a second `spinning_detected` escalation is forbidden by 4B.2. No skill action modifies the pair's interpretation — it is extracted from the event payloads and compared byte-for-byte.

### Deterministic test_id processing order

On a multi-failure `qa_execution_failed` (several tests failed in one run), the skill processes `failed_tests[]` in array order (the same stable order qa-execution emits — see [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) §"Step 5"). A partial-progress invocation that crashes after filing for test 1 but before filing for test 2 resumes safely on replay: test 1's filing is detected and skipped, test 2's filing proceeds.

### What idempotence does NOT require

- **A persistent cursor on the event log.** The live scan is authoritative; cursor state would introduce a new class of bug (stale cursors across invocations, races between concurrent invokers).
- **Transactional multi-event emission.** If the skill writes the inbox file and then crashes before emitting `qa_regression_filed`, the inbox file is present but the event is not. The next replay's idempotence scan (4A.1) finds no event and proceeds to re-write the inbox file (overwrite, byte-identical if inputs match) and emit the event. No state rollback needed.
- **Cross-feature coordination.** One invocation = one feature = one triggering event. The skill does not batch across features.

## Verification

Before returning from any invocation, the skill confirms the following. **The first bullet is the grep-able Q4 invariant clause** — codified verbatim in [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification" for this skill.

- **No write to labels or state on any task other than the QA task itself.** Specifically: no write to labels or state on the ORIGINAL implementation task under test, no write to labels or state on any spawned regression-fix task, no write to labels or state on any other task the QA agent does not own. The skill's writes are confined to (a) files under `/inbox/qa-regression/` and `/inbox/human-escalation/`, (b) event lines appended to `/events/<feature>.jsonl`. A review of every write path in this skill confirms no `gh issue edit` or label-mutation call exists on any task-level correlation ID other than the qa_execution task that triggered the invocation, and that qa_execution task's transitions are already owned by [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md), not by this skill.
- The triggering event's `event_type` was `qa_execution_failed` or `qa_execution_completed` and its payload round-tripped through its per-type schema at parse time.
- The `implementation_task_correlation_id` resolved in step 3 via the Q4 algorithm is a task ID that appears in the feature registry's `task_graph`, with `type: implementation`.
- On the first-failure path: the inbox artifact at `inbox/qa-regression/<feature>-<test_id>.md` was written AND re-read AND its frontmatter parses AND its frontmatter fields match the triggering event's payload.
- On every emission path: every event round-trips through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) with exit `0` (envelope + per-type payload), was appended to the feature event log, and was re-read as a valid JSONL line.
- `source_version` on every skill-emitted event (`qa_regression_filed`, `qa_regression_resolved`, `human_escalation`, `escalation_resolved`) was produced by [`scripts/read-agent-version.sh qa`](../../../../scripts/read-agent-version.sh) at emission time.
- No secret-looking value appears in any written payload or inbox file per [`/shared/rules/security-boundaries.md`](../../../../shared/rules/security-boundaries.md) §"Log hygiene" (the `first_signal` carried from the upstream `qa_execution_failed` has already been redacted by qa-execution, but the skill re-checks before inclusion in the inbox body).
- Every correlation ID written matches the pattern in [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md): feature-level for `qa_regression_filed` / `qa_regression_resolved` envelopes; task-level (original impl task) for `human_escalation` / `escalation_resolved` envelopes on the repeat-failure and its resolution.
- No path written is in [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md). Specifically: `inbox/qa-regression/` is a new inbox subdirectory, additive per architecture §7.4's extensibility clause; `inbox/human-escalation/` is the existing escalation inbox governed by [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md); `/events/<feature>.jsonl` is the feature event log.

Failure handling follows [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable (e.g., event failed its own schema validation) → retry once with re-validation; three failed cycles on the same `(impl_task, test_id)` pair → escalate `spinning_detected` **on the qa-regression invocation as a whole, keyed on the feature-level correlation ID**, not on the original implementation task (this branch is a QA-internal spin, distinct from the 4B spinning path which is about the system under test); spec-level blocker → escalate accordingly per step 2 and step 3's branches.

## Worked example 1 — Full resolution loop (FEAT-2026-0061)

Continuation of the WU 3.3 example at [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) §"Worked example — three tests, three runs". The feature `FEAT-2026-0061 — Widgets export rate-limit` has task graph (frontmatter excerpt):

```yaml
task_graph:
  - id: T01
    type: qa_authoring
    depends_on: []
    assigned_repo: clabonte/api-sample
  - id: T02
    type: implementation
    depends_on: []
    assigned_repo: clabonte/api-sample
  - id: T03
    type: implementation
    depends_on: []
    assigned_repo: clabonte/persistence-sample
  - id: T04
    type: qa_execution
    depends_on: [T02, T01]
    assigned_repo: clabonte/api-sample
    autonomy: review
```

T04 `qa_execution` depends on T02 (impl, `clabonte/api-sample` — the rate-limit middleware) and T01 (qa_authoring). Filtered to `type: implementation`, T04's depends_on is `[T02]` — exactly one. Q4 attribution resolves unambiguously to `FEAT-2026-0061/T02`.

### Invocation A — first failure

Triggering event on `/events/FEAT-2026-0061.jsonl` (from WU 3.3 Run 2):

```json
{
  "timestamp": "2026-04-23T18:42:00Z",
  "correlation_id": "FEAT-2026-0061",
  "event_type": "qa_execution_failed",
  "source": "qa",
  "source_version": "1.2.0",
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

**Step 1** — intent: "I will process a qa-regression signal for FEAT-2026-0061 in response to qa_execution_failed at 2026-04-23T18:42:00Z." Rules reloaded.

**Step 2** — feature registry read; `task_graph` parses; T04 is in the graph. Event log read fresh.

**Step 3** — Q4 resolution: T04's `depends_on` filtered to implementation = `[T02]` — exactly one. `implementation_task_correlation_id = FEAT-2026-0061/T02`.

**Step 4A** — failed_tests has one entry: `widgets-export-rate-limit-enforced-429`.

- 4A.1: no prior `qa_regression_filed` with `(FEAT-2026-0061/T02, widgets-export-rate-limit-enforced-429)`. Proceed.
- 4A.2: plan file read; test entry located; `expected = "101st request in a rolling minute window returns HTTP 429"`, `commands = [curl loop]`, `covers = "AC-2: …"`.
- 4A.3: T02's `assigned_repo = clabonte/api-sample`.
- 4A.4: write `/inbox/qa-regression/FEAT-2026-0061-widgets-export-rate-limit-enforced-429.md`:

```markdown
---
correlation_id_feature: FEAT-2026-0061
test_id: widgets-export-rate-limit-enforced-429
regressed_implementation_task_correlation_id: FEAT-2026-0061/T02
failing_qa_execution_event_ts: 2026-04-23T18:42:00Z
failing_commit_sha: def56789abcdef0123456789abcdef0123456789
test_plan_path: /product/test-plans/FEAT-2026-0061.md
target_repo: clabonte/api-sample
---

## Failed test

- Test plan: /product/test-plans/FEAT-2026-0061.md
- Test ID: widgets-export-rate-limit-enforced-429

## Expected behavior

101st request in a rolling minute window returns HTTP 429 Too Many Requests.

## Observed behavior

HTTP 200 returned on 101st request; expected 429 Too Many Requests.

## Reproduction steps

1. Start the api-sample service at commit def56789abcdef0123456789abcdef0123456789.
2. Issue 101 sequential requests to `GET /widgets/export` within a one-minute window.
3. Confirm the 101st response's HTTP status.

## Regression context

- Regressed against implementation task: FEAT-2026-0061/T02
- Failing commit: def56789abcdef0123456789abcdef0123456789
- Failing qa_execution event timestamp: 2026-04-23T18:42:00Z
- Target repo: clabonte/api-sample
```

Re-read confirms.

- 4A.5: emit `qa_regression_filed`:

```json
{
  "timestamp": "2026-04-23T18:44:00Z",
  "correlation_id": "FEAT-2026-0061",
  "event_type": "qa_regression_filed",
  "source": "qa",
  "source_version": "1.3.0",
  "payload": {
    "implementation_task_correlation_id": "FEAT-2026-0061/T02",
    "test_id": "widgets-export-rate-limit-enforced-429",
    "failing_qa_execution_event_ts": "2026-04-23T18:42:00Z",
    "failing_commit_sha": "def56789abcdef0123456789abcdef0123456789",
    "regression_inbox_file": "inbox/qa-regression/FEAT-2026-0061-widgets-export-rate-limit-enforced-429.md"
  }
}
```

Validates (envelope + per-type payload), appended, re-read. See [`/shared/schemas/examples/qa_regression_filed.json`](../../../../shared/schemas/examples/qa_regression_filed.json) for the fixture.

Invocation A returns. Time passes: a PM inbox consumer (or the human) reads the inbox file, mints a new implementation task correlation ID `FEAT-2026-0061/T05`, opens a fresh issue against `clabonte/api-sample` with the file's body as the issue body. T05 goes through its lifecycle; component agent fixes the rate-limit middleware. T05's PR merges; `task_completed` with `correlation_id = FEAT-2026-0061/T05` at new commit `0123456789abcdef0123456789abcdef01234567` appended to the feature event log. A new `qa_execution` task `FEAT-2026-0061/T06` is opened (regression re-run), reaches ready, and qa-execution runs the plan at the new commit.

### Invocation B — resolution

Triggering event:

```json
{
  "timestamp": "2026-04-23T20:14:00Z",
  "correlation_id": "FEAT-2026-0061",
  "event_type": "qa_execution_completed",
  "source": "qa",
  "source_version": "1.2.0",
  "payload": {
    "task_correlation_id": "FEAT-2026-0061/T06",
    "commit_sha": "0123456789abcdef0123456789abcdef01234567",
    "plan_path": "/product/test-plans/FEAT-2026-0061.md",
    "test_count": 3,
    "total_duration_seconds": 4.3
  }
}
```

**Step 1–2** — same procedure; log re-read fresh.

**Step 3** — Q4 resolution for T06: its `depends_on` must include impl tasks (the regression-fix impl task T05, possibly T02 as well). Assuming `depends_on = [T05]` (the regression-fix task), filtered to implementation = `[T05]`. `implementation_task_correlation_id = FEAT-2026-0061/T05`.

**Step 4C** — for each plan test_id:

- `widgets-export-happy-path-200ok`: 4C.1 → no open `qa_regression_filed` for `(T05, widgets-export-happy-path-200ok)`. Skip. (Note: the open filed event from Invocation A is keyed on `T02`, not `T05` — Q4 attribution on the resolving run picks up the NEW impl task, so resolution does not cross-match. **This is a v1 limitation worth naming: a regression filed against T02 cannot be auto-resolved by a qa_execution whose Q4 resolution yields T05, even though T05 was spawned to fix the T02 regression.** See §"Deferred — cross-attribution resolution" below.)

The v1 skill handles this by a **fallback resolution scan**: after the per-test_id loop, the skill walks all open `qa_regression_filed` events on the feature (any impl_task_correlation_id), and for each one whose `test_id` appears in the current plan, it checks the triggering event's outcome for that test_id. If the test_id is NOT in `failed_tests[]` (since this is a `qa_execution_completed`, no test_id is in `failed_tests[]` — an all-pass run passes every test), AND the resolving commit SHA differs from the failing commit SHA AND post-dates it, the fallback emits `qa_regression_resolved` keyed on the ORIGINAL filed event's `implementation_task_correlation_id`.

Applied here: the fallback scan finds the open `qa_regression_filed` for `(FEAT-2026-0061/T02, widgets-export-rate-limit-enforced-429)`. The resolving commit `0123456789…` differs from the failing `def56789…` and post-dates it. Emit:

```json
{
  "timestamp": "2026-04-23T20:15:00Z",
  "correlation_id": "FEAT-2026-0061",
  "event_type": "qa_regression_resolved",
  "source": "qa",
  "source_version": "1.3.0",
  "payload": {
    "implementation_task_correlation_id": "FEAT-2026-0061/T02",
    "test_id": "widgets-export-rate-limit-enforced-429",
    "filed_event_ts": "2026-04-23T18:44:00Z",
    "resolving_qa_execution_event_ts": "2026-04-23T20:14:00Z",
    "resolving_commit_sha": "0123456789abcdef0123456789abcdef01234567"
  }
}
```

See [`/shared/schemas/examples/qa_regression_resolved.json`](../../../../shared/schemas/examples/qa_regression_resolved.json).

**Step 4C.4** — no prior `human_escalation` with `reason: spinning_detected` on `FEAT-2026-0061/T02` between the filed event (2026-04-23T18:44:00Z) and the resolving event (2026-04-23T20:14:00Z). No `escalation_resolved` emitted on this loop.

Invocation B returns. The open regression is now closed on the event log; a future qa-curation pass (WU 3.5) will read the `qa_regression_resolved` and permit the test to be touched during curation if needed.

## Worked example 2 — Repeat failure path

Variant branch from Example 1. After Invocation A, T05 is spawned and the component agent attempts a fix. T05 merges; `task_completed` for T05 appended at `2026-04-23T19:30:00Z`. However, the fix did not actually close the regression — the new qa_execution `T06` runs the plan and the same test fails again.

### Invocation B' — repeat failure

Triggering event:

```json
{
  "timestamp": "2026-04-23T19:45:00Z",
  "correlation_id": "FEAT-2026-0061",
  "event_type": "qa_execution_failed",
  "source": "qa",
  "source_version": "1.2.0",
  "payload": {
    "task_correlation_id": "FEAT-2026-0061/T06",
    "commit_sha": "abcdef0123456789abcdef0123456789abcdef01",
    "plan_path": "/product/test-plans/FEAT-2026-0061.md",
    "test_count": 3,
    "failed_tests": [
      {"test_id": "widgets-export-rate-limit-enforced-429", "first_signal": "HTTP 200 returned on 101st request; expected 429 Too Many Requests.", "exit_code": 0}
    ]
  }
}
```

**Step 1–2** — same.

**Step 3** — Q4 resolution: T06's impl-filtered depends_on determines attribution. At v1, to preserve the repeat-failure detection against the ORIGINAL filed pair (T02), the skill attributes this triggering event to `FEAT-2026-0061/T02` by the same fallback scan pattern: if the current Q4 resolution yields a task distinct from the open filed pair's impl task, the skill falls back to the open filed pair's impl task for the repeat-failure check. This is the v1 compromise — see §"Deferred — cross-attribution resolution". Applied here: attributing to `T02` for the repeat-failure match.

**Step 4A.1** — prior `qa_regression_filed` at 2026-04-23T18:44:00Z exists for `(T02, widgets-export-rate-limit-enforced-429)`. Jump to Step 4B.

**Step 4B.1** — linked fix attempt scan: walk event log for `task_completed` with ts > 2026-04-23T18:44:00Z, task-level correlation_id on this feature, NOT equal to `FEAT-2026-0061/T02`. The `task_completed` on `FEAT-2026-0061/T05` at 2026-04-23T19:30:00Z matches. Fix attempt detected. Proceed to 4B.2.

**Step 4B.2** — idempotence guard: no prior `human_escalation` on `FEAT-2026-0061/T02` with `reason: spinning_detected` newer than the filed event. Proceed.

**Step 4B.3** — write `/inbox/human-escalation/FEAT-2026-0061-T02-qa-regression-spinning.md`:

```markdown
## Correlation ID

FEAT-2026-0061/T02

## Reason

spinning_detected

## Agent state

- Role: qa (qa-regression skill)
- What I was doing: processing a qa_execution_failed event for FEAT-2026-0061 at commit abcdef0123…
- Prior regression filed: test_id `widgets-export-rate-limit-enforced-429` against impl task `FEAT-2026-0061/T02`, filed 2026-04-23T18:44:00Z (`inbox/qa-regression/FEAT-2026-0061-widgets-export-rate-limit-enforced-429.md`).
- Linked fix attempt: task `FEAT-2026-0061/T05` completed 2026-04-23T19:30:00Z.
- Re-execution failed: the same test_id failed again at commit abcdef0123… with the same first_signal.
- Per architecture §6.4: repeat failure after a linked fix attempt is a `spinning_detected` condition on the ORIGINAL implementation task; the QA agent does NOT flip `FEAT-2026-0061/T02`'s state — see `agents/qa/CLAUDE.md` §"Cross-task regression semantics".

## Decision requested

The rate-limit regression on `FEAT-2026-0061/T02` (widgets export, `widgets-export-rate-limit-enforced-429`) persists after one fix attempt on spawned task `FEAT-2026-0061/T05`. Pick one:

1. **Re-plan the implementation task** — PM opens a fresh impl task with a tighter prompt; current regression artifact remains the reproduction.
2. **Abandon the failing test** — curation PR retires `widgets-export-rate-limit-enforced-429` with rationale.
3. **Re-open the spec** — file a spec issue on the underlying behavior; feature may transition to `blocked_spec` pending resolution.
```

**Step 4B.4** — emit `human_escalation`:

```json
{
  "timestamp": "2026-04-23T19:46:00Z",
  "correlation_id": "FEAT-2026-0061/T02",
  "event_type": "human_escalation",
  "source": "qa",
  "source_version": "1.3.0",
  "payload": {
    "reason": "spinning_detected",
    "inbox_file": "inbox/human-escalation/FEAT-2026-0061-T02-qa-regression-spinning.md",
    "summary": "test_id widgets-export-rate-limit-enforced-429 re-failed at commit abcdef0123 after a linked fix attempt on FEAT-2026-0061/T05; spinning_detected on original implementation task FEAT-2026-0061/T02."
  }
}
```

Validates, appended. NO second `qa_regression_filed` (anti-pattern #6 in [`../../CLAUDE.md`](../../CLAUDE.md) would be violated otherwise).

**Step 4B.5** — stop. No label write on `FEAT-2026-0061/T02`. The Q4 invariant holds.

### Invocation B' continued — eventual resolution

The human reviews, picks option 1, re-plans. A new impl task `FEAT-2026-0061/T07` is minted and completes with a correct fix. A new `qa_execution` task `FEAT-2026-0061/T08` runs the plan against the new commit `fedcba9876543210fedcba9876543210fedcba98` and produces `qa_execution_completed` at 2026-04-23T22:00:00Z.

qa-regression invoked (resolution path):

**Step 4C** — fallback scan finds the open `qa_regression_filed` for `(T02, widgets-export-rate-limit-enforced-429)`. Resolving commit differs and post-dates. Emit `qa_regression_resolved` (same shape as Invocation B in Example 1, with updated `resolving_commit_sha` and `resolving_qa_execution_event_ts`).

**Step 4C.4** — human_escalation scan finds the 2026-04-23T19:46:00Z escalation on `FEAT-2026-0061/T02` with reason `spinning_detected`, no matching `escalation_resolved` yet. Emit:

```json
{
  "timestamp": "2026-04-23T22:01:00Z",
  "correlation_id": "FEAT-2026-0061/T02",
  "event_type": "escalation_resolved",
  "source": "qa",
  "source_version": "1.3.0",
  "payload": {
    "resolution_kind": "qa_regression_resolved",
    "resolved_escalation_event_ts": "2026-04-23T19:46:00Z",
    "resolved_escalation_inbox_file": "inbox/human-escalation/FEAT-2026-0061-T02-qa-regression-spinning.md",
    "summary": "qa-execution at commit fedcba9876 passes test_id widgets-export-rate-limit-enforced-429; prior spinning_detected escalation on FEAT-2026-0061/T02 retired."
  }
}
```

Envelope `correlation_id` is task-level — it matches the retired `human_escalation`. Validates, appended.

Cycle closed. Throughout: no QA write to any label or state on `FEAT-2026-0061/T02`, `FEAT-2026-0061/T05`, or `FEAT-2026-0061/T07`. Q4 invariant holds.

## F2.10 absorption — retiring the Phase 2 orphan

**The first application of `escalation_resolved` in this WU's commit** retires the orphan inbox file from the Phase 2 walkthrough: `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md`. Per [`docs/walkthroughs/phase-2/retrospective.md`](../../../../docs/walkthroughs/phase-2/retrospective.md) §"Finding F2.10" and §"Loose ends", the cycle was resolved out of band (Edit C-fix) but the inbox file was left in place as a deliberate demonstration of the missing resolution signal. This WU's commit:

1. Deletes `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md`.
2. Appends one `escalation_resolved` line to `events/FEAT-2026-0005.jsonl` with `source: human`, `source_version: n/a`, `resolution_kind: human_resolved`, `resolved_escalation_event_ts: 2026-04-22T21:01:11Z` (the original `human_escalation` line), `resolved_escalation_inbox_file: inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md`, and a summary naming Edit C-fix as the out-of-band resolution.

The orphan retirement is done in the same commit as this skill's authoring per WU 3.4 AC #3. The `escalation_resolved` substrate is therefore exercised from day one; the F2.10 carry-item closes.

## Deferred — cross-attribution resolution

A v1 limitation worth naming explicitly (Phase 4 home):

**Problem.** When a regression is filed against impl task T-A and the PM inbox consumer spawns a new impl task T-B to fix it, a later qa_execution whose Q4 resolution yields T-B (because the regression-fix qa_execution task's `depends_on` includes T-B, not T-A) would not naturally resolve the open filed event (which is keyed on T-A).

**v1 workaround.** The resolution-path fallback scan (Step 4C after the per-test_id loop) walks ALL open filed events on the feature regardless of Q4 attribution, and resolves any whose `test_id` matches the current plan AND whose `failing_commit_sha` differs from AND pre-dates the triggering event's `commit_sha`. The repeat-failure path applies the same fallback in reverse: if the Q4 resolution yields an impl task distinct from an open filed pair's impl task on the same feature+test_id, the skill attributes the repeat-failure check to the filed pair's impl task.

**Phase 4 fix.** Add a `spawned_from_regression_inbox_file` field to the task graph's implementation task entries (minted by the PM inbox consumer when it spawns the regression-fix task). The qa-regression skill can then resolve a triggering event's Q4 attribution AND follow the `spawned_from_regression_inbox_file` pointer back to the original filed event's impl task, making cross-attribution resolution deterministic and removing the fallback scan. The v1 fallback is correct under the assumption that no two open filed events on the same feature share a `test_id`, which the idempotence key enforces; it is imprecise only when a feature has multiple implementation tasks whose regressions happen to alias onto the same test_id across different cardinality-override groupings.

## What this skill does not do

- It does **not** run the test plan. That is [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) (WU 3.3).
- It does **not** author test plans. That is [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) (WU 3.2).
- It does **not** curate the regression suite. That is [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) (WU 3.5).
- It does **not** spawn the regression-fix implementation task's GitHub issue. It writes the inbox file; the PM inbox consumer (or the human) reads the file, mints the new task correlation ID, opens the issue.
- It does **not** mint any task-level correlation ID. Minting is exclusively the PM agent's function per [`../../CLAUDE.md`](../../CLAUDE.md) §"Role definition".
- It does **not** flip labels or state on the implementation task under test, on the spawned regression-fix task, on the qa_execution task that triggered the invocation, or on any other task. The qa_execution task's own transitions are owned by qa-execution; this skill is downstream of those transitions.
- It does **not** modify existing inbox files — it only writes new ones under `/inbox/qa-regression/` and `/inbox/human-escalation/`, and on the F2.10 application it deletes the specific orphan `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md` in this WU's commit (once; the skill at runtime does not delete `human_escalation` inbox files — archival is the polling loop's concern per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"Expected human response loop").
- It does **not** modify the feature registry's `task_graph`, its `state`, its `involved_repos`, or any other frontmatter field.
- It does **not** emit `task_created`, `task_ready`, `task_started`, `task_completed`, `task_blocked`, `feature_state_changed`, or any event not listed in the §"Outputs" section above. Those belong to other roles (PM, merge watcher, component).
- It does **not** re-emit an event when the idempotence scan finds a match. A duplicate would fragment the regression signal and corrupt downstream curation.
- It does **not** swallow Q4 ambiguity. More-than-one or zero implementation tasks in the qa_execution's `depends_on` → `spec_level_blocker`.
- It does **not** cache the event log, the feature registry, the plan file, or any prior invocation's state. Every pickup re-reads fresh.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §6.3 (transition ownership — the Q4 invariant's architectural basis), §6.4 (spinning detection — the repeat-failure path's authority), §7.3 (event log semantics), §7.4 (inbox extensibility — authorizes the new `/inbox/qa-regression/` subdirectory).
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 3.4" — the work unit that authored this skill.
- [`/docs/walkthroughs/phase-2/retrospective.md`](../../../../docs/walkthroughs/phase-2/retrospective.md) §"Finding F2.10" + §"Loose ends" — the origin of the `escalation_resolved` substrate and the orphan retirement.
- [`../../CLAUDE.md`](../../CLAUDE.md) — the QA role config; §"Cross-task regression semantics" fixes the Q4 invariant this skill implements, §"Role-specific verification" names the grep-able clause this skill's §"Verification" reproduces, §"Anti-patterns" #1 / #6 / #12 / #13 are the hard stops enforced here.
- [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) — upstream skill (WU 3.2) that authored the test plan this skill reads on the first-failure path.
- [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) — upstream skill (WU 3.3) whose `qa_execution_failed` / `qa_execution_completed` events trigger this skill.
- [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) — downstream skill (WU 3.5) that reads this skill's `qa_regression_filed` / `qa_regression_resolved` pairs for open-regression protection.
- [`../../../pm/skills/dependency-recomputation/SKILL.md`](../../../pm/skills/dependency-recomputation/SKILL.md) — pattern reference for the "skill is a function, trigger is external, live-reads over cached state" posture.
- [`/shared/schemas/test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — plan contract this skill reads on the first-failure path.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — envelope; `qa_regression_filed`, `qa_regression_resolved`, and `escalation_resolved` added to the enum in this WU.
- [`/shared/schemas/events/qa_regression_filed.schema.json`](../../../../shared/schemas/events/qa_regression_filed.schema.json) — first-failure event payload contract.
- [`/shared/schemas/events/qa_regression_resolved.schema.json`](../../../../shared/schemas/events/qa_regression_resolved.schema.json) — resolution-path event payload contract.
- [`/shared/schemas/events/escalation_resolved.schema.json`](../../../../shared/schemas/events/escalation_resolved.schema.json) — F2.10 substrate event payload contract.
- [`/shared/schemas/events/qa_execution_failed.schema.json`](../../../../shared/schemas/events/qa_execution_failed.schema.json) — upstream trigger payload contract.
- [`/shared/schemas/events/qa_execution_completed.schema.json`](../../../../shared/schemas/events/qa_execution_completed.schema.json) — upstream trigger payload contract on the resolution path.
- [`/shared/schemas/events/human_escalation.schema.json`](../../../../shared/schemas/events/human_escalation.schema.json) — shape of the escalation emitted on the repeat-failure path.
- [`/shared/schemas/examples/qa_regression_filed.json`](../../../../shared/schemas/examples/qa_regression_filed.json) — worked-example fixture.
- [`/shared/schemas/examples/qa_regression_resolved.json`](../../../../shared/schemas/examples/qa_regression_resolved.json) — worked-example fixture.
- [`/shared/schemas/examples/escalation_resolved.json`](../../../../shared/schemas/examples/escalation_resolved.json) — worked-example fixture (the F2.10 `human_resolved` variant).
- [`/shared/templates/qa-regression-issue.md`](../../../../shared/templates/qa-regression-issue.md) — v0.2 template the inbox artifact is composed from.
- [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md) — template the repeat-failure escalation file is composed from.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation protocol the repeat-failure path routes through (additively — no regression to Phase 2's contract).
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 — universal discipline; per-type payload validation applies to all three new events automatically.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally per invocation.
- [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — the patterns this skill emits.
- [`/shared/rules/security-boundaries.md`](../../../../shared/rules/security-boundaries.md) §"Log hygiene" — redaction discipline for inbox artifact body and payload fields.
- [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md) — re-confirmed: no written path in this skill is in the never-touch list.
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — applies the per-type payload schemas.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
