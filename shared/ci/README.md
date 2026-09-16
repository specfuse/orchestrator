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
   (`feat/INIT-2026-0001-F06-…` → `INIT-2026-0001/F06`). A branch with no initiative feature
   ID — including a loop-local `FEAT-YYYY-NNNN` branch — is skipped (the workflow no-ops).
2. Flips the feature issue in this repo to `state:done` and closes it (`reason: completed`).
3. Appends a validated `task_completed` event (`source: merge-watcher`) to the orchestration
   repo's `events/<INITIATIVE>.jsonl` and pushes it (retries with rebase on concurrent merges).

The orchestrator poller (`specfuse poller`) picks up from there: it sees the feature done
(via the `state:done` label / closed issue) and recomputes dependents `pending → ready`.

### Install (per component repo)
1. Copy `merge-watcher.yml` to `.github/workflows/merge-watcher.yml` in the component repo
   (`specfuse pm init --target component <repo>` does this).
2. Set the **`SPECFUSE_ORCH_REPO`** Actions variable (repo or org level) to the orchestration
   repo as `owner/name`, e.g. `gh variable set SPECFUSE_ORCH_REPO --body my-org/orchestration`.
   The workflow names no repo itself, so the file is identical in every consumer. If the
   variable is missing or malformed, the run fails with an error before the issue is closed.
3. Add two repo secrets for the **`specfuse-merge-watcher` GitHub App** (installed on the
   orchestration repo with `contents: write`):
   - **`SPECFUSE_APP_ID`** — the App's numeric ID.
   - **`SPECFUSE_APP_PRIVATE_KEY`** — the App's PEM private key.
   The workflow mints a short-lived, orchestrator-scoped installation token at runtime via
   `actions/create-github-app-token`. The built-in `GITHUB_TOKEN` already covers this repo's
   issues (the workflow requests `issues: write`). (Replaces the former long-lived `ORCH_TOKEN`
   PAT — tokens now auto-expire ~1h and carry an org audit trail.)
4. Ensure the feature issues in this repo follow the title convention `[INIT-YYYY-NNNN/FNN] …`
   and that feature branches are named `feat/INIT-YYYY-NNNN-FNN-<slug>` (the poller/loop do this).

### Upgrades and local edits
orchestrator-init records the sha256 of every file it writes in
`.specfuse/orchestrator-install.json` (commit it with the rest of `.specfuse/`). On upgrade, a
file whose content no longer matches its recorded hash is reported as `preserve: … (locally
modified)` and left alone — so a Dependabot action bump or a hand edit survives. Delete the
file and re-run to take the shipped version. Installs that predate the record are compared
against every merge-watcher version previously shipped: an unedited one is updated, anything
else is preserved.

### Assumptions / limitations (MVP)
- Correlation ID is read from the **branch name**. A non-conforming branch is skipped silently.
- One feature ⇒ one PR ⇒ one issue. Work-unit-level commits squashed onto the feature branch
  carry `Feature: …/FNN/TNN` trailers but the watcher operates at feature granularity.
- Concurrent merges racing on the same `events/<INITIATIVE>.jsonl` are handled by push-retry
  with `--rebase`; pathological contention is not (acceptable at current scale). If every
  retry is rejected the step fails rather than reporting success.
- The event is pushed straight to the orchestration repo's default branch. A ruleset that
  blocks the App's installation token will reject it; either add the App as a bypass actor
  or leave that branch unprotected for `events/`. (Open design question on #92.)
- Event validation requires the `specfuse` package (installed in the job). A validation
  failure aborts the append (the event is never written half-formed).
