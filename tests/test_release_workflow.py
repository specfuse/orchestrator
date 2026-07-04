"""Structural validation of .github/workflows/release.yml (FEAT-2026-0004/T01)."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "release.yml"


def _load_workflow():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text), text


def test_release_workflow_shape():
    workflow, raw = _load_workflow()

    # YAML parses "on" as boolean True; PyYAML 6 keeps it as the string key "on"
    # in some configs, so accept either.
    on_section = workflow.get("on") or workflow.get(True)
    assert on_section is not None, "workflow must define a trigger ('on') section"

    tags = on_section.get("push", {}).get("tags", [])
    assert any("v" in tag for tag in tags), "workflow must trigger on v* tags"

    jobs = workflow["jobs"]
    assert "build-test" in jobs, "workflow must define a build-test job"
    assert "publish" in jobs, "workflow must define a publish job"

    build_test = jobs["build-test"]
    steps = build_test["steps"]
    step_runs = " ".join(step.get("run", "") for step in steps)

    assert "python -m build" in step_runs, "build-test must build wheel + sdist"
    assert "pytest" in step_runs, "build-test must run pytest against the built wheel"
    assert any(
        step.get("name", "").lower().startswith("tag/version")
        or "tag" in step.get("run", "").lower()
        and "version" in step.get("run", "").lower()
        for step in steps
    ), "build-test must include a tag==version agreement step"

    publish = jobs["publish"]
    assert publish.get("needs") == "build-test", "publish must depend on build-test"
    assert "startsWith(github.ref, 'refs/tags/v')" in str(publish.get("if", "")), (
        "publish must be gated on a v* tag ref"
    )
    assert publish.get("permissions", {}).get("id-token") == "write", (
        "publish must request OIDC id-token: write permission"
    )
    assert publish.get("environment") == "pypi", "publish must use the pypi environment"

    publish_uses = " ".join(step.get("uses", "") for step in publish["steps"])
    assert "pypa/gh-action-pypi-publish" in publish_uses, (
        "publish must use pypa/gh-action-pypi-publish"
    )

    # No stored PyPI token / password anywhere in the workflow — OIDC only.
    lowered = raw.lower()
    assert "password:" not in lowered
    assert "pypi_token" not in lowered
    assert "api-token" not in lowered
