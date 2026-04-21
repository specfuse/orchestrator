# Phase 1 walkthrough — Task C log

## Identity

- **Walkthrough:** Phase 1, WU 1.5
- **Task:** C (edge case — `spec_level_blocker` escalation path)
- **Correlation ID:** `FEAT-2026-0003/T01`
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample)
- **Started:** 2026-04-21
- **Operator:** @Bontyyy (playing PM agent; Claude as co-pilot for drafting and picking the task shape, as component agent for execution)
- **Component agent version at execution:** 1.2.0
- **Status:** Escalated to `blocked_spec`; no PR opened by design.

## Objective

Run the v1 component agent end-to-end through an **escalation path** the walkthrough has not yet exercised. Tasks A (trivial, zero design judgment) and B (moderate, bounded design judgment with one scope correction) together confirm the non-escalation flow on the happy path. Per the WU 1.5 acceptance criterion 3 — _"an edge case: exercises a chemin d'escalation the happy path has not touched"_ — the most useful signal is on the `spec_level_blocker` → `blocked_spec` transition: does the agent recognize an irresolvable product-level ambiguity and stop, rather than push through with an arbitrary convention?

The **success condition of Task C is an escalation, not a merged PR.** Concretely: a filed spec issue, a well-formed `/inbox/human-escalation/` file, a label rotation to `state:blocked-spec`, and three events appended to the feature event log (`spec_issue_raised`, `task_blocked`, `human_escalation`). If the component agent ships an arbitrary convention to make the ambiguity go away, that is the finding.

## Task selection (PM role)

Three candidates were pre-identified as edge-case shapes against the sample repo:

1. **Generated-code override exercise** — excluded. The sample repo has no `_generated/` tree; there is nothing to override.
2. **Spec ambiguity → `blocked_spec`** — the issue body carries a genuine product-level ambiguity the agent cannot resolve from the repo alone; the correct response is to file a spec issue and stop.
3. **Spinning self-detection** — a task crafted to fail verification three cycles in a row, tripping the internal counter to `3`.

Candidate 2 was chosen. The two reasons it wins on the "edge case" criterion:

- **Realism of the signal.** Spec-level ambiguity is an everyday occurrence in any real backlog. Crafting a task explicitly to fail verification three times requires either unrealistic brittleness (the agent detects the impossibility before cycle 1 and escalates `spec_level_blocker` instead) or a contrived failure path that does not generalize. The spinning-counter mechanism is also a few lines of deterministic code in the escalation skill — if that logic has a bug, it is better surfaced by a unit test than by a walkthrough.
- **Surface tested.** Candidate 2 exercises: the spec-issue filing flow, the `/inbox/human-escalation/` file contract, the `in_progress → blocked_spec` transition with its label rotation, and three of the eight event types the component agent emits (`spec_issue_raised`, `task_blocked`, `human_escalation`). Candidate 3 would exercise the counter, one inbox file, and two events. Candidate 2 is strictly broader coverage of the escalation surface this walkthrough is designed to validate.

## Feature registry minting decision

Consistent with Task B's precedent ("one feature = one coherent user-facing capability"), Task C mints a new feature **FEAT-2026-0003 — Widget name uniqueness**. The capability (a uniqueness rule on `Widget.Name`) is categorically distinct from quantity validation (FEAT-2026-0001) and deletion (FEAT-2026-0002).

One consequence of the escalation outcome: the feature's `state` in [`features/FEAT-2026-0003.md`](../../../features/FEAT-2026-0003.md) stays `in_progress` after the escalation, not `blocked` — the feature as a whole is alive, only its sole implementation task is blocked. Per [`escalation-protocol.md`](../../../shared/rules/escalation-protocol.md) §"State machine effects of raising an escalation", feature-level state flips to `blocked` only when the escalation is raised outside of a specific task (e.g., a reconciliation-pass escalation).

## Shape of the ambiguity (PM role)

The work-unit issue body spec'd the uniqueness rule at a high level and deliberately left three independent product-level questions unspecified:

1. **Case sensitivity of the uniqueness comparison.** Is `"Blue Widget"` the same name as `"BLUE WIDGET"`? The sample repo has zero precedent: a `grep` across `src/` for `StringComparison`, `OrdinalIgnoreCase`, `InvariantCulture`, `ToLower`, `ToUpper` returns no matches. Picking `Ordinal` is the C# default; picking `OrdinalIgnoreCase` is the common user-facing choice. Both are defensible and produce observably different API behavior.
2. **HTTP error contract for the rejection.** Repo convention: every input-validation rejection surfaces `ValidationException` → `400 validation_failed`. REST standard (RFC 9110 §15.5.10) for duplicate-resource semantics on `POST`: `409 Conflict`. Extending the repo convention is local-consistency-optimal; extending the REST standard is protocol-consistency-optimal. Neither is mechanically derivable from the code.
3. **Repository method signature for the uniqueness lookup.** `IWidgetRepository` currently exposes only `AddAsync`, `GetByIdAsync`, `DeleteAsync`. A uniqueness check needs a new read method, but its signature depends on the resolution of (1): does it take a raw name, a normalized name, a (name, comparison) pair?

A secondary whitespace-handling concern is partially pre-resolved by `WidgetService.CreateAsync:44` (`Name: name.Trim()`). It is noted in the spec issue for completeness but was not treated as a fourth escalation-worthy axis on its own.

**The issue body is internally consistent.** It does not contradict itself — that was Task B's friction and would be a different test. It is internally under-specified, which is a different failure mode the `spec_level_blocker` path is explicitly designed to catch.

## Issue filing (on component repo)

- **Issue:** [Bontyyy/orchestrator-api-sample#7](https://github.com/Bontyyy/orchestrator-api-sample/issues/7)
- **Title:** `[FEAT-2026-0003/T01] Enforce unique widget name on POST /widgets`
- **Labels at creation:** `state:ready`, `type:implementation`, `autonomy:review`
- **Body:** follows [`work-unit-issue.md`](../../../shared/templates/work-unit-issue.md) v1.0 — five mandatory sections, YAML frontmatter carrying correlation ID, task type `implementation`, autonomy `review`, empty `depends_on`, empty `generated_surfaces`.

## Component agent execution

### Pickup

- `ready → in_progress` flipped on issue #7 via `gh issue edit --remove-label state:ready --add-label state:in-progress`.
- **No feature branch cut.** By escalation-skill design, the agent escalates before writing code; `task_started`'s `branch` payload was therefore `null`. The agent is entitled to cut the branch before analysis if it prefers — this run deliberately did not, to keep the component repo clean on an escalation that will not produce a PR.
- `task_started` event emitted to [`events/FEAT-2026-0003.jsonl`](../../../events/FEAT-2026-0003.jsonl) at `2026-04-21T21:02:20Z`.

### Analysis

The agent read, in order:

- The issue body — identified acceptance criteria 1 and 3 as the load-bearing ones and noted that both contain unresolved product-level questions.
- [`WidgetService.cs`](https://github.com/Bontyyy/orchestrator-api-sample/blob/main/src/OrchestratorApiSample.Application/Services/WidgetService.cs) — confirmed the existing `CreateAsync` validation pattern (`ValidationException`-based, name is trimmed before persist).
- [`IWidgetRepository.cs`](https://github.com/Bontyyy/orchestrator-api-sample/blob/main/src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs) — confirmed there is no read-by-name port method today.
- [`Widget.cs`](https://github.com/Bontyyy/orchestrator-api-sample/blob/main/src/OrchestratorApiSample.Domain/Widget.cs) — confirmed the domain record is a trivial `(Id, Name, Sku, Quantity)` carrier with no normalization.
- A repo-wide `grep` for `StringComparison`, `OrdinalIgnoreCase`, `InvariantCulture`, `ToLower`, `ToUpper` — zero matches across `src/`.

At the end of analysis, three ambiguities remained genuinely unresolved by any combination of re-reading the issue body, re-reading the code, or looking for convention. Per [`escalation/SKILL.md`](../../../agents/component/skills/escalation/SKILL.md) §2 _"a spec contradiction, omission, or ambiguity the agent cannot resolve inside the current task"_, this is a `spec_level_blocker` trigger.

### Escalation

1. **Spec issue filed.** [clabonte/orchestrator#5](https://github.com/clabonte/orchestrator/issues/5), titled `[spec-issue] FEAT-2026-0003/T01 — Widget name uniqueness is ambiguous on case sensitivity, error contract, and repository method signature`. Body follows [`spec-issue.md`](../../../shared/templates/spec-issue.md) v0.1: Observation (the three axes, stated as symptoms not causes), Location (#7 and the feature registry), Triggering task (FEAT-2026-0003/T01), Suggested resolution (a concrete amendment for each axis plus a preferred choice and its rationale, with the filing agent explicitly declining to decide unilaterally).

   **Routing decision:** the spec issue was filed against the orchestrator repo (`clabonte/orchestrator`) rather than against a dedicated product specs repo (which does not exist for this walkthrough) and rather than against the component repo itself (which is not a specs-authoring surface). The precedent for this routing was set in [`features/FEAT-2026-0002.md`](../../../features/FEAT-2026-0002.md) §"Related specs". See Finding 1 below.

2. **Inbox file written.** [`inbox/human-escalation/FEAT-2026-0003-T01-spec.md`](../../../inbox/human-escalation/FEAT-2026-0003-T01-spec.md), following [`human-escalation.md`](../../../shared/templates/human-escalation.md) v0.1: correlation ID, reason (`spec_level_blocker`), agent state (role, what I was doing, what I tried, relevant links), decision requested (three closed options — normal unblock, task reshape, abandon). The "what I tried" section enumerates the grep of `src/`, the re-read of the issue body, and the rejected consideration of self-authorizing an override (per anti-pattern 7).

3. **Label rotation.** `state:in-progress → state:blocked-spec` on issue #7 via `gh issue edit`.

4. **Events appended.** Three entries added to `events/FEAT-2026-0003.jsonl` at `2026-04-21T21:03:55Z`, in order:
   - `spec_issue_raised` — payload carries the spec issue URL, the triggering task ID, and a one-sentence summary.
   - `task_blocked` — payload names category `spec`, the inbox filename, and cross-references the spec issue URL for convenience.
   - `human_escalation` — payload carries reason `spec_level_blocker`, the inbox filename, and a one-sentence summary.

   All four entries in the event log validate against [`event.schema.json`](../../../shared/schemas/event.schema.json) on the required-fields check (`timestamp`, `correlation_id`, `event_type`, `source`, `source_version`, `payload`).

### Verification gates — deliberately not run

The six mandatory verification gates and the per-task verification commands were **not run** on this task. Per the escalation skill §"After escalating", the agent stops the moment the escalation is raised; running verification would be both wasted work and a signal that the escalation discipline did not hold. The `task_completed` event is consequently **not emitted** — only `task_started`, `spec_issue_raised`, `task_blocked`, and `human_escalation` appear in the event log. A later resumption (after the human triages the spec issue and rotates the label back to `state:ready`) would pick up from analysis and run the full gate set at that point.

### No PR

No feature branch was pushed on the sample repo. No PR was opened. These are non-actions by design on a `blocked_spec` escalation.

## Friction surfaced

### Finding 1 — spec-issue routing for walkthrough features is implicit, not documented

**What happened.** The escalation skill says the component agent files a spec issue "against the product specs repo or the Specfuse generator project" (§2). The walkthrough sample repo has no product specs repo. The precedent set in `FEAT-2026-0002.md` §"Related specs" says _"No product specs repo entries — this is a walkthrough feature, not a product feature"_ — but does not say where a spec issue for such a feature should be filed.

The agent picked the orchestrator repo (`clabonte/orchestrator`) as the surrogate specs surface, on the reasoning that the feature registry entry lives there and amendments to it would land via a PR to that repo. It documented this routing choice in both the spec issue body ("Filing context" section) and the inbox file.

**Why it's worth logging.** The choice is defensible but not deterministic. A different component agent run could as plausibly file on the sample repo itself, or skip the spec issue entirely and describe the situation in the inbox file only. This ambiguity in the escalation skill (about where to route for walkthrough / specs-less features) is a real gap. Candidate fix: add an explicit clause to [`escalation/SKILL.md`](../../../agents/component/skills/escalation/SKILL.md) §2 or to [`features/README.md`](../../../features/README.md) stating: _"when a feature has no product specs repo (walkthrough features, early bootstrap, legacy), file the spec issue against the orchestrator repo itself."_ Alternatively, amend the work-unit-issue template to carry a `specs_repo` frontmatter field the PM sets at feature creation, removing the ambiguity at the contract level.

Carried to WU 1.6 retrospective candidate list.

### Finding 2 — `null` branch in `task_started` payload passes the schema but may confuse downstream consumers

**What happened.** Because the agent did not cut a feature branch before escalating, the `task_started` event's payload was `{"issue_url": "...", "branch": null}`. The schema permits this (payload is a free-form object), but downstream analysis code that assumes `payload.branch` is always a string would break.

**Why it's worth logging.** The event-log schema v0 deliberately leaves per-type payload shapes free ([`event.schema.json`](../../../shared/schemas/event.schema.json) comment: _"Per-type payload schemas will be added under /shared/schemas/events/ as they stabilize."_). This run is the first evidence that the `task_started` payload shape will need at least two cases: one where a branch has been cut (majority case, happy path), and one where the agent escalates before writing code (minority case, escalation path). Candidate fix for the Phase 2+ schema hardening: define `task_started.branch` as `string | null`, with `null` semantically meaning "escalated before code". Task A and Task B both carried a non-null branch so this shape was not visible before.

Carried to WU 1.6 retrospective candidate list.

### Finding 3 — event schema validation still not automated (carried over from Task A and Task B)

Still present. The four events were constructed by hand against [`event.schema.json`](../../../shared/schemas/event.schema.json) and validated with an ad-hoc Python script that only checks required-field presence, not full schema conformance. Tasks A and B carried the same finding on their smaller payloads; Task C's three-escalation-event burst made the cost of manual validation more visible. Third run in a row surfacing the same gap.

### Finding 4 — `source_version` drift risk (carried over from Task A and Task B)

Still present. All four events hard-code `"1.2.0"` after the agent reads `agents/component/version.md` by eye. Third run in a row.

### No Task B-style scope error this run

The issue body for T01 was drafted with Task B's finding in mind ("PM issue-drafting skill must verify claims about repo state, not assert them from memory of the repo's convention"). Every claim about repo state in the issue body was verified by reading the file at draft time. No mid-task scope correction was needed. This is one data point in favor of the WU 1.6 retrospective prioritizing that finding as a **fix-in-Phase-1** candidate rather than deferring it.

## Config / skill changes prompted by this run

**None required for agent correctness on the escalation path.** The v1 component agent configuration produced a well-formed escalation that held the stop discipline. Candidates for the WU 1.6 retrospective list:

- **Escalation skill ambiguity on walkthrough/specs-less features** (Finding 1). One-sentence addendum or template change.
- **Event schema per-type payload shapes** (Finding 2). Schema hardening for Phase 2+.
- **Carryover items** (Findings 3, 4). Event-schema validation automation and `source_version` auto-read are now seen in three consecutive walkthrough runs — evidence that manual discipline is not sufficient and a small automation would pay back immediately.

These are candidates for triage, not blocking changes to ship on this branch.

## Outcome

Task C succeeded on its stated success condition: a well-formed `spec_level_blocker` escalation was produced without code being written or verification being bypassed. Specifically:

| Artifact | Status |
|---|---|
| Feature registry entry at `features/FEAT-2026-0003.md` | Written; feature `state: in_progress`. |
| Work-unit issue on component repo | Filed as [Bontyyy/orchestrator-api-sample#7](https://github.com/Bontyyy/orchestrator-api-sample/issues/7), label now `state:blocked-spec`. |
| Spec issue on surrogate specs repo | Filed as [clabonte/orchestrator#5](https://github.com/clabonte/orchestrator/issues/5). |
| Inbox file | Written at `inbox/human-escalation/FEAT-2026-0003-T01-spec.md`. |
| Event log | `task_started` + `spec_issue_raised` + `task_blocked` + `human_escalation` in `events/FEAT-2026-0003.jsonl`, all schema-valid on required fields. |
| Feature branch on component repo | None (by design). |
| PR on component repo | None (by design). |
| `task_completed` event | Not emitted (correct — verification not run, task not complete). |

Combined with Tasks A and B, the walkthrough has now validated the v1 component agent on three shapes:

- **Trivial happy path** (Task A, FEAT-2026-0001): 2 files, 0 design judgment, 1 cycle, merged.
- **Moderate happy path** (Task B, FEAT-2026-0002): 6 files, 1 bounded design call, 1 cycle after scope correction, merged.
- **Edge-case escalation** (Task C, FEAT-2026-0003): 0 code files, escalation on irresolvable product-level ambiguity, no cycles run, blocked.

All three WU 1.5 acceptance criteria are met. The walkthrough is ready to wrap, with the retrospective (WU 1.6) positioned to triage the accumulated findings from all three runs — most of which now have cross-task evidence rather than single-run evidence.

## Open loose ends (human must close)

1. **Triage the spec issue.** [clabonte/orchestrator#5](https://github.com/clabonte/orchestrator/issues/5). The intended outcome of the walkthrough is to close the loop by recording the decision on the three axes — either in a comment on the spec issue, in an amendment to the work-unit issue body, or in a closing comment that points at wherever the decision is captured. The escalation is correctly staged; it should not be left hanging as a permanent demonstration artifact.
2. **Decide the task's ultimate resolution.** Among the three options presented in the inbox file: (a) resolve and unblock (then a future walkthrough session would pick T01 up from `ready` and run the happy path on a concrete spec), (b) reshape, or (c) abandon. For the walkthrough's purposes, any of the three is valid — the escalation itself is the artifact the walkthrough was designed to produce. Choosing (c) abandon is the cleanest close if the walkthrough does not intend to carry FEAT-2026-0003 forward into real implementation.
3. **Push this branch and open a PR.** Branch `phase-1/walkthrough-task-c` on the orchestrator repo carries the feature registry entry, the event log, the inbox file, and this log. Opens and merges with the same pattern as Tasks A and B.
