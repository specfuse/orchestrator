---
project: <repo / project name>
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
| FEAT-2026-0002 | Drivers resolve agent versions from the package (adoption feature B) | planned | — | — |

Status: `planned` → `active` → `done` (or `abandoned`).

## FEAT-2026-0002 — Drivers resolve agent versions from the package (adoption feature B)

**Why.** The drivers read `<state_repo>/agents/<role>/version.md` at runtime (event `source_version`), forcing every consumer to vendor `agents/`. Accepted decision #3 of the adoption design: a consumer should hold ONLY state.

**Goal.** Have the version reader (`specfuse.orchestrator._version`) resolve agent version markers from the installed package/plugin rather than the consumer's `agents/` tree, so drivers no longer depend on vendored `agents/`. This is the enabling change for "consumer holds only state" — it retires the vendoring drift and the downstream-migration question.

**Benefits.** Consumers stop vendoring `agents/`; converting an existing downstream becomes trivial (install package, keep state). Collapses the version streams; no drift.

**Status: planned.**

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
