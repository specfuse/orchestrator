---
id: FEAT-2026-0003/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.60
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - agents/qa/skills/qa-authoring/SKILL.md
gate_set: code
---

# Document the plan ↔ harness linkage convention (`test_id` ↔ executable-spec tag)

**Objective.** Add a normative "Plan ↔ harness linkage" section to the qa-authoring skill
that fixes how a plan's `test_id` binds to the downstream harness's executable-spec tag, so
a cross-component E2E harness's per-test result threads back to the authoring plan and the
`(implementation_task_correlation_id, test_id)` regression key survives the plan/harness
boundary.

**Context.** Feature FEAT-2026-0003 / gate 2, `FEAT-2026-0003/T04` (the consumption layer).
Gate 2's DoD (GATE-02.md) requires: "The plan↔harness linkage convention (plan `test_id` ↔
executable-spec tag) is documented." Home for this convention is
`agents/qa/skills/qa-authoring/SKILL.md` — that skill mints the `test_id`s (see its
`test_id` convention paragraph, "a stable kebab-case identifier unique within this plan",
and the `test_id` stability contract in its §"Deferred integration"). The executable-spec
tag lives on the **downstream** harness (the first consumer is RestoManager's
`restomanager-e2e` repo, per `.specfuse/roadmap.md` / PLAN.md); qa-execution runs that
harness and emits `failed_tests[].test_id`, which must resolve back to a plan `test_id`.

The convention to document:
- The plan's `test_id` is the **source of truth**; the harness's executable spec (a
  Playwright/Arazzo/other scenario) carries the **same** `test_id` as a tag/annotation. The
  binding is by exact string equality on `test_id`.
- The concrete tag mechanism (a Playwright test tag, an Arazzo `x-test-id`, a `@<test_id>`
  annotation, etc.) is the **downstream harness's** choice — it is a cross-repo convention,
  not a schema field. Document it as a convention with the authoritative source named for
  verification at arm time (see the gate review's Cross-repo contracts table); do NOT invent
  a binding the downstream repo does not actually carry.
- Why it is load-bearing: qa-regression keys artifacts on
  `(implementation_task_correlation_id, test_id)`; a cross-component E2E `qa_execution_failed`
  whose `failed_tests[].test_id` cannot resolve to a plan `test_id` breaks regression
  routing. Renames stay a curation-PR concern (the existing `test_id` stability contract),
  preserving open-regression traceability across the harness link.

`agents/qa/` is a Phase-3-frozen surface; the architectural justification for touching it is
recorded by `FEAT-2026-0003/T05` (the QA-agent-config delta), a sibling WU — do not restate
it here. Binding rules in `.specfuse/rules/` apply (reference, do not restate). The
`/authoring-work-units` craft applies — see §8 (verify cross-surface contract values against
the authoritative source; the executable-spec tag is exactly such a value).

Red-test exempt: pure documentation of a convention (skill prose); no executable production
symbol is introduced. The `code` gate is the regression oracle; the grep existence check
below confirms the section landed.

**Acceptance criteria.**
- A new normative section titled "Plan ↔ harness linkage" (or clearly equivalent) is added
  to `agents/qa/skills/qa-authoring/SKILL.md`, stating: (a) the plan `test_id` is the source
  of truth and the harness's executable spec carries the same `test_id` as a tag/annotation
  bound by exact string equality; (b) the concrete tag mechanism is the downstream harness's
  choice, documented as a cross-repo convention (not a schema field); (c) the linkage
  preserves the `(implementation_task_correlation_id, test_id)` regression key across the
  plan/harness boundary, and renames remain a curation-PR concern.
  (`grep -n "harness" agents/qa/skills/qa-authoring/SKILL.md` returns the new section.)
- The section cross-references the `test_id` stability contract already in the skill (it does
  not duplicate or contradict it) and names the downstream harness (`restomanager-e2e`) as
  the first consumer without hard-coding a tag syntax the downstream repo may not use.
- The skill's inline version header is bumped (`v1.1 → v1.2`) with a one-line changelog note
  naming FEAT-2026-0003/T04 and the linkage convention.
- No schema change (`shared/schemas/**` untouched); no new `test-plan.schema.json` field.
  The full `code` set stays green.

**Do not touch.** `shared/schemas/**` and `_substrate/`; `tests/**`; the sibling QA skill
`agents/qa/skills/qa-execution/SKILL.md` (T03) and any other skill; the QA config
`agents/qa/CLAUDE.md` and `agents/qa/version.md` (T05 owns those); secrets, `.git/`,
`PLAN.md status`. The driver owns all git — edit files only.

**Verification.** The `code` set in `.specfuse/verification.yml` as the regression oracle.
Skill-content existence check: `grep -n "harness" agents/qa/skills/qa-authoring/SKILL.md`
returns the new "Plan ↔ harness linkage" section. Confirm the diff touches only
`agents/qa/skills/qa-authoring/SKILL.md`.

**Escalation triggers.** If documenting the linkage turns out to require a new schema field
on the test entry (e.g. a `harness_tag` on each test in `test-plan.schema.json`) rather than
a prose convention, that is a gate-1 contract change — emit `status: blocked` naming the
field rather than adding it to the schema from this doc WU. If the linkage section is absent
from the file you edited, emit `status: blocked` — do not claim complete.
