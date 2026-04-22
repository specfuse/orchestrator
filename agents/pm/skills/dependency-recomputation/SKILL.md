# PM agent — dependency recomputation skill (v1.0)

## Purpose

This skill is the PM agent's only authorized writer of the `pending → ready` transition on a task, for every case except the no-dep-at-creation flip that [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) (WU 2.4) owns. It runs once per `task_completed` event on a feature, walks every `pending` task in the feature's task graph, reads the live GitHub labels of each task's `depends_on` targets, and flips to `state:ready` exactly those tasks whose dependencies are all `state:done`.

The skill's correctness bar is **idempotence under replay**. A `task_completed` event re-delivered to the skill — whether by a polling loop re-running against an unadvanced cursor, a file-watcher double-firing, or a manual re-invocation — must produce no duplicate `task_ready` events and no duplicate label flips. The live-read of every target's current state, performed before every flip, is what makes this safe: a task already `state:ready` is skipped silently; a task in any other unexpected state triggers a malformed-graph escalation rather than a clobber.

## Scope

In scope:

- Consuming one `task_completed` event per invocation as the trigger.
- Reading the feature's task graph from `/features/<correlation_id>.md` frontmatter to enumerate tasks and their `depends_on` edges.
- Live-reading the GitHub labels of every task involved in the walk — every `pending` candidate and every candidate's `depends_on` targets.
- Flipping issues from `state:pending` to `state:ready` when every dependency carries `state:done`, and emitting one `task_ready` event per flip with `trigger: "task_completed:<TNN>"`.
- Detecting malformed dependency state (post-hoc cycle, orphan reference, unexpected live-label state) and escalating `spec_level_blocker` at the feature level without performing further flips.

Out of scope (belongs elsewhere):

- The no-dep-at-creation `pending → ready` flip — [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) owns it, with `trigger: "no_dep_creation"`.
- Every other state transition — `ready → in_progress` (component/QA), `in_progress → in_review` (component/QA), `in_review → done` (merge watcher), `plan_review → generating` (human), any `blocked_* → ready` unblock (human). Architecture §6.3; [`/shared/rules/state-vocabulary.md`](../../../../shared/rules/state-vocabulary.md).
- Detection of the triggering `task_completed` event. The polling loop / commit hook / CLI that invokes the skill is external; this skill is a function, not a daemon. See §"Trigger — external invocation" below.
- Emitting `feature_state_changed` or closing the feature on the last task's `done`. That belongs to a future PM flow invoked separately when the task graph is drained.

## Inputs

Per invocation:

1. The **triggering `task_completed` event** (object or file pointer — deployment-dependent). The skill reads its `correlation_id` (task-level `FEAT-YYYY-NNNN/TNN`), uses the feature-level portion to locate the feature registry, and uses the task-level portion as the `trigger` tag in subsequent `task_ready` payloads.
2. `/features/<feature_correlation_id>.md` — the feature registry file, whose frontmatter contains the authoritative `task_graph` (IDs, `depends_on`, `assigned_repo`). The task graph is the skill's structural input; it is never rewritten by this skill.
3. `/events/<feature_correlation_id>.jsonl` — the feature's event log, read once to confirm the triggering event is the most recent `task_completed` for the given task-level correlation ID (see §"Idempotence discipline" below).
4. The GitHub issues on every `assigned_repo` in the feature's `involved_repos` — label and state reads only. No body reads, no issue creation, no comments.
5. [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — the event contract.
6. [`/shared/schemas/events/task_started.schema.json`](../../../../shared/schemas/events/task_started.schema.json) — present in the directory as a reference precedent for per-type payload schemas; this skill does not consume it directly, but `scripts/validate-event.py` applies every per-type schema transparently.
7. [`../../CLAUDE.md`](../../CLAUDE.md) and this skill — re-read per invocation per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

## Outputs

Per invocation:

- Zero or more GitHub label rotations on issues in the feature's component repos: `state:pending` removed, `state:ready` added. One rotation per newly-eligible task.
- Zero or more `task_ready` events appended to `/events/<feature_correlation_id>.jsonl`, one per flip, each validated through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) with exit `0`.
- On malformed dependency state: one escalation file under `/inbox/human-escalation/` per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md), plus one `human_escalation` event on the event log. No further flips are performed in the same invocation after the escalation is raised.

No writes to feature frontmatter (the task graph is authoritative; this skill does not reshape it). No writes to component-repo code paths. No writes to `/product/` or `/overrides/`.

## Trigger — external invocation

The trigger-detection mechanism is deliberately **outside this skill**. Consistent with [`../plan-review/SKILL.md`](../plan-review/SKILL.md) §"The trigger-detection loop is external", the skill exposes a procedure that some invoking actor calls. Candidate invokers (any acceptable, deployment choice):

- A polling loop that tails every `/events/FEAT-*.jsonl` file and runs the skill on each new `task_completed` line detected since the last cursor position.
- A CLI (`scripts/recompute-dependencies.sh FEAT-YYYY-NNNN/TNN`) the human runs manually after acknowledging a merge.
- A GitHub webhook on `pull_request.closed` that emits the `task_completed` and invokes this skill in the same handler.
- A file-watcher (inotify / FSEvents) on the event log during local development.

The skill takes two inputs from the invoker: the feature-level correlation ID and the task-level correlation ID of the task that just completed. It does not poll, does not schedule itself, and does not persist state across invocations — every invocation reads everything fresh. This is the same "skill is a function" posture the plan-review skill established.

## The recomputation procedure

Single pass per invocation, typically short (bounded by the feature's task count).

### Step 1 — State intent

Per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1: "I will recompute dependencies on `<feature_correlation_id>` following completion of `<feature_correlation_id>/<TNN>`."

### Step 2 — Read the triggering event and confirm its shape

Read the triggering `task_completed` event object. Confirm:

- `event_type == "task_completed"`.
- `correlation_id` matches the task-level pattern `FEAT-YYYY-NNNN/TNN`.
- The feature-level prefix of `correlation_id` is the feature ID the invoker supplied.

If any check fails, the invocation is malformed — return an error to the invoker without emitting anything. This is the invoker's bug, not a dependency-graph bug; no escalation, no event.

### Step 3 — Read the feature's task graph

Read `/features/<feature_correlation_id>.md`. Parse the frontmatter. Confirm:

- `correlation_id` in the frontmatter matches the feature-level correlation ID.
- `task_graph` is non-empty.
- The triggering task's TNN exists in the task graph.

Build the in-memory representation: a dict `tasks[TNN] = {type, depends_on, assigned_repo, autonomy}` indexed by task ID.

### Step 4 — Structural re-validation (post-hoc cycle / orphan check)

Before any live-reads or flips, re-validate the task graph's structural integrity:

- **Cycle check.** Topologically sort the `depends_on` edges. If cycle detected, escalate `spec_level_blocker` with reason "post-hoc cycle in task graph of `<feature_correlation_id>`". Cycles should have been caught at plan review (WU 2.3 §Re-ingest validation); a cycle present here means the plan file or frontmatter was edited outside the review flow.
- **Orphan check.** Every `TNN` referenced in any `depends_on` array must match a task `id` in the graph. Orphan → escalate `spec_level_blocker`.

These checks run cheap (local read, no GitHub API) and gate every live operation below. A malformed graph at this stage is a drafting or ingest bug, not a recomputation bug — escalate without further walk.

### Step 5 — Enumerate candidate tasks

Walk the task graph. A candidate is any task whose `depends_on` includes the just-completed TNN **and** has at least one dependency (i.e. `depends_on` non-empty). Tasks whose `depends_on` is empty are not candidates — they were ready-flipped by the issue-drafting skill at creation time (`trigger: "no_dep_creation"`) and this skill never owns their flip.

For each candidate, the skill will perform the live-read sequence in step 6 before deciding whether to flip. The walk order is deterministic (task ID sort order) so that replay reproduces the same sequence.

### Step 6 — Per-candidate live-read and flip decision

For each candidate TNN, in task-ID order:

**6a. Live-read the candidate's own GitHub state.** Use `gh issue list --repo <assigned_repo> --state all --search "[FEAT-YYYY-NNNN/TNN] in:title" --json number,labels,state` (or `gh issue view <N> --json number,labels,state` if the issue number is known). Inspect the issue's current `state:*` label.

Branch on the observed state:

- **`state:pending`** — the expected case. Proceed to 6b.
- **`state:ready`** — the task has already been flipped (previous recompute pass, or replay). **Skip silently.** No flip, no `task_ready` event, no error. Continue to the next candidate.
- **`state:in-progress`, `state:in-review`, `state:done`** — the task advanced past `ready` without this skill having flipped it. Single-writer invariant violated: escalate `spec_level_blocker` with reason "`<assigned_repo>#<N>` carries `<state>` while still in `pending` region of dependency graph". Stop the walk.
- **`state:blocked-spec`, `state:blocked-human`, `state:abandoned`** — the task is blocked or dead. Not a candidate for recomputation; the human will unblock or re-plan. **Skip silently.** No flip, no event. Continue to the next candidate.
- **Issue not found** — `gh` returned zero results. Orphan reference between task graph and GitHub. Escalate `spec_level_blocker`.

**6b. Live-read every `depends_on` target's state.** For each TNN in the candidate's `depends_on`, fetch the target issue's current labels. The task graph tells us which TNN; the feature's `assigned_repo` per-task tells us which repo; `gh issue list --repo <target_repo> --state all --search "[FEAT-YYYY-NNNN/<dep_TNN>] in:title"` returns the target.

For each dependency:

- **`state:done`** — satisfied. Continue to the next dependency.
- **`state:ready`, `state:pending`, `state:in-progress`, `state:in-review`** — not yet done. The candidate cannot flip on this pass. **Break out of the dependency loop** and move to the next candidate; the candidate stays pending. No flip, no event.
- **`state:blocked-spec`, `state:blocked-human`, `state:abandoned`** — the dependency is blocked or dead. The candidate cannot flip on this pass. **Break out** and move to the next candidate. No flip, no event. A blocked dependency is not a malformed-graph condition — it is the human's gate to decide (unblock or abandon). Do not escalate here.
- **Issue not found** — orphan. Escalate `spec_level_blocker`, stop the walk.

**6c. If every dependency is `state:done`, flip.**

Execute:

```sh
gh issue edit <N> --repo <assigned_repo> \
  --remove-label state:pending \
  --add-label state:ready
```

Re-read labels via `gh issue view <N> --repo <assigned_repo> --json labels`:

- Confirm `state:ready` is present.
- Confirm `state:pending` is absent.
- Confirm exactly one `state:*` label overall.

If the re-read does not match the intended post-state, do **not** emit `task_ready`. Retry the edit once; if still mismatched, escalate `spec_level_blocker` with reason "label rotation on `<assigned_repo>#<N>` did not round-trip".

**6d. Emit `task_ready`.**

Construct:

```json
{
  "timestamp": "<ISO-8601 now>",
  "correlation_id": "FEAT-YYYY-NNNN/<candidate_TNN>",
  "event_type": "task_ready",
  "source": "pm",
  "source_version": "<from scripts/read-agent-version.sh pm>",
  "payload": {
    "issue": "<assigned_repo>#<N>",
    "trigger": "task_completed:<triggering_TNN>"
  }
}
```

Pipe through [`scripts/validate-event.py`](../../../../scripts/validate-event.py); require exit `0`. Append to `/events/<feature_correlation_id>.jsonl`. Re-read the appended line to confirm JSON integrity.

Continue to the next candidate.

### Step 7 — Return

When every candidate has been processed (each either flipped, skipped, or escalation-terminated), the invocation is complete. The skill returns to its invoker. No summary event (`recomputation_complete` or similar) is emitted — the `task_ready` events and the absence thereof are the complete record.

## Idempotence discipline

Idempotence under replay is the skill's load-bearing correctness bar. Three mechanisms make a replayed `task_completed` a no-op:

### Live-read before flip

Step 6a reads the candidate's current GitHub label before any write. On replay, the candidate is already `state:ready` from the first pass; 6a's `state:ready` branch skips it silently. This is the primary guard and is sufficient on its own in the normal case.

### Single-writer invariant

Only the dependency-recomputation skill (and the issue-drafting skill, for no-dep tasks at creation) writes `state:pending → state:ready`. No other role is authorized to perform this transition. A candidate whose 6a read returns `state:in-progress`, `state:in-review`, or `state:done` therefore signals a writer violation — the skill escalates rather than continuing, because any "flip" it performs now would be clobbering a state written by someone else.

### Deterministic walk order

Step 5 walks candidates in task-ID sort order, and step 6 processes each deterministically. A replay produces the same sequence of `gh` reads, the same branch decisions, and the same (empty, on replay) set of flips. Non-determinism would break the replay invariant by making the "did this flip already happen?" question depend on the walk order; the sort pins it.

### What idempotence does NOT require

- **Event log deduplication.** The skill does not scan the event log for prior `task_ready` emissions and compare. The live-read on GitHub is authoritative; the event log is descriptive. If somehow a `task_ready` appears in the log without a corresponding label flip on GitHub (bug in the emission path, manual log edit), the live-read catches it.
- **Cross-invocation state.** The skill persists nothing between invocations. Every recomputation reads everything fresh.
- **Transactional flips.** If the skill flips T02 and then fails while flipping T04, T02's flip stands. The next invocation re-walks, sees T02 already `state:ready` (skip), sees T04 still `state:pending` with satisfied deps (flip), and emits only T04's `task_ready`. Partial-progress resumption is a natural consequence of the live-read design; no additional machinery needed.

## Escalation on malformed state

Three conditions trigger `spec_level_blocker` at **feature level** (not task level — the dependency graph is the feature's invariant, and a broken graph puts the whole feature in a re-plan state rather than a single task):

### Post-hoc cycle

Detected in step 4 by topological sort. A cycle indicates a plan-file edit or frontmatter edit after plan approval that was not re-ingested through [`../plan-review/SKILL.md`](../plan-review/SKILL.md) — that skill would have caught the cycle at re-ingest time.

### Orphan reference

A `TNN` in a `depends_on` array that does not match any task `id` in the graph (step 4), or a task in the graph with no corresponding GitHub issue on its `assigned_repo` (step 6a's "issue not found" branch), or a `depends_on` target with no corresponding issue (step 6b). Any of the three is a broken contract between the planned graph and the realized issues.

### Unexpected live-label state on a candidate

Step 6a's `state:in-progress`, `state:in-review`, `state:done` branch. The task advanced past `ready` without the dependency-recomputation skill having flipped it — a single-writer violation. Escalation is correct here even though the underlying cause is likely benign (manual label edit, duplicate PM instance running concurrently), because the skill cannot safely continue without human diagnosis.

### The escalation file

Use [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md). Name: `/inbox/human-escalation/<feature_correlation_id>-dep-recomp.md`. Reason: `spec_level_blocker`. Correlation ID on the event and in the file: feature-level (`FEAT-YYYY-NNNN`), not task-level. The "Agent state" section names the specific malformation (which TNN, which dependency, which observed label). The "Decision requested" section names the human's options concretely (re-plan via `plan_review`, manually correct the labels, abandon the feature).

One `human_escalation` event is appended to the feature's event log, payload `{"reason": "spec_level_blocker", "inbox_file": "...", "summary": "<one sentence>"}`.

### Stopping the walk

Once an escalation is raised, the skill does not continue processing remaining candidates in the same invocation. The graph is malformed; further flips would be acting on an invalid premise. Flips already performed earlier in the same invocation are not rolled back (GitHub label history is the audit), but the `task_ready` events they emitted stand — the downstream consumers acted on valid state at the time of emission.

## Event payload — `task_ready`

Consistent with the shape authored in [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md), but with a different `trigger` value to distinguish provenance:

```json
{
  "issue": "<owner>/<repo>#<number>",
  "trigger": "task_completed:<completing_TNN>"
}
```

- `issue` — `<owner>/<repo>#<number>` short form. Same shape as the `task_created` event's `issue` field for the same task; consumers cross-reference by the shared `correlation_id`.
- `trigger` — the literal string `"task_completed:"` followed by the completing task's TNN (e.g. `"task_completed:T01"`). This distinguishes dependency-recomputation flips from issue-drafting's `"no_dep_creation"` flips. A future skill that introduces another flip path (e.g. a manual human-directed flip) would use its own distinct trigger tag.

The top-level event's `correlation_id` is the **candidate's** task-level ID (the one being flipped), not the triggering task's. The `trigger` payload field carries the triggering TNN. Consumers looking for "which task just became ready" read the top-level `correlation_id`; consumers looking for "what caused this flip" read `payload.trigger`.

A future per-type schema at `/shared/schemas/events/task_ready.schema.json` (not authored in this WU) will pin the `trigger` field's pattern more tightly — e.g. `^(no_dep_creation|task_completed:T\d{2})$`. Until then, the payload shape above is documented here and must remain stable.

## Verification

Universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 apply on every emission, plus the skill-local checks below.

### Before returning from any invocation

- The triggering event's `event_type` was `task_completed` and its `correlation_id` matched the task-level pattern.
- The feature registry's task graph passed cycle and orphan checks in step 4.
- Every flip performed was preceded by a fresh live-read confirming the candidate was `state:pending`.
- Every flip was followed by a fresh live-read confirming `state:ready` present and `state:pending` absent.
- Every `task_ready` event passed `scripts/validate-event.py` with exit `0` and was appended to the feature's event log.
- `source_version` on every event was produced by `scripts/read-agent-version.sh pm` at emission time.
- No state transition was performed on any task not in the candidate set of step 5.
- No write to feature frontmatter, component-repo code paths, `/product/`, or `/overrides/`.
- No path written is in [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md).

### Before returning from an escalation invocation

- The escalation file at `/inbox/human-escalation/<feature_correlation_id>-dep-recomp.md` is written per [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md).
- One `human_escalation` event is appended with feature-level correlation ID.
- No further candidates are processed after the escalation.

### Before returning from a replay invocation (no flips)

- Every candidate's live-read returned `state:ready` (or `state:blocked-*` / `state:abandoned`), causing the skill to skip silently.
- Zero `task_ready` events appended.
- Zero label rotations performed.
- The event log's tail is byte-identical to its pre-invocation state.

Failure handling per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable failures retry once; three consecutive verification failures on the same candidate → `spinning_detected`; fundamentally blocked (malformed graph) → `spec_level_blocker` per §"Escalation on malformed state".

## Worked example 1 — happy-path walk after `FEAT-2026-0050/T01` completes

Reuses the fictional feature from [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) §"Worked example" — `FEAT-2026-0050 — Widget export endpoint`, a 5-task graph across two repos.

### Pre-invocation state

Task graph (excerpt from `/features/FEAT-2026-0050.md` frontmatter):

```yaml
task_graph:
  - id: T01
    type: implementation
    depends_on: []
    assigned_repo: clabonte/persistence-sample
  - id: T02
    type: implementation
    depends_on: [T01]
    assigned_repo: clabonte/api-sample
  - id: T03
    type: qa_authoring
    depends_on: []
    assigned_repo: clabonte/api-sample
  - id: T04
    type: qa_execution
    depends_on: [T01, T02, T03]
    assigned_repo: clabonte/api-sample
    autonomy: review
  - id: T05
    type: qa_curation
    depends_on: [T04]
    assigned_repo: clabonte/api-sample
```

Live GitHub labels on each issue, immediately after T01's PR merged and `task_completed` fired (but before this skill runs):

| Task | Repo / Issue | `state:*` |
|---|---|---|
| T01 | `clabonte/persistence-sample#12` | `state:done` |
| T02 | `clabonte/api-sample#47` | `state:pending` |
| T03 | `clabonte/api-sample#48` | `state:ready` |
| T04 | `clabonte/api-sample#49` | `state:pending` |
| T05 | `clabonte/api-sample#50` | `state:pending` |

T03 was created `state:ready` by the issue-drafting skill (no deps, `trigger: "no_dep_creation"`). T02, T04, T05 were created `state:pending` (had deps). T01 transitioned `pending → ready → in_progress → in_review → done` over its normal lifecycle; the merge watcher emitted `task_completed` when its PR merged.

### The triggering event

```json
{
  "timestamp": "2026-04-22T14:18:03Z",
  "correlation_id": "FEAT-2026-0050/T01",
  "event_type": "task_completed",
  "source": "component:persistence-sample",
  "source_version": "1.5.0",
  "payload": { "...": "..." }
}
```

The polling loop (or equivalent invoker) detects this as a new `task_completed` line and calls `recompute("FEAT-2026-0050", "FEAT-2026-0050/T01")`.

### Step 1 — Intent

"I will recompute dependencies on FEAT-2026-0050 following completion of FEAT-2026-0050/T01."

### Step 2 — Triggering event shape

`event_type == "task_completed"` ✓. `correlation_id == "FEAT-2026-0050/T01"` matches the pattern ✓. Feature prefix matches invoker-supplied ID ✓.

### Step 3 — Read task graph

Frontmatter parses. `correlation_id == "FEAT-2026-0050"` matches. `task_graph` has 5 entries. T01 is in the graph. Proceed.

### Step 4 — Structural re-validation

- Cycle check: topological order is `T01 → T02 → T04 → T05`, T03 parallel. No cycles ✓.
- Orphan check: `depends_on` references are `T01, T01, T02, T03, T04`, all present as task IDs ✓.

### Step 5 — Enumerate candidates

Tasks whose `depends_on` includes T01 and is non-empty: **T02** (`depends_on: [T01]`), **T04** (`depends_on: [T01, T02, T03]`). T03's `depends_on` is empty → not a candidate. T05 does not reference T01 directly → not a candidate on this pass (T05 will become a candidate when T04 completes).

Walk order (task-ID sort): T02, then T04.

### Step 6 — Per-candidate live-reads

**Candidate T02 (`clabonte/api-sample#47`)**

6a. `gh issue view 47 --repo clabonte/api-sample --json number,labels,state` → `state:pending` ✓. Proceed to 6b.

6b. Dependencies: `[T01]`. Live-read T01 on `clabonte/persistence-sample#12`:

```sh
gh issue list --repo clabonte/persistence-sample --state all \
  --search "[FEAT-2026-0050/T01] in:title" --json number,labels,state
# → [{ "number": 12, "labels": [{"name": "state:done"}, ...], "state": "closed" }]
```

T01 is `state:done` ✓. All T02 dependencies satisfied.

6c. Flip:

```sh
gh issue edit 47 --repo clabonte/api-sample \
  --remove-label state:pending --add-label state:ready
# → https://github.com/clabonte/api-sample/issues/47
```

Re-read: `state:ready` present ✓, `state:pending` absent ✓, exactly one `state:*` ✓.

6d. Emit:

```json
{
  "timestamp": "2026-04-22T14:18:05Z",
  "correlation_id": "FEAT-2026-0050/T02",
  "event_type": "task_ready",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "issue": "clabonte/api-sample#47",
    "trigger": "task_completed:T01"
  }
}
```

Validates through `scripts/validate-event.py` (exit 0). Appended to `/events/FEAT-2026-0050.jsonl`. Re-read confirms.

**Candidate T04 (`clabonte/api-sample#49`)**

6a. Live-read `#49` → `state:pending` ✓.

6b. Dependencies: `[T01, T02, T03]`. Live-reads:

- T01 on `clabonte/persistence-sample#12` → `state:done` ✓.
- T02 on `clabonte/api-sample#47` → `state:ready` (just flipped in this same invocation). **Not `state:done`.** **Break.**

T04 stays `state:pending`. No flip, no event. Continue to the next candidate.

(No more candidates after T04.)

### Step 7 — Return

Exactly one flip performed (T02). Exactly one `task_ready` event emitted. Invocation complete.

### Post-invocation state

| Task | `state:*` | Change from pre-invocation |
|---|---|---|
| T01 | `state:done` | unchanged |
| T02 | `state:ready` | `pending → ready` (this invocation) |
| T03 | `state:ready` | unchanged |
| T04 | `state:pending` | unchanged |
| T05 | `state:pending` | unchanged |

A component agent instantiated against `clabonte/api-sample` will now pick T02 up via its `state:ready` label and begin the implementation. When T02 eventually merges, its `task_completed` will re-invoke this skill; T04's dependencies will then be T01=done, T02=done, T03=still-ready-but-not-done, so T04 stays pending until T03 (qa_authoring) also completes. The progression is driven entirely by merge events; no further coordination needed.

## Worked example 2 — idempotent replay of the same `task_completed`

Same feature, same triggering event, but delivered a second time — e.g. the polling loop's cursor regressed, a developer ran `scripts/recompute-dependencies.sh FEAT-2026-0050/T01` manually after the first recompute already ran, or a webhook re-fired.

### Pre-invocation state (identical to post-invocation of Example 1)

| Task | `state:*` |
|---|---|
| T01 | `state:done` |
| T02 | `state:ready` |
| T03 | `state:ready` |
| T04 | `state:pending` |
| T05 | `state:pending` |

### Same triggering event

```json
{
  "timestamp": "2026-04-22T14:18:03Z",
  "correlation_id": "FEAT-2026-0050/T01",
  "event_type": "task_completed",
  "source": "component:persistence-sample",
  "source_version": "1.5.0",
  "payload": { "...": "..." }
}
```

### Walk

Steps 1–5 reproduce Example 1 deterministically (same intent, same frontmatter, same cycle/orphan checks pass, same candidate set `[T02, T04]`, same walk order).

**Candidate T02 (`clabonte/api-sample#47`)**

6a. Live-read → `state:ready`. **Already flipped on the previous invocation.** **Skip silently.** No 6b, no 6c, no 6d. No event. Move on.

**Candidate T04 (`clabonte/api-sample#49`)**

6a. Live-read → `state:pending` ✓.

6b. T01 → `state:done` ✓. T02 → `state:ready` (not `state:done`). **Break.** T04 stays pending.

### Step 7 — Return

Zero flips. Zero `task_ready` events emitted. The event log's tail is byte-identical to its pre-invocation state.

### Post-invocation state (identical to pre-invocation)

| Task | `state:*` | Change |
|---|---|---|
| T01 | `state:done` | unchanged |
| T02 | `state:ready` | unchanged |
| T03 | `state:ready` | unchanged |
| T04 | `state:pending` | unchanged |
| T05 | `state:pending` | unchanged |

### Why replay is safe

The live-read of T02's label in 6a is the single guard that made this safe. No event log deduplication logic was consulted; no "have I already processed this trigger?" flag was checked; no cross-invocation state was persisted. The skill simply did the same walk and discovered, at each step, that GitHub's current state already matched the skill's intended post-state. That is the posture every recomputation pass maintains: flip what needs flipping, skip what is already flipped, escalate what is not in a state the skill can interpret.

## What this skill does not do

- It does **not** own the no-dep `pending → ready` flip at creation. That lives in [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) with `trigger: "no_dep_creation"`.
- It does **not** detect `task_completed` events. The polling loop / hook / CLI that invokes the skill is external.
- It does **not** modify the task graph. The frontmatter is read-only during recomputation.
- It does **not** modify feature state. `in_progress → done` is the merge watcher's (on the last task) followed by a separate PM flow that closes the feature; neither lives in this skill.
- It does **not** reshape dependency edges. Post-hoc edits to the graph during `in_progress` are re-plan events, not recomputation events; this skill detects them as malformation and escalates.
- It does **not** batch flips across multiple features. One invocation = one feature = one triggering `task_completed`.
- It does **not** deduplicate events via the event log. The live-read on GitHub is authoritative; the log is descriptive.
- It does **not** create, close, comment on, or label any issue beyond the flip on `state:*`. Other labels (`type:*`, `autonomy:*`, area labels) are untouched.
- It does **not** emit `feature_state_changed`. Feature-level transitions belong to other PM flows.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §6.2 (task state machine), §6.3 (transition ownership — PM agent owns every `pending → ready` flip via this skill plus issue-drafting's no-dep case), §7.3 (event log semantics).
- [`/shared/rules/state-vocabulary.md`](../../../../shared/rules/state-vocabulary.md) — single-owner invariants this skill defends.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 — universal discipline; extended in WU 2.5 to describe per-type payload validation.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally on every invocation.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation surface used on malformed-state branches.
- [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — the `FEAT-YYYY-NNNN/TNN` pattern the title-prefix searches rely on.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — envelope contract; `task_completed` and `task_ready` already in the enum.
- [`/shared/schemas/events/README.md`](../../../../shared/schemas/events/README.md) — per-type payload schema directory created in WU 2.5 (Finding 5 absorption).
- [`/shared/schemas/events/task_started.schema.json`](../../../../shared/schemas/events/task_started.schema.json) — the first per-type schema precedent, referenced but not consumed by this skill.
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — extended in WU 2.5 to apply per-type schemas when present.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
- [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md) — template for escalation files written on malformed-state branches.
- [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) — upstream skill that drafts the task graph this skill walks; the worked example's FEAT-2026-0050 originates there.
- [`../plan-review/SKILL.md`](../plan-review/SKILL.md) — upstream skill whose re-ingest validation catches cycles/orphans before plan approval; this skill re-checks post-hoc in case the graph was edited outside that flow.
- [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) — sibling skill that owns the no-dep-at-creation flip; this skill owns every other `pending → ready` flip on the feature's lifetime.
- [`../../CLAUDE.md`](../../CLAUDE.md) — PM role config; the "Role-specific verification" clause names this skill as the place the single-writer invariant for `pending → ready` is enforced post-creation.
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 2.5 — Dependency recomputation skill (absorbs Finding 5)" — the work unit that authored this skill.
- [`/docs/walkthroughs/phase-1/retrospective.md`](../../../../docs/walkthroughs/phase-1/retrospective.md) §"Finding 5" — the retrospective that deferred per-type payload schemas to Phase 2 under this WU.
