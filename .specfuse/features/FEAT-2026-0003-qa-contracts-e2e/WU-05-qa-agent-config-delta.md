---
id: FEAT-2026-0003/T05
type: implementation
status: done
attempts: 1
planned_cost_usd: 0.60
model: sonnet
effort: medium
generated_surfaces: []
produces:
  - agents/qa/version.md
  - agents/qa/CLAUDE.md
gate_set: code
driver_version: 0.3.11
started_at: 2026-07-09T20:24:44.875598+00:00
duration_seconds: 58.748
cost_usd: 0.587927
input_tokens: 7575
output_tokens: 3648
---

# QA-agent-config delta — record the Phase-3-freeze justification and align the idempotence-key references

**Objective.** Reconcile the QA agent's config surface with the gate-2 skill changes:
record — in `agents/qa/version.md` — the single architectural justification the Phase-3
freeze requires for touching `agents/qa/` in this feature, tie each `agents/qa/` change to
it, and update the two places in `agents/qa/CLAUDE.md` that state the qa-execution
idempotence key as `(task_correlation_id, commit_sha)` to the manifest-aware form.

**Context.** Feature FEAT-2026-0003 / gate 2, `FEAT-2026-0003/T05` (the consumption layer),
runs after `T03` and `T04`. Gate 2's DoD (GATE-02.md): "The QA-agent-config delta carries
the architectural justification the Phase-3 freeze requires for touching `agents/qa/`."

**Where the freeze is declared and where justification is recorded.** The QA config is
"Frozen as the Phase 3 baseline on 2026-04-24" — `agents/qa/CLAUDE.md` top banner and
`agents/qa/version.md` both say "Changes to this config during Phase 4+ require architectural
justification" and cite `docs/walkthroughs/phase-3/retrospective.md` §"Phase 3 freeze
declaration" as the source of record. The **record surface** for each change's justification
is the `agents/qa/version.md` changelog (see how v1.5.3 / v1.5.2 entries each carry their own
justification and freeze-compat statement). This WU adds the FEAT-2026-0003 entry there.

**The architectural justification** (state it once, in the version.md entry): the QA contracts
assumed single-repo, single-SHA testing; the first cross-component E2E consumer —
RestoManager's `restomanager-e2e` — cannot express a result because no single `commit_sha`
identifies what was tested (per PLAN.md / `.specfuse/roadmap.md`). Gate 1 extended the schemas
additively; gate 2's consumption layer requires the qa-execution idempotence rule to key on
`manifest_hash` and the plan↔harness linkage to be documented. Those changes necessarily touch
the frozen QA config surface, which is why this justification is recorded.

**The three `agents/qa/` touches to tie to it** (enumerate them in the version.md entry):
1. `agents/qa/skills/qa-execution/SKILL.md` (v1.0 → v1.1) — manifest-keyed idempotence rule
   (FEAT-2026-0003/T03).
2. `agents/qa/skills/qa-authoring/SKILL.md` (v1.1 → v1.2) — plan↔harness linkage convention
   (FEAT-2026-0003/T04).
3. `agents/qa/CLAUDE.md` — idempotence-key reference alignment (this WU).

`agents/qa/CLAUDE.md` states the `(task_correlation_id, commit_sha)` key in two load-bearing
spots that must now read as manifest-aware:
- **§Anti-patterns #5** — "Emitting duplicate `qa_execution_*` events for the same
  `(task_correlation_id, commit_sha)` pair."
- **§Role-specific verification**, the qa-execution bullet — "confirms no prior event exists
  for the same `(task_correlation_id, commit_sha)` pair (idempotence under replay)."

Both should generalize to `(task_correlation_id, manifest_hash)` when a `stack_manifest` is
present, falling back to `(task_correlation_id, commit_sha)` — matching T03's rule. Do NOT
rewrite the freeze banner's wording; the justification lives in version.md.

Binding rules in `.specfuse/rules/` apply (reference, do not restate). The
`/authoring-work-units` craft applies.

Red-test exempt: documentation/config reconciliation (markdown); no executable production
symbol introduced. The `code` gate is the regression oracle; the grep checks below confirm
the deltas landed.

**Acceptance criteria.**
- `agents/qa/version.md` gains one new changelog entry that (a) bumps the QA agent config
  version (minor bump — the skills' behavior changes; e.g. 1.5.3 → 1.6.0), (b) states the
  single architectural justification above, citing `docs/walkthroughs/phase-3/retrospective.md`
  §"Phase 3 freeze declaration" as the freeze source of record, and (c) enumerates the three
  `agents/qa/` touches (T03 qa-execution v1.0→v1.1, T04 qa-authoring v1.1→v1.2, this CLAUDE.md
  delta), each tied to the justification.
  (`grep -n "FEAT-2026-0003" agents/qa/version.md` and `grep -n "Phase 3 freeze" agents/qa/version.md`
  both return the new entry.)
- `agents/qa/CLAUDE.md` §Anti-patterns #5 and the §Role-specific-verification qa-execution
  bullet both state the manifest-aware key (`manifest_hash` when a manifest is present, else
  `commit_sha`), consistent with T03.
  (`grep -n "manifest_hash" agents/qa/CLAUDE.md` returns hits at both spots.)
- The top freeze banner's wording is unchanged; the version header at the top of CLAUDE.md is
  updated only if the file already couples a version string to the banner (keep it consistent
  with the version.md bump).
- No schema change (`shared/schemas/**` untouched); no skill-body edit (T03/T04 own the skill
  files). The full `code` set stays green.

**Do not touch.** The skill files `agents/qa/skills/qa-execution/SKILL.md` (T03) and
`agents/qa/skills/qa-authoring/SKILL.md` (T04) — read them to describe their versions, but
edit only `agents/qa/version.md` and `agents/qa/CLAUDE.md`; `shared/schemas/**` and
`_substrate/`; `tests/**`; secrets, `.git/`, `PLAN.md status`. The driver owns all git —
edit files only.

**Verification.** The `code` set in `.specfuse/verification.yml` as the regression oracle.
Content existence checks (from repo root):
- `grep -n "FEAT-2026-0003" agents/qa/version.md` — the new changelog entry is present.
- `grep -n "Phase 3 freeze" agents/qa/version.md` — the justification cites the freeze source.
- `grep -n "manifest_hash" agents/qa/CLAUDE.md` — both key references are updated.
Confirm the diff touches only `agents/qa/version.md` and `agents/qa/CLAUDE.md`.

**Escalation triggers.** If reconciling the config reveals that the gate-2 change is not a
justifiable amendment to the frozen baseline but an actual violation of the freeze's intent
(a behavioral divergence the architecture forbids, not merely one that needs justification),
emit `status: blocked` for a human architectural decision rather than writing a justification
that papers over it. If the version.md justification entry is absent from the file you
edited, emit `status: blocked` — do not claim complete.
