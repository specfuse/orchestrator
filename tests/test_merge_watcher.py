# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""merge-watcher.yml's push-retry loop must fail the step when no push lands (#92)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(__file__).resolve().parent.parent / "shared" / "ci" / "merge-watcher.yml"
APPEND_STEP = "Append task_completed event to the orchestration event log"
LOOP_MARKER = "# Tolerate concurrent merges racing on the event log"


def _push_loop() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text())
    steps = [s for job in doc["jobs"].values() for s in job["steps"]]
    run = next(s["run"] for s in steps if s.get("name") == APPEND_STEP)
    return run[run.index(LOOP_MARKER):]


def _run_loop(tmp_path: Path, push_results: list[int]) -> subprocess.CompletedProcess:
    """Run the loop against a stub `git` whose Nth push exits push_results[N]."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (tmp_path / "pushes").write_text("")
    codes = " ".join(str(c) for c in push_results)
    stub = bindir / "git"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = push ]; then\n'
        f'  n=$(wc -l < "{tmp_path}/pushes"); echo x >> "{tmp_path}/pushes"\n'
        f"  codes=({codes}); exit ${{codes[$n]:-1}}\n"
        "fi\n"
        "exit 0\n"
    )
    stub.chmod(0o755)
    script = "set -euo pipefail\n" + _push_loop()
    return subprocess.run(
        ["bash", "-c", script],
        env={"PATH": f"{bindir}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )


pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


def test_step_fails_when_every_push_is_rejected(tmp_path):
    result = _run_loop(tmp_path, [1, 1, 1, 1, 1])
    assert result.returncode != 0, result.stdout
    assert "pushed" not in result.stdout.splitlines()


def test_step_succeeds_on_first_push(tmp_path):
    result = _run_loop(tmp_path, [0])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pushed" in result.stdout.splitlines()


def test_step_succeeds_after_a_rejected_push(tmp_path):
    result = _run_loop(tmp_path, [1, 1, 0])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pushed" in result.stdout.splitlines()
