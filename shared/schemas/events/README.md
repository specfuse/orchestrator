# Per-type event payload schemas

One JSON Schema file per `event_type` enum value in [`../event.schema.json`](../event.schema.json). The top-level schema governs the envelope (`timestamp`, `correlation_id`, `event_type`, `source`, `source_version`, `payload`); the files in this directory govern the **shape of the `payload` object** for a specific event type.

## Conventions

- File name: `<event_type>.schema.json`, where `<event_type>` matches an enum value in `../event.schema.json` exactly (e.g. `task_started.schema.json`, not `task-started.schema.json`).
- Root type: `object`. The schema validates the contents of `payload`, not the full event.
- `$id`: `https://specfuse.dev/orchestrator/schemas/events/<event_type>.schema.json`.
- `$schema`: `https://json-schema.org/draft/2020-12/schema`.
- `additionalProperties: false` by default. A payload field not declared in the schema is a mis-emission; tightening here produces early, loud failures over silent drift.
- Every declared field has a type and, where applicable, a `format` or `pattern`. Optional fields are admitted only when a legitimate use case (like `task_started.branch` in the escalation-before-branch-cut case) justifies the optionality — documented in the schema's description.

## Additive extension — Phase 1 freeze contract preserved

[`../../../scripts/validate-event.py`](../../../scripts/validate-event.py) applies a per-type schema **only when the corresponding file exists in this directory**. An event type without a schema file here is validated against the top-level envelope alone; its historical emissions remain valid. The validator's behavior for unschematized event types is unchanged from the Phase 1 contract — see [`../../rules/verify-before-report.md`](../../rules/verify-before-report.md) §3.

This is deliberate. Phase 1 froze the component agent's emission patterns (`task_started`, `task_completed`, `task_blocked`, `spec_issue_raised`, `human_escalation`) at version 1.2.0 and above. Adding a per-type schema here after the fact must not retroactively invalidate existing event log entries. Each per-type schema added in this directory is authored by re-reading representative historical payloads and drafting the schema to accept them; breaking changes require a separate migration commit that rewrites historical `/events/*.jsonl` entries.

## Current per-type schemas

- [`task_started.schema.json`](task_started.schema.json) — `payload.branch` is `string | null` (the nullable case covers tasks that escalate before cutting a branch, per Phase 1 retrospective Finding 5). Authored 2026-04-22 in WU 2.5 as the first per-type schema precedent.
- [`template_coverage_checked.schema.json`](template_coverage_checked.schema.json) — `payload.involved_repos` (array of repo strings) + `payload.task_count` (integer). Authored 2026-04-22 in WU 2.6.
- [`feature_state_changed.schema.json`](feature_state_changed.schema.json) — `payload.from_state`, `payload.to_state` (enum over feature state vocabulary), `payload.trigger` (freeform string). Authored 2026-04-23 in WU 2.9; closes finding F1.1.
- [`human_escalation.schema.json`](human_escalation.schema.json) — `payload.summary` (prose), `payload.reason` (enum: `spinning_detected`, `autonomy_requires_approval`, `spec_level_blocker`, `override_expiry_needs_review`), `payload.inbox_file` (optional path), `payload.cycle_members` (optional array of task IDs). Authored 2026-04-23 in WU 2.9; closes finding F2.8. Historical payloads (FEAT-2026-0005 line 4) validated before authoring.
- [`test_plan_authored.schema.json`](test_plan_authored.schema.json) — `payload.plan_path` (required, string matching `^/product/test-plans/FEAT-\d{4}-\d{4}\.md$`) + `payload.test_count` (required, integer ≥1). Authored 2026-04-23 in WU 3.2; first QA-emitted per-type schema. Follows the `template_coverage_checked` precedent of carrying the minimum fields a consumer needs without duplicating the canonical artifact (the plan file itself).
- [`qa_execution_completed.schema.json`](qa_execution_completed.schema.json) — `payload.task_correlation_id` (required, task-level ID), `payload.commit_sha` (required, 40-char git SHA), `payload.plan_path` (required), `payload.test_count` (required, integer ≥1), `payload.total_duration_seconds` (optional). Authored 2026-04-23 in WU 3.3. The `(task_correlation_id, commit_sha)` pair is the idempotence key the qa-execution skill enforces before emitting.
- [`qa_execution_failed.schema.json`](qa_execution_failed.schema.json) — same identifying fields as completed, plus `payload.failed_tests` (required, array of `{test_id, first_signal, optional exit_code, optional stderr_excerpt}`, minItems 1). Authored 2026-04-23 in WU 3.3. Same idempotence key as completed. The `implementation_task_correlation_id` being regressed against is NOT carried in the payload — WU 3.4 (qa-regression) resolves it from the feature task graph (SOT = feature registry), because feature-scope overrides on qa_authoring cardinality (WU 2.10) make the test→implementation mapping not 1:1.

## When to add a new per-type schema

- When a role about to emit a new event type is being written (e.g. the QA agent in Phase 3 emitting `test_plan_drafted`).
- When ambiguity in an existing event type's payload is observed in a walkthrough or review — the per-type schema is the place to pin the ambiguity down.
- Not before the event type has at least one representative emission. Schemas authored without real data tend to over-specify ornamental fields and miss the load-bearing ones.

A new per-type schema lands in one commit together with (a) its example under `../examples/` and (b) a validator round-trip against representative historical payloads confirming the new schema admits them.

## Example instances

Valid payload examples for each per-type schema live in [`../examples/`](../examples/), mirroring the sibling convention for the top-level schema. The examples are regression fixtures: the validator round-trips them on every change to a schema file.
