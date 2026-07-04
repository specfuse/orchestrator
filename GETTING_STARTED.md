# Getting started

Get from "I want to try the Specfuse orchestrator" to "ready to draft my first feature" in about 5 minutes.

## Prerequisites

- `git` and the [`gh` CLI](https://cli.github.com), authenticated against your private GitHub org (`gh auth status` should pass).
- [Claude Code CLI](https://claude.com/claude-code) installed.
- Python 3 with `pip`.
- `pip install specfuse-orchestrator` (published on [PyPI](https://pypi.org/project/specfuse-orchestrator/)). To install the whole suite instead: `pipx install specfuse[orchestrator]`.
- (Recommended) The [Specfuse validator CLI](https://specfuse.dev) on `$PATH`, so spec validation in the pipeline isn't simulated.

## The 5-minute path — same for greenfield and brownfield

```bash
pip install specfuse-orchestrator
specfuse-orchestrator init my-product-orchestration
```

`specfuse-orchestrator init <dir>` git-inits a fresh state repo at `<dir>` and, in one pass:

- Scaffolds the user-owned state directories: `features/`, `events/`, `project/`, `inbox/`, `overrides/`, and a starter `roadmap.md`.
- Wires `.claude/` — the `specfuse/specfuse` marketplace, the `specfuse-orchestrator@specfuse` plugin, and a deny-specs-edit hook.
- Writes a personalized `project/NEXT_STEPS.md` with your exact next commands.

The frozen substrate (`shared/**` — schemas, rules, templates) ships **inside the installed wheel** and is resolved at runtime; it is not copied into your state repo, so upgrades are clean.

### Create and push the GitHub repo (manual operator step)

`init` does **not** create the GitHub repo. Do it yourself after `init`:

```bash
cd my-product-orchestration
gh repo create <your-org>/my-product-orchestration --private --source=. --push
```

After that, **everything you need to do next is in `project/NEXT_STEPS.md`** — read that, not generic docs.

## What you'll have

- A fresh, git-initialized orchestration repo for your project (its own new repo — you license it however you want).
- The five agents (specs, PM, component, QA, onboarding) available through the `specfuse-orchestrator@specfuse` plugin.
- The frozen substrate resolved from the installed `specfuse-orchestrator` wheel.
- A personalized `project/NEXT_STEPS.md` with your exact next commands.

## What's next

Open a Claude Code session at the orchestration repo, install the plugin, and invoke `/onboard`:

```bash
cd my-product-orchestration
claude
```

Then in the Claude Code session:

```
/plugin install specfuse-orchestrator@specfuse
/onboard
```

`/plugin install specfuse-orchestrator@specfuse` (already in the `specfuse/specfuse` marketplace) gives you the five agents plus the `/onboard` skill. The onboarding agent then picks the right skill based on your project type:

- **Greenfield** → `bootstrap-greenfield` skill produces `project/bootstrap-checklist.md` with environment prereqs, repo-creation order, per-repo conventions, and first-feature scoping.
- **Brownfield** → `repo-inventory` skill walks each of your existing repos and produces per-repo readiness assessments. After that, run `/onboard` again — the agent then routes you to `integration-plan` to draft a phased rollout.

From there, work through the artifact `/onboard` produced. When you're ready for your first feature, [`docs/operator-runbook.md`](docs/operator-runbook.md) is the day-1 quickstart and [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) is the full lifecycle reference.

## Keeping up to date

When a new `specfuse-orchestrator` release ships, upgrade in place:

```bash
pip install -U specfuse-orchestrator
specfuse-orchestrator upgrade my-product-orchestration
```

`upgrade` re-syncs the substrate from the newly-installed wheel and refreshes the `.claude` wiring. Your state (`features/`, `events/`, `project/`, `inbox/`, `overrides/`) is untouched.

## Slash commands you'll use

In a Claude Code session at the orchestration repo, the plugin provides one slash command:

| Command | What it does |
|---|---|
| `/onboard` | Switch into the onboarding-agent role; runs the appropriate skill based on `/project/` state. |

## If something goes wrong

- Re-run `specfuse-orchestrator init <dir>` on a fresh directory if the scaffold looks incomplete, or `specfuse-orchestrator upgrade <dir>` to refresh an existing repo's substrate and `.claude` wiring.
- Make sure `gh auth status` passes before the `gh repo create` step.
- [`README.md`](README.md) — full project overview.
- Open an issue on the [`specfuse-orchestrator`](https://github.com/specfuse/orchestrator) repo if the failure looks like a tooling bug.
</content>
</invoke>
