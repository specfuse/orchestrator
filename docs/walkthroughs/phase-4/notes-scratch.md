# Phase 4 walkthrough — notes scratch

This is the pre-walkthrough work doc for WU 4.6. Five zones:

1. **Pre-computed task graphs** (sanity-check targets for PM task-decomposition).
2. **Pre-findings from skill dry-read** (hypotheses about friction).
3. **Session prompts — Feature 1** (FEAT-2026-0008, widget update PATCH, happy path).
4. **Session prompts — Feature 2** (FEAT-2026-0009, bulk creation POST, regression cycle).
5. **Real-time walkthrough notes** — appended during execution.

All absolute paths use:
- Orchestrator: `/Users/christian/Specfuse/orchestrator/`
- API sample: `/Users/christian/Specfuse/orchestrator-api-sample/`
- Specs sample: `/Users/christian/Specfuse/orchestrator-specs-sample/`

---

## Preamble clauses (absorbing Phase 3 findings)

Every subagent prompt includes these 5 clauses unless noted otherwise:

**P1 (F3.5):** Do NOT run `git commit` or `git add` on the orchestrator repo. You may read/write files there, but commits to the orchestrator are made only by the human operator's orchestration session.

**P2 (F3.13):** All timestamps in events must be produced by `date -u +"%Y-%m-%dT%H:%M:%SZ"` at the moment of emission. Do NOT synthesize timestamps from memory or from prior events.

**P3 (F3.6, F3.14):** Before constructing an event payload, read the per-type schema at `/Users/christian/Specfuse/orchestrator/shared/schemas/events/<event_type>.schema.json` if it exists. Use exactly the field names from the schema. If no per-type schema exists, construct a reasonable payload with envelope-only validation.

**P4 (F3.10, F3.25, F3.28):** To emit an event, follow this exact safe-append pattern:
1. Construct the event as a SINGLE LINE of JSON (no pretty-printing, no newlines within the JSON).
2. Write the event to a temporary file (e.g., `/tmp/event-check.json`).
3. Validate: `python3 /Users/christian/Specfuse/orchestrator/scripts/validate-event.py --file /tmp/event-check.json` — require exit 0.
4. Append: `printf '%s\n' "$(cat /tmp/event-check.json)" >> /Users/christian/Specfuse/orchestrator/events/FEAT-YYYY-NNNN.jsonl`
Do NOT use `cat tmpfile >> logfile` without the printf wrapper (JSONL concatenation bug from F3.28).

**P5 (F3.35):** Report every friction point, surprise, or workaround encountered during the session — even minor ones. Do NOT sanitize your report. These are retrospective inputs.

---

## 1 — Pre-computed task graphs

### FEAT-2026-0008 (Widget update — PATCH /widgets/:id)

| id | type | depends_on | assigned_repo | required_templates* |
|---|---|---|---|---|
| T01 | implementation | [] | Bontyyy/orchestrator-api-sample | `[api-controller, api-request-validator]` |
| T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample | `[test-plan]` |
| T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample | `[]` |
| T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample | `[]` |

Rationale:
- **T01 required_templates.** PATCH endpoint needs controller (routing + action method) + request validator (partial body validation — must reject empty body? validate field ranges?). `api-response-serializer` arguably optional since the response shape is the same Widget model the GET endpoints already serialize, but included implicitly via controller. Going with `[api-controller, api-request-validator]` — serializer not separately required since the existing Widget response shape is reused.
- **T02 qa_authoring** is independent — test plan authored from spec ACs, not from implementation.
- **T03 qa_execution** depends on T01 (code to run tests against) + T02 (test plan to execute).
- **T04 qa_curation** follows T03.
- **All assigned_repo = api-sample.** Single-repo feature. T02 and T04 carry `deliverable_repo: Bontyyy/orchestrator-specs-sample` in the work-unit-issue body.

### FEAT-2026-0009 (Bulk creation — POST /widgets/bulk)

| id | type | depends_on | assigned_repo | required_templates* |
|---|---|---|---|---|
| T01 | implementation | [] | Bontyyy/orchestrator-api-sample | `[api-controller, api-request-validator]` |
| T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample | `[test-plan]` |
| T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample | `[]` |
| T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample | `[]` |

On regression (T03 fails AC-3):
| T05 | implementation | [] | Bontyyy/orchestrator-api-sample | `[]` |

Rationale:
- **T01 required_templates.** Bulk endpoint needs controller + request validator (array body validation, batch size check, per-item validation).
- **Regression T05** is filed by QA agent via `/inbox/qa-regression/` — a new implementation task targeting the same repo. No templates required (it's a fix to existing code, not a new template-driven scaffold).
- **Re-execution after fix** is a re-run of T03 against the fixed commit, not a separate T06. Per qa-regression SKILL.md, resolution happens when qa-execution passes on a commit post-dating the regression filing.

\*`required_templates` added by human during plan_review (PM task-decomposition v1 does NOT infer them).

---

## 2 — Pre-findings from skill dry-read

### PF-1 — Specs agent sessions are session-driven, not task-driven

**What.** Unlike PM/component/QA which process structured task inputs, the specs agent is conversational. For the walkthrough, we simulate the human's role in the conversation within the subagent prompt. The prompt must include: (a) the feature description, (b) scoping answers, (c) AC guidance, so the specs agent can produce outputs without an interactive back-and-forth.

**Expected friction.** The spec-drafting skill expects multi-turn conversation (Phase 1: scoping questions → Phase 2: draft specs → Phase 3: review). Flattening this into a single subagent prompt may produce slightly mechanical output. Acceptable for walkthrough purposes.

**Surfaces at:** F1 S2 (spec-drafting), F2 S2 (spec-drafting).

### PF-2 — Specfuse validator may not be installed locally

**What.** The spec-validation skill invokes `specfuse validate <path>`. The Specfuse tool may not be available on the walkthrough machine. If absent, the walkthrough operator simulates validation output.

**Expected friction.** If `specfuse` CLI is not installed, S3 (spec-validation) requires a workaround: either install it, or have the human provide simulated validation output. The skill's procedure is written to interpret actual validator output, so a simulated pass is the simplest fallback.

**Surfaces at:** F1 S3, F2 S3.

### PF-3 — Feature-intake worked example uses FEAT-2026-0008

**What.** The feature-intake SKILL.md worked example uses `FEAT-2026-0008` as its example correlation ID — the exact ID our walkthrough will mint for Feature 1. This is coincidental (the example was written generically) but may confuse a subagent that reads the worked example and sees the same ID in its output.

**Expected friction.** Low — the collision check in the skill procedure will detect if the file exists and increment. But worth noting.

**Surfaces at:** F1 S1.

### PF-4 — Specs-to-PM handoff (validating → planning) is first-ever runtime exercise

**What.** The `validating → planning` transition has been authored (WU 4.4 spec-validation skill) but never exercised at runtime. This is the first time a feature actually transitions from specs agent to PM agent through the event-driven handoff.

**Expected friction.** The PM agent's task-decomposition skill reads features with `state: planning`. If the specs agent's transition writes the correct state and event, the PM picks up seamlessly. If not, the handoff fails and we have a finding.

**Surfaces at:** Between F1 S3 and F1 S4.

### PF-5 — qa-regression inbox consumer simulation

**What.** Same as Phase 3 PF-7. The qa-regression skill writes to `/inbox/qa-regression/` but does NOT spawn the fix task. The human must simulate the PM inbox consumer: read the inbox file, mint T05, open the GitHub issue, emit `task_created` + `task_ready` events.

**Expected friction.** Manual + novel (first-ever runtime exercise of this path). Detailed runbook in F2 session plan.

**Surfaces at:** F2 between S14 and S16.

### PF-6 — Widget entity is an immutable record (sealed)

**What.** The api-sample's Widget is `public sealed record Widget(string Id, string Name, string Sku, int Quantity)`. PATCH requires partial update on an immutable record. The component agent will need to construct a new record with changed fields. This is natural in C# 10+ (`widget with { Name = newName }`) but the agent must recognize the pattern.

**Expected friction.** Low for Sonnet 4.6 — C# `with` expression on records is well-known. May surface as the agent choosing between mutation vs. reconstruction.

**Surfaces at:** F1 S8 (component implementation).

---

## 3 — Session prompts (F1: FEAT-2026-0008 — Widget update PATCH)

Each prompt is designed for `Agent` tool:
```
Agent({
  description: "F1 session N — <short>",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: <body below>
})
```

---

### F1 S1 — Specs agent feature-intake

```
You are acting as the specs agent (v1.0.0) performing the feature-intake skill. This is a Phase 4 walkthrough session — honesty about friction is required.

Setup discipline (re-read before acting, per /shared/rules/role-switch-hygiene.md):
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/specs/CLAUDE.md (specs role config).
3. Read /Users/christian/Specfuse/orchestrator/agents/specs/skills/feature-intake/SKILL.md (the skill you are executing).

Preamble clauses:
P1: Do NOT run `git commit` or `git add` on the orchestrator repo.
P2: Timestamps via `date -u +"%Y-%m-%dT%H:%M:%SZ"`.
P3: Read per-type event schema before constructing payload — check /Users/christian/Specfuse/orchestrator/shared/schemas/events/feature_created.schema.json.
P4: Safe-append pattern: write event to /tmp/event-check.json, validate via `python3 /Users/christian/Specfuse/orchestrator/scripts/validate-event.py --file /tmp/event-check.json`, then `printf '%s\n' "$(cat /tmp/event-check.json)" >> /Users/christian/Specfuse/orchestrator/events/FEAT-YYYY-NNNN.jsonl`.
P5: Report all friction unsanitized.

Task:
The human wants to create a new feature. Inputs:
- Feature title: "Widget update endpoint"
- Involved repos: ["Bontyyy/orchestrator-api-sample"]
- Autonomy default: review

Follow the feature-intake SKILL.md procedure steps 1–7:
- Determine next available ordinal (scan existing /Users/christian/Specfuse/orchestrator/features/FEAT-2026-*.md files).
- Handle collision check.
- Create registry file from template at /Users/christian/Specfuse/orchestrator/shared/templates/feature-registry.md.
- Validate frontmatter via `python3 /Users/christian/Specfuse/orchestrator/scripts/validate-frontmatter.py --file /Users/christian/Specfuse/orchestrator/features/FEAT-2026-NNNN.md`.
- Emit feature_created event per safe-append pattern.
- Verify: re-read registry + event log.

Expected output: FEAT-2026-0008 (since max existing is FEAT-2026-0007).

Do NOT:
- Transition feature state beyond drafting.
- Write to any repo other than the orchestrator.
- Populate task_graph (stays empty []).
- Draft spec content (that's spec-drafting skill).

Report:
- The registry file path and frontmatter.
- The full event JSON emitted.
- Verification evidence (validate-frontmatter.py exit code, validate-event.py exit code).
- All friction encountered.
```

---

### F1 S2 — Specs agent spec-drafting

```
You are acting as the specs agent (v1.0.0) performing the spec-drafting skill. This is a Phase 4 walkthrough session — honesty about friction is required.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/specs/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/specs/skills/spec-drafting/SKILL.md.
4. Read /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md (the feature registry entry from S1).

Preamble clauses:
P1: Do NOT run `git commit` or `git add` on the orchestrator repo.
P5: Report all friction unsanitized.

Context: Feature FEAT-2026-0008 — "Widget update endpoint". The human wants to add a PATCH /widgets/:id endpoint to the existing widget API on Bontyyy/orchestrator-api-sample.

The human's scoping answers (simulating the conversational Phase 1 of the skill):
- Description: Add partial-update capability to the widget entity. Clients send a JSON body with any subset of {name, sku, quantity} fields. Only provided fields are updated; omitted fields retain their current values.
- Scope: Single new endpoint PATCH /widgets/:id on the existing WidgetsController. Uses the existing Widget model and InMemoryWidgetRepository.
- Out of scope: Full replacement (PUT), bulk updates, ETag/concurrency control, field-level validation beyond existing CreateWidget rules (name non-blank, sku non-blank, quantity 0-10000).
- Involved repos: Bontyyy/orchestrator-api-sample only.
- Acceptance criteria:
  - AC-1: PATCH /widgets/:id with a valid partial body (any subset of {name, sku, quantity}) returns HTTP 200 with the full updated widget JSON. Omitted fields retain their prior values.
  - AC-2: PATCH /widgets/:id with a non-existent ID returns HTTP 404 with a JSON error body containing error.code = "widget_not_found".

Your task (spec-drafting Phase 2 + Phase 3):
1. Create a feature narrative file at /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0008.md with:
   - Feature title, description, scope, out of scope
   - Acceptance criteria section with AC-1 and AC-2 formatted per the skill's guidance
2. Update the orchestrator feature registry at /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md:
   - Populate ## Description, ## Scope, ## Out of scope sections
   - Add ## Related specs section with link to the spec file in Bontyyy/orchestrator-specs-sample
3. Do NOT create an OpenAPI spec file — the feature narrative with ACs is sufficient for this walkthrough feature (same pattern as Phase 3 walkthroughs FEAT-2026-0006 and FEAT-2026-0007).
4. Verify: re-read both files after writing to confirm content.

Acceptance criteria format per skill guidance:
- Each AC is testable (single behavior, verifiable by command + outcome)
- Each AC is scoped (one criterion = one observable)
- Response status codes and error codes are explicit

Do NOT:
- Run Specfuse validation (that's spec-validation skill, S3).
- Modify feature state in frontmatter (stays drafting).
- Write to /product/test-plans/ (QA agent's subtree).
- Write to /business/ in specs-sample.
- Push to GitHub.

Report:
- The feature narrative file content.
- The updated registry file content.
- Verification evidence (re-read confirms).
- All friction encountered.
```

---

### F1 S3 — Specs agent spec-validation

```
You are acting as the specs agent (v1.0.0) performing the spec-validation skill. This is a Phase 4 walkthrough session.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/specs/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/specs/skills/spec-validation/SKILL.md.
4. Read /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md (current state).
5. Read the event log at /Users/christian/Specfuse/orchestrator/events/FEAT-2026-0008.jsonl (for idempotence guards).

Preamble clauses: P1, P2, P3, P4, P5 (see preamble section above — apply all 5).
P3 detail: Read /Users/christian/Specfuse/orchestrator/shared/schemas/events/feature_state_changed.schema.json AND /Users/christian/Specfuse/orchestrator/shared/schemas/events/spec_validated.schema.json before constructing events.

Task:
The human has signaled that the spec for FEAT-2026-0008 is ready for validation. Follow the spec-validation SKILL.md procedure:

Step 1: Read feature registry, confirm state=drafting, extract spec paths from ## Related specs.
Step 2: Emit drafting → validating transition (feature_state_changed event + frontmatter update).
Step 3: Attempt to run Specfuse validation. NOTE: The `specfuse` CLI may not be installed on this machine. Try `specfuse validate <path>` first. If the command is not found, report this as friction and proceed with a SIMULATED clean validation pass — this is documented as a known limitation (PF-2 in notes-scratch).
Step 4: Emit spec_validated event (pass=true if simulated clean pass).
Step 5: On pass — emit validating → planning transition (feature_state_changed event + frontmatter update).
Step 6: Verify — re-read registry state (should be planning), re-read event log.

Events to emit (3 total):
1. feature_state_changed: from_state=drafting, to_state=validating, trigger=human_requested_validation (or trigger=validation_requested per CLAUDE.md)
2. spec_validated: feature_correlation_id=FEAT-2026-0008, pass=true, spec_files_checked=[...], errors=[], validator_version="simulated-1.0" (if specfuse not available)
3. feature_state_changed: from_state=validating, to_state=planning, trigger=validation_clean (or trigger=validation_passed per CLAUDE.md)

source on all events: "specs"
source_version: produced by `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh specs`

Each event validated individually via safe-append pattern (P4).

Do NOT:
- Transition beyond planning.
- Create task graph or open issues (PM agent's job).
- Write to component repos.
- Skip the spec_validated event even on simulated pass.

Report:
- All 3 events emitted (full JSON).
- Registry state after completion (should be: state=planning).
- Verification evidence.
- Friction — especially note the specfuse CLI availability and how you handled it.
```

---

### F1 S4 — PM task-decomposition on FEAT-2026-0008

```
You are acting as the PM agent (v1.6.3, frozen Phase 2 baseline) performing the task-decomposition skill. This is a walkthrough session — honesty about friction is required.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/pm/skills/task-decomposition/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Feature registry: /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md (state=planning, task_graph=[]).
- Related specs file: /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0008.md (local clone).

Expected flow per SKILL.md:
- Read feature registry + spec files.
- Enumerate capabilities (2 ACs → 1 behavior: partial-update endpoint with success + error cases).
- Build task list: T01 implementation, T02 qa_authoring, T03 qa_execution, T04 qa_curation.
- Build depends_on edges: T01=[], T02=[], T03=[T01,T02], T04=[T03].
- Validate in memory.
- Write task_graph to frontmatter + emit task_graph_drafted event.

Writes:
- /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md — update task_graph array. LEAVE state=planning.
- /Users/christian/Specfuse/orchestrator/events/FEAT-2026-0008.jsonl — append task_graph_drafted event.

Do NOT populate `required_templates` (human adds during plan_review).
source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh pm`

Do NOT: modify frozen surfaces, push to GitHub, transition feature state, open issues.

Report: task graph table, event JSON, verification evidence, all friction.
```

---

### F1 S5 — Human plan_review (manual, no subagent)

Steps for the human operator:
1. Edit /features/FEAT-2026-0008.md frontmatter — add `required_templates` per task:
   - T01: `[api-controller, api-request-validator]`
   - T02: `[test-plan]`
   - T03: `[]`
   - T04: `[]`
2. Change `state: planning` → `state: generating` (skip transient plan_review in frontmatter).
3. Emit 2 events via safe-append:
   - `feature_state_changed(planning → plan_review, trigger=plan_ready)` — source=human, source_version=<short SHA>
   - `feature_state_changed(plan_review → generating, trigger=plan_approved)` — source=human, source_version=<short SHA>
4. Validate both events + frontmatter.

---

### F1 S6 — PM template-coverage-check

```
You are acting as the PM agent (v1.6.3) performing the template-coverage-check skill.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/pm/skills/template-coverage-check/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Feature registry: /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md (state=generating, task_graph populated with required_templates).
- Template declarations: /Users/christian/Specfuse/orchestrator-api-sample/.specfuse/templates.yaml (local clone).

Flow: read registry → read template declarations → cross-reference required_templates per task against provided_templates → emit template_coverage_checked event.

Expected: all tasks satisfied. api-sample provides [api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]. T01 needs [api-controller, api-request-validator] ✓. T02 needs [test-plan] ✓. T03/T04 need [] ✓.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh pm`

Do NOT: modify frozen surfaces, push to GitHub, open issues, modify feature state.

Report: coverage result, event JSON, verification evidence, friction.
```

---

### F1 S7 — PM issue-drafting

```
You are acting as the PM agent (v1.6.3) performing the issue-drafting skill.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/pm/skills/issue-drafting/SKILL.md.
4. Read /Users/christian/Specfuse/orchestrator/shared/templates/work-unit-issue.md (v1.2 template).
5. Read /Users/christian/Specfuse/orchestrator/shared/templates/work-unit-issue.example.md (worked example).

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Feature registry: /Users/christian/Specfuse/orchestrator/features/FEAT-2026-0008.md (state=generating).
- Feature spec: /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0008.md.
- Target repo for all issues: Bontyyy/orchestrator-api-sample.

Open 4 GitHub issues on Bontyyy/orchestrator-api-sample:
- T01 (implementation, ready): branch name format = feat/FEAT-2026-0008-T01-widget-update
- T02 (qa_authoring, ready): deliverable_repo = Bontyyy/orchestrator-specs-sample (NOT clabonte/orchestrator — per F3.7 mitigation)
- T03 (qa_execution, pending): depends on T01 + T02
- T04 (qa_curation, pending): depends on T03, deliverable_repo = Bontyyy/orchestrator-specs-sample

Issue labels: `type:implementation`/`type:qa_authoring`/`type:qa_execution`/`type:qa_curation` + `state:ready` or `state:pending`.
Feature label: `feature:FEAT-2026-0008`.

Emit events (6 total):
- 4 × task_created (one per task, with correlation_id = FEAT-2026-0008/T01 through T04)
- 2 × task_ready (for T01 and T02 — they have no dependencies)

After all 4 issues opened, emit feature_state_changed(generating → in_progress, trigger=first_task_opened) per WU 3.10.

OBSERVATION POINT: record whether you emitted generating → in_progress on the FIRST task_created or after ALL task_created events. This is the "first round semantics" observation for the walkthrough.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh pm`

Do NOT: modify frozen surfaces, merge anything, implement code.

Report: all issue URLs + numbers, all events (full JSON), generating→in_progress timing observation, verification evidence, friction.
```

---

### F1 S8 — Component implementation T01

```
You are acting as the component agent (v1.5.2, frozen Phase 1 baseline) implementing task FEAT-2026-0008/T01.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/component/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/component/skills/verification/SKILL.md.
4. Read /Users/christian/Specfuse/orchestrator/agents/component/skills/pr-submission/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read the T01 issue on Bontyyy/orchestrator-api-sample (use `gh issue view <number> -R Bontyyy/orchestrator-api-sample`). The issue number will have been recorded in the F1 S7 output.
- Read the feature spec at /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0008.md.
- Working directory for implementation: /Users/christian/Specfuse/orchestrator-api-sample/

Implementation requirements (from ACs):
- AC-1: Add PATCH /widgets/:id action to WidgetsController. Accept JSON body with optional fields {name, sku, quantity}. Update only provided fields. Return 200 + full updated widget.
- AC-2: If widget ID not found, return 404 with {"error":{"code":"widget_not_found","message":"..."}}.

Implementation notes:
- Widget is a `sealed record` — use C# `with` expression for immutable update.
- WidgetService needs a new UpdateAsync method.
- IWidgetRepository needs a new Update method (replace entry in ConcurrentDictionary).
- Apply existing validation rules to updated fields (name non-blank after update, sku non-blank, quantity 0-10000).

Flow:
1. Pull latest main: `cd /Users/christian/Specfuse/orchestrator-api-sample && git pull origin main`
2. Create feature branch: `git checkout -b feat/FEAT-2026-0008-T01-widget-update`
3. Implement the PATCH endpoint + service + repository changes.
4. Write unit tests.
5. Run all 6 verification gates per verification.yml.
6. Pre-gate: `dotnet restore && dotnet build` (F3.1 mitigation).
7. Submit PR via `gh pr create` with Feature: FEAT-2026-0008/T01 trailer.
8. Emit task_started event to orchestrator events file.

Do NOT:
- Merge the PR (human merges).
- Modify generated code directories without override.
- Push to orchestrator repo.

Report: PR URL, verification gate results (6/6), event JSON, implementation summary, friction.
```

---

### F1 S9 — Human merge T01 (manual)

Steps:
1. Review PR on api-sample.
2. Merge via `gh pr merge <number> -R Bontyyy/orchestrator-api-sample --merge`.
3. Emit task_completed event for FEAT-2026-0008/T01 (source=human, commit SHA from merge).

---

### F1 S10 — QA qa-authoring T02

```
You are acting as the QA agent (v1.5.2, frozen Phase 3 baseline) performing the qa-authoring skill for task FEAT-2026-0008/T02.

Setup discipline:
1. Read every file under /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/qa/skills/qa-authoring/SKILL.md.
4. Read /Users/christian/Specfuse/orchestrator/shared/schemas/test-plan.schema.json.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read the T02 issue on Bontyyy/orchestrator-api-sample (use `gh issue view <number> -R Bontyyy/orchestrator-api-sample`).
- Read the feature spec at /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0008.md.

Author a test plan at /Users/christian/Specfuse/orchestrator-specs-sample/product/test-plans/FEAT-2026-0008.md covering:
- AC-1: PATCH with valid partial body → 200 + updated widget (test partial updates of each field individually)
- AC-2: PATCH with non-existent ID → 404 + widget_not_found error

Branch convention: `qa-authoring/FEAT-2026-0008-T02`
PR target: Bontyyy/orchestrator-specs-sample (NOT api-sample)

Emit test_plan_authored event to /Users/christian/Specfuse/orchestrator/events/FEAT-2026-0008.jsonl.
Emit task_started event for FEAT-2026-0008/T02.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Do NOT: merge the PR, execute tests, modify frozen surfaces.

Report: test plan content, PR URL, events, friction.
```

---

### F1 S11 — Human merge T02 (manual)

Steps:
1. Review + merge test plan PR on specs-sample.
2. Emit task_completed event for FEAT-2026-0008/T02.

---

### F1 S12 — PM dependency-recomputation

```
You are acting as the PM agent (v1.6.3) performing dependency-recomputation for FEAT-2026-0008.

Setup discipline:
1. Read /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/pm/skills/dependency-recomputation/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task: T01 and T02 are now complete. T03 (qa_execution) depends on [T01, T02] — both satisfied. Emit task_ready event for T03 (FEAT-2026-0008/T03).

Read the feature registry + event log first to confirm T01 and T02 have task_completed events.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh pm`

Report: task_ready event JSON, verification evidence, friction.
```

---

### F1 S13 — QA qa-execution T03

```
You are acting as the QA agent (v1.5.2) performing qa-execution for task FEAT-2026-0008/T03.

Setup discipline:
1. Read /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/qa/skills/qa-execution/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read T03 issue on Bontyyy/orchestrator-api-sample.
- Read test plan at /Users/christian/Specfuse/orchestrator-specs-sample/product/test-plans/FEAT-2026-0008.md.
- Working directory: /Users/christian/Specfuse/orchestrator-api-sample/
- Pull latest main (with T01 merged).

Execute the test plan:
- For each test case in the plan, run the test against the live API or unit test suite.
- This is a .NET project — run `dotnet test` to execute existing tests, and verify AC-1/AC-2 behaviors.
- Determine pass/fail per test.

Expected: ALL PASS (happy path — F1 is not designed to trigger regression).

Emit:
- task_started event for FEAT-2026-0008/T03
- qa_execution_completed event (if all pass) with commit_sha from HEAD of main

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Report: per-test results, events, friction.
```

---

### F1 S14 — QA qa-curation T04

```
You are acting as the QA agent (v1.5.2) performing qa-curation for task FEAT-2026-0008/T04.

Setup discipline:
1. Read /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/qa/skills/qa-curation/SKILL.md.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read T04 issue on Bontyyy/orchestrator-api-sample.
- Read the test plan corpus at /Users/christian/Specfuse/orchestrator-specs-sample/product/test-plans/ (all .md files).
- Curate: scan for duplicates, orphans, overlapping coverage across the corpus.

This is the first feature in a Phase 4 walkthrough — the corpus now includes FEAT-2026-0006, FEAT-2026-0007, FEAT-2026-9001/9002/9003 (Phase 3 seeded fixtures), and FEAT-2026-0008 (new).

Emit:
- task_started for FEAT-2026-0008/T04
- regression_suite_curated event

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Report: curation findings, events, friction.
```

---

### F1 S15 — Human verify + close (manual)

Steps:
1. Emit task_completed for T03 and T04.
2. Verify all 4 tasks have task_completed events.
3. Emit feature_state_changed(in_progress → done, trigger=all_tasks_complete).
4. Update feature registry state to done.
5. Validate all events: `python3 scripts/validate-event.py --file events/FEAT-2026-0008.jsonl`.
6. Validate frontmatter: `python3 scripts/validate-frontmatter.py --file features/FEAT-2026-0008.md`.

---

## 4 — Session prompts (F2: FEAT-2026-0009 — Bulk creation POST)

F2 follows the same session structure as F1 (S1–S9) with different feature content, then diverges at S13 (expected failure) into the regression loop.

F2 preamble: same P1–P5 as F1, plus:

**P6 (F2-specific):** This feature is designed to exercise the qa-regression runtime path. AC-3 is a two-layer trap (atomicity + per-item failure reporting). The walkthrough expects qa_execution_failed at S13. If all tests pass, the walkthrough uses the fallback path (manually introduce regression). Document honestly which path was taken.

---

### F2 S1 — Specs agent feature-intake (FEAT-2026-0009)

Same structure as F1 S1 with:
- Feature title: "Bulk widget creation endpoint"
- Involved repos: ["Bontyyy/orchestrator-api-sample"]
- Autonomy default: review
- Expected correlation ID: FEAT-2026-0009

---

### F2 S2 — Specs agent spec-drafting (FEAT-2026-0009)

Same structure as F1 S2 with different scoping:
- Description: Add a bulk-create endpoint POST /widgets/bulk that accepts an array of widget objects and creates them all in a single request. Supports atomic validation — if any widget fails validation, none are persisted.
- Scope: Single new endpoint POST /widgets/bulk on WidgetsController.
- Out of scope: Bulk update, bulk delete, streaming/async batch processing, idempotency keys.
- Acceptance criteria:
  - AC-1: POST /widgets/bulk with 1–50 valid widget objects returns HTTP 201 with an array of created widgets (each with a generated ID).
  - AC-2: POST /widgets/bulk with more than 50 items returns HTTP 400 with error.code = "batch_size_exceeded" and error.message describing the 50-item limit.
  - AC-3: If ANY widget in the batch fails validation (name blank, sku blank, or quantity outside 0–10000), the ENTIRE batch is rejected — zero widgets are persisted. Response is HTTP 422 with error.code = "batch_validation_failure" and error.failures array where each entry has "index" (0-based position of the failing item in the input array) and "reason" (human-readable validation message describing why that item failed).

---

### F2 S3 — Specs agent spec-validation (FEAT-2026-0009)

Same structure as F1 S3 with FEAT-2026-0009 correlation ID.

---

### F2 S4 — PM task-decomposition (FEAT-2026-0009)

Same structure as F1 S4 with FEAT-2026-0009.

---

### F2 S5 — Human plan_review (manual)

Same as F1 S5 with FEAT-2026-0009 and required_templates:
- T01: [api-controller, api-request-validator]
- T02: [test-plan]
- T03/T04: []

---

### F2 S6 — PM template-coverage-check (FEAT-2026-0009)

Same structure as F1 S6 with FEAT-2026-0009.

---

### F2 S7 — PM issue-drafting (FEAT-2026-0009)

Same structure as F1 S7 with FEAT-2026-0009. Branch for T01: `feat/FEAT-2026-0009-T01-bulk-creation`.

---

### F2 S8 — Component implementation T01

```
You are acting as the component agent (v1.5.2) implementing task FEAT-2026-0009/T01.

Setup discipline: same as F1 S8.
Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read T01 issue on Bontyyy/orchestrator-api-sample.
- Read feature spec at /Users/christian/Specfuse/orchestrator-specs-sample/product/features/FEAT-2026-0009.md.
- Working directory: /Users/christian/Specfuse/orchestrator-api-sample/

Implementation requirements:
- AC-1: POST /widgets/bulk with 1-50 valid widgets → 201 + array of created widgets.
- AC-2: POST /widgets/bulk with >50 items → 400 + batch_size_exceeded error.
- AC-3: If ANY widget fails validation, NONE persisted → 422 + batch_validation_failure + failures[] with index + reason.

NOTE: The component agent implements based on the ACs in the issue. It may or may not implement AC-3 correctly. This is the regression trap — do NOT give hints about atomicity or the failures array beyond what's in the issue/spec.

Flow: pull main, create branch feat/FEAT-2026-0009-T01-bulk-creation, implement, test, verify 6 gates, submit PR, emit task_started.

Report: PR URL, verification results, implementation summary, friction.
```

---

### F2 S9 — Human merge T01 (manual)

Same as F1 S9 for FEAT-2026-0009/T01.

---

### F2 S10 — QA qa-authoring T02 (FEAT-2026-0009)

Same structure as F1 S10 with 3 ACs to cover. Test plan should have at least 3 tests:
- Test 1: valid bulk create (AC-1)
- Test 2: >50 items rejected (AC-2)
- Test 3: mixed valid/invalid batch → all rejected + failures array with per-item detail (AC-3)

---

### F2 S11 — Human merge T02 (manual)

Same as F1 S11 for FEAT-2026-0009.

---

### F2 S12 — PM dependency-recomputation (FEAT-2026-0009)

Same as F1 S12 for FEAT-2026-0009.

---

### F2 S13 — QA qa-execution T03 (EXPECT FAILURE)

```
You are acting as the QA agent (v1.5.2) performing qa-execution for task FEAT-2026-0009/T03.

Setup discipline: same as F1 S13.
Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read T03 issue.
- Read test plan at /Users/christian/Specfuse/orchestrator-specs-sample/product/test-plans/FEAT-2026-0009.md.
- Working directory: /Users/christian/Specfuse/orchestrator-api-sample/
- Pull latest main (with T01 merged).

Execute the test plan against the implementation. Run each test case.

EXPECTED OUTCOME: AC-3 test(s) FAIL. The component agent likely missed the atomicity requirement (validates/persists items sequentially) and/or the per-item failures[] array in the 422 response.

If ALL tests pass (AC-3 implemented correctly):
- Report this as the "same outcome as Phase 3" — component agent got it right on first pass.
- The human operator will use the FALLBACK PATH: manually introduce a regression before re-executing.

Emit:
- task_started for FEAT-2026-0009/T03
- If failures: qa_execution_failed event with failed_tests array (test_id, first_signal per test)
- If all pass: qa_execution_completed event

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Report: per-test results with clear pass/fail, events, which AC(s) failed and why, friction.
```

---

### F2 S14 — QA qa-regression (if S13 failed)

```
You are acting as the QA agent (v1.5.2) performing the qa-regression skill. This is the FIRST RUNTIME EXERCISE of this skill — it was authored in WU 3.4 but never executed. Honesty is critical.

Setup discipline:
1. Read /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/qa/CLAUDE.md — pay special attention to "Cross-task regression semantics" and the Q4 invariant.
3. Read /Users/christian/Specfuse/orchestrator/agents/qa/skills/qa-regression/SKILL.md — the full skill procedure.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
T03 qa-execution just failed. The qa_execution_failed event has been emitted. Now follow the qa-regression SKILL procedure:

1. Read the qa_execution_failed event from /Users/christian/Specfuse/orchestrator/events/FEAT-2026-0009.jsonl.
2. Identify the implementation task via depends_on: T03 depends on [T01, T02] → filter to type=implementation → T01 is the regression target.
3. Check idempotence: no prior qa_regression_filed event for this (T01, test_id) pair.
4. Write the regression inbox artifact at /Users/christian/Specfuse/orchestrator/inbox/qa-regression/FEAT-2026-0009-<test_id>.md.
5. Emit qa_regression_filed event.

Q4 INVARIANT (CRITICAL):
- You MUST NOT write labels, state changes, or comments to the ORIGINAL T01 implementation task/issue.
- The inbox artifact is the ONLY handoff — a new implementation task will be spawned from it by the human (simulating PM inbox consumer).
- Your only outputs are: the inbox file + the qa_regression_filed event.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Report: inbox file content, event JSON, Q4 compliance statement (did you write to T01's issue?), friction.
```

---

### F2 S15 — Human Q4 audit + spawn fix task (manual)

Steps:
1. Q4 cross-attribution audit:
   - Verify the qa-regression agent wrote ONLY: inbox file + event. Nothing on T01 issue.
   - Check `gh issue view <T01-number> -R Bontyyy/orchestrator-api-sample` — no new comments or label changes from the regression session.
   - Document the audit in the walkthrough log.

2. Simulate PM inbox consumer:
   - Read /inbox/qa-regression/FEAT-2026-0009-<test_id>.md.
   - Mint new task: FEAT-2026-0009/T05 (type=implementation, regression fix).
   - Open GitHub issue on Bontyyy/orchestrator-api-sample with the regression fix requirements.
   - Emit task_created + task_ready events for T05.
   - Label the issue: type:implementation, state:ready, feature:FEAT-2026-0009.

---

### F2 S16 — Component implementation T05 (regression fix)

```
You are acting as the component agent (v1.5.2) implementing the regression-fix task FEAT-2026-0009/T05.

Setup discipline: same as F1 S8.
Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Read the T05 issue on Bontyyy/orchestrator-api-sample.
- The issue describes the AC-3 regression: the bulk creation endpoint either lacks atomicity (persists valid items before rejecting invalid ones) or lacks the per-item failures[] array in the 422 response, or both.
- Working directory: /Users/christian/Specfuse/orchestrator-api-sample/

Fix requirements (from the regression inbox artifact):
- Ensure POST /widgets/bulk validates ALL items BEFORE persisting ANY.
- On validation failure, return 422 with error.code = "batch_validation_failure" and error.failures array with {index, reason} per failed item.
- Zero valid items should be persisted when any item fails.

Flow: pull main, create branch fix/FEAT-2026-0009-T05-bulk-atomicity, fix, test, verify 6 gates, submit PR, emit task_started.

Report: PR URL, what was fixed, verification results, friction.
```

---

### F2 S17 — Human merge T05 fix (manual)

Steps:
1. Review + merge fix PR.
2. Emit task_completed for T05.

---

### F2 S18 — QA qa-execution re-run T03

```
You are acting as the QA agent (v1.5.2) performing qa-execution for task FEAT-2026-0009/T03 (re-execution after regression fix).

Setup discipline: same as F2 S13.
Preamble clauses: P1, P2, P3, P4, P5.

Task:
- Pull latest main (with T05 fix merged).
- Re-execute the test plan at /Users/christian/Specfuse/orchestrator-specs-sample/product/test-plans/FEAT-2026-0009.md.
- The AC-3 tests that previously failed should now pass.

Emit:
- qa_execution_completed event (if all pass now) with the NEW commit_sha from HEAD of main (post-fix).

Report: per-test results, events, friction.
```

---

### F2 S19 — QA qa-regression resolution

```
You are acting as the QA agent (v1.5.2) performing the qa-regression resolution path.

Setup discipline:
1. Read /Users/christian/Specfuse/orchestrator/shared/rules/ (8 files).
2. Read /Users/christian/Specfuse/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/christian/Specfuse/orchestrator/agents/qa/skills/qa-regression/SKILL.md — the resolution section.

Preamble clauses: P1, P2, P3, P4, P5.

Task:
T03 re-execution passed. The qa_execution_completed event (with a commit SHA post-dating the qa_regression_filed event) has been emitted. Per qa-regression SKILL resolution path:

1. Read the event log to find the qa_regression_filed event and the subsequent qa_execution_completed event.
2. Confirm the qa_execution_completed commit_sha post-dates the qa_regression_filed event.
3. Emit qa_regression_resolved event.
4. If a prior human_escalation event exists for this regression, emit escalation_resolved event.

source_version: `bash /Users/christian/Specfuse/orchestrator/scripts/read-agent-version.sh qa`

Report: resolution events, verification evidence, friction.
```

---

### F2 S20 — QA qa-curation + human close (manual)

Steps:
1. Run qa-curation (same pattern as F1 S14) for FEAT-2026-0009.
2. Emit task_completed for T03, T04.
3. Emit feature_state_changed(in_progress → done).
4. Validate all events.
5. Update registry state to done.

---

## 5 — Real-time walkthrough notes

(To be appended during execution.)
