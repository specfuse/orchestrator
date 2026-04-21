# Override registry protocol

An **override** is an authorized manual change to a file inside a generated directory. Under normal flow only the Specfuse generator writes to those directories (see `never-touch.md`); an override is the narrow, time-boxed exception. This rule defines who writes what, when, and how the exception is retired.

**Architecture §9.3 is normative.** This file operationalizes it for agents pulling `/shared/rules/` into context. The record shape is fixed by `shared/schemas/override.schema.json`.

## Scope

Overrides exist to unblock a task that cannot make progress without modifying generated code, while the real fix (a template or spec change) is still pending. They are a safety valve, not a permanent escape hatch. Every override is tied to an expiring condition that names exactly what resolves it, so the generator remains the long-term source of truth for its output directories.

If a task can be completed without touching generated code — by raising a spec issue, by waiting on an upstream fix, by adjusting hand-written code on the generator-consumer side — that is the correct path. An override is a last resort.

## Authorization

No agent may apply an override on its own authority. The authorization chain is:

1. The agent discovers that generated code is blocking progress and cannot proceed via the spec-issue path alone.
2. The agent raises a human escalation with reason `override_expiry_needs_review` or stops the task into `blocked_spec` (whichever the situation calls for; see `escalation-protocol.md`).
3. A human authorizes the override explicitly. This authorization is the trigger for creating the override record.
4. Only the component agent that owns the target repo may then apply and record the override, because reconciliation (below) is its responsibility and no other agent has the context to reconcile.

If a role that is not the owning component agent finds itself "needing to apply an override" — for example, a QA agent wanting to adjust a generated test harness — it stops and escalates instead. Cross-role overrides are not authorized.

## Recording

An override record is a structured file under `/overrides/`, validated against `shared/schemas/override.schema.json`. The required fields are:

- `files` — paths (relative to the component repo) of the generated files the override modifies. At least one, unique within the record.
- `task_correlation_id` — the task-level correlation ID (`FEAT-YYYY-NNNN/TNN`) of the task that required the override. This anchors the override in the event log.
- `tracking_issue` — the GitHub issue whose resolution retires the override, in `owner/repo#number` form. This is typically a spec issue or a generator template issue.
- `expiry_condition` — a human-readable description of what retires the override. Conventional phrasing: `"on closure of <tracking_issue>"`. Broader conditions are allowed when the situation demands them, but narrower is better.
- `timestamp` — ISO 8601 timestamp with timezone, marking when the human authorized the override.
- `status` — `active` when first recorded, `expired` once retired.

The component agent writes this file on the same commit as the manual modification to the generated file. An override that exists in the code but not in `/overrides/`, or vice versa, is inconsistent state; treat it as a `blocked_spec` condition.

On the same commit, append an `override_applied` event to the feature's event log, with the override record's identifying fields in the payload. This is how the override enters the cross-repo audit trail.

## The initial model: generator does not read the registry

**In the initial model, the Specfuse generator does not read `/overrides/`.** On every run it regenerates deterministically and blindly overwrites whatever lives in the generated directories, including manual overrides applied since the previous run. The registry exists for the agents' reconciliation logic, not for the generator.

This is a known, bounded risk: overrides can be clobbered between regeneration and reconciliation. The mitigation is the reconciliation step below. The future model (architecture §9.3, deferred) will invert control so the registry is authoritative and the generator reads it; that change is deferred because it raises the blast radius of a generator bug substantially.

## Reconciliation

After **any** regeneration event in a component repo, the component agent owning that repo walks the set of `active` override records against that repo. For each record, it performs exactly one of:

- **Reapply.** If the tracking issue still reflects reality — the underlying generator problem is not yet fixed and the manual change is still needed — reapply the change to the regenerated file, then append a reconciliation event to the event log. The override record stays `active`.
- **Retire.** If the tracking issue has been resolved upstream — the regenerated output now behaves correctly without the manual change — do not reapply. Instead:
  1. Leave the regenerated file alone.
  2. Set the override record's `status` to `expired` in `/overrides/`.
  3. Close the tracking issue if it is still open (the upstream fix landed; the tracker is formally retired here).
  4. Append an `override_expired` event to the feature's event log.

Reconciliation is the component agent's responsibility. The generator does not do it in the initial model. The human does not do it in the routine case. No other agent role does it. A single owner avoids race conditions between reapplication and retirement.

## Failure during reconciliation

If reapplication fails — for example, the regenerated file has shifted structurally and the override no longer cleanly applies — the component agent does **not** invent a substitute override. It:

1. Leaves the override record `active` and unmodified.
2. Transitions the relevant task to `blocked_spec`.
3. Raises a spec issue describing the structural change in the regenerated output that broke the override.
4. Raises a human escalation with reason `override_expiry_needs_review` so the human can decide whether to re-authorize a new override, wait on the upstream fix, or abandon the task.

A repeatedly-failing reapplication is a signal that the override has outlived its usefulness — the generator output has moved far enough that the patch no longer maps. That is a human decision, not an agent decision.

## Retirement outside reconciliation

If an agent observes that a tracking issue has been closed and the override's condition has been met, but no regeneration has yet occurred, the override stays `active`. Retirement only happens on the reconciliation pass triggered by regeneration, because only at that point is it safe to verify that the regenerated output behaves correctly without the override. Do not preemptively mark an override `expired`.

## Summary of responsibilities

| Action | Actor | Trigger |
|---|---|---|
| Authorize override | Human | Escalation from the owning component agent |
| Apply change to generated file | Owning component agent | Human authorization |
| Write `/overrides/<record>` with `status: active` | Owning component agent | Same commit as the file modification |
| Append `override_applied` event | Owning component agent | Same commit |
| Reconcile (reapply or retire) | Owning component agent | Any regeneration event in its repo |
| Mark record `expired`, append `override_expired` event | Owning component agent | Retirement during reconciliation |
| Read `/overrides/` | All agents (read-only) | When reasoning about generated code in a component repo |
| Write `/overrides/` | Owning component agent only | Per the flow above |

Other roles read the registry but do not write to it. The specs agent consults it when triaging spec issues; the PM agent consults it when recomputing dependencies (an outstanding override may constrain which tasks are safe to unblock); the QA agent consults it when authoring or executing tests against code that has diverged from the generated baseline.
