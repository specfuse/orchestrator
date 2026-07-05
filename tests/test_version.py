"""Deferred red test for `specfuse/orchestrator/_version.py` (T05), greened here."""

from __future__ import annotations

import pytest

from specfuse.orchestrator._version import main, read_agent_version, resolve_agent_version


def test_read_agent_version(tmp_path):
    (tmp_path / "agents" / "demo").mkdir(parents=True)
    (tmp_path / "agents" / "demo" / "version.md").write_text(
        "# Demo agent version\n\nCurrent version: **2.3.1**\n",
        encoding="utf-8",
    )
    assert read_agent_version(tmp_path, "demo") == "2.3.1"


def test_read_agent_version_missing_role(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_agent_version(tmp_path, "no-such-role")


def test_read_agent_version_missing_marker_line(tmp_path):
    (tmp_path / "agents" / "demo").mkdir(parents=True)
    (tmp_path / "agents" / "demo" / "version.md").write_text(
        "# Demo agent version\n\nno marker line here\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        read_agent_version(tmp_path, "demo")


def test_main_prints_version_with_explicit_repo(tmp_path, capsys):
    (tmp_path / "agents" / "demo").mkdir(parents=True)
    (tmp_path / "agents" / "demo" / "version.md").write_text(
        "# Demo agent version\n\nCurrent version: **2.3.1**\n",
        encoding="utf-8",
    )
    rc = main(["demo", "--repo", str(tmp_path)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "2.3.1"


# ── §5: default resolution is package-based, not the state repo ──────────────

@pytest.fixture
def packaged_map(tmp_path, monkeypatch):
    """Point paths.substrate('agent-versions.json') at a temp map (hermetic —
    no dependency on a built _substrate)."""
    import json
    m = tmp_path / "agent-versions.json"
    m.write_text(json.dumps({"pm": "1.6.4", "component": "1.5.3"}) + "\n")
    monkeypatch.setattr("specfuse.orchestrator.paths.substrate",
                        lambda *parts: m if parts == ("agent-versions.json",) else tmp_path)
    return m


def test_resolve_agent_version_from_packaged_map(packaged_map):
    assert resolve_agent_version("pm") == "1.6.4"
    assert resolve_agent_version("component") == "1.5.3"


def test_resolve_agent_version_unknown_role_raises(packaged_map):
    with pytest.raises(KeyError):
        resolve_agent_version("no-such-role")


def test_main_defaults_to_packaged_version(packaged_map, capsys):
    # no --repo → resolve from the installed package, not the state root
    rc = main(["pm"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "1.6.4"


def test_main_unknown_role_exits_2(packaged_map, capsys):
    rc = main(["no-such-role"])
    assert rc == 2
    assert "error:" in capsys.readouterr().err


def test_main_repo_override_reads_state_repo(tmp_path, capsys):
    (tmp_path / "agents" / "demo").mkdir(parents=True)
    (tmp_path / "agents" / "demo" / "version.md").write_text(
        "# Demo agent version\n\nCurrent version: **9.9.9**\n", encoding="utf-8",
    )
    rc = main(["demo", "--repo", str(tmp_path)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "9.9.9"
