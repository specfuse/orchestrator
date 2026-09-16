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


# --- orchestration repo slug and branch matching ------------------------------------------

def _steps() -> list[dict]:
    doc = yaml.safe_load(WORKFLOW.read_text())
    return [s for job in doc["jobs"].values() for s in job["steps"]]


def _step(step_id: str) -> dict:
    return next(s for s in _steps() if s.get("id") == step_id)


def _run_step(tmp_path: Path, step_id: str, env: dict[str, str]) -> tuple[int, dict[str, str], str]:
    out = tmp_path / f"{step_id}.out"
    out.write_text("")
    r = subprocess.run(
        ["bash", "-c", _step(step_id)["run"]],
        env={"PATH": "/usr/bin:/bin", "GITHUB_OUTPUT": str(out), **env},
        capture_output=True, text=True,
    )
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines() if "=" in line)
    return r.returncode, outputs, r.stdout + r.stderr


def test_template_carries_no_example_org():
    assert "acme" not in WORKFLOW.read_text()


def test_orchestration_repo_comes_from_the_repository_variable():
    doc = yaml.safe_load(WORKFLOW.read_text())
    assert doc["env"]["ORCH_REPO"] == "${{ vars.SPECFUSE_ORCH_REPO }}"
    token = next(s for s in _steps() if s.get("id") == "orchtoken")["with"]
    assert token["owner"] == "${{ steps.orch.outputs.owner }}"
    assert token["repositories"] == "${{ steps.orch.outputs.name }}"
    checkout = next(s for s in _steps() if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["repository"] == "${{ env.ORCH_REPO }}"


def test_orchestration_repo_resolves_owner_and_name(tmp_path):
    code, outputs, _ = _run_step(tmp_path, "orch", {"ORCH_REPO": "example-org/orchestration"})
    assert code == 0
    assert outputs == {"owner": "example-org", "name": "orchestration"}


@pytest.mark.parametrize("value", ["", "orchestration", "a/b/c", "owner/"])
def test_orchestration_repo_step_fails_clearly_when_variable_is_unusable(tmp_path, value):
    code, _, output = _run_step(tmp_path, "orch", {"ORCH_REPO": value})
    assert code != 0
    assert "SPECFUSE_ORCH_REPO" in output


def test_feature_branch_resolves_initiative_and_feature(tmp_path):
    code, outputs, _ = _run_step(tmp_path, "cid", {"BRANCH": "feat/INIT-2026-0011-F03-guardrails"})
    assert code == 0
    assert outputs == {"cid": "INIT-2026-0011/F03", "init": "INIT-2026-0011", "skip": "false"}


@pytest.mark.parametrize("branch", ["feat/FEAT-2026-0042-loop-local", "fix/typo", "INIT-2026-0011"])
def test_non_initiative_branches_are_skipped(tmp_path, branch):
    code, outputs, _ = _run_step(tmp_path, "cid", {"BRANCH": branch})
    assert code == 0
    assert outputs == {"skip": "true"}


def test_orchestration_repo_is_checked_before_the_issue_is_closed():
    ids = [s.get("id") or s.get("name") for s in _steps()]
    assert ids.index("orch") < ids.index("Flip feature issue to state:done and close")
