#!/usr/bin/env bash
#
# Read the current version of an orchestrator agent role from
# agents/<role>/version.md. Used to fill the source_version field
# on events at emission time, per shared/rules/verify-before-report.md §3.
#
# Usage:
#   scripts/read-agent-version.sh <role>
#
# Example:
#   scripts/read-agent-version.sh component
#     -> prints "1.4.0" on stdout
#
# Exit codes:
#   0 — version read successfully; the version string is on stdout
#   1 — version.md exists but no "Current version: **X.Y.Z**" line (parse fail)
#   2 — setup error (missing arg, file not found, unknown role)

if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then
    echo "usage: $(basename "$0") <role>" >&2
    echo "       <role> is the agent role name (e.g. component, pm, qa, specs, config-steward, merge-watcher)." >&2
    exit 2
fi

role="$1"
script_dir="$(cd "$(dirname "$0")" && pwd)"
version_file="$script_dir/../agents/$role/version.md"

if [ ! -f "$version_file" ]; then
    echo "error: version file not found at $version_file" >&2
    echo "       (unknown role '$role'? expected a directory under agents/<role>/ with a version.md)" >&2
    exit 2
fi

version="$(sed -nE 's/^Current version: \*\*([^*]+)\*\*$/\1/p' "$version_file" | head -n 1)"

if [ -z "$version" ]; then
    echo "error: no 'Current version: **X.Y.Z**' line found in $version_file" >&2
    exit 1
fi

printf '%s\n' "$version"
