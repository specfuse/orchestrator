<!--
Spec issue body template. v0.1.

Filed against the product specs repo (or the Specfuse generator project) when
a component or QA agent encounters a spec-level problem — a contradiction,
omission, or generated-code behavior that cannot be resolved inside the
triggering task. Generated files are never edited in place; they produce a
spec issue instead (orchestrator-architecture.md §9.1).

Fill in every placeholder and delete these HTML comments before posting.
-->

## Observation

<!-- What was observed, in one or two sentences. State the symptom, not the
hypothesized cause. -->

<observation>

## Location

<!-- File path and line range where the issue surfaces. Use
`<path>:<line>` or `<path>:<start>-<end>`. List multiple locations if the
problem spans files. -->

- <path>:<line>

## Triggering task

<!-- The task that uncovered the issue. Both the human-readable task reference
(`owner/repo#N`) and the task-level correlation ID are required so the event
log can be threaded back to this issue. -->

- Task issue: <owner/repo#N>
- Correlation ID: FEAT-YYYY-NNNN/TNN

## Suggested resolution

<!-- The fix the filing agent would propose, stated as a concrete change to
the spec or generator. If none is obvious, describe the constraints any fix
must satisfy. -->

<proposal>
