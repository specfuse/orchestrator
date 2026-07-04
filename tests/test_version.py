"""Deferred red test for `specfuse/orchestrator/_version.py` (T05), greened here."""

from __future__ import annotations

import pytest

from specfuse.orchestrator._version import read_agent_version


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
