# Phase 2 walkthrough — Feature 2 log (edge case: plan-review re-ingest stress)

## Identity

- **Walkthrough:** Phase 2, WU 2.7
- **Feature:** `FEAT-2026-0005` — widget bulk operations (bulk import + CSV export, cross-repo)
- **Shape chosen:** edge case — **plan-review re-ingest stress**. Per WU 2.7 acceptance criterion 2, the operator picks one of three candidates at walkthrough time; this walkthrough selected re-ingest stress because it exercises the densest structural-validation surface in any Phase 2 skill (schema round-trip, cycle check, orphan check, assigned-repo sanity, task-ID uniqueness, correlation-ID immutability, prose-body preservation) and because the edit stream comes from real human decisions rather than synthetic inputs.
- **Started:** 2026-04-22
- **Operator:** @Bontyyy
- **Orchestration model:** Opus 4.7 (this session — note-taking, commits, subagent invocation, human editor role)
- **PM-agent model:** Sonnet 4.6 (instantiated per skill invocation via subagent)
- **Component repos:**
  - [Bontyyy/orchestrator-api-sample](https://github.com/Bontyyy/orchestrator-api-sample) — .NET
  - [Bontyyy/orchestrator-persistence-sample](https://github.com/Bontyyy/orchestrator-persistence-sample) — Python
- **PM agent version at execution:** 1.0.0
- **Status:** in progress

## Inputs from Feature 1

Setup artifacts produced during Feature 1 and merged into main (PR #20) are inherited as-is:
- `Bontyyy/orchestrator-persistence-sample` exists, 15 labels provisioned, `.specfuse/{verification,templates}.yaml` in place.
- `Bontyyy/orchestrator-api-sample` carries `.specfuse/templates.yaml` (merged as PR #8).
- `docs/walkthroughs/phase-2/` directory exists.
- `features/FEAT-2026-0005.md` drafted with `state: planning`, `task_graph: []`, two behaviors (bulk import + CSV export), explicit `## Task routing` whose entries are deliberately debatable (Behavior 1 routes to BOTH repos — "one implementation task per repo"; Behavior 2 routes to api-only and reuses existing persistence).

The deliberately-debatable routing is the setup for realistic plan-review edits later: the PM agent will produce an initial task graph from the routing section, and the human-operator (playing its editor role) will make non-trivial structural changes that the re-ingest skill must handle faithfully.

## Planned edit stream (for reference — populated by walkthrough execution)

Five edits are planned to stress the re-ingest skill in distinct ways. Each is logged with (a) what was edited, (b) what the re-ingest skill did, (c) what validated or escalated, (d) any observation.

1. **Edit A — Structural: retarget a task across repos.** Move one implementation task from one `assigned_repo` to the other. Stresses schema validation + assigned-repo sanity.
2. **Edit B — Structural: add a task T0N.** Insert a new task in the middle of the graph. Stresses task-ID uniqueness and dep-graph integrity.
3. **Edit C — Structural: introduce a dependency cycle.** Temporarily make the graph cyclic. Expect `spec_level_blocker` escalation.
4. **Edit C-fix — Structural: remove the cycle.** Revert edit C. Expect clean re-ingest.
5. **Edit D — Prose-only: tighten a work unit prompt.** No YAML block change. Expect idempotent no-op re-ingest.
6. **Edit E — Structural: remove the task added in B.** Tests task removal and dep-graph consistency when a task that other tasks depend on is removed.

Whether all 5-6 edits run depends on friction surfaced mid-walkthrough; honest-log discipline means stopping early if the signal is clear and noting why.

## Skill invocations

All invocations use fresh Sonnet 4.6 subagents with full role-switch hygiene (re-read `/shared/rules/*`, `agents/pm/CLAUDE.md`, the specific skill). Observations per invocation, then a consolidated findings section at the end.

### Step 1 — task-decomposition on FEAT-2026-0005

- **Invoked by:** orchestration session (Opus 4.7) via `Agent` subagent, `model=sonnet`, fresh context.
- **Output:** 8-task graph (larger than Feature 1's 5 tasks):

| ID | Type | Repo | `depends_on` |
|---|---|---|---|
| T01 | implementation | persistence-sample | `[]` |
| T02 | implementation | api-sample | `[T01]` |
| T03 | implementation | api-sample | `[]` |
| T04 | qa_authoring | api-sample | `[]` |
| T05 | qa_execution | api-sample | `[T02, T03, T04]` |
| T06 | qa_authoring | api-sample | `[]` |
| T07 | qa_execution | api-sample | `[T02, T03, T06]` |
| T08 | qa_curation | api-sample | `[T05, T07]` |

Validation evidence: all 5 Step-7 checks PASS; `task_graph_drafted` event emitted, validator exit 0.

#### Findings

**F2.1 — Skill ambiguity F1.9 resolves the OTHER way in Feature 2.** In F1, the subagent produced 1 `qa_authoring` + 1 `qa_execution` (following the feature's `## Scope` "one authored test plan covering both behaviors"). In F2, the subagent produced 2 `qa_authoring` + 2 `qa_execution` (one per behavior, strict Step-4 rule reading). The feature scopes are analogous — both say "one authored test plan" — but the subagents diverged in interpretation. **This confirms F1.9 is a real ambiguity**, not a one-off. The skill rule and the feature scope constraint genuinely conflict in how they're read. High-priority retrospective item.

**F2.2 — Cross-behavior coupling in qa_execution `depends_on`.** Step 5 rule 3 says qa_execution depends on "all implementation tasks on the same repo as itself". T05 (Behavior 1 QA) and T07 (Behavior 2 QA) both depend on T02 AND T03 — even though each behavior is independent. So T05 cannot start until T03 (Behavior 2 impl) is also done. The subagent noted this feels "overconstrained" — the whole-repo-gate reading vs. a same-behavior-gate reading. Related to F1.10 but manifesting differently here because F2 has two distinct behaviors on the same repo.

### Step 2 — required_templates population + template-coverage-check

Human populated `required_templates` on T01, T02, T03, T04, T06 (tokens chosen to match what the two repos' `.specfuse/templates.yaml` declare).

template-coverage-check subagent ran clean: all 8 required tokens matched across 2 declarations. One `template_coverage_checked` event emitted, validator exit 0.

#### Findings

**F2.3 — Skill contract violation: template-coverage-check subagent auto-populated `required_templates`.** The skill explicitly scopes this out: "populating `required_templates` on task graph entries — the task-decomposition skill (WU 2.2) does not set this field at v1. The human adds it during drafting or during `plan_review` re-ingest." But when the subagent found `required_templates` absent, it **materialized the field itself** based on task-routing heuristics rather than escalating or failing. This is a well-meaning "helpfulness" violation — the skill's out-of-scope clause is not sticky enough to prevent a Sonnet 4.6 session from filling in the field. In my orchestration session I had also tried to populate via direct Edit (which failed due to "file modified since read"), but the subagent succeeded independently. **Critical retrospective input:** add a "DO NOT populate this field even if absent; escalate `spec_level_blocker`" clause to the skill, or add a pre-flight check that explicitly errors if `required_templates` has never been populated at least once.

### Step 3 — plan-review Phase A

Standard Phase A. Plan file emitted at `/features/FEAT-2026-0005-plan.md`, feature state flipped `planning → plan_review`, `plan_ready` emitted. 3 events in log.

#### Findings

**F2.4 — Subagent misread the schema on `required_templates`.** The subagent reported in friction: "the feature-frontmatter schema does not declare `required_templates` as an allowed field on task objects". This is incorrect — WU 2.6 added the field to the schema's task `$defs` with a kebab-case pattern constraint. The subagent still copied the field verbatim as instructed, so no harm — but the misread is a signal that even the current schema structure (plus the Phase 2 additive history) is hard to trace for a fresh Sonnet session. **Retrospective input:** consider adding a top-of-file comment in the schema naming which fields have been added in which WU.

### Edit stream (5 distinct stress tests on Phase B re-ingest)

Each edit invoked a fresh Sonnet 4.6 subagent running plan-review Phase B. Sequential, not parallel.

#### Edit A — Retarget T03 from api-sample to persistence-sample (structural)

Human narrative: reconsider whether CSV generation logic lives closer to persistence. `assigned_repo` and `required_templates` both updated in the plan file's YAML block.

- **Phase B re-ingest result:** schema PASS, cycle PASS, orphan PASS, assigned-repo sanity PASS (`persistence-sample ∈ involved_repos` — was already there because T01 was there), task-ID uniqueness PASS, correlation-ID immutability PASS. Frontmatter updated. No event.
- **Finding F2.5:** re-ingest does NOT re-run template-coverage-check after `assigned_repo` + `required_templates` retarget. If the human had retargeted `assigned_repo` but not updated `required_templates` to match the new repo's declared tokens, the `required_templates` would reference the wrong repo's vocabulary — structurally valid (tokens still pass pattern), but semantically incorrect. Template-coverage-check would catch it **only if re-invoked**; Phase B does not chain to template-coverage-check. **Design gap** — retrospective should decide whether Phase B should chain to coverage check on detect-repo-change, or whether this remains a human-discipline concern.
- **Finding F2.6:** re-ingest is silent (no event), so the audit trail for a human review session with 10 edits is only the git history on two files. The `human_escalation` events from any escalations remain in the log; successful re-ingests leave no trace. For a high-velocity review, this is under-observable.

#### Edit B — Add task T09 (implementation, persistence-sample, `required_templates: [migration]`) (structural)

- **Phase B result:** schema PASS, all 5 structural checks PASS, frontmatter now 9 tasks. No event.
- **Finding F2.7 (most important of F2):** Phase B **does not flag that template-coverage-check should be re-run** when a task with a new `required_templates` set is added. The `migration` token happens to be declared in persistence-sample's `templates.yaml`, so in this instance the actual coverage is fine — but Phase B doesn't know, doesn't check, doesn't warn. If the human had added T09 with `required_templates: [migration-rollback]` (undeclared), the re-ingest would have accepted it structurally, and the gap would surface only at generation time. **Critical retrospective input** — at minimum, Phase B's response should include a warning ("task_graph changed; recommend re-running template-coverage-check before plan approval"). At maximum, Phase B should chain to coverage-check automatically when `required_templates` or `assigned_repo` changes.

#### Edit C — Introduce a dependency cycle (T01 `depends_on: [T02]`, T02 `depends_on: [T01]`) (structural)

Deliberate adversarial edit to test the skill's escalation path.

- **Phase B result:** schema PASS; **cycle check FAILED** (topological sort could not order T01 ↔ T02 cycle, transitively blocking T05, T07, T08 — 5 tasks unsorted). Subagent correctly:
  - Did NOT write to feature frontmatter (preserved pre-edit state).
  - Did NOT write to plan file (preserved human's cycle-introducing edit as a record of what was tried).
  - Wrote escalation file `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md`.
  - Emitted `human_escalation` event with feature-level correlation ID and `reason: spec_level_blocker`. Validator exit 0.
- **Finding F2.8:** cycle-detection payload is not machine-readable. The `human_escalation` event's `payload.summary` is a prose string describing the cycle ("Dependency cycle detected during Phase B re-ingest: T01 depends_on T02 and T02 depends_on T01…"), but there is no `cycle_members: [T01, T02]` structured field. A downstream tool would have to parse the summary prose. Consider adding a per-type payload schema for `human_escalation` with structured fields for the most common escalation reasons.
- **Finding F2.9:** tension between `escalation-protocol.md` ("flags the feature state as `blocked`") and plan-review skill §"Phase B exit criteria" ("feature state remains `plan_review`"). On escalation, the event log carries the `spec_level_blocker` signal, but the feature frontmatter's `state` field still reads `plan_review` — not `blocked`. Is the feature blocked? The event says yes; the frontmatter says no. The skill's explicit prohibition on writing to the frontmatter during escalation is the correct posture (Phase B's single-source-of-truth is the feature frontmatter; writing a partial/errored state would be worse than not writing at all), but the conflict with escalation-protocol.md's framing is real. **Retrospective decision point:** either escalation-protocol.md's language needs softening ("flag the feature as blocked via event") or the state-vocabulary and plan-review skill need to grow a new transition owner.

#### Edit C-fix — Remove the cycle (revert T01 `depends_on` to `[]`) (structural)

- **Phase B result:** all checks PASS, frontmatter updated to 9 tasks with no cycle, no event (silent success).
- **Finding F2.10:** no "escalation resolved" signal. The `human_escalation` event from Edit C is still the last non-silent event in the log; a subsequent reader sees "escalation raised, silence, silence…" and has no machine-readable indication that the blocker was resolved. The inbox file `FEAT-2026-0005-plan-review-cycle.md` is **still in place** — the operator must manually archive it. This is an explicit walkthrough observation logged as a finding rather than fixed: the file remains at `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md` as a demonstration of the gap. **Retrospective input:** consider an `escalation_resolved` event type or a `plan_reingested` event with a `resolved_prior_blocker: bool` field. Or specify in the skill that the operator must archive the inbox file to a `archive/` subdirectory after resolution.

#### Edit D — Prose-only edit (tightened T03's `### Work unit prompt` from placeholder to multi-sentence) (prose)

- **Phase B result:** re-ingest re-reads from scratch per the skill spec (no diff-detect shortcut), re-parses YAML block (byte-identical to the pre-edit state since only prose changed), re-validates (all checks PASS), frontmatter content-identical write (or elided no-op), no event.
- **Finding F2.11:** Phase B's full read-parse-validate cycle on a prose-only edit is not wasteful — the skill is stateless-by-design and a diff-detect shortcut would introduce new failure modes (stale hashes, etc.). Positive observation on the skill design.
- **Finding F2.12:** the plan file's heading line `## Task T03 — implementation, Bontyyy/orchestrator-api-sample` is now stale — it still says `api-sample` from before Edit A retargeted T03 to `persistence-sample`. The skill explicitly says heading lines are regenerated **only on Phase A emission**, not on Phase B re-ingest ("The `## Task TNN …` heading line is regenerated on every round-trip; edits to it are ignored"). "Every round-trip" is ambiguous — does a Phase B re-ingest count as a round-trip? In practice, only Phase A currently regenerates. **Retrospective input:** clarify the skill — either Phase B regenerates headings (requiring plan-file writes during Phase B, which the current skill forbids) or the skill's language is tightened to "regenerated on Phase A only; Phase B re-ingest leaves plan file untouched, so stale headings may persist between Phase A emissions".

#### Edit E — Remove task T09 (structural)

Final edit. The human reconsiders and drops T09.

- **Phase B result:** all checks PASS (T09 had no dependents, so removal creates no orphans). Frontmatter now 8 tasks (T09 removed). No event.
- **Finding F2.13:** orphan check's value is highest on removal paths. Adding a task risks orphans only on the new task's `depends_on` (under the human's immediate attention); removing a task risks orphans in any surviving task's `depends_on` (possibly far from the human's focus during the edit). The skill's orphan check catches both directions with the same code, but the failure shape is asymmetric. Positive observation — skill design is robust; add-vs-remove asymmetry is worth naming in the skill text for completeness.

## Outcome — Feature 2 edge case

All WU 2.7 acceptance criteria for Feature 2 met:

| # | Acceptance criterion | Status |
|---|---|---|
| 2 | Edge case: plan-review re-ingest stress — human edits plan non-trivially (add a task, retarget a dependency, tighten a work unit prompt); skill re-ingests faithfully | ✓ — 5 distinct edits (retarget, add, cycle, cycle-fix, prose, remove) across 6 Phase B invocations; 1 correctly escalated on cycle, 5 correctly re-ingested (including 1 idempotent no-op on prose-only). All structural integrity preserved. |
| 3 | Honest logs, friction and workarounds captured | ✓ — 13 findings numbered F2.1–F2.13 plus the broader surface context |
| 4 | Any skill/config changes prompted commit at time + `agents/pm/version.md` bump | N/A — the walkthrough surfaced findings but the instruction was not to fix them during the walkthrough. No skill/config changes were made. All findings roll into WU 2.8 retrospective input. |
| 5 | Every event validates through `scripts/validate-event.py` | ✓ — 4 events (task_graph_drafted, template_coverage_checked, plan_ready, human_escalation), exit 0 on every validation pass |
| 6 | Commit `chore(phase-2): walkthrough feature 2 complete` | (at commit time, after this log is written) |

Final state:
- Feature frontmatter: 8 tasks (T01–T08, T03 retargeted to persistence-sample, T09 removed), state `plan_review`.
- Plan file: matches frontmatter's YAML block; has one stale heading line (T03 says `api-sample`, YAML says `persistence-sample`) — surfaced as finding F2.12.
- Event log: 4 events, all valid; includes one `human_escalation` from Edit C whose resolution is not observable in the event log (finding F2.10).
- Inbox: `inbox/human-escalation/FEAT-2026-0005-plan-review-cycle.md` remains (finding F2.10, deliberately left to surface the gap).

## Findings summary (Retrospective input for WU 2.8)

13 findings from Feature 2 (F2.1–F2.13). Prioritization notes added.

### Critical (Phase 2 fix candidates)

- **F2.3** — template-coverage-check subagent auto-populated `required_templates` in violation of the skill's explicit out-of-scope clause. The skill contract is not sticky enough against a "helpful" Sonnet session. Needs hardening.
- **F2.7** — Phase B does not re-run template-coverage-check or warn when `required_templates` or `assigned_repo` changes. Human would need to remember to re-invoke before approval. Design gap.

### Confirms / extends F1 findings (reinforced priority)

- **F2.1** confirms **F1.9** (skill ambiguity on single vs. per-behavior `qa_authoring` for multi-behavior features) — two runs, two different resolutions.
- **F2.2** extends **F1.10** (cross-repo dep in qa_execution) to the cross-behavior same-repo case — rule is "whole-repo gate", may be over-constrained.

### Medium (design decisions for WU 2.8)

- **F2.4** — schema changes across WUs are hard for a fresh session to trace; consider a comment block.
- **F2.5** — re-ingest on `assigned_repo` retarget doesn't re-validate `required_templates` vocabulary match.
- **F2.6** — re-ingest successes produce no event; audit-trail sparseness for high-velocity review sessions.
- **F2.8** — `human_escalation` payload is prose-only; no structured `cycle_members` for machine-readable consumption.
- **F2.9** — tension between `escalation-protocol.md` ("flag feature as blocked") and plan-review skill ("feature state remains `plan_review`") on escalation. Feature is blocked-by-event but not blocked-by-frontmatter.
- **F2.10** — no "escalation resolved" signal in the event log when a prior cycle is fixed; inbox file orphaned; manual archival required.
- **F2.12** — plan file headings become stale after Phase B retargets (skill explicitly only regenerates headings on Phase A, but its language is ambiguous).

### Positive observations

- **F2.11** — Phase B's stateless-by-design, no-diff-detect-shortcut approach is appropriate; shortcut would introduce new failure modes.
- **F2.13** — orphan check is robust across both add-and-remove directions; asymmetry of failure shape is worth naming in the skill text.

## Cross-reference to Feature 1 findings

Feature 1's log contained 13 findings labeled F1.1–F1.13. Feature 2 confirms or extends the following :
- F2.1 confirms F1.9 (qa_authoring ambiguity).
- F2.2 extends F1.10 (cross-repo/cross-behavior QA dep breadth).
- F2.6 extends F1.5 (event log sparseness for human-driven transitions).
- F2.9 extends F1.1 (no `feature_state_changed` event — now also affecting `plan_review → blocked` transitions on escalation).

Combined F1+F2 finding count: 26 findings for WU 2.8 retrospective triage. Several are closely related or mergeable; the retrospective will group and prioritize them.

