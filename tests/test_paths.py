"""Deferred red tests for `specfuse/orchestrator/paths.py` (T02), greened here.

`test_substrate_resolves_packaged_file` asserts against an installed wheel
(see WU-02-paths-seam.md Verification — `_substrate/` is a build artifact
absent from the working tree until built). `test_substrate_resolves_locally`
is an additional direct check against the `substrate_ready`-regenerated tree
in the source checkout; it exists to exercise `substrate()` in-process (the
subprocess-based wheel check runs in a separate interpreter that this
session's `coverage` cannot observe).
"""

from __future__ import annotations

import subprocess

import pytest

from specfuse.orchestrator import paths


def test_state_root_env(tmp_path, monkeypatch):
    (tmp_path / "project").mkdir()
    (tmp_path / "features").mkdir()
    monkeypatch.setenv("SPECFUSE_ORCH_STATE", str(tmp_path))
    assert paths.state_root().resolve() == tmp_path.resolve()


def test_state_root_explicit_arg(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECFUSE_ORCH_STATE", raising=False)
    assert paths.state_root(str(tmp_path)).resolve() == tmp_path.resolve()


def test_state_root_walk_up(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECFUSE_ORCH_STATE", raising=False)
    (tmp_path / "project").mkdir()
    (tmp_path / "features").mkdir()
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert paths.state_root().resolve() == tmp_path.resolve()


def test_state_root_unresolved_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECFUSE_ORCH_STATE", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError):
        paths.state_root()


def test_substrate_resolves_locally(substrate_ready):
    resolved = paths.substrate("schemas", "event.schema.json")
    assert resolved.is_file()


def test_substrate_resolves_packaged_file(installed_wheel):
    venv_python = installed_wheel / "bin" / "python"
    result = subprocess.run(
        [
            str(venv_python),
            "-c",
            "from specfuse.orchestrator.paths import substrate; "
            "import sys; "
            "sys.exit(0 if substrate('schemas', 'event.schema.json').is_file() else 1)",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
