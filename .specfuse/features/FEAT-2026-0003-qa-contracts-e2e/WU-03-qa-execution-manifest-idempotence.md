---
id: FEAT-2026-0003/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.00
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - agents/qa/skills/qa-execution/SKILL.md
gate_set: code
driver_version: 0.3.11
started_at: 2026-07-09T20:22:13.788352+00:00
duration_seconds: 101.583
cost_usd: 0.803966
input_tokens: 17044
output_tokens: 6344
---

# Key qa-execution idempotence on `(task_correlation_id, manifest_hash)` with `commit_sha` fallback

**Objective.** Rewrite the qa-execution skill's idempotence rule so a run carrying a
`stack_manifest`/`manifest_hash` (a cross-component E2E run) is deduplicated on
`(task_correlation_id, manifest_hash)`, falling back to the existing
`(task_correlation_id, commit_sha)` key for single-repo runs — the consumption-layer
counterpart to the gate-1 schema fields, with **no** schema change.

**Context.** Feature FEAT-2026-0003 / gate 2, `FEAT-2026-0003/T03` (the consumption layer).
Gate 1 shipped the contract: `qa_execution_completed` / `qa_execution_failed` now carry
optional `stack_manifest` (`{slug: sha_or_version}`) and `manifest_hash` (`^[0-9a-f]{64}$`),
with `commit_sha` relaxed to `anyOf[commit_sha | stack_manifest]` (see
`shared/schemas/events/qa_execution_*.schema.json` and the fixture
`shared/schemas/examples/qa_execution_completed_manifest.json`). This WU makes the skill's
idempotence RULE consume those fields; gate 1 already changed the schema — **this WU must
not**.

Target file: `agents/qa/skills/qa-execution/SKILL.md`. The
`(task_correlation_id, commit_sha)` key is stated in four load-bearing places today (the
line numbers cited in the gate-1 plan-next were §Scope, §Inputs, §Step 3 — the key appears
in each; verify against the current file, do not trust the numbers blindly):

1. **§Scope** — the bullet "Enforcing idempotence on `(task_correlation_id, commit_sha)`
   before emitting any event."
2. **§Inputs** — bullet 3, "scanned end-to-end for prior `qa_execution_completed` or
   `qa_execution_failed` entries matching `(task_correlation_id, commit_sha)`."
3. **§Step 3 — Idempotence check** — the match predicate (`payload.commit_sha` equals the
   resolved `commit_sha`) and the surrounding prose.
4. **§Verification** — "no prior event exists for the same `(task_correlation_id, commit_sha)`
   pair (idempotence under replay)."
5. **§Deferred integration → "What persists across Phase 4 and Phase 5"** — "Idempotence key
   `(task_correlation_id, commit_sha)` — load-bearing across every future phase." This must
   generalize so future phases preserve the manifest-aware key, not just the SHA pair.

`agents/qa/` is a Phase-3-frozen surface; the architectural justification for touching it
is recorded by `FEAT-2026-0003/T05` (the QA-agent-config delta), which this WU is a sibling
of. Do not restate the justification here. Binding rules in `.specfuse/rules/` apply
(`result-contract.md`, `never-touch.md`, `correlation-ids.md`, `security-boundaries.md`) —
reference, do not restate. The `/authoring-work-units` craft applies.

Red-test exempt: this WU's deliverable is a behavioral-spec (skill prose) contract, not
executable production code — the idempotence rule is agent-executed prose, not a Python
symbol a unit test can exercise. The `code` gate is the regression oracle (the gate-1
`tests/test_qa_contracts.py` fixtures must stay green, proving no schema/fixture reference
was corrupted); the manifest-keyed "red example" required below is the worked-example proof
that keying on `commit_sha` alone would miss a cross-component replay.

**Acceptance criteria.**
- **§Step 3 — Idempotence check** is rewritten so the match predicate is: an existing
  `qa_execution_completed`/`qa_execution_failed` entry with the same
  `payload.task_correlation_id` **and** — when the current run carries a `stack_manifest` —
  the same `payload.manifest_hash`; **falling back** to the same `payload.commit_sha` when
  the run has no `stack_manifest` (single-repo). The rule compares the **emitted**
  `manifest_hash` field for equality; it does not recompute the hash.
  (`grep -n "manifest_hash" agents/qa/skills/qa-execution/SKILL.md` returns hits inside the
  Step 3 region.)
- The §Scope, §Inputs, and §Verification key references are updated to the same
  manifest-aware form (each now reads as `(task_correlation_id, manifest_hash)` with the
  `commit_sha` fallback, not the bare SHA pair).
- **§Deferred integration → "What persists"** is updated so the invariant future phases must
  preserve is the manifest-aware key (`manifest_hash` when a manifest is present, else
  `commit_sha`), not the `commit_sha`-only pair.
- A worked-example section (a "Run 4 — cross-component E2E replay") is added to
  §"Worked example" proving the manifest-hash key path: a cross-component E2E `qa_execution`
  run whose event carries `stack_manifest` (e.g. `{"api": "<40-hex sha>", "web": "2.1.0"}`)
  and `manifest_hash` (`<64-hex>`) and **no** `commit_sha`; a replay with the same
  `(task_correlation_id, manifest_hash)` is **idempotent-skipped**. The example states
  explicitly that a `commit_sha`-only key would fail to detect this replay (no `commit_sha`
  to match on) — that is why the manifest-hash key is load-bearing. It references the gate-1
  fixture `shared/schemas/examples/qa_execution_completed_manifest.json`.
- The skill's inline version header is bumped (`v1.0 → v1.1`) with a one-line changelog note
  naming FEAT-2026-0003/T03 and the manifest-keyed idempotence rule.
- No change under `shared/schemas/**` (the schema is gate 1's); no change to any
  `tests/**` fixture. The full `code` set stays green.

**Do not touch.** `shared/schemas/**` and the `_substrate/` mirror (gate-1 contract,
hatch-generated); `tests/test_qa_contracts.py` and its fixtures (gate-1 shipped); the sibling
QA skills `agents/qa/skills/qa-authoring/SKILL.md` (T04) and any other skill; the QA config
`agents/qa/CLAUDE.md` and `agents/qa/version.md` (T05 owns those); secrets, `.git/`,
`PLAN.md status`. The driver owns all git — edit files only.

**Verification.** The `code` set in `.specfuse/verification.yml` (build/pytest/ruff/bandit/
coverage) as the regression oracle — it must stay green. Skill-content existence checks
(run from repo root):
- `grep -n "manifest_hash" agents/qa/skills/qa-execution/SKILL.md` — hits in §Step 3, §Scope,
  §Inputs, §Verification, and §Deferred integration.
- `grep -n "stack_manifest" agents/qa/skills/qa-execution/SKILL.md` — the Run 4 worked
  example is present.
- Confirm `shared/schemas/` and `tests/` are unchanged by this WU (the diff touches only
  `agents/qa/skills/qa-execution/SKILL.md`).

**Escalation triggers.** If keying idempotence on `manifest_hash` turns out to require a
schema change after all — e.g. `manifest_hash` cannot be relied on as emitted and needs a
new required field or a derivation constraint the schema must enforce — that belongs in a
re-opened gate 1, not this skill WU. Emit `status: blocked` naming the schema gap rather than
smuggling a contract change into the skill. If the idempotence rule (skill prose) is absent
from the files you edited, emit `status: blocked` — do not claim complete.
