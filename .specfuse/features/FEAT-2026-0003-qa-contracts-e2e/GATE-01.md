---
gate: 1
status: passed
---

# Gate 1 — contract layer: additive QA schema extensions

## Definition of done

- `test-plan.schema.json` carries optional per-test `tier` (enum
  `smoke|contract|journey|regression|uat`) and `components` (array of repo-slug strings);
  `additionalProperties:false` and existing `required` unchanged.
- `qa_execution_completed` and `qa_execution_failed` payloads carry optional
  `stack_manifest` (`{slug: sha_or_version}`) and `manifest_hash` (`^[0-9a-f]{64}$`), with
  top-level `commit_sha` relaxed to `anyOf[commit_sha | stack_manifest]`.
- Existing example fixtures (`shared/schemas/examples/test-plan.json`,
  `qa_execution_completed.json`, `qa_execution_failed.json`) validate unchanged; a new
  manifest-based fixture validates; negative cases (bad tier, neither key, short SHA)
  rejected.
- Covered by new `tests/test_qa_contracts.py`; the full `code` set passes.

Non-terminal gate — closing sequence is `close-intermediate` + `plan-next`. Gate 2's
substantive WUs are drafted by this gate's plan-next.

## Reflection notes

<Written by the human at review time.>
