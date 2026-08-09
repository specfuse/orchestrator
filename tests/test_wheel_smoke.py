"""Against-the-wheel smoke test (T08, cluster F06 WU-02).

Builds the wheel, installs it into a temp venv (via the shared
`installed_wheel` fixture), and runs each of the four console scripts from
that venv — the runnable proof that packaging (T06) actually produces working
CLI entry points post-install, not just importable modules.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# The DEPRECATED flat console scripts. Users drive the suite through
# `specfuse <subcommand>`, but a standalone `pip install specfuse-orchestrator`
# still ships these and this venv has no umbrella on PATH, so they are what the
# wheel must expose. They come out in the coordinated 1.0.0 release train.
CONSOLE_SCRIPTS = [
    "specfuse-poller",
    "specfuse-runner",
    "specfuse-validate-event",
    "specfuse-validate-frontmatter",
]


@pytest.mark.parametrize("script", CONSOLE_SCRIPTS)
def test_console_script_help(installed_wheel, script):
    exe = installed_wheel / "bin" / script
    assert exe.is_file(), f"{script} was not installed as a console script"
    result = subprocess.run([str(exe), "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_validate_event_script_on_valid_fixture(installed_wheel):
    exe = installed_wheel / "bin" / "specfuse-validate-event"
    result = subprocess.run(
        [str(exe), "--file", str(FIXTURES / "valid_event.jsonl")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
