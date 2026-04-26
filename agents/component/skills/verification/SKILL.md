# Component agent — verification skill (v1)

## Purpose

This skill is how the component agent operationalizes [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) for its role. It defines the exact verification gates the agent runs before emitting a `task_completed` event, how the agent discovers which commands to run in the target component repo, how it interprets results, how it reports evidence, and how it handles failure.

The gates enumerated here **match** the GitHub branch-protection checks from architecture §10. An agent that passes its own verification but fails branch protection is doing the wrong thing — the gate sets are aligned by design.

## Scope

This skill governs the verification that happens inside the component agent, before the PR is opened (and, when the task demands, after opening if a required check depends on the PR existing). It does **not** replace branch protection; it confirms the PR is ready to be subjected to it.

The per-task `## Verification` section in the work unit issue body is separate: those are task-specific acceptance commands. The agent runs those **in addition** to the mandatory gates below, per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md). Both sets must pass.

## The `.specfuse/verification.yml` convention

Every component repo declares how its mandatory gates are run in a file at the repo root:

```
<component-repo>/
  .specfuse/
    verification.yml
```

The component agent reads this file on every task. A repo whose `verification.yml` is missing, invalid YAML, or missing a mandatory gate is not ready for autonomous agent work; the agent escalates with `spec_level_blocker` (reason in the escalation body: "repository verification contract missing or incomplete").

### Shape

```yaml
# .specfuse/verification.yml — verification contract for this component repo.
# Consumed by the component agent verification skill (agents/component/skills/verification/SKILL.md).
#
# All six mandatory gates below must be declared. A gate that cannot yet be
# configured in this repo sets `status: not_yet_configured` with a `tracking_issue`
# pointing at the issue that will land the configuration; until then, tasks in
# this repo cannot pass verification.

tests:
  command: "<shell command that runs the full test suite>"
  passing_pattern: "<optional regex matched against stdout to confirm success>"
coverage:
  command: "<shell command that produces a coverage report>"
  report_path: "<relative path to the produced report>"
  minimum_line_coverage: 0.90  # architecture §10 mandates >= 0.90
compiler_warnings:
  command: "<shell command that builds with warnings-as-errors>"
lint:
  command: "<shell command that runs the linter(s) in check mode>"
security_scan:
  command: "<shell command that runs the OWASP-equivalent scan>"
  report_path: "<relative path to the produced report>"
build:
  command: "<shell command that produces a release build>"
```

Each top-level key is a **gate name** and corresponds to one row in the structured verification output the agent emits. The agent runs the gates in the order listed above: `tests`, `coverage`, `compiler_warnings`, `lint`, `security_scan`, `build`. Ordering matters because cheaper gates fail fast and expensive gates (security scan, full build) run only when earlier gates have already passed.

### Declaring a gate as not yet configured

```yaml
security_scan:
  status: not_yet_configured
  tracking_issue: acme/some-repo#42
```

A gate in this state is treated as a **failing gate** for verification purposes — the agent does not emit `task_completed`. The only way to unblock is for the human to land the configuration change. This is deliberate: the alternative — "skip the gate for now" — corrodes the trust model as soon as it is allowed.

## The six mandatory gates

Mirror architecture §10. None is optional.

1. **`tests`** — every test in the suite passes. Any test runner.
2. **`coverage`** — line coverage ≥ 90% on the produced report. The agent parses the `report_path` and compares against `minimum_line_coverage`.
3. **`compiler_warnings`** — zero compiler warnings. Build with warnings-as-errors (or equivalent strict mode).
4. **`lint`** — clean lint. Linter runs in check/verify mode (non-modifying).
5. **`security_scan`** — clean OWASP-equivalent scan on the repo's declared stack.
6. **`build`** — clean release build. Catches problems a debug build tolerates.

The gates are a **conjunction**: all must pass. A single failure means the task is not done.

## Pre-gate build step

Before entering the gate sequence, if any mandatory gate's command embeds `--no-build` or `--no-restore` (or the equivalent "skip-build" flag for the component's language stack), the agent **must** run a build command against the repo root first — for .NET components, `dotnet restore && dotnet build`; for equivalent flags on other stacks, the stack's standard restore-and-build sequence. The pre-step runs once per task, immediately before gate 1 (`tests`); its output is not part of the `task_completed` evidence shape.

The failure mode this prevents is the **stale-artifact trap**: a gate command that embeds `--no-build` silently runs against whatever binaries are already on disk. On a fresh checkout — or after the agent has added new test files, renamed a symbol, or switched branches — the pre-existing `bin/` and `obj/` artifacts are out of sync with the current source tree. A `tests` gate using `dotnet test --no-build` against stale artifacts can pass while the new tests are never actually executed, or fail for reasons unrelated to the code change under test. Either outcome corrodes the trust model the gate set exists to uphold.

This pre-step is **not** itself one of the six gates — it is a prerequisite. It does not appear in the `task_completed` payload's `gates[]` array, it does not participate in spinning detection, and its output shape is not defined here. If the pre-build itself fails (exit non-zero), the agent treats the failure as a gate-sequence blocker per §"Failure handling" below (category 1: correctable locally) — the agent reads the build error, corrects its change, and retries the full pre-step plus gate sequence from the top.

Origin: this section absorbs Phase 1 retrospective Finding 8 per the Phase 1 retrospective's defer language ("carry into the next edit of `verification/SKILL.md`, opportunistically — no dedicated work unit required"). Phase 3 walkthrough WU 3.6 produced 2-feature live empirical evidence for the trap on component-agent verification runs (F1 Step 5 and F2 Step 5 of [`docs/walkthroughs/phase-3/`](../../../../docs/walkthroughs/phase-3/)), satisfying the Phase 1 dispatch condition.

## Running a gate

For each gate, the agent:

1. Resolves the command from `verification.yml`.
2. Records the wall-clock start time.
3. Invokes the command with the repo root as the working directory.
4. Captures exit code, stdout, and stderr.
5. Records the wall-clock end time and computes `duration_seconds`.
6. Applies the gate-specific interpretation below.
7. Emits a structured result object (shape defined below).

### Per-gate interpretation

| Gate | Pass condition |
|---|---|
| `tests` | Exit code `0`. If `passing_pattern` is set, it must match stdout in addition. |
| `coverage` | Exit code `0` **and** the parsed line-coverage value from `report_path` is `>= minimum_line_coverage`. |
| `compiler_warnings` | Exit code `0`. (The command is responsible for failing on warnings — typically via warnings-as-errors.) |
| `lint` | Exit code `0`. |
| `security_scan` | Exit code `0` **and** the parsed report at `report_path` contains zero high or critical findings. |
| `build` | Exit code `0`. |

If a command's declared behavior is not met (e.g., a coverage command exited `0` but `report_path` does not exist), the gate is treated as **fail with an invalid run**, not pass. Invalid runs count as a failed verification cycle for spinning detection.

### Output shape per gate

```json
{
  "gate_name": "tests",
  "status": "pass",
  "evidence": "Passed! - Failed: 0, Passed: 412, Skipped: 3, Total: 415",
  "duration_seconds": 12.3
}
```

- `gate_name` — one of `tests`, `coverage`, `compiler_warnings`, `lint`, `security_scan`, `build`.
- `status` — `pass` or `fail`. No third value.
- `evidence` — a short, human-readable excerpt that substantiates the status: a test summary line, the parsed coverage number, the count of warnings found, the top finding from the security scan, etc. If the raw output is too large, excerpt to the most load-bearing line and reference where the full output lives (artifact path in CI, gist URL, etc.). Secrets must be redacted per [`security-boundaries.md`](../../../../shared/rules/security-boundaries.md) before any evidence is emitted.
- `duration_seconds` — wall-clock seconds, floating point.

## Reporting: the `task_completed` payload

When **all six** gates pass and the per-task `## Verification` commands from the issue body pass, the agent emits a single `task_completed` event whose `payload` carries the verification evidence:

```json
{
  "pr_url": "https://github.com/<owner>/<repo>/pull/<N>",
  "branch": "feat/FEAT-YYYY-NNNN-TNN-<slug>",
  "verification": {
    "overall_status": "pass",
    "total_duration_seconds": 128.7,
    "gates": [
      { "gate_name": "tests", "status": "pass", "evidence": "412/412 passed", "duration_seconds": 12.3 },
      { "gate_name": "coverage", "status": "pass", "evidence": "line coverage 0.94 (threshold 0.90)", "duration_seconds": 14.1 },
      { "gate_name": "compiler_warnings", "status": "pass", "evidence": "0 warnings", "duration_seconds": 8.9 },
      { "gate_name": "lint", "status": "pass", "evidence": "clean", "duration_seconds": 3.2 },
      { "gate_name": "security_scan", "status": "pass", "evidence": "0 high, 0 critical findings", "duration_seconds": 41.2 },
      { "gate_name": "build", "status": "pass", "evidence": "Release build ok", "duration_seconds": 49.0 }
    ],
    "task_verification": [
      { "command": "<command from issue body>", "status": "pass", "evidence": "<excerpt>", "duration_seconds": 0.8 }
    ]
  }
}
```

The event itself must validate against [`event.schema.json`](../../../../shared/schemas/event.schema.json). The `payload` object is open by schema, but the shape above is the **role-specific contract** for component-agent `task_completed` events; deviations from it are a bug in this skill, not an allowed variation.

Before emitting the event, the agent re-runs the universal checks from [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md):

- Every correlation ID in the payload and the event itself matches the pattern in [`correlation-ids.md`](../../../../shared/rules/correlation-ids.md).
- The event JSON is piped through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) and the validator exits `0` before the line is appended to `events/FEAT-YYYY-NNNN.jsonl`. Exit `1` (schema violation) sends the event back to construction and counts as a failed verification cycle; exit `2` (setup error) escalates per `verify-before-report.md` §3.
- No secret-looking value appears anywhere in the payload (see [`security-boundaries.md`](../../../../shared/rules/security-boundaries.md) §"Log hygiene").

## Failure handling

If any gate fails — including an invalid run — the agent does **not** emit `task_completed`. It is now in one of three situations, in order of first-to-try:

### 1. Correctable locally (one verification cycle)

The failure indicates a problem in the agent's own change: a test it broke, a warning it introduced, a coverage drop from missing tests on new code, etc.

The agent:

1. Reads the failing evidence.
2. Makes a corrective edit to its own hand-written code.
3. Commits the correction on the same feature branch with a `fixup:` or `verification:` prefix on the message, preserving the `Feature: FEAT-YYYY-NNNN/TNN` trailer.
4. Re-runs **every** gate from the top, not only the failing one. Partial re-runs are forbidden: a later gate may have been masked by the earlier failure.

A cycle is complete only when the full gate set has been re-run green. A run that fixes the original failure but introduces a new failure counts as a **failed** cycle, not a passed one.

### 2. Three cycles have failed in a row

Per architecture §6.4 and [`escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md), the agent transitions the task to `blocked_human`, writes a `human-escalation.md` with reason `spinning_detected`, appends a `human_escalation` event, and stops.

The agent tracks this cycle count **internally during the task** — it is not a field in `verification.yml` or the issue body. The detailed mechanics of the counter (state storage, reset rules) live in [`../escalation/SKILL.md`](../escalation/SKILL.md); this skill only raises the event and stops.

### 3. The failure is not locally correctable

If the failing gate points at a spec-level or generator-level problem — for example, a test against the generated surface that fails because the generated code is wrong — the agent does not rewrite the test to accept the wrong behavior, and it does not edit the generated file. It:

1. Files a `spec-issue.md` against the specs or generator repo.
2. Transitions the task to `blocked_spec` and appends a `task_blocked` event (plus a `spec_issue_raised` event referencing the filed issue).
3. Writes a `human-escalation.md` with reason `spec_level_blocker` only if the human needs to unblock something the spec-issue filing alone does not surface (e.g., the blocked task is on a critical path).

This path is distinct from spinning: the agent is not iterating against itself, so the cycle counter does not apply.

## Worked example — clean run

Task `FEAT-2026-0007/T03` adds a validation check to a handler in `acme/api-sample`. The repo's `.specfuse/verification.yml` declares .NET commands for the six gates.

The agent, after writing the change and committing:

1. Reads `.specfuse/verification.yml`. Valid, all six gates declared with real commands.
2. Runs `tests`: exit `0`, evidence `"Passed! - Failed: 0, Passed: 128"`, duration `8.1s`. → `pass`.
3. Runs `coverage`: exit `0`, parses `./coverage.opencover.xml`, line coverage `0.93`, threshold `0.90`. → `pass`.
4. Runs `compiler_warnings`: exit `0` with warnings-as-errors, evidence `"0 warnings"`. → `pass`.
5. Runs `lint`: exit `0`. → `pass`.
6. Runs `security_scan`: exit `0`, report has `0 high, 0 critical`. → `pass`.
7. Runs `build`: exit `0`. → `pass`.
8. Runs the per-task `## Verification` commands from the issue body — all pass.
9. Re-reads the produced diff, commit, and PR description; every correlation ID matches pattern; no secret-looking value in the event payload.
10. Opens the PR, transitions `in_progress → in_review`, emits `task_completed` with the payload shape above. Stops.

## Worked example — failing run retried

Same task as above. The agent's first pass introduces a test regression.

1. Runs `tests`: exit `1`, evidence `"Failed: 1, Passed: 127 — OrdersControllerTests.Reject_missing_email"`, duration `8.3s`. → `fail`.
2. Cycle 1 failure: agent reads the failing test, sees it expected the handler to reject missing emails, realizes its validation check was over-permissive. Corrects the handler code, commits with message `verification: tighten email presence check — Feature: FEAT-2026-0007/T03`.
3. Re-runs **all six gates** from `tests`. This time `tests` passes (`128/128`).
4. Continues through `coverage` (`0.91`, passes), `compiler_warnings` (pass), `lint` (fails — new code path has a style violation).
5. Cycle 2 failure: agent reads the lint evidence, applies the fix, commits, re-runs all six gates from the top.
6. Full pass on cycle 2 re-run. No per-task verification failures. Opens PR. Emits `task_completed` with a payload whose gates are all `pass` and whose `total_duration_seconds` covers the final green run — not the failed cycles. The failed cycles are reconstructable from the commit history and event log but do not appear in the success payload.

Had cycle 2 also failed, the agent would still have had one cycle left before spinning. Had three consecutive cycles failed, the agent would have stopped and escalated per §"Failure handling" above.

## What this skill does not cover

- How the PR is actually opened, including branch-name and commit-trailer discipline — that is [`../pr-submission/SKILL.md`](../pr-submission/SKILL.md) (WU 1.3).
- How the escalation counter is stored, reset, and surfaced — that is [`../escalation/SKILL.md`](../escalation/SKILL.md) (WU 1.3).
- How overrides are reconciled after regeneration — that follows [`override-registry.md`](../../../../shared/rules/override-registry.md) and is invoked separately from this skill, not as part of a per-task verification run.

## Version

- `1.2` — WU 3.8: added §"Pre-gate build step" documenting the mandatory `dotnet restore && dotnet build` (or stack-equivalent) pre-step before any gate whose command embeds `--no-build` or `--no-restore`. Absorbs Phase 1 walkthrough retrospective Finding 8 per its defer language ("carry into the next edit of `verification/SKILL.md`, opportunistically — no dedicated work unit required"). Triggered by 2-feature live empirical evidence from Phase 3 WU 3.6 (F1 Step 5 + F2 Step 5; finding F3.1 of the Phase 3 retrospective). Amendment is purely additive — no existing gate, gate order, or output shape is modified; Phase 1 v1.5.0 frozen surface is preserved.
- `1.1` — WU 1.7: tightened pre-emission checks to require `scripts/validate-event.py` exit `0` before appending the `task_completed` event. Exit `1` loops back as a failed verification cycle; exit `2` escalates. Finding 1 of the Phase 1 walkthrough retrospective.
- `1.0` — Phase 1 initial.
