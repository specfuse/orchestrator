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
| FEAT-2026-0001 | Local-first, location-agnostic `init` (adoption feature A) | active  | — | — |
| FEAT-2026-0002 | Drivers resolve agent versions from the package (adoption feature B) | planned | — | — |

Status: `planned` → `active` → `done` (or `abandoned`).

## FEAT-2026-0001 — Local-first, location-agnostic `init` (adoption feature A)

**Why.** Post-pip, `specfuse-orchestrator init` still git-inits a fresh repo, carrying the fork-era "one dedicated repo up front" assumption. Broader OSS adopters (solo, monorepo, mixed CI) often want to scaffold state into an existing repo's subdirectory, or just a local folder, with git/GitHub deferred. Accepted decision #1 of `docs/design/adoption-and-collaboration.md`.

**Goal.** Make `init <dir>` local-first and location-agnostic: scaffold the user-owned state dirs into `<dir>` without forcing `git init`; never `gh repo create`. If `<dir>` is already inside a git repo, do not re-init. Add an opt-in `--git` flag to initialize a repo when the user wants one. Rewrite `project/NEXT_STEPS.md` to present the three adoption shapes (dedicated repo / subdir / local-first) with a one-liner each for publishing when ready.

**Benefits.** Zero-commitment start (no repo needed to try it); fits monorepos + subdir layouts; matches how varied OSS users actually begin. Foundation for the §6 onboarding rewrite.

**Status: planned.**

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
