# Phase 1 walkthrough — Task B log

## Identity

- **Walkthrough:** Phase 1, WU 1.5
- **Task:** B (moderate)
- **Correlation ID:** `FEAT-2026-0002/T01`
- **Component repo:** [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample)
- **Started:** 2026-04-21
- **Operator:** @Bontyyy (playing PM agent; Claude as co-pilot for drafting and picking the task shape, as component agent for execution)
- **Component agent version at execution:** 1.2.0
- **Status:** Agent work complete, PR awaiting human merge

## Objective

Run a moderate-difficulty realistic task end-to-end through the v1 component agent configuration, producing a mergeable PR that spans multiple files and requires genuine design judgment within tight constraints. Per the WU 1.5 acceptance criterion 2: _"spans 2 files, requires writing a new test, involves some genuine design judgment within tight constraints. Produces a mergeable PR possibly requiring one round of human PR review feedback."_

The 2-files floor was taken as the spirit of "more than trivial" rather than a hard cap — Task A already touched 2 files, so moderate must meaningfully exceed that shape.

## Task selection (PM role)

Two candidates were pre-identified as moderate shapes against the sample repo:

1. **`DELETE /widgets/{id}`** — adds an endpoint, a repository port method, a service method, and a controller action. Spans 4+ files, design judgment bounded to the `204` vs `404` choice on an unknown id.
2. **`GET /widgets` listing** — same file shape, but the design question is pagination, which opens multiple independent decisions (no pagination vs offset-limit vs cursor, default limit, max limit, ordering, empty-list semantics).

DELETE was chosen. The two reasons it wins on the "moderate" criterion:

- The design judgment is **bounded**. Two defensible options with a clear tradeoff vocabulary (RFC 9110 idempotence vs strict existence semantics). The agent can actually exercise judgment inside a spec-able boundary.
- GET listing at the same file count would either underspecify the design question (ship without pagination, punt on the interesting part) or overspecify it (turn a moderate task into a feature on its own). Neither is "moderate with tight constraints".

An additional consideration: DELETE adds a new method on both `IWidgetRepository` (port) and `InMemoryWidgetRepository` (adapter), stretching the port/adapter pattern rather than only the service layer. GET listing would mostly exercise a read-side shape the service already has.

## Feature registry minting decision

FEAT-2026-0001 was "widget quantity ceiling" — a single narrow validation rule. Task B adds a new HTTP verb on the same resource. These are categorically different capabilities. The walkthrough therefore minted **FEAT-2026-0002 — Widget deletion** as a new feature, with `T01` as its sole task, rather than appending T02 to FEAT-2026-0001.

This matches how the PM agent will mint features in normal operation: one feature = one coherent user-facing capability, not a catch-all bucket of nearby changes. Cramming DELETE into `FEAT-2026-0001` would misrepresent feature scope for any downstream analysis that groups events by feature ID.

Registry entry: [`features/FEAT-2026-0002.md`](../../../features/FEAT-2026-0002.md).

## Issue filing (on component repo)

- **Issue:** [Bontyyy/orchestrator-api-sample#5](https://github.com/Bontyyy/orchestrator-api-sample/issues/5)
- **Title:** `[FEAT-2026-0002/T01] Add DELETE /widgets/{id} endpoint`
- **Labels at creation:** `state:ready`, `type:implementation`, `autonomy:review`

The initial issue body followed the [`work-unit-issue.md`](../../../shared/templates/work-unit-issue.md) template: five mandatory sections, YAML frontmatter carrying correlation ID / task type / autonomy / repo / deps / generated surfaces. The body spec'd **policy A (idempotent, 204 on unknown id)** as the preferred design decision and asked the agent to document the tradeoff in the PR description. Labels were already provisioned during Task A.

**The initial issue body carried a factual error that became the friction finding of this run.** See "Friction surfaced" below.

## Component agent execution

### Pickup

- `ready → in_progress` flipped on issue #5 via `gh issue edit --remove-label state:ready --add-label state:in-progress`.
- Feature branch cut on sample repo: `feat/FEAT-2026-0002-T01-widget-delete-endpoint` from `main`.
- `task_started` event emitted to [`events/FEAT-2026-0002.jsonl`](../../../events/FEAT-2026-0002.jsonl) at `2026-04-21T20:36:03Z`.

### Implementation

- **Commit:** `25a7d40` on the feature branch (message carries mandatory `Feature: FEAT-2026-0002/T01` trailer per [`pr-submission/SKILL.md`](../../../agents/component/skills/pr-submission/SKILL.md)).
- **Files touched (6, not the originally-spec'd 5 — see friction finding):**
  - `src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs` — 1 new method signature.
  - `src/OrchestratorApiSample.Api/Persistence/InMemoryWidgetRepository.cs` — 1 new method implemented via `ConcurrentDictionary.TryRemove`.
  - `src/OrchestratorApiSample.Application/Services/WidgetService.cs` — 1 new `DeleteAsync` method mirroring `GetByIdAsync`'s input-validation shape.
  - `src/OrchestratorApiSample.Api/Controllers/WidgetsController.cs` — 1 new `[HttpDelete("{id}")]` action returning `NoContent` on success and `BadRequest` on `ValidationException`.
  - `tests/OrchestratorApiSample.Tests/WidgetServiceTests.cs` — 3 new tests (known-id delegation, unknown-id idempotence, blank-id theory).
  - `tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs` — 3 new tests (existing-id returns NoContent and widget is gone, unknown-id returns NoContent, blank-id returns BadRequest). Added mid-task after coverage gate failure; see friction finding.
- No `_generated/` paths touched (none exist in the sample repo).

### Design decision narrative

Policy **A (idempotent, 204 always)** was implemented as spec'd. Three reasons are documented in the PR description, distilled:

- REST idempotence is stronger with A — repeated `DELETE` on the same id produces the same observable result every time, matching RFC 9110.
- Less information leakage on arbitrary id probes — a strict 404 would let a caller distinguish "id exists but I can't delete it" from "id does not exist", a minor but real side channel on a future-authorized resource.
- The repository contract stays simpler — `DeleteAsync` returns `Task` with no payload, so it cannot signal "not found", which removes a failure-mode surface the service would otherwise collapse back into silent success anyway.

The PR description explicitly names policy B as reversible on reviewer request, noting that the implementation change would be mechanical (`TryRemove`'s bool return surfaced through the stack, controller maps false → `NotFound()`). This is the "one round of human PR review feedback" shape the WU 1.5 moderate criterion calls for.

### Verification (six gates + per-task)

All six mandatory gates and all five per-task verification commands passed on **cycle 1 after the coverage-gate-induced scope correction** (see friction finding). No escalation condition triggered; no spinning. Evidence as stored in the `task_completed` event payload:

| Gate | Status | Evidence |
|---|---|---|
| `tests` | pass | 29/29 passed (21 existing + 5 new service + 3 new controller) |
| `coverage` | pass | line coverage 1.0000, branch coverage 1.0000 (86/86 lines, 14/14 branches; threshold 0.90) |
| `compiler_warnings` | pass | 0 warnings under `/warnaserror` |
| `lint` | pass | `dotnet format --verify-no-changes` clean |
| `security_scan` | pass | 0 High, 0 Critical advisories |
| `build` | pass | Release build succeeded, 0 warnings |

Per-task verification (from amended issue body):

| Command | Status | Evidence |
|---|---|---|
| `dotnet test --filter "FullyQualifiedName~WidgetServiceTests"` | pass | 22/22 passed |
| `dotnet test --filter "FullyQualifiedName~WidgetsControllerTests"` | pass | 7/7 passed |
| `grep -F "HttpDelete" WidgetsController.cs` | pass | match found |
| `grep -F "DeleteAsync" IWidgetRepository.cs` | pass | match found |
| `grep -F "TryRemove" InMemoryWidgetRepository.cs` | pass | match found |

### PR

- **URL:** [Bontyyy/orchestrator-api-sample#6](https://github.com/Bontyyy/orchestrator-api-sample/pull/6)
- Label rotated `state:in-progress → state:in-review` on issue #5 after PR open.
- CI `verification gates` check: **pass** (49s) — confirmed the local six-gate verification aligns with branch-protection enforcement.
- `task_completed` event emitted to the event log at `2026-04-21T20:46:28Z` with full six-gate evidence + per-task verification payload, per the shape in [`verification/SKILL.md`](../../../agents/component/skills/verification/SKILL.md) §"Reporting".

### Merge

- _Pending human approval and merge of PR #6. Per architecture §10, merge is branch-protection-gated; component agent does not self-merge._
- After merge: human rotates issue #5 label to `state:done` manually (merge watcher gap carried over from Task A).

## Friction surfaced

### Finding 1 — PM-authored issue body carried a factually wrong scope exclusion (resolved mid-task)

**What happened.** The initial issue body included this bullet under "Out of scope":

> Controller-level tests. Out of scope by symmetry with the other widget endpoints, which also only have service-level tests in this repo.

The symmetry claim was **false**. [`tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs`](https://github.com/Bontyyy/orchestrator-api-sample/blob/main/tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs) already existed on main and covered `Create` and `GetById` at the controller level (the asymmetry was between the two verbs in the service tests vs the two verbs in the controller tests, which both had test files of their own). The PM author (Claude in co-pilot role) had read the test directory inattentively during issue drafting and missed the controller test file.

**How it surfaced.** The component agent implemented the 5-file-spec'd change. On gate 2 (coverage), line-rate dropped from 1.0000 to 0.8604 — below the 0.90 threshold — because the new `WidgetsController.Delete` action and `InMemoryWidgetRepository.DeleteAsync` were not exercised by any test. The agent investigated by re-running coverage on `main` (`0.8604` on stale binaries, `1.0000` on a fresh build — a separate red herring covered below), then inspecting the test directory and discovering `WidgetsControllerTests.cs`.

**Resolution path chosen.** Three options were on the table:

- **A. Escalate `spec_level_blocker`.** The issue body is internally inconsistent (demands 90% coverage while excluding the tests that would achieve it). Correct per the escalation protocol, but a heavy response to a mechanical error the agent can verify in one grep.
- **B. Follow the issue body literally.** Fail coverage → enter spinning loop → escalate at 3 cycles. Maximally wasteful.
- **C. Amend the issue body (PM role) and add the controller tests (component role).** Documents the friction on the artifact itself, fixes scope to match repository reality, keeps the work moving. Chosen.

The issue body was amended via `gh issue edit --body-file` with an explicit dated amendment block naming the mistake and revising acceptance criterion 6 and the verification command list to include controller tests. The three controller tests were added in the same implementation commit.

**Why this matters beyond the walkthrough.** In normal operation, PM would be a separate agent from the component agent. A component agent encountering this exact shape could not reach option C unilaterally — it would have to escalate (option A) because it does not own the issue body. The walkthrough collapses both roles on the same human-plus-Claude pair, which let us correct the scope in-flight. But the finding is: **PM agent's issue-drafting skill must verify claims about existing repo state, not assert them from memory of the repo's convention.** A fix-in-Phase-1 candidate for the WU 1.6 retrospective is to add a "verify against repo state" checklist item to the PM issue-drafting skill before the PM-agent role is built.

### Finding 2 — `dotnet test --no-build` against stale binaries gave misleading coverage on main

**What happened.** During friction-finding 1's investigation, the agent stashed its edits, checked out `main`, and re-ran `dotnet test --no-build --collect:"XPlat Code Coverage"` to confirm main's baseline. That first run reported `line-rate="0.8604"` — which appeared to say Task A had been merged with coverage below threshold (contradicting Task A's log and PR #4's CI log, both of which reported 1.0000).

**Root cause.** The `--no-build` flag skipped rebuilding, so the test run executed the binaries still compiled from the agent's Task B edits (before the stash). The stash covered source files but not `bin/`/`obj/`.

**How it was confirmed.** Running `dotnet build` explicitly on main before the coverage collection gave `line-rate="1"` (68/68), which matches Task A's CI output. The 0.8604 in the stale-binaries case was the *correct* post-edit Task-B coverage — the confusion was only that the binary under test did not match the source on disk.

**Takeaway.** Component agent coverage-gate runs should be preceded by a build to guarantee `--no-build` is safe. Or, when re-establishing baseline on a different branch, drop `--no-build`. Candidate for the verification skill's guidance — a single "always rebuild before coverage" sentence would have saved the detour.

### Finding 3 — `source_version` drift risk (carried over from Task A)

Still present. The agent again hard-coded `"1.2.0"` in both the `task_started` and `task_completed` events after reading `agents/component/version.md` by eye. Task A's observation 4 remains open; this is the second run where it applied.

### Finding 4 — event schema validation still not run (carried over from Task A)

Events were constructed by hand against the schema for both transitions. Task A's observation 2 remains open. This run had enough structural complexity in the `task_completed` payload (five per-task verification entries, six gate entries) that manual construction was visibly more error-prone than Task A's simpler payload.

## Config / skill changes prompted by this run

**None required for agent correctness on the happy path.** The v1 component agent configuration produced a passing implementation. However, the WU 1.6 retrospective candidate list grows:

- **PM issue-drafting skill** needs a "verify claims about repo state against the repo" step before publication (Finding 1).
- **Component verification skill** could benefit from a "rebuild before coverage" note (Finding 2).
- **Observations 2 and 4 from Task A** (event schema validation, `source_version` auto-read) remain and had material impact on this run's authoring effort (Findings 3, 4).

These are all candidates for triage, not blocking changes to ship on this branch.

## Outcome

Task B succeeded end-to-end with one recoverable mid-task scope correction, zero failed-verification cycles once scope was correct, and one round of in-flight PM amendment (played by the operator). The v1 component agent configuration held up under a six-file moderate change with genuine design judgment; the friction observed was in the PM-role artifact, not the component-role execution.

Combined with Task A's happy-path pass, the walkthrough has now validated the v1 component agent on:
- A trivial pattern-mirror task (Task A: 2 files, 0 design judgment, 1 cycle).
- A moderate multi-file task with bounded design judgment (Task B: 6 files, 1 design call documented in PR, 1 cycle after scope correction).

Task C (edge case) remains. Candidates: generated-code override exercise (N/A on sample repo), spec ambiguity → `blocked_spec` escalation, or spinning self-detection trigger. The most-useful-next-test remains an escalation-path exercise, since the two happy-path shapes are now covered.
