# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""orchestrator-init leaves core-owned (`methodology` upgrader) entries to core and the loop (#91).

Core provisions them and the loop ships them into component repos; an orchestrator
re-ship would overwrite the loop's newer copies with the orchestrator's vendored ones."""
from __future__ import annotations

import pytest

yaml = pytest.importorskip("yaml")

from specfuse.orchestrator import init  # noqa: E402  (after importorskip)


def _manifest() -> dict:
    return yaml.safe_load(init.MANIFEST.read_text())


CORE_OWNED_COMPONENT_PATHS = [
    ".specfuse/docs/methodology.md",
    ".specfuse/rules/correlation-ids.md",
    ".specfuse/rules/never-touch.md",
    ".specfuse/rules/security-boundaries.md",
    ".specfuse/rules/verification-discipline.md",
]


def test_methodology_is_not_shipped():
    assert "methodology" not in init.SHIP_UPGRADERS


METHODOLOGY_SLOT = ".specfuse/methodology/"


def test_manifest_core_owned_component_slots_are_the_methodology_upgraders():
    """Outside core's own slot, the methodology entries' component slots are exactly the five
    paths the loop also writes."""
    slots = sorted(
        i["path"]
        for e in _manifest()["entries"]
        if e["upgrader"] == "methodology"
        for i in e.get("install", [])
        if i["target"] == "component" and not i["path"].startswith(METHODOLOGY_SLOT)
    )
    assert slots == CORE_OWNED_COMPONENT_PATHS


def test_manifest_declares_cores_provisioned_slot_on_both_targets():
    """`specfuse` provisions methodology/{rules,schemas} into .specfuse/methodology/ (#87)."""
    slots = {
        (i["target"], i["path"]): e
        for e in _manifest()["entries"]
        for i in e.get("install", [])
        if i["path"].startswith(METHODOLOGY_SLOT)
    }
    expected = {
        (t, f"{METHODOLOGY_SLOT}{sub}/")
        for t in ("component", "specs")
        for sub in ("rules", "schemas")
    }
    assert set(slots) == expected
    for (_, path), e in slots.items():
        assert e["upgrader"] == "methodology"
        assert e["authority"] == "core-canonical"
        sub = path[len(METHODOLOGY_SLOT):]
        assert e["canonical_source"] == {"repo": "specfuse", "path": f"methodology/{sub}"}


def test_upgrade_preserves_loop_copies_of_core_owned_files(tmp_path, monkeypatch):
    target = tmp_path / "component"
    for rel in CORE_OWNED_COMPONENT_PATHS:
        f = target / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"loop copy of {rel}\n")
    monkeypatch.setattr(init, "gitignore_guard", lambda _repo: None)

    init.install_into("component", target, _manifest(), upgrade=True, dry=False)

    for rel in CORE_OWNED_COMPONENT_PATHS:
        assert (target / rel).read_text() == f"loop copy of {rel}\n", rel


def test_fresh_install_writes_no_core_owned_files_and_imports_only_owned_rules(tmp_path, monkeypatch):
    target = tmp_path / "component"
    target.mkdir()
    monkeypatch.setattr(init, "gitignore_guard", lambda _repo: None)

    init.install_into("component", target, _manifest(), upgrade=False, dry=False)

    for rel in CORE_OWNED_COMPONENT_PATHS:
        assert not (target / rel).exists(), rel
    assert not (target / METHODOLOGY_SLOT).exists()
    imports = [
        line for line in (target / ".claude" / "CLAUDE.md").read_text().splitlines()
        if line.startswith("@.specfuse/rules/")
    ]
    assert imports, "orchestrator-owned rules should still be wired"
    for rel in CORE_OWNED_COMPONENT_PATHS:
        assert f"@{rel}" not in imports


def test_resolve_source_remaps_methodology_to_vendored_substrate():
    from specfuse.orchestrator import paths
    # rules → substrate/rules
    p = init._resolve_source({"repo": "specfuse", "path": "methodology/rules/correlation-ids.md"})
    assert p == paths.substrate("rules", "correlation-ids.md")
    # the gate-cycle doc → substrate/docs
    p = init._resolve_source({"repo": "specfuse", "path": "methodology/methodology.md"})
    assert p == paths.substrate("docs", "methodology.md")
    # schemas → substrate/schemas
    p = init._resolve_source({"repo": "specfuse", "path": "methodology/schemas/event.schema.json"})
    assert p == paths.substrate("schemas", "event.schema.json")
    # orchestrator-owned entries: leading shared/ stripped
    p = init._resolve_source({"repo": "orchestrator", "path": "shared/rules/override-registry.md"})
    assert p == paths.substrate("rules", "override-registry.md")




def test_discover_repos_reads_from_state_root(tmp_path):
    """--all discovery reads project/repos/*.md from the orchestration STATE repo,
    not from the installed package (the old SRC_ROOT bug)."""
    repos = tmp_path / "project" / "repos"
    repos.mkdir(parents=True)
    (repos / "api.md").write_text("# api\n\n**Repo:** `acme/api`\n")
    (repos / "web.md").write_text("# web\n\n**Repo:** `acme/web`\n")
    (repos / "notes.md").write_text("no repo marker here\n")  # ignored

    found = init.discover_repos(tmp_path)

    assert ("component", "acme/api") in found
    assert ("component", "acme/web") in found
    assert any(t == "specs" for t, _ in found)  # the product specs repo is appended
    # the marker-less file contributed nothing
    assert len([r for r in found if r[0] == "component"]) == 2


def test_no_agent_config_is_scaffolded():
    """Adoption §5: agent role prompts ship in the plugin, not scaffolded into any
    consumer. No manifest install slot targets .specfuse/agents/<role>/."""
    slots = [
        i["path"]
        for e in _manifest()["entries"]
        for i in e.get("install", [])
    ]
    assert not [p for p in slots if p.startswith(".specfuse/agents/")], (
        "an agent config is still scaffolded; the plugin should be the sole home"
    )
