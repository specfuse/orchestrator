# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""orchestrator-init records what it wrote and never overwrites a file the consumer edited (#92)."""
from __future__ import annotations

import hashlib
import json

import pytest

yaml = pytest.importorskip("yaml")

from specfuse.orchestrator import init, paths  # noqa: E402  (after importorskip)

WATCHER = ".github/workflows/merge-watcher.yml"
RULE = ".specfuse/rules/override-registry.md"


def _manifest() -> dict:
    return yaml.safe_load(init.MANIFEST.read_text())


def _install(target, capsys, *, upgrade=True, dry=False) -> str:
    init.install_into("component", target, _manifest(), upgrade=upgrade, dry=dry)
    return capsys.readouterr().out


def _record(target) -> dict:
    return json.loads((target / init.INSTALL_RECORD).read_text())


def _shipped(rel: str) -> str:
    src = {WATCHER: ("ci", "merge-watcher.yml"), RULE: ("rules", "override-registry.md")}[rel]
    return paths.substrate(*src).read_text()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture(autouse=True)
def _no_git_probe(monkeypatch):
    monkeypatch.setattr(init, "gitignore_guard", lambda _repo: None)


@pytest.fixture
def target(tmp_path):
    t = tmp_path / "component"
    t.mkdir()
    return t


def test_fresh_install_records_every_written_file(target, capsys):
    _install(target, capsys, upgrade=False)
    record = _record(target)
    assert record[WATCHER] == _sha((target / WATCHER).read_text())
    assert record[RULE] == _sha((target / RULE).read_text())


def test_upgrade_preserves_an_edited_workflow_and_says_so(target, capsys):
    _install(target, capsys, upgrade=False)
    edited = (target / WATCHER).read_text() + "# consumer edit\n"
    (target / WATCHER).write_text(edited)

    out = _install(target, capsys)

    assert (target / WATCHER).read_text() == edited
    assert f"preserve: {target / WATCHER}" in out
    assert "locally modified" in out


def test_upgrade_updates_a_recorded_file_the_consumer_did_not_touch(target, capsys):
    stale = "stale shipped content\n"
    (target / WATCHER).parent.mkdir(parents=True)
    (target / WATCHER).write_text(stale)
    (target / init.INSTALL_RECORD).parent.mkdir(parents=True)
    (target / init.INSTALL_RECORD).write_text(json.dumps({WATCHER: _sha(stale)}))

    out = _install(target, capsys)

    assert (target / WATCHER).read_text() == _shipped(WATCHER)
    assert f"update: {target / WATCHER}" in out
    assert _record(target)[WATCHER] == _sha((target / WATCHER).read_text())


def test_legacy_install_of_a_previously_shipped_workflow_is_updated(target, capsys, monkeypatch):
    legacy = "workflow as some earlier release shipped it\n"
    monkeypatch.setitem(init.LEGACY_SHIPPED_SHA256, WATCHER, frozenset({_sha(legacy)}))
    (target / WATCHER).parent.mkdir(parents=True)
    (target / WATCHER).write_text(legacy)

    _install(target, capsys)

    assert (target / WATCHER).read_text() == _shipped(WATCHER)


def test_legacy_install_of_an_edited_workflow_is_preserved(target, capsys):
    edited = "hand-edited workflow, no install record\n"
    (target / WATCHER).parent.mkdir(parents=True)
    (target / WATCHER).write_text(edited)

    out = _install(target, capsys)

    assert (target / WATCHER).read_text() == edited
    assert f"preserve: {target / WATCHER}" in out
    assert WATCHER not in _record(target)


def test_legacy_install_without_a_shipped_history_is_overwritten_as_before(target, capsys):
    (target / RULE).parent.mkdir(parents=True)
    (target / RULE).write_text("older rule, no install record\n")

    _install(target, capsys)

    assert (target / RULE).read_text() == _shipped(RULE)


def test_dry_run_reports_preserve_and_writes_nothing(target, capsys):
    edited = "hand-edited workflow, no install record\n"
    (target / WATCHER).parent.mkdir(parents=True)
    (target / WATCHER).write_text(edited)

    out = _install(target, capsys, dry=True)

    assert f"would preserve: {target / WATCHER}" in out
    assert not (target / init.INSTALL_RECORD).exists()

