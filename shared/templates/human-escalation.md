<!--
Human escalation body template. v0.1.

Written by an agent into `/inbox/human-escalation/` when it cannot proceed
without a human decision. The polling loop routes the file from the inbox;
this template is the file's content contract (orchestrator-architecture.md
§7.4, §6.4).

Fill in every placeholder and delete these HTML comments before saving. One
escalation per file.
-->

## Correlation ID

<!-- Feature-level (`FEAT-YYYY-NNNN`) if the escalation is about the feature
as a whole; task-level (`FEAT-YYYY-NNNN/TNN`) if it is about a single task. -->

<FEAT-YYYY-NNNN or FEAT-YYYY-NNNN/TNN>

## Reason

<!-- Exactly one value from the enumerated list below. The handler dispatches
on this value; ad-hoc reasons are not routed. -->

<spinning_detected | autonomy_requires_approval | spec_level_blocker | override_expiry_needs_review>

## Agent state

<!-- The agent's current state at the moment of escalation: which role is
escalating, what it was doing, what it has tried, and any relevant links
(issues, PRs, event log entries). Enough that a human can pick up the thread
cold. -->

- Role: <specs | pm | qa | component:<name> | config-steward | merge-watcher>
- What I was doing: <one sentence>
- What I tried: <bullet or one sentence>
- Relevant links: <issue/PR/event URLs>

## Decision requested

<!-- The specific decision the human is expected to make. Phrase it as a
question with the options spelled out, so the answer is an unambiguous
selection. -->

<question, with the options the human can choose from>
