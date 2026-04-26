# SKILL: repo-inventory — v0.1.0

Inventory the project's repositories: for each one involved in the product, produce a durable readiness assessment under `/project/repos/<repo-slug>.md`, and maintain a top-level summary at `/project/manifest.md`.

This is a v0.1 working draft intended to be exercised on a real project and hardened. The procedure below describes the happy path; expect refinements after first use.

## When to invoke

- **Greenfield**: as each new repo is created. Run incrementally, one repo at a time.
- **Brownfield**: at integration time, in a single multi-repo session. Walk every involved repo and produce one inventory file per repo plus the manifest.
- **Maintenance**: when a repo's purpose, build/test commands, or framework changes substantially; when a repo is added or removed from the project.

## Inputs the agent reads

- The human's stated list of involved repos (org/repo slugs).
- For each repo: clone URL or local clone path. The agent walks the repo's:
  - Root README and any `docs/` content
  - Package/dependency files (`package.json`, `pyproject.toml`, `*.csproj`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile`, etc.)
  - Build/test config (Makefile, build scripts, `.github/workflows/`, CI definitions)
  - Existing root `CLAUDE.md` if present
  - `.specfuse/templates.yaml` if present
  - Top-level directory structure (without diving deep — surface-level shape is enough)
- The orchestration repo's existing `/project/` content (for incremental updates).

## Procedure

### Step 1 — Establish project context

If `/project/manifest.md` does not exist, ask the human:

- Project name and one-line description.
- Primary human operator(s).
- Default autonomy for the project (`auto`, `review`, `manual`) — used as the suggested default for new features.
- Target feature cadence (e.g., "2–3 features per week" or "informal").
- Product reference repo location (the repo holding `/product/` and `/business/`).

Create or update `/project/manifest.md` with these. The repo list will be filled in as inventory entries are produced.

### Step 2 — For each involved repo

For each repo the human names (or one repo if running incrementally):

1. **Confirm access.** The human either provides a local clone path or grants the agent network access to the repo. If neither, escalate `onboarding_blocker_unclear_scope`.
2. **Walk the repo.** Read README, package/dependency files, build/test config, root `CLAUDE.md` (if any), `.specfuse/templates.yaml` (if any), and the top-level directory structure. Use `Glob` and `Read` rather than reading every file — surface-level shape is the goal.
3. **Conversation with the human.** Confirm or fill in:
   - Repo's purpose in the product (one paragraph, in the human's own words — what does this component do?).
   - Repo's stability state — is it actively developed, in maintenance, deprecated?
   - In-flight features being worked there now (free-text list, references to existing issues/PRs if any).
   - Repo ownership (single owner, team, shared).
4. **Produce the inventory file** at `/project/repos/<repo-slug>.md` using the template below.
5. **Re-read the file** after writing to confirm content; correct any drift.

### Step 3 — Update the manifest

After every inventory file is produced (or on incremental updates), append/update the manifest's repo list:

```markdown
## Involved repos

- [`<repo-slug>`](repos/<repo-slug>.md) — <one-line summary from the inventory's `## Purpose` section>
- ...
```

Confirm the manifest's repo list matches the set of files under `/project/repos/`.

### Step 4 — Verification

- Re-read the manifest and every inventory file produced this session.
- For each inventory file, confirm the orchestrator-readiness checklist has concrete answers (no "TBD" placeholders).
- Confirm the manifest's repo list and the actual `/project/repos/` directory contents agree.

### Step 5 — Optional event emission

If this is a major inventory pass (initial onboarding or substantial revision), append an `onboarding_artifact_produced` event to a project-level event log at `/events/PROJ-<slug>.jsonl` (synthetic correlation ID `PROJ-<slug>`). Envelope-only validation at v0.1; per-type schema is a future addition. Skip for incremental single-repo updates.

## Inventory file template

The agent produces one file per repo at `/project/repos/<repo-slug>.md`. Suggested structure:

```markdown
# <repo-slug>

**Repo:** `<org>/<repo>`
**Inventoried:** <YYYY-MM-DD>
**Inventory version:** v0.1

## Purpose

<one paragraph: what this repo does in the product, in the human's own words>

## Tech surface

- **Language(s):** <e.g., Go 1.21, TypeScript / React, .NET 8>
- **Framework:** <if applicable>
- **Build:** <command(s) — e.g., `pnpm build`, `dotnet build`>
- **Test:** <command(s) — e.g., `pnpm test`, `dotnet test`>
- **Lint/format:** <command(s)>
- **Package manager:** <pnpm / npm / pip / cargo / nuget / etc.>

## Current state

- **Stability:** <actively developed / maintenance / deprecated>
- **Owner(s):** <single owner / team / shared>
- **In-flight features:** <free-text — names, issue/PR references>
- **CI:** <where CI runs, key gates>

## Spec coverage

- **Specs in product reference repo:** <path(s) under `/product/` if any specs exist for this repo>
- **Acceptance criteria style:** <how ACs are written today — formal, informal, none>

## Orchestrator-readiness

- **`.specfuse/templates.yaml`:** <present / absent / N-A — if present, list provided_templates>
- **Root `CLAUDE.md`:** <present / absent — if present, summarize what it covers>
- **`_generated/` boundary:** <present / absent / N-A — does the repo distinguish hand-written from generated code?>
- **`/overrides/` registry:** <not yet seeded / seeded — overrides exist for these regenerated files: ...>
- **Branch protection:** <enabled / disabled — required gates>
- **`gh` CLI access:** <confirmed / unconfirmed>

## Onboarding actions

Concrete actions the human will take to bring this repo to orchestrator-readiness, derived from the gaps above. The integration-plan skill aggregates these across all repos.

- [ ] <action 1>
- [ ] <action 2>

## Notes / open questions

<anything the human flagged that doesn't fit the sections above>
```

## Worked example

Imagine a small project with three repos: `acme/web` (Next.js frontend), `acme/api` (Go REST API), `acme/specs` (the product reference repo). The agent:

1. Asks for project name → "Acme Widget Tracker", operator → "Christian", autonomy → `review`, cadence → "2–3 features per week", product reference repo → `acme/specs`.
2. Creates `/project/manifest.md` with these.
3. For `acme/web`: walks the repo, sees `package.json` (Next.js 14, pnpm), `.github/workflows/test.yml` (CI on PR), no `CLAUDE.md`, no `.specfuse/templates.yaml`. Asks the human for purpose ("user-facing dashboard"), in-flight features ("WIDG-42 — bulk export, in code review"). Produces `/project/repos/acme-web.md` with the readiness checklist showing missing `.specfuse/templates.yaml`, missing root `CLAUDE.md`, no overrides registry yet. Onboarding actions: add the templates.yaml stub, add a root CLAUDE.md with the pnpm/Next.js conventions, leave overrides registry for first regenerated work.
4. Repeats for `acme/api`.
5. Skips `acme/specs` from `/project/repos/` (it's the product reference repo, not a component repo) but notes it in the manifest's product-reference-repo field.
6. Updates the manifest's `## Involved repos` list with two entries.
7. Re-reads everything; reports done.

## Friction the v0.1 expects

- **Repo access.** If the agent can't read the repo (no clone, no network), it can only inventory by interview, which is brittle. Ask the human to provide local clones first.
- **Long-running conversations.** A 10-repo project's full inventory may take multiple sessions. The skill is incremental-friendly — re-running only inventories the requested repos.
- **Stale inventories.** Six months later, build commands change. The skill is happy to re-inventory a single repo on request; the manifest's `Inventoried:` date is the indicator.
- **The `repos/` slug convention.** Suggested: `<org>-<repo>` with hyphen replacement. The agent picks a slug and asks the human to confirm before creating files.

## Anti-patterns

- Producing an inventory without walking the repo (anti-pattern #4 in the role config).
- Capturing product-discussion artifacts in `/project/repos/` notes — those go upstream to the product reference repo (anti-pattern #1).
- Marking checklist items as "TBD" in the file's final state — every item must have a concrete answer or "unconfirmed at inventory time".

## Where this v0.1 is likely to evolve

- Per-type event schema for `onboarding_artifact_produced` (currently envelope-only).
- Programmatic readiness checks (does `.specfuse/templates.yaml` validate? does root `CLAUDE.md` reference the orchestrator?) — currently the agent reads-and-judges, future versions can run scripts.
- Multi-product projects (one orchestrator instance, multiple distinct products). v0.1 assumes one product per orchestration repo.
