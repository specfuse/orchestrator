<!--
QA regression issue body template. v0.1.

Opened by the QA agent against the implementation task whose delivered code
fails a QA-execution run. A first failure opens this issue and flips the
implementation task back to a regression state; a repeat failure after an
attempted fix escalates to human (orchestrator-architecture.md §6.4).

Fill in every placeholder and delete these HTML comments before posting.
-->

## Failed test

<!-- Pointer to the specific test that failed: the test plan document in the
product specs repo and the test identifier inside it. -->

- Test plan: <path in product specs repo>
- Test ID: <identifier>

## Expected behavior

<!-- What the test plan states the system should do, quoted or paraphrased
from the plan itself. No interpretation beyond what the plan says. -->

<expected>

## Observed behavior

<!-- What actually happened during execution. Include the first signal of
failure (assertion message, HTTP status, stack trace head). Keep to the facts
of the run. -->

<observed>

## Reproduction steps

<!-- Numbered steps sufficient for a fresh agent or human to reproduce the
failure against the same commit. Include environment setup only if it differs
from the repo default. -->

1. <step>
2. <step>

## Implementation task correlation

<!-- The implementation task this regression is filed against, so the event
log threads the failure back to the code under test. -->

- Task issue: <owner/repo#N>
- Correlation ID: FEAT-YYYY-NNNN/TNN

## Regression count

<!-- `first` on the initial failure, `repeat` on any subsequent failure after
an attempted fix. A `repeat` value triggers human escalation per §6.4. -->

<first | repeat>
