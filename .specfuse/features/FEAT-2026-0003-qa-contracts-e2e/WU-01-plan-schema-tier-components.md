---
id: FEAT-2026-0003/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 0.80
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - shared/schemas/test-plan.schema.json
  - tests/test_qa_contracts.py
gate_set: code
driver_version: 0.3.11
started_at: 2026-07-09T20:07:15.952087+00:00
duration_seconds: 99.845
cost_usd: 0.507841
input_tokens: 9256
output_tokens: 4795
---

# Add optional `tier` + `components` to the test-plan schema

**Objective.** Extend `shared/schemas/test-plan.schema.json` so each test may optionally
declare a `tier` (`smoke|contract|journey|regression|uat`) and `components` (repos under
test), keeping the change fully additive — existing plans validate unchanged.

**Context.** Feature FEAT-2026-0003 / gate 1, `FEAT-2026-0003/T01`. Roadmap goal in
`.specfuse/roadmap.md`. `shared/schemas/` is the source of truth; the hatch build hook
mirrors it into `specfuse/orchestrator/_substrate/` — do NOT hand-edit `_substrate/`. The
plan schema's per-test object currently requires `test_id, covers, commands, expected`
with `additionalProperties:false`, so adding fields is a schema change, not just a doc.
No test currently validates the example fixtures against the schemas — this WU authors the
first such test file, `tests/test_qa_contracts.py`, loading the schema directly from
`shared/schemas/` via `jsonschema.Draft202012Validator` (NOT `paths.substrate`, which can
be a stale build artifact in a source checkout). Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**
- Red test: `tests/test_qa_contracts.py::test_plan_tier_components_validate` fails on HEAD
  and passes after — a test-plan object whose `tests[0]` carries `tier: "journey"` and
  `components: ["api", "web"]` validates against `shared/schemas/test-plan.schema.json`.
- `tests/test_qa_contracts.py::test_plan_existing_example_still_valid` — the shipped
  `shared/schemas/examples/test-plan.json` (no new fields) validates unchanged.
- `tests/test_qa_contracts.py::test_plan_bad_tier_rejected` — a `tier` value outside the
  enum (e.g. `"e2e"`) is rejected by the validator.
- Schema delta: `tier` = optional `{enum: [smoke, contract, journey, regression, uat]}`;
  `components` = optional `{type: array, minItems: 1, items: {type: string, minLength: 1}}`;
  the per-test `additionalProperties:false` and `required` list are unchanged.
- The schema's `$comment` gains a one-line FEAT-2026-0003 additive-extension provenance note.
- Full `code` set green (build/pytest/ruff/bandit/coverage). Schemas are data — no
  coverage-floor change expected.

**Do not touch.** The event payload schemas (`qa_execution_*` — that is T02), the
`_substrate/` mirror (hatch-generated), `agents/`, the qa-execution skill, secrets,
`.git/`, `PLAN.md status`.

**Verification.** The `code` set in `.specfuse/verification.yml`; the three tests above.
Schema self-check: `python3 -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('shared/schemas/test-plan.schema.json')))"`.

**Escalation triggers.** If adding `components` as a per-test field conflicts with a
plan-level placement the schema's design implies (e.g. components belong on the plan, not
the test), emit `status: blocked` naming the ambiguity rather than guessing the level —
the field's home (test vs plan) is load-bearing for gate 2's failure-routing.
