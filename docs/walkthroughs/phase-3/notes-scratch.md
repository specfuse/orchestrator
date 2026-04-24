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

## 4 — Real-time walkthrough notes

Append here during execution. Format: `YYYY-MM-DD HH:MM` + session N + observation. Keep entries lapidary — 1–3 bullets per session. Post-session, write up the detailed log in feature-1-log.md.

```
(empty — filled during walkthrough)
```
