# shared/ci — distributable CI for component repos

Canonical CI artifacts the orchestrator owns and distributes into **component repos**. They
are not run on the orchestration repo itself; they are templates installed elsewhere (by the
Track C `init` scaffolding, or by hand until that lands).

## merge-watcher.yml

The merge watcher: owns the `in_review → done` task/feature transition
(orchestrator-architecture.md §6.3, §10). It is **not** the merge gate — branch protection is.
It reacts only *after* a PR is merged, so by definition all required checks have already passed.

**What it does**, on a feature PR merge (Model B = one PR per feature):
1. Extracts the feature correlation ID from the PR head branch
   (`feat/INIT-2026-0001-F06-…` → `INIT-2026-0001/F06`; legacy `FEAT-YYYY-NNNN` also matched).
   A branch with no specfuse ID is skipped (the workflow no-ops).
2. Flips the feature issue in this repo to `state:done` and closes it (`reason: completed`).
3. Appends a validated `task_completed` event (`source: merge-watcher`) to the orchestration
   repo's `events/<INITIATIVE>.jsonl` and pushes it (retries with rebase on concurrent merges).

The orchestrator poller (`specfuse-poller`) picks up from there: it sees the feature done
(via the `state:done` label / closed issue) and recomputes dependents `pending → ready`.

### Install (per component repo)
1. Copy `merge-watcher.yml` to `.github/workflows/merge-watcher.yml` in the component repo.
2. Add two repo secrets for the **`specfuse-merge-watcher` GitHub App** (installed on
   `RestoManagerApp/orchestrator` with `contents: write`):
   - **`SPECFUSE_APP_ID`** — the App's numeric ID.
   - **`SPECFUSE_APP_PRIVATE_KEY`** — the App's PEM private key.
   The workflow mints a short-lived, orchestrator-scoped installation token at runtime via
   `actions/create-github-app-token`. The built-in `GITHUB_TOKEN` already covers this repo's
   issues (the workflow requests `issues: write`). (Replaces the former long-lived `ORCH_TOKEN`
   PAT — tokens now auto-expire ~1h and carry an org audit trail.)
3. Ensure the feature issues in this repo follow the title convention `[INIT-YYYY-NNNN/FNN] …`
   and that feature branches are named `feat/INIT-YYYY-NNNN-FNN-<slug>` (the poller/loop do this).

### Assumptions / limitations (MVP)
- Correlation ID is read from the **branch name**. A non-conforming branch is skipped silently.
- One feature ⇒ one PR ⇒ one issue. Work-unit-level commits squashed onto the feature branch
  carry `Feature: …/FNN/TNN` trailers but the watcher operates at feature granularity.
- Concurrent merges racing on the same `events/<INITIATIVE>.jsonl` are handled by push-retry
  with `--rebase`; pathological contention is not (acceptable at current scale).
- Event validation requires `scripts/requirements.txt` (installed in the job). A validation
  failure aborts the append (the event is never written half-formed).
