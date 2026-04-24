# QA agent — qa-authoring skill (v1.1)

## Purpose

This skill turns a validated feature specification into an executable test plan file at `/product/test-plans/FEAT-YYYY-NNNN.md` in the product specs repo. It is the first skill in the QA pipeline: every downstream QA skill (`qa-execution`, `qa-regression`, `qa-curation`) consumes the plan this one produces. The test plan's machine-readable shape is therefore a **hard internal contract** for Phase 3.

The skill does not run tests, does not file regression artifacts, and does not curate the regression suite. It authors the plan only; its siblings take it from there.

## Scope

In scope:

- Reading the feature registry and the product specs listed under `## Related specs` to understand what the feature delivers and which acceptance-criteria fragments need coverage.
- Enumerating the behaviors a test plan must cover — one test per behavior by default, honoring the feature-scope override on `qa_authoring` cardinality (WU 2.10).
- Minting stable, kebab-case `test_id`s that `qa-regression` and `qa-curation` downstream can key off.
- Writing the plan file to `/product/test-plans/FEAT-YYYY-NNNN.md` as YAML frontmatter (validated against the stub schema) plus optional prose.
- Validating the plan against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) before reporting.
- Emitting `test_plan_authored` with payload `{plan_path, test_count}` to the feature's event log.

Out of scope (each belongs to a later skill or phase):

- **Running the plan against the implementation** — [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md), WU 3.3.
- **Filing regressions when execution fails** — [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md), WU 3.4.
- **Curating the growing suite** — [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md), WU 3.5.
- **Richer, Arazzo-backed plan structures or generator-emitted skeletons** — Phase 4 and Phase 5 respectively, see §"Deferred integration" below.
- **Any write outside `/product/test-plans/` or the orchestration repo's event log.** Writing elsewhere in `/product/` belongs to the specs agent; writing to component-repo code paths belongs to the component agent.

## Inputs

The skill reads, in order:

1. The QA task issue (task type `qa_authoring`) assigned to it. The task-level correlation ID (`FEAT-YYYY-NNNN/TNN`) in the issue title carries the feature correlation ID.
2. The feature registry at `/features/<feature_correlation_id>.md` in the orchestration repo — its frontmatter (`correlation_id`, `state`, `involved_repos`) and its prose body, including the `## Scope` section (for the `qa_authoring` cardinality override).
3. The spec files listed under `## Related specs` in the feature registry — typically paths under the product specs repo's `/product/` tree (OpenAPI, AsyncAPI, Arazzo, feature narratives).
4. This skill's own file and [`../../CLAUDE.md`](../../CLAUDE.md) — reloaded per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

The skill does **not** read the component repos' source at authoring time. The plan is authored from the spec; whether the implementation matches the plan is `qa-execution`'s concern (WU 3.3).

## Outputs

- A test plan file at `/product/test-plans/<feature_correlation_id>.md` in the product specs repo. The file has YAML frontmatter conforming to [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json), optionally followed by a prose body explaining coverage choices.
- A `test_plan_authored` event appended to `/events/<feature_correlation_id>.jsonl` in the orchestration repo. Payload shape: `{plan_path, test_count}` per [`events/test_plan_authored.schema.json`](../../../../shared/schemas/events/test_plan_authored.schema.json).
- Standard QA-task-lifecycle events the skill is responsible for emitting on its own task: `task_started` on pickup and `task_completed` on successful completion (or `task_blocked` on escalation).

No component-repo writes. No `/product/` writes outside `/product/test-plans/`. No label or state writes on any task other than the `qa_authoring` task this instance owns.

## The authoring procedure

### Step 1 — State intent and pick up the task

State the intent (per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1): "I will author the test plan for `<feature_correlation_id>`."

Flip the `qa_authoring` task's label `state:ready → state:in-progress` (this is a role-owned transition per [`../../CLAUDE.md`](../../CLAUDE.md) §"Entry transitions owned"). Emit `task_started`.

### Step 2 — Read the feature context

Read the feature registry frontmatter and confirm:

- `state` is `in_progress` or `generating` — the PM agent has opened QA task issues and flipped the feature past `plan_review`. If the feature is still in `planning` or `plan_review`, the `qa_authoring` task should not have been opened; escalate `spec_level_blocker` with reason "qa_authoring picked up on feature in unexpected state: `<state>`".
- `involved_repos` is populated.

Read the prose body. The `## Description`, `## Scope`, `## Out of scope`, and `## Related specs` sections are load-bearing. The `## Scope` section specifically may include a **feature-scope override on `qa_authoring` cardinality** per WU 2.10 — a statement like "one authored test plan covering both behaviors" collapses the default per-behavior count.

Read every spec file listed under `## Related specs`.

### Step 3 — Enumerate behaviors to cover

A **behavior** is a discrete, spec-stated outcome the feature delivers. The spec is the source of truth; the skill does not invent behaviors from prose alone.

For each spec type, the behavior unit is:

- **OpenAPI** — one behavior per response status code of each operation that is part of the feature's stated scope. A 200-happy-path and a 400-validation case on the same operation are two behaviors.
- **AsyncAPI** — one behavior per operation (per channel direction) per success/failure outcome stated in the spec.
- **Arazzo workflow** — one behavior per workflow outcome. Intermediate steps are not separate behaviors at the plan level.
- **Feature narrative with explicit `### Behavior N` or acceptance-criteria headings** — one behavior per heading. If the feature uses numbered acceptance criteria (`AC-1`, `AC-2`, …), the numbering is inherited.
- **DB schema / migration fragments** — not directly a behavior unit. Behaviors emerge from the API or service layer that exposes the schema change; plan against that layer.
- **UI screen / component spec** — one behavior per user-visible outcome stated in the spec (e.g., "form submits successfully", "form rejects invalid input"). Sub-component rendering is not a behavior unless the spec names it.

If a spec type is not listed above, the skill escalates `spec_level_blocker` with reason "unhandled spec type for behavior enumeration: `<path>`". It does not invent behaviors.

### Step 4 — Apply the feature-scope `qa_authoring` cardinality override

**Read the feature's `## Scope` section before counting tests.** The WU 2.10 convention: the feature scope can explicitly collapse the default per-behavior count (e.g., "one authored test plan covering both behaviors"). The override is one-directional — the feature can only collapse, not expand.

- If `## Scope` names a `qa_authoring` cardinality lower than the default, honor it: produce the collapsed count by merging multiple behaviors under fewer `tests` entries. Each merged test's `covers` field cites all the behaviors it covers.
- If `## Scope` is silent on `qa_authoring`, apply the default: one test per behavior.
- If `## Scope` appears to constrain `qa_authoring` but the clause is ambiguous (e.g., the number is not stated), escalate `spec_level_blocker` with reason "ambiguous qa_authoring cardinality override in `## Scope`". **The skill does not guess.**

### Step 5 — Draft each test entry

#### Pre-step: discover the component's runtime port

Before drafting any `commands`, the skill discovers the runtime port of every component repo the plan exercises, by inspecting the component repo's standard declared sources in this order:

1. **.NET** — `<component_repo>/<project>/Properties/launchSettings.json`. Read the first profile (typically `http` or the project-name profile); take its `applicationUrl` (first entry if the value is a semicolon-separated list). Example: `"applicationUrl": "http://localhost:5083;https://localhost:7019"` → port `5083`.
2. **Node / Express / similar** — `package.json` `scripts.start` (parse for `-p <port>` / `PORT=<port>` / `--port <port>`), or `.env.example` `PORT=<port>`, or the service's README if it documents the port as a stable contract.
3. **Containerized (Dockerfile)** — `EXPOSE <port>` instruction.
4. **Containerized (docker-compose)** — `services.<service>.ports[0]` left-hand side.
5. **Other stacks** — a stack-equivalent declared source (Python Flask/FastAPI entry-point, Go `http.ListenAndServe` literal, Rust `tokio::net::TcpListener::bind` literal, etc.). The source must be a durable declaration in the repo, not a value inferred from a prior walkthrough or memory.

Silence on ports is a defect, not an assumption opportunity. If none of the above sources yields a discoverable port, the skill escalates `spec_level_blocker` with reason "unable to discover runtime port for `<component_repo>`". The skill does **not** default to `5000`, `8080`, or any other "common" port.

Once the port is discovered, the skill threads it into the plan through two complementary conventions (both apply unless the component's startup is genuinely more complex than a single backgrounded command, in which case (i) is omitted and (ii) carries the full procedure):

- **(i) Startup command in `commands[0]` of the first test.** The first test's `commands[]` array carries the service-startup command as its first element, backgrounded with `&`, so qa-execution's first test run starts the service. Example: `["dotnet run --project src/OrchestratorApiSample.Api/ --urls \"http://localhost:5083\" &", "curl -sS -o body.json -w '%{http_code}' http://localhost:5083/widgets"]`. Subsequent tests' `commands[]` do not repeat the startup (the service is assumed running by the time they execute).
- **(ii) Port and source file documented in `## Coverage notes`.** The plan's prose body always states the discovered port and the source file it was read from (e.g., "Runtime port: `5083`, sourced from `src/OrchestratorApiSample.Api/Properties/launchSettings.json`, profile `http`."). This documentation is mandatory regardless of whether (i) applies — it gives qa-execution a grep-able record of the port's provenance.

When (i) is not applicable (the component needs DB migrations, multi-process startup, seed data, or other setup a single backgrounded command cannot express), (ii) carries the full procedure as prose. A plan with neither (i) nor a complete (ii) is malformed; the skill re-drafts or escalates.

#### Drafting each test

For each behavior (or merged behavior group, per step 4), draft:

- **`test_id`** — a stable kebab-case identifier unique within this plan. Convention: `<domain>-<outcome>` (e.g., `widgets-export-default-page-size`, `widgets-export-page-size-over-limit-rejected`). The feature correlation ID is **not** prefixed into the `test_id` — the file's `feature_correlation_id` already scopes it. Stability is load-bearing: `qa-regression` keys regression artifacts on `(implementation_task_correlation_id, test_id)`, so a later rename would orphan open regressions. If a subsequent re-authoring pass discovers a badly-named `test_id`, handle the rename as a curation PR (WU 3.5), not as an in-place edit on this plan.
- **`covers`** — a direct citation of the acceptance-criteria fragment this test validates. Include the AC identifier if the spec uses one (e.g., `"AC-1: GET /widgets/export returns the first 50 widgets when no page_size parameter is supplied."`). A `covers` field that only paraphrases without identifying the source fragment is too weak — a human reading the plan later must be able to locate the covered behavior in the source spec without guessing.
- **`commands`** — the executable step list. At v1 (Phase 3 stub), each command is a free-form shell string the `qa-execution` skill will run. Keep commands self-contained: no hidden setup, no undeclared environment assumptions beyond what the spec or the feature narrative establishes. If a command requires environment setup the spec does not declare, that is a spec gap — escalate `spec_level_blocker` rather than bake the assumption into the plan.
- **`expected`** — a prose success predicate describing what `qa-execution` will confirm. At v1, this is a textual statement (e.g., "HTTP status is 200 and body parses as a JSON array of exactly 50 widget objects"). Phase 4 structures this as a machine-evaluable predicate; for now, the prose must be concrete enough that a human or the `qa-execution` skill can decide pass/fail without re-interpreting the spec.

### Step 6 — Validate the draft plan in memory

Before writing, the skill validates the draft plan object against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) using `ajv`, Python `jsonschema`, or equivalent. `additionalProperties: false` is on; unknown fields fail.

Beyond the schema round-trip:

- **Unique `test_id` check.** Collect every `test_id` in the `tests` array and confirm the set's size equals the array length. JSON Schema cannot express this constraint directly on a nested field; the skill enforces it. A duplicate `test_id` is a malformed plan — correct the draft and re-validate, or escalate `spec_level_blocker` if the ambiguity is in the spec (two behaviors the spec cannot distinguish).
- **Coverage check.** Every acceptance-criteria fragment the feature spec names must be cited in at least one test's `covers` field. An AC fragment with no covering test means the plan is incomplete — return to step 5 and add the missing test. Exception: the feature-scope override from step 4 may have merged multiple AC fragments under one test; the merged test's `covers` field must name all merged fragments.

If any check fails and cannot be corrected by re-drafting, escalate `spec_level_blocker`. The skill **does not** write a partially-validated plan.

### Step 7 — Write the plan file and emit `test_plan_authored`

After all checks pass:

1. Write the plan file to `/product/test-plans/<feature_correlation_id>.md` in the product specs repo. The file has two parts:
   - **YAML frontmatter** — the machine-readable plan object, delimited by `---` lines.
   - **Prose body (optional)** — narrative explaining coverage choices, merged behaviors, or notable gaps. Not schema-governed; human-readable only.
   If a plan file already exists for this feature (re-authoring after a spec change), overwrite it. Do not merge — the prior plan is superseded by this authoring pass.
2. Re-read the written file, re-parse the frontmatter, and re-validate against the schema per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3. The re-read is the authoritative confirmation — the in-memory draft is not sufficient.
3. Construct the `test_plan_authored` event:
   - `timestamp`: ISO-8601 at emission time.
   - `correlation_id`: the feature-level ID (no task suffix).
   - `event_type`: `test_plan_authored`.
   - `source`: `qa`.
   - `source_version`: produced by [`scripts/read-agent-version.sh qa`](../../../../scripts/read-agent-version.sh) at emission time — never eye-cached from [`version.md`](../../version.md).
   - `payload`: `{"plan_path": "/product/test-plans/<feature_correlation_id>.md", "test_count": <length of tests array>}`.
4. Pipe the event through [`scripts/validate-event.py`](../../../../scripts/validate-event.py). Require exit `0` before appending.
5. Append the event to `/events/<feature_correlation_id>.jsonl` in the orchestration repo.
6. Re-read the appended line and confirm it matches what was constructed.
7. Emit `task_completed` on the `qa_authoring` task and flip the task's label to `state:in-review` per [`../../CLAUDE.md`](../../CLAUDE.md) §"Entry transitions owned". The PR containing the plan file (in the product specs repo) is the deliverable under review — see §"Delivery convention" below for the full branch / commit / PR mechanics.

## Delivery convention

The authoring pass's deliverable is a **PR on the product specs repo** containing the written plan file. The convention mirrors [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) §"Output" on the same specs repo, so an operator or merge watcher sees consistent shape across QA skills. An agent running this skill from a cold context must be able to produce the PR from the discipline below without external prompting.

### Branch

Create the branch `qa-authoring/<task_correlation_id>` in the **product specs repo**, branching from `main`'s current HEAD. The task-correlation-ID separator `/` is replaced with `-` in the branch name. Example: a `qa_authoring` task with correlation ID `FEAT-2026-0006/T02` produces branch `qa-authoring/FEAT-2026-0006-T02`.

Branch-name format is grep-able: `^qa-authoring/FEAT-\d{4}-\d{4}-T\d{2}$`. A malformed branch name prevents the merge watcher from matching the PR back to the `qa_authoring` task issue; the skill does not invent alternative patterns.

### Commit

Write the plan file (per §Step 7 above), stage it, and commit on the authoring branch with:

- **Message headline** — Conventional Commits shape: `feat(qa): test plan for <feature_correlation_id>` (or `chore(qa): test plan for <feature_correlation_id>` when the plan is a re-authoring of an existing plan). Keep under 72 characters.
- **Message body** — one short paragraph summarizing coverage (one line per behavior covered, or a count reference to the `tests[]` array).
- **Mandatory trailer** — `Feature: FEAT-YYYY-NNNN/TNN` (the `qa_authoring` task-level correlation ID), mirroring the component-agent PR-submission convention ([`/agents/component/skills/pr-submission/SKILL.md`](../../../component/skills/pr-submission/SKILL.md)). Every commit on the authoring branch carries this trailer; a missing or malformed trailer is a correctness bug.

The commit's author identity is the QA agent's role identity, not the human operator's. Trailer verification is a pre-push check: re-read the commit's message via `git log -1 --format=%B` and confirm the trailer is present and well-formed before opening the PR.

### PR

Open the PR against the specs repo's `main` branch. Not a draft PR — the plan is review-ready when the authoring pass completes.

- **Title** — `feat(qa): test plan for <feature_correlation_id>` (mirrors the commit headline; keep under 72 characters).
- **Body** — structured:
  - **First line** — the `qa_authoring` task-level correlation ID on its own (e.g., `FEAT-2026-0006/T02`), so the merge watcher and reviewers can pattern-match it from the PR body's first line.
  - **`## Summary`** — one-paragraph prose: what feature is covered, how many tests are in the plan, and the cardinality-override rationale if any.
  - **`## Plan** — path to the written plan file with a brief excerpt or reference to the rendered file.
  - **`## Coverage matrix`** — one line per test: `- <test_id> covers <AC identifier>`.
  - **`## How to review`** — what the reviewer should check (schema round-trip, coverage completeness, runtime-port assumption per §Step 5 pre-step).
  - **`Closes <owner>/<repo>#<N>`** — mandatory — references the `qa_authoring` task issue (in whichever repo it lives — typically the same component repo the plan targets). GitHub's `Closes` directive wires the merge-watcher's PR→task pairing; without it, the match is lost. The qa-curation skill's equivalent convention is authoritative on the same-owner cross-repo behavior (qa-curation SKILL §"Step 6" + Phase 3 walkthrough cross-repo evidence F3.12 reclassification).

### Stop-at-open discipline

Once the PR is open:

1. Flip the `qa_authoring` task's label `state:in-progress → state:in-review` per [`../../CLAUDE.md`](../../CLAUDE.md) §"Entry transitions owned".
2. Emit `task_completed` on the `qa_authoring` task (per §Step 7 steps 3–6 above).
3. **Stop.**

The skill does **not** merge the PR, close the PR, add reviewers, self-approve, or advance the PR's state in any way after opening. The `in_review → done` transition belongs to the merge watcher (architecture §6.3) once a human reviewer approves and merges. A skill invocation that attempts any of these further actions is a Q4 / anti-pattern #1 violation — the PR is a task-owned deliverable, but the merge is not a qa_authoring-role-owned transition.

### Idempotence on re-invocation

A replayed invocation on the same `qa_authoring` task should not produce a duplicate PR. Three mechanisms:

- **Branch-name uniqueness.** The branch `qa-authoring/<task_correlation_id>` is derived from the task correlation ID. A second invocation on the same task finds the branch already present and aborts with "idempotent skip: authoring branch already exists at `<branch>`; PR state = `<gh pr view state>`".
- **Task-label check.** A second invocation on a task already at `state:in-review` treats the prior invocation as successful and emits nothing further (no duplicate `task_completed`, no duplicate `test_plan_authored` — the per-type schema plus event-log read of the feature's prior `test_plan_authored` event acts as the emission guard, per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 idempotence discipline).
- **Plan-file-already-written branch.** If the plan file at `/product/test-plans/<feature_correlation_id>.md` already exists on `main` with frontmatter matching the current draft, the re-authoring is a no-op; the skill emits `task_completed` with `no_change: true` in a comment on the task issue and does not open a PR.

## Verification

Before emitting `test_plan_authored`, every check from step 6 must have passed with direct evidence (not inferred, not assumed). The skill's verification evidence for an authoring run includes:

- The schema-round-trip output confirming the written frontmatter validates.
- The unique-`test_id` check result.
- The coverage-check result (every AC fragment → at least one covering test).
- The re-read of the written plan file confirming the frontmatter on disk matches the validated draft.

Beyond the skill's local checks, the universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) apply:

- Re-read the produced artifact (the plan file) after writing (step 7 above).
- Round-trip the `test_plan_authored` event through `scripts/validate-event.py` with exit `0`.
- Confirm `source_version` is produced by `scripts/read-agent-version.sh qa` at emission time.
- Confirm the written path (`/product/test-plans/<feature_correlation_id>.md`) is not in [`never-touch.md`](../../../../shared/rules/never-touch.md). It is not; `/product/test-plans/` is explicitly QA-owned per [`../../CLAUDE.md`](../../CLAUDE.md).
- Confirm every state transition performed is one this role owns on this task type.

Failure handling follows [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable → retry, spinning at 3 cycles → escalate `spinning_detected` on the `qa_authoring` task (not on any implementation task), unrecoverable → escalate `spec_level_blocker`.

## Worked example

Fictional feature `FEAT-2026-0060 — Widgets export pagination`, used for illustration. One `qa_authoring` task on `clabonte/api-sample`, two acceptance criteria.

### Feature registry (before authoring)

```yaml
---
correlation_id: FEAT-2026-0060
state: in_progress
involved_repos:
  - clabonte/api-sample
autonomy_default: auto
task_graph:
  - id: T01
    type: implementation
    depends_on: []
    assigned_repo: clabonte/api-sample
  - id: T02
    type: qa_authoring
    depends_on: []
    assigned_repo: clabonte/api-sample
  # ... qa_execution, qa_curation omitted for brevity
---

## Description

Paginate the `GET /widgets/export` endpoint. By default, return the first 50
widgets. Reject `page_size` values over 500 with a structured 400 error.

## Scope

- Default page size of 50 when `page_size` is not supplied.
- Reject `page_size > 500` with HTTP 400 and error code
  `page_size_over_limit`.

## Related specs

- `product/api/openapi.yaml` (operation `GET /widgets/export`).

## Acceptance criteria

- **AC-1** — `GET /widgets/export` returns the first 50 widgets when no
  `page_size` parameter is supplied.
- **AC-2** — `GET /widgets/export` returns 400 Bad Request with error code
  `page_size_over_limit` when `page_size` exceeds 500.
```

### Behavior enumeration (step 3)

From the OpenAPI spec and the `## Acceptance criteria` section, two behaviors:

1. **Default page size** — AC-1.
2. **Page-size over limit** — AC-2.

### Cardinality override check (step 4)

The `## Scope` section is silent on `qa_authoring` cardinality. Default applies: one test per behavior, so two tests.

### Test drafting (step 5)

Runtime port discovered per the §Step 5 pre-step from `clabonte/api-sample`'s `src/ApiSample.Api/Properties/launchSettings.json` profile `http` → `applicationUrl: "http://localhost:8080"` → port `8080`. Threaded into `commands[]` below and documented in `## Coverage notes`.

- `test_id: widgets-export-default-page-size`
  - `covers`: "AC-1: GET /widgets/export returns the first 50 widgets when no page_size parameter is supplied."
  - `commands`: `["dotnet run --project src/ApiSample.Api/ --urls \"http://localhost:8080\" &", "curl -sS -o body.json -w '%{http_code}' http://localhost:8080/widgets/export"]`
  - `expected`: "HTTP status is 200 and body.json parses as a JSON array of exactly 50 widget objects, each with the fields id, status, and created_at."
- `test_id: widgets-export-page-size-over-limit-rejected`
  - `covers`: "AC-2: GET /widgets/export returns 400 Bad Request when page_size exceeds 500."
  - `commands`: `["curl -sS -o body.json -w '%{http_code}' 'http://localhost:8080/widgets/export?page_size=501'"]`
  - `expected`: "HTTP status is 400 and body.json contains an error object with error.code == 'page_size_over_limit'."

The first test's `commands[0]` starts the service (backgrounded with `&`); the second test inherits the running service. This is convention (i) from §Step 5 pre-step.

### Schema round-trip (step 6)

The draft object round-trips against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — see [`/shared/schemas/examples/test-plan.json`](../../../../shared/schemas/examples/test-plan.json) for the serialized form. Unique-`test_id` check: `{widgets-export-default-page-size, widgets-export-page-size-over-limit-rejected}` has size 2, matches array length 2 — unique. Coverage check: AC-1 cited in test 1, AC-2 cited in test 2 — every AC fragment covered.

### Written plan file (step 7)

Contents of `/product/test-plans/FEAT-2026-0060.md` in the product specs repo:

```markdown
---
schema_version: 1
feature_correlation_id: FEAT-2026-0060
tests:
  - test_id: widgets-export-default-page-size
    covers: "AC-1: GET /widgets/export returns the first 50 widgets when no page_size parameter is supplied."
    commands:
      - "dotnet run --project src/ApiSample.Api/ --urls \"http://localhost:8080\" &"
      - "curl -sS -o body.json -w '%{http_code}' http://localhost:8080/widgets/export"
    expected: "HTTP status is 200 and body.json parses as a JSON array of exactly 50 widget objects, each with the fields id, status, and created_at."
  - test_id: widgets-export-page-size-over-limit-rejected
    covers: "AC-2: GET /widgets/export returns 400 Bad Request when page_size exceeds 500."
    commands:
      - "curl -sS -o body.json -w '%{http_code}' 'http://localhost:8080/widgets/export?page_size=501'"
    expected: "HTTP status is 400 and body.json contains an error object with error.code == 'page_size_over_limit'."
---

## Coverage notes

Two tests, one per acceptance criterion. Default `qa_authoring` cardinality
applied — the feature's `## Scope` section does not collapse the count.

**Runtime port: `8080`**, sourced from
`src/ApiSample.Api/Properties/launchSettings.json` profile `http`
(`applicationUrl: "http://localhost:8080"`). The first test's `commands[0]`
backgrounds the service startup; the second test inherits the running
service. qa-execution should confirm the service has bound port 8080
before evaluating test 1's `expected` predicate.
```

### Emitted event

```json
{
  "timestamp": "2026-04-23T16:45:00Z",
  "correlation_id": "FEAT-2026-0060",
  "event_type": "test_plan_authored",
  "source": "qa",
  "source_version": "1.1.0",
  "payload": {
    "plan_path": "/product/test-plans/FEAT-2026-0060.md",
    "test_count": 2
  }
}
```

The event passes [`scripts/validate-event.py`](../../../../scripts/validate-event.py) (exit `0`) against both the top-level envelope and the per-type payload schema, and is appended to `/events/FEAT-2026-0060.jsonl`. See [`/shared/schemas/examples/test_plan_authored.json`](../../../../shared/schemas/examples/test_plan_authored.json) for the fixture.

## Deferred integration — Phase 4 + Phase 5 brief

The v1 skill is a **stub**. The `test-plan.schema.json` contract is deliberately minimal: `test_id`, `covers`, `commands`, `expected`. Phase 4 and Phase 5 extend this shape additively. The future WU author inherits a concrete brief from this section — no blank-sheet re-design is expected.

### What Phase 4 changes — specs-agent-driven richer plans

When the specs agent lands (Phase 4), plan authoring shifts from "QA agent reads specs and drafts a plan" to "specs agent emits a richer plan as part of spec authoring, QA agent verifies and extends". The QA agent stays in the loop — it remains the authority on regression, curation, and execution — but the authoring step becomes a specs-agent collaboration rather than a QA-only pass.

Specific schema evolution expected at Phase 4:

- **Arazzo-backed `commands` structure.** The free-form shell string becomes a structured step with explicit operation refs, input bindings, and output capture. An example shape (non-binding on Phase 4's final decision):
  ```yaml
  commands:
    - arazzo_step_ref: workflows.export.steps.happy_path
      inputs:
        page_size: null
      capture:
        body: $response.body
        status: $response.status
  ```
  The `commands` field on `test-plan.schema.json` becomes `oneOf: [{type: string}, {type: object, ...arazzo-step-schema}]` to preserve Phase 3 stubs while admitting the richer shape additively.
- **Structured `expected` predicates.** The textual prose becomes a machine-evaluable predicate (e.g., JSONPath assertions, response-schema conformance, state-based checks). Phase 4 picks the predicate language — candidates include JSONPath, JMESPath, CEL, or a custom mini-DSL.
- **`preconditions` field on each test.** Explicit state the test requires (database fixtures, seed data, feature flags). Phase 3 tests assume the setup is implicit in the `commands`; Phase 4 structures it.
- **Bindings between `covers` and the source spec.** Instead of a free-form citation string, `covers` becomes a structured reference (spec file + anchor/AC identifier) that tooling can cross-validate.

What Phase 4 does **not** change:

- **`test_id` stability contract.** `qa-regression` keys regression artifacts on `(implementation_task_correlation_id, test_id)`. Phase 4 does not regenerate `test_id`s or alter their format. Renames remain a curation PR concern, not an authoring one.
- **`feature_correlation_id` scoping.** One plan per feature; feature-level scope is preserved.
- **The escalation surface.** Ambiguity in the spec still routes through `spec_level_blocker`. Phase 4 may reduce the frequency of escalations by tightening spec contracts, but the surface is unchanged.
- **The `test_plan_authored` event payload.** `{plan_path, test_count}` remains the minimum signal. If Phase 4 needs richer event data, it adds fields additively, not by replacement.

### What Phase 5 changes — generator-emitted skeletons

When the Specfuse generator emits code scaffolds (Phase 5), it also emits **test plan skeletons** keyed off the OpenAPI/Arazzo surface it generated. The QA agent's role in authoring shifts from "draft from scratch" to "fill in and verify the skeleton". Concretely:

- The generator emits a skeleton plan file at `/product/test-plans/<feature>.md` with `tests[]` entries pre-populated for every generated operation's success and failure paths — `test_id` minted deterministically from the operation's OperationId, `covers` pointing at the OpenAPI response, `commands` and `expected` left as `TODO` placeholders for the QA agent to fill.
- The qa-authoring skill at Phase 5 becomes a **verification + completion** skill: confirm the skeleton's coverage matches the feature's acceptance criteria (same check as Phase 3's step 6), fill in `commands` and `expected` for each skeletal test, and add hand-authored tests for behaviors the skeleton did not enumerate.
- The `test-plan.schema.json` contract is unchanged. Phase 5 changes **who drafts the first pass** of the tests, not the shape of the artifact.

Phase 5 may introduce a `source: generator | qa | hybrid` field on each test entry for audit traceability, but that is an additive extension.

### Summary for the Phase 4 / Phase 5 WU authors

- This skill's structure and verification discipline persist — preserved as-is, the step-5 drafting section evolves.
- [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) evolves additively: richer `commands` and `expected` shapes, new optional fields. The Phase 3 stub remains valid.
- [`test_plan_authored.schema.json`](../../../../shared/schemas/events/test_plan_authored.schema.json) payload shape is preserved. Downstream consumers (`qa-execution` in WU 3.3) see no difference across phases.
- The `test_id` stability contract survives every phase. Renames remain curation's concern.
- The Phase 3 walkthrough (WU 3.6) is the input for Phase 4's cardinality and over-specification calls — which fields proved useful in practice, which are unused ornamentation.

## What this skill does not do

- It does **not** run the authored plan. Execution is [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) (WU 3.3).
- It does **not** file regressions. Regression handling is [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) (WU 3.4).
- It does **not** curate the suite. Curation is [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) (WU 3.5).
- It does **not** write to any path other than `/product/test-plans/<feature>.md` (product specs repo) and `/events/<feature>.jsonl` (orchestration repo). Writes elsewhere belong to other roles; see [`../../CLAUDE.md`](../../CLAUDE.md) §"Output artifacts and where they go".
- It does **not** flip labels or state on any task other than its own `qa_authoring` task. See [`../../CLAUDE.md`](../../CLAUDE.md) §"Cross-task regression semantics" — the invariant applies here even though regressions are out of scope for this skill.
- It does **not** guess. Every escalation point in the procedure is `spec_level_blocker` — the spec or scope information is insufficient, and the human (or specs agent) must resolve it before authoring continues.
- It does **not** query the Specfuse generator or any Arazzo tooling. Phase 4 and Phase 5 introduce those integrations; v1 is a stub.
- It does **not** rename a `test_id` in place during re-authoring. If a rename is needed, handle it via a curation PR (WU 3.5), preserving open-regression traceability.
- It does **not** merge an existing plan with a new draft on re-authoring. A spec change triggers a full re-draft; the prior plan is superseded.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §4.3 (test plan location), §5 (QA role), §6.2 (task types), §6.3 (transition ownership), §7.3 (event log).
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 3.2" — the work unit that authored this skill.
- [`/shared/schemas/test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — the stub contract authored in this WU.
- [`/shared/schemas/events/test_plan_authored.schema.json`](../../../../shared/schemas/events/test_plan_authored.schema.json) — per-type payload schema for the success event; first QA-emitted per-type schema.
- [`/shared/schemas/examples/test-plan.json`](../../../../shared/schemas/examples/test-plan.json) — the worked-example plan fixture.
- [`/shared/schemas/examples/test_plan_authored.json`](../../../../shared/schemas/examples/test_plan_authored.json) — the worked-example event fixture.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — `test_plan_authored` added to the enum in this WU.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 — universal discipline; per-type payload validation applies to `test_plan_authored` automatically.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally per invocation.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation surface spec ambiguities route through.
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — applies the per-type payload schema additively.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
- [`../../CLAUDE.md`](../../CLAUDE.md) — the QA role config that orchestrates this skill alongside its siblings.
- [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) — downstream skill (WU 3.3) that consumes the plan this one produces.
- [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) — further downstream (WU 3.4) that keys regression artifacts on `test_id`.
- [`../qa-curation/SKILL.md`](../qa-curation/SKILL.md) — curation skill (WU 3.5) that handles renames, dedup, and retirement.
- [`/agents/pm/skills/task-decomposition/SKILL.md`](../../../../agents/pm/skills/task-decomposition/SKILL.md) — pattern reference; this skill follows its structure.
- [`/agents/pm/skills/template-coverage-check/SKILL.md`](../../../../agents/pm/skills/template-coverage-check/SKILL.md) — pattern reference for the stub-protocol posture and §"Deferred integration" shape.
