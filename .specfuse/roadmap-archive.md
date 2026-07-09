---
project: <repo / project name>
---

# Archived feature details

This file holds the detail sections for features whose status has reached `done` or `abandoned`.

<!-- Archived sections appended below -->
<a id="feat-2026-0002"></a>
## FEAT-2026-0002 — Drivers resolve agent versions from the package (adoption feature B)

**Why.** The drivers read `<state_repo>/agents/<role>/version.md` at runtime (event `source_version`), forcing every consumer to vendor `agents/`. Accepted decision #3 of the adoption design: a consumer should hold ONLY state.

**Goal.** Have the version reader (`specfuse.orchestrator._version`) resolve agent version markers from the installed package/plugin rather than the consumer's `agents/` tree, so drivers no longer depend on vendored `agents/`. This is the enabling change for "consumer holds only state" — it retires the vendoring drift and the downstream-migration question.

**Benefits.** Consumers stop vendoring `agents/`; converting an existing downstream becomes trivial (install package, keep state). Collapses the version streams; no drift.

**Status: planned.**

<a id="feat-2026-0001"></a>
## FEAT-2026-0001 — Local-first, location-agnostic `init` (adoption feature A)

**Why.** Post-pip, `specfuse-orchestrator init` still git-inits a fresh repo, carrying the fork-era "one dedicated repo up front" assumption. Broader OSS adopters (solo, monorepo, mixed CI) often want to scaffold state into an existing repo's subdirectory, or just a local folder, with git/GitHub deferred. Accepted decision #1 of `docs/design/adoption-and-collaboration.md`.

**Goal.** Make `init <dir>` local-first and location-agnostic: scaffold the user-owned state dirs into `<dir>` without forcing `git init`; never `gh repo create`. If `<dir>` is already inside a git repo, do not re-init. Add an opt-in `--git` flag to initialize a repo when the user wants one. Rewrite `project/NEXT_STEPS.md` to present the three adoption shapes (dedicated repo / subdir / local-first) with a one-liner each for publishing when ready.

**Benefits.** Zero-commitment start (no repo needed to try it); fits monorepos + subdir layouts; matches how varied OSS users actually begin. Foundation for the §6 onboarding rewrite.

**Status: planned.**

