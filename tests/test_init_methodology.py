# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Track C2: orchestrator-init ships the core-methodology (`methodology` upgrader) entries."""
from __future__ import annotations

import pytest

yaml = pytest.importorskip("yaml")

from specfuse.orchestrator import init  # noqa: E402  (after importorskip)


def _manifest() -> dict:
    return yaml.safe_load(init.MANIFEST.read_text())


def test_methodology_is_shipped():
    assert "methodology" in init.SHIP_UPGRADERS


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


def test_every_methodology_install_slot_has_a_real_source():
    """The distributor must never hit a MISSING source: every scaffolded methodology
    entry resolves to a file the orchestrator actually vendors locally."""
    missing = []
    for e in _manifest()["entries"]:
        if e.get("upgrader") != "methodology":
            continue
        if not e.get("install"):
            continue  # install: [] entries are documented-only, not scaffolded
        src = init._resolve_source(e["canonical_source"])
        if not src.exists():
            missing.append((e["id"], str(src)))
    assert not missing, f"methodology entries with no local source: {missing}"


def test_install_entry_copies_a_methodology_rule(tmp_path):
    target = tmp_path / "component"
    entry = {
        "id": "rule-correlation-ids",
        "upgrader": "methodology",
        "category": "shared-core",
        "canonical_source": {"repo": "specfuse", "path": "methodology/rules/correlation-ids.md"},
    }
    install = {"target": "component", "path": ".specfuse/rules/correlation-ids.md",
               "_target_repo": str(target)}
    init.install_entry(entry, install, dry=False)
    dst = target / ".specfuse" / "rules" / "correlation-ids.md"
    assert dst.is_file()
    # shipped content equals the orchestrator's vendored core copy
    from specfuse.orchestrator import paths
    assert dst.read_text() == paths.substrate("rules", "correlation-ids.md").read_text()


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


def test_install_entry_ships_methodology_doc(tmp_path):
    target = tmp_path / "component"
    entry = {
        "id": "methodology-gate-cycle",
        "upgrader": "methodology",
        "category": "shared-core",
        "canonical_source": {"repo": "specfuse", "path": "methodology/methodology.md"},
    }
    install = {"target": "component", "path": ".specfuse/docs/methodology.md",
               "_target_repo": str(target)}
    init.install_entry(entry, install, dry=False)
    assert (target / ".specfuse" / "docs" / "methodology.md").is_file()
