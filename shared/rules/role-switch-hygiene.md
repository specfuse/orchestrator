# Role-switch hygiene

The shared rule set under `/shared/rules/` must be re-read **unconditionally at the start of every task**, including when the agent is switching roles within a single session.

## Why

The `/shared/rules/` directory is the load-bearing substrate under every role's `CLAUDE.md`. An agent that skips re-reading it on a role-switch carries forward stale context from its previous role: rule amendments since the session's last read are invisible, and role-specific overrides that applied under the previous role (and should not apply under the new one) can bleed through without notice.

The failure mode is silent. A rule that applies non-obviously to the new role can be missed, producing a correctness bug downstream. Phase 1 walkthrough Task A surfaced the pattern — see `docs/walkthroughs/phase-1/retrospective.md` §"Finding 6". No rule was in fact missed in that instance, but the discipline gap was observed and the retrospective scheduled it as a Phase 2 absorption item. This file is that absorption: it extends the implicit "read before acting" directive in every `CLAUDE.md` to the within-session role-switch case that was previously implicit.

## The rule

Before performing any action under a role:

1. Re-read the full `/shared/rules/*` set, regardless of whether the current session has read them earlier under a different role.
2. Re-read the `CLAUDE.md` and skills of the new role.
3. Then, and only then, proceed with the task's intent (step 1 of [`verify-before-report.md`](verify-before-report.md)).

The re-read is the action. "I read them a few minutes ago" is not the re-read; "I remember what they say" is not the re-read. The rule is strict because the failure mode it prevents is silent.

## When this applies

- The start of every task, every time.
- Every role-switch within a single session — for example, a session that co-pilots planning with the PM agent and then hands off to the component agent for implementation: the component agent re-reads before acting, even though the session has already read the shared rules minutes earlier.
- Every resumption of a previously-paused session where more than one role will run.

A fresh-session start is already covered by the "read before acting" directive in each role's `CLAUDE.md`; this rule is the additional commitment that the directive is not weakened by a prior in-session read under a different role.

## Scope and exceptions

This rule is shared because every operational role is subject to it symmetrically — the §5.3 test in [`orchestrator-architecture.md`](../../docs/orchestrator-architecture.md). It lives here, rather than duplicated into each role's `rules/` directory, precisely to prevent per-role drift of the re-read discipline.

There are no exceptions at v0.1. A future revision may narrow the scope (e.g., skip the re-read if the session has not advanced past a role's own substrate), but any such narrowing must come with the justification and walkthrough evidence the retrospective protocol requires for shared-rule amendments.

## References

- [`docs/walkthroughs/phase-1/retrospective.md`](../../docs/walkthroughs/phase-1/retrospective.md) §"Finding 6" — the originating observation (Task A, component agent, no rule missed but discipline gap noted) and the deferral rationale that scheduled this rule for Phase 2 absorption.
- [`verify-before-report.md`](verify-before-report.md) — the four-step cycle this rule is a prerequisite to.
- [`docs/orchestrator-implementation-plan.md`](../../docs/orchestrator-implementation-plan.md) §"Work unit 2.1 — PM agent config v1" — the work unit that codified this rule.
