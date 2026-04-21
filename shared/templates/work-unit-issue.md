<!--
Work unit issue body template. v0.1.

Used for every GitHub issue that represents a task (implementation or QA) in a
component repository. The five `##` sections below are the work unit contract
defined in orchestrator-architecture.md §8 — all five are mandatory. An issue
missing any section is malformed and will be rejected by the PM agent's
self-check.

Fill in every placeholder (`<...>`) and delete these HTML comments before
posting. Do not rename, reorder, or omit sections.
-->

```yaml
correlation_id: FEAT-YYYY-NNNN/TNN
task_type: <implementation | qa_authoring | qa_execution | qa_curation>
autonomy: <auto | review | supervised>
depends_on: [] # task-local IDs within this feature, e.g. [T01, T03]
```

## Context

<!-- One paragraph placing this task in its feature: what the feature is, which
slice this task owns, and links to the specs or test plans in the product specs
repo that define the target behavior. Include the feature correlation ID. -->

## Acceptance criteria

<!-- A numbered list of explicit, testable statements of done. Each item must
be something a reviewer can mechanically check against the delivered change. -->

1. <criterion>
2. <criterion>

## Do not touch

<!-- Paths and concerns this task must leave alone: generated code directories
(`_generated/`, `gen-src/`, etc.), files owned by other tasks in the graph,
anything under `/business/`, branch protection configuration, and secrets. Be
explicit; silence here is not permission. -->

- <path or concern>
- <path or concern>

## Verification

<!-- The exact commands the agent must run before declaring the task done, in
execution order. Output of these commands is the evidence attached to the
`task_completed` event. -->

```sh
<command>
<command>
```

## Escalation triggers

<!-- Conditions under which the agent must stop and raise a structured issue
rather than push through. At minimum: spec-level contradictions, missing
boilerplate the plan assumed, three consecutive failed verification cycles, or
any change that would require modifying a "do not touch" path. -->

- <trigger>
- <trigger>
