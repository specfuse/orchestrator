"""Marketplace publish delta: staged `marketplace.json` entry for gate-1's plugin.

The operator applies this entry to the `specfuse/specfuse` marketplace repo
(T05 runbook); this test only asserts the staged artifact is internally
consistent with the plugin manifest already committed in this repo.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRY_PATH = REPO_ROOT / "docs" / "publish" / "marketplace-orchestrator-entry.json"
PLUGIN_MANIFEST_PATH = (
    REPO_ROOT / "plugins" / "specfuse-orchestrator" / ".claude-plugin" / "plugin.json"
)


def test_marketplace_entry_matches_plugin():
    entry = json.loads(ENTRY_PATH.read_text(encoding="utf-8"))
    plugin = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert set(entry.keys()) == {"name", "source"}
    assert entry["name"] == plugin["name"] == "specfuse-orchestrator"
    assert entry["source"] == "./plugins/specfuse-orchestrator"
    assert PLUGIN_MANIFEST_PATH.is_file()
