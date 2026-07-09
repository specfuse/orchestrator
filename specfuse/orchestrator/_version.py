"""Agent version resolution for the `source_version` event field.

The version of the agent role that emitted an event is resolved from the
**installed package** — the versions baked into `_substrate/agent-versions.json`
at build time (adoption §5: a consumer holds only state, the tooling/versions
ship in the wheel). `read_agent_version()` remains for the state-repo case
(`--repo`), reading the "Current version: **X.Y.Z**" marker from
<repo>/agents/<role>/version.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_VERSION_LINE_RE = re.compile(r"^Current version: \*\*([^*]+)\*\*$", re.MULTILINE)


def resolve_agent_version(role: str) -> str:
    """Return `role`'s version from the packaged agent-versions map.

    Reads `_substrate/agent-versions.json` (baked from agents/<role>/version.md at
    build time). Raises KeyError for an unknown role. If the map is absent (an
    unbuilt source tree / editable install), falls back to reading
    agents/<role>/version.md directly from the package's own repo root; raises
    FileNotFoundError if neither is available.
    """
    from specfuse.orchestrator import paths

    map_path = paths.substrate("agent-versions.json")
    if not map_path.is_file():
        repo_root = Path(__file__).resolve().parents[2]
        return read_agent_version(repo_root, role)
    versions = json.loads(map_path.read_text(encoding="utf-8"))
    if role not in versions:
        raise KeyError(f"unknown agent role {role!r}; known: {sorted(versions)}")
    return versions[role]


def read_agent_version(repo: Path | str, role: str) -> str:
    """Return the current version string for `role` under `repo`/agents/.

    Raises FileNotFoundError if `<repo>/agents/<role>/version.md` is missing,
    and ValueError if the file has no `Current version: **X.Y.Z**` line.
    """
    version_file = Path(repo) / "agents" / role / "version.md"
    if not version_file.is_file():
        raise FileNotFoundError(
            f"version file not found at {version_file} "
            f"(unknown role '{role}'? expected a directory under agents/<role>/ with a version.md)"
        )

    text = version_file.read_text(encoding="utf-8")
    match = _VERSION_LINE_RE.search(text)
    if not match:
        raise ValueError(f"no 'Current version: **X.Y.Z**' line found in {version_file}")

    return match.group(1)


def main(argv=None) -> int:
    """CLI: print the current version marker for an agent role.

    Replaces the retired `scripts/read-agent-version.sh <role>`. The repo holding
    `agents/<role>/version.md` defaults to the resolved state root; override with
    `--repo`.
    """
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m specfuse.orchestrator._version",
        description="Print the current version marker for an agent role.",
    )
    ap.add_argument("role", help="agent role, e.g. pm / component / qa")
    ap.add_argument("--repo", default=None,
                    help="resolve from <repo>/agents/<role>/version.md instead of the "
                         "installed package (state-repo / dev override)")
    args = ap.parse_args(argv)
    import sys
    try:
        if args.repo is not None:
            print(read_agent_version(args.repo, args.role))
        else:
            print(resolve_agent_version(args.role))
    except (KeyError, FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
