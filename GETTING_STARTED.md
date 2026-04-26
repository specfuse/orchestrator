# Getting started

Get from "I want to try the Specfuse orchestrator" to "ready to draft my first feature" in about 5 minutes, with a single command after the clone.

## Prerequisites

- `git` and the [`gh` CLI](https://cli.github.com), authenticated against your private GitHub org (`gh auth status` should pass).
- [Claude Code CLI](https://claude.com/claude-code) installed.
- Python 3 with `pip install -r scripts/requirements.txt` workable.
- (Recommended) The [Specfuse validator CLI](https://specfuse.dev) on `$PATH`, so spec validation in the pipeline isn't simulated.

## Three commands — same for greenfield and brownfield

```bash
git clone https://github.com/Specfuse/orchestrator.git my-product-orchestration
cd my-product-orchestration
./scripts/setup.sh
```

The setup script asks you four questions:

1. Your GitHub org or username.
2. The downstream repo name (default: the cloned directory's name).
3. A human-readable project name.
4. Project type: **g**reenfield (brand-new, no repos yet) or **b**rownfield (existing project with code).

Then it does, in one pass:

- Strips upstream walkthrough/feature/event content.
- Captures the upstream anchor in a top-level `UPSTREAM` file.
- Initializes a fresh git history with one initial commit.
- Creates your private GitHub repo via `gh repo create` and pushes.
- Configures the upstream Specfuse-orchestrator as a read-only remote (push URL set to `DISABLE`).
- Writes a personalized `project/NEXT_STEPS.md` tailored to your project type and pushes it.

After the script completes, **everything you need to do next is in `project/NEXT_STEPS.md`** — read that, not generic docs.

## What you'll have

- A private orchestration repo on GitHub for your project.
- The four operational agents (specs, PM, component, QA) at frozen v1, ready to run.
- The onboarding agent ready to populate `/project/`.
- The upstream Specfuse-orchestrator wired as a read-only remote so you can pull future improvements via `/sync-upstream`.
- A personalized `project/NEXT_STEPS.md` with your exact next commands.
- **A proprietary `LICENSE`** (upstream's Apache 2.0 is replaced; current year and your GitHub org auto-filled as copyright holder) and a `NOTICES.md` preserving Apache 2.0 attribution for upstream-derived files. `project/NEXT_STEPS.md` Step 0 walks you through reviewing/adjusting it, including the one-line revert if your downstream is itself open-source. See [`README.md`](README.md) §"Licensing — upstream vs. downstream" for the rationale.

## What's next

Open a Claude Code session at the orchestration repo and invoke `/onboard`:

```bash
cd my-product-orchestration
claude
```

Then in the Claude Code session:

```
/onboard
```

The onboarding agent picks the right skill based on your project type:

- **Greenfield** → `bootstrap-greenfield` skill produces `project/bootstrap-checklist.md` with environment prereqs, repo-creation order, per-repo conventions, and first-feature scoping.
- **Brownfield** → `repo-inventory` skill walks each of your existing repos and produces per-repo readiness assessments. After that, run `/onboard` again — the agent then routes you to `integration-plan` to draft a phased rollout.

From there, work through the artifact `/onboard` produced. When you're ready for your first feature, [`docs/operator-runbook.md`](docs/operator-runbook.md) is the day-1 quickstart and [`docs/operator-pipeline-reference.md`](docs/operator-pipeline-reference.md) is the full lifecycle reference.

## Slash commands you'll use

In any Claude Code session at the orchestration repo, three slash commands wrap the most common operations:

| Command | What it does |
|---|---|
| `/onboard` | Switch into the onboarding-agent role; runs the appropriate skill based on `/project/` state. |
| `/sync-upstream` | Pull upstream improvements (cherry-pick chosen commits since `UPSTREAM` anchor). |
| `/contribute-upstream` | Extract scaffolding-only patches for an upstream PR. |

## If something goes wrong

The setup script's pre-flight checks fail loudly if a prereq is missing (`gh` not authenticated, dirty working tree, not a fresh clone, etc.). Fix the named issue and re-run; it's idempotent where it can be — already-stripped clones skip the strip step.

For deeper troubleshooting:

- [`README.md`](README.md) — full project overview.
- [`docs/upstream-downstream-sync.md`](docs/upstream-downstream-sync.md) — manual fallback for any setup step.
- Open an issue on the upstream repo if the failure looks like a tooling bug.
