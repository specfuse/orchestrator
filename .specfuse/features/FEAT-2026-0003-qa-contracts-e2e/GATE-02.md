---
gate: 2
status: open
---

# Gate 2 — consumption layer: manifest-keyed idempotence, linkage, config delta (terminal)

## Definition of done

- The qa-execution skill's idempotence rule keys on `(task_correlation_id, manifest_hash)`
  when a `stack_manifest` is present, falling back to `(task_correlation_id, commit_sha)`
  for single-repo runs.
- The plan↔harness linkage convention (plan `test_id` ↔ executable-spec tag) is documented.
- The QA-agent-config delta carries the architectural justification the Phase-3 freeze
  requires for touching `agents/qa/`.

Terminal gate — single `close`. Substantive WUs are drafted by gate 1's `plan-next` and
inserted before the `G2-CLOSE` placeholder.

## Reflection notes

<Written at review time / recorded by auto-close.>
