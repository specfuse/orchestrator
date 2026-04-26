#!/usr/bin/env bash
# Strip walkthrough/feature/event content from a fresh template clone of the
# Specfuse orchestrator scaffolding, preparing it for use as a downstream
# project's orchestration repo.
#
# See docs/upstream-downstream-sync.md for the full template-clone workflow.
#
# This script does NOT touch .git. The caller is responsible for re-initializing
# the git history (rm -rf .git && git init) before pushing the downstream repo.

set -euo pipefail

usage() {
  cat >&2 <<EOF
Usage: $(basename "$0") <target-dir> [--strip-impl-plan] [--dry-run]

  <target-dir>        Path to a fresh template clone of the orchestrator
                      scaffolding.

  --strip-impl-plan   Also remove docs/orchestrator-implementation-plan.md
                      (the orchestrator's own build plan — not relevant to a
                      downstream project's operation).

  --dry-run           Print what would be removed without making changes.

  -h, --help          Show this help.
EOF
  exit 2
}

target=""
strip_impl_plan=0
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strip-impl-plan) strip_impl_plan=1; shift ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
    *)
      if [[ -z "$target" ]]; then target="$1"; shift
      else echo "Unexpected argument: $1" >&2; usage
      fi
      ;;
  esac
done

[[ -z "$target" ]] && usage
[[ -d "$target" ]] || { echo "Not a directory: $target" >&2; exit 1; }

cd "$target"

# Sanity: confirm this looks like an orchestrator template clone.
for marker in agents/onboarding/CLAUDE.md shared/rules/README.md scripts/validate-event.py; do
  [[ -f "$marker" ]] || { echo "Missing $marker — does not look like an orchestrator template clone." >&2; exit 1; }
done

# Note: a fresh template clone and the upstream's own dev source-of-truth
# both have .git remote = Specfuse/orchestrator, so the script can't
# distinguish them. The marker-file check above confirms this is an
# orchestrator scaffolding tree; "don't run strip on your dev source-of-truth"
# is the operator's responsibility, not something the script can reliably
# enforce. If you accidentally run it in the wrong place, `git restore .`
# recovers everything.

run() {
  if [[ $dry_run -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

# Capture the upstream anchor (URL + commit SHA) BEFORE stripping, so we can
# durably record where this downstream was template-cloned from. The .git
# directory is what gives us this info; running this before the user does
# `rm -rf .git` is the only window we have to capture it automatically.
upstream_url=""
upstream_sha=""
if [[ -d .git ]]; then
  upstream_url=$(git config --get remote.origin.url 2>/dev/null || true)
  upstream_sha=$(git rev-parse HEAD 2>/dev/null || true)
fi
upstream_captured=1
if [[ -z "$upstream_url" || -z "$upstream_sha" ]]; then
  upstream_captured=0
fi
clone_date=$(date -u +"%Y-%m-%d")

strip_pattern() {
  local label="$1" base_dir="$2"
  shift 2
  local found=()
  if [[ -d "$base_dir" ]]; then
    while IFS= read -r -d '' f; do found+=("$f"); done < <(find "$base_dir" "$@" -print0 2>/dev/null)
  fi
  if [[ ${#found[@]} -gt 0 ]]; then
    echo "Stripping ${#found[@]} file(s): $label"
    for f in "${found[@]}"; do run rm -f "$f"; done
  else
    echo "Already clean: $label"
  fi
}

strip_dir() {
  local label="$1" path="$2"
  if [[ -d "$path" ]]; then
    echo "Removing directory: $label ($path)"
    run rm -rf "$path"
  else
    echo "Already absent: $label ($path)"
  fi
}

ensure_gitkeep() {
  local dir="$1"
  run mkdir -p "$dir"
  if [[ ! -f "$dir/.gitkeep" ]]; then
    echo "Seeding .gitkeep: $dir"
    run touch "$dir/.gitkeep"
  fi
}

# 1. Strip phase walkthrough features and events at the top level of features/ and events/.
strip_pattern "phase walkthrough features"  features -maxdepth 1 -type f -name 'FEAT-*.md'
strip_pattern "phase walkthrough events"    events   -maxdepth 1 -type f -name 'FEAT-*.jsonl'

# 2. Strip per-feature inbox artifacts. Conservative: only FEAT-*.md files at depth >= 2.
strip_pattern "phase walkthrough inbox files" inbox -mindepth 2 -type f -name 'FEAT-*.md'

# 3. Strip the entire docs/walkthroughs/ tree (Phase 1-4 logs + retrospectives).
strip_dir "phase walkthroughs (logs + retrospectives)" docs/walkthroughs

# 4. Optionally strip the orchestrator's own implementation plan.
if [[ $strip_impl_plan -eq 1 ]]; then
  if [[ -f docs/orchestrator-implementation-plan.md ]]; then
    echo "Removing: docs/orchestrator-implementation-plan.md"
    run rm -f docs/orchestrator-implementation-plan.md
  fi
fi

# 5. Seed .gitkeep in directories that must remain part of the scaffolding.
for d in features events overrides \
         inbox/human-escalation inbox/plan-approved inbox/qa-regression \
         inbox/spec-issue inbox/spec-issue/processed; do
  ensure_gitkeep "$d"
done

# 6. Write the UPSTREAM anchor file (only if it doesn't already exist — re-runs
#    of the strip don't clobber a downstream's existing anchor record).
if [[ -f UPSTREAM ]]; then
  echo "UPSTREAM file already present — not overwriting."
elif [[ $upstream_captured -eq 1 ]]; then
  echo "Writing UPSTREAM (anchor captured from .git: ${upstream_sha:0:12} on ${upstream_url})"
  if [[ $dry_run -eq 0 ]]; then
    cat > UPSTREAM <<EOF
# Upstream anchor
#
# Records which upstream Specfuse-orchestrator commit this downstream
# orchestration repo was template-cloned from. Used as the diff base for
# periodic upstream syncs (see docs/upstream-downstream-sync.md).
#
# Bump 'commit' and 'last_synced' after every upstream sync to reflect the
# new anchor.

upstream: ${upstream_url}
commit: ${upstream_sha}
cloned: ${clone_date}
last_synced: ${clone_date}
EOF
  fi
else
  echo "WARNING: cannot capture upstream anchor (no .git remote.origin or HEAD found)."
  echo "Writing UPSTREAM with placeholders — fill in manually before committing."
  if [[ $dry_run -eq 0 ]]; then
    cat > UPSTREAM <<EOF
# Upstream anchor — INCOMPLETE
#
# This file should record the upstream URL and commit SHA at template-clone
# time, but the strip script could not detect them automatically (typically
# because the script ran after 'rm -rf .git').
#
# Fill in the values below manually, then commit.

upstream: <fill in upstream URL, e.g. https://github.com/Specfuse/orchestrator.git>
commit: <fill in upstream commit SHA at clone time>
cloned: ${clone_date}
last_synced: ${clone_date}
EOF
  fi
fi

cat <<'EOF'

Strip complete. The upstream anchor has been captured in the top-level UPSTREAM
file (URL + commit SHA at clone time). It will be used by scripts/add-upstream-remote.sh
in step 5 below, and again whenever you sync from upstream.

Next steps:
  1. Edit README.md — replace the upstream framing with a description of YOUR
     product's orchestration repo.
  2. (Optional) Edit project/README.md for project-specific framing.
  3. Initialize a fresh git history (if not already done):
       rm -rf .git
       git init -b main
       git add -A
       git commit -m "chore: initial template clone from Specfuse-orchestrator"
  4. Push to your private repo:
       gh repo create <your-org>/<your-product>-orchestration --private --source=. --push
  5. Configure the upstream remote as read-only (uses the captured UPSTREAM file):
       ./scripts/add-upstream-remote.sh
  6. Open a Claude Code session at the new repo with agents/onboarding/CLAUDE.md
     as the role prompt and run repo-inventory + integration-plan (brownfield)
     or bootstrap-greenfield (greenfield).

See docs/upstream-downstream-sync.md for ongoing upstream sync and contribution.
EOF
