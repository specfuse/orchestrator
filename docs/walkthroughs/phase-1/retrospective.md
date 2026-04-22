# Phase 1 walkthrough — Retrospective (WU 1.6)

## Identity

- **Walkthrough:** Phase 1, WU 1.6 (retrospective over WU 1.5)
- **Scope:** triage of findings surfaced in Tasks A, B, and C of WU 1.5
- **Operator:** @Bontyyy (co-piloted with Claude as Opus 4.7)
- **Date conducted:** 2026-04-22
- **Inputs:** [task-A-log.md](task-A-log.md), [task-B-log.md](task-B-log.md), [task-C-log.md](task-C-log.md), [orchestrator-implementation-plan.md](../../orchestrator-implementation-plan.md) §"Phase 1", the feature registry entries for `FEAT-2026-0001` through `FEAT-2026-0003`, and the JSONL event logs for the same.
- **Status:** triage complete; Fix-in-Phase-1 work plan staged; items deferred to Phase 2+ tagged and cross-referenced.

## Objective

Triage the friction and gap findings surfaced across the three WU 1.5 tasks and decide, for each finding, whether it must be fixed before the Phase 1 configuration freeze or can be deferred to Phase 2+. Produce a concrete work plan for the Phase 1 fixes and a documented handoff list for the deferred items so Phase 2 (PM agent automation) starts from a fully-catalogued backlog rather than a fresh discovery pass.

Per the implementation plan, WU 1.6 is the decision artifact. Execution of the Fix-in-Phase-1 items themselves is carried by subsequent Phase 1 work units.

## Walkthrough outcome

All three WU 1.5 acceptance criteria were met by the tasks as executed:

| Criterion | Task | Feature | Shape | Outcome |
|---|---|---|---|---|
| 1 — trivial happy path, zero design judgment | A | `FEAT-2026-0001` | 2 files, 1 cycle | Merged ([sample repo PR #4](https://github.com/Bontyyy/orchestrator-api-sample/pull/4)) |
| 2 — moderate happy path, bounded design judgment | B | `FEAT-2026-0002` | 6 files, 1 design call, 1 cycle after scope correction | Merged ([sample repo PR #6](https://github.com/Bontyyy/orchestrator-api-sample/pull/6)) |
| 3 — escalation-path edge case | C | `FEAT-2026-0003` | 0 code files, `spec_level_blocker` escalation | Blocked-spec; loose ends closed as walkthrough artifacts (see below) |

The v1 component agent configuration (CLAUDE.md, skills at 1.2.0, shared rules) executed correctly across all three shapes. No skill needed correction mid-walkthrough to unblock the agent; all friction findings are tuning opportunities rather than configuration bugs. Phase 1's core goal — validating the component agent against the three shapes the plan called for — is achieved.

## Triage criteria

Every finding was scored against three questions in order. A "yes" on any of them qualifies the finding for **Fix in Phase 1**; otherwise it is **Deferred to Phase 2+**.

1. **Does it gate Phase 2?** If the PM agent (Phase 2's deliverable) would either re-encounter the finding on its first real task or inherit a broken contract from the current Phase 1 configuration, the finding must be fixed before Phase 2 starts. The inheritance case matters: anything the PM agent would copy — event-emission patterns, skill templates, shared schemas — is cheaper to fix once in Phase 1 than separately in every downstream role.

2. **Is there 3-run evidence?** A finding surfaced in all three of Tasks A, B, and C is not a single-session artifact; it is a reproducible failure of manual discipline. Three runs is the evidence threshold at which "we'll be more careful next time" stops being a credible answer and small automation becomes the cheaper long-term cost.

3. **Is the cost of deferring greater than the cost of fixing now?** Some single-run findings are cheap enough to fix (a one-sentence documentation clause, a template field) that deferring them manufactures friction for no saving. Applied sparingly — the default on single-run findings is to defer unless the forward cost is obviously larger.

Findings that fail all three tests defer by default. The deferred list is not "won't fix" — it is "fix when the context to fix it is already open", typically during the Phase 2+ work unit that touches the same surface.

## Findings triage

Eight findings total across the three task logs. Two with 3-run evidence (both Phase 1 fixes), six with 1-run evidence (three Phase 1 fixes on gate-Phase-2 grounds, three defers).

| # | Finding | Source | Runs | Gate P2? | **Decision** |
|---|---|---|---|---|---|
| 1 | Event schema validation is not automated | A obs. 2, B finding 4, C finding 3 | 3 | Yes | **Fix in Phase 1** |
| 2 | `source_version` is hard-coded from an eye-read of `version.md` | A obs. 4, B finding 3, C finding 4 | 3 | Yes | **Fix in Phase 1** |
| 3 | PM issue-drafting does not verify claims about repo state | B finding 1 (confirmed by absence in C) | 1 | Yes (hard) | **Fix in Phase 1** |
| 4 | Spec-issue routing for specs-less features is implicit | C finding 1 | 1 | Yes (partial) | **Fix in Phase 1** |
| 5 | `task_started.branch` payload should be formalized as `string \| null` | C finding 2 | 1 | No | **Defer to Phase 2+** |
| 6 | Shared-rules re-read discipline is implicit at role-switch | A obs. 1 | 1 | No | **Defer to Phase 2+** |
| 7 | `source: component:<name>` convention is under-specified | A obs. 3 | 1 | Yes (marginal) | **Fix in Phase 1** |
| 8 | Coverage gate should mandate a rebuild before `--no-build` | B finding 2 | 1 | No | **Defer to Phase 2+** |

The per-finding sections below justify each decision.

### Finding 1 — Event schema validation is not automated

**What.** Events (`task_started`, `task_completed`, `spec_issue_raised`, `task_blocked`, `human_escalation`) were constructed by hand against [`event.schema.json`](../../../shared/schemas/event.schema.json) and validated with ad-hoc, required-fields-only checks. No round-trip through a conformant JSON Schema validator occurred before events were appended to the `events/*.jsonl` log.

**Evidence.** Task A observation 2, Task B finding 4, Task C finding 3. Every task surfaced the same gap. Task C's three-event burst made the cost of manual validation more visible than the simpler payloads of Tasks A and B.

**Decision.** Fix in Phase 1.

**Rationale.** 3-run evidence — the threshold at which manual discipline is demonstrated to be insufficient. The finding also directly gates Phase 2: the PM agent emits additional event types (`task_created`, `task_ready`, `plan_approved`, etc.) and will copy the current hand-authoring pattern verbatim unless the validation harness exists by the time its skills are written. A shared validator (e.g. `scripts/validate-event.py`) invoked by every role before `>> events/*.jsonl` is inexpensive to build and pays back on every future event in every future role.

### Finding 2 — `source_version` is hard-coded from an eye-read of `version.md`

**What.** Every event emitted in WU 1.5 carried `source_version: "1.2.0"` because the agent read [`agents/component/version.md`](../../../agents/component/version.md) manually before writing each event. No runtime read of the file occurred at event-construction time.

**Evidence.** Task A observation 4, Task B finding 3, Task C finding 4.

**Decision.** Fix in Phase 1.

**Rationale.** 3-run evidence, identical logic to Finding 1. The PM agent (Phase 2) will have its own `agents/pm/version.md` and will inherit the eye-read pattern unless a convention is established now. The fix is either a shared-rule discipline ("agents read `agents/<role>/version.md` at event-construction time, never cached by eye") or a tiny helper (e.g. `scripts/read-agent-version.sh`) the event-construction step calls. Either path is small; pick at implementation time.

### Finding 3 — PM issue-drafting does not verify claims about repo state

**What.** In Task B, the initial work-unit issue body excluded controller-level tests "by symmetry with the other widget endpoints, which also only have service-level tests in this repo." The symmetry claim was false — `WidgetsControllerTests.cs` already existed on `main`. The component agent hit a coverage-gate failure mid-task and required an in-flight issue-body amendment plus three added controller tests to close scope.

**Evidence.** Task B finding 1 (primary). Task C's explicit *absence* of a similar scope error — the operator drafted T01's body with a repo-verification pass per Task B's lesson — is confirmatory: the finding is teachable, not a one-off.

**Decision.** Fix in Phase 1.

**Rationale.** This is the hardest Phase 2 gate on the list. The PM agent's core competency is drafting work-unit issue bodies that component and QA agents can execute against. An issue body whose "Out of scope" or "Context" sections assert things about repo state from memory — rather than verified from the repo at draft time — produces exactly the kind of internally-inconsistent document that forces downstream agents to escalate (the `spec_level_blocker` failure mode Task C was specifically designed to exercise). Shipping a PM agent without a "verify against repo" step in the issue-drafting skill would guarantee that failure mode in normal operation. The Phase 1 action is to codify the requirement — in a shared rule or in a specification note under [`/agents/pm/`](../../../agents/pm/) — so the Phase 2 work unit that authors the PM issue-drafting skill inherits a corrected contract from day one.

### Finding 4 — Spec-issue routing for specs-less features is implicit

**What.** [`escalation/SKILL.md`](../../../agents/component/skills/escalation/SKILL.md) §2 says the component agent files spec issues "against the product specs repo or the Specfuse generator project." Task C's feature had neither — walkthrough features have no dedicated specs repo. The agent picked the orchestrator repo as a surrogate specs surface, following the precedent in [`features/FEAT-2026-0002.md`](../../../features/FEAT-2026-0002.md) §"Related specs". Defensible but non-deterministic.

**Evidence.** Task C finding 1. Single run, but the ambiguity is structural — it recurs on any bootstrap or legacy feature without a product specs repo.

**Decision.** Fix in Phase 1.

**Rationale.** Partial but real Phase 2 gate. The PM agent will mint features, some of which — during bootstrap or for cross-repo coordination features that have no product-level spec — will have no specs repo to route escalations to. If the escalation skill remains silent on the specs-less case, every downstream component agent hit by the same situation will make its own routing choice, producing inconsistent event logs and inconsistent inbox files. The fix is small: a one-sentence clause in the escalation skill ("when the feature has no product specs repo, file the spec issue against the orchestrator repository") is the lower-cost path. A richer alternative — a `specs_repo` frontmatter field on the work-unit issue template that the PM agent sets explicitly — is available if desired, but the one-sentence clause is sufficient for Phase 1.

### Finding 5 — `task_started.branch` payload should be formalized as `string | null`

**What.** Task C escalated before cutting a feature branch (correct behavior on the escalation path), producing a `task_started` event with `payload.branch = null`. The schema permits this because per-type payload shapes are deliberately un-constrained today, but any downstream consumer assuming `payload.branch` is a string would break.

**Evidence.** Task C finding 2. First appearance of this payload shape.

**Decision.** Defer to Phase 2+.

**Rationale.** Task C's log itself classifies this as "Candidate fix for the Phase 2+ schema hardening" and that framing holds: no downstream consumer of the event log exists yet, so no contract is actively being violated. The schema hardening work (per-type payload shapes under `/shared/schemas/events/`) is a bundled Phase 2+ effort; this case is one input among several that will drive it. Fixing in Phase 1 in isolation — adding a single `task_started` payload schema — would create asymmetric rigor (only one event type's payload formalized) for no immediate payoff.

### Finding 6 — Shared-rules re-read discipline is implicit at role-switch

**What.** The component agent CLAUDE.md prescribes reading the full `/shared/rules/*` set before any task. In Task A, Claude-as-agent had already read those docs during the earlier co-pilot portion of the same session and did not re-read them explicitly at the role-switch into the agent loop. For Task A this was harmless; for a task where a rule applies non-obviously it could produce a miss.

**Evidence.** Task A observation 1. Did not recur in Tasks B or C.

**Decision.** Defer to Phase 2+.

**Rationale.** 1-run evidence, no Phase 2 gate (this is purely a component-agent behavior, and the finding's non-recurrence in B and C is a weak counter-signal). The fix is cheap — one sentence in the component agent CLAUDE.md stating "re-read `/shared/rules/*` unconditionally at the start of each task, including after role-switches within the same session" — but not urgent. Appropriate carry item when the component agent config is next opened (e.g., opportunistically during Fix-in-Phase-1 item 2).

### Finding 7 — `source: component:<name>` convention is under-specified

**What.** The events schema's `source` field admits `component:[a-z0-9][a-z0-9-]*` but does not specify whether `<name>` should be the bare repo name, the `<owner>/<repo>` string, or something else. WU 1.5 used the bare repo name (`component:orchestrator-api-sample`) by local decision.

**Evidence.** Task A observation 3.

**Decision.** Fix in Phase 1.

**Rationale.** Marginal but real Phase 2 gate. The PM and QA agents will also emit events with `source:` values (`pm:…`, `qa:…`), and the same underspecification will appear in each role's skill unless settled now. Fixing the convention — a 1-2 line clause in a shared rule or in the events schema's description fields — sets a consistent contract across all downstream roles at negligible cost. Leaving it open multiplies the ambiguity by each new role that comes online.

### Finding 8 — Coverage gate should mandate a rebuild before `--no-build`

**What.** In Task B, a coverage-gate investigation on `main` used `dotnet test --no-build` against stale binaries from the agent's own earlier edits (the stash covered source files but not `bin/`/`obj/`), producing a misleading coverage number that briefly suggested Task A had merged under threshold. Rebuilding cleared the confusion.

**Evidence.** Task B finding 2.

**Decision.** Defer to Phase 2+.

**Rationale.** 1-run red herring localized to Task B. No Phase 2 gate — the verification skill is component-agent-specific and does not propagate to the PM agent. The fix is a one-sentence note in [`verification/SKILL.md`](../../../agents/component/skills/verification/SKILL.md) ("always rebuild before coverage collection, especially when switching branches"), cheap to add anytime. Low-signal deferral.

## Fix-in-Phase-1 work plan

Five findings qualify for fix in Phase 1. Sequencing is suggested, not mandated — the items are independently landable.

1. **Event schema validation harness (Finding 1).** Build a shared script (e.g. `scripts/validate-event.py`) that takes a single JSON line and validates it against [`event.schema.json`](../../../shared/schemas/event.schema.json) using a conformant JSON Schema validator. Amend [`verify-before-report.md`](../../../shared/rules/verify-before-report.md) to require that agents pipe every event through this script before appending to `events/*.jsonl`. Update the component agent's event-emission patterns in CLAUDE.md and the relevant skills to invoke it.

2. **`source_version` runtime read (Finding 2).** Establish a shared convention that every event's `source_version` is read from `agents/<role>/version.md` at event-construction time, never cached by eye. Decide between: (a) a documented discipline in [`verify-before-report.md`](../../../shared/rules/verify-before-report.md) that the role's skill invokes a read before each emission, or (b) a tiny helper (e.g. `scripts/read-agent-version.sh`) the event-construction step calls. Option (a) is lighter; (b) is more robust. Pick at implementation time.

3. **PM issue-drafting "verify against repo" step (Finding 3).** Add a specification note — under [`/agents/pm/`](../../../agents/pm/) or in a shared rule, whichever is more discoverable — stating that the PM agent's issue-drafting skill must re-verify every claim about the target repo's state (files that exist or do not exist, test files, existing conventions, file contents) against the repo at draft time, and must log the verification command or file read in the issue-drafting transcript. This is a Phase 1 *specification* action; the Phase 2 WU that authors the PM skill then implements the requirement on day one.

4. **Spec-issue routing for specs-less features (Finding 4).** Add a one-sentence clause to [`escalation/SKILL.md`](../../../agents/component/skills/escalation/SKILL.md) §2 stating that when a feature has no product specs repo (walkthrough, bootstrap, or legacy features), the spec issue is filed against the orchestrator repository itself. Cross-reference the clause from [`features/README.md`](../../../features/README.md) if the features-registry README is a more discoverable surface.

5. **`source: component:<name>` convention (Finding 7).** Amend [`event.schema.json`](../../../shared/schemas/event.schema.json) or the shared rule that documents event authorship to specify that `<name>` is the bare component repository name (no owner prefix), matching the convention WU 1.5 used de facto. One-to-two lines of clarification; at implementation time, decide whether the schema's description field or a shared rule is the canonical home.

These five items are independent of each other and can be authored and landed in any order. Collectively they are the pre-freeze Phase 1 work; once they ship, the Phase 1 configuration is frozen and Phase 2 (PM agent automation) begins.

## Deferred to Phase 2+

Three findings defer. Each is tagged with where it will be picked up.

- **Finding 5 — `task_started.branch` as `string | null`.** Carry into the Phase 2+ per-type event payload schema work (under `/shared/schemas/events/` when that directory is introduced). First input into the `task_started` payload shape.
- **Finding 6 — shared-rules re-read at role-switch.** Carry into the next component agent CLAUDE.md revision, opportunistically during Fix-in-Phase-1 item 2 if it happens to touch the same file set, or separately at Phase 2 kickoff.
- **Finding 8 — coverage gate rebuild discipline.** Carry into the next edit of [`verification/SKILL.md`](../../../agents/component/skills/verification/SKILL.md), opportunistically — no dedicated work unit required.

Deferred items are not closed; they are scheduled. The forward work units that touch the relevant surfaces should consult this list at their start and absorb the applicable items.

## Loose ends

Both loose ends from Task C's log were closed before WU 1.6 began:

- [clabonte/orchestrator#5](https://github.com/clabonte/orchestrator/issues/5) — the spec issue filed by Task C — was closed with a comment framing it as a walkthrough artifact (no product decision required, since `FEAT-2026-0003` was a deliberately-ambiguous task to exercise the escalation path and will not be implemented).
- [Bontyyy/orchestrator-api-sample#7](https://github.com/Bontyyy/orchestrator-api-sample/issues/7) — the work-unit task — was closed with label `state:abandoned`, consistent with the "abandon walkthrough artifact" option outlined in Task C's inbox file.

No Task C follow-up is outstanding.

## Outcome

WU 1.6 concludes Phase 1's decision work. The walkthrough validated the v1 component agent across the three shapes the plan called for; the retrospective sorted the resulting findings into five Phase 1 fixes and three Phase 2+ defers, with explicit rationales and a concrete work plan. Phase 1 is ready to freeze once the five Fix-in-Phase-1 items ship; Phase 2 (PM agent automation) starts from the corrected configuration and the documented deferred list rather than from a cold re-discovery pass.

## Phase 1 freeze declaration

**Declared on 2026-04-22 as part of WU 1.12.**

All five Fix-in-Phase-1 items identified by the WU 1.6 triage have shipped to `main`:

| # | Finding | WU | PR |
|---|---|---|---|
| 1 | Event schema validation harness | WU 1.7 | [#8](https://github.com/clabonte/orchestrator/pull/8) |
| 2 | `source_version` runtime read | WU 1.8 | [#9](https://github.com/clabonte/orchestrator/pull/9) |
| 3 | PM issue-drafting "verify against repo" requirement | WU 1.9 | [#11](https://github.com/clabonte/orchestrator/pull/11) |
| 4 | Spec-issue routing for specs-less features | WU 1.10 | [#10](https://github.com/clabonte/orchestrator/pull/10) |
| 7 | `source: component:<name>` convention | WU 1.11 | [#10](https://github.com/clabonte/orchestrator/pull/10) |

With the five items landed, the component agent configuration is declared frozen for Phase 2 consumption:

> **Component agent v1.5.0 is the baseline Phase 2 depends on. Changes to this config during Phase 2 require architectural justification.**

The freeze applies to the operational surface of the component role: [`agents/component/CLAUDE.md`](../../../agents/component/CLAUDE.md), the three role skills (`verification/SKILL.md` v1.1, `pr-submission/SKILL.md` v1.1, `escalation/SKILL.md` v1.2), and the shared substrate the role consumes ([`shared/rules/*`](../../../shared/rules/), [`shared/schemas/*`](../../../shared/schemas/), [`shared/templates/*`](../../../shared/templates/)). The scripts added in WUs 1.7 and 1.8 ([`scripts/validate-event.py`](../../../scripts/validate-event.py), [`scripts/read-agent-version.sh`](../../../scripts/read-agent-version.sh)) are part of the frozen baseline because the shared rule and role skills reference them by path.

The freeze does **not** cover:

- The PM, QA, specs, config-steward, or merge-watcher role configs. Those remain Phase 0 v0.1 drafts (PM currently at v0.2.0 after WU 1.9's forward specification addition) pending their respective phases.
- The three findings deferred to Phase 2+ by this retrospective (Findings 5, 6, 8). They are scheduled carry-items, not part of the frozen surface.
- The `scripts/` directory as a whole — future scripts may land without contradicting the freeze, so long as they do not alter the behavior of the two scripts the component role depends on.

Phase 2 (PM agent automation) can now start. The Fix-in-Phase-1 items and their rationales above are the contract Phase 2 inherits.
