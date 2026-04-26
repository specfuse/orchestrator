# Upstream / downstream sync

This document explains how to **template-clone** the upstream Specfuse orchestrator scaffolding into a private downstream repo for your own product, how to **pull upstream improvements** back into the downstream over time, and how to **contribute fixes** from your downstream back to the upstream.

The orchestrator is intentionally not consumed as a dependency, library, or container image — it is consumed as **scaffolding**: a directory tree of agent configurations, shared rules, schemas, templates, and scripts that you copy, adapt, and version-control alongside your project's coordination state. The trade-off is a manual sync overhead in exchange for total control over which changes apply when.

## Why a separate downstream repo

The orchestration repo is the **process-state store for one product**. It accumulates `/features/`, `/events/`, `/inbox/`, `/overrides/` data over time — private operational state that should not live in a public upstream repo. Conversely, the upstream evolves with new agent capabilities, fixes, and (eventually) Phase 5+ surfaces that you'll want to take selectively into your downstream.

A fork is the wrong shape: the fork's history would interleave private feature data with upstream commits, making cherry-picking either direction painful. A **template clone** (copy the scaffolding, init a fresh git history, push to a new private repo) cleanly separates the two histories. You take upstream changes by selective merge or cherry-pick on a remote you set up, and contribute back by preparing scaffolding-only patches against an upstream fork.

## Licensing — upstream vs. downstream

The upstream is **Apache 2.0**. Most downstreams hold proprietary content (project specs, integration plans, in-flight feature data) and want their LICENSE to reflect that, not the upstream's permissive terms. The strip script handles this conversion automatically:

- **Replaces the upstream `LICENSE`** (Apache 2.0) with a proprietary placeholder. `setup.sh` substitutes the current year and your GitHub org as the copyright holder; you review and adjust to match your legal entity name in `project/NEXT_STEPS.md` Step 0.
- **Writes a `NOTICES.md` at the downstream root** that attributes the upstream Apache 2.0 origin, lists which directories/files are upstream-derived, and reproduces the upstream's `LICENSE` and `NOTICE` text in full — satisfying Apache 2.0 §4.b.
- **Removes the upstream `NOTICE`** since its content has been folded into `NOTICES.md`.

License boundary in the resulting downstream:

- **Upstream-derived files** (`agents/`, `shared/`, `scripts/`, `docs/`, `project/README.md`, the top-level Markdown docs, `.github/`, `.claude/`) remain available under Apache 2.0. Modifications you make to them must carry a notice that they were changed (Apache 2.0 §4.b — a commit message or changelog entry suffices).
- **Original work added by you** (your `/features/`, `/events/`, `/inbox/` content, project-specific `/agents/<role>/rules/` additions, `/project/` content beyond `README.md`) is governed by the downstream's `LICENSE`.

If your downstream is itself open-source and you want to preserve the upstream's Apache 2.0 LICENSE, the revert is one line — documented in `project/NEXT_STEPS.md` Step 0.

This is a starting template, not legal advice. Consult your organization's legal counsel for the final licensing arrangement.

## Initial template clone

### Prerequisites

- The upstream repo cloned or accessible (HTTPS, SSH, or local path).
- `gh` CLI authenticated against your private org.

### Procedure

**1. Clone the upstream scaffolding.** Use `--depth 1` if you don't need history; full clone if you want the upstream commits available for later syncs.

```bash
git clone https://github.com/Specfuse/orchestrator.git my-product-orchestration
cd my-product-orchestration
```

**2. Run the strip script.** Removes phase-walkthrough features, events, inbox artifacts, and `docs/walkthroughs/` — content from the upstream's own development history that has no place in your downstream. **Also captures the upstream anchor automatically** (URL + commit SHA at clone time) into a top-level `UPSTREAM` file — this is the durable record of where your downstream diverged from upstream, used as the diff base for every future sync. **And replaces the upstream Apache 2.0 `LICENSE` with a proprietary placeholder, writing a `NOTICES.md` that preserves Apache 2.0 attribution in full** — see "Licensing" below for the rationale and the revert path for OSS downstreams. **Run this before `rm -rf .git`** so the script can read the upstream URL and HEAD from `.git/`.

```bash
./scripts/template-clone-strip.sh . --dry-run    # preview what will be removed
./scripts/template-clone-strip.sh .              # actually strip + capture UPSTREAM
```

Optional flags:

- `--strip-impl-plan` also removes `docs/orchestrator-implementation-plan.md` (the upstream's own build plan; not relevant to your downstream's day-to-day operation, but you may want to keep it as a reference).
- `--dry-run` prints actions without performing them.

**3. Adapt `README.md`.** The upstream README opens with framing for the Specfuse orchestrator project itself ("Specfuse Orchestrator is a filesystem-based coordination layer..."). Replace the opening paragraph and "Status" section with framing for your product's orchestration repo. The "Get started on a real project" section can stay largely as-is — it points at the onboarding agent regardless of which product runs in the repo.

**4. Re-initialize git and push.** Strip the upstream's git history; start your own. The `UPSTREAM` file from step 2 carries forward into the new history.

```bash
rm -rf .git
git init -b main
git add -A
git commit -m "chore: initial template clone from Specfuse-orchestrator"
gh repo create my-org/my-product-orchestration --private --source=. --push
```

**5. Configure the upstream remote as read-only.** Uses the URL captured in `UPSTREAM`; idempotent.

```bash
./scripts/add-upstream-remote.sh
```

This adds `upstream` as a fetch-only remote (push URL set to `DISABLE`) so accidental pushes to upstream cannot happen from this clone.

**6. Run the onboarding agent.** Open a Claude Code session at the new repo with `agents/onboarding/CLAUDE.md` as the role prompt and run the appropriate skills (`repo-inventory` + `integration-plan` for brownfield, or `bootstrap-greenfield` for greenfield). See [`README.md`](../README.md) §"Get started on a real project".

## Pulling upstream changes

The upstream evolves: bug fixes, Phase 5+ deliverables, new agent skills, refined shared rules. You pull these into your downstream **selectively** — taking the scaffolding changes (`/agents/`, `/shared/`, `/scripts/`, `/docs/`) without taking the upstream's volatile dirs (`/features/`, `/events/`, `/inbox/`, `/overrides/`, `/docs/walkthroughs/`).

### One-time setup (per downstream repo)

The upstream remote is configured by [`scripts/add-upstream-remote.sh`](../scripts/add-upstream-remote.sh) during the initial template clone (step 5 of "Initial template clone" above). If you skipped that step or are setting up a downstream repo that didn't use the strip script, run it now:

```bash
./scripts/add-upstream-remote.sh
```

The script reads the URL from the top-level `UPSTREAM` file, adds an `upstream` fetch remote, and disables the push URL so accidental pushes to upstream cannot happen from this clone. If `UPSTREAM` is missing or has placeholder values, fill it in first (the format is documented at the top of the file).

### Periodic sync (recommended cadence: monthly, or on upstream release)

The recommended path is the interactive sync script, which walks you through the upstream commits since your last anchor and cherry-picks the ones you want. From a Claude Code session, the same workflow is available as the `/sync-upstream` slash command — Claude introduces what's about to happen, asks you to run the script via `! ./scripts/sync-upstream.sh`, and helps with conflict resolution and post-sync follow-ups.

```bash
./scripts/sync-upstream.sh
```

It reads the base from `UPSTREAM`, fetches `upstream/main`, lists every commit that touches scaffolding paths (excluding `docs/walkthroughs/` and downstream-private dirs), and for each one shows the SHA, subject, and files touched, then prompts: take **[y]es**, **[n]o**, view **[d]iff**, or **[q]uit**. On a "yes," it cherry-picks; on conflict, it halts with clear instructions to resolve and re-run. At the end, it offers to advance the `UPSTREAM` anchor automatically.

```bash
./scripts/sync-upstream.sh --list           # read-only review (no prompts, no picks)
./scripts/sync-upstream.sh --target <ref>   # compare against a different upstream ref
```

If you prefer manual control, the script is just a wrapper around three git operations you can run directly:

- **Cherry-pick specific commits.** Best for targeted fixes.

  ```bash
  git fetch upstream
  git log --oneline HEAD..upstream/main -- agents/ shared/ scripts/ docs/ ':!docs/walkthroughs/'
  git cherry-pick <sha>
  ```

- **Path-scoped checkout.** Best for larger upstream refactors.

  ```bash
  git checkout upstream/main -- agents/ shared/ scripts/ docs/operator-runbook.md
  git diff --staged
  git commit -m "chore: sync upstream <commit-range>"
  ```

  This brings the *full upstream state* of those paths into your working tree, replacing your downstream's version. Review carefully — local customizations may be overwritten.

After any sync session (script-driven or manual), do these:

- **Run validators.** `scripts/validate-event.py` and `scripts/validate-frontmatter.py` round-trip your downstream's existing artifacts through the synced schemas. If a sync changed a schema, this catches whether your existing data still validates.
- **Review per-agent versions.** Each agent under `/agents/<role>/version.md` carries its own version. Synced commits typically already carry the bumps and changelog entries; verify they landed.
- **Bump UPSTREAM if you didn't let the script do it.** `commit:` to the SHA you synced to (or `upstream/main` HEAD if you reviewed everything), `last_synced:` to today.

### What not to take

The strip script's removal list is also the upstream-sync ignore list:

- `features/FEAT-*.md` — upstream's walkthrough features, not yours.
- `events/FEAT-*.jsonl` — upstream's walkthrough event logs.
- `inbox/*/FEAT-*.md` and `inbox/spec-issue/processed/*` — upstream's walkthrough escalations/regressions.
- `docs/walkthroughs/` — upstream's phase walkthrough logs and retrospectives.
- `docs/orchestrator-implementation-plan.md` — upstream's own build plan (debatable; some downstreams keep it as a reference).

A path-scoped checkout that explicitly lists `agents/`, `shared/`, `scripts/`, and selected `docs/` files (operator-runbook, operator-pipeline-reference, walkthrough-planning-conventions, vision, architecture, design-summary) avoids these naturally. Cherry-picks rarely touch these paths in upstream development, so conflicts there are uncommon.

### Conflict resolution

Conflicts between your downstream customizations and upstream changes are handled like any git conflict, with two principles:

1. **Per-agent versions are authoritative.** If your downstream is at `agents/specs/version.md` v1.0.1 and upstream is at v1.1.0, the upstream's prose is generally what you want — the version bump signals deliberate change. Resolve in upstream's favor unless your downstream had a specific local override.
2. **Shared rules are load-bearing.** Conflicts in `shared/rules/` deserve careful review. A rule that you customized locally may need to be re-customized after the sync, or your customization may have been absorbed upstream.

Keep an eye on your role-specific `rules/` directories (e.g., `/agents/specs/rules/`) — those are where your downstream-specific overrides live, and upstream typically does not touch them.

## Contributing back to upstream

If you find a bug, write a useful new skill, or improve a shared rule in your downstream, you may want to contribute it back. The path is more involved than upstream-pull because your downstream commits include private feature data that must not leak.

The recommended path is the interactive contribution helper, which reviews your downstream commits since the `UPSTREAM` anchor, identifies which touch scaffolding paths, and produces clean path-scoped patches. From a Claude Code session, the same workflow is available as the `/contribute-upstream` slash command.

```bash
./scripts/contribute-upstream.sh
```

For each downstream commit since `UPSTREAM`, the script:

- **Categorizes** as `scaffolding-only` (clean candidate), `mixed` (touches both scaffolding and private paths), or `private-only` (silently skipped).
- **Shows** which scaffolding files are in the commit and, for mixed commits, which private files will be **dropped** from the extracted patch.
- **Warns** when commit messages reference downstream-specific tokens (FEAT-YYYY-NNNN correlation IDs, ticket prefixes like `WIDG-NN` / `JIRA-NN`) that you'll need to rewrite.
- **Prompts** take / skip / diff / quit per commit.
- **Extracts** chosen commits as `git format-patch` files in `./upstream-contributions/<timestamp>/`, scoped to scaffolding paths only — private file diffs cannot leak even if a commit was mixed.

```bash
./scripts/contribute-upstream.sh --list           # read-only review (no extraction)
./scripts/contribute-upstream.sh --since <sha>    # override the base
./scripts/contribute-upstream.sh --output <dir>   # custom output location
```

After extraction, the script prints next steps. Briefly:

**1. Review each `.patch` file.** The path scope drops private *files*; commit messages still carry the downstream's framing. Verify no private references survive in the message bodies.

**2. Fork the upstream Specfuse/orchestrator on GitHub** (one-time):

```bash
gh repo fork Specfuse/orchestrator --clone=false
```

**3. Clone your fork to a working directory outside the downstream repo, then apply:**

```bash
cd <some-other-dir>
gh repo clone <your-username>/orchestrator
cd orchestrator
git checkout -b your-contribution-name
git am /path/to/upstream-contributions/<timestamp>/*.patch
```

**4. Sanitize commit messages.** Rewrite anything referencing downstream context that doesn't translate upstream:

```bash
git rebase -i <base>     # 'reword' the relevant commits
```

**5. Validate against upstream.** Run upstream's scripts on any schema or event-format changes.

**6. Push and open the PR:**

```bash
git push -u origin your-contribution-name
gh pr create --repo Specfuse/orchestrator --title "..." --body "..."
```

**7. After merge, sync upstream into your downstream** via `scripts/sync-upstream.sh`. Your contribution lands upstream; the next sync brings the merged version back, letting you drop any local-only commits the merged version supersedes.

### What not to contribute back

- **Anything project-specific.** Skills, rules, or templates that only make sense for your product are downstream-only. Upstream changes should be useful to any project running the orchestrator.
- **Anti-pattern fixes that contain private context.** A fix that hard-codes "the Acme Widget Tracker pagination convention" doesn't belong upstream. Generalize first or keep it local.
- **Commits with private references.** Feature names, repo URLs, customer names. The script's path scope drops private files automatically and warns on common ID patterns in commit messages, but **commit message sanitization is your responsibility** — review every patch before `git am` and reword as needed.

## Compatibility considerations

The orchestrator scaffolding doesn't have a top-level version (yet). Per-agent versions in `/agents/<role>/version.md` track behavioral changes within each role; cross-role compatibility is not currently formalized.

Practical implications:

- **A downstream synced months apart from upstream may drift in subtle ways.** Per-agent versions help you spot what changed; the per-event `source_version` field in the event log helps you reconstruct what produced any given event after a sync.
- **Schema changes are the highest-risk sync category.** A change to `shared/schemas/event.schema.json` or any per-type event schema can invalidate prior events. The upstream's discipline is additive (per-type schemas added; envelope-only kept compatible), but verify against your event log after every sync.
- **Phase 5 will likely formalize a scaffolding-version concept.** Until then, the `UPSTREAM` file recommendation above is the closest substitute — it tells you which commit you anchored on.

## Recommended cadence

- **Initial clone:** once per project.
- **Upstream sync:** monthly, or whenever upstream announces a Phase release / notable fix.
- **Contribution back:** event-driven — when you have something genuinely upstream-worthy. Don't accumulate; the longer you wait, the harder the patch extraction.

## Reference

- [`README.md`](../README.md) — project getting-started, links to onboarding agent.
- [`scripts/template-clone-strip.sh`](../scripts/template-clone-strip.sh) — the strip + UPSTREAM-capture script.
- [`scripts/add-upstream-remote.sh`](../scripts/add-upstream-remote.sh) — upstream remote configuration helper.
- [`agents/onboarding/README.md`](../agents/onboarding/README.md) — onboarding agent documentation.
- [`docs/orchestrator-architecture.md`](orchestrator-architecture.md) §4 — repository topology.
