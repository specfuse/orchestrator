# Verify-before-report discipline

Every agent in the orchestrator operates on a four-step cycle: **state intent, act, verify, report.** The sequence is not advisory — it is the contract the orchestrator relies on to trust agent-emitted events. A `task_completed` event whose claim of completion was never verified is worse than no event at all, because downstream dependency recomputation will flip other tasks to `ready` on the strength of it.

This discipline applies to every operational role and to every unit of work, from writing a single file to closing a task.

## The four steps

### 1. State intent

Before acting, state in one sentence what you are about to do and why it is the next right step. This is the agent's equivalent of writing the PR title before the diff. Its purpose is to catch mismatches early: if you cannot state the intent clearly, you are not ready to act; if the stated intent disagrees with the task's acceptance criteria, the task is not what you thought it was.

The intent is addressed to the reader of the event log and — in multi-agent handoffs — to the next agent. It is not a soliloquy. Keep it factual, specific, and in the present tense ("I will add a validation check to the POST /orders handler," not "This task requires various modifications across the codebase").

### 2. Act

Perform the change. This is the ordinary work — editing a file, opening an issue, running a generator, writing a test plan. Stay within the scope declared in step 1. If the act expands beyond the intent — "while I was here I also fixed X" — either revise the intent and stay, or stop the act and leave X for another task. Drift between intent and action is the most common source of ambiguous PRs and is fixable only by discipline.

### 3. Verify

The verification step is the one agents most often skip, and the reason the discipline is named after it. "Verify" has two generic meanings and both apply unless the task explicitly narrows the scope:

**Re-read the produced artifact.** After writing a file, read it back. After opening an issue, fetch it back. After committing, inspect the resulting commit. The purpose is to confirm the action landed as intended: the text is what you meant to write, the labels are what you meant to apply, the YAML frontmatter parses. This catches silent failures of the writing tool, truncation, encoding surprises, and the class of bugs where the agent thought it produced X but produced Y.

**Run the declared verification commands.** Every work unit issue carries a `## Verification` section with a specific sequence of commands the agent must run (architecture §8). Run them in the declared order. The output of those commands is the evidence attached to the `task_completed` event. Generic verifications — "I assume the tests still pass" — are not verifications. The commands are the verification.

Additional generic checks apply in specific situations:

- Every event line must be piped through `scripts/validate-event.py` before it is appended to `events/*.jsonl`. The validator exits `0` on pass, `1` on schema violation (correct the event and re-validate — this counts as a verification cycle per §"Failure handling" below), and `2` on setup error (missing dependency or schema file — escalate rather than loop). An event that has not round-tripped through the validator with exit `0` must not be written to the log.
- When a per-type payload schema exists at `shared/schemas/events/<event_type>.schema.json`, the validator additionally validates the event's `payload` object against it after the top-level envelope check. An event whose envelope is well-formed but whose payload fails the per-type schema does not pass validation. Event types without a per-type schema file are unaffected — the extension is strictly additive, preserving the Phase 1 freeze contract for component-agent emissions whose per-type schemas have not yet been authored. Adding a new per-type schema later does not invalidate historical emissions that pre-dated it; the precedent and conventions live in `shared/schemas/events/README.md`.
- The `source_version` field on every event must be produced by `scripts/read-agent-version.sh <role>` at emission time, where `<role>` is the emitter's role directory under `/agents/` (`component`, `pm`, `qa`, `specs`, `config-steward`, `merge-watcher`). Never eye-cache the version string from an earlier read of `agents/<role>/version.md`: the value must be read at the moment the event is constructed. The script exits `0` with the version on stdout, `1` on parse failure (treat as a failed verification cycle), and `2` on setup error (unknown role, file missing — escalate). `human` events use the orchestration-repo commit SHA or `n/a` per the schema and do not invoke the script.

  **`source: human` events — commit SHA vs. `n/a` convention (WU 2.14, absorbs F1.5 + F2.6).** When populating `source_version` on a `source: human` event, choose as follows:

  - **Use the short commit SHA** (e.g. `42feb0d`, 7-hex characters from `git rev-parse --short HEAD` in the orchestration repo) when the emission is occurring in the context of a versioned orchestration-repo action — plan approval, feature state flip, manual escalation dispatch, or any human action directly tied to a specific orchestration-repo commit. The SHA names the repo state at the moment of the human's decision, which is informationally meaningful for audit and replay.
  - **Use `n/a`** when the emission is unattached to a specific orchestration-repo commit — for example, a test-time emission, a synthetic replay of a historical event, or a migration script running without a meaningful HEAD context.
  - **Default: prefer the commit SHA when in doubt.** It carries more provenance than `n/a` and costs nothing extra. `n/a` is the explicit opt-out for the unattached case.

  This convention is purely a human discipline; it does not change schema validation (the schema accepts any non-empty string for `source_version`). Historical events that used commit SHA or `n/a` remain valid — both values were permitted by the schema description before this clause was written, and this clause promotes the choice convention to a shared rule without retroactively invalidating any emission.
- Any other emitted JSON or YAML must parse. A feature frontmatter that fails `shared/schemas/feature-frontmatter.schema.json` is invalid. Verify before committing.
- Any correlation ID must match the pattern in `correlation-ids.md`. Verify before committing.
- Any state transition must be one your role is authorized to perform (`state-vocabulary.md`). Verify before committing.
- Any path you are about to write must not be in `never-touch.md`. Verify before writing.

If a verification check fails, the task is not done. You are now in one of three situations:

1. **Correctable locally.** Go back to step 2, act on the correction, verify again. This counts as one verification cycle.
2. **Three consecutive cycles have failed.** Spinning detection triggers; escalate per `escalation-protocol.md` with reason `spinning_detected`.
3. **Fundamentally blocked by spec or generator.** Escalate with reason `spec_level_blocker`; do not report completion.

### 4. Report structured output

Report only what verification confirmed. The structured output is:

- The `task_completed` (or equivalent) event appended to the feature's event log, with a payload describing what was produced and which verification commands passed.
- Any artifact the task was supposed to produce (PR, issue, file) referenced by its stable identifier (URL, path, correlation ID).
- A short human-facing summary for the reviewer, limited to what verification confirmed. Speculation, caveats, and "I did not test X" belong in the summary only if the task's verification scope genuinely left X untested — in which case that gap is a missed acceptance criterion, not a note.

**Do not report completion before verification has passed.** This is the inviolable rule. An event that claims `task_completed` without the corresponding verification output in the payload is a correctness bug in the orchestrator, not a style issue. Dependency recomputation will act on the claim; downstream tasks will be released; humans reviewing will trust the signal. If the verification did not pass, the event does not get emitted — the task state transitions to `blocked_*` or the verification cycle continues.

## What "verify" does not mean

- It does not mean "I thought about it and it seems right." The check must be mechanical.
- It does not mean "the previous step succeeded." Tools return success for the action they took, not for the property you want to guarantee.
- It does not mean "a similar task has passed before." Nothing about a prior run's success transfers to this one.
- It does not mean "I ran some of the verification commands." Run all of them unless the task explicitly marks one optional, in which case "optional" is still reported in the output.

## Forbidden shortcuts

- Reporting `task_completed` and then "let me go verify" in the same turn. Verification precedes the report; the order is part of the discipline.
- Editing a verification command out of the task issue because it is failing. That is a `never-touch.md` violation for branch protection's downstream analog — you do not weaken the checks to unblock yourself.
- Re-reading the artifact as a visual sanity check and then reporting without running the declared commands. Visual inspection complements the commands; it does not replace them.
- Running the verification commands once, seeing a failure, fixing the artifact, and reporting without running them again. Every verification cycle ends with a green run of the declared commands, or the cycle is not complete.

## Why this matters

The orchestrator's trust model is that agent-emitted events are reliable claims. Dependency recomputation, merge gating, and human review all bank on that. When an agent skips verification, the cost is not its own — it is paid by every downstream actor that trusted the event. Distributed "I think it's fine" is how drift becomes outage.

The discipline is uniform because the trust surface is uniform: no role gets to skip it, no task gets to skip it, no amount of previous success licenses skipping it this time. State intent, act, verify, report. Every time.
