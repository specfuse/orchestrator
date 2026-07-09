---
project: specfuse-orchestrator
---

# Roadmap

The master plan for this repository. Each feature lives in its own folder under
`.specfuse/features/` with a `PLAN.md` (task graph), `GATE-NN.md` files, and
`WU-*.md` files. This roadmap owns *feature* definitions and *feature* status; the
PLAN owns the *graph*; GATE files own *gate* status; WU files own *work-unit* status.
One fact, one home — the same split the Specfuse Orchestrator uses, so this folds in
unchanged.

Detail a feature's first-gate work units when you are ready to start it; the gate
after that is drafted for you by the prior gate's plan-next. Until you start a
feature, a one-line entry here is enough.

Add your first feature with **`/roadmap-add`** (it auto-picks the next
`FEAT-YYYY-NNNN` ID and writes the row + detail section), or add a row by hand in
the canonical column order below.

| Feature ID     | Title | Status | Folder | Detail |
|----------------|-------|--------|--------|--------|
| FEAT-2026-0001 | Local-first, location-agnostic `init` (adoption feature A) | done  | — | [→ archive](roadmap-archive.md#feat-2026-0001) |
| FEAT-2026-0002 | Drivers resolve agent versions from the package (adoption feature B) | done | agent-version-from-package | [→ archive](roadmap-archive.md#feat-2026-0002) |
| FEAT-2026-0003 | E2E-capable QA contracts: test tiers, components, stack manifest | active | — | — |

Status: `planned` → `active` → `done` (or `abandoned`).

## FEAT-2026-0003 — E2E-capable QA contracts: test tiers, components, stack manifest

**Why.** The QA contracts assume single-repo, single-SHA testing: `test-plan.schema.json` (v1 stub) has no notion of test tier or components-under-test, and the `qa_execution_completed` / `qa_execution_failed` event payloads require a single `commit_sha` with idempotence keyed on `(task_correlation_id, commit_sha)`. A cross-component E2E run (e.g. a consumer's Playwright harness driving a deployed multi-service stack) cannot express its result: no single SHA identifies what was tested, and plans cannot distinguish a smoke check from a journey or route a failure to the responsible component. First consumer hitting this wall: RestoManager's `restomanager-e2e` repo.

**Goal.** Additive extension of the QA contracts. Plan schema: optional per-test `tier` (`smoke | contract | journey | regression | uat`) and `components` (repos under test). Execution event payloads: optional `stack_manifest` (component→SHA/version map) plus `manifest_hash`, with the qa-execution skill's idempotence rule updated to key on `(task_correlation_id, manifest_hash)` when a manifest is present, falling back to `commit_sha` for single-repo runs. Document the plan↔harness linkage convention (plan `test_id` ↔ executable-spec tag). QA agent config delta carries the architectural justification the Phase-3 freeze requires.

**Benefits.** Product-level E2E/UAT results become expressible in the existing QA pipeline without breaking single-repo consumers (all new fields optional; existing plans and events validate unchanged). Failure attribution gains the component axis needed for regression-routing triage. Downstream consumers get the extension via the package instead of vendored-schema drift.

**Status: active.**

## Notes

- Correlation IDs are allocated here, sequentially per year: `FEAT-YYYY-NNNN`. Work
  units take `FEAT-YYYY-NNNN/TNN`. The same scheme threads commits (trailer
  `Feature: FEAT-YYYY-NNNN/TNN`), the per-feature event log, and — at fold-in —
  GitHub issues across repos.
- The feature folder name carries the full ID plus a slug, so it greps, sorts, and
  threads cleanly.
- **Read `.specfuse/LEARNINGS.md` before detailing a new feature.** It is the
  accumulated output of every gate's lessons step and exists to make the next plan
  better than the last.
