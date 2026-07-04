"""Asserts the marketplace publish runbook documents the required operator steps.

The runbook (`docs/publish/marketplace-publish-runbook.md`) is the human-run,
cross-repo counterpart to the T04 staged delta — the loop cannot PR
`specfuse/specfuse` itself, so this test only checks the document's shape, not
any live marketplace state.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = REPO_ROOT / "docs" / "publish" / "marketplace-publish-runbook.md"


def test_runbook_has_operator_sections() -> None:
    body = RUNBOOK.read_text(encoding="utf-8")

    for heading in ("## Prerequisites", "## Steps", "## Post-merge verification"):
        assert heading in body, f"runbook missing {heading!r} section"

    for needle in (
        "specfuse/specfuse",
        ".claude-plugin/marketplace.json",
        "docs/publish/marketplace-orchestrator-entry.json",
    ):
        assert needle in body, f"runbook missing reference to {needle!r}"

    for needle in ("/plugin install", "specfuse-orchestrator@specfuse"):
        assert needle in body, f"runbook missing post-merge check {needle!r}"
