# Gate 2 review & arm — FEAT-2026-0003 (qa-contracts-e2e)

Written by gate 1's `plan-next` (`FEAT-2026-0003/G1-PLAN`). This is the human
review-and-arm checkpoint: read the drafted gate-2 WUs, verify the cross-repo contract
values below against their authoritative sources, then arm by flipping each WU's
`status: draft → pending`. The driver dispatches nothing while a WU is `draft`.

## What gate 2 delivers

The **consumption layer** for the additive QA-contract extension gate 1 shipped. Gate 1
changed the schemas (`tier`/`components` on the plan; `stack_manifest`/`manifest_hash` +
`anyOf` `commit_sha` relaxation on the execution events). Gate 2 makes the QA agent's
skills and config consume those fields. **No gate-2 WU changes a schema** — a concern that
turns out to need one is an escalation back to a re-opened gate 1.

## Drafted WUs (arm order follows `depends_on`)

| WU | File | Deliverable | Traces to |
|----|------|-------------|-----------|
| `T03` | `WU-03-qa-execution-manifest-idempotence.md` | qa-execution SKILL.md idempotence rule keys on `(task_correlation_id, manifest_hash)` with `commit_sha` fallback; manifest-keyed "red example" | GATE-02 DoD bullet 1 |
| `T04` | `WU-04-plan-harness-linkage-convention.md` | qa-authoring SKILL.md documents the plan `test_id` ↔ executable-spec tag linkage | GATE-02 DoD bullet 2 |
| `T05` | `WU-05-qa-agent-config-delta.md` | `agents/qa/version.md` records the Phase-3-freeze justification tying each `agents/qa/` touch; `agents/qa/CLAUDE.md` idempotence-key references aligned | GATE-02 DoD bullet 3 |
| `G2-CLOSE` | `WU-90-gate-2-close.md` | terminal close + verdict (already scaffolded) | terminal ceremony |

`depends_on`: `T03` and `T04` are independent (different skill files). `T05` depends on
both (its version.md entry enumerates their final versions). `G2-CLOSE` depends on all three.
Every WU traces to a GATE-02 DoD bullet — no invented scope.

## Phase-3-freeze note (read before arming)

`agents/qa/` is frozen as the Phase 3 baseline (2026-04-24). All three substantive WUs touch
it. The **single architectural justification** — the RestoManager `restomanager-e2e` consumer
cannot express a cross-component E2E result under single-SHA testing — is recorded once, by
`T05`, in `agents/qa/version.md`, and cites `docs/walkthroughs/phase-3/retrospective.md`
§"Phase 3 freeze declaration". `T03` and `T04` reference that record rather than restating it.

## Cross-repo contracts — verify against the authoritative source before arming

Per `/authoring-work-units` §8, a `plan-next` draft systematically invents plausible but
unverified downstream values. Each row below is a value referenced by a gate-2 WU that lives
in **another repo/system** and must be checked against its source before that WU is armed.

| Value | Used by | Authoritative source | Status |
|-------|---------|----------------------|--------|
| The executable-spec **tag mechanism** carrying `test_id` (Playwright tag vs Arazzo `x-test-id` vs `@<test_id>` annotation) | `T04` | RestoManager `restomanager-e2e` harness repo (the actual scenario files) | ☐ unverified — T04 deliberately documents the tag as the *downstream's choice* and does not hard-code a syntax; confirm the repo actually carries `test_id` verbatim |
| `manifest_hash` **derivation convention** (how the emitting harness computes the 64-hex hash from `stack_manifest` — e.g. sha256 of canonical-JSON) | `T03` | `restomanager-e2e` emitter + gate-1 `qa_execution_completed.schema.json` (`^[0-9a-f]{64}$` only constrains shape, not derivation) | ☐ unverified — T03's rule compares the *emitted* `manifest_hash` field and does not recompute it, so equality is sound regardless of derivation; still confirm the emitter produces a *stable* hash for the same stack |
| `stack_manifest` slug vocabulary (`api`, `web`, …) | `T03` example | gate-1 schema (`{slug: sha_or_version}`, additive) + the consumer's repo slugs | ☑ schema'd in gate 1; example values are illustrative only |

The two unchecked rows are **not blockers to authoring** — both WUs are written to avoid
depending on the unverified specifics (tag mechanism = downstream's choice; hash = compared as
emitted). Check them at arm time so the shipped convention matches the real harness, then tick.

## To arm

1. Confirm each drafted WU's five sections read cleanly for a cold session.
2. Resolve the two ☐ rows above against the `restomanager-e2e` repo.
3. Flip `status: draft → pending` on `WU-03`, `WU-04`, `WU-05` (and `WU-90-gate-2-close.md`
   when ready). Leave `PLAN.md status: active` — the driver owns the terminal flip.
4. `specfuse-lint` the feature dir to confirm structural validity after arming.
