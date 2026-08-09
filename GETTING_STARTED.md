# Getting started

Get from "I want to try the Specfuse orchestrator" to "ready to draft my first feature" in about 5 minutes.

## Prerequisites

- [Claude Code CLI](https://claude.com/claude-code) installed.
- Python 3.
- `uv tool install specfuse` (or `pipx install specfuse`) — the umbrella hard-depends on every component, so one install puts the whole suite on `$PATH` behind the single `specfuse` command. No extras, no flags, no bracket quoting. (`pip install specfuse-orchestrator` still works if you want this package as a library, but it is no longer the documented path for suite users.)
- (Recommended) The [Specfuse validator CLI](https://specfuse.dev) on `$PATH`, so spec validation in the pipeline isn't simulated.
- `git` and the [`gh` CLI](https://cli.github.com) are **optional** — needed only later, if and when you put the state under version control or wire the merge-watcher CI. You do not need them to start.

## The principle: you hold *state*, the wheel holds *tooling*

The tooling — drivers, CLI, agents, and the frozen substrate (schemas, rules, templates, agent versions) — ships **inside the installed wheel + the `specfuse-orchestrator@specfuse` plugin** and is resolved at runtime. Your **state** — `features/`, `events/`, `project/`, `inbox/`, `overrides/`, `roadmap.md` — is plain files you own, kept wherever you like. Upgrades touch only the tooling, never your state.

## The 5-minute path

1. **Install the tooling.**
   ```bash
   uv tool install specfuse    # or: pipx install specfuse
   ```
2. **Install the plugin** in Claude Code: `/plugin install specfuse-orchestrator@specfuse`.
3. **Pick where your state lives, then `init` it** — location-agnostic, no git or GitHub required:
   ```bash
   specfuse pm init <path>
   ```

   | Shape | `<path>` | Best for |
   |---|---|---|
   | **Dedicated repo** | a new folder | multi-repo products, teams wanting clean separation |
   | **Subdirectory** | `orchestration/` inside an existing repo | monorepos, "keep it near the code" |
   | **Local-first** | any plain folder | evaluation, offline, "just try it" — promote later |

   `init` scaffolds the state directories, wires `.claude/` (marketplace + plugin), and writes a personalized `project/NEXT_STEPS.md`. It does **not** run `git init` or create a GitHub repo; if `<path>` is already inside a git repo it leaves git alone.
4. **`/onboard`** in a Claude Code session at `<path>` — the agent captures your repo topology (mono / multi / single) and product layout.
5. ***Optional, when ready:*** put the state under version control, give it its own GitHub repo, or wire the `merge-watcher` CI. Each is a documented one-liner in `NEXT_STEPS.md`, not a precondition — for example a dedicated repo:
   ```bash
   cd <path> && git init && gh repo create <org>/<name> --private --source=. --push
   ```

**Everything you need next is in `project/NEXT_STEPS.md`** — read that, not generic docs.

## What you'll have

- Your orchestration **state** at `<path>` — a plain directory (put it under git/GitHub whenever you choose, or not).
- The execution-plane agents (**PM, component, QA, onboarding**) via the `specfuse-orchestrator@specfuse` plugin. (The **specs** agent is the product-definition plane — it ships in the separate `specfuse-authoring` plugin and hands a validated initiative to the orchestrator at `planning`.)
- The frozen substrate + agent versions resolved from the installed `specfuse-orchestrator` wheel — nothing vendored into your state.
- A personalized `project/NEXT_STEPS.md` with your exact next commands.

## What's next

Open a Claude Code session at your state directory (`<path>`) and invoke `/onboard`:

```bash
cd <path>
claude
```

Then in the Claude Code session:

```
/plugin install specfuse-orchestrator@specfuse
/onboard
```

`/plugin install specfuse-orchestrator@specfuse` (already in the `specfuse/specfuse` marketplace) gives you the four execution-plane agents (PM, component, QA, onboarding) plus the `/onboard` skill. The onboarding agent then picks the right skill based on your project type:

- **Greenfield** → `bootstrap-greenfield` skill produces `project/bootstrap-checklist.md` with environment prereqs, repo-creation order, per-repo conventions, and first-feature scoping.
- **Brownfield** → `repo-inventory` skill walks each of your existing repos and produces per-repo readiness assessments. After that, run `/onboard` again — the agent then routes you to `integration-plan` to draft a phased rollout.

From there, work through the artifact `/onboard` produced. When you're ready for your first feature, [`docs/operator-runbook.md`](docs/operator-runbook.md) is the day-1 quickstart and [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) is the full lifecycle reference.

## Keeping up to date

When a new `specfuse-orchestrator` release ships, upgrade in place:

```bash
specfuse upgrade                # re-resolves and pulls every component
specfuse pm upgrade <path>
```

(`specfuse upgrade` is `uv tool upgrade specfuse` / `pipx upgrade specfuse` under the hood — because the umbrella hard-depends on each component, a new orchestrator release lands without waiting on an umbrella version bump.)

`upgrade` re-syncs the substrate from the newly-installed wheel and refreshes the `.claude` wiring. Your state (`features/`, `events/`, `project/`, `inbox/`, `overrides/`) is untouched.

## Slash commands you'll use

In a Claude Code session at your state directory, the plugin provides one slash command:

| Command | What it does |
|---|---|
| `/onboard` | Switch into the onboarding-agent role; runs the appropriate skill based on `/project/` state. |

## If something goes wrong

- Re-run `specfuse pm init <dir>` on a fresh directory if the scaffold looks incomplete, or `specfuse pm upgrade <dir>` to refresh an existing repo's substrate and `.claude` wiring.
- Make sure `gh auth status` passes before the `gh repo create` step.
- [`README.md`](README.md) — full project overview.
- Open an issue on the [`specfuse-orchestrator`](https://github.com/specfuse/orchestrator) repo if the failure looks like a tooling bug.
