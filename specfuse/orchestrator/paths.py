"""Path seam: consumer state root vs. packaged substrate.

`state_root()` resolves the consumer's state repo (features/ events/
overrides/ project/ roadmap.md). `substrate()` resolves read-only data
shipped inside the wheel (schemas/rules/templates/distribution). These are
independent roots — a driver must never derive one from the other.
"""

from __future__ import annotations

import importlib.resources
import os
from pathlib import Path

_MARKER_DIRS = ("project", "features")


def state_root(explicit: str | None = None) -> Path:
    """Resolve the consumer state repo root.

    Resolution order: `$SPECFUSE_ORCH_STATE` env var, then `explicit` if
    given, then walking up from `Path.cwd()` for a directory containing both
    `project/` and `features/`. Raises `RuntimeError` if none resolves.
    """
    env_value = os.environ.get("SPECFUSE_ORCH_STATE")
    if env_value:
        return Path(env_value)

    if explicit:
        return Path(explicit)

    for candidate in (Path.cwd(), *Path.cwd().parents):
        if all((candidate / marker).is_dir() for marker in _MARKER_DIRS):
            return candidate

    raise RuntimeError(
        "Could not resolve state_root(): no $SPECFUSE_ORCH_STATE env var set, "
        "no explicit state_root argument passed, and no ancestor of "
        f"{Path.cwd()} contains both 'project/' and 'features/' directories."
    )


def substrate(*parts: str) -> Path:
    """Resolve a path under the packaged substrate tree shipped in the wheel."""
    root = importlib.resources.files("specfuse.orchestrator") / "_substrate"
    for part in parts:
        root = root / part
    with importlib.resources.as_file(root) as resolved:
        return Path(resolved)
