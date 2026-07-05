"""Structure gate for `plugins/specfuse-orchestrator/`.

No `plugin-lint` tool exists for Claude Code plugins, so this file is the local
oracle for the plugin's manifest and layout.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "specfuse-orchestrator"
MANIFEST_PATH = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
AGENTS_DIR = PLUGIN_ROOT / "agents"

REQUIRED_KEYS = {"name", "version", "description", "author", "license"}
# specs is authoring-plane — it ships in the specfuse-authoring plugin, not here.
EXPECTED_AGENT_NAMES = {"pm", "component", "qa", "onboarding"}
REQUIRED_AGENT_FRONTMATTER_KEYS = {"name", "description"}
REQUIRED_SKILL_FRONTMATTER_KEYS = {"name", "description"}


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_agent_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter block"
    _, frontmatter_raw, _ = text.split("---\n", 2)
    return yaml.safe_load(frontmatter_raw)


def test_plugin_manifest_valid():
    manifest = _load_manifest()
    missing = REQUIRED_KEYS - manifest.keys()
    assert not missing, f"plugin.json missing required keys: {missing}"
    assert manifest["name"] == "specfuse-orchestrator"


def test_agents_present():
    assert AGENTS_DIR.is_dir()
    agent_files = sorted(AGENTS_DIR.glob("*.md"))
    assert len(agent_files) == len(EXPECTED_AGENT_NAMES), f"expected {len(EXPECTED_AGENT_NAMES)} agent files, found {len(agent_files)}"
    assert {f.stem for f in agent_files} == EXPECTED_AGENT_NAMES

    for path in agent_files:
        assert path.stat().st_size > 0, f"{path} is empty"
        frontmatter = _load_agent_frontmatter(path)
        missing = REQUIRED_AGENT_FRONTMATTER_KEYS - frontmatter.keys()
        assert not missing, f"{path} frontmatter missing required keys: {missing}"
        assert frontmatter["name"] == path.stem


def test_onboard_skill_present():
    skill_dir = PLUGIN_ROOT / "skills" / "onboard"
    assert skill_dir.is_dir()
    skill_path = skill_dir / "SKILL.md"
    assert skill_path.is_file()
    assert skill_path.stat().st_size > 0, f"{skill_path} is empty"

    frontmatter = _load_agent_frontmatter(skill_path)
    missing = REQUIRED_SKILL_FRONTMATTER_KEYS - frontmatter.keys()
    assert not missing, f"{skill_path} frontmatter missing required keys: {missing}"
    assert frontmatter["name"] == "onboard"
