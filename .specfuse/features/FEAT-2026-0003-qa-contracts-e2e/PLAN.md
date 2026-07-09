---
feature_id: FEAT-2026-0003
title: E2E-capable QA contracts — test tiers, components, stack manifest
slug: qa-contracts-e2e
branch: feat/qa-contracts-e2e
roadmap_goal: Additively extend the QA contracts — plan schema gains optional `tier`/`components`, execution events gain optional `stack_manifest`/`manifest_hash` with manifest-keyed idempotence — so cross-component E2E/UAT results are expressible without breaking single-repo consumers.
autonomy_default: review
status: done
planned_cost_usd: 5.50
---

# Plan: E2E-capable QA contracts — test tiers, components, stack manifest

The QA contracts assume single-repo, single-SHA testing. `test-plan.schema.json` (v1
stub) has no notion of test tier or components-under-test, and the
`qa_execution_completed` / `qa_execution_failed` payloads require a single `commit_sha`,
with idempotence keyed on `(task_correlation_id, commit_sha)`. A cross-component E2E run
(a consumer's harness driving a deployed multi-service stack) cannot express its result:
no single SHA identifies what was tested, and plans cannot distinguish a smoke check from
a journey or route a failure to the responsible component. First consumer hitting this
wall: RestoManager's `restomanager-e2e` repo.

This feature extends the contracts **additively** — every new field is optional and every
existing plan and event validates unchanged. The extension lands in two layers:

- **Gate 1 — contract layer.** The schemas gain the new optional fields: plan `tier` +
  `components`; event `stack_manifest` + `manifest_hash`, with `commit_sha` relaxed to
  `anyOf[commit_sha | stack_manifest]` so a cross-component run need not fabricate a
  primary SHA. New `tests/test_qa_contracts.py` round-trips example fixtures against the
  schemas (a coverage gap today — no test validates `shared/schemas/examples/`).
- **Gate 2 — consumption layer.** The qa-execution skill's idempotence rule keys on
  `(task_correlation_id, manifest_hash)` when a manifest is present, falling back to
  `commit_sha`; the plan↔harness linkage convention (`test_id` ↔ executable-spec tag) is
  documented; the QA-agent-config delta carries the architectural justification the
  Phase-3 freeze requires. Gate 2's substantive WUs are drafted by gate 1's plan-next.

`shared/schemas/` is the source of truth; the hatch build hook mirrors it into
`_substrate/`. Edits land in `shared/`. Red tests load schemas directly from `shared/`
via `jsonschema`, not `paths.substrate` (which can be a stale build artifact in a source
tree).

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0003/T01
        file: WU-01-plan-schema-tier-components.md
        depends_on: []
      - id: FEAT-2026-0003/T02
        file: WU-02-event-payload-stack-manifest.md
        depends_on: [FEAT-2026-0003/T01]
      - id: FEAT-2026-0003/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0003/T01, FEAT-2026-0003/T02]
      - id: FEAT-2026-0003/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0003/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive WUs drafted by gate 1's plan-next (FEAT-2026-0003/G1-PLAN) — the
      # consumption layer: manifest-keyed idempotence rule / plan↔harness linkage doc /
      # QA-agent-config delta carrying the Phase-3-freeze justification. Armed at the
      # GATE-02-REVIEW.md checkpoint (status: draft -> pending).
      - id: FEAT-2026-0003/T03
        file: WU-03-qa-execution-manifest-idempotence.md
        depends_on: []
      - id: FEAT-2026-0003/T04
        file: WU-04-plan-harness-linkage-convention.md
        depends_on: []
      - id: FEAT-2026-0003/T05
        file: WU-05-qa-agent-config-delta.md
        depends_on: [FEAT-2026-0003/T03, FEAT-2026-0003/T04]
      - id: FEAT-2026-0003/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: [FEAT-2026-0003/T03, FEAT-2026-0003/T04, FEAT-2026-0003/T05]
```

## Notes

- The `code` gate's `pytest` set is the oracle; the new `tests/test_qa_contracts.py`
  validates example fixtures against `shared/schemas/`. Schemas are data, not python — no
  coverage-floor impact.
- Backwards contract: all new fields optional; `anyOf` relaxation keeps every existing
  `commit_sha`-bearing fixture valid. Call this out at each close.
- Scope OUT: the downstream harness implementation (RestoManager `restomanager-e2e`
  Playwright suite, deploy wiring) is a consumer concern, not built here — this feature
  ships only the contracts.
