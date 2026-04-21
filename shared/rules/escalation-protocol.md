# Escalation protocol

When an agent cannot proceed without a human decision, it stops and raises an escalation. Escalation is a one-way, file-based handoff: the agent writes a structured file into the orchestration repo's `/inbox/human-escalation/` directory and waits. The polling loop routes it; the human responds; the agent resumes from a resumable state, not from mid-action.

This rule defines when to escalate, the exact file to write, the closed set of reasons the handler dispatches on, and the response loop the agent participates in. Architecture §6.4, §7.4, and the "inbox flow" discussion in the design summary are the sources.

## When to escalate

Four situations require escalation. They are the only situations the polling loop knows how to route, and are enumerated as values of the `reason` field in the escalation file:

- **`spinning_detected`** — the agent has hit one of the spinning thresholds from architecture §6.4: three consecutive failed verification cycles, wall-clock exceeded, or token budget exceeded. The agent stops before grinding further and escalates.
- **`autonomy_requires_approval`** — the task's autonomy level (`supervised`, in particular) requires a human "go" before writing code; or the autonomy level implies human-in-the-loop at a gate the agent has just reached.
- **`spec_level_blocker`** — the agent has encountered a spec-level contradiction, omission, or ambiguity that cannot be resolved inside the current task. A `spec-issue.md` has typically been filed against the specs/generator repo; this escalation notifies the human that a decision is blocked behind it.
- **`override_expiry_needs_review`** — an override's reapplication failed during reconciliation (see `override-registry.md`), or a tracking issue's resolution is ambiguous, and a human must decide whether to re-authorize, wait, or retire.

These four values are the only acceptable content of the `reason` field. Ad-hoc reasons are not routed — the handler dispatches on the enum, and a file whose reason falls outside it is dropped to a dead-letter path and a warning is emitted.

If the situation you are in does not fit one of these four, that is itself a signal: either you are being overly conservative and should continue, or you have discovered a new class of blocker that warrants a protocol change. In the latter case, still escalate — pick the closest-fitting reason and describe the situation precisely in the "Agent state" and "Decision requested" sections of the escalation file. Do not invent a new reason value.

## Writing the escalation file

Use the template at `shared/templates/human-escalation.md`. Fill in every placeholder, delete the HTML comments, and save the file under `/inbox/human-escalation/` with a name that a human can read at a glance: `<correlation_id>-<short-slug>.md`, for example `FEAT-2026-0042-T07-spinning.md`. One escalation per file.

The template has four mandatory sections:

1. **Correlation ID** — feature-level (`FEAT-YYYY-NNNN`) if the escalation is about the feature as a whole; task-level (`FEAT-YYYY-NNNN/TNN`) if it is about a single task.
2. **Reason** — exactly one of the four enumerated values above.
3. **Agent state** — the role, what the agent was doing, what it tried, and links to relevant issues, PRs, or event log entries. Enough for a human to pick up the thread cold without replaying the agent's history.
4. **Decision requested** — a specific question phrased so the human's answer is an unambiguous selection, with the options spelled out.

Poor escalations are the ones that force the human to reconstruct context before they can decide. The "Agent state" and "Decision requested" sections are where that work gets done on the agent side of the wall. Lead with facts, not hypotheses.

## State machine effects of raising an escalation

Raising an escalation is not only a message — it is a state transition on the work unit:

- For a **task**, the agent transitions the GitHub issue state to `blocked_human` (for `spinning_detected` and `autonomy_requires_approval`) or `blocked_spec` (for `spec_level_blocker`). See `state-vocabulary.md` for transition ownership. Label the issue accordingly (`state:blocked-human` or `state:blocked-spec`).
- For the **feature as a whole**, the agent escalates with a feature-level correlation ID and flags the feature state as `blocked` via an event. Only the human transitions the feature back to `in_progress` once the decision is recorded.
- For **`override_expiry_needs_review`**, the relevant task enters `blocked_spec` and the override record stays `active` until the human decides.

Transition the issue first, then write the inbox file. The file-write is what the polling loop picks up; the issue-state change is what other agents pick up if they look for ready work while the escalation is outstanding.

## Event-log accompaniment

On escalation, append a `human_escalation` event to the feature's event log. The payload should carry at minimum the `reason` value, the inbox filename, and a short (one-sentence) `summary`. The event and the inbox file are redundant by design: the inbox is the live work queue; the event log is the historical trail.

## Expected human response loop

Once the inbox file is written and the state is transitioned, the agent is done with its part. From here:

1. The polling loop archives the inbox file after dispatch.
2. The human reads the file, decides, and records the decision. The decision surface depends on the reason:
   - `spinning_detected` / `autonomy_requires_approval`: the human comments or edits the issue, then transitions it out of `blocked_human` back to `ready` (or `abandoned`, or another state the decision implies).
   - `spec_level_blocker`: the human typically triggers or approves a spec-repo change that resolves the underlying spec issue, then transitions the task out of `blocked_spec` to `ready`.
   - `override_expiry_needs_review`: the human either authorizes a new override, re-queues the task, or abandons it; the component agent picks up from there.
3. The corresponding `blocked_* → ready` (or `* → abandoned`) transition on the task, or the feature-level unblock, is the human's write — not the escalating agent's. Do not attempt to unblock your own escalation.

If a response does not arrive within whatever SLA the project is operating under, the agent does not re-escalate by writing a second inbox file. That produces duplicates and makes the queue harder to read. The agent stays stopped; the human sees a stale inbox and acts, or the polling loop surfaces long-outstanding items separately (out of scope here).

## What escalation is not

Escalation is not:

- **A soft "please review."** Use a PR review request for that. Escalation is for decisions that must be made before the agent can act.
- **An alternative to filing a spec issue.** Spec issues belong in the specs or generator repo as GitHub issues; they are the durable record of the spec-level problem. Escalations are the short-lived notification that something is now blocked on the human.
- **A way to broadcast progress.** Progress lives in the event log. Escalation is for things that have stopped.
- **Reversible without human action.** Once raised, the agent does not "withdraw" the escalation by deleting the file. If the situation resolves on its own — rare — append a follow-up event note and let the human close the loop.

## Quick checklist

Before writing the inbox file, confirm:

- The `reason` is one of the four enumerated values.
- The correlation ID is well-formed (see `correlation-ids.md`).
- The "Agent state" section has enough context for a cold reader.
- The "Decision requested" section names the options.
- The task/feature state has been transitioned appropriately.
- A `human_escalation` event has been (or will be, on the same commit) appended to the event log.

Then write the file. Once it is written, stop.
