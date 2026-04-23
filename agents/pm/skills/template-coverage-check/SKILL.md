# PM agent — template coverage check skill (v1.1, stub protocol)

## Purpose

This skill is the PM agent's plan-time gate on Specfuse template availability. It answers one question before a feature advances into `plan_review`: does every task in the feature's task graph have the generator templates it needs, declared by its target component repo? When yes, the skill emits `template_coverage_checked` and returns; when no, it escalates `spec_level_blocker` at the feature level so the gap is surfaced to the human before any code is written.

This is a **stub protocol** — deliberately so. The Phase 2 acceptance criterion "template coverage gaps identified at planning time" (architecture §9.2) is satisfiable without a real generator query, using a convention file in each component repo. The real Phase 5 integration replaces the file with a live generator call but preserves the skill's shape, its escalation surface, and the `required_templates` contract on the task graph. See §"Deferred integration — Phase 5 brief" below. Decisions made here — token vocabulary, declaration-file path, task-level `required_templates`, skill invocation point — are chosen to survive the Phase 5 replacement; changing them later would be a breaking migration.

## Scope

In scope:

- Reading each involved component repo's `.specfuse/templates.yaml` declaration (or the configured equivalent) via a live fetch, at check time.
- Walking the feature's task graph, cross-referencing each task's `required_templates` against its `assigned_repo`'s `provided_templates`.
- Aggregating gaps into a single feature-level escalation on failure, or emitting one `template_coverage_checked` event on success.
- Treating absence of the declaration file, schema-invalid declarations, and missing tokens uniformly as gaps (never as silent coverage).

Out of scope (belongs elsewhere):

- Real generator-backed coverage checks. Deferred to Phase 5 per §"Deferred integration".
- Inferring `required_templates` from feature specs or task types. Phase 5 territory; v1 reads what the frontmatter carries.
- **DO NOT populate `required_templates` even if absent.** The task-decomposition skill deliberately does not set this field at v1. The human adds it during drafting or during `plan_review` re-ingest. If any task in the feature's task graph is missing `required_templates` at check time (field absent — not the same as an explicit empty array `[]`), the skill MUST escalate `spec_level_blocker` rather than infer the field; populating it from task-type or repo heuristics silently breaks the human-in-the-loop contract of `plan_review`. The template-coverage-check skill is a consumer of the field, not its author. See §"Pre-flight check — absent `required_templates`" for mechanical enforcement.
- Negotiating with the generator to add missing templates. A gap is escalated to the human, who decides whether to add a template, reshape the task, or abandon the feature.
- Re-running automatically on every plan-review re-ingest. The skill runs once in the `planning → plan_review` flow; if the human later adds `required_templates` during `plan_review`, the operator re-invokes the skill before the human approves the plan. This skill does not self-schedule.
- Writing to any component repo. The skill is strictly read-only against component repos.

## Inputs

Per invocation:

1. The feature-level correlation ID.
2. `/features/<feature_correlation_id>.md` — the feature registry file. The skill reads the frontmatter's `task_graph`, `involved_repos`, and `state` (confirms `state == "planning"` before running; re-runs during `plan_review` also permitted but the caller is responsible for invocation).
3. Each `assigned_repo`'s `.specfuse/templates.yaml`, fetched live from the repo's default branch. The skill uses the GitHub API (or a deployment-chosen equivalent — `curl` on `raw.githubusercontent.com`, a local clone, etc.); the contract below is "read a fresh copy per check", not "cache".
4. [`/shared/schemas/template-coverage.schema.json`](../../../../shared/schemas/template-coverage.schema.json) — the declaration-file schema, authored in this WU.
5. [`/shared/schemas/feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) — its task $defs gained an optional `required_templates: [string]` field in this WU. The skill reads the field. **Field absent** means the human has not yet populated this task — the pre-flight check (Step 2.5) escalates before coverage evaluation begins. **Explicit empty array `[]`** means the human explicitly set no templates needed — trivially covered, included in `task_count`.
6. [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — the event contract. `template_coverage_checked` was added to the enum in this WU; its per-type payload schema lives at [`/shared/schemas/events/template_coverage_checked.schema.json`](../../../../shared/schemas/events/template_coverage_checked.schema.json).
7. This skill and [`../../CLAUDE.md`](../../CLAUDE.md) — re-read per invocation per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

## Outputs

Per invocation, exactly one of:

- **Success** — one `template_coverage_checked` event appended to `/events/<feature_correlation_id>.jsonl`, validated through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) (top-level + per-type payload schema) with exit `0`.
- **Escalation** — one file under `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md` per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md), one `human_escalation` event appended to the event log with feature-level correlation ID, reason `spec_level_blocker`, and a payload listing every gap detected.

No writes to feature frontmatter (the skill reads, never edits). No writes to component repos. No state transition on the feature.

## Trigger — external invocation

Consistent with the Phase 2 pattern, the skill is a **function**, not a daemon. The invoker runs it once in the `planning → plan_review` flow, typically between task-decomposition completion and plan-review Phase A emission:

1. Task-decomposition (WU 2.2) writes `task_graph` to feature frontmatter, emits `task_graph_drafted`, leaves state in `planning`.
2. [If needed — human or an upstream drafting step populates `required_templates` on each task that requires generator output.]
3. **Template-coverage-check** (this skill) runs. On success, proceeds to step 4. On escalation, the feature halts; the human decides how to proceed.
4. Plan-review Phase A (WU 2.3) emits the plan file, flips state to `plan_review`, emits `plan_ready`.

The invoker (polling loop, CLI, or explicit orchestration script) is responsible for gating step 4 on step 3's success. This skill does not flip any state or chain to plan-review automatically.

If `required_templates` are added by the human during `plan_review` re-ingest (Phase B of plan-review), the operator may re-invoke this skill before the human approves the plan; it is idempotent over repeated invocations on the same feature state.

## The declaration-file convention

### Path

Each component repo carries `.specfuse/templates.yaml` at its root. The path is **fixed by convention** — the skill does not accept alternative paths at v1. The choice of a separate file (not an additive section of `.specfuse/verification.yml`) is deliberate:

- `.specfuse/verification.yml` is read by the **frozen** component agent verification skill ([`/agents/component/skills/verification/SKILL.md`](../../../../agents/component/skills/verification/SKILL.md) v1.1). Adding a `provided_templates` section there would couple two orthogonal concerns and require a tolerant-parse accommodation that the frozen skill does not currently guarantee.
- Separating concerns keeps each file single-purpose: `verification.yml` = how to test the repo; `templates.yaml` = which generator templates the repo provides.
- Phase 5's real-generator integration can retire `templates.yaml` without touching `verification.yml`.

### Shape

The declaration file validates against [`/shared/schemas/template-coverage.schema.json`](../../../../shared/schemas/template-coverage.schema.json). Minimal v1 form:

```yaml
schema_version: 1
provided_templates:
  - api-controller
  - api-request-validator
  - persistence-port
  - persistence-adapter
  - test-plan
  - test-runner
```

- `schema_version: 1` — pins the declaration contract. Bumped on breaking changes; this skill reads `schema_version == 1` only and escalates otherwise.
- `provided_templates` — a flat list of tokens. Kebab-case strings (`^[a-z0-9][a-z0-9-]*$`). Each token names a generator template category; the vocabulary is **free-form at v1** (no central registry) and will be surveyed for consistency during the Phase 2 walkthrough (WU 2.7). A token absent from a repo's declaration means the repo does not support that template category.

### Token vocabulary

At v1, tokens are free-form kebab-case. No central registry. Each repo and each feature uses whatever tokens communicate. The skill's cross-reference is **exact-string match**: `required_templates: [api-controller]` matches `provided_templates: [api-controller, ...]`, but not `provided_templates: [api_controller]` or `[ApiController]` or `[api-controllers]`.

Two consequences:

- **A typo is a gap.** Spelling `api-contoller` on one side and `api-controller` on the other produces an escalation. This is intentional — the exact-match discipline is the v1 safety against silent drift; Phase 5's real generator query will validate tokens against an authoritative list.
- **The walkthrough (WU 2.7) is the token-audit pass.** If the two features exercised there drift — one uses `controller`, the other `api-controller` — the retrospective will capture the divergence and the Phase 5 WU will inherit a concrete token-vocabulary brief. The v1 skill does nothing to prevent divergence proactively.

## The coverage check procedure

Single pass per invocation.

### Step 1 — State intent

Per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1: "I will check template coverage for `<feature_correlation_id>`."

### Step 2 — Read the feature's task graph

Read `/features/<feature_correlation_id>.md`. Parse the frontmatter. Confirm:

- `correlation_id` matches.
- `task_graph` is non-empty (decomposition has run).
- `involved_repos` is non-empty.

If the frontmatter fails to parse or any check fails, return an error to the invoker without emitting. This is an upstream bug, not a coverage gap — no escalation, no event.

### Step 2.5 — Pre-flight check: `required_templates` field presence

Before enumerating the coverage demand, walk every task in the task graph and check whether the `required_templates` field is **present** — regardless of its value.

**Critical semantic distinction:**

- **Field absent** (key does not exist in the task object at all): the human has never populated this field. This is a contract violation — it means the human has not completed their required input for this task before coverage-check was invoked. **Escalate immediately.**
- **Explicit empty array `[]`** (key present, value is an empty list): the human populated the field and declared that this task needs no generator templates. This is valid and expected — `qa_execution` and `qa_curation` tasks conventionally carry `required_templates: []` because execution and curation do not generate code via template. **Do not escalate for this.**

```yaml
# Field absent — escalate (human has not populated)
- id: T03
  type: implementation
  assigned_repo: owner/repo-a
  # required_templates key is missing entirely

# Explicit empty array — do NOT escalate (human deliberately set to empty)
- id: T05
  type: qa_execution
  assigned_repo: owner/repo-a
  required_templates: []
```

**Procedure:**

1. Collect the set of tasks where the `required_templates` key is absent from the task object.
2. If that set is **non-empty**: the skill immediately escalates `spec_level_blocker`. Do NOT proceed to Step 3. Do NOT emit `template_coverage_checked`.
   - Compose the escalation file at `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md` per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md). The "Agent state" section names every task with a missing `required_templates` field as a bulleted list: `- T03 (implementation on owner/repo-a): required_templates field absent — human must populate before coverage check`. The "Decision requested" section asks the human to populate `required_templates` on each named task — either with a list of needed tokens, or with an explicit `[]` if the task genuinely needs no generator output — and then re-invoke the coverage check.
   - Construct and append the `human_escalation` event per §"Escalation on gap" below.
   - Return escalation to the invoker. The invoker does not proceed with plan-review Phase A.
3. If that set is **empty**: all tasks have the field present (possibly as `[]`). Proceed to Step 3.

This pre-flight check is **mechanical enforcement** of the imperative stated in §"Out of scope". Both are present by design: the imperative is voice/intent guidance to the skill reader against a future session's helpfulness bias; the pre-flight check is the runtime gate that stops the skill even if the reader missed the Out-of-scope clause.

### Step 3 — Enumerate coverage demand

Build the list of `(task_id, assigned_repo, required_tokens)` tuples from the task graph. Skip tasks whose `required_templates` is empty (`[]`) — they are trivially covered (the field is present but the human declared no generator templates needed). The remaining set is the **demand**.

If the demand is empty (no task requires any template), the feature trivially satisfies coverage. Skip to step 6 with `gaps = []`.

### Step 4 — Fetch the declaration for every repo in demand

For each unique `assigned_repo` in the demand, fetch `<assigned_repo>/.specfuse/templates.yaml` from the repo's default branch. Recommended command:

```sh
gh api repos/<owner>/<repo>/contents/.specfuse/templates.yaml?ref=main \
  --jq '.content' | base64 --decode
```

Or equivalent (`curl` on `https://raw.githubusercontent.com/<owner>/<repo>/main/.specfuse/templates.yaml`, or filesystem read if a local clone is authoritative in the deployment).

Four failure modes, each a gap:

- **File not found** (HTTP 404 from `gh api`, or missing path on filesystem) → record a gap with reason `declaration_missing`.
- **Network / transport error** (transient fetch failure) → retry once; if still failing, treat as inconclusive and escalate with `spinning_detected` per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md). This is not a coverage gap — it is a skill availability failure.
- **YAML parse failure** → record a gap with reason `declaration_invalid_yaml` and the parse error message.
- **Schema validation failure** against [`/shared/schemas/template-coverage.schema.json`](../../../../shared/schemas/template-coverage.schema.json) → record a gap with reason `declaration_schema_invalid` and the validator error path.

A declaration fetched and validated cleanly is cached for the duration of this invocation only; the next invocation re-fetches.

### Step 5 — Cross-reference per task

For each `(task_id, assigned_repo, required_tokens)` in the demand:

- If the `assigned_repo`'s declaration was a fetch/parse/schema gap (step 4), the task inherits the gap — no per-token check needed. The gap's reason is `declaration_*` from step 4.
- Otherwise, for each `token` in `required_tokens`:
  - If `token ∈ provided_templates`, the requirement is satisfied.
  - If `token ∉ provided_templates`, record a gap `{task_id, assigned_repo, missing_token: token, reason: "token_missing"}`.

The walk is exhaustive — every task in the demand is checked against every `required_token`, and every gap is collected. No early-exit: a feature with three gaps gets all three reported in one escalation, not the first one discovered.

### Step 6 — Decide: emit or escalate

**If `gaps` is empty** (success path):

1. Construct the `template_coverage_checked` event:

   ```json
   {
     "timestamp": "<ISO-8601 now>",
     "correlation_id": "<feature_correlation_id>",
     "event_type": "template_coverage_checked",
     "source": "pm",
     "source_version": "<from scripts/read-agent-version.sh pm>",
     "payload": {
       "involved_repos": ["<owner>/<repo>", "..."],
       "task_count": <n>
     }
   }
   ```

2. Pipe through `scripts/validate-event.py`; require exit `0` (top-level + per-type payload schema both validated).
3. Append to `/events/<feature_correlation_id>.jsonl`. Re-read the appended line.
4. Return success to the invoker.

**If `gaps` is non-empty** (escalation path):

1. Compose the escalation file at `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md`, using [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md). Reason: `spec_level_blocker`. Correlation ID: **feature-level** (`FEAT-YYYY-NNNN`). The "Agent state" section enumerates every gap as a bulleted list: `- T02 on clabonte/persistence-sample: missing token 'persistence-adapter' (declaration does not list it)`. The "Decision requested" section names the human's concrete options: add the missing template to the generator and update the declaration; reshape the task so it does not require the missing template; abandon the feature.
2. Construct the `human_escalation` event:

   ```json
   {
     "timestamp": "<ISO-8601 now>",
     "correlation_id": "<feature_correlation_id>",
     "event_type": "human_escalation",
     "source": "pm",
     "source_version": "<from scripts/read-agent-version.sh pm>",
     "payload": {
       "reason": "spec_level_blocker",
       "inbox_file": "inbox/human-escalation/<feature_correlation_id>-template-coverage.md",
       "summary": "<N> template coverage gap(s) on <feature_correlation_id> at plan time",
       "gaps": [
         {"task_id": "T02", "assigned_repo": "clabonte/persistence-sample", "missing_token": "persistence-adapter", "reason": "token_missing"},
         {"...": "..."}
       ]
     }
   }
   ```

3. Pipe through `scripts/validate-event.py`; require exit `0`.
4. Append to `/events/<feature_correlation_id>.jsonl`. Re-read.
5. Do **not** emit `template_coverage_checked`. The absence of that event on a feature that reached the coverage step is the gap signal — consumers of the event log reading "feature moved to plan_review" without a preceding `template_coverage_checked` know the check escalated.
6. Return escalation to the invoker. The invoker does not proceed with plan-review Phase A.

## Missing-declaration handling

Absence of `.specfuse/templates.yaml` on any `assigned_repo` in the demand is a **gap**, not a trivial pass. Per the WU 2.6 "Do not touch" clause: "Do not silently treat absence of a declaration file as coverage — absence is a `spec_level_blocker` so the human either adds the declaration or abandons the task."

The escalation's payload lists the missing-declaration case with reason `declaration_missing`, so the human sees:

- Which repo is missing a declaration.
- Which task(s) in the feature required generator output on that repo.

This ensures every component repo drawn into a feature has either an explicit declaration of what templates it supports, or an explicit human decision to proceed without one (which would be recorded as feature-level override, out of scope of this skill).

### Why strict-by-default is safer than tolerant-by-default

A tolerant default ("no declaration means no coverage needed") would let a feature advance into `plan_review` on a repo that genuinely lacks generator support, discovering the gap only when a component agent opens a task and can't find boilerplate. That is exactly the mid-implementation replanning that architecture §9.2 exists to prevent. Strict-by-default forces the coverage conversation to happen at plan time, with the human in the loop.

## Escalation on gap — file and event

### Escalation file

Template: [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md). Path: `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md`. Correlation ID in the file: **feature-level**, not task-level — the graph itself is what's malformed relative to generator coverage, so the feature re-plans, not just one task.

The "Agent state" section is concrete: every gap is a bullet with repo, task, token (or declaration error reason), so the human can decide each independently. The "Decision requested" section enumerates options per the §Procedure step 6 escalation path above — add template, reshape task, or abandon. If the feature has multiple gaps across multiple repos, the human may respond to each bullet differently (add some templates, abandon others).

### Event

`human_escalation` with feature-level correlation ID, reason `spec_level_blocker`, and payload that duplicates the gap list inline (so a consumer of the event log can reason about gap structure without pulling the inbox file). No dedicated `template_coverage_gap` event; the `human_escalation` event is the signal. This keeps the enum concise — adding one event per failure mode of every skill would inflate the enum without buying separation that `reason` and payload structure already provide.

### Stopping the flow

On escalation, the skill does not proceed to emit `template_coverage_checked`. The feature stays in `planning`. The invoker does not flip to `plan_review`. The human sees the inbox file, takes one of the documented actions, and the operator re-runs the coverage check when the gap(s) are closed.

## Event payload — `template_coverage_checked`

Per-type schema at [`/shared/schemas/events/template_coverage_checked.schema.json`](../../../../shared/schemas/events/template_coverage_checked.schema.json), validated by `scripts/validate-event.py` after the top-level envelope check (per the discipline established in WU 2.5):

```json
{
  "involved_repos": ["<owner>/<repo>", "..."],
  "task_count": 3
}
```

- `involved_repos` — duplicates the feature frontmatter's `involved_repos` at check time. Redundant with the feature file but self-contained for event-log readers.
- `task_count` — total task count in the graph at check time, including trivially-satisfied tasks (those with empty `required_templates`). A task that contributed nothing to the demand is still counted; the field is a "how big was the feature when coverage passed" marker, not a "how many tasks required templates" counter.

The skill does **not** include `required_templates` or `provided_templates` in the event payload. Those are in the feature frontmatter and in each repo's declaration file respectively; duplicating them into the event log would mix surfaces. The event asserts "coverage held at `<timestamp>` for this shape"; the shape is reconstructible from the two canonical sources.

## Verification

Universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 apply on every emission, plus the skill-local checks below.

### Before returning from a success invocation

- Every task in the task graph was walked (whether it contributed to the demand or not).
- Every `assigned_repo` in the demand had its declaration fetched, parsed, and schema-validated in this invocation (no cross-invocation caching).
- Zero gaps detected.
- `template_coverage_checked` event passed `scripts/validate-event.py` (top-level + per-type payload schemas) with exit `0`, appended to the event log, re-read.
- `source_version` on the event was produced by `scripts/read-agent-version.sh pm` at emission time.
- Feature state is unchanged (still `planning`, or whatever it was at invocation).
- No write to any component repo, `/product/`, `/overrides/`, or component-repo code paths.
- No path written is in [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md).

### Before returning from an escalation invocation (pre-flight — absent `required_templates`)

- At least one task was found with the `required_templates` field entirely absent (not `[]` — absent).
- Escalation file written at `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md` naming every task with the absent field.
- `human_escalation` event passed validation (exit 0), was appended, and was re-read.
- No `template_coverage_checked` was emitted. Skill exited before Step 3.
- Feature state is unchanged.

### Before returning from an escalation invocation (coverage gap — Step 6 path)

- At least one gap was collected during the coverage walk (Steps 3–5).
- Escalation file written at `/inbox/human-escalation/<feature_correlation_id>-template-coverage.md` with every gap enumerated and the human's options spelled out.
- `human_escalation` event passed validation (exit 0), was appended, and was re-read.
- No `template_coverage_checked` was emitted.
- Feature state is unchanged (still `planning`).

### Before returning from a transient-failure escalation (`spinning_detected`)

- Retry-once policy exhausted on at least one repo's declaration fetch.
- Escalation file written with reason `spinning_detected` and specifics of the transport failure.
- `human_escalation` event appended.
- No coverage decision was rendered (the check was inconclusive, not failed).

Failure handling per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable retry; three consecutive failed cycles → `spinning_detected`; fundamentally blocked → `spec_level_blocker` per §"Escalation on gap".

## Worked example 1 — coverage passes

Fictional feature `FEAT-2026-0053 — Widget export history` on two repos. The task graph (after decomposition):

```yaml
task_graph:
  - id: T01
    type: implementation
    depends_on: []
    assigned_repo: clabonte/persistence-sample
    required_templates: [persistence-port, persistence-adapter]
  - id: T02
    type: implementation
    depends_on: [T01]
    assigned_repo: clabonte/api-sample
    required_templates: [api-controller, api-request-validator]
  - id: T03
    type: qa_authoring
    depends_on: []
    assigned_repo: clabonte/api-sample
    required_templates: [test-plan]
```

### Declarations on each repo

`clabonte/persistence-sample/.specfuse/templates.yaml`:

```yaml
schema_version: 1
provided_templates:
  - persistence-port
  - persistence-adapter
  - migration
```

`clabonte/api-sample/.specfuse/templates.yaml`:

```yaml
schema_version: 1
provided_templates:
  - api-controller
  - api-request-validator
  - api-response-serializer
  - test-plan
  - test-runner
```

### Walk

Step 1 — intent: "I will check template coverage for FEAT-2026-0053."

Step 2 — read frontmatter. `task_graph` is non-empty (3 tasks), `involved_repos` is `[clabonte/persistence-sample, clabonte/api-sample]`. Proceed.

Step 2.5 — pre-flight check: every task has `required_templates` present. T01 → `[persistence-port, persistence-adapter]`, T02 → `[api-controller, api-request-validator]`, T03 → `[test-plan]`. No task is missing the field. Proceed.

Step 3 — demand:

| Task | Repo | Required |
|---|---|---|
| T01 | `clabonte/persistence-sample` | `[persistence-port, persistence-adapter]` |
| T02 | `clabonte/api-sample` | `[api-controller, api-request-validator]` |
| T03 | `clabonte/api-sample` | `[test-plan]` |

Step 4 — fetch declarations:

```sh
gh api repos/clabonte/persistence-sample/contents/.specfuse/templates.yaml?ref=main \
  --jq '.content' | base64 --decode
# → schema_version: 1 ; provided_templates: [persistence-port, persistence-adapter, migration]

gh api repos/clabonte/api-sample/contents/.specfuse/templates.yaml?ref=main \
  --jq '.content' | base64 --decode
# → schema_version: 1 ; provided_templates: [api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]
```

Both parse clean, both validate against `template-coverage.schema.json`. No fetch or schema gap.

Step 5 — cross-reference:

| Task | Token | Provided? |
|---|---|---|
| T01 | `persistence-port` | ✓ |
| T01 | `persistence-adapter` | ✓ |
| T02 | `api-controller` | ✓ |
| T02 | `api-request-validator` | ✓ |
| T03 | `test-plan` | ✓ |

Zero gaps.

Step 6 — success:

```json
{
  "timestamp": "2026-04-22T19:42:10Z",
  "correlation_id": "FEAT-2026-0053",
  "event_type": "template_coverage_checked",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "involved_repos": ["clabonte/api-sample", "clabonte/persistence-sample"],
    "task_count": 3
  }
}
```

Validates through `scripts/validate-event.py` (top-level + per-type) with exit `0`. Appended to `/events/FEAT-2026-0053.jsonl`. Re-read confirms.

The invoker now proceeds to plan-review Phase A; feature flips `planning → plan_review`.

## Worked example 2 — coverage fails with one gap

Same feature, same task graph, but `clabonte/persistence-sample/.specfuse/templates.yaml` has drifted:

```yaml
schema_version: 1
provided_templates:
  - persistence-port
  - migration
```

(`persistence-adapter` dropped — perhaps removed when a different feature replaced it with a manual implementation.)

### Walk (deltas from example 1)

Steps 1–2.5 identical (pre-flight check passes — all tasks have `required_templates` present).

Steps 2.5–3 identical.

Step 4 — fetch declarations. Both fetch cleanly, both schema-validate.

Step 5 — cross-reference:

| Task | Token | Provided? |
|---|---|---|
| T01 | `persistence-port` | ✓ |
| T01 | `persistence-adapter` | ✗ (missing) |
| T02 | `api-controller` | ✓ |
| T02 | `api-request-validator` | ✓ |
| T03 | `test-plan` | ✓ |

One gap:

```
{"task_id": "T01", "assigned_repo": "clabonte/persistence-sample", "missing_token": "persistence-adapter", "reason": "token_missing"}
```

Step 6 — escalate.

Inbox file `/inbox/human-escalation/FEAT-2026-0053-template-coverage.md` (abbreviated):

```markdown
# Human escalation — FEAT-2026-0053

## Correlation ID

FEAT-2026-0053

## Reason

spec_level_blocker

## Agent state

**Role:** pm (template-coverage-check skill v1.0)

**What I was doing:** template coverage check on FEAT-2026-0053 at plan time.

**What I found:** 1 coverage gap.

- **T01** on `clabonte/persistence-sample`: missing token `persistence-adapter`. The repo's `.specfuse/templates.yaml` lists `[persistence-port, migration]`; the task's `required_templates` includes `persistence-adapter` which is not declared.

**Event log:** `/events/FEAT-2026-0053.jsonl`
**Feature registry:** `/features/FEAT-2026-0053.md`

## Decision requested

One gap. Options:

1. **Add the template.** Extend the Specfuse generator to emit a `persistence-adapter` and update `clabonte/persistence-sample/.specfuse/templates.yaml` to declare it. Re-run coverage check.
2. **Reshape T01.** Modify the task's `required_templates` to drop `persistence-adapter` if the implementation can proceed without generator output for that surface (e.g., hand-written adapter). Re-run coverage check.
3. **Abandon the feature.** Flip `FEAT-2026-0053` to `abandoned` if the gap is not worth closing.

Which option, and (for option 1 or 2) who is responsible for the follow-up?
```

Event:

```json
{
  "timestamp": "2026-04-22T19:42:10Z",
  "correlation_id": "FEAT-2026-0053",
  "event_type": "human_escalation",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "reason": "spec_level_blocker",
    "inbox_file": "inbox/human-escalation/FEAT-2026-0053-template-coverage.md",
    "summary": "1 template coverage gap on FEAT-2026-0053 at plan time",
    "gaps": [
      {
        "task_id": "T01",
        "assigned_repo": "clabonte/persistence-sample",
        "missing_token": "persistence-adapter",
        "reason": "token_missing"
      }
    ]
  }
}
```

Validates through `scripts/validate-event.py`. Appended. Re-read.

No `template_coverage_checked` event is emitted. The feature stays in `planning`. The invoker does not call plan-review Phase A. The human will read the inbox file, decide, and the operator re-invokes the skill once the gap is addressed.

## Deferred integration — Phase 5 brief

Phase 5 replaces the `.specfuse/templates.yaml` declaration file with a live query against the Specfuse generator. The skill's shape, its escalation surface, and the `required_templates` contract on the task graph persist across the migration.

### What Phase 5 changes

- **Template authority moves from declaration files to the generator itself.** The generator exposes an interface (RPC / CLI subcommand / library function — TBD at Phase 5 based on the generator's language and deployment shape) that returns the authoritative list of templates it supports, keyed by the target repo.
- **The declaration file may or may not persist.** Two candidate paths:
  - **Retire `.specfuse/templates.yaml`.** Phase 5 removes the convention; every coverage check goes through the generator. Simpler. Requires the generator to be reachable from wherever the PM agent runs (deployment constraint).
  - **Keep `.specfuse/templates.yaml` as a cached fallback.** Phase 5 prefers the live generator query, falls back to the declaration file if the generator is unreachable, and escalates if the two disagree. More resilient; doubles the maintenance burden.
  - The decision lives with the Phase 5 WU; the architectural commitment here is that Phase 5 inherits the option and picks explicitly.

### What Phase 5 does not change

- **The `required_templates` field on the task graph.** It remains the contract — "these tokens are what this task needs from the generator." Its schema is already frozen in `feature-frontmatter.schema.json` after this WU.
- **The escalation surface.** Gap detection remains a `spec_level_blocker` escalation at feature level, with the same inbox file shape. Phase 5's generator-backed check still routes gaps through `human_escalation`, keeping the human-facing interface unchanged.
- **The invocation point.** Still once in the `planning → plan_review` flow. Phase 5 does not change when the skill runs; it changes only how the skill resolves provided templates.
- **The success event.** `template_coverage_checked` payload shape remains `{involved_repos, task_count}`. Phase 5 consumers of the event log see no difference.

### Token vocabulary in Phase 5

The v1 vocabulary is free-form kebab-case — any string matching `^[a-z0-9][a-z0-9-]*$` is a valid token. Two paths are available to Phase 5:

- **Formalize a central token registry.** Introduce `shared/schemas/template-tokens.yaml` (or equivalent), enumerate every token the generator supports, and validate `required_templates` and `provided_templates` entries against it. Prevents typos and vocabulary drift; adds one file to maintain per generator release.
- **Leave tokens free-form.** If the Phase 2 walkthrough (WU 2.7) and the phase-3/4 experience show no significant drift, Phase 5 inherits the loose convention without formalizing it. The generator's live query is the authority; a mismatch is just a gap.

The Phase 5 WU author inherits this decision and chooses based on walkthrough evidence. The current skill makes no commitment either way.

### Summary for the Phase 5 WU author

The Phase 5 WU for replacing the template-coverage stub inherits:

- This file (the skill structure and verification discipline — preserved as-is, one behavior section replaced).
- `shared/schemas/template-coverage.schema.json` (retire, keep as cached fallback, or evolve — Phase 5 decides).
- `shared/schemas/events/template_coverage_checked.schema.json` (payload unchanged — the event remains the success signal).
- The `required_templates` field on `feature-frontmatter.schema.json`'s task $defs (preserved; still the contract).
- The invocation point in the `planning → plan_review` flow (unchanged).
- A walkthrough-informed decision on central token registry vs. free-form (Phase 2 retrospective WU 2.8 is the input).

No blank-sheet re-design is expected. The Phase 5 WU's budget is changing the **resolution mechanism** (file → live query), not the surrounding design.

## What this skill does not do

- It does **not** populate `required_templates` on the task graph — and it is **prohibited from doing so even if the field is absent**. The task-decomposition skill deliberately does not set this field; the human owns it during drafting or `plan_review`. If a task is missing the field at check time, the skill escalates `spec_level_blocker` (Step 2.5) rather than inferring the field.
- It does **not** query the generator. A stub at v1, a live call at Phase 5; today, all template authority flows through `.specfuse/templates.yaml`.
- It does **not** modify feature frontmatter, component repos, `/product/`, `/overrides/`, or any code path.
- It does **not** flip feature state. The invoker chains to plan-review Phase A on success; the skill itself does not transition.
- It does **not** run automatically on every plan-review re-ingest. The operator invokes the skill; v1 is a one-shot function per invocation.
- It does **not** attempt to reconcile a token typo. Exact-string match, no fuzzy matching, no suggestions. A typo is a gap; the human corrects it and re-runs.
- It does **not** silently treat a missing declaration as coverage. Explicit gap per [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 2.6" "Do not touch" clause.
- It does **not** emit a separate `template_coverage_gap` event. Gaps ride on `human_escalation`; adding a per-failure event type inflates the enum without buying separation.
- It does **not** cache declarations across invocations. Each invocation re-fetches — the skill is stateless between runs.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §9.2 — template coverage at plan time; the architectural commitment this skill implements.
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 2.6 — Template-coverage check skill (stub protocol)" — the work unit that authored this skill.
- [`/shared/schemas/template-coverage.schema.json`](../../../../shared/schemas/template-coverage.schema.json) — declaration-file schema, authored in this WU.
- [`/shared/schemas/examples/template-coverage.json`](../../../../shared/schemas/examples/template-coverage.json) — worked-example declaration, validated against the schema above.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — `template_coverage_checked` added to the enum in this WU.
- [`/shared/schemas/events/template_coverage_checked.schema.json`](../../../../shared/schemas/events/template_coverage_checked.schema.json) — per-type payload schema for the success event; second precedent under the Phase 2 per-type schema convention (first being `task_started.schema.json` from WU 2.5).
- [`/shared/schemas/feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) — task $defs gained optional `required_templates` in this WU.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 — universal discipline; per-type payload validation applies to `template_coverage_checked` automatically.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally per invocation.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation surface gaps route through.
- [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md) — the escalation file template.
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — applies per-type payload schemas additively per WU 2.5.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
- [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) — upstream skill that writes the task graph this skill consumes.
- [`../plan-review/SKILL.md`](../plan-review/SKILL.md) — downstream skill invoked by the same orchestrator flow, gated on this skill's success.
- [`../issue-drafting/SKILL.md`](../issue-drafting/SKILL.md) — further downstream; runs after plan approval and feature transition to `generating`, independent of this skill.
- [`../dependency-recomputation/SKILL.md`](../dependency-recomputation/SKILL.md) — sibling skill that runs on every `task_completed` during `in_progress`; unrelated to coverage but shares the per-type payload schema convention.
- [`/agents/component/skills/verification/SKILL.md`](../../../../agents/component/skills/verification/SKILL.md) — frozen. This skill deliberately does not touch or depend on it; `.specfuse/templates.yaml` is the separate file chosen to avoid coupling.
- [`../../CLAUDE.md`](../../CLAUDE.md) — PM role config; the "Role-specific verification" clause and "Entry transitions owned" clause both reference this skill as the place template coverage is gated before `planning → plan_review`.
