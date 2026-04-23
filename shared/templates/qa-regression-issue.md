<!--
QA regression inbox file. v0.2.

Written by the QA agent under `/inbox/qa-regression/<FEAT>-<TESTID>.md` in
response to the first `qa_execution_failed` event for a given
`(implementation_task_correlation_id, test_id)` pair. The file is consumed by
the PM inbox handler (or the human) to spawn a NEW `implementation` task
against the component repo under test — the file's body becomes that new
issue's body; the frontmatter carries the machine-readable fields needed to
spawn without re-scanning the event log. The QA agent never mints the new
task's correlation ID and never flips labels or state on the original
implementation task under test (Q4 cross-task regression invariant — see
agents/qa/CLAUDE.md §"Cross-task regression semantics" and
agents/qa/skills/qa-regression/SKILL.md §"Verification").

Repeat failures (a second failure for the same pair after a linked fix
attempt) do NOT file a second artifact — they escalate `spinning_detected`
on the ORIGINAL implementation task via a `human_escalation` inbox file.
Hence this template carries no "first vs. repeat" field: the file's
existence at all means "first".

Fill in every placeholder and delete these HTML comments before writing.

Version history:
  v0.2 (WU 3.4) — added YAML frontmatter for inbox-consumer spawning;
                  reframed from "issue body against the implementation task"
                  to "inbox artifact that spawns a new implementation task";
                  removed the "Regression count (first | repeat)" field
                  (incompatible with the Q4 model).
  v0.1 (Phase 0) — initial draft, pre-Q4 model.
-->

---
correlation_id_feature: <FEAT-YYYY-NNNN>
test_id: <kebab-case test_id from the plan>
regressed_implementation_task_correlation_id: <FEAT-YYYY-NNNN/TNN>
failing_qa_execution_event_ts: <ISO-8601>
failing_commit_sha: <40-char git SHA>
test_plan_path: /product/test-plans/<FEAT-YYYY-NNNN>.md
target_repo: <owner/repo>
---

## Failed test

<!-- Pointer to the specific test that failed: the test plan document in the
product specs repo and the test identifier inside it. Values must match the
frontmatter fields above. -->

- Test plan: <path in product specs repo>
- Test ID: <identifier>

## Expected behavior

<!-- What the test plan states the system should do, quoted or paraphrased
from the plan's `expected` predicate. No interpretation beyond what the plan
says. -->

<expected>

## Observed behavior

<!-- What actually happened during execution. Include the `first_signal`
from the `qa_execution_failed` payload (assertion message, HTTP status, stack
trace head). Keep to the facts of the run. -->

<observed>

## Reproduction steps

<!-- Numbered steps sufficient for a fresh agent or human to reproduce the
failure against `failing_commit_sha`. Typically the test plan's `commands`
list, expanded with environment setup only if it differs from the repo
default. -->

1. <step>
2. <step>

## Regression context

<!-- The implementation task this regression is filed against, and the
coordinates that thread back into the event log. The spawning PM consumer
reads these fields from the frontmatter; this prose block is for the human
reviewing the spawned task issue. -->

- Regressed against implementation task: <FEAT-YYYY-NNNN/TNN>
- Failing commit: <40-char git SHA>
- Failing qa_execution event timestamp: <ISO-8601>
- Target repo: <owner/repo>
