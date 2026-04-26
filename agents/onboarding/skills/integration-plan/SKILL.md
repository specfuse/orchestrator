# SKILL: integration-plan — v0.1.0

For a brownfield project (one with existing code, specs, and possibly in-flight features), draft a phased integration plan at `/project/integration-plan.md`. The plan sequences how the team adopts the orchestrator without disrupting current delivery.

This is a v0.1 working draft intended to be exercised on a real project and hardened. Greenfield projects use [`bootstrap-greenfield`](../bootstrap-greenfield/SKILL.md) instead.

## When to invoke

- After `repo-inventory` has produced the project manifest and per-repo inventory entries.
- Once per project at integration time. Re-run if the inventory or project goals change substantially.

## Inputs the agent reads

- `/project/manifest.md` — the project overview and repo list.
- `/project/repos/*.md` — every per-repo inventory entry (this is the grounding source — the plan refers only to repos and gaps documented in the inventory).
- The orchestration repo's `/agents/`, `/shared/`, `/scripts/` for current orchestrator capabilities.
- [`docs/operator-runbook.md`](../../../../docs/operator-runbook.md) and [`docs/operator-pipeline-reference.md`](../../../../docs/operator-pipeline-reference.md) for the operational target state.
- Conversation with the human: goals, constraints, deadlines, risk tolerance.

## Procedure

### Step 1 — Confirm the inventory is current

Read `/project/manifest.md` and every file under `/project/repos/`. Confirm:

- Every involved repo from the manifest has a corresponding inventory entry.
- Inventory `Inventoried:` dates are recent enough to trust (operator judgment — typically within the last month).
- No entry has unresolved "TBD" placeholders.

If the inventory is stale or incomplete, escalate or recommend running `repo-inventory` first. Do not draft a plan against shaky data.

### Step 2 — Conversation: goals, constraints, deadlines

Ask the human:

- **Why are you adopting the orchestrator?** Specific outcomes (e.g., reduce coordination overhead, enforce spec discipline, automate QA) — frames the success criteria.
- **What's the timeline?** Is there a deadline by which the team needs to be running on the orchestrator, or is adoption open-ended?
- **What's the risk tolerance?** Can in-flight features be paused/redirected, or must they continue uninterrupted?
- **Are there parts of the project explicitly out of scope for orchestrator adoption?** (E.g., a legacy repo in maintenance mode that nobody wants to onboard.)
- **Who owns each onboarding action?** The human's plan-execution capacity is the gating constraint; if the integration plan recommends 50 actions and one operator, sequence accordingly.

Capture the answers — they shape the plan's phasing.

### Step 3 — Identify per-repo onboarding gaps

Aggregate the `## Onboarding actions` checklist from every `/project/repos/*.md` inventory entry. Group by repo and by action type:

- **Templates surface** — repos missing `.specfuse/templates.yaml`.
- **Repo-specific conventions** — repos missing a root `CLAUDE.md` describing build/test/lint quirks.
- **Generation boundary** — repos without a clear `_generated/` (or equivalent) marker.
- **Overrides registry** — repos with regenerated code but no `/overrides/` records.
- **CI / branch protection** — repos missing the gates the merge watcher will rely on.
- **Spec coverage** — repos whose acceptance-criteria style is too informal for QA-authoring to consume.
- **`gh` access** — repos where the operator's `gh` CLI is not yet authenticated/scoped.

The aggregated list is the raw material for the plan's per-repo onboarding sections.

### Step 4 — Draft the phased plan

Produce `/project/integration-plan.md` with the structure below. **Phasing** is the plan's distinctive choice — adopting everything at once is rarely correct on a brownfield project. Typical phasing:

- **Phase A — Pilot (one new feature, one repo).** Pick a single new feature and a single component repo with the cleanest onboarding posture. Do all the per-repo onboarding for that repo only. Run the feature end-to-end through the operator runbook. Capture friction; don't expand until Phase A succeeds.
- **Phase B — Expand component coverage (remaining new features, more repos).** Onboard the remaining component repos. Continue running new features only — no in-flight import yet.
- **Phase C — In-flight import (selective).** For in-flight features at natural breakpoints (next feature transition, next major merge), retroactively mint feature registry entries and bring them under orchestrator coordination. Skip features close to completion — let them finish in the existing workflow.
- **Phase D — Steady state.** All net-new features go through the orchestrator. Existing-workflow features are wound down. Decide on auto-merge, regression-suite curation cadence, etc.

Each phase has explicit **entry conditions**, **exit criteria**, and **estimated duration** (operator's judgment, not the agent's invention).

### Step 5 — Risk register

For each known risk, record:

- **What** — concrete description of what could go wrong.
- **Likelihood** — operator's qualitative judgment (low/medium/high).
- **Impact** — what happens if it materializes.
- **Mitigation** — concrete action the plan takes (or surfaces as a contingency).

Common risks on a brownfield rollout:

- A repo's existing convention conflicts with an orchestrator expectation (e.g., generated code intermixed with hand-written code; no clear boundary).
- An in-flight feature reaches completion mid-rollout and the operator must decide whether to import or let it finish in the old workflow.
- An existing CI configuration doesn't expose the gates the merge watcher needs.
- The team's product-discussion habit doesn't currently funnel into the product reference repo, leaving the specs agent without an upstream source for feature ideas.
- The Specfuse CLI isn't installed (Phase 4 finding F4.1) — silently degrades validation.

### Step 6 — Success criteria

Concrete, observable criteria for declaring the integration "done":

- A specific number of features delivered through the orchestrator end-to-end.
- All involved repos have completed their per-repo onboarding actions.
- The team's product-discussion habit funnels into the product reference repo, and feature-intake sessions consume from there.
- (Optional) Auto-merge enabled, or a documented decision not to enable it.

### Step 7 — Verification

- Re-read `/project/integration-plan.md` after writing.
- Confirm every per-repo onboarding action references a specific repo from the inventory (no generic recommendations).
- Confirm phase entry/exit conditions are observable (not "team is comfortable" — that's not testable).
- Confirm the risk register has named mitigations, not just named risks.
- Confirm success criteria are observable.

### Step 8 — Optional event emission

Append an `onboarding_artifact_produced` event to `/events/PROJ-<slug>.jsonl` (synthetic correlation ID, envelope-only validation).

## Plan template

```markdown
# Integration plan — <project name>

**Drafted:** <YYYY-MM-DD>
**Plan version:** v0.1
**Type:** Brownfield

## Goals

<from Step 2: the "why" the human stated, in their own words>

## Constraints

- **Timeline:** <open-ended / deadline:YYYY-MM-DD>
- **Risk tolerance:** <description>
- **Out of scope:** <repos or features explicitly not part of this rollout>
- **Operator capacity:** <hours per week / FTEs the human can dedicate to onboarding actions>

## Phases

### Phase A — Pilot

- **Entry:** <what must be true before this phase starts — e.g., inventory complete>
- **Scope:** Pilot feature `<feature title>` on `<pilot-repo-slug>`.
- **Onboarding actions for `<pilot-repo-slug>`:**
  - [ ] <specific action 1>
  - [ ] <specific action 2>
- **Pilot feature execution:** Run end-to-end via [`docs/operator-runbook.md`](../docs/operator-runbook.md).
- **Exit:** <what must be true to declare this phase done — e.g., feature merged, retrospective captured>
- **Duration estimate:** <operator's call>

### Phase B — Expand component coverage

- **Entry:** Phase A exit conditions met.
- **Scope:** Onboarding actions for `<remaining repo slugs>`. Continue running net-new features only.
- **Onboarding actions:** <aggregated from /project/repos/ for repos in scope>
- **Exit:** All in-scope repos have orchestrator-readiness checklists complete; <N> features delivered through the orchestrator.
- **Duration estimate:** <operator's call>

### Phase C — In-flight import (selective)

- **Entry:** Phase B exit conditions met.
- **Scope:** Bring selected in-flight features under orchestrator coordination at natural breakpoints.
- **Selection criteria:** <which in-flight features are imported, and why>
- **Per-feature actions:** Mint `/features/FEAT-YYYY-NNNN.md` retroactively; populate task_graph to match current state; the event log starts empty (no historical reconstruction).
- **Exit:** Specified in-flight features are running on the orchestrator or have completed in the old workflow.
- **Duration estimate:** <operator's call>

### Phase D — Steady state

- **Entry:** Phase C exit conditions met.
- **Scope:** All net-new features go through the orchestrator. Decide on auto-merge, regression cadence, Phase 5 readiness.
- **Exit:** Steady state achieved; integration plan is closed.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| <concrete risk> | <low/med/high> | <description> | <concrete mitigation or contingency> |
| ... | ... | ... | ... |

## Success criteria

- [ ] <observable criterion 1>
- [ ] <observable criterion 2>
- [ ] ...

## Open decisions

<things the human deferred during planning conversation — explicit list, not buried in prose>
```

## Worked example

For the Acme Widget Tracker project (3 repos, 2 in-flight features, deadline in 8 weeks):

- Phase A: pilot feature "Widget archive endpoint" on `acme-api` (cleanest onboarding posture). Add `.specfuse/templates.yaml`, root `CLAUDE.md`, mark `_generated/`. Run end-to-end. Estimated 2 weeks.
- Phase B: onboard `acme-web`. Run two net-new features. Estimated 3 weeks.
- Phase C: import in-flight feature WIDG-42 (currently in code review — too late, let it finish). Import in-flight feature WIDG-44 (in early implementation — natural breakpoint). Estimated 2 weeks.
- Phase D: steady state, decide on auto-merge after 6 weeks of clean QA cycles. Estimated 1 week.

Risk register names the specific in-flight features and the specific CI gaps.

## Friction the v0.1 expects

- **Phasing decisions are operator judgment, not algorithmic.** The agent suggests; the human decides. Phase boundaries, durations, and selection criteria are not computed.
- **The plan goes stale.** Real-world execution diverges from the plan within weeks. The skill is happy to be re-run; treat the plan as a living document, not a contract.
- **Mid-rollout repo additions.** If a new repo joins the project mid-rollout, run `repo-inventory` for it and re-run `integration-plan` to fold it in.

## Anti-patterns

- Producing a plan against a stale or absent inventory (anti-pattern #5 in the role config).
- Generic recommendations not tied to specific repos or specific in-flight features (anti-pattern: integration plans must be grounded).
- Phase entry/exit conditions that aren't observable ("team is ready" → not testable; "feature merged + retrospective committed" → testable).

## Where this v0.1 is likely to evolve

- Programmatic readiness checks (does `.specfuse/templates.yaml` validate? does the repo's CI expose the merge-watcher gates?) — currently human-and-agent judgment.
- Multi-quarter rollout templates — v0.1 assumes a single integration project, not a sustained adoption program.
- Integration with Phase 5 generator-feedback — once that lands, the plan can include generator-template work in its scope.
