#!/usr/bin/env bash
# setup.sh — interactive one-shot setup for a downstream
# orchestration repo. Bundles strip + git re-init + private GitHub repo
# creation + upstream remote configuration into a single guided flow.
#
# Run this from inside a fresh clone of the upstream Specfuse-orchestrator
# scaffolding. Asks for your downstream org + repo name + project type, then
# does the full setup and writes a personalized project/NEXT_STEPS.md.
#
# Pre-conditions:
#   - working directory is a fresh clone of the upstream scaffolding
#   - gh CLI authenticated (gh auth status)
#   - working tree clean

set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

# --- Pre-flight checks ---

if [[ ! -d .git ]]; then
  echo "Error: not in a git repository (no .git directory)." >&2
  echo "Run this from inside a fresh clone of the upstream scaffolding." >&2
  exit 1
fi

# Sanity: are we in an orchestrator scaffolding clone?
for marker in agents/onboarding/CLAUDE.md shared/rules/README.md scripts/template-clone-strip.sh; do
  if [[ ! -f "$marker" ]]; then
    echo "Error: missing $marker — not an orchestrator scaffolding clone." >&2
    exit 1
  fi
done

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty. Commit or stash before running setup." >&2
  git status --short >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: 'gh' CLI not found. Install it from https://cli.github.com." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: 'gh' CLI not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

# Detect if this clone has already been partially set up (idempotence guard).
already_stripped=0
if [[ ! -d docs/walkthroughs ]] && ! ls features/FEAT-*.md >/dev/null 2>&1; then
  already_stripped=1
fi

origin_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
upstream_origin=0
if echo "$origin_url" | grep -Eqi 'specfuse[/:]orchestrator(\.git)?(/|$)'; then
  upstream_origin=1
fi

# --- Interactive prompts ---

echo
echo "═════════════════════════════════════════════════════════════"
echo "Specfuse orchestrator — downstream setup"
echo "═════════════════════════════════════════════════════════════"
echo
echo "This script bundles the one-time setup steps into a single guided run:"
echo "  1. Strip walkthrough/feature/event content from this clone"
echo "  2. Capture the upstream anchor in UPSTREAM"
echo "  3. Re-initialize git history (rm -rf .git; git init)"
echo "  4. Create your private GitHub repo and push"
echo "  5. Configure the upstream remote as read-only"
echo "  6. Write a personalized project/NEXT_STEPS.md"
echo

if [[ $upstream_origin -eq 0 ]] && [[ -n "$origin_url" ]]; then
  echo "Warning: origin URL is '$origin_url', not the upstream Specfuse/orchestrator."
  echo "If this isn't a fresh clone, the setup may behave unexpectedly."
  echo
fi

if [[ $already_stripped -eq 1 ]]; then
  echo "Notice: this clone appears to already be stripped (no walkthroughs, no FEAT-* files)."
  echo "Setup will skip the strip step."
  echo
fi

# Reads a value interactively. Prompt text and read both go through /dev/tty
# rather than stdout/stdin — two reasons:
#   1. Callers use `var=$(prompt "...")` which captures stdout. If the prompt
#      text were written to stdout it would land in $var alongside the answer,
#      contaminating values used in case-pattern matches and shell expansions.
#   2. Under Claude Code's `!` prefix, stdout may be line-buffered so a
#      newline-less printf to stdout never flushes; /dev/tty writes flush
#      to the terminal immediately.
prompt() {
  local prompt_text="$1" default="${2:-}"
  local answer
  if [[ -n "$default" ]]; then
    printf "%s [%s]: " "$prompt_text" "$default" > /dev/tty
  else
    printf "%s: " "$prompt_text" > /dev/tty
  fi
  read -r answer < /dev/tty
  if [[ -z "$answer" && -n "$default" ]]; then
    answer="$default"
  fi
  echo "$answer"
}

org=$(prompt "Your GitHub org or username")
while [[ -z "$org" ]]; do
  echo "  org cannot be empty."
  org=$(prompt "Your GitHub org or username")
done

repo_name=$(prompt "Downstream repo name" "$(basename "$(pwd)")")
while [[ -z "$repo_name" ]]; do
  echo "  repo name cannot be empty."
  repo_name=$(prompt "Downstream repo name")
done

project_name=$(prompt "Project name (one-line, human-readable)" "$repo_name")

while true; do
  project_type=$(prompt "Project type — [g]reenfield (new) or [b]rownfield (existing)" "")
  case "$project_type" in
    g|G|greenfield) project_type="greenfield"; break ;;
    b|B|brownfield) project_type="brownfield"; break ;;
    *) echo "  please answer 'g' or 'b'." ;;
  esac
done

echo
echo "Summary:"
echo "  GitHub repo:   $org/$repo_name (private)"
echo "  Project name:  $project_name"
echo "  Project type:  $project_type"
echo

confirm=$(prompt "Proceed? [y/N]")
if [[ ! "$confirm" =~ ^[Yy] ]]; then
  echo "Aborted."
  exit 0
fi

# --- Execute ---

echo
echo "─── Step 1/6: Strip walkthrough/feature content ──────────────"
if [[ $already_stripped -eq 0 ]]; then
  ./scripts/template-clone-strip.sh .
else
  echo "  (already stripped — skipping)"
fi

# After strip, UPSTREAM file should exist with anchor captured.
if [[ ! -f UPSTREAM ]]; then
  echo "Error: UPSTREAM file was not created by the strip step." >&2
  exit 1
fi

echo
echo "─── Step 2/6: Re-initialize git history ──────────────────────"
rm -rf .git
git init -b main >/dev/null
git add -A
git commit -m "chore: initial template clone from Specfuse-orchestrator" >/dev/null
echo "  fresh git history initialized; first commit created."

echo
echo "─── Step 3/6: Create private GitHub repo and push ────────────"
gh repo create "$org/$repo_name" --private --source=. --push
echo "  pushed to $org/$repo_name."

echo
echo "─── Step 4/6: Configure upstream remote (read-only) ──────────"
./scripts/add-upstream-remote.sh

echo
echo "─── Step 5/6: Write project/NEXT_STEPS.md ────────────────────"

mkdir -p project
today=$(date -u +"%Y-%m-%d")

if [[ "$project_type" == "greenfield" ]]; then
  next_skill="bootstrap-greenfield"
  next_artifact="project/bootstrap-checklist.md"
  type_blurb="brand-new project — no existing code or repos yet"
else
  next_skill="repo-inventory"
  next_artifact="project/repos/<repo-slug>.md per repo, plus project/manifest.md"
  type_blurb="existing project with code, possibly in-flight features"
fi

cat > project/NEXT_STEPS.md <<EOF
# Next steps — $project_name

Generated by \`scripts/setup.sh\` on $today.

This downstream orchestration repo is set up. You are at \`$org/$repo_name\` (private),
template-cloned from the upstream Specfuse-orchestrator. Project type: **$project_type**
($type_blurb).

## What's already done

- ✅ Stripped upstream walkthrough/feature/event content
- ✅ Captured upstream anchor (see [\`UPSTREAM\`](../UPSTREAM))
- ✅ Initialized fresh git history; pushed initial commit to \`$org/$repo_name\`
- ✅ Configured the upstream Specfuse-orchestrator as a read-only remote

## What to do next

### Step 1 — Open a Claude Code session at this repo

\`\`\`
cd $(pwd)
claude
\`\`\`

### Step 2 — Run \`/onboard\`

In the Claude Code session, type:

\`\`\`
/onboard
\`\`\`

Claude switches into the **onboarding agent** role and runs the **\`$next_skill\`** skill,
which is the right one for a $project_type project.

The skill will:

EOF

if [[ "$project_type" == "greenfield" ]]; then
  cat >> project/NEXT_STEPS.md <<'EOF'
- Ask you about your project: vision (one paragraph), anticipated component repos, team size, autonomy preferences.
- Produce `project/bootstrap-checklist.md` with the full setup path: environment prereqs, repo creation order (product reference repo first, then component repos), per-repo conventions (`.specfuse/templates.yaml`, root `CLAUDE.md`, `_generated/` boundary, branch protection), and first-feature scoping.
- Produce a stub `project/manifest.md` with your project metadata.

After the skill completes, work through `project/bootstrap-checklist.md` step by step.
EOF
else
  cat >> project/NEXT_STEPS.md <<'EOF'
- Ask you about each involved repo: purpose, language/framework, build/test commands, current spec coverage, in-flight features.
- Walk each repo to read README, package files, CI config, and existing conventions.
- Produce `project/repos/<repo-slug>.md` per repo with a readiness checklist showing what's missing for orchestrator coordination (`.specfuse/templates.yaml`, root `CLAUDE.md`, `_generated/` boundary, etc.).
- Produce `project/manifest.md` with your project metadata and the inventoried repo list.

After `repo-inventory` completes, run `/onboard` again — the onboarding agent will detect that the inventory exists and route you to the **`integration-plan`** skill, which drafts `project/integration-plan.md` with a phased rollout (pilot → expand → import in-flight → steady state), a risk register, and success criteria.

After the integration plan exists, execute it phase by phase. The plan's per-repo onboarding actions become your work list.
EOF
fi

cat >> project/NEXT_STEPS.md <<'EOF'

### Step 3 — Run your first feature

When the onboarding agent's artifacts say you're ready (typically after the bootstrap checklist or pilot phase of the integration plan):

1. Open the feature idea in your project's product reference repo (under `/product/`). The orchestrator engages downstream of product discussion — brainstorming and feature ideation happen there, not here.
2. Open a Claude Code session at this orchestration repo with `agents/specs/CLAUDE.md` as the role prompt.
3. Walk through `docs/operator-runbook.md`'s session walkthrough: feature-intake → spec-drafting → spec-validation → handoff to PM agent.
4. Continue through the full pipeline per `docs/operator-pipeline-reference.md`.

## Day-to-day references

| What | Where |
|---|---|
| One-page quickstart (this file's source) | `GETTING_STARTED.md` |
| Drafting your first feature | `docs/operator-runbook.md` |
| Full pipeline (PM, component, QA, inbox, escalations) | `docs/operator-pipeline-reference.md` |
| Pulling upstream improvements | `docs/upstream-downstream-sync.md` or `/sync-upstream` |
| Contributing back to upstream | `CONTRIBUTING.md` or `/contribute-upstream` |
| Onboarding agent (project-level) | `agents/onboarding/README.md` or `/onboard` |
| Architecture authority | `docs/orchestrator-architecture.md` |

## Slash commands available in any Claude Code session at this repo

- `/onboard` — onboarding agent (you'll use this next)
- `/sync-upstream` — pull upstream improvements (after some weeks have passed)
- `/contribute-upstream` — contribute downstream improvements back to upstream

EOF

echo "  written: project/NEXT_STEPS.md"

echo
echo "─── Step 6/6: Commit personalized next-steps file ────────────"
git add project/NEXT_STEPS.md
git commit -m "chore: personalized next-steps for $project_name ($project_type)" >/dev/null
git push --quiet
echo "  pushed."

# --- Final message ---

cat <<EOF

═════════════════════════════════════════════════════════════
Setup complete.

  Repo:        $org/$repo_name (private)
  Type:        $project_type
  Next file:   project/NEXT_STEPS.md  ← read this next

═════════════════════════════════════════════════════════════
What's next:

  1. cd $(pwd)
  2. claude               # open a Claude Code session
  3. /onboard             # the onboarding agent will run $next_skill

The onboarding agent will produce $next_artifact with the
project-specific actions to bring you to your first feature.

For a refresher, project/NEXT_STEPS.md has everything in one place.
EOF
