# Shared rules

Prose-form rules that every operational agent in the orchestrator reads before acting. These files are the pulled-in reference that each role's `CLAUDE.md` layers its role-specific behavior on top of. The split is governed by the test in architecture §5.3: **if every operational role must behave identically under the rule, it belongs here; if two roles would diverge, the rule belongs under `/agents/<role>/rules/` instead.**

Prose lives here; the machine contracts it references live in [`/shared/schemas/`](../schemas/README.md), and the document shapes live in [`/shared/templates/`](../templates/README.md). When a rule and a schema or template disagree, the schema or template wins — those artifacts are machine-enforced.

## Contents

- [`correlation-ids.md`](correlation-ids.md) — the `FEAT-YYYY-NNNN` and `FEAT-YYYY-NNNN/TNN` scheme: format, where it must appear, how to mint the next one, and the failure modes for malformed IDs.
- [`state-vocabulary.md`](state-vocabulary.md) — the feature and task state machines, the meaning of each state, and which role owns the entry transition into each one. Mirrors architecture §6.3.
- [`never-touch.md`](never-touch.md) — the five prohibition categories: generated code directories, branch protection configuration, secrets and credentials, `/business/` in the product specs repo, and `.git/` contents.
- [`override-registry.md`](override-registry.md) — how overrides to generated code are authorized, recorded, reconciled, and retired, per architecture §9.3. Reconciliation is the owning component agent's responsibility in the initial model.
- [`escalation-protocol.md`](escalation-protocol.md) — how agents raise inbox files for human attention: the closed enum of reasons, the state-machine effects, and the expected human response loop.
- [`verify-before-report.md`](verify-before-report.md) — the four-step discipline every agent follows: state intent, act, verify, report structured output. Reporting completion without verification is forbidden.
- [`security-boundaries.md`](security-boundaries.md) — read and write surfaces, secrets handling, and the response when a task appears to require privileged access.

## How these files are used

Each role's `CLAUDE.md` under `/agents/<role>/` pulls in the full set above, unmodified, as its shared substrate. The role then layers its own prompts, tools, verification steps, and output formats on top. Reading this directory cover-to-cover is a prerequisite for any agent to execute a task; individual files are cross-referenced from the role-specific layers as needed.

Roles may override a shared rule only with explicit justification in their own `rules/` directory. An override means the shared rule does not apply to that role; the justification documents why the role needs to behave differently, which is the §5.3 test being failed deliberately. In the normal case, no overrides are expected — if a role finds itself wanting to override frequently, the shared rule is likely misscoped and should be revised here instead.

## Revision

This is the v0.1 revision of the shared rules, produced during Phase 0 of the implementation plan. They will evolve as the walkthroughs surface gaps; changes land as normal commits, version-stewarded alongside the rest of `/shared/`. When a rule changes, cross-reference any file — schemas, templates, role configs — that references it, and keep the set coherent.
