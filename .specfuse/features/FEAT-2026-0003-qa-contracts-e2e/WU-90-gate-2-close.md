---
id: FEAT-2026-0003/G2-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 0.40
generated_surfaces: []
model: opus
effort: high
gate_set: plannext
---

# Gate 2 close (terminal) — retrospective + lessons + docs + verdict

**Objective.** Terminal close for FEAT-2026-0003: retrospective, lessons, docs, cost
analysis, and the feature verdict.

**Context.** Terminal gate of the QA-contracts-E2E feature. Placeholder drafted at feature
creation so lint reads gate 1 as non-terminal; gate 1's `plan-next` inserts gate 2's
substantive WUs before this and sets this WU's `depends_on`. The driver owns the
`PLAN.md status -> done` flip (gated on `verdict: met`) — do not write it here. Binding
rules in `.specfuse/rules/`.

**Acceptance criteria.**
- `RETROSPECTIVE.md` gains a `## Gate 2` section; `verdict` frontmatter; a
  `### Failure-class breakdown` if any attempt failed.
- Lessons appended to `.specfuse/LEARNINGS.md` (or an explicit none-generalized note).
- A `## Cost analysis` section reconciling `planned_cost_usd` (PLAN.md + per-WU
  frontmatter) against actual spend (events.jsonl), with the delta named.
- A `## What the loop did NOT verify` section enumerating any acceptance criterion whose
  verification was deferred; or `(nothing — every acceptance criterion was verified
  in-loop)`. If >2 entries or >30% of criteria, flag sizing under `## What I'd change`.
- **Backwards note:** record that the QA-contract extension is fully additive — every new
  field optional, `commit_sha` relaxed via `anyOf`, existing plans/events validate
  unchanged; the downstream harness implementation (RestoManager `restomanager-e2e`) is
  out of scope and consumes the contracts post-merge.
- Verdict stated with justification.

**Do not touch.** Source once implemented, `_substrate/`, `agents/` beyond what gate 2's
substantive WUs declare, secrets, `.git/`, `PLAN.md status`.

**Verification.** The `plannext` gate set; RETROSPECTIVE has the required sections.

**Escalation triggers.** If the feature's DoD is not met, emit `status: blocked` with a
`partial`/`unmet` verdict rather than closing green.
