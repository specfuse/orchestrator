---
correlation_id_feature: FEAT-2026-9002
test_id: widgets-metadata-has-last-updated
regressed_implementation_task_correlation_id: FEAT-2026-9002/T02
failing_qa_execution_event_ts: 2026-04-20T14:22:17Z
failing_commit_sha: 0000000000000000000000000000000000000002
test_plan_path: /product/test-plans/FEAT-2026-9002.md
target_repo: Bontyyy/orchestrator-api-sample
---

## Failed test

- Test plan: /product/test-plans/FEAT-2026-9002.md
- Test ID: widgets-metadata-has-last-updated

## Expected behavior

HTTP status is 200 and the response body contains a 'last_updated' ISO-8601 timestamp field.

## Observed behavior

HTTP 200 returned; body contains only 'count' field, no 'last_updated' key present.

## Reproduction steps

1. Start the api-sample service at commit 0000000000000000000000000000000000000002.
2. Issue `curl -sS http://localhost:5083/widgets/metadata`.
3. Inspect the JSON response — no `last_updated` key present.

## Regression context

- Regressed against implementation task: FEAT-2026-9002/T02
- Failing commit: 0000000000000000000000000000000000000002
- Failing qa_execution event timestamp: 2026-04-20T14:22:17Z
- Target repo: Bontyyy/orchestrator-api-sample

**FIXTURE NOTE:** This inbox artifact is seeded by the Phase 3 WU 3.6 F2 backup walkthrough (2026-04-24) to exercise qa-curation's open-regression protection path. No real implementation task was spawned; no real fix is forthcoming. The paired `qa_regression_filed` event at `/events/FEAT-2026-9002.jsonl` is the protection trigger. See `docs/walkthroughs/phase-3/feature-2-log.md` for walkthrough context.
