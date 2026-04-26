# PM agent — task decomposition skill (v1.2)

## Purpose

This skill turns a validated feature specification into a complete task graph persisted in the feature registry frontmatter. It is the first skill in the PM pipeline: every downstream skill (plan-review, issue-drafting, dependency-recomputation, template-coverage) consumes the graph this one produces. The shape of the graph is therefore a **hard internal contract** for Phase 2.

The skill does not draft issue bodies, does not open GitHub issues, and does not validate template coverage. It produces the graph structure only; its siblings take it from there.

## Scope

In scope:

- Reading the feature spec files and feature registry to understand what the feature delivers and which repos it touches.
- Identifying implementation tasks and QA tasks (with QA subtypes per architecture §6.2).
- Assigning each task to a specific component repo from the feature's `involved_repos`.
- Constructing the `depends_on` edges between tasks.
- Setting autonomy (feature-level default, with skill-driven overrides where safety policy requires).
- Writing the resulting graph to the feature frontmatter and emitting `task_graph_drafted`.

Out of scope (each belongs to a later skill or WU):

- Drafting GitHub issue bodies — [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md), WU 2.4.
- Materializing the task graph as a human-readable review file — [`../plan-review/SKILL.md`](../plan-review/SKILL.md), WU 2.3.
- Confirming Specfuse template coverage for each task — [`../template-coverage/SKILL.md`](../template-coverage/SKILL.md), WU 2.6.
- Flipping the feature state from `planning` to `plan_review` — that happens in the plan-review skill after this skill plus template-coverage have succeeded.

## Inputs

The skill reads, in order:

1. The feature registry file at `/features/<correlation_id>.md` — its frontmatter (`correlation_id`, `state`, `involved_repos`, `autonomy_default`) and its prose body.
2. The spec files listed in the feature registry's `## Related specs` section — typically paths under the product specs repo's `/product/` tree (OpenAPI, AsyncAPI, Arazzo, feature narratives, test-plan stubs).
3. The feature registry's `## Task routing` section (if present) — the explicit mapping from capability to target repo when `involved_repos` has more than one entry. The specs agent or human writes this section during feature drafting.
4. This skill's own file and [`../../CLAUDE.md`](../../CLAUDE.md) — reloaded per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

The skill does **not** read the target component repos' source at decomposition time. Target-repo state is only re-read at issue-drafting time (WU 2.4), per [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) — the two skills have different verification windows by design.

## Outputs

- The `task_graph` array in `/features/<correlation_id>.md`'s frontmatter, populated.
- A `task_graph_drafted` event appended to `/events/<correlation_id>.jsonl`.

No GitHub API calls. No issue creation. No state flip on the feature (it stays in `planning`).

## The decomposition procedure

**The procedure consists of 8 numbered steps** (Step 1 through Step 8). Downstream references — in the work unit issue body's `## Verification` section, in [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification", or in any other consumer — should use this SKILL's step numbering as the canonical source. Step 1 (Read the feature context), Step 2 (Identify capabilities from the spec), Step 3 (Derive implementation tasks + target-repo assignment), Step 4 (Derive QA tasks), Step 5 (Construct `depends_on` edges), Step 6 (Set autonomy levels), Step 7 (Validate the graph), Step 8 (Write to frontmatter and emit `task_graph_drafted`).

### Step 1 — Read the feature context

State the intent (per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1): "I will decompose `<correlation_id>` into a task graph."

Read the feature registry frontmatter and confirm:

- `state` is `planning` (the skill runs only while the feature is in the PM-owned planning window).
- `task_graph` is currently empty. If it is non-empty, the feature has already been decomposed once; this is a **re-decomposition pass** (the spec has changed since the first pass) and the skill must increment `decomposition_pass` in its emitted event. Re-decomposition overwrites the prior `task_graph` field — it is not a merge.
- `involved_repos` lists at least one repo.
- `autonomy_default` is set.

Read the prose body for the `## Description`, `## Scope`, `## Out of scope`, `## Related specs`, and `## Task routing` sections. Every spec path listed under `## Related specs` is read next.

### Step 2 — Identify capabilities from the spec

A **capability** is a discrete, user-facing or system-facing behavior the feature delivers. The spec is the source of truth for the capability list; the skill does not invent capabilities from the feature prose alone.

For each spec type, the capability unit is:

- **OpenAPI** — one capability per operation (`path` + `method`). An operation with multiple response schemas is still one capability.
- **AsyncAPI** — one capability per operation (per channel direction). A single channel with both `publish` and `subscribe` operations yields two capabilities.
- **Arazzo workflow** — one capability per workflow. Multi-step workflows are a single capability at the decomposition level; the step-by-step shape is a component-agent implementation concern.
- **DB schema / migration fragment** — one capability per logical change (a new table, a new column on an existing table, a new index).
- **UI screen / component spec** — one capability per top-level screen or component. Sub-components are implementation detail.
- **Feature narrative in `/product/features/*.md` without a formal spec** — one capability per explicit "behavior" or "user story" heading.

If a spec type is not listed above, the skill escalates `spec_level_blocker` with reason "unhandled spec type: `<path>`". It does not invent a capability unit.

### Step 3 — Derive implementation tasks + target-repo assignment

One `implementation` task per capability, with the following target-repo assignment rules (applied in order):

1. **Single-repo feature.** If `involved_repos` has exactly one entry, every implementation task is assigned to that repo. No capability-level mapping required.
2. **Multi-repo feature.** If `involved_repos` has two or more entries, every capability must have an explicit target-repo declaration. The skill looks in:
   - The spec file itself (frontmatter `x-repo: owner/repo`, or a `Repo: owner/repo` line in a feature-prose spec).
   - The feature registry's `## Task routing` section, which maps capabilities to repos (e.g. `- GET /widgets/export → acme/api-sample`).
3. **No explicit declaration.** If rule 2 applies and a capability has no explicit declaration, the skill escalates `spec_level_blocker` with reason "target repo not declared for capability: `<capability>`". **The skill does not guess from repo names, path conventions, or spec heuristics.**

If a single capability is implemented across two repos (a rare but legitimate case — e.g., an API operation with a paired persistence port), the skill produces **one implementation task per repo**, with dependencies per step 5.

Each implementation task gets a sequential task ID (`T01`, `T02`, …) in the order they emerge from the capability list. The skill does not renumber mid-decomposition.

### Step 4 — Derive QA tasks

Per architecture §6.2, QA has three subtypes:

- `qa_authoring` — the QA agent drafts a test plan in `/product/test-plans/` (on the specs repo). One `qa_authoring` task per implementation task that changes observable behavior. Tasks that are internal refactors (no observable behavior delta) do not require QA authoring.
- `qa_execution` — the QA agent executes an authored plan against the delivered code. One `qa_execution` task per corresponding `qa_authoring` task. They pair 1:1.
- `qa_curation` — the QA agent reviews whether any existing regression suite entry should be added, updated, or retired in light of the feature. **One `qa_curation` task per feature**, not per implementation task. Assigned to the repo that hosts the dominant regression suite for the feature (if ambiguous, pick the repo with the most implementation tasks, and escalate `spec_level_blocker` if still ambiguous — do not guess).

#### Feature scope overrides

**The feature's `## Scope` section can explicitly constrain `qa_authoring` cardinality.** When it does — for example, "one authored test plan covering both behaviors" on a feature with two observable-behavior implementation tasks — honor the feature's stated shape and collapse the default per-behavior count to the number the feature names. The skill's default rule (one `qa_authoring` per implementation task that changes observable behavior) applies only when the feature's `## Scope` section does not address `qa_authoring` cardinality.

The override is one-directional: the feature can only collapse the count (fewer `qa_authoring` tasks than the default), not expand it. A feature scope that is silent on `qa_authoring` always uses the default.

*Example:* a two-repo feature with two behaviors names "one authored test plan covering both behaviors" in its `## Scope` section. The default rule would produce two `qa_authoring` tasks (one per behavior), but the explicit scope constraint collapses the count to one — resulting in one `qa_authoring` task on the primary-behavior repo, one `qa_execution` paired with it, and one `qa_curation`. Read the feature's `## Scope` before counting `qa_authoring` tasks; when in doubt whether a scope clause is constraining cardinality, treat it as constraining and produce the collapsed count.

QA task repo assignment:

- `qa_authoring` and `qa_execution` are assigned to the **same repo** as the implementation task they pair with. If an implementation task spans two repos (per step 3's rare case), the QA tasks pair with the primary repo (the one where the user-facing behavior is observable — typically the API or frontend side).
- `qa_curation` is assigned as described above.

QA task IDs continue the same sequence (`T03`, `T04`, …).

### Step 5 — Construct `depends_on` edges

The skill constructs dependencies using these rules, each applied independently:

1. **Implementation → implementation** (capability chain). If capability B builds on capability A (A's output is B's input), the `implementation` task for B depends on the `implementation` task for A. The capability chain is derived from the spec's `## Scope` ordering, explicit Arazzo workflow steps, and OpenAPI `$ref` chains. If the chain is ambiguous from the spec, the skill escalates `spec_level_blocker` — it does not guess ordering.
2. **qa_authoring** — no dependencies on implementation tasks. Test plans are authored from the spec in parallel with implementation.
3. **qa_execution** — depends on (a) the `implementation` tasks **for the same behavior** as its matched `qa_authoring`, AND (b) the matched `qa_authoring` task itself. The scope is the behavior, not the whole repo.

   *Same-behavior identification:* the feature's `### Behavior N` headings and `## Task routing` section map each behavior to its implementation task(s). Read those to determine which implementation tasks realize the behavior the `qa_execution` covers; only those tasks go into `depends_on`. When the feature has only one behavior implemented on a given repo, this rule collapses to "all implementation tasks on that repo" and is identical to the prior whole-repo reading.

   *Cross-repo implementation tasks mocked at the test boundary:* when the feature's narrative or `## Task routing` section states that the test-side repo mocks the cross-repo component (e.g. "the API side mocks the persistence port"), the cross-repo implementation task is NOT added to `qa_execution.depends_on`. The mock boundary is identified by reading the feature's behavioral description and the implementation task's stated contract; do not infer it from repo names alone.

   *Worked example — two behaviors on the same repo:* a feature with Behavior 1 (impl on api-repo: T02) and Behavior 2 (impl on api-repo: T03), each with its own `qa_authoring` (T04 for B1, T06 for B2) and `qa_execution` (T05 for B1, T07 for B2), produces: `T05.depends_on = [T02, T04]` (not `[T02, T03, T04]`) and `T07.depends_on = [T03, T06]` (not `[T02, T03, T06]`). Each `qa_execution` waits only for its own behavior's implementation to land, not for the unrelated behavior.
4. **qa_curation** — depends on every `qa_execution` task on the feature. Curation runs after all execution is green.
5. **No cross-feature dependencies.** `depends_on` only contains task IDs (`TNN`) within the same feature. A capability that genuinely depends on another feature's work is a **staging problem** — escalate `spec_level_blocker` so the specs/human can serialize the two features.

After building the edge set, the skill checks:

- **No cycles.** Standard topological-sort check. A cycle is a correctness bug in the rules above or a malformed spec; escalate `spec_level_blocker`.
- **No orphan references.** Every `TNN` in any `depends_on` array must correspond to a task `id` in the graph.

### Step 6 — Set autonomy levels

Every task starts with `autonomy` unset (it inherits `autonomy_default` from the feature frontmatter). The skill applies these **two override rules**, in order:

1. **`qa_execution` is never `auto`.** If `autonomy_default` is `auto`, every `qa_execution` task gets `autonomy: review` set explicitly on the task. Reasoning: a QA execution task running without review can silently mark a regression as "green" through a brittle assertion — the loss is asymmetric.
2. **Sensitive-path implementation tasks get `supervised`.** A task is "sensitive-path" if the spec-file or capability narrative explicitly mentions one of: authentication, authorization, credential handling, PII storage, payment processing, key management, or security-boundary enforcement. The skill sets `autonomy: supervised` on such implementation tasks (even if `autonomy_default` is `review` — the override strengthens, never weakens).

All other tasks keep `autonomy` absent, inheriting `autonomy_default`. Any additional per-task override — including weakening `supervised` back to `review` — is the human's call during plan review (WU 2.3).

The skill does not apply overrides beyond rules 1 and 2. Extending the override set requires a skill revision with retrospective justification.

### Step 7 — Validate the graph

Before writing, the skill runs these checks against the draft graph in memory:

1. **Schema round-trip.** The full feature frontmatter (including the draft `task_graph`) validates against [`/shared/schemas/feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) using `ajv`, `jsonschema`, or equivalent. Additional-properties rejection is on; unknown fields fail.
2. **Cycle check.** Topological sort of the `depends_on` edge set succeeds (no back-edges).
3. **Orphan check.** Every `TNN` appearing in any `depends_on` array matches a task `id` in the graph.
4. **Assigned-repo sanity.** Every task's `assigned_repo` is a member of `involved_repos`. A task assigned to a repo not declared in `involved_repos` means the decomposition is reaching outside the feature's declared footprint — escalate `spec_level_blocker`.
5. **QA pairing.** Every `qa_execution` task has exactly one matching `qa_authoring` task on its same repo, and vice versa (unless the implementation task is an internal refactor with no observable behavior, in which case both QA tasks are absent by design).

Note on the orphan check (check 3): the failure shape is asymmetric by edit direction. Adding a task risks orphans only on the new task's own `depends_on` entries — typically under the human's immediate attention during plan editing. Removing a task risks orphans in any surviving task's `depends_on` array, which may be far from the human's focus at the moment of the edit. The same check catches both directions; the asymmetry is worth keeping in mind when reviewing a plan-review edit that removes tasks.

If any check fails, the skill **does not write** the graph. It either corrects the draft (re-entering step 3–6) or escalates `spec_level_blocker`. It does not ship a partially-validated graph.

### Step 8 — Write to frontmatter and emit `task_graph_drafted`

After all checks pass:

1. Write the updated feature frontmatter to `/features/<correlation_id>.md`. Preserve the prose body unchanged — the skill edits frontmatter only.
2. Re-read the file back and confirm the frontmatter parses as written (per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3, re-read the produced artifact).
3. Construct the `task_graph_drafted` event:
   - `timestamp`: ISO-8601 at emission time.
   - `correlation_id`: the feature-level ID (no task suffix).
   - `event_type`: `task_graph_drafted`.
   - `source`: `pm`.
   - `source_version`: produced by `scripts/read-agent-version.sh pm` at emission time — never eye-cached from `version.md`.
   - `payload`: see shape below.
4. Pipe the event through `scripts/validate-event.py`. Require exit 0 before appending.
5. Append the event to `/events/<correlation_id>.jsonl`.
6. Re-read the appended event line and confirm it matches what was constructed.

### `task_graph_drafted` payload shape

```json
{
  "task_count": 4,
  "involved_repos": ["acme/api-sample", "acme/persistence-sample"],
  "decomposition_pass": 1
}
```

- `task_count` — integer, the number of tasks in the written `task_graph`.
- `involved_repos` — the `involved_repos` array from the feature frontmatter at emission time. Duplicated into the payload so a downstream consumer reading the event log without pulling the feature file can still reason about scope.
- `decomposition_pass` — 1 on first decomposition; incremented by 1 on each re-decomposition (spec change after planning). **This counter is not persisted in the feature frontmatter.** It is derived at emission time by counting the number of prior `task_graph_drafted` events already present in `/events/<correlation_id>.jsonl` for this feature (plus 1). On the first decomposition pass, the event log contains zero prior `task_graph_drafted` events for the feature, so `decomposition_pass` is 1. On each subsequent re-decomposition, count the existing `task_graph_drafted` events before appending the new one.

The payload is deliberately minimal. The task graph itself lives in the feature frontmatter and is not duplicated into the event — events reference state, they do not replicate it. Per-type payload schemas under `/shared/schemas/events/` are a Phase 2+ item (see WU 2.5, absorbing Finding 5); until then, this shape is documented here and must remain stable.

## Verification

Before emitting `task_graph_drafted`, every check from step 7 must have passed with direct evidence (not inferred, not assumed). The skill's verification evidence for a decomposition includes:

- The ajv/jsonschema command output confirming the frontmatter validates.
- The cycle-check output (a topologically-sorted task-ID sequence, or the explicit "no edges" result for a dep-free graph).
- The orphan-check output (the set of `TNN` references minus the set of task IDs — must be empty).
- The assigned-repo check (every `assigned_repo` ∈ `involved_repos`).
- The QA-pairing check.

Beyond the skill's local checks, the universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) apply:

- Re-read the feature registry file after writing (step 8 above).
- Round-trip the `task_graph_drafted` event through `scripts/validate-event.py` with exit 0.
- Confirm `source_version` is produced by `scripts/read-agent-version.sh pm` at emission time.
- Confirm the feature file path being written is not in [`never-touch.md`](../../../../shared/rules/never-touch.md).
- Confirm no state-machine transition was performed (the skill does not transition state; `state` remains `planning`).

Failure handling follows [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable → retry, spinning at 3 cycles → escalate `spinning_detected`, unrecoverable → escalate `spec_level_blocker`.

## Worked example

Fictional feature `FEAT-2026-0050 — Widget export endpoint`, used for illustration. Two component repos (API + persistence), four tasks, one autonomy override. The feature registry file before decomposition:

```yaml
---
correlation_id: FEAT-2026-0050
state: planning
involved_repos:
  - acme/api-sample
  - acme/persistence-sample
autonomy_default: auto
task_graph: []
---

## Description

Add a `GET /widgets/export` endpoint that streams all widgets as a filtered CSV,
supporting the `status` and `created_after` query parameters. The endpoint reads
from the persistence component via a new repository method.

## Scope

- New `IWidgetRepository.ExportAsync(filter, cancellation)` port in the persistence
  component, returning an async enumerable of widgets matching the filter.
- New `GET /widgets/export` handler in the API component, streaming the port's
  output as CSV with RFC 4180 quoting.

## Out of scope

- Pagination. The endpoint streams the full result set.
- Authorization. The sample repo has no auth; a real deployment would add it in
  a separate feature.

## Related specs

- `product/api/openapi.yaml` (operation `GET /widgets/export`).
- `product/features/widget-export.md` (narrative).
- `product/persistence/ports.md` (port contract).

## Task routing

- `GET /widgets/export` → `acme/api-sample`
- `IWidgetRepository.ExportAsync` → `acme/persistence-sample`
```

### Capability identification (step 2)

From the spec set, the skill identifies two capabilities:

1. **Persistence port `ExportAsync`** (from `product/persistence/ports.md`).
2. **API operation `GET /widgets/export`** (from `product/api/openapi.yaml`).

### Implementation tasks (step 3)

`involved_repos` has two entries, so rule 2 applies: capabilities must declare their target repo. The `## Task routing` section declares both:

- `T01 implementation` → `acme/persistence-sample` (the port).
- `T02 implementation` → `acme/api-sample` (the handler).

### QA tasks (step 4)

The API endpoint is user-observable (new HTTP response), so it gets `qa_authoring` + `qa_execution`. The persistence port is internal (no externally observable behavior), so by the rule in step 4 it does not get its own QA tasks — the API endpoint's QA covers the port indirectly via behavior. The feature gets one `qa_curation`.

- `T03 qa_authoring` → `acme/api-sample`.
- `T04 qa_execution` → `acme/api-sample`.
- `T05 qa_curation` → `acme/api-sample` (dominant-suite repo: api-sample has 2 QA tasks vs 0 for persistence).

### Dependencies (step 5)

- T01 (persistence port) → no deps. Capability chain puts it before T02.
- T02 (API handler) → depends on T01. The handler consumes the port.
- T03 (qa_authoring) → no deps. Authored from the spec in parallel with implementation.
- T04 (qa_execution) → depends on [T01, T02, T03]. T03 is the matched `qa_authoring`. T02 (api-sample) and T01 (persistence-sample) are both the implementation tasks for the same capability the test covers — the API endpoint behavior directly invokes the persistence port, so the test must wait for both. The feature narrative does not describe a mock boundary on the test side, so T01 is included. (If the feature had stated "API tests mock the persistence port", T01 would be excluded per the cross-repo mock carve-out in step 5 rule 3.)
- T05 (qa_curation) → depends on [T04]. Runs after execution is green.

Cycle check: topological order is `T01 → T02 → T04 → T05`, with T03 in parallel. No cycles. Orphan check: all `TNN` in `depends_on` arrays match a task `id`. Clean.

### Autonomy (step 6)

Feature default is `auto`. Overrides:

- T04 `qa_execution` → **override to `review`** (rule 1: qa_execution is never auto).
- No sensitive-path keywords in this spec (no auth, PII, payments, etc.) — no supervised overrides.

T01, T02, T03, T05 have no `autonomy` field set (inherit `auto`).

### Written task graph

```yaml
---
correlation_id: FEAT-2026-0050
state: planning
involved_repos:
  - acme/api-sample
  - acme/persistence-sample
autonomy_default: auto
task_graph:
  - id: T01
    type: implementation
    depends_on: []
    assigned_repo: acme/persistence-sample
  - id: T02
    type: implementation
    depends_on: [T01]
    assigned_repo: acme/api-sample
  - id: T03
    type: qa_authoring
    depends_on: []
    assigned_repo: acme/api-sample
  - id: T04
    type: qa_execution
    depends_on: [T01, T02, T03]
    assigned_repo: acme/api-sample
    autonomy: review
  - id: T05
    type: qa_curation
    depends_on: [T04]
    assigned_repo: acme/api-sample
---
```

### Emitted event

```json
{
  "timestamp": "2026-04-22T18:30:00Z",
  "correlation_id": "FEAT-2026-0050",
  "event_type": "task_graph_drafted",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "task_count": 5,
    "involved_repos": ["acme/api-sample", "acme/persistence-sample"],
    "decomposition_pass": 1
  }
}
```

The event passes `scripts/validate-event.py` (exit 0) and is appended to `/events/FEAT-2026-0050.jsonl`.

## What this skill does not do

- It does **not** draft GitHub issue bodies. The task graph gives the structural skeleton; drafting is [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) (WU 2.4).
- It does **not** materialize the task graph as a human-readable review file. That is [`../plan-review/SKILL.md`](../plan-review/SKILL.md) (WU 2.3).
- It does **not** check Specfuse template coverage. That is [`../template-coverage/SKILL.md`](../template-coverage/SKILL.md) (WU 2.6).
- It does **not** flip `state: planning` to `state: plan_review`. That is the plan-review skill, after template-coverage has also succeeded.
- It does **not** re-verify target-repo state. Target-repo state is re-verified at issue-drafting time per [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) — the two skills have different verification windows and responsibilities.
- It does **not** guess. Every escalation point in the procedure above is `spec_level_blocker` — the specs or routing information is insufficient, and the human (or specs agent) must resolve it before decomposition continues.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §3 (vocabulary, task types), §6.2 (task state machine), §6.3 (transition ownership), §9.2 (template coverage at plan time — this skill's sibling).
- [`/shared/schemas/feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) — the machine contract this skill's output must validate against.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — the event contract for `task_graph_drafted`.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) — the four-step discipline every action here sits under.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — the re-read requirement before this skill runs.
- [`../../CLAUDE.md`](../../CLAUDE.md) — the PM role config that orchestrates this skill alongside its siblings.
- [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) — inherited contract the downstream issue-drafting skill must honor; referenced here for the split verification windows.
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 2.2 — Task decomposition skill" — the work unit that authored this skill.
