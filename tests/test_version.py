"""Deferred red test for `specfuse/orchestrator/_version.py` (T05), greened here."""

from __future__ import annotations

import pytest

from specfuse.orchestrator._version import main, read_agent_version


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


def test_main_defaults_repo_to_state_root(tmp_path, monkeypatch, capsys):
    (tmp_path / "agents" / "demo").mkdir(parents=True)
    (tmp_path / "agents" / "demo" / "version.md").write_text(
        "# Demo agent version\n\nCurrent version: **9.9.9**\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "specfuse.orchestrator.paths.state_root", lambda: tmp_path
    )
    rc = main(["demo"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "9.9.9"
