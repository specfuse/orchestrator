---
id: FEAT-2026-0003/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.10
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - shared/schemas/events/qa_execution_completed.schema.json
  - shared/schemas/events/qa_execution_failed.schema.json
  - shared/schemas/examples/qa_execution_completed_manifest.json
  - tests/test_qa_contracts.py
gate_set: code
driver_version: 0.3.11
started_at: 2026-07-09T20:08:55.861252+00:00
duration_seconds: 125.189
cost_usd: 0.676241
input_tokens: 7843
output_tokens: 10562
---

# Add `stack_manifest` + `manifest_hash` to the execution-event payloads

**Objective.** Extend both `qa_execution_completed` and `qa_execution_failed` payload
schemas with optional `stack_manifest` and `manifest_hash`, and relax `commit_sha` from a
hard requirement to `anyOf[commit_sha | stack_manifest]`, so a cross-component run can
report a result without a single primary SHA — additively, existing events validate
unchanged.

**Context.** Feature FEAT-2026-0003 / gate 1, `FEAT-2026-0003/T02`, depends on T01.
Both schemas live under `shared/schemas/events/`; `shared/` is the source of truth (hatch
mirrors to `_substrate/` — do NOT edit `_substrate/`). Today each payload's top-level
`required` includes `commit_sha` (`^[0-9a-f]{40}$`) with `additionalProperties:false`.
The idempotence RULE that consumes `manifest_hash` lands in gate 2 (qa-execution skill);
this WU only declares the fields and relaxes the constraint. Extends the same
`tests/test_qa_contracts.py` T01 created, loading schemas directly from `shared/schemas/`
via `jsonschema`. Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**
- Red test: `tests/test_qa_contracts.py::test_event_stack_manifest_validates` fails on HEAD
  and passes after — a `qa_execution_completed` payload with
  `stack_manifest: {"api": "<40-hex sha>", "web": "2.1.0"}`, `manifest_hash: <64-hex>`,
  `plan_path`, `test_count`, `task_correlation_id`, and **no** `commit_sha` validates.
- `tests/test_qa_contracts.py::test_event_commit_sha_only_still_valid` — the shipped
  `shared/schemas/examples/qa_execution_completed.json` AND `qa_execution_failed.json`
  (commit_sha, no manifest) validate unchanged against their schemas.
- `tests/test_qa_contracts.py::test_event_neither_key_rejected` — a payload with neither
  `commit_sha` nor `stack_manifest` is rejected (both schemas).
- `tests/test_qa_contracts.py::test_event_short_sha_rejected` — a short `commit_sha` is
  still rejected.
- Schema delta (both files): add `stack_manifest`
  `{type: object, minProperties: 1, additionalProperties: {type: string, minLength: 1}}`
  and `manifest_hash` `{type: string, pattern: "^[0-9a-f]{64}$"}`; replace the top-level
  `required` entry `commit_sha` with
  `anyOf: [{required: [commit_sha]}, {required: [stack_manifest]}]` while leaving the other
  required fields (`task_correlation_id, plan_path, test_count`; plus `failed_tests` on the
  failed schema) intact; keep `additionalProperties:false`.
- New example fixture `shared/schemas/examples/qa_execution_completed_manifest.json`
  (manifest-based, no commit_sha) is added and validated by the red test.
- Each schema's `$comment` idempotence note is updated to say the key becomes
  `(task_correlation_id, manifest_hash)` when a manifest is present (rule authored in G2).
- Full `code` set green.

**Do not touch.** `test-plan.schema.json` (T01), the `_substrate/` mirror, the
qa-execution SKILL idempotence logic (gate 2), `agents/`, secrets, `.git/`, `PLAN.md status`.

**Verification.** The `code` set; the four tests above. Schema self-check on both files:
`python3 -c "import json,jsonschema,glob; [jsonschema.Draft202012Validator.check_schema(json.load(open(f))) for f in glob.glob('shared/schemas/events/qa_execution_*.schema.json')]"`.

**Escalation triggers.** If the `anyOf` relaxation makes an already-shipped fixture
elsewhere in the tree fail validation (grep `shared/schemas/examples/` and any event-log
fixtures under `tests/`), emit `status: blocked` naming the fixture rather than editing a
consumer's data to fit — the additive guarantee is the contract, and a breaking fixture
means the relaxation is wrong, not the fixture.
