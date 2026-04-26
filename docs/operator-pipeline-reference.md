# Operator pipeline reference

Full-lifecycle reference for driving a feature from `drafting` through `done` across all four operational agents. The specs-agent entry point is covered in depth in [`operator-runbook.md`](operator-runbook.md); this document picks up at `planning` and covers everything downstream, plus reactive flows (inbox handling, escalations) that don't fit a linear walkthrough.

This is a reference, not a tutorial — read [`operator-runbook.md`](operator-runbook.md) first for context, then come back here when you need the details for a specific agent or flow.

## Lifecycle overview

The orchestrator's feature state machine is defined in architecture §6.1 and §6.3. Owners by transition:

| Transition | Owner | Trigger |
|---|---|---|
| `(new) → drafting` | Specs agent | feature-intake skill creates registry entry |
| `drafting → validating` | Specs agent | spec-validation skill, `validation_requested` |
| `validating → planning` | Specs agent | spec-validation skill, `validation_passed` |
| `planning → plan_review` | PM agent | task-decomposition skill produces a plan |
| `plan_review → generating` | Human | approves the plan |
| `generating → in_progress` | PM agent | first task issue opened (`first_task_opened` semantics) |
| `in_progress → done` | Merge watcher | last task PR merges; branch protection green |
| `* → blocked` | Any agent | escalation written to `/inbox/human-escalation/` |
| `blocked → <prior>` | Human | resolves the escalation |

Task-level transitions (`pending → ready → in_review → done`) are owned by the PM agent (`pending → ready` via dependency-recomputation), the component agent (`ready → in_review` via PR submission), and the merge watcher (`in_review → done`).

## Specs agent (drafting → planning)

See [`operator-runbook.md`](operator-runbook.md). Skills: feature-intake, spec-drafting, spec-validation, spec-issue-triage. This section covers only the reactive skill (spec-issue-triage) since the others are session-driven and live in the runbook.

### Spec-issue triage

When a downstream agent (component or QA) files a spec issue, it lands as a markdown file under `/inbox/spec-issue/` using [`shared/templates/spec-issue.md`](../shared/templates/spec-issue.md). The specs agent's [`spec-issue-triage`](../agents/specs/skills/spec-issue-triage/SKILL.md) skill is reactive: open a session, point the agent at the inbox file, and it triages.

The triage decision tree:

1. **Spec-content fix** (issue names a `/product/` file with a content problem) — agent edits the spec, re-runs validation, emits `spec_issue_resolved`.
2. **Generator-template fix** (issue names a `_generated/` file with a template problem) — agent files an issue against the generator project via `gh`, emits `spec_issue_routed`. The orchestrator does not fix generator templates directly; that's Phase 5 work.
3. **Spec error propagated through generation** (issue names `_generated/` but the root cause is in the spec) — agent treats it as case 1, fixes the spec, regenerates. This is the subtlest case; case-(c) in the skill.
4. **Ambiguous** — agent escalates to the human via `/inbox/human-escalation/`.

Inbox files move to `/inbox/spec-issue/processed/` after triage; they're never deleted.

> **Note (Phase 5 carry).** The spec-issue-triage skill was authored in WU 4.5 but never exercised at runtime during Phase 4 — no spec issue was filed during the walkthroughs. Treat the first real-project triage as a smoke test; report any contract bugs as Phase 5 inputs.

## PM agent (planning → generating)

The PM agent ([`agents/pm/CLAUDE.md`](../agents/pm/CLAUDE.md), v1.6.3 frozen) picks up at `planning` and converts the validated spec into a task graph plus open GitHub issues. Skills:

- **task-decomposition** — reads the feature registry and `/product/` specs, produces a task graph with `pending`/`ready` states, types (`implementation`, `qa_authoring`, `qa_execution`, `qa_curation`, `qa_regression`), dependencies, and worked-example WU prompts. Emits `feature_state_changed(planning → plan_review)`.
- **plan-review** — presents the plan for human approval. The human's `approve` answer flips state to `generating` and unblocks issue creation.
- **template-coverage-check** — sanity-checks that the plan's task types map to the available skill/template surface. Operator-directed; entry condition expects `state == planning` (Phase 3+4 finding F3.27/F4.7 — known low-severity friction).
- **issue-drafting** — creates GitHub issues in the involved component repos using [`shared/templates/work-unit-issue.md`](../shared/templates/work-unit-issue.md). Threads the correlation ID through the title (`[FEAT-YYYY-NNNN T01]`), branch name suggestion, body, and labels. Emits `task_created` events.
- **dependency-recomputation** — sole writer of task-level `pending → ready`. Re-runs whenever a task's dependencies' merge state changes (today: human-driven; Phase 5 plans a merge-watcher to automate this).

### Driving a PM session

Open a Claude Code session with `agents/pm/CLAUDE.md` as the role prompt. Tell it: *"Pick up FEAT-YYYY-NNNN."* Expect:

1. Agent reads the registry, confirms `state: planning`, reads `/product/` specs.
2. Agent proposes a task graph; review the proposed types and dependencies.
3. Agent invokes plan-review for your approval. If you approve, state flips to `generating`.
4. Agent invokes issue-drafting to open issues in component repos. Watch the agent's `gh issue create` output and verify each issue lands.
5. Agent recomputes dependencies; the entry tasks (no upstream deps) flip to `ready`. The first task opened triggers `generating → in_progress`.

### PM gotchas

- **`task-decomposition` cardinality wording.** F3.17 / F4.6: the skill's parsing of `## Scope` cardinality clauses can miss narrative specs without `### Behavior` headings. If the agent proposes a task count that surprises you, re-check your spec's scope language (the spec-drafting skill's F3.32 absorption is the upstream defense).
- **Issue path bug F4.10.** The issue-drafting skill's worked example referenced `product/features/test-plans/` instead of `product/test-plans/` once during Phase 4. The QA agent recovered (schema-guided), but if you see a generated issue body with `product/features/test-plans/`, edit the issue manually and note it.
- **`autonomy_default: review` is the safe default.** Even with `auto`, the PM agent gates plan-review on a human; `review` extends that gate to per-task issue creation. Use `review` for the first 2–3 real-project features.

## Component agent (ready → in_review, per repo)

The component agent ([`agents/component/CLAUDE.md`](../agents/component/CLAUDE.md), v1.5.2 frozen) runs **once per component repo** — open a separate Claude Code session per repo, with that repo as the working directory. Skills:

- **verification** — pre-PR check: build passes, tests pass, lints pass, no `/business/` writes, no override-registry violations. Phase 3 WU 3.8 added a build step before tests; if you see test runs without prior builds, the skill is being skipped.
- **pr-submission** — opens a PR via `gh pr create` with the work-unit body, threads the correlation ID through the title and branch name, links the issue. Emits `task_state_changed(ready → in_review)`.
- **escalation** — files a spec issue (when the spec is ambiguous or contradicts itself) or a human escalation (when the work crosses never-touch boundaries or hits autonomy gates).

### Driving a component session

Open Claude Code with the **component repo as cwd** and `agents/component/CLAUDE.md` as the role prompt. Tell it: *"Pick up issue #N in this repo."* Expect:

1. Agent reads the issue body, the linked feature registry, and the relevant `/product/` specs.
2. Agent confirms the task is `ready` (not `pending`) and that no upstream override conflicts exist.
3. Agent writes hand-written code, **never** in `_generated/` paths or any directory listed in [`shared/rules/never-touch.md`](../shared/rules/never-touch.md).
4. Agent runs verification (build, tests, lints).
5. Agent invokes pr-submission. PR opens; task transitions to `in_review`.

The merge watcher (a GitHub Action; Phase 5 will formalize it) handles `in_review → done` once branch protection is green.

### Component gotchas

- **One agent per repo, no cross-repo writes.** A component agent never reaches into another component repo; cross-repo work is decomposed at PM time.
- **Overrides are the component agent's exclusive write surface.** The agent reconciles `/overrides/` for its repo only, per [`shared/rules/override-registry.md`](../shared/rules/override-registry.md). Specs and QA agents do not touch overrides.
- **Branch protection settings can block the regression fallback** (F4.15). If you induced a regression to exercise the qa-regression loop and find the component agent can't push the fix-branch, check that branch protection allows your PR-submission flow on that repo.
- **`gh` permission scopes** can block label edits or pushes (F4.8). Verify `gh auth status` shows `repo` and `workflow` scopes before the first session.

## QA agent (per task)

The QA agent ([`agents/qa/CLAUDE.md`](../agents/qa/CLAUDE.md), v1.5.2 frozen) handles four task types, each with its own skill and its own session pattern:

- **qa-authoring** — converts a feature's acceptance criteria into a test plan under `/product/test-plans/<feature-slug>.yaml`, validating against [`test-plan.schema.json`](../shared/schemas/test-plan.schema.json). Each `test_id` has `covers`, `commands`, `expected`. Authoring is *collapse-only* on cardinality (F3.32 / F3.17): the skill never expands beyond the spec's stated count; only collapses with explicit justification.
- **qa-execution** — runs the test plan against the deployed component(s). Operator-directed (the skill's Rule 1 says `qa_execution never auto`). Captures observed-vs-expected per test, emits `qa_execution_completed` (clean) or `qa_execution_failed` (with failure detail).
- **qa-regression** — on `qa_execution_failed`, files a *new* implementation task back to the PM agent's task graph (Q4 cross-attribution invariant: never write labels or state to the failed implementation task). When the regression fix lands and re-execution passes, emits `qa_regression_resolved` + `escalation_resolved`.
- **qa-curation** — promotes test cases to a long-running regression suite. Reactive; runs at human direction.

### Driving a QA session

Open a Claude Code session with `agents/qa/CLAUDE.md` as the role prompt. Tell it: *"Pick up `qa_authoring` task #N for FEAT-YYYY-NNNN."* (or `qa_execution`, etc.). Expect:

1. Agent reads the task, the feature registry, the spec, and any existing `/product/test-plans/` artifact.
2. For authoring: agent produces the test plan, validates schema, opens a PR.
3. For execution: agent runs each test command, captures output, compares to `expected`, reports the per-test verdict.
4. Agent emits the appropriate task lifecycle event.

### QA gotchas

- **`dotnet test --no-build` false-greens (F4.13).** If your component repo uses .NET, ensure the qa-execution skill's invocation builds first. Phase 4 caught this in Feature 2; the underlying SKILL.md fix is on the QA frozen surface (Phase 5+).
- **Runtime-port discovery.** The qa-authoring skill's port-discovery discipline (Phase 3 WU 3.9) means tests should not hard-code ports; if you see hard-coded ports in a generated test plan, that's a bug, not a feature.
- **Q4 invariant audit.** During a regression cycle, verify the QA agent files a *new* implementation task — it must not edit the original failing implementation task's labels, state, or body. The retrospective (Phase 4 §"Q4 cross-attribution audit") shows the audit pattern.
- **First-pass clean is normal.** If qa-execution passes on first pass, that's the happy path. The qa-regression skill is for the unhappy path; you do not need to manufacture a regression to exercise it on every feature.

## Inbox handling

The orchestration repo's `/inbox/` has two compartments:

- `/inbox/human-escalation/` — anything an agent escalates to you. Read these promptly; the feature is in `blocked` state until you respond. Escalation file format: [`shared/templates/human-escalation.md`](../shared/templates/human-escalation.md).
- `/inbox/spec-issue/` — spec issues filed by component or QA agents. Triaged by the specs agent (see "Spec-issue triage" above). After triage, files move to `/inbox/spec-issue/processed/`.

You should not need to write to `/inbox/` directly. If an agent has missed a beat and you find yourself wanting to drop a file in `/inbox/`, that's a signal to either restart the agent's skill or escalate via the existing protocol.

## Escalations

Per [`shared/rules/escalation-protocol.md`](../shared/rules/escalation-protocol.md), every agent escalates by writing a file to `/inbox/human-escalation/` and transitioning the feature to `blocked`. Common reasons (see each agent's `## Role-specific escalation` section for the full list):

- `spec_level_blocker` — the agent can't proceed without a spec change or human adjudication.
- `override_expiry_needs_review` — an override conflicts with the work and the human must decide.
- `autonomy_requires_approval` — the feature's autonomy gate triggered.
- `spinning_detected` — the agent has retried beyond the threshold (3 cycles, wall-clock, or token budget).

To resolve an escalation: read the file, take the named action (edit a spec, retire an override, approve, etc.), then **emit an `escalation_resolved` event manually** if the agent's flow doesn't do it automatically. The feature transitions out of `blocked` to its prior state when you do.

## Working with multiple sessions

A single feature can have several concurrent sessions: one specs (during drafting), one PM (during planning/generating), N component (one per involved repo), and several QA (one per active QA task). Operator hygiene:

- **Each session has one role.** Do not switch role mid-session by reloading a different `CLAUDE.md`. Open a new session.
- **Re-read the registry between sessions.** Multi-session features accumulate state; agents do this automatically per role-switch-hygiene, but it's worth confirming.
- **One feature per session.** Multi-feature sessions confuse correlation-ID threading.
- **Logs are append-only.** `/events/FEAT-YYYY-NNNN.jsonl` is the source of truth for what happened. Do not edit historical events; if a bad event landed, write a corrective event with a clear payload, not a redaction.

## Known carry items affecting operations

These are documented friction points carried into Phase 5+ that you may encounter on a real project. None block the pipeline; each has a named home.

| Carry | Symptom | Workaround |
|---|---|---|
| F4.1 | Specfuse validation simulated, not run | Install the validator CLI before Step 4 of the runbook |
| F4.2 | `/tmp` writes blocked in some sandboxes | Set `$TMPDIR` to a writable path |
| F4.7 / F3.27 | template-coverage-check expects `state == planning` | Operator-directed invocation; not a blocker |
| F4.8 | `gh` permissions blocked label/push | Verify `gh auth status` shows `repo` + `workflow` scopes |
| F4.10 | Issue body mis-references `product/features/test-plans/` | Edit issue body manually if observed |
| F4.13 | `dotnet test --no-build` false-greens | Ensure build runs before tests in qa-execution |
| F4.15 | Branch protection blocked regression-fix push | Adjust branch protection if exercising induced regressions |
| F3.11 | Long SKILL.md files exceed 25k token read limit | Read in chunks; the agent handles this internally |
| F3.33 | `tail -1 log \| json.tool` fails on blank trailing line | Use `grep -v '^$' log \| tail -1 \| json.tool` |
| Phase 5 carry | spec-issue-triage runtime path unvalidated | Treat first real triage as a smoke test |

Full carry list and dispositions: [`walkthroughs/phase-4/retrospective.md`](walkthroughs/phase-4/retrospective.md) §"Carry list for Phase 5 inputs".

## Reference

- Architecture: [`orchestrator-architecture.md`](orchestrator-architecture.md)
- Vision: [`orchestrator-vision.md`](orchestrator-vision.md)
- Implementation plan: [`orchestrator-implementation-plan.md`](orchestrator-implementation-plan.md)
- Specs runbook: [`operator-runbook.md`](operator-runbook.md)
- Per-role configs: [`/agents/specs/`](../agents/specs/), [`/agents/pm/`](../agents/pm/), [`/agents/component/`](../agents/component/), [`/agents/qa/`](../agents/qa/)
- Shared substrate: [`/shared/`](../shared/)
- Walkthrough logs (worked examples): [`walkthroughs/phase-1/`](walkthroughs/phase-1/), [`walkthroughs/phase-2/`](walkthroughs/phase-2/), [`walkthroughs/phase-3/`](walkthroughs/phase-3/), [`walkthroughs/phase-4/`](walkthroughs/phase-4/)
