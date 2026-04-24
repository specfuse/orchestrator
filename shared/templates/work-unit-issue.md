<!--
Work unit issue body template. v1.2.

This template is the body of every GitHub issue that represents a task
(implementation or QA) in a component repository. It is the contract
between the PM agent (which produces the issue) and the component or
QA agent (which consumes it).

This contract is **hard**. An issue whose frontmatter fails schema
validation or whose body is missing any of the five mandatory `##`
sections is malformed and will be rejected by the PM agent's
self-check at creation time. Agents that encounter a malformed issue
in the wild stop and raise a `spec_level_blocker` escalation rather
than attempt to infer the missing content.

The five-section structure below is fixed by orchestrator-architecture.md
§8 and may not be renamed, reordered, or extended with additional
top-level `##` sections. Sub-structure inside each section is free.
The optional `## Deliverables` section (added in v1.1) is the single
authorized extension to that structure — it sits between `## Context`
and `## Acceptance criteria` and may be omitted for implementation tasks.

Fill every `<...>` placeholder and delete these HTML comments before
posting. A fully-worked example of this template lives at
`shared/templates/work-unit-issue.example.md`.

v1.1 changes (WU 2.13):
- Added optional `deliverable_repo` frontmatter field (see annotation below).
- Added optional `## Deliverables` section between `## Context` and
  `## Acceptance criteria`.
Both additions are backwards-compatible: issues authored before v1.1
(without `deliverable_repo`, without `## Deliverables`) remain structurally
valid. For most tasks, omit `deliverable_repo` (defaults to `component_repo`).
For QA authoring / curation tasks whose deliverable lives in a product
specs repo, set `deliverable_repo: <product-specs-owner>/<product-specs-repo>`.

v1.2 changes (WU 3.10):
- Replaced the Phase-2-era concrete example target `clabonte/orchestrator`
  in this template's comments with the generic placeholder
  `<owner>/<repo>` (or `<product-specs-owner>/<product-specs-repo>` when
  clearly referring to a product specs repo). Rationale: Phase 2 predated
  the product specs repo split — product specs and test plans were
  committed to the orchestrator repo itself. From Phase 3 onwards, product
  specs live in a separate repo (e.g., `Bontyyy/orchestrator-specs-sample`
  for the walkthroughs), and the stale concrete example was inducing
  "stickiness" in cold invocations (F3.7 of the Phase 3 retrospective).
  Comment-only change; no YAML structure, frontmatter field, or mandatory
  section is modified. Fully backwards-compatible with v1.1 issues.
-->

```yaml
correlation_id: FEAT-YYYY-NNNN/TNN
task_type: <implementation | qa_authoring | qa_execution | qa_curation>
autonomy: <auto | review | supervised>
component_repo: <owner>/<repo>
# deliverable_repo: <owner>/<repo>   # OPTIONAL — omit for most tasks (defaults to component_repo).
                                      # Set when the task's primary deliverable lives in a different
                                      # repo from component_repo (e.g. QA authoring / curation tasks
                                      # whose test plan or curation record is committed to a
                                      # product specs repo rather than the target component repo).
                                      # Example: deliverable_repo: <product-specs-owner>/<product-specs-repo>
                                      # Commands in §Verification that operate on the deliverable
                                      # (read the file, run a script against it) run from
                                      # deliverable_repo's root; commands that build or test the
                                      # target component (dotnet test, pytest, mypy) still run from
                                      # component_repo's root.
depends_on: [] # task-local IDs within this feature, e.g. [T01, T03]
generated_surfaces: [] # paths (in component_repo) to generated files this task's acceptance depends on, e.g. ["_generated/Controllers/OrdersController.cs"]
```

<!--
Frontmatter field semantics:

- `correlation_id` (required) — task-level ID in the form
  `FEAT-YYYY-NNNN/TNN`, matching the pattern in
  `shared/rules/correlation-ids.md`. Unique within the feature.
- `task_type` (required) — one of the four task types from
  orchestrator-architecture.md §3. Drives which agent picks up the
  issue and which skills apply.
- `autonomy` (required) — one of `auto`, `review`, `supervised`
  from §3. `auto` currently behaves as `review` per §10 (auto-merge
  not yet enabled); set it honestly anyway so the downstream
  auto-merge flip is a config change, not a retroactive edit of
  every issue.
- `component_repo` (required for implementation and all QA task
  types) — the `<owner>/<repo>` the agent is instantiated against.
  An agent that picks up an issue whose `component_repo` does not
  match its own assignment stops and escalates with
  `spec_level_blocker`.
- `deliverable_repo` (optional) — the `<owner>/<repo>` where the
  task's primary deliverable lives. When absent, defaults to
  `component_repo`. When present, §Verification commands that
  operate on the deliverable file run from `deliverable_repo`'s root;
  commands that build, test, or gate-check the component still run
  from `component_repo`'s root. Typical use: `qa_authoring` and
  `qa_curation` tasks whose test plan or curation record is committed
  to a product specs repo (`<product-specs-owner>/<product-specs-repo>`),
  not the target component repo.
- `depends_on` (required, possibly empty) — task-local IDs (e.g.
  `[T01, T03]`) inside the same feature that must be `done` before
  this task can transition to `ready`. The PM agent's dependency
  recomputation reads this field.
- `generated_surfaces` (required, possibly empty) — paths inside
  `component_repo` to files under a generated directory
  (`_generated/`, `gen-src/`, or the repo's declared equivalent) that
  this task's acceptance depends on existing and behaving correctly.
  Used by the PM agent at plan time to cross-check generator template
  coverage (orchestrator-architecture.md §9.2) before flipping the
  task to `ready`.
-->

## Context

<!--
One paragraph placing this task in its feature: what the feature is,
which slice this task owns, links to the specs, test plans, or feature
description in the product specs repo that define the target behavior.
Include the feature-level correlation ID (`FEAT-YYYY-NNNN`) if it is
not already obvious from links.

The reader of this section is the agent picking the task up cold. Give
it enough context that it does not need to fetch the feature registry
entry before starting. Do not summarize the acceptance criteria here —
that is the next section.
-->

<!--
## Deliverables   ← OPTIONAL SECTION (v1.1)

Use this section when the task produces named files or artifacts that
live outside `component_repo` — typically `qa_authoring` and
`qa_curation` tasks whose deliverables are committed to `deliverable_repo`
(e.g. a product specs repo) rather than edited in-place in the target
component repo.

Omit for implementation tasks: their deliverable is the set of edited
source files in `component_repo`, which §Verification's build/test
commands already cover implicitly. No placeholder is needed.

When present, format as a short bullet list. Each bullet names the file
by its relative path from `deliverable_repo`'s root and adds a half-
sentence on what it contains. Example for a `qa_authoring` task:

  - `docs/walkthroughs/phase-2/test-plans/FEAT-2026-0004.md` — authored
    test plan covering widget quantity-filtered listing acceptance criteria.

Leave this block comment in place when posting; it is an HTML comment and
will not render on GitHub. Delete only when populating the section.
-->

## Acceptance criteria

<!--
A numbered list of explicit, testable statements of done. Each item
must be something a reviewer (or the QA agent) can mechanically check
against the delivered change. Avoid compound criteria ("X and also Y")
— split them so a single failure can be attributed to a single line.

Every criterion must be verifiable at merge time, not later. A
criterion that can only be checked in production is out of scope for
this template and belongs in a QA task of its own.
-->

1. <criterion>
2. <criterion>

## Do not touch

<!--
Paths and concerns this task must leave alone. Silence is not
permission — list every known boundary even when it feels redundant.
Conventional entries:

- Generated directories in `component_repo` (`_generated/`, `gen-src/`,
  or the repo's equivalent), unless `generated_surfaces` names an
  override path authorized for this task.
- Files owned by other tasks in the feature's task graph, named
  explicitly if the graph is already laid out.
- Anything under `/business/` in the product specs repo.
- Branch protection configuration anywhere.
- Secrets files (`.env`, `*.pem`, `*.key`, `credentials.json`, …).
- `.git/` internals.

A task that genuinely needs to write to one of the above is either
misscoped (escalate with `spec_level_blocker`) or needs a distinct
authorization path (the override protocol for generated code, a
human-approved branch-protection change for CI, etc.).
-->

- <path or concern>
- <path or concern>

## Verification

<!--
Exact commands the agent must run, in execution order, before
declaring the task done. These are the per-task acceptance checks
that ride on top of the six mandatory gates declared in
`.specfuse/verification.yml` (see
`/agents/component/skills/verification/SKILL.md`). Both sets must pass.

Commands run in the `component_repo` root unless the comment on the
line says otherwise. Prefer idempotent, deterministic commands — a
verification that passes flakily is not a verification.

Output from these commands is the evidence attached to the
`task_completed` event's `task_verification` array. Keep commands
focused: one command per acceptance line, ideally.
-->

```sh
<command>
<command>
```

## Escalation triggers

<!--
Conditions under which the agent must stop and raise a structured
escalation rather than push through. The four reasons enumerated in
`/shared/rules/escalation-protocol.md` — `spec_level_blocker`,
`override_expiry_needs_review`, `autonomy_requires_approval`,
`spinning_detected` — apply to every task unconditionally; do not
restate them here.

Use this section for task-specific triggers: spec ambiguities the
task is known to brush up against, dependencies whose absence the
agent should surface rather than work around, generated surfaces that
may or may not be present depending on upstream state, and anything
else where "push through" would be wrong.

If no task-specific triggers exist beyond the universal four, write
a single bullet: `- None beyond the four universal triggers in
shared/rules/escalation-protocol.md.`
-->

- <trigger>
- <trigger>
