# Phase 3 walkthrough — notes scratch

This is the pre-walkthrough work doc. Three zones:

1. **Pre-computed inputs** (task graphs, sanity-check expectations).
2. **Pre-findings from skill dry-read** (hypotheses about friction; walkthrough either confirms or disproves).
3. **Ready-to-paste subagent prompts** for F1 sessions 1–9. F2 prompts filled during walkthrough (session pattern predictable from F1).
4. **Real-time walkthrough notes** — appended during execution.

Archival disposition per WU 3.7: either kept in-place as a walkthrough artifact, or its useful contents migrated into the feature logs + retrospective and the file is retired.

---

## 1 — Pre-computed task graphs (sanity-check targets)

After PM task-decomposition (session 1) runs, compare its output against these expected shapes. A mismatch is either: (a) PM skill-rendering bug (write up as F3 finding), (b) my pre-computation missed a rule, or (c) legitimate ambiguity — deserves a note.

### FEAT-2026-0006 expected task graph

| id | type | depends_on | assigned_repo | required_templates* |
|---|---|---|---|---|
| T01 | implementation | [] | Bontyyy/orchestrator-api-sample | `[api-controller, api-response-serializer]` |
| T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample | `[test-plan]` |
| T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample | `[]` |
| T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample | `[]` |

Rationale:
- **T01 required_templates.** The endpoint is a minimal GET with no query params and no request body — no `api-request-validator` needed. Controller + response serializer only.
- **T02 / T03 depends_on.** T02 qa_authoring is independent — authors from spec, not from impl (per qa-authoring SKILL §Step 2 Inputs). T03 qa_execution needs both T01 (code to run against) and T02 (plan to run).
- **T04 qa_curation depends_on [T03].** Standard per-feature single curation task.
- **`assigned_repo` = api-sample for all 4.** Single-repo feature. qa_authoring + qa_curation tasks are `assigned_repo: api-sample` per architecture §6.2 convention (the task *issue* lives on the component repo); their *deliverable* lives in specs-sample, which is expressed via `deliverable_repo: Bontyyy/orchestrator-specs-sample` in the work-unit issue body (template v1.1 field). **PM issue-drafting must emit `deliverable_repo` on T02 and T04.**

### FEAT-2026-0007 expected task graph

| id | type | depends_on | assigned_repo | required_templates* |
|---|---|---|---|---|
| T01 | implementation | [] | Bontyyy/orchestrator-api-sample | `[api-controller, api-request-validator, api-response-serializer]` |
| T02 | qa_authoring | [] | Bontyyy/orchestrator-api-sample | `[test-plan]` |
| T03 | qa_execution | [T01, T02] | Bontyyy/orchestrator-api-sample | `[]` |
| T04 | qa_curation | [T03] | Bontyyy/orchestrator-api-sample | `[]` |

Rationale:
- **T01 adds `api-request-validator`.** AC-3 requires validating `page_size > 500`; that's input validation (middleware or controller-layer validator).

\*`required_templates` are added by the human during plan_review simulation (between session 1 and session 2) — PM task-decomposition at v1 does NOT infer them (per Phase 2 WU 2.10 and the feature-frontmatter schema description of the `required_templates` field).

---

## 2 — Pre-findings from skill dry-read

Hypotheses about friction. Walkthrough confirms or disproves; confirmed hypotheses become F3 retrospective findings.

### PF-1 — qa-authoring PR-based flow is unspecified

**What.** qa-authoring SKILL §Step 7 says "Write the plan file to `/product/test-plans/<feature_correlation_id>.md` in the product specs repo" and later "The PR containing the plan file (in the product specs repo) is the deliverable under review." Implies PR-based flow on specs-sample, but the skill does NOT specify: branch name convention, commit message, PR title, PR body format, how the PR references the qa_authoring task issue for merge-watcher matching.

**Expected friction.** The qa-authoring subagent will have to invent a convention. Two likely picks: (a) branch `qa-authoring/FEAT-2026-0006-T02` (mirroring qa-curation's convention); (b) direct commit to main with no PR. If it picks (b), the "deliverable under review" phrase is violated. If it picks (a), we get a PR but the subagent has to guess the body format.

**Surfaces at:** Session 7 (F1) + session 7 (F2).

**Reco for walkthrough:** in the session-7 prompt, I'll give explicit guidance — branch convention `qa-authoring/<task_correlation_id>`, PR body = the test plan file's coverage-notes prose + link back to task issue. If the subagent doesn't follow this, log as F3 friction.

### PF-2 — `required_templates` gap between task-decomposition and template-coverage-check

**What.** Per Phase 2 WU 2.10 + feature-frontmatter schema: task-decomposition does NOT populate `required_templates`; it is set by human during plan_review. Our walkthrough skips the dedicated plan-review skill session. → Between session 1 (task-decomp) and session 2 (template-coverage-check), the human has to manually add `required_templates` to the frontmatter.

**Expected friction.** Mechanical — 1-minute edit. If the human forgets, template-coverage-check will fail with `required_templates` absent (per WU 2.11 hardening: "absent ≠ []"; absent → pre-flight rejection).

**Surfaces at:** Between session 1 and session 2, both features.

**Reco for walkthrough:** explicit step in session-1 output — "human, next: edit feature registry to add required_templates per task; values are in notes-scratch §1." Mitigation against forgetting.

### PF-3 — qa_authoring / qa_curation deliverable_repo field (**UPDATED after dry-read**)

**What.** Work-unit-issue template v1.1 introduced optional `deliverable_repo` frontmatter field for QA tasks whose deliverable lives in a different repo from `component_repo` (WU 2.13). PM issue-drafting skill v1.2 knows about this — confirmed via dry-read of `agents/pm/skills/issue-drafting/SKILL.md` §"Worked example — FEAT-2026-0004/T03 (Python stack + `deliverable_repo`)".

**HOWEVER:** the worked example uses `deliverable_repo: clabonte/orchestrator` (the Phase 2 convention — test plans lived in the orchestrator repo itself because Phase 0 WU 0.8 deferred the specs repo). Our walkthrough is **the first exercise of the pattern with `deliverable_repo: Bontyyy/orchestrator-specs-sample`**. The mechanics should be identical but the target is novel.

**Expected friction.** The subagent has a clear worked example showing the mechanics. Low risk of omission. Medium risk the subagent faithfully replicates the example's `clabonte/orchestrator` target instead of adapting to our `Bontyyy/orchestrator-specs-sample`.

**Surfaces at:** Session 4 (F1 + F2) — issue-drafting session.

**Reco for walkthrough:** session-4 prompt already carries explicit guidance naming `Bontyyy/orchestrator-specs-sample` for T02 + T04. If the subagent still uses `clabonte/orchestrator`, log as F3 friction (evidence: worked-example stickiness → candidate WU for issue-drafting SKILL update).

### PF-4 — specs-sample fetch pattern ambiguity

**What.** Feature registry `## Related specs` section points at `product/features/FEAT-2026-0006.md` in `Bontyyy/orchestrator-specs-sample` — formatted as markdown link with both repo-relative path and full GitHub URL. Skills (task-decomposition, qa-authoring, qa-regression) need to fetch this file. Three plausible methods:
- (a) Local clone read: `cat /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0006.md`.
- (b) `gh api` remote fetch: `gh api repos/Bontyyy/orchestrator-specs-sample/contents/product/features/FEAT-2026-0006.md?ref=main --jq .content | base64 -d`.
- (c) Raw HTTPS: `curl https://raw.githubusercontent.com/Bontyyy/orchestrator-specs-sample/main/product/features/FEAT-2026-0006.md`.

Skill doesn't specify.

**Expected friction.** Subagents may inconsistent — session 1 picks (b), session 7 picks (a). Friction is mild if all 3 work; becomes a finding if any subagent fails to fetch at all.

**Surfaces at:** Sessions 1, 3, 7 (and F2 equivalents).

**Reco for walkthrough:** in each session prompt, explicitly state "use local clone at `/Users/bonty/Documents/GitHub/orchestrator-specs-sample/`" to eliminate ambiguity. Log if a subagent still struggles.

### PF-5 — task_graph_drafted event — no per-type schema (**RESOLVED pre-walkthrough**)

**What.** Confirmed via `ls shared/schemas/events/`: no `task_graph_drafted.schema.json` file exists. Only envelope validation (against `event.schema.json`) applies to this event. Same for `task_created`, `task_ready`, `task_completed`, `task_blocked`, `dependency_recomputed`, `plan_approved`, `spec_issue_raised`, `override_applied`, `override_expired` — all envelope-only at v1.

**Per-type schemas that EXIST:** `escalation_resolved`, `feature_state_changed`, `human_escalation`, `qa_execution_completed`, `qa_execution_failed`, `qa_regression_filed`, `qa_regression_resolved`, `regression_suite_curated`, `task_started`, `template_coverage_checked`, `test_plan_authored`.

**Implication for walkthrough:** session 1's `task_graph_drafted` event only needs envelope fields (timestamp, correlation_id, event_type, source, source_version, payload) — the payload shape is free-form per WU 2.5 precedent. Phase 2 events for similar feature-state transitions commonly carried `{task_count: N, involved_repos: [...], decomposition_pass: 1}` as payload — subagent can follow that convention, it's not schema-enforced.

**Surfaces at:** Session 1. Nothing to surface — resolved pre-walkthrough.

### PF-6 — Test plan commit discipline — how much of a PR?

**What.** qa-authoring opens a PR on specs-sample with the test plan file. Given specs-sample has no branch protection (no required reviews, no required status checks), the PR can merge instantly. But the walkthrough convention is that the human reviews + merges, mirroring the production flow.

**Expected friction.** Low mechanical; potential for the subagent to "merge its own PR" rather than leave it for review. anti-pattern per orchestrator design (merge watcher, not agent, merges).

**Reco for walkthrough:** session-7 prompt explicitly forbids the subagent from merging its own PR — "stop at PR open + `gh pr view <url>` confirmation; the human merges."

### PF-7 — F2 step 12 (human spawns fix task from inbox) is underspecified

**What.** qa-regression SKILL §Out of scope: "Spawning the regression-fix implementation task. The inbox artifact is the handoff; the PM inbox consumer (future WU) or the human picks the file up, mints the new task's correlation ID, opens the issue against the target repo, and transitions it through its lifecycle. This skill stops at the inbox write." → The human (me, as walkthrough operator) must simulate the PM inbox consumer. No skill docs this simulation.

**Expected friction.** Manual + novel. The human has to: read the inbox file, pick TNN (next available = T05 for FEAT-2026-0007 since T01–T04 already used), compose a work-unit-issue body using the inbox file's reproduction brief, open the GitHub issue, flip labels, emit `task_created` + `task_ready` events.

**Reco for walkthrough:** F2 session 12 gets a detailed manual runbook in notes-scratch — not a subagent prompt but a step-by-step for the human.

---

## 3 — Session prompts (F1)

Each prompt is designed to be pasted into `Agent` tool with `subagent_type=general-purpose` and `model=sonnet`. The subagent starts with zero context — every prompt is self-contained.

Use-as:

```
Agent({
  description: "F1 session N — <short>",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: <paste the body below>
})
```

All absolute paths use `/Users/bonty/Documents/GitHub/orchestrator/` and `/Users/bonty/Documents/GitHub/orchestrator-specs-sample/` and `/Users/bonty/Documents/GitHub/orchestrator-api-sample/`.

---

### F1 Session 1 — PM task-decomposition on FEAT-2026-0006

```
You are acting as the PM agent (v1.6.0, frozen as Phase 2 baseline) performing the task-decomposition skill on a fresh feature. This is a walkthrough session — honesty about friction is required. Do not sanitize your report.

Setup discipline (re-read before acting, per /shared/rules/role-switch-hygiene.md):
1. Read every file under /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md (PM role config).
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/task-decomposition/SKILL.md (the skill you are executing).

Task:
- Feature registry to decompose: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md (state=planning, task_graph=[]).
- Related specs file: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0006.md (local clone; the specs-sample repo is Bontyyy/orchestrator-specs-sample on GitHub).

Expected flow per SKILL.md steps 1–7:
- Step 1: state intent.
- Step 2: read feature registry + spec files. Spec has 1 AC (AC-1: GET /widgets/count returns {"count": N}).
- Step 3: enumerate capabilities. Per spec type "feature narrative with AC-N headings", expect 1 behavior.
- Step 4: build the task list. Expect: 1 implementation (impl the endpoint on api-sample), 1 qa_authoring, 1 qa_execution, 1 qa_curation.
- Step 5: build depends_on edges.
- Step 6: validate task graph in memory (schema + capability coverage + dependency acyclicity).
- Step 7: write the task_graph back to the feature registry's frontmatter + emit task_graph_drafted event.

Writes expected:
- /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md — update frontmatter's task_graph array. LEAVE `state: planning` (do NOT transition to plan_review — that's human-owned per /shared/rules/state-vocabulary.md).
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0006.jsonl — create file + append 1 JSONL line with the task_graph_drafted event.

Do NOT populate `required_templates` field on tasks — per feature-frontmatter schema description and Phase 2 WU 2.10, the PM agent at v1 does NOT infer required_templates; the human adds them during plan_review.

Do NOT:
- Modify /agents/pm/*, /agents/component/*, /agents/qa/*, or /shared/rules/* (frozen surfaces).
- Push anything to GitHub.
- Transition feature state.
- Open GitHub issues (that's session 3).
- Run template-coverage-check (that's session 2).

Verification (per /shared/rules/verify-before-report.md §3):
- Pipe the constructed event through `python3 /Users/bonty/Documents/GitHub/orchestrator/scripts/validate-event.py --file <event.json>` → require exit 0 before appending.
- After writing: re-read the appended event line from events/FEAT-2026-0006.jsonl to confirm JSONL integrity.
- Run `python3 /Users/bonty/Documents/GitHub/orchestrator/scripts/validate-frontmatter.py --file /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md` → require exit 0.
- `source_version` on the event must be produced by `bash /Users/bonty/Documents/GitHub/orchestrator/scripts/read-agent-version.sh pm` at emission time — NOT eye-cached from version.md. Expected: `1.6.0`.

Report back:
- The task_graph you produced, rendered as a markdown table (id, type, depends_on, assigned_repo).
- The full event JSON you emitted (envelope + payload).
- Verification evidence: both validate-* exit codes, the re-read event line.
- Every friction, surprise, or workaround encountered — even minor. Flag any clause in the skill you had to re-read more than once or that was ambiguous. These are retrospective inputs; DO NOT sanitize.
- How long the session took (rough wall-clock).
```

---

### F1 Session 2 — Human plan_review transition (manual, no subagent)

**Orchestrator actions (you, Opus 4.7, not a subagent):**

1. Review the task_graph produced by session 1. Compare against the expected graph in §1 of this file. Note any divergence.
2. Edit `features/FEAT-2026-0006.md` — add `required_templates` field to each task per the §1 table. YAML edit, ~1 min.
3. Transition feature state: `planning → plan_review → generating`. At v1, this is a human file-edit (change the `state` field) + emitting `feature_state_changed` events. Two events if you emit both transitions, or one `plan_review → generating` if you skip plan_review entirely (per our walkthrough decision to skip the dedicated plan-review skill). **My reco: emit one `planning → plan_review`, then one `plan_review → generating` with a 10-second gap, so the event log shows the canonical sequence even though the plan-review skill session was skipped.**
4. Validate after each frontmatter edit: `python3 scripts/validate-frontmatter.py --file features/FEAT-2026-0006.md` → exit 0.
5. Validate + append each `feature_state_changed` event via `validate-event.py` → `events/FEAT-2026-0006.jsonl`.

---

### F1 Session 3 — PM template-coverage-check on FEAT-2026-0006

```
You are acting as the PM agent (v1.6.0 frozen) performing the template-coverage-check skill on FEAT-2026-0006.

Setup discipline:
1. Read every file under /Users/bonty/Documents/GitHub/orchestrator/shared/rules/.
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/template-coverage-check/SKILL.md.

Task:
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md (state=generating, task_graph populated, required_templates populated by the human on each task).
- The involved repo Bontyyy/orchestrator-api-sample has .specfuse/templates.yaml declaring `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`. Fetch via local clone at /Users/bonty/Documents/GitHub/orchestrator-api-sample/.specfuse/templates.yaml.

Expected flow per SKILL.md:
- Read each task's required_templates from the feature frontmatter.
- For each task, compare against the assigned_repo's .specfuse/templates.yaml provided_templates.
- Per WU 2.11 hardening: `required_templates: []` is valid (trivially satisfies); absent field is a pre-flight reject (Phase 2 F2.3 absorbed).
- Coverage satisfied iff every required_templates token appears in the provided_templates set.
- If gap: escalate spec_level_blocker (no auto-fill).
- If clean: emit template_coverage_checked event.

Writes expected:
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0006.jsonl — append 1 template_coverage_checked event line.

Do NOT:
- Modify feature frontmatter.
- Modify any .specfuse/ file on any repo.
- Touch frozen surfaces.
- Open GitHub issues.

Verification:
- validate-event.py on the event → exit 0.
- Re-read the appended line.
- Confirm coverage is satisfied by naming, per task, which required_templates tokens matched against which provided_templates tokens.

Report back:
- Coverage satisfaction matrix (task id → required_templates → provided_templates intersection).
- The emitted event JSON.
- Validation outputs.
- Friction / surprises verbatim.
```

---

### F1 Session 4 — PM issue-drafting on FEAT-2026-0006

```
You are acting as the PM agent (v1.6.0 frozen) performing the issue-drafting skill on FEAT-2026-0006.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/issue-drafting/SKILL.md.
4. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/issue-drafting-spec.md (the contract).
5. Read /Users/bonty/Documents/GitHub/orchestrator/shared/templates/work-unit-issue.md (v1.1, with optional `deliverable_repo` + `## Deliverables` section).

Task:
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md (state=generating, task_graph fully populated).
- Open 4 GitHub issues on Bontyyy/orchestrator-api-sample — one per task in the graph.

Per-task issue requirements:
- **T01 (implementation):** `deliverable_repo` omitted (defaults to component_repo = api-sample).
- **T02 (qa_authoring):** `deliverable_repo: Bontyyy/orchestrator-specs-sample` — the test plan lives on specs-sample, not api-sample.
- **T03 (qa_execution):** `deliverable_repo` omitted (execution runs against code in api-sample, no plan file write).
- **T04 (qa_curation):** `deliverable_repo: Bontyyy/orchestrator-specs-sample` — the curation PR lives on specs-sample.

Labels per issue:
- `type:implementation` / `type:qa-authoring` / `type:qa-execution` / `type:qa-curation` (one).
- `autonomy:review` (feature-level default).
- `state:ready` for tasks with `depends_on: []` (T01, T02). `state:pending` for tasks with dependencies (T03, T04).

Events emitted per task:
- task_created (all 4 tasks).
- task_ready (only for T01, T02 — the tasks transitioning straight to ready via no_dep_creation trigger).

Writes:
- 4 GitHub issues on Bontyyy/orchestrator-api-sample via `gh issue create`.
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0006.jsonl — 6 event lines appended (4 task_created + 2 task_ready).

Do NOT:
- Open issues on specs-sample (the deliverable_repo field just points; the issue itself always lives on component_repo).
- Touch frozen surfaces.
- Merge any PR.

Verification per task:
- validate-event.py on each emitted event → exit 0.
- Re-read the appended events.
- Confirm the GitHub issue exists by `gh issue view <url> --json number,title,labels,body`.

Report back:
- Table of 4 issues: T id, issue URL, labels applied, deliverable_repo value.
- All 6 events emitted.
- Verification outputs.
- Friction / surprises verbatim (especially on deliverable_repo — this is a PF-3 verification point).
```

---

### F1 Session 5 — Component implementation on T01

```
You are acting as the component agent (v1.5.0, frozen as Phase 1 baseline) performing an implementation task on Bontyyy/orchestrator-api-sample.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/component/CLAUDE.md.
3. Read each skill under /Users/bonty/Documents/GitHub/orchestrator/agents/component/skills/ that CLAUDE.md references for an implementation task (likely include verification/SKILL.md).

Task:
- GitHub issue URL: <FILL IN WITH T01 ISSUE URL FROM SESSION 4 OUTPUT>.
- Repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample (local clone).
- Feature: FEAT-2026-0006 — implement GET /widgets/count endpoint returning {"count": N} as non-negative integer.

Implementation requirements (from spec + feature registry):
- New endpoint GET /widgets/count.
- Returns HTTP 200 with JSON body {"count": N} where N is the total widget count.
- Uses the existing widget repository abstraction (IWidgetRepository / WidgetService patterns already in the sample repo).
- Add unit tests covering the endpoint.
- Coverage ≥ 90%, zero warnings, passes all CI gates.

Expected flow:
- State intent.
- Pick up the T01 issue (flip `state:ready → state:in-progress` via gh issue edit).
- Emit task_started event to /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0006.jsonl.
- Implement on a feature branch (`feat/FEAT-2026-0006-T01-widget-count-endpoint` or similar — follow existing sample repo conventions from the api-sample's git log).
- Run all verification gates per .specfuse/verification.yml. Require all gates pass before reporting.
- Push branch + open PR on api-sample with `Closes Bontyyy/orchestrator-api-sample#<N>` in body.
- Flip T01 issue `state:in-progress → state:in-review`.
- Emit task_completed event on T01 with verification evidence.

Do NOT:
- Merge your own PR (merge watcher, simulated by human, does that).
- Touch .specfuse/verification.yml or branch protection.
- Touch any orchestrator repo file.
- Touch /agents/* (frozen).

Verification evidence to include in report:
- PR URL.
- All verification gate outputs (test pass, coverage %, warnings, OWASP, linter).
- Re-read of task_completed event line.

Report back:
- PR URL + summary of the change (files modified, tests added).
- Verification outputs.
- Friction / surprises verbatim.
```

---

### F1 Session 6 — Human: merge T01 PR (manual)

**Orchestrator actions:**

1. Review T01 PR on Bontyyy/orchestrator-api-sample. Confirm all checks pass (per branch protection).
2. Merge PR (squash per existing convention on api-sample).
3. Flip T01 issue `state:in-review → state:done` via `gh issue edit`.
4. Close T01 issue via `gh issue close`.
5. Note the merge commit SHA (40-char full hex) — needed for session 8 qa-execution.
6. Emit `task_completed` event on T01 manually (or confirm component agent already did in session 5 — depending on skill convention). If component agent emitted it, verify by tail of events/FEAT-2026-0006.jsonl. Per architecture, task_completed is emitted by the actor that closes the task, which for impl tasks may be the component agent or the merge watcher — check the component CLAUDE.md v1.5.0 for exact convention.

---

### F1 Session 7 — QA qa-authoring on T02

```
You are acting as the QA agent (v1.4.0) performing the qa-authoring skill on FEAT-2026-0006.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-authoring/SKILL.md.

Task:
- GitHub issue URL: <FILL IN WITH T02 ISSUE URL FROM SESSION 4 OUTPUT>.
- Feature: FEAT-2026-0006.
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md.
- Related specs file: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0006.md.
- Deliverable repo: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/ (local clone of Bontyyy/orchestrator-specs-sample).

Expected flow per qa-authoring SKILL.md steps 1–7:
- Step 1: state intent; flip T02 issue state:ready → state:in-progress; emit task_started.
- Step 2: read feature registry + spec file.
- Step 3: enumerate behaviors. Spec has 1 AC → 1 behavior → 1 test expected (default cardinality; no feature-scope override).
- Step 4: cardinality check — the feature's ## Scope is silent on qa_authoring cardinality; default = 1 test per behavior = 1 test total.
- Step 5: draft the test entry. test_id convention = kebab-case `<domain>-<outcome>`. Propose: `widgets-count-returns-total`.
- Step 6: validate plan in memory (schema round-trip, unique test_id, coverage check).
- Step 7: write plan file + emit test_plan_authored event.

CONVENTION FOR THIS WALKTHROUGH (addresses PF-1 ambiguity):
- Create a branch on specs-sample: `qa-authoring/FEAT-2026-0006-T02`.
- Commit the plan file to that branch with message `feat(test-plan): FEAT-2026-0006 — widget count endpoint`.
- Push branch.
- Open PR via `gh pr create` against specs-sample's main. PR title: `feat(test-plan): FEAT-2026-0006 — widget count endpoint`. PR body: short summary + link to T02 issue URL.
- STOP at PR open. Do NOT merge the PR (human/merge-watcher role).
- Flip T02 issue `state:in-progress → state:in-review` (role-owned transition).
- Emit task_completed event on T02 with payload pointing at the PR URL.

Do NOT:
- Merge your own PR.
- Write outside /product/test-plans/ on specs-sample.
- Touch component repo code.
- Flip labels or state on any task other than T02 (Q4 invariant).
- Touch frozen surfaces on orchestrator repo.

Verification per SKILL.md §Verification:
- Plan file round-trips through /Users/bonty/Documents/GitHub/orchestrator/shared/schemas/test-plan.schema.json (use `python3 -c "import json, jsonschema; jsonschema.validate(...)"` or equivalent).
- Unique test_id check.
- Coverage check (every AC fragment cited in at least one test's `covers`).
- test_plan_authored event via validate-event.py → exit 0.
- Re-read written plan file post-write.
- source_version = `bash scripts/read-agent-version.sh qa` at emission time (expect 1.4.0).

Report back:
- The test plan file contents (full YAML frontmatter + prose body).
- PR URL on specs-sample.
- The test_plan_authored event JSON.
- Verification evidence.
- Friction / surprises verbatim — especially any clause of the skill you had to interpret (PR convention, commit message, PR body format).
```

---

### F1 Session 8 — Human: merge qa-authoring PR + close T02 (manual)

**Orchestrator actions:**

1. Review the qa-authoring PR on specs-sample. Confirm plan file validates.
2. Merge PR (squash).
3. Flip T02 issue `state:in-review → state:done` + close via `gh issue close`.
4. Emit `task_completed` event on T02 (if not already done by qa-authoring session).

---

### F1 Session 9 — PM dependency-recomputation on FEAT-2026-0006

```
You are acting as the PM agent (v1.6.0 frozen) performing the dependency-recomputation skill on FEAT-2026-0006.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/dependency-recomputation/SKILL.md.

Trigger: T02 just completed (task_completed event appended). Feature event log now shows task_completed on both T01 and T02. T03's dependencies (`depends_on: [T01, T02]`) are satisfied.

Task:
- Read /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0006.md frontmatter task_graph.
- Read /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0006.jsonl end-to-end.
- For each task whose `state` (derived from events, per WU 2.10 event-log-derived convention) is `pending`, check whether all `depends_on` tasks are `done`. If yes, flip the GitHub issue's label `state:pending → state:ready` and emit `task_ready` event.

Expected outcome:
- T03 qa_execution flipped pending → ready.
- T04 qa_curation stays pending (T03 not done yet).

Writes:
- GitHub issue label flip on T03 (T03 issue URL = <FILL IN FROM SESSION 4 OUTPUT>).
- 1 task_ready event appended to events/FEAT-2026-0006.jsonl.

Do NOT:
- Flip T04 (dep T03 not done).
- Touch any task_graph or feature state.

Verification:
- validate-event.py on the task_ready event → exit 0.
- gh issue view T03 --json labels confirms `state:ready` present + `state:pending` removed.

Report back:
- Which tasks were evaluated and the dependency-status per task.
- Which tasks transitioned.
- Events emitted.
- Friction / surprises verbatim.
```

---

### F1 Session 10 — QA qa-execution on T03

```
You are acting as the QA agent (v1.4.0) performing the qa-execution skill on FEAT-2026-0006.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-execution/SKILL.md.

Task:
- GitHub issue URL: <FILL IN WITH T03 ISSUE URL>.
- Feature: FEAT-2026-0006.
- Plan file (merged in session 8): /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/FEAT-2026-0006.md (pull latest via `git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample pull` to ensure post-merge state).
- Component repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample. main HEAD SHA after T01 merge.
- Commit SHA = the merge SHA from session 6 (noted there). Use the 40-char full hex.

Expected flow per qa-execution SKILL.md steps 1–7:
- Step 1: state intent; flip T03 state:ready → state:in-progress; task_started.
- Step 2: resolve plan + commit_sha (cd /Users/bonty/Documents/GitHub/orchestrator-api-sample && git rev-parse HEAD for the SHA; plan round-trips through test-plan.schema.json).
- Step 3: idempotence check — no prior qa_execution_* event for (T03 correlation_id, commit_sha) expected.
- Step 4: per-test loop. Start the api-sample service (`dotnet run --project src/...` or equivalent — follow api-sample README). Run each plan command. Evaluate `expected` predicate against captured outputs.
- Step 5: aggregate. Expected outcome for happy path = qa_execution_completed (all pass).
- Step 6: validate + append event.
- Step 7: flip T03 state:in-progress → state:in-review; emit task_completed.

Do NOT:
- Write to plan file.
- Flip label / state on T01 impl task or any other task (Q4 invariant).
- Commit to component repo or open a PR against it.
- Touch frozen surfaces.

Verification per SKILL.md §Verification:
- All declared commands ran.
- Each test has definite pass/fail.
- qa_execution_completed event validates.
- source_version from read-agent-version.sh qa.
- Re-read appended event.

Report back:
- For each test: test_id, commands run, outputs captured, expected predicate, pass/fail verdict.
- The emitted event JSON.
- commit_sha used.
- Verification evidence.
- Friction verbatim.
```

---

### F1 Sessions 11–14 — curation + feature close (abbreviated templates)

**Session 11** — Human closes T03 manually (in-review → done + task_completed).

**Session 12** — PM dependency-recomputation (T04 becomes ready). Same prompt shape as session 9, trigger = T03 task_completed.

**Session 13** — QA qa-curation on T04. Expected empty-curation (1 plan in corpus). Prompt shape below.

```
You are acting as the QA agent (v1.4.0) performing the qa-curation skill on FEAT-2026-0006 (drafting mode).

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-curation/SKILL.md.

Task:
- qa_curation task: T04 on FEAT-2026-0006 (issue URL <FILL IN>).
- Scan cohort: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/*.md — exactly 1 plan at this point (FEAT-2026-0006.md).
- Expected: 0 dedup candidates (1 plan = no pairs), 0 orphans (plan covers AC-1 which still exists), 0 consolidation candidates (no failure history), 0 rename candidates (no rename-request line in plan prose).

Expected flow per SKILL.md drafting mode steps 1–7:
- Steps 1–3: pickup, read plan, classify candidates → 0 surviving candidates.
- Step 5: `scope: empty` / no surviving → skip to step 7.
- Step 7: empty-curation branch. No PR opened. Comment on T04 issue with summary. Flip T04 state:in-progress → state:in-review. Emit task_completed with `empty_curation: true` payload field. NO regression_suite_curated event emitted (per SKILL.md §Empty-curation branch).

Do NOT:
- Open a PR for an empty-curation pass.
- Emit regression_suite_curated when no PR landed.
- Touch any task other than T04 (Q4 invariant).
- Touch frozen surfaces.

Verification:
- validate-event.py on task_completed → exit 0.
- gh issue view T04 shows state:in-review.
- tail of events/FEAT-2026-0006.jsonl has task_completed with empty_curation: true; no regression_suite_curated line.

Report back:
- Scan cohort size + per-plan classification (candidates kind).
- Comment text posted on T04 issue.
- task_completed event JSON.
- Verification evidence.
- Friction verbatim.
```

**Session 14** — Human closes T04 (in-review → done) + flip feature state `in_progress → done`. Emit feature_state_changed.

---

## 4 — Real-time walkthrough notes (F1)

Append here during F1 execution. Format: `YYYY-MM-DD HH:MM` + session N + observation. Keep entries lapidary — 1–3 bullets per session. Post-session, write up the detailed log in feature-1-log.md.

```
(F1 complete 2026-04-24; see feature-1-log.md for the detailed narrative)
```

---

## 5 — Session prompts (F2)

Same shape as §3 (F1): each prompt is designed to be pasted into the `Agent` tool with `subagent_type=general-purpose` and `model=sonnet`. Subagent starts with zero context — every prompt is self-contained.

Expected total: **20 sessions** (12 agent + 8 manual) = F1 shape (9 sessions) + regression loop (6 additions: fail-execution, file, spawn, fix-impl, merge, re-execute) + resolution (1: qa-regression resolved) + curation + close (4).

### F2 preamble — mitigation clauses baked into every subagent prompt (absorbs F1 findings F3.2, F3.3, F3.5, F3.6, F3.13)

Include these five clauses in every subagent prompt, in addition to the F1 base (role-switch-hygiene re-read, verification, friction reporting):

1. **Do NOT commit on orchestrator repo.** Leave event-log appends and frontmatter edits as uncommitted working-tree changes under `/Users/bonty/Documents/GitHub/orchestrator/`. The orchestration session (Opus 4.7) produces the single walkthrough-wrap commit at the end. You may `git add` if a tool requires staging; you may NOT `git commit` on the orchestrator repo. Commits on `orchestrator-api-sample` and `orchestrator-specs-sample` are allowed when the skill requires them (component impl, qa-authoring PR branch).
2. **Timestamp discipline.** Every `timestamp` field on every event MUST be produced by `date -u +%Y-%m-%dT%H:%M:%SZ` at the moment the event is constructed. Do NOT synthesize from conversation context, from today's date string, or by copying/adjusting nearby log timestamps. If you're about to emit an event without having just run `date -u`, stop and run it.
3. **Per-type event payload schemas — cross-reference before constructing.** Check `/Users/bonty/Documents/GitHub/orchestrator/shared/schemas/events/<event_type>.schema.json` exists; if yes, the payload must satisfy it. For `task_started`: required fields `issue_url` (full GitHub URL) + `branch`; do NOT use the bare `issue` field (that's the schema-less `task_created` convention). For events without a per-type schema, envelope-only validation applies (validate-event.py silently skips payload check).
4. **validate-event.py invocation.** `/dev/stdin` pipe fails on macOS with exit 2. Use temp-file pattern: `python3 /Users/bonty/Documents/GitHub/orchestrator/scripts/validate-event.py --file /tmp/event-<descriptor>.json` with the event JSON written to that path first.
5. **Friction reporting non-sanitized.** Record every surprise, workaround, re-read, or ambiguity — even minor. These feed WU 3.7 retro triage. Do NOT sanitize; honest friction data is the walkthrough's primary deliverable.

Absolute paths: `/Users/bonty/Documents/GitHub/orchestrator/`, `/Users/bonty/Documents/GitHub/orchestrator-specs-sample/`, `/Users/bonty/Documents/GitHub/orchestrator-api-sample/`.

---

### F2 Session 1 — PM task-decomposition on FEAT-2026-0007

```
You are acting as the PM agent (v1.6.0, frozen as Phase 2 baseline) performing the task-decomposition skill on a fresh feature. This is a walkthrough session — honesty about friction is required. Do not sanitize your report.

Setup discipline (re-read before acting, per /shared/rules/role-switch-hygiene.md):
1. Read every file under /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md (PM role config, v1.6.0).
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/task-decomposition/SKILL.md.

F2 preamble (5 mitigation clauses — absorbs F1 findings):
1. Do NOT `git commit` on the orchestrator repo. Leave appends uncommitted.
2. Every event timestamp MUST be produced by `date -u +%Y-%m-%dT%H:%M:%SZ` at emission time.
3. Per-type event payload schemas live at /Users/bonty/Documents/GitHub/orchestrator/shared/schemas/events/. `task_graph_drafted` has NO per-type schema (envelope-only).
4. validate-event.py /dev/stdin broken on macOS — use `--file /tmp/event.json` pattern.
5. Friction reporting non-sanitized. Record every surprise.

Task:
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md (state=planning, task_graph=[]).
- Related specs file: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0007.md. Spec carries AC-1 (default 50), AC-2 (1 ≤ N ≤ 500 slice), AC-3 (N > 500 → HTTP 400 + error.code=page_size_over_limit).

Expected flow per SKILL.md steps 1–7:
- Step 1: state intent.
- Step 2: read feature registry + spec. Spec has 3 ACs.
- Step 3: enumerate capabilities. Per default cardinality (1 AC → 1 behavior), expect 3 behaviors grouped into 1 implementation task (all 3 are the same endpoint's different request shapes).
- Step 4: build task list. Expected shape: 1 implementation, 1 qa_authoring, 1 qa_execution, 1 qa_curation.
- Step 5: depends_on edges.
- Step 6: validate in memory (schema + capability coverage + acyclic).
- Step 7: write task_graph to feature frontmatter + emit task_graph_drafted event.

Writes expected:
- /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md — update frontmatter task_graph array. LEAVE state=planning.
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0007.jsonl — create file + append 1 JSONL line (task_graph_drafted event).

Do NOT populate `required_templates` — that's human's role during plan_review (v1 discipline, WU 2.10).

Do NOT:
- Modify /agents/*, /shared/rules/* (frozen).
- Push to GitHub.
- Transition feature state.
- Open GitHub issues (that's session 4).
- Run template-coverage-check (session 3).
- `git commit` on orchestrator repo.

Verification:
- validate-event.py --file /tmp/task_graph_drafted.json → exit 0.
- Re-read appended line.
- validate-frontmatter.py on FEAT-2026-0007.md → exit 0.
- source_version via `bash scripts/read-agent-version.sh pm` at emission (expect 1.6.0).

Report back:
- task_graph rendered as a markdown table (id, type, depends_on, assigned_repo).
- Full event JSON emitted.
- Verification evidence (exit codes, re-read line).
- Every friction, surprise, workaround — even minor. DO NOT sanitize.
- Wall-clock duration + rough tool-use count.
```

---

### F2 Session 2 — Human plan_review transition (manual)

**Orchestrator actions (Opus 4.7 — me, not a subagent):**

1. Review task_graph from S1. Compare against pre-computed §1 expected graph for FEAT-2026-0007. Note any divergence as F3.x finding.
2. Edit `features/FEAT-2026-0007.md` — add `required_templates` per task per §1 table (T01: `[api-controller, api-request-validator, api-response-serializer]`; T02: `[test-plan]`; T03/T04: `[]`).
3. Transition feature state: `planning → plan_review → generating`. Emit TWO `feature_state_changed` events with 10s gap (canonical trajectory preserved even though plan-review skill session skipped).
4. `source: human`, `source_version: <short SHA>` via `git rev-parse --short HEAD` on orchestrator repo.
5. Validate each edit: `validate-frontmatter.py --file features/FEAT-2026-0007.md` → exit 0. Each event via validate-event.py → exit 0.

---

### F2 Session 3 — PM template-coverage-check on FEAT-2026-0007

```
You are acting as the PM agent (v1.6.0 frozen) performing the template-coverage-check skill on FEAT-2026-0007.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/template-coverage-check/SKILL.md.

F2 preamble (5 mitigation clauses — same as S1).

Task:
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md (state=generating, task_graph populated, required_templates populated).
- Component repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample. Its .specfuse/templates.yaml declares `[api-controller, api-request-validator, api-response-serializer, test-plan, test-runner]`.

Expected flow per SKILL.md:
- For each task, compare required_templates against assigned_repo's provided_templates.
- WU 2.11 hardening: `required_templates: []` is valid; absent field is pre-flight reject.
- Clean → emit template_coverage_checked event (per-type schema EXISTS at shared/schemas/events/template_coverage_checked.schema.json — use it).

Writes expected:
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0007.jsonl — append 1 template_coverage_checked event.

Do NOT:
- Modify feature frontmatter, .specfuse/ files, frozen surfaces.
- Open GitHub issues.
- `git commit` on orchestrator repo.

Verification:
- validate-event.py --file /tmp/template_coverage_checked.json → exit 0 (envelope + per-type payload).
- Re-read appended line.
- Name per task which required_templates tokens matched which provided_templates.

Report back:
- Coverage satisfaction matrix.
- Emitted event JSON.
- Validation outputs.
- Friction verbatim.
- Duration + tool-use count.
```

---

### F2 Session 4 — PM issue-drafting on FEAT-2026-0007

```
You are acting as the PM agent (v1.6.0 frozen) performing the issue-drafting skill on FEAT-2026-0007.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/issue-drafting/SKILL.md (may exceed 25k read limit — use offset/limit chunking).
4. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/issue-drafting-spec.md.
5. Read /Users/bonty/Documents/GitHub/orchestrator/shared/templates/work-unit-issue.md (v1.1).

F2 preamble (5 mitigation clauses). Additional: **F3.7 mitigation — the SKILL's worked example uses `clabonte/orchestrator` as deliverable_repo, which is the Phase 2 era convention. For THIS walkthrough, ADAPT: T02 and T04 use `deliverable_repo: Bontyyy/orchestrator-specs-sample` (NOT clabonte/orchestrator).**

Task:
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md (state=generating, task_graph fully populated).
- Open 4 GitHub issues on Bontyyy/orchestrator-api-sample — one per task.

Per-task issue requirements:
- T01 (implementation): `deliverable_repo` omitted.
- T02 (qa_authoring): `deliverable_repo: Bontyyy/orchestrator-specs-sample`.
- T03 (qa_execution): `deliverable_repo` omitted.
- T04 (qa_curation): `deliverable_repo: Bontyyy/orchestrator-specs-sample`.

Labels: `type:<kind>`, `autonomy:review`, `state:ready` for T01+T02 (no deps), `state:pending` for T03+T04.

Events emitted: 4× task_created + 2× task_ready (on T01, T02).

Writes:
- 4 issues via `gh issue create` on Bontyyy/orchestrator-api-sample.
- /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0007.jsonl — 6 event lines.

Do NOT:
- Open issues on specs-sample.
- Touch frozen surfaces.
- Merge any PR.
- `git commit` on orchestrator repo.

Verification per issue:
- validate-event.py --file /tmp/<event>.json → exit 0 for each.
- `gh issue view <url> --json number,title,labels,body` — confirm 5 mandatory ## sections + labels + deliverable_repo + ## Deliverables iff deliverable_repo set.

Report back:
- Table: T id, issue URL, labels, deliverable_repo value.
- All 6 events JSON.
- Verification outputs.
- Friction verbatim (especially deliverable_repo adaptation from the worked example).
- Duration + tool-use count.
```

---

### F2 Session 5 — Component implementation on T01

```
You are acting as the component agent (v1.5.0, frozen as Phase 1 baseline) performing an implementation task on Bontyyy/orchestrator-api-sample.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/component/CLAUDE.md.
3. Read each skill under /Users/bonty/Documents/GitHub/orchestrator/agents/component/skills/ that CLAUDE.md references for an implementation task (include verification/SKILL.md).

F2 preamble (5 mitigation clauses). Additional: **F3.1 mitigation — api-sample's .specfuse/verification.yml uses `--no-build` on tests and coverage gates. Before running verification gate sequence, explicitly run `dotnet restore && dotnet build` on the feature branch. A gate sequence run literally on --no-build without a fresh build can trap on stale artifacts (Phase 1 Finding 8). Document this pre-step in your verification evidence.**

Task:
- GitHub issue URL: <FILL IN T01 ISSUE URL FROM SESSION 4>.
- Repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample (local clone). Pull latest main first: `git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample fetch && git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample checkout main && git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample pull`.
- Feature: FEAT-2026-0007 — paginate GET /widgets with page_size query parameter. Implement per AC-1, AC-2, AC-3 as written in the spec at /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0007.md. Read the spec carefully.

Implementation discipline:
- Feature branch name: `feat/FEAT-2026-0007-T01-widgets-pagination` (follow api-sample git log conventions otherwise).
- Add unit tests covering every AC enumerated in the spec.
- Coverage ≥ 90%, zero warnings, all CI gates green.
- Existing widget repository/service abstractions already in the sample repo — reuse, do not refactor.

Expected flow:
- State intent.
- Flip T01 `state:ready → state:in-progress` via `gh issue edit`.
- Emit task_started event (payload requires issue_url + branch per per-type schema).
- Implement on feature branch.
- Pre-gate build: `dotnet restore && dotnet build` (F3.1 mitigation).
- Run all verification gates per .specfuse/verification.yml. Require all pass before reporting.
- Push branch + `gh pr create` with `Closes Bontyyy/orchestrator-api-sample#<N>` in body.
- Flip T01 `state:in-progress → state:in-review`.
- Emit task_completed event on T01 with verification evidence.

Do NOT:
- Merge your own PR.
- Touch .specfuse/verification.yml, branch protection, /agents/*.
- `git commit` on orchestrator repo (event appends stay uncommitted).

Verification evidence:
- PR URL.
- Every gate output (tests N/N, coverage %, warnings, OWASP, lint, build).
- Re-read of task_completed event line.

Report back:
- PR URL + file changes summary.
- Gate outputs.
- Friction verbatim.
- Duration + tool-use count.
```

---

### F2 Session 6 — Human: merge T01 PR (manual)

**Orchestrator actions:**

1. Review T01 PR on api-sample. Confirm CI `verification gates` workflow SUCCESS.
2. Squash-merge via `gh pr merge <N> --squash --delete-branch`.
3. Note T01 merge commit SHA (full 40-char hex) — needed for S10 qa-execution `commit_sha` payload field.
4. Flip T01 issue `state:in-review → state:done` via `gh issue edit`.
5. Issue auto-closes via `Closes` directive (same-repo); if not, `gh issue close <N>`.
6. No second `task_completed` event — S5 subagent already emitted at PR open (F1 convention).

---

### F2 Session 7 — QA qa-authoring on T02

```
You are acting as the QA agent (v1.4.0) performing the qa-authoring skill on FEAT-2026-0007.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-authoring/SKILL.md.

F2 preamble (5 mitigation clauses). Additional:
- **F3.2 mitigation — PR convention PINNED explicit** (SKILL underspecifies):
  - Branch on specs-sample: `qa-authoring/FEAT-2026-0007-T02`.
  - Commit message: `feat(test-plan): FEAT-2026-0007 — widgets list pagination`.
  - Push + `gh pr create` against specs-sample main.
  - PR title: `feat(test-plan): FEAT-2026-0007 — widgets list pagination`.
  - PR body: summary + coverage notes (if any) + `Closes Bontyyy/orchestrator-api-sample#<T02_ISSUE_NUMBER>`.
  - STOP at PR open + `gh pr view <url>`. Do NOT merge.
- **F3.3 mitigation — port convention.** api-sample's launchSettings.json http profile listens on `http://localhost:5083`. Author all `commands[]` in the plan targeting `http://localhost:5083` (NOT 5000). Include `## Coverage notes` mentioning the port choice so qa-execution can re-confirm.

Task:
- GitHub issue URL: <FILL IN T02 ISSUE URL>.
- Feature: FEAT-2026-0007.
- Registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md.
- Spec: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/features/FEAT-2026-0007.md — 3 ACs.
- Deliverable repo clone: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/ (pull latest first: `git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample fetch && git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample checkout main && git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample pull`).

Expected flow per SKILL.md steps 1–7:
- Step 1: intent; flip T02 `state:ready → state:in-progress`; emit task_started (issue_url + branch per per-type schema — the BRANCH here is your specs-sample branch name `qa-authoring/FEAT-2026-0007-T02`).
- Step 2: read registry + spec.
- Step 3: enumerate behaviors. 3 ACs → 3 tests under default cardinality (no scope override collapses this). Expected test_ids (kebab-case, unique within plan):
  - `widgets-list-default-page-size-50` (AC-1)
  - `widgets-list-explicit-page-size-honored` (AC-2)
  - `widgets-list-page-size-over-limit-rejected` (AC-3)
- Step 4: cardinality — scope silent on QA cardinality override → default = 1 test per behavior = 3 tests.
- Step 5: draft plan entries with `covers` quoting AC prose verbatim, `commands` using curl against http://localhost:5083/widgets, `expected` prose predicates per AC.
- Step 6: validate in-memory (schema round-trip via test-plan.schema.json, unique test_ids, coverage check).
- Step 7: write plan at /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/FEAT-2026-0007.md, PR per convention above, emit test_plan_authored event (per-type schema at shared/schemas/events/test_plan_authored.schema.json — payload `{plan_path, test_count: 3}`).

Flip T02 `state:in-progress → state:in-review`. Emit task_completed with PR URL.

Do NOT:
- Merge your own PR.
- Write outside /product/test-plans/ on specs-sample.
- Touch component code on api-sample.
- Flip labels on ANY task other than T02 (Q4 invariant).
- `git commit` on orchestrator repo (event appends stay uncommitted). Commits on specs-sample branch ARE allowed.

Verification per SKILL §Verification:
- Plan file round-trips shared/schemas/test-plan.schema.json.
- Unique test_ids.
- Coverage check: every AC fragment covered.
- test_plan_authored event validates (envelope + per-type).
- Re-read plan file post-write.
- source_version via `bash scripts/read-agent-version.sh qa` (expect 1.4.0).

Report back:
- Full plan file contents (YAML frontmatter + prose).
- PR URL on specs-sample.
- All 3 events JSON (task_started, test_plan_authored, task_completed).
- Verification evidence.
- Friction verbatim — especially any PR-convention ambiguity (F3.2 mitigation stress test) and any startup-command assumption (F3.3).
- Duration + tool-use count.
```

---

### F2 Session 8 — Human: merge qa-authoring PR + close T02 (manual)

**Orchestrator actions:**

1. Review specs-sample PR. Confirm plan validates via test-plan.schema.json.
2. Squash-merge via `gh pr merge <N> --squash --delete-branch` (specs-sample).
3. Flip T02 issue `state:in-review → state:done` via `gh issue edit -R Bontyyy/orchestrator-api-sample <T02_N>`.
4. **Manually close T02** via `gh issue close -R Bontyyy/orchestrator-api-sample <T02_N>` — cross-repo `Closes` doesn't auto-fire (F1 F3.12 confirmed).
5. No second `task_completed` event — S7 subagent already emitted.

---

### F2 Session 9 — PM dependency-recomputation (first invocation)

```
You are acting as the PM agent (v1.6.0 frozen) performing the dependency-recomputation skill on FEAT-2026-0007.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/pm/skills/dependency-recomputation/SKILL.md.

F2 preamble (5 mitigation clauses).

Trigger: T02 task_completed event just appended. T01 and T02 both done. T03 depends_on [T01, T02] is satisfied.

Task:
- Read /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md frontmatter task_graph.
- Read /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0007.jsonl fresh (no cached snapshots).
- For each `pending` task (derived from event log), check if all `depends_on` are `done`. If yes, flip `state:pending → state:ready` on the GitHub issue and emit task_ready.

Expected:
- T03 pending → ready.
- T04 stays pending (dep T03 not done).

Writes:
- Label flip on T03 (issue URL <FILL IN>).
- 1 task_ready event on events/FEAT-2026-0007.jsonl with trigger: "task_completed:T02".

Do NOT:
- Flip T04.
- Touch task_graph or feature state.
- `git commit` on orchestrator repo.

Verification:
- validate-event.py → exit 0.
- gh issue view T03 --json labels → confirms state:ready present, state:pending absent.

Report back: evaluated tasks + dependency status; transitions; events JSON; friction verbatim; duration.
```

---

### F2 Session 10 — QA qa-execution on T03 (expected FAIL on AC-3)

```
You are acting as the QA agent (v1.4.0) performing the qa-execution skill on FEAT-2026-0007.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-execution/SKILL.md.

F2 preamble (5 mitigation clauses). Additional:
- **Important: qa_execution_failed is a VALID QA task completion.** The QA work is to run commands + report evidence; whether the system under test passes or fails is downstream (consumed by qa-regression). A failing test is NOT your problem to fix — report it faithfully per the per-type schema.

Task:
- GitHub issue URL: <FILL IN T03 ISSUE URL>.
- Feature: FEAT-2026-0007.
- Plan file (post-merge): /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/FEAT-2026-0007.md. Pull latest: `git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample fetch && git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample checkout main && git -C /Users/bonty/Documents/GitHub/orchestrator-specs-sample pull`.
- Component repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample. Pull latest: `git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample fetch && git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample checkout main && git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample pull`.
- commit_sha = `git -C /Users/bonty/Documents/GitHub/orchestrator-api-sample rev-parse HEAD` (full 40-char hex) = the T01 merge commit.

Expected flow per SKILL.md steps 1–7:
- Step 1: intent; flip T03 `state:ready → state:in-progress`; task_started (issue_url + branch=main).
- Step 2: resolve plan + commit_sha. Plan round-trips test-plan.schema.json.
- Step 3: idempotence scan — no prior qa_execution_* for (T03, commit_sha).
- Step 4: start service (`dotnet run --project src/OrchestratorApiSample.Api/` from /Users/bonty/Documents/GitHub/orchestrator-api-sample; the launchSettings.json http profile should serve 5083 automatically — if plan uses 5083, native startup works; if plan uses a different port, override via `--urls`). Wait for 200 response. Run each test's commands verbatim. Evaluate `expected` predicate per test.
- Step 5: aggregate. If ANY test fails → qa_execution_failed (per-type schema at shared/schemas/events/qa_execution_failed.schema.json requires failed_tests[] with minItems 1).
- Step 6: validate + append event.
- Step 7: flip T03 `state:in-progress → state:in-review`; emit task_completed.
- Kill the service process. No leak.

Do NOT:
- Modify plan file.
- Flip labels on T01 or any task other than T03 (Q4 invariant — qa-execution SKILL §Verification first bullet).
- Commit to api-sample or open a PR there.
- Touch frozen surfaces.
- `git commit` on orchestrator repo.

Verification per SKILL §Verification:
- All declared commands ran.
- Each test has definite pass/fail verdict.
- qa_execution_completed OR qa_execution_failed event validates (envelope + per-type payload).
- source_version from read-agent-version.sh qa.
- Re-read appended event.

Report back:
- For each test: test_id, commands run, stdout/status captured, expected predicate, pass/fail verdict + first_signal if fail.
- Emitted event JSON (identify whether it's completed or failed).
- commit_sha used.
- Verification evidence.
- Friction verbatim.
- Duration + tool-use count.
```

---

### F2 Session 11 — QA qa-regression (first-failure path)

```
You are acting as the QA agent (v1.4.0) performing the qa-regression skill on FEAT-2026-0007 — FIRST-FAILURE path.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-regression/SKILL.md.
4. Read /Users/bonty/Documents/GitHub/orchestrator/shared/templates/qa-regression-issue.md (v0.2).

F2 preamble (5 mitigation clauses). Additional:
- **Q4 invariant is the primary stress test of this session.** The skill's §Verification first bullet is: "No write to labels or state on any task other than the QA task itself." Specifically: no write to T01 impl task's labels/state, no write to the (not-yet-minted) spawned fix task.
- **No QA-owned task transitions here.** This skill is event-reactive (trigger = qa_execution_failed from S10). No `state:ready → state:in-progress` flip on any task — you're acting on an already-completed-and-closed qa_execution task.

Task:
- Triggering event: the `qa_execution_failed` line appended by S10 to /Users/bonty/Documents/GitHub/orchestrator/events/FEAT-2026-0007.jsonl. Read end-to-end; the triggering event is the last `qa_execution_failed` line.
- Feature registry: /Users/bonty/Documents/GitHub/orchestrator/features/FEAT-2026-0007.md (for Q4 impl_task resolution via depends_on).
- Plan file: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/FEAT-2026-0007.md (for `expected` + `commands` of each failing test).

Expected flow per SKILL.md Steps 1–4A (first-failure):
- Step 1: intent; reload hygiene.
- Step 2: read feature registry; confirm task_correlation_id in task_graph. Read event log fresh.
- Step 3: Q4 resolve implementation_task_correlation_id = intersect T03's depends_on with type=implementation → exactly 1 → T01.
- Step 4A.1: idempotence scan — no prior qa_regression_filed for (T01, failed_test_id).
- 4A.2: read plan; locate failed test entry; capture expected/commands/covers.
- 4A.3: target_repo from T01.assigned_repo = Bontyyy/orchestrator-api-sample.
- 4A.4: write /Users/bonty/Documents/GitHub/orchestrator/inbox/qa-regression/FEAT-2026-0007-<failed_test_id>.md per qa-regression-issue.md template v0.2. Frontmatter fields: correlation_id_feature, test_id, regressed_implementation_task_correlation_id, failing_qa_execution_event_ts, failing_commit_sha, test_plan_path, target_repo. Body: Expected, Observed (first_signal from trigger), Reproduction steps (expand commands), Regression context (mirror frontmatter). Re-read.
- 4A.5: emit qa_regression_filed (per-type schema shared/schemas/events/qa_regression_filed.schema.json; payload keys implementation_task_correlation_id + test_id + failing_qa_execution_event_ts + failing_commit_sha + regression_inbox_file). source_version = 1.4.0.

If failed_tests[] contains multiple entries (unlikely for our naive-impl scenario, but possible), loop 4A for each independently.

Do NOT:
- Write labels or state to T01 or to any not-yet-existent spawned fix task.
- Flip T03 labels (it's already in-review from S10).
- Open GitHub issues (inbox writing only — spawning is out of scope per SKILL).
- Modify plan file.
- Touch frozen surfaces.
- `git commit` on orchestrator repo.

Verification per SKILL §Verification:
- First bullet (Q4): no write to labels/state on non-QA tasks.
- Triggering event envelope + per-type payload parsed.
- implementation_task_correlation_id resolved from task_graph with type=implementation.
- Inbox artifact written + re-read; frontmatter parses + matches triggering event payload.
- qa_regression_filed event validates (envelope + per-type).
- No never-touch path.

Report back:
- Triggering event timestamp + failed_tests identified.
- impl_task resolved.
- Full inbox artifact contents (frontmatter + body).
- qa_regression_filed event JSON.
- Verification evidence — ESPECIALLY your audit of the Q4 first bullet (enumerate every write and confirm none touch T01).
- Friction verbatim.
- Duration + tool-use count.
```

---

### F2 Session 12 — Human: spawn T05 fix task from inbox (manual runbook)

**Orchestrator actions (simulating PM inbox consumer — deferred to later WU per architecture):**

1. Read inbox file `/Users/bonty/Documents/GitHub/orchestrator/inbox/qa-regression/FEAT-2026-0007-<failed_test_id>.md`.
2. Mint T05 correlation ID (next TNN after T04).
3. Update `features/FEAT-2026-0007.md` task_graph: append T05 entry with `{id: T05, type: implementation, depends_on: [], assigned_repo: Bontyyy/orchestrator-api-sample, required_templates: [api-controller, api-request-validator, api-response-serializer]}`. Also append T06 entry with `{id: T06, type: qa_execution, depends_on: [T05, T02], assigned_repo: Bontyyy/orchestrator-api-sample, required_templates: []}` — this is the regression re-execution task (pre-mint it so S15 dep-recomp flips it to ready).
   - **Note on T04 curation dep update**: T04's original `depends_on: [T03]` — add T06 to it so curation waits for resolution: `depends_on: [T03, T06]`. (Open pre-finding — this may surface as PF-7 variant: the task graph shape for regression re-runs isn't explicit in the skills.)
4. Validate frontmatter via `validate-frontmatter.py`.
5. `gh issue create -R Bontyyy/orchestrator-api-sample --title "FEAT-2026-0007/T05 — Fix page_size_over_limit rejection (regression)" --body <body from inbox file> --label "type:implementation" --label "autonomy:review" --label "state:ready"`. Body must follow work-unit-issue.md template v1.1 structure with the inbox file's Expected/Observed/Reproduction sections embedded.
6. Also open T06 issue: `gh issue create -R Bontyyy/orchestrator-api-sample --title "FEAT-2026-0007/T06 — qa-execution re-run after T05 fix" --body <standard qa-execution body> --label "type:qa-execution" --label "autonomy:review" --label "state:pending"`.
7. Emit 2× task_created (T05, T06) + 1× task_ready (T05) events. source: human, source_version: <short SHA>.
8. Record T05 + T06 issue URLs in notes-scratch §6 working notes for S13, S15 references.

**Friction watch:** Novel manual step — log every ambiguity (task_graph shape for regression tasks is underspecified at v1; T06 depends_on edges; whether T04 dep should be updated).

---

### F2 Session 13 — Component implementation on T05 (fix)

```
You are acting as the component agent (v1.5.0, frozen) performing a regression-fix implementation task on Bontyyy/orchestrator-api-sample.

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/component/CLAUDE.md.
3. Read component skills referenced for an implementation task.
4. Read the inbox artifact at /Users/bonty/Documents/GitHub/orchestrator/inbox/qa-regression/FEAT-2026-0007-<failed_test_id>.md — it IS the reproduction brief for this fix.

F2 preamble (5 mitigation clauses). F3.1 mitigation (dotnet build pre-gate — same as S5).

Task:
- GitHub issue URL: <FILL IN T05 ISSUE URL FROM S12>.
- Repo: /Users/bonty/Documents/GitHub/orchestrator-api-sample. Pull latest main first.
- Feature: FEAT-2026-0007/T05 — fix the regression described in the inbox artifact. Specifically: make GET /widgets?page_size=N with N > 500 return HTTP 400 with body `{"error": {"code": "page_size_over_limit", "message": "..."}}` with error.code exactly equal to "page_size_over_limit".

Implementation discipline:
- Feature branch: `fix/FEAT-2026-0007-T05-page-size-over-limit`.
- Add/update unit tests covering AC-3 specifically.
- Do NOT regress existing AC-1, AC-2 tests.
- Coverage ≥ 90%, zero warnings, all gates green.
- dotnet restore && dotnet build before running --no-build gates.

Expected flow:
- State intent.
- Flip T05 `state:ready → state:in-progress`.
- Emit task_started (issue_url + branch).
- Implement fix.
- Verify all gates including the re-run of existing tests.
- Push + `gh pr create` with `Closes Bontyyy/orchestrator-api-sample#<T05_N>`.
- Flip T05 `state:in-progress → state:in-review`.
- Emit task_completed with evidence.

Do NOT:
- Merge own PR.
- Weaken existing tests.
- Touch /agents/*, frozen surfaces.
- `git commit` on orchestrator repo.

Report back: PR URL, file changes, gate outputs, friction, duration.
```

---

### F2 Session 14 — Human: merge T05 PR (manual)

**Orchestrator actions:** Same as S6. Squash-merge, note T05 merge commit SHA (for S16 qa-execution commit_sha), flip T05 `in-review → done`, auto-close via `Closes`.

---

### F2 Session 15 — PM dependency-recomputation (second invocation)

```
You are acting as the PM agent (v1.6.0 frozen) performing dependency-recomputation on FEAT-2026-0007.

Setup + F2 preamble as prior PM sessions.

Trigger: T05 task_completed just appended. T06 depends_on [T05, T02] now satisfied (T02 already done from S8).

Task:
- Read feature registry + event log fresh.
- T06 should flip pending → ready.
- T04 depends_on was updated to [T03, T06] in S12 — T04 stays pending (T06 not done yet).

Writes: T06 label flip + 1 task_ready event with trigger: "task_completed:T05".

Do NOT: flip T04; touch task_graph; `git commit` orchestrator.

Verification: validate-event.py → exit 0; `gh issue view T06 --json labels` confirms ready.

Report back: evaluated tasks, dependency status, transitions, events, friction, duration.
```

---

### F2 Session 16 — QA qa-execution on T06 (expected PASS)

```
You are acting as the QA agent (v1.4.0) performing qa-execution on FEAT-2026-0007 — this is the REGRESSION RE-RUN.

Setup + F2 preamble as S10. This session re-reads rules/SKILL unconditionally per role-switch-hygiene.

Task:
- GitHub issue URL: <FILL IN T06 ISSUE URL>.
- Plan file unchanged at /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/FEAT-2026-0007.md (pull latest).
- Component repo at /Users/bonty/Documents/GitHub/orchestrator-api-sample. Pull main → HEAD is now T05's merge SHA.
- commit_sha for this execution = current api-sample main HEAD (from `git rev-parse HEAD`) — DIFFERENT from S10's commit_sha.

Expected flow per SKILL.md S10 shape:
- Same as S10. Idempotence scan should find no prior event for (T06, new_commit_sha).
- All 3 tests expected to PASS this time (T05 fix addressed AC-3).
- Emit qa_execution_completed (per-type schema at shared/schemas/events/qa_execution_completed.schema.json).

Do NOT: flip T01, T05, any task other than T06 (Q4); modify plan; `git commit` orchestrator.

Verification: as S10.

Report back: per-test verdict (all 3 expected pass), event JSON (qa_execution_completed vs _failed), commit_sha, verification evidence, friction, duration.
```

---

### F2 Session 17 — QA qa-regression (resolution path)

```
You are acting as the QA agent (v1.4.0) performing qa-regression on FEAT-2026-0007 — RESOLUTION path.

Setup + F2 preamble as S11. Re-read unconditionally.

Task:
- Triggering event: last `qa_execution_completed` from S16 on events/FEAT-2026-0007.jsonl.
- Registry + plan as S11.

Expected flow per SKILL.md Steps 1–4C (resolution):
- Steps 1-2: as S11.
- Step 3: Q4 resolve for T06's depends_on filtered to implementation — T06 depends_on = [T05, T02]; filtered to implementation = [T05]. implementation_task_correlation_id = T05.
- Step 4C.1: open regression scan per test_id in plan. For `widgets-list-page-size-over-limit-rejected`: keyed on (T05, test_id) there's no filed event → skip. **BUT the open filed event from S11 is keyed on (T01, test_id) — different impl_task.** Trigger the v1 fallback scan per SKILL §"Deferred — cross-attribution resolution": walk ALL open qa_regression_filed on feature, match any whose test_id appears in current plan, check resolving_commit_sha differs + post-dates failing_commit_sha.
- 4C.2: resolution eligibility — resolving commit from S16 differs from S10's failing commit + post-dates.
- 4C.3: emit qa_regression_resolved. Payload: implementation_task_correlation_id = T01 (from the ORIGINAL filed event, via fallback), test_id, filed_event_ts, resolving_qa_execution_event_ts, resolving_commit_sha.
- 4C.4: scan for outstanding human_escalation on T01 with reason=spinning_detected between filed and resolving ts. NONE expected (single fix attempt; no repeat-failure path triggered). → `escalation_resolved` NOT emitted on this invocation.

Do NOT:
- Flip labels on any task (event-reactive, no QA task transitions here).
- Write to /inbox/ (resolution path is event-only).
- `git commit` orchestrator.

Verification per SKILL §Verification:
- Q4 first bullet: no write to non-QA labels/state — enumerate explicitly in report.
- qa_regression_resolved event validates (envelope + per-type).

Report back: triggering event, Q4 impl_task, fallback-scan match (T01-keyed), qa_regression_resolved JSON, confirm NO escalation_resolved emitted + why (no outstanding spinning escalation), Q4 audit enumeration, friction, duration.
```

---

### F2 Session 18 — Human: close T06 + T04 dep-recomp (manual)

**Orchestrator actions:**

1. Flip T06 `state:in-review → state:done` + close (cross-issue close if needed, but T06 has no external PR deliverable — manual close).
2. Emit `task_completed` for T06 on the event log if not already there (source: human).
3. **Dep-recomp for T04** — T04.depends_on = [T03, T06]. Both done now. Flip T04 `state:pending → state:ready`. Emit task_ready with trigger: "task_completed:T06". **Doing this manually rather than subagent** — it's a trivial case and we've already exercised dep-recomp in S9+S15.

---

### F2 Session 19 — QA qa-curation on T04

```
You are acting as the QA agent (v1.4.0) performing qa-curation on FEAT-2026-0007 (drafting mode).

Setup discipline:
1. Read /Users/bonty/Documents/GitHub/orchestrator/shared/rules/ (8 files).
2. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/CLAUDE.md.
3. Read /Users/bonty/Documents/GitHub/orchestrator/agents/qa/skills/qa-curation/SKILL.md (may exceed 25k — chunk).

F2 preamble (5 mitigation clauses). Additional:
- **Open-regression protection stress test.** Scan cohort includes FEAT-2026-0006 (from F1) and FEAT-2026-0007. The FEAT-2026-0007 feature log has an open `qa_regression_filed` → `qa_regression_resolved` PAIR (S11 filed, S17 resolved) — the regression is CLOSED, so protection should NOT refuse anything for `widgets-list-page-size-over-limit-rejected`. Exercise the protection logic's "already resolved" branch.

Task:
- T04 qa_curation (issue URL <FILL IN>).
- Scan cohort: /Users/bonty/Documents/GitHub/orchestrator-specs-sample/product/test-plans/*.md (2 plans post-F1: FEAT-2026-0006.md + FEAT-2026-0007.md).
- Pull specs-sample latest first.
- Expected candidates:
  - Dedup: check `covers` overlap across 4 tests total (1 in FEAT-0006, 3 in FEAT-0007). No overlap expected — widget-count and widgets-list are distinct endpoints.
  - Orphan: scan feature registries; all ACs covered still exist. No orphans expected.
  - Consolidation: scan qa_execution_failed events within 30d/50-event window. One exists (S10 on FEAT-0007) but a single failure doesn't cluster. No candidates expected.
  - Rename: no rename-request lines.
- **Expected outcome: empty-curation branch** per SKILL §Step 7.

Expected flow per SKILL.md drafting mode:
- Pickup; flip T04 `state:ready → state:in-progress`; task_started.
- Steps 1-4: read + classify → 0 candidates surviving.
- Step 7 empty branch: NO PR, NO regression_suite_curated event. Comment on T04 issue with summary ("Curation pass complete. 0 accepted candidates, 0 refused. Scan covered 2 plans..."). Flip T04 `state:in-progress → state:in-review`. Emit task_completed with `empty_curation: true` additive payload field.

Do NOT:
- Open a PR for an empty-curation pass.
- Emit regression_suite_curated (no PR landed).
- Touch tasks other than T04 (Q4).
- Touch frozen surfaces.
- `git commit` orchestrator.

Verification:
- validate-event.py on task_completed → exit 0.
- gh issue view T04 --json labels → state:in-review.
- tail events/FEAT-2026-0007.jsonl → task_completed with empty_curation:true; NO regression_suite_curated.
- Enumerate protection check on `widgets-list-page-size-over-limit-rejected`: open filed exists but paired resolved exists → not protected = OK to retire IF we had a retire candidate (we don't).

Report back:
- Scan cohort (2 plans).
- Per-plan candidate classification (0 across all 4 kinds).
- Protection-logic exercise summary (resolved pair verification).
- T04 comment text.
- task_completed event JSON.
- Verification evidence including Q4 audit (no non-T04 writes).
- Friction verbatim.
- Duration + tool-use count.
```

---

### F2 Session 20 — Human: close T04 + feature done (manual)

**Orchestrator actions:**

1. Flip T04 `state:in-review → state:done` + close issue.
2. Emit `feature_state_changed(in_progress → done, trigger=all_tasks_done)`. source: human, source_version: <short SHA>.
3. Update features/FEAT-2026-0007.md frontmatter: `state: generating → state: done` (or `in_progress → done` depending on whether S12 or similar flipped generating→in_progress — note F1 had F3.4 gap here; watch for it in F2).
4. If `feature_state_changed(generating → in_progress)` missing from log: retro-emit with trigger=`first_round_issues_opened_retroactive` (F1 F3.4 mitigation pattern).
5. Validate frontmatter + final event.
6. Full event log re-validation: every line via validate-event.py.

---

### Backup branch — qa-curation stress (activate if S10 all-pass OR 2× fix fails)

If triggered, pivot at S10 (for criterion a) or at S13+re-fail (for criterion b). Steps:

1. Document the pivot decision in feature-2-log.md §"Outcome" with triggering criterion + rationale.
2. Seed 3 fixture test plans in specs-sample `/product/test-plans/`:
   - **FEAT-2026-9001.md** — dedup stress: test `widgets-listing-default-limit-50` with `covers: "AC-1: GET /widgets default slice"` (overlaps FEAT-0007 test if F2 reached S7, otherwise overlap fictive).
   - **FEAT-2026-9002.md** — orphan stress: covers AC fragment absent from any real registry.
   - **FEAT-2026-9003.md** — rename stress: prose body contains `rename-request: old-test-id → new-test-id`.
3. Seed 1 `qa_regression_filed` (without paired _resolved) in /events/FEAT-2026-9002.jsonl to exercise protection refusal path.
4. Invoke qa-curation subagent with expanded scan cohort. Expected: PR with dedup merge + orphan retire for FEAT-9002 tests OTHER than the protected one + rename + `refused_candidates` entry for the protected one.
5. Log Q4 audit + friction in feature-2-log.md.

---
