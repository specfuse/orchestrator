"""Hatch build hook: mirror shared/** + the agent version markers into the package.

`shared/` is the single source of truth for rules, schemas, and templates; this
hook mirrors it into `specfuse/orchestrator/_substrate/` so the wheel ships a
self-contained substrate without a committed duplicate. It also bakes the agent
version markers (agents/<role>/version.md) into `_substrate/agent-versions.json`
so drivers resolve `source_version` from the installed package — not from a
vendored `agents/` copy in the consumer's state repo (adoption §5).
"""

import json
import re
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_VERSION_LINE_RE = re.compile(r"^Current version: \*\*([^*]+)\*\*$", re.MULTILINE)


def _agent_versions(root: Path) -> dict[str, str]:
    """{role: version} parsed from every agents/<role>/version.md."""
    out: dict[str, str] = {}
    agents_dir = root / "agents"
    for vf in sorted(agents_dir.glob("*/version.md")):
        m = _VERSION_LINE_RE.search(vf.read_text(encoding="utf-8"))
        if m:
            out[vf.parent.name] = m.group(1)
    return out


class SubstrateBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        src = root / "shared"
        dest = root / "specfuse" / "orchestrator" / "_substrate"

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

        # Bake the agent version markers into the packaged substrate.
        (dest / "agent-versions.json").write_text(
            json.dumps(_agent_versions(root), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # `_substrate/` is gitignored (build artifact), so hatchling's default
        # VCS-aware file selection would otherwise drop it from the wheel.
        build_data.setdefault("artifacts", []).append(
            "specfuse/orchestrator/_substrate/**/*"
        )
