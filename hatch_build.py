"""Hatch build hook: copy shared/** into specfuse/orchestrator/_substrate/.

`shared/` is the single source of truth for rules, schemas, and templates;
this hook mirrors it into the package at build time so the wheel ships a
self-contained substrate without a committed duplicate.
"""

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class SubstrateBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        src = root / "shared"
        dest = root / "specfuse" / "orchestrator" / "_substrate"

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

        # `_substrate/` is gitignored (build artifact), so hatchling's default
        # VCS-aware file selection would otherwise drop it from the wheel.
        build_data.setdefault("artifacts", []).append(
            "specfuse/orchestrator/_substrate/**/*"
        )
