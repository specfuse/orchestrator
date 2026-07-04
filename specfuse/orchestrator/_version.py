"""Agent version marker reader.

Reads the "Current version: **X.Y.Z**" marker line from
<repo>/agents/<role>/version.md, used to fill the `source_version` field on
events at emission time.
"""

from __future__ import annotations

import re
from pathlib import Path

_VERSION_LINE_RE = re.compile(r"^Current version: \*\*([^*]+)\*\*$", re.MULTILINE)


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
