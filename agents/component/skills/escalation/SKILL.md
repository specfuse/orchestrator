# Component agent — escalation skill (v1)

## Purpose

This skill is how the component agent operationalizes [`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) for its role. It defines the four escalation reasons that can apply to the component agent, the exact trigger for each one, the artifacts to produce, the state transitions and events that accompany the escalation, and — most importantly — what the agent does **after** escalating (answer: stop, do not continue).

The shared escalation protocol is normative. This skill narrows it to the component role and specifies the internal mechanics — notably the spinning counter — that the shared rule deliberately does not prescribe.

## The four escalation reasons

The component agent escalates for exactly one of:

1. **`spinning_detected`** — three consecutive failed verification cycles, wall-clock exceeded, or token budget exceeded.
2. **`spec_level_blocker`** — a spec contradiction, omission, or ambiguity that cannot be resolved inside the current task; **or** the task's verification appears to require writing to a [`never-touch.md`](../../../../shared/rules/never-touch.md) path without the correct protocol.
3. **`override_expiry_needs_review`** — reconciliation of an active override has failed, or a tracking issue's resolution is ambiguous.
4. **`autonomy_requires_approval`** — the task is `supervised` and the agent has reached the "propose plan, await human go" gate.

These four values are the only acceptable content of the `reason` field in [`human-escalation.md`](../../../../shared/templates/human-escalation.md) for this role. Other reason values exist in the protocol but are not emitted by the component agent. Ad-hoc reasons are not routed.

If the situation does not fit any of the four, follow the guidance in [`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"When to escalate": pick the closest-fitting reason, describe the situation precisely in the escalation body, and let the human triage. Do not invent a new `reason` value.

## Triggers and flows

For each reason, the skill describes: the precise trigger, the artifacts produced, the state transition, the events emitted, and the stop condition. All four flows share the stop condition — once the escalation is written and the state is transitioned, the agent does not continue.

### 1. `spinning_detected`

**Trigger.** Any of:

- The **internal spinning counter** (see §"Spinning counter" below) has reached `3`.
- The wall-clock duration of the task has exceeded the runtime-configured wall-clock threshold. *(Threshold source: environment — see §"Runtime-configured thresholds".)*
- The cumulative token budget of the task has exceeded the runtime-configured token threshold. *(Threshold source: environment.)*

**Artifacts.** A `human-escalation.md` file at `/inbox/human-escalation/<task-correlation-id>-spinning.md` in the orchestration repo, filled per [`human-escalation.md`](../../../../shared/templates/human-escalation.md). The "Agent state" section names the failing gate(s), the last-seen evidence, the number of cycles consumed, and the wall-clock / token usage if those are what tripped. The "Decision requested" section offers the human a closed choice: retry with guidance, reassign, split, or abandon.

**State transition.** `in_progress → blocked_human`. Label rotation: `state:in-progress` → `state:blocked-human`.

**Events.** Append to `/events/FEAT-YYYY-NNNN.jsonl`:

- `task_blocked` — payload names the blocker category (`spinning`), the cycle count at escalation, and the inbox filename.
- `human_escalation` — payload carries the reason (`spinning_detected`), the inbox filename, and a one-sentence `summary`.

Both events go on the same commit as the inbox file write. The transition happens first, then the commit lands.

**Stop.** The agent does not attempt a fourth cycle. It does not preemptively mark the task for abandonment. It does not write a second inbox file if a response is slow. It waits for the human's `blocked_human → ready` transition (or `* → abandoned`) and resumes from the resumable state named in the inbox file.

### 2. `spec_level_blocker`

**Trigger.** One of:

- A spec contradiction, omission, or ambiguity the agent cannot resolve inside the current task: the generated code behaves in a way the spec does not describe, two specs disagree, the spec's acceptance criteria cannot be mechanically tested, or a generated surface the task depends on does not exist.
- The task's verification appears to require writing to a path in [`never-touch.md`](../../../../shared/rules/never-touch.md) without the correct protocol (generated file edit without override, branch-protection change, secret access, `/business/` reference, `.git/` internals).
- A cross-repo change surfaces: the task as written implies modifying a second repo beyond the one this agent instance is assigned to.

**Artifacts.**

1. If the trigger is a spec or generator problem, file a `spec-issue.md` against the product specs repo or the Specfuse generator project (template at [`spec-issue.md`](../../../../shared/templates/spec-issue.md)). The filing agent does not propose a fix beyond what the template's "Suggested resolution" section asks for.
2. Whether or not a spec issue was filed, write a `human-escalation.md` at `/inbox/human-escalation/<task-correlation-id>-spec.md`. The "Agent state" section links the spec issue (or explains why none was filed — e.g., cross-repo scope), names what the agent tried, and points at the offending path or spec reference. The "Decision requested" section asks the human: (a) is the escalation correctly routed; (b) should the task be split or reshaped; (c) should it be abandoned while the spec-level fix lands.

**State transition.** `in_progress → blocked_spec`. Label: `state:in-progress` → `state:blocked-spec`.

**Events.**

- `spec_issue_raised` — when a spec issue was filed. Payload carries the spec-issue URL and the `triggering_task` correlation ID.
- `task_blocked` — payload names the blocker category (`spec`) and the inbox filename.
- `human_escalation` — payload carries reason `spec_level_blocker`, inbox filename, `summary`.

**Stop.** The agent does not work around the blocker (no local stub, no "I will come back to this"). It stops until the human either authorizes an override, resolves the spec-level fix, or abandons the task.

### 3. `override_expiry_needs_review`

**Trigger.** During reconciliation after a regeneration event (per [`override-registry.md`](../../../../shared/rules/override-registry.md) §"Reconciliation"), one of:

- Reapplying an active override to the regenerated file fails — the regenerated structure has shifted and the saved change no longer cleanly applies.
- The override's tracking issue is ambiguous — open, but with comments suggesting resolution; or closed, but the regenerated behavior does not yet match the expected outcome.

**Artifacts.**

1. Leave the override record `status: active` and untouched.
2. File a `spec-issue.md` describing the structural change in the regenerated output that broke reapplication (when applicable; ambiguity of the tracking issue may not warrant a new spec issue).
3. Write a `human-escalation.md` at `/inbox/human-escalation/<task-correlation-id>-override-review.md`. The "Agent state" section names the override record path, the tracking issue, the nature of the failure (reapplication vs. ambiguity), and links any newly-filed spec issue. The "Decision requested" section offers: (a) re-authorize a revised override; (b) wait on the upstream fix; (c) retire the override and abandon the dependent task.

**State transition.** The task that triggered reconciliation transitions `in_progress → blocked_spec`. If reconciliation was triggered outside of a task (e.g., a dedicated reconciliation pass), the feature transitions to `blocked` instead — see [`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"State machine effects of raising an escalation".

**Events.**

- `task_blocked` or feature-level equivalent, payload names the override record path and category (`override_reconciliation`).
- `human_escalation` — payload carries reason `override_expiry_needs_review`, inbox filename, `summary`.

**Stop.** The agent does not invent a substitute override. It does not speculatively rewrite the override record.

### 4. `autonomy_requires_approval`

**Trigger.** The task's `autonomy` field (from the work-unit-issue frontmatter) is `supervised`, and the agent has just reached the "propose plan, await human go" gate — which is **before any code is written**, after the task has been picked up and read.

**Artifacts.**

1. A comment on the task's GitHub issue containing the agent's plan: a short paragraph of intent and a numbered list of steps the agent would take. The plan is specific enough that the human's "go" is a real approval, not a rubber stamp. Keep the plan honest — include anything the agent is uncertain about.
2. A `human-escalation.md` at `/inbox/human-escalation/<task-correlation-id>-supervised.md`. The "Agent state" section links the plan comment. The "Decision requested" section is: "Approve the plan as-is; approve with modifications (specify); or abandon."

**State transition.** `in_progress → blocked_human`. Label: `state:in-progress` → `state:blocked-human`.

**Events.**

- `task_blocked` — payload names category (`autonomy_gate`), inbox filename.
- `human_escalation` — payload carries reason `autonomy_requires_approval`, inbox filename, `summary`.

**Stop.** The agent writes no code on this branch beyond whatever scaffolding the pickup may have produced (none, in the normal case). It does not proceed on the strength of a self-assessment that "the plan is obviously fine."

## Spinning counter

The agent tracks a single integer `consecutive_failed_cycles` for the current task. State storage is in-memory for the run of the agent session; if the session is interrupted and resumed, the counter resets to `0` because the continuation is a fresh observation of the task state, not a continuation of the failure streak.

**Rules:**

- Initialize to `0` when the task is picked up.
- A **failed verification cycle** — any gate in the mandatory set or any per-task verification command failing at the end of a cycle per [`../verification/SKILL.md`](../verification/SKILL.md) — increments the counter by `1`.
- A **passed verification cycle** — the full gate set plus per-task commands all green in a single cycle — resets the counter to `0`. The reset must happen even if earlier cycles on the same task had failures; the goal is to detect *consecutive* failures, not total failures.
- When the counter reaches `3`, trigger `spinning_detected` per §1 above. Do not attempt a fourth cycle.

An **invalid run** (a gate whose declared behavior was not met — e.g., coverage command exited `0` but the report file is missing) counts as a failed cycle. Repeated invalid runs are themselves spinning.

A cycle is **one pass through the gate set**; partial re-runs do not constitute a cycle. If the agent corrects a failing gate and re-runs only that gate, the counter does not update until the full gate set has been re-run.

## Runtime-configured thresholds

Two spinning inputs are runtime-configured and not hard-coded in this skill:

- `wall_clock_threshold` — maximum wall-clock duration the agent may spend on a single task before `spinning_detected` fires regardless of cycle count.
- `token_budget_threshold` — maximum cumulative token spend on a single task before the same.

Both values are read from the agent's runtime environment (the polling-loop configuration in the initial model). The exact variable names and default values are **TBD** per architecture §11; this skill treats them as externally supplied. When either threshold is absent from the environment, the skill still applies the cycle-count rule unchanged — the two threshold mechanisms are complementary, not dependent.

If the agent cannot read its environment (rare, indicates a platform problem), escalate with `spec_level_blocker` and include the environment failure in the "Agent state" section.

## Event emission: what goes where

Every escalation touches three surfaces: the inbox file (live work queue), the issue state (filter surface for other agents), and the event log (historical trail). They are redundant by design per [`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"Event-log accompaniment". The skill's discipline is to keep all three consistent on the same commit:

1. Rotate the issue label to the new `state:*` value.
2. Write the inbox file and any companion artifact (spec issue comment, plan comment).
3. Append the accompanying events to the feature event log.
4. Commit with a message that mentions the task correlation ID in the body (headline is a simple `chore(escalation): raise <reason> for FEAT-YYYY-NNNN/TNN`).

If step 1 or 3 fails, the escalation is in an inconsistent state. The agent stops and — if possible — writes a follow-up `human-escalation.md` with reason `spec_level_blocker` referencing the failed step. It does not invent a recovery.

## After escalating

Escalation is terminal for the agent's turn on this task:

- **Do not continue the task.** Not even for "the easy parts."
- **Do not re-raise** by writing a second inbox file if the response is slow. Duplicates make the queue harder to read ([`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) §"Expected human response loop").
- **Do not withdraw** by deleting the inbox file. Once raised, the escalation is the human's to close.
- **Do not unblock your own escalation.** The `blocked_* → ready` transition is the human's write.

The next action on this task is entirely the human's. When the human writes the unblock transition, the agent may pick the task up again and resume from the resumable state named in the "Agent state" section of the original escalation.

## Worked example — `spinning_detected`

Task `FEAT-2026-0007/T04`. The agent's first cycle fails on `tests` (a new test regression). It corrects, cycle 2 fails on `coverage` (the correction dropped a path below 0.90). It corrects, cycle 3 fails on `lint` (a style violation the correction introduced). The counter is now `3`.

The agent:

1. Stops before attempting cycle 4.
2. Rotates the task issue label from `state:in-progress` to `state:blocked-human`.
3. Writes `/inbox/human-escalation/FEAT-2026-0007-T04-spinning.md`:
   - Correlation ID: `FEAT-2026-0007/T04`.
   - Reason: `spinning_detected`.
   - Agent state: "component:api, attempted to add email validation. Cycle 1 failed on tests (OrdersControllerTests.Reject_missing_email). Cycle 2 failed on coverage (line coverage 0.88 vs threshold 0.90, missing tests for error branch). Cycle 3 failed on lint (unused variable after refactor). The failure mode appears to be my changes introducing new failures while fixing old ones."
   - Decision requested: "Should I: (a) retry with the enumerated tests-to-add as guidance; (b) be reassigned to a narrower task scope; (c) abandon this task in favor of a replan?"
4. Appends `task_blocked` (category `spinning`, cycle count `3`) and `human_escalation` (reason `spinning_detected`) to `/events/FEAT-2026-0007.jsonl`.
5. Commits: `chore(escalation): raise spinning_detected for FEAT-2026-0007/T04`.
6. Stops.

## Worked example — `spec_level_blocker` with generated-code issue

Task `FEAT-2026-0042/T09` asks the agent to extend a request handler in `clabonte/api-sample`. The handler lives partly in `/_generated/Controllers/OrdersController.cs` (generated from the OpenAPI spec) and partly in a hand-written sidecar. The agent's acceptance criteria require modifying both. The generated controller currently throws on a valid input because the OpenAPI spec's enum is missing a legitimate value.

The agent:

1. Recognizes that editing `/_generated/Controllers/OrdersController.cs` is a [`never-touch.md`](../../../../shared/rules/never-touch.md) violation without an authorized override.
2. Files a spec issue against the product specs repo — [`spec-issue.md`](../../../../shared/templates/spec-issue.md) — describing the missing enum value, its location (`product/openapi.yaml:142`), the triggering task (`FEAT-2026-0042/T09`), and a suggested resolution (add the value).
3. Rotates the task issue label to `state:blocked-spec`.
4. Writes `/inbox/human-escalation/FEAT-2026-0042-T09-spec.md`:
   - Correlation ID: `FEAT-2026-0042/T09`.
   - Reason: `spec_level_blocker`.
   - Agent state: "component:api, picked up T09. Implementation path touches `_generated/Controllers/OrdersController.cs`, which is generated from `product/openapi.yaml`. The OpenAPI enum at line 142 is missing a legitimate value; the generated controller rejects valid inputs as a result. Filed <link to spec issue>. I am not applying an override because the spec-level fix is the clean path; an override would hide a real spec gap."
   - Decision requested: "Please triage the spec issue and either: (a) approve the spec fix (normal path); (b) authorize an override if the spec fix is not going to land this cycle; (c) abandon T09 and replan."
5. Appends `spec_issue_raised` (with the spec-issue URL) and `task_blocked` (category `spec`) and `human_escalation` (reason `spec_level_blocker`) to `/events/FEAT-2026-0042.jsonl`.
6. Commits: `chore(escalation): raise spec_level_blocker for FEAT-2026-0042/T09`.
7. Stops.

## What this skill does not cover

- How overrides are applied and reconciled in the normal (non-failing) case — that is [`override-registry.md`](../../../../shared/rules/override-registry.md). This skill handles only the reconciliation-failure path (§3 above).
- How PRs are opened — that is [`../pr-submission/SKILL.md`](../pr-submission/SKILL.md).
- How the verification gates run — that is [`../verification/SKILL.md`](../verification/SKILL.md).

## Version

- `1.0` — Phase 1 initial.
