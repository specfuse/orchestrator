"""Deferred red tests for the ownership fragment + `specfuse.ownership` entry
point (T07), greened here.

Entry-point discovery reads installed distribution metadata
(`importlib.metadata`), which only exists once the wheel is installed — these
two required nodeids run against the `installed_wheel` fixture's temp venv via
subprocess. `test_ownership_fragment_resolver_returns_existing_file` is an
additional direct, in-process check of the `ownership_fragment()` resolver
itself against the source tree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from specfuse.orchestrator import ownership_fragment


def test_ownership_fragment_resolver_returns_existing_file():
    resolved = Path(ownership_fragment())
    assert resolved.is_file()
    assert resolved.name == "orchestrator.ownership.yaml"


def test_ownership_fragment_discoverable(installed_wheel):
    venv_python = installed_wheel / "bin" / "python"
    script = (
        "from importlib.metadata import entry_points; import sys; "
        "eps = entry_points(group='specfuse.ownership'); "
        "sys.exit(0 if any(e.name == 'orchestrator' for e in eps) else 1)"
    )
    result = subprocess.run(
        [str(venv_python), "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_ownership_fragment_is_valid_slice(installed_wheel):
    venv_python = installed_wheel / "bin" / "python"
    script = (
        "from importlib.metadata import entry_points; import yaml, sys; "
        "ep = next(e for e in entry_points(group='specfuse.ownership') if e.name == 'orchestrator'); "
        "fragment_path = ep.load()(); "
        "doc = yaml.safe_load(open(fragment_path)); "
        "entries = doc.get('entries'); "
        "ok = (isinstance(entries, list) and bool(entries) "
        "and all((e.get('canonical_source') or {}).get('repo') != 'loop' for e in entries)); "
        "sys.exit(0 if ok else 1)"
    )
    result = subprocess.run(
        [str(venv_python), "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
