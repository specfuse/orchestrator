# PM agent — issue-drafting specification

This file is a **forward specification**, not a v0.1 operational contract. It is a requirement that the Phase 2 work unit which authors the PM agent's issue-drafting skill must honor on day one. It exists because WU 1.5 Task B demonstrated the failure mode it prevents; WU 1.6 (retrospective) promoted it to Fix-in-Phase-1 under Finding 3 and scheduled it as WU 1.9.

When the issue-drafting skill is written in Phase 2, this file is its inherited contract. Revisions require the same level of justification as amendments to a shared rule: they alter the contract every downstream agent depends on.

## Why this exists

In WU 1.5 Task B, the PM-drafted work-unit issue body excluded controller-level tests "by symmetry with the other widget endpoints, which also only have service-level tests in this repo." The claim was false — `WidgetsControllerTests.cs` already existed on `main`. The component agent picked up the task, wrote code against the false scope, hit the coverage gate mid-task, and required an in-flight issue-body amendment plus three added controller tests before the task could close.

An issue body whose factual claims about repo state are asserted from memory — rather than verified from the repo at draft time — produces exactly the kind of internally-inconsistent document that forces downstream agents into `spec_level_blocker` escalations. The downstream cost is not theoretical; Task B paid it and Task C was deliberately designed to re-exercise it. Shipping a PM agent that does not re-verify claims at draft time would guarantee the failure mode in normal operation.

The discipline below is the minimum contract the Phase 2 issue-drafting skill must implement.

## What must be verified

Every factual claim about the target component repo's state that appears in the issue body must be re-verified against the repo at drafting time. "Claim" is deliberately broad — if the body asserts something about the repo, the skill must have a fresh observation supporting it. The categories below are not exhaustive:

- **File existence / non-existence.** Claims that a file exists, that a file does not exist, or that a directory contains (or lacks) a particular class of file. Verified by a listing or read of the path at draft time.
- **Existing conventions.** Claims that the repo follows a pattern (e.g. "tests live under `tests/<module>/`", "all controllers inherit from `BaseController`", "the repo uses X library for validation"). Verified by reading a representative sample — not a single outlier — at draft time.
- **File contents.** Claims that a named file contains (or lacks) a specific class, method, constant, or fragment. Verified by reading the file at draft time, not by trusting an earlier read from the same session.
- **Build, test, or tooling commands.** Claims that a specific command works or produces a specific output. Verified by reading `.specfuse/verification.yml`, the repo's package manifest, CI config, or equivalent — not by inferring from conventions.
- **Dependency and call relationships.** Claims that code A calls code B, that a component consumes an upstream, that a handler routes to a service. Verified by a grep or symbol search at draft time.
- **Prior related work.** Claims about what a previous task, PR, or feature produced in the target repo. Verified by inspecting `git log`, the merged PR, or the resulting files — not by trusting the feature registry alone, which can drift from repo state.

Claims about the specs repo, the generator, or orchestrator-internal state (event log, feature registry, labels) are out of scope for this specification. Those surfaces have their own verification disciplines (`verify-before-report.md` §3 for events, frontmatter schemas for the registry).

## Which sections of the issue body are covered

All five mandatory sections of `shared/templates/work-unit-issue.md` can carry claims about repo state:

- **Context** — most-frequent home of "the repo currently does X" framing.
- **Acceptance criteria** — often implies "X does not currently exist" or "the existing implementation of X is Y".
- **Do not touch** — names files and conventions by assertion; if the named path does not exist or the named convention is not actually in force, the clause is vacuous or misleading.
- **Verification** — references commands that must actually work on the target repo.
- **Escalation triggers** — may reference specific paths or conditions that must match repo reality to be actionable.

The specification applies section-by-section: any assertion about repo state in any section is in scope, not only the "Context" section.

## Discipline

Verification must happen **at drafting time**, not from earlier reads in the same session. A read performed when the feature was first decomposed into tasks has already gone stale by the time the task body is being written: other work in the session, other tasks on the same feature, or upstream commits may have changed the relevant surface. The rule is strict because the failure mode (Task B) was a session-cached assumption that was true when first observed and false by the time the body was written.

The Phase 2 skill's concrete implementation of this discipline is its own decision, but it must cover:

1. **Per-claim verification.** Each assertion about repo state is paired with a verification action (command, file read, grep) taken at draft time.
2. **No transitive trust.** The skill does not infer "X is still true" from an earlier observation in the same session, even if the earlier observation was documented in the feature registry or a sibling task's body.
3. **Structured reformulation when verification fails.** If a claim cannot be verified (the asserted fact is not the current state, or the verification is ambiguous), the skill either reformulates the claim to match what is verifiable, or escalates `spec_level_blocker` if the task's shape depends on the unverifiable assertion. The skill does not ship the claim unverified with a hedge.

## Evidence logging

A reviewer reading the issue later must be able to reconstruct what was verified and how. The Phase 2 skill picks the durable surface:

- The **drafting transcript** — the conversation log between the PM agent and the human, including the tool calls and their outputs.
- The **Context section of the issue body** — a short paragraph listing the verifications performed, suitable for reviewers who will not read the transcript.
- An **event payload** on the feature's event log — e.g. a new event type or an addition to `task_ready` that references the verification set.

At least one of the three must carry the evidence. The choice is the Phase 2 implementation's, but silent drafting — where no record of the verification exists after the fact — is not acceptable. The audit requirement is the whole point of the discipline.

## Failure mode — when a claim cannot be verified

Two legitimate outcomes:

1. **Reformulate.** If the claim is decorative (e.g. framing in the Context section) or scope-informing (Out-of-scope hints), and the verification is inconclusive rather than contradicted, the skill reformulates the claim to what *is* verifiable. "The other widget endpoints also only have service-level tests" becomes "The existing widget endpoints have mixed coverage; controller-level tests are required for new endpoints in this task per §Acceptance criteria." Accuracy over elegance.

2. **Escalate `spec_level_blocker`.** If the task's shape depends on an assertion that turns out to be contradicted by repo state (the "symmetry" assumption that Task B was built on was load-bearing — removing it changed the task's scope), the skill stops drafting and escalates. The feature returns to `planning` or the task is reshaped; it is never shipped as a malformed issue.

The skill does **not** paper over an unverifiable claim with a hedge ("should be", "I think", "per convention"). A claim that cannot be stated as a verified fact does not belong in the issue body.

## References

- `docs/walkthroughs/phase-1/task-B-log.md` — the incident this specification addresses.
- `docs/walkthroughs/phase-1/retrospective.md` §"Finding 3" — triage and rationale for fixing in Phase 1.
- `docs/orchestrator-implementation-plan.md` §"Addendum — post-retrospective Phase 1 fixes" — ladder entry for WU 1.9.
- `shared/rules/verify-before-report.md` §3 — the post-action verification discipline this specification complements. Verify-before-report covers what the agent produces; this file covers what the agent *claims* in order to produce it.
- `shared/templates/work-unit-issue.md` — the document whose contents this specification constrains.
