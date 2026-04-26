#!/usr/bin/env bash
# contribute-upstream.sh — extract scaffolding-only patches for upstream PR.
#
# Reviews downstream commits since the UPSTREAM anchor, identifies which touch
# scaffolding paths (i.e., contain content potentially worth contributing
# upstream), and produces path-scoped .patch files for the chosen ones. The
# operator then applies these to their upstream fork and opens a PR.
#
# Path scope determines what's contributable:
#   Scaffolding (contributable):  agents/, shared/, scripts/, docs/ (except
#                                 walkthroughs/), project/README.md, README.md,
#                                 LICENSE, NOTICE
#   Private (never contributed):  features/, events/, inbox/, overrides/,
#                                 project/* (except README.md), UPSTREAM,
#                                 anything else
#
# Each downstream commit is categorized:
#   scaffolding-only — touches only scaffolding paths; clean candidate.
#   mixed            — touches both scaffolding and private paths; can still
#                      be extracted via path-scoping (private files dropped
#                      from the patch automatically).
#   private-only     — touches no scaffolding paths; silently skipped.

set -euo pipefail

SCAFFOLD_PATHSPEC=(
  'agents/'
  'shared/'
  'scripts/'
  'docs/'
  ':!docs/walkthroughs/'
  'project/README.md'
  'README.md'
  'LICENSE'
  'NOTICE'
)

base_override=""
output_dir=""
list_only=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) base_override="$2"; shift 2 ;;
    --output) output_dir="$2"; shift 2 ;;
    --list) list_only=1; shift ;;
    -h|--help)
      cat >&2 <<EOF
Usage: $(basename "$0") [--since <sha>] [--output <dir>] [--list]

  --since <sha>   Override the base for the commit list (default: UPSTREAM commit:).
  --output <dir>  Where to put extracted .patch files
                  (default: ./upstream-contributions/<timestamp>/).
  --list          List candidate commits without prompting (read-only review).
EOF
      exit 2
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# --- Pre-flight ---

if [[ ! -d .git ]]; then
  echo "Error: not a git repository." >&2; exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty. Commit or stash before extracting." >&2
  git status --short >&2
  exit 1
fi
if ! git remote get-url upstream >/dev/null 2>&1; then
  echo "Error: 'upstream' remote not configured." >&2
  echo "Run scripts/add-upstream-remote.sh first." >&2
  exit 1
fi
if [[ ! -f UPSTREAM ]]; then
  echo "Error: UPSTREAM file not found." >&2; exit 1
fi

# --- Determine base ---

if [[ -n "$base_override" ]]; then
  base_sha="$base_override"
else
  base_sha=$(awk -F': *' '$1 == "commit" { print $2; exit }' UPSTREAM | sed 's/[[:space:]]*$//')
  if [[ -z "$base_sha" ]] || [[ "$base_sha" == \<* ]]; then
    echo "Error: UPSTREAM 'commit:' field missing or has placeholder." >&2
    exit 1
  fi
fi

if ! git rev-parse --verify "$base_sha^{commit}" >/dev/null 2>&1; then
  echo "Error: base commit $base_sha is not reachable in this repository." >&2
  exit 1
fi

# --- List downstream commits ---

# Portable read-into-array (bash 3.2 has no `mapfile`/`readarray`).
all_commits=()
while IFS= read -r line; do
  all_commits+=("$line")
done < <(git log --reverse --format='%H' "${base_sha}..HEAD" 2>/dev/null)

if [[ ${#all_commits[@]} -eq 0 ]]; then
  echo "No downstream commits since ${base_sha:0:12}. Nothing to contribute."
  exit 0
fi

echo "Reviewing ${#all_commits[@]} downstream commit(s) since ${base_sha:0:12}..."
echo

# --- Categorize ---

candidate_shas=()
candidate_kinds=()

for sha in "${all_commits[@]}"; do
  scaffold_count=$(git diff-tree --no-commit-id --name-only -r "$sha" -- "${SCAFFOLD_PATHSPEC[@]}" 2>/dev/null | grep -c . || true)
  all_count=$(git diff-tree --no-commit-id --name-only -r "$sha" 2>/dev/null | grep -c . || true)

  if [[ "$scaffold_count" -eq 0 ]]; then
    continue  # private-only; silently skip
  fi

  if [[ "$scaffold_count" -lt "$all_count" ]]; then
    candidate_kinds+=("mixed")
  else
    candidate_kinds+=("scaffolding-only")
  fi
  candidate_shas+=("$sha")
done

if [[ ${#candidate_shas[@]} -eq 0 ]]; then
  echo "No commits since ${base_sha:0:12} touched scaffolding paths."
  echo "Nothing to contribute upstream."
  exit 0
fi

echo "Found ${#candidate_shas[@]} commit(s) with scaffolding content:"
echo

for i in "${!candidate_shas[@]}"; do
  sha="${candidate_shas[$i]}"
  kind="${candidate_kinds[$i]}"
  short=$(git log --format='%h %ad %s' --date=short -1 "$sha")
  printf '  [%2d] %-18s %s\n' "$((i+1))" "[$kind]" "$short"
done

echo

if [[ $list_only -eq 1 ]]; then
  echo "Run without --list to interactively select and extract patches."
  exit 0
fi

# --- Prepare output dir ---

if [[ -z "$output_dir" ]]; then
  timestamp=$(date -u +%Y%m%d-%H%M%S)
  output_dir="upstream-contributions/$timestamp"
fi
mkdir -p "$output_dir"
echo "Output directory: $output_dir"
echo

# --- Interactive review ---

chosen_shas=()

for i in "${!candidate_shas[@]}"; do
  sha="${candidate_shas[$i]}"
  kind="${candidate_kinds[$i]}"
  short=$(git log --format='%h %ad %s' --date=short -1 "$sha")

  echo "─────────────────────────────────────────────────────────────"
  echo "[$((i+1))/${#candidate_shas[@]}] [$kind] $short"

  echo
  echo "Scaffolding files (will be included in extracted patch):"
  git diff-tree --no-commit-id --name-only -r "$sha" -- "${SCAFFOLD_PATHSPEC[@]}" 2>/dev/null | sed 's/^/  + /'

  if [[ "$kind" == "mixed" ]]; then
    echo
    echo "Private files (will be DROPPED from extracted patch):"
    comm -23 \
      <(git diff-tree --no-commit-id --name-only -r "$sha" 2>/dev/null | sort) \
      <(git diff-tree --no-commit-id --name-only -r "$sha" -- "${SCAFFOLD_PATHSPEC[@]}" 2>/dev/null | sort) \
      | sed 's/^/  - /'
  fi

  # Sanitization warnings: scan commit message for downstream-specific tokens.
  msg_warnings=()
  full_msg=$(git log -1 --format='%s%n%b' "$sha")
  if echo "$full_msg" | grep -qE 'FEAT-[0-9]{4}-[0-9]+'; then
    msg_warnings+=("references a FEAT-YYYY-NNNN correlation ID — likely downstream-specific")
  fi
  if echo "$full_msg" | grep -qiE '\b(WIDG|JIRA|CARD|TICKET)-[0-9]+'; then
    msg_warnings+=("references a ticket-ID pattern — likely downstream-specific")
  fi

  if [[ ${#msg_warnings[@]} -gt 0 ]]; then
    echo
    echo "  ⚠ Sanitization warnings on the commit message:"
    for w in "${msg_warnings[@]}"; do
      echo "      - $w"
    done
    echo "    Review and rewrite the message for upstream context after extraction."
  fi

  echo
  while true; do
    # Prompt and read both go through /dev/tty so the prompt text flushes
    # immediately even when stdout is line-buffered (e.g., Claude Code's `!`).
    printf "Extract this commit? [y]es / [n]o / [d]iff / [q]uit: " > /dev/tty
    read -r answer < /dev/tty
    case "$answer" in
      y|Y|yes)
        chosen_shas+=("$sha")
        echo "  marked for extraction."
        break ;;
      n|N|no)
        echo "  skipped."
        break ;;
      d|D|diff)
        git --no-pager show --stat "$sha" -- "${SCAFFOLD_PATHSPEC[@]}"
        ;;
      q|Q|quit)
        echo "Quitting."
        break 2 ;;
      *)
        echo "Unrecognized: '$answer'. Enter y, n, d, or q." ;;
    esac
  done
  echo
done

# --- Extract ---

if [[ ${#chosen_shas[@]} -eq 0 ]]; then
  echo "No commits chosen. Nothing extracted."
  rmdir "$output_dir" 2>/dev/null || true
  exit 0
fi

echo "═════════════════════════════════════════════════════════════"
echo "Extracting ${#chosen_shas[@]} patch(es) to $output_dir/..."
echo

n=1
for sha in "${chosen_shas[@]}"; do
  git format-patch --output-directory "$output_dir" --start-number "$n" \
    "${sha}^..${sha}" -- "${SCAFFOLD_PATHSPEC[@]}" >/dev/null
  n=$((n + 1))
done

echo "Extracted patches:"
ls -1 "$output_dir" | sed 's/^/  /'

abs_output_dir=$(cd "$output_dir" && pwd)

cat <<EOF

═════════════════════════════════════════════════════════════
Next steps:

  1. Review each .patch file in $output_dir.
     Confirm no private references (feature names, repo URLs, ticket IDs)
     remain in commit messages or diff content. The path scope drops private
     FILES, but commit messages still carry the downstream's framing.

  2. Fork the upstream Specfuse/orchestrator on GitHub (one-time setup):
       gh repo fork Specfuse/orchestrator --clone=false

  3. Clone your fork to a working directory OUTSIDE this downstream repo:
       cd <some-other-dir>
       gh repo clone <your-username>/orchestrator
       cd orchestrator

  4. Create a contribution branch and apply the patches:
       git checkout -b your-contribution-name
       git am $abs_output_dir/*.patch

  5. Sanitize commit messages — rewrite anything that references downstream
     context that doesn't translate upstream:
       git rebase -i <base>     # 'reword' the relevant commits

  6. Run the upstream validators on any schema/event-format changes:
       python3 scripts/validate-event.py ...
       python3 scripts/validate-frontmatter.py ...

  7. Push and open the PR:
       git push -u origin your-contribution-name
       gh pr create --repo Specfuse/orchestrator --title "..." --body "..."

The extracted patches in $output_dir can be deleted once the PR is open.
You may want to add 'upstream-contributions/' to .gitignore so the patch
directories don't show up as untracked.
EOF
