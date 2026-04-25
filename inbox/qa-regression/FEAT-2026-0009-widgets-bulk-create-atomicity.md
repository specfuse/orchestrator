---
correlation_id_feature: FEAT-2026-0009
test_id: widgets-bulk-create-atomicity
regressed_implementation_task_correlation_id: FEAT-2026-0009/T01
failing_qa_execution_event_ts: 2026-04-25T17:27:50Z
failing_commit_sha: bba7afa9712219cc2daa1e87f49fdf49612653b1
test_plan_path: /product/test-plans/FEAT-2026-0009.md
target_repo: Bontyyy/orchestrator-api-sample
---

## Failed test

- Test plan: /product/test-plans/FEAT-2026-0009.md
- Test ID: widgets-bulk-create-atomicity

## Expected behavior

HTTP status in bulk_status.txt is 422. The count value in count_after.json equals the count value in count_before.json, confirming that the valid widget in the batch was NOT persisted when the batch contained an invalid item. The python3 assertion exits 0 on success and raises AssertionError with a descriptive message if the count changed.

## Observed behavior

AssertionError: Atomicity violated: count changed from 5 to 6. Valid widget at index 0 was persisted before invalid item at index 1 was detected.

## Reproduction steps

1. Start the api-sample service at commit bba7afa9712219cc2daa1e87f49fdf49612653b1: `dotnet run --project src/OrchestratorApiSample.Api/ --urls "http://localhost:5083" &` then `sleep 3`.
2. Capture the widget count before the bulk request: `curl -sS http://localhost:5083/widgets/count -o count_before.json`
3. Issue a mixed-valid/invalid bulk POST: `curl -sS -o bulk_body.json -w '%{http_code}' -X POST http://localhost:5083/widgets/bulk -H 'Content-Type: application/json' -d '[{"name":"GoodWidget","sku":"SKU-G001","quantity":7},{"name":"","sku":"SKU-BAD","quantity":5}]' > bulk_status.txt`
4. Capture the widget count after the bulk request: `curl -sS http://localhost:5083/widgets/count -o count_after.json`
5. Assert counts are equal: `python3 -c "import json; before=json.load(open('count_before.json'))['count']; after=json.load(open('count_after.json'))['count']; assert before==after, f'Atomicity violated: count changed from {before} to {after}'"`

## Regression context

- Regressed against implementation task: FEAT-2026-0009/T01
- Failing commit: bba7afa9712219cc2daa1e87f49fdf49612653b1
- Failing qa_execution event timestamp: 2026-04-25T17:27:50Z
- Target repo: Bontyyy/orchestrator-api-sample
