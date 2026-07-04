"""Shared fixtures for the specfuse-orchestrator pytest harness.

Two fixtures back most of tests/:

- `substrate_ready` (autouse): regenerates `specfuse/orchestrator/_substrate/`
  from `shared/` in place, mirroring `hatch_build.py`'s `SubstrateBuildHook`.
  `_substrate/` is a gitignored build artifact absent from a fresh checkout;
  drivers that call `paths.substrate(...)` need it on disk to resolve schemas.
- `installed_wheel` (session-scoped): builds the wheel and installs it into a
  fresh temp venv once per test session. Entry-point discovery
  (`importlib.metadata`) and package-data resolution can only be observed from
  an installed distribution, not the source tree, so tests that assert
  against-the-wheel behavior run a subprocess against this venv's
  interpreter/console scripts instead of importing in-process.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def substrate_ready():
    dest = REPO_ROOT / "specfuse" / "orchestrator" / "_substrate"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(REPO_ROOT / "shared", dest)
    yield dest


@pytest.fixture(scope="session")
def installed_wheel(tmp_path_factory):
    build_dir = tmp_path_factory.mktemp("wheel-build")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(build_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = sorted(build_dir.glob("*.whl"))
    assert wheels, "wheel build produced no .whl file"

    venv_dir = tmp_path_factory.mktemp("wheel-venv")
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"

    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True,
        capture_output=True,
        text=True,
    )
    return venv_dir
