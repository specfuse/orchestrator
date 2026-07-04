"""Structural validation of docs/publish/release-runbook.md (FEAT-2026-0004/T02)."""

from __future__ import annotations

from pathlib import Path

RUNBOOK_PATH = Path(__file__).resolve().parent.parent / "docs" / "publish" / "release-runbook.md"


def test_release_runbook_sections():
    assert RUNBOOK_PATH.exists(), f"missing {RUNBOOK_PATH}"
    text = RUNBOOK_PATH.read_text(encoding="utf-8")
    lowered = text.lower()

    # PyPI trusted-publisher setup.
    assert "trusted publish" in lowered or "trusted-publish" in lowered
    assert "pypi" in lowered

    # Version bump + tag + push.
    assert "__version__" in text
    assert "git tag" in lowered
    assert "git push" in lowered

    # Trusted publisher must be configured before the first tag is pushed.
    assert "before" in lowered and "tag" in lowered

    # Post-publish verification.
    assert "pip install specfuse-orchestrator" in text
    assert "pipx install specfuse[orchestrator]" in text
