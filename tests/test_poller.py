"""Behavioral tests for the poller's dispatch/state logic.

The poller was untested before the distribution migration; these cover its pure
and near-pure decision functions (feature loading, done-detection, autonomy
resolution, dispatch routing, initiative-state derivation, next-step defaults).
GitHub- and subprocess-touching paths (hydrate_from_github, dispatch backends)
are out of scope — they need a live gh/loop and belong in integration tests.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from specfuse.orchestrator import poller


def _registry(tmp_path, *, graph_key="feature_graph", state="in_progress"):
    p = tmp_path / "INIT-2026-0001.md"
    p.write_text(textwrap.dedent(f"""\
        ---
        correlation_id: INIT-2026-0001
        state: {state}
        involved_repos:
          - acme/backend
        autonomy_default: review
        {graph_key}:
          - id: F01
            type: implementation
            depends_on: []
            assigned_repo: acme/backend
          - id: F02
            type: qa_execution
            depends_on: [F01]
            assigned_repo: acme/backend
        ---

        body
        """))
    return p


def test_load_initiative_feature_graph(tmp_path):
    init = poller.load_initiative(_registry(tmp_path))
    assert init.correlation_id == "INIT-2026-0001"
    assert init.autonomy_default == "review"
    assert set(init.features) == {"F01", "F02"}
    assert init.features["F02"].ftype == "qa_execution"
    assert init.features["F02"].depends_on == ["F01"]


def test_load_initiative_accepts_legacy_task_graph(tmp_path):
    # The INIT reframe kept task_graph valid; load_initiative must accept either.
    init = poller.load_initiative(_registry(tmp_path, graph_key="task_graph"))
    assert set(init.features) == {"F01", "F02"}


def test_is_done_via_label_or_closed_issue():
    f = poller.Feature(fid="F01", ftype="implementation", depends_on=[], assigned_repo="acme/backend")
    assert poller.is_done(f) is False
    f.state_label = "state:done"
    assert poller.is_done(f) is True
    f.state_label = "state:ready"
    f.gh_state = "CLOSED"
    assert poller.is_done(f) is True


def test_feature_autonomy_label_overrides_default(tmp_path):
    init = poller.load_initiative(_registry(tmp_path))  # autonomy_default: review
    f = init.features["F01"]
    assert poller.feature_autonomy(init, f) == "review"
    f.autonomy_label = "autonomy:auto"
    assert poller.feature_autonomy(init, f) == "auto"


def test_executor_for_routes_qa_to_agent_impl_to_loop():
    qa = poller.Feature(fid="F02", ftype="qa_execution", depends_on=[], assigned_repo="acme/backend")
    impl = poller.Feature(fid="F01", ftype="implementation", depends_on=[], assigned_repo="acme/backend")
    assert poller.executor_for(qa) == "qa-agent"
    assert poller.executor_for(impl) == "component-loop"


def test_current_initiative_state_prefers_last_event(tmp_path, monkeypatch):
    monkeypatch.setenv("SPECFUSE_ORCH_STATE", str(tmp_path))
    (tmp_path / "project").mkdir()
    (tmp_path / "features").mkdir()
    events = tmp_path / "events"
    events.mkdir()
    init = poller.load_initiative(_registry(tmp_path, state="planning"))
    # no log yet -> falls back to frontmatter state
    assert poller.current_initiative_state(init) == "planning"
    (events / "INIT-2026-0001.jsonl").write_text(
        '{"event_type":"feature_state_changed","correlation_id":"INIT-2026-0001","payload":{"to_state":"generating"}}\n'
        '{"event_type":"feature_state_changed","correlation_id":"INIT-2026-0001","payload":{"to_state":"in_progress"}}\n'
    )
    assert poller.current_initiative_state(init) == "in_progress"


def test_default_next_step_known_and_unknown():
    ns = poller._default_next_step("planning")
    assert ns["owner"] == "pm-agent"
    assert "updated" in ns
    with pytest.raises(RuntimeError):
        poller._default_next_step("not-a-state")


def test_pm_version_uses_package_resolver(monkeypatch):
    monkeypatch.setattr(poller, "resolve_agent_version", lambda role: "9.9.9")
    assert poller.pm_version() == "9.9.9"


@pytest.mark.parametrize("exc", [KeyError("pm"), FileNotFoundError("gone")])
def test_pm_version_na_on_missing(monkeypatch, exc):
    def raiser(role):
        raise exc
    monkeypatch.setattr(poller, "resolve_agent_version", raiser)
    assert poller.pm_version() == "n/a"


def test_no_driver_runtime_reads_vendored_agents():
    orch_dir = Path(poller.__file__).parent
    for path in sorted(orch_dir.glob("*.py")):
        source = path.read_text()
        if path.name == "_version.py":
            # the resolver's `--repo` dev-override fallback legitimately walks
            # agents/<role>/version.md via read_agent_version itself.
            continue
        assert "read_agent_version(REPO_ROOT" not in source, (
            f"{path}: runtime read of vendored agents/ tree via REPO_ROOT"
        )
        for node in ast.walk(ast.parse(source, filename=str(path))):
            if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
                continue
            const_strs = [
                n.value for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            ]
            if "agents" in const_strs and "version.md" in const_strs:
                pytest.fail(f"{path}: constructs an agents/<role>/version.md path at runtime")
