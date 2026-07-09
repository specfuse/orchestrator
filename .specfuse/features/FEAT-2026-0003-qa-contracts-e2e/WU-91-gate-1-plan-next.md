---
id: FEAT-2026-0003/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 0.50
generated_surfaces: []
model: opus
effort: high
gate_set: plannext
---

# Gate 1 plan-next — draft gate 2's work units

**Objective.** Draft gate 2's substantive work units (the consumption layer) from gate 1's
retrospective and lessons, inserting them before the `G2-CLOSE` placeholder and setting its
`depends_on`.

**Context.** Runs after `G1-CLOSE-INTERMEDIATE`. Gate 2's definition of done (GATE-02.md):
qa-execution idempotence keyed on `(task_correlation_id, manifest_hash)` with `commit_sha`
fallback; the plan↔harness linkage convention documented; the QA-agent-config delta
carrying the Phase-3-freeze architectural justification for touching `agents/qa/`. Binding
rules and the `/authoring-work-units` craft apply.

**Acceptance criteria.**
- Gate 2's substantive WUs are drafted (`status: draft`) with five-section bodies, wired
  into `PLAN.md`'s gate-2 `work_units` graph ahead of `G2-CLOSE`, and `G2-CLOSE`'s
  `depends_on` is updated to the drafted WUs.
- The idempotence-rule WU targets `agents/qa/skills/qa-execution/SKILL.md` (steps 3, 15,
  71 carry the `(task_correlation_id, commit_sha)` key today) and includes a red example
  proving the manifest-hash key path; it must NOT change the schema (gate 1 did that).
- The QA-agent-config-delta WU names where the Phase-3-freeze justification is recorded and
  ties each `agents/qa/` change to it.
- `GATE-NN-REVIEW.md` is written for the human review-and-arm checkpoint.
- Each drafted WU traces to gate 2's DoD or a gate-1 lesson — no invented scope.

**Do not touch.** Gate 1's shipped schemas/tests, `_substrate/`, secrets, `.git/`,
`PLAN.md status`.

**Verification.** The `plannext` gate set (`specfuse-lint {feature_dir}` must pass with
the newly drafted gate 2).

**Escalation triggers.** If a gate-2 concern turns out to need a schema change after all
(so it belongs in a re-opened gate 1, not gate 2), emit `status: blocked` naming it rather
than smuggling a contract change into a skill/doc WU.
