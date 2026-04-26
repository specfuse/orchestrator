#!/usr/bin/env bash
# Configure the upstream Specfuse-orchestrator remote on this downstream
# orchestration repo as read-only (push URL set to DISABLE so accidental
# pushes to upstream cannot happen from this clone).
#
# Reads the upstream URL from the top-level UPSTREAM file, which was captured
# automatically by scripts/template-clone-strip.sh at clone time.
#
# Run this once, after you have re-initialized git and pushed to your private
# downstream repo (i.e., after `gh repo create ... --source=. --push`).
#
# Idempotent: if an `upstream` remote is already configured, the script reports
# its current state and exits without changes.

set -euo pipefail

if [[ ! -f UPSTREAM ]]; then
  echo "Error: UPSTREAM file not found in $(pwd)." >&2
  echo "Run this script from the root of a downstream orchestration repo" >&2
  echo "that was set up via scripts/template-clone-strip.sh." >&2
  exit 1
fi

if [[ ! -d .git ]]; then
  echo "Error: not a git repository ($(pwd) has no .git directory)." >&2
  echo "Initialize git (git init -b main && git add -A && git commit) and push" >&2
  echo "your downstream repo before running this script." >&2
  exit 1
fi

# Extract the upstream URL. We can't use `awk -F': *'` here because the URL
# itself contains a colon (e.g., `https://...`), so a `:`-based field split
# would truncate the URL at the first colon and capture only "https".
upstream_url=$(grep -m1 '^upstream:' UPSTREAM | sed -E 's/^upstream:[[:space:]]*//; s/[[:space:]]+$//')

if [[ -z "$upstream_url" ]] || [[ "$upstream_url" == \<* ]]; then
  echo "Error: UPSTREAM file does not contain a valid upstream URL." >&2
  echo "Open UPSTREAM and fill in the 'upstream:' field before running this script." >&2
  exit 1
fi

# Idempotence: if upstream remote already exists, report state and exit.
if existing=$(git remote get-url upstream 2>/dev/null); then
  echo "Upstream remote already configured."
  echo "  fetch URL: $existing"
  echo "  push URL:  $(git remote get-url --push upstream 2>/dev/null || echo '(unset)')"
  echo
  echo "If the push URL is not 'DISABLE', re-run with --reset to reconfigure:"
  echo "  $0 --reset"
  if [[ "${1:-}" == "--reset" ]]; then
    echo
    echo "--reset requested; removing existing upstream remote first."
    git remote remove upstream
  else
    exit 0
  fi
fi

echo "Adding upstream remote: $upstream_url"
git remote add upstream "$upstream_url"

echo "Disabling push to upstream (read-only)"
git remote set-url --push upstream DISABLE

echo
echo "Upstream remote configured. Verify with:"
echo "  git remote -v"
echo
echo "Periodic sync workflow lives in docs/upstream-downstream-sync.md."
