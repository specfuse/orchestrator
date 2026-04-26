#!/usr/bin/env bash
# sync-upstream.sh — interactive helper for periodic upstream sync.
#
# Lists upstream commits since the downstream's UPSTREAM anchor, scoped to
# scaffolding paths only (excludes upstream's own walkthroughs and private
# downstream dirs), and walks the operator through cherry-picking the ones
# they want to take.
#
# Run from the root of a downstream orchestration repo.
#
# Pre-conditions:
#   - working tree is clean (no uncommitted changes)
#   - 'upstream' remote is configured (run scripts/add-upstream-remote.sh)
#   - top-level UPSTREAM file exists with a valid 'commit:' field
#
# On cherry-pick conflict, the script halts with instructions; the operator
# resolves manually and re-runs the script to continue.

set -euo pipefail

# Path scope: scaffolding only. Upstream-private (docs/walkthroughs/) and
# downstream-private (features/, events/, inbox/, overrides/) are excluded.
PATHSPEC=(
  'agents/'
  'shared/'
  'scripts/'
  'docs/'
  'project/'
  'README.md'
  ':!docs/walkthroughs/'
)

target_ref="upstream/main"
list_only=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list) list_only=1; shift ;;
    --target) target_ref="$2"; shift 2 ;;
    -h|--help)
      cat >&2 <<EOF
Usage: $(basename "$0") [--list] [--target <ref>]

  --list           List upstream commits without prompting (read-only review).
  --target <ref>   Compare against this upstream ref (default: upstream/main).
EOF
      exit 2
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# --- Pre-flight checks ---

if [[ ! -d .git ]]; then
  echo "Error: not a git repository." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty. Commit or stash before syncing." >&2
  git status --short >&2
  exit 1
fi

if ! git remote get-url upstream >/dev/null 2>&1; then
  echo "Error: 'upstream' remote not configured." >&2
  echo "Run scripts/add-upstream-remote.sh first." >&2
  exit 1
fi

if [[ ! -f UPSTREAM ]]; then
  echo "Error: UPSTREAM file not found at $(pwd)/UPSTREAM." >&2
  exit 1
fi

base_sha=$(awk -F': *' '$1 == "commit" { print $2; exit }' UPSTREAM | sed 's/[[:space:]]*$//')
if [[ -z "$base_sha" ]] || [[ "$base_sha" == \<* ]]; then
  echo "Error: UPSTREAM 'commit:' field missing or contains a placeholder." >&2
  echo "Fill it in before running this script." >&2
  exit 1
fi

# --- Fetch and resolve target ---

echo "Fetching upstream..."
git fetch upstream --quiet

if ! target_sha=$(git rev-parse --verify "$target_ref^{commit}" 2>/dev/null); then
  echo "Error: cannot resolve target ref '$target_ref'." >&2
  exit 1
fi

if [[ "$base_sha" == "$target_sha" ]]; then
  echo "UPSTREAM anchor matches $target_ref ($target_sha). Already in sync."
  exit 0
fi

# --- List commits in scope ---

mapfile -t commits < <(
  git log --reverse --format='%H' "${base_sha}..${target_ref}" -- "${PATHSPEC[@]}" 2>/dev/null
)

if [[ ${#commits[@]} -eq 0 ]]; then
  echo "No upstream commits in $base_sha..$target_ref touch scaffolding paths."
  echo "(Upstream may have advanced with walkthrough/private content only.)"
  echo
  echo "Suggest bumping UPSTREAM 'commit:' to ${target_sha:0:12} and 'last_synced:' to $(date -u +%Y-%m-%d)."
  exit 0
fi

echo
echo "Upstream commits since ${base_sha:0:12} (target: $target_ref @ ${target_sha:0:12}):"
echo "Scope: scaffolding paths only (agents/, shared/, scripts/, docs/, project/, README.md)."
echo "Total: ${#commits[@]} commit(s) to consider."
echo

# --- List-only mode: print and exit ---

if [[ $list_only -eq 1 ]]; then
  for sha in "${commits[@]}"; do
    short=$(git log --format='%h %ad %s' --date=short -1 "$sha")
    echo "  $short"
  done
  echo
  echo "Run without --list to interactively cherry-pick."
  exit 0
fi

# --- Interactive review-and-pick ---

picked=()
declined=()

idx=0
total=${#commits[@]}
for sha in "${commits[@]}"; do
  idx=$((idx + 1))

  short=$(git log --format='%h %ad %s' --date=short -1 "$sha")
  files=$(git diff-tree --no-commit-id --name-only -r "$sha" -- "${PATHSPEC[@]}" 2>/dev/null | head -20)
  files_total=$(git diff-tree --no-commit-id --name-only -r "$sha" -- "${PATHSPEC[@]}" 2>/dev/null | wc -l | tr -d ' ')

  echo "─────────────────────────────────────────────────────────────"
  echo "[$idx/$total] $short"
  echo
  echo "Files touched ($files_total):"
  echo "$files" | sed 's/^/  /'
  if [[ "$files_total" -gt 20 ]]; then
    echo "  … and $((files_total - 20)) more"
  fi
  echo

  while true; do
    # Prompt and read both go through /dev/tty so the prompt text flushes
    # immediately even when stdout is line-buffered (e.g., Claude Code's `!`).
    printf "Take this commit? [y]es / [n]o / [d]iff / [q]uit: " > /dev/tty
    read -r answer < /dev/tty
    case "$answer" in
      y|Y|yes)
        echo "Cherry-picking $short..."
        if git cherry-pick --keep-redundant-commits "$sha"; then
          picked+=("$sha")
          echo "  applied."
        else
          echo
          echo "Cherry-pick conflict. The script is halting." >&2
          echo "Resolve the conflict, then run one of:" >&2
          echo "  git cherry-pick --continue   (commit the resolution)" >&2
          echo "  git cherry-pick --abort      (back out this pick)" >&2
          echo "Then re-run sync-upstream.sh to continue." >&2
          exit 1
        fi
        break
        ;;
      n|N|no)
        declined+=("$sha")
        echo "  skipped."
        break
        ;;
      d|D|diff)
        git --no-pager show --stat "$sha" -- "${PATHSPEC[@]}"
        # Re-prompt
        ;;
      q|Q|quit)
        echo "Quitting. Cherry-picks already applied are kept."
        break 2
        ;;
      *)
        echo "Unrecognized: '$answer'. Enter y, n, d, or q."
        ;;
    esac
  done
  echo
done

# --- Report ---

echo "═════════════════════════════════════════════════════════════"
echo "Sync session complete."
echo "  Picked:   ${#picked[@]}"
echo "  Declined: ${#declined[@]}"
echo "  Total considered: ${#commits[@]} of ${total}"
echo

# --- Offer to update UPSTREAM ---

if [[ ${#picked[@]} -gt 0 ]] || [[ ${#declined[@]} -gt 0 ]]; then
  echo "If you reviewed all commits in this session, you can advance the UPSTREAM"
  echo "anchor to ${target_sha:0:12} so future syncs don't re-list these."
  echo
  printf "Update UPSTREAM to %s? [y/N]: " "${target_sha:0:12}" > /dev/tty
  read -r answer < /dev/tty
  if [[ "$answer" =~ ^[Yy] ]]; then
    today=$(date -u +%Y-%m-%d)
    # Update commit: and last_synced: lines in place.
    tmpfile=$(mktemp)
    awk -v new_sha="$target_sha" -v new_date="$today" '
      /^commit:/        { print "commit: " new_sha; next }
      /^last_synced:/   { print "last_synced: " new_date; next }
      { print }
    ' UPSTREAM > "$tmpfile"
    mv "$tmpfile" UPSTREAM
    echo "UPSTREAM updated. Don't forget to commit it:"
    echo "  git add UPSTREAM && git commit -m 'chore: sync upstream to ${target_sha:0:12}'"
  else
    echo "UPSTREAM unchanged. Manual edit later if you want to advance it."
  fi
fi

# --- Follow-up reminders ---

if [[ ${#picked[@]} -gt 0 ]]; then
  echo
  echo "Follow-up:"
  echo "  1. Validate event log + frontmatter against the synced schemas:"
  echo "       python3 scripts/validate-event.py --file events/<your-feature>.jsonl"
  echo "       python3 scripts/validate-frontmatter.py --file features/<your-feature>.md"
  echo "  2. Review per-agent versions for any picked commits that bumped them;"
  echo "     your downstream's behavior may have changed."
  echo "  3. If the picks include skill or rule changes, re-read affected"
  echo "     SKILL.md / rule files in the next agent session."
fi
