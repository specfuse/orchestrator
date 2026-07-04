"""Behavioral tests for the runner's per-feature status logic.

Covers the pure/fixture-driven decision functions the runner uses to classify a
feature's loop state (gate-passed, awaiting-review, plan-complete), plus id
encoding and frontmatter mutation. Git/worktree/loop-dispatch paths need a live
repo and are out of scope here.
"""

from __future__ import annotations

import textwrap

from specfuse.orchestrator import runner


def _gate(dirpath, n, status):
    (dirpath / f"GATE-0{n}.md").write_text(f"---\ngate: {n}\nstatus: {status}\n---\n\n# Gate {n}\n")


def _plan(dirpath, status):
    (dirpath / "PLAN.md").write_text(
        f"---\nfeature_id: INIT-2026-0001/F01\nstatus: {status}\n---\n\n# Plan\n"
    )


def test_encode_id_slash_to_dash():
    assert runner.encode_id("INIT-2026-0001/F06") == "INIT-2026-0001-F06"
    assert runner.encode_id("FEAT-2026-0001") == "FEAT-2026-0001"


def test_all_gates_passed(tmp_path):
    assert runner.all_gates_passed(tmp_path) is False  # no gates
    _gate(tmp_path, 1, "passed")
    _gate(tmp_path, 2, "passed")
    assert runner.all_gates_passed(tmp_path) is True
    _gate(tmp_path, 2, "awaiting_review")
    assert runner.all_gates_passed(tmp_path) is False


def test_any_gate_awaiting_review(tmp_path):
    _gate(tmp_path, 1, "passed")
    assert runner.any_gate_awaiting_review(tmp_path) is False
    _gate(tmp_path, 2, "awaiting_review")
    assert runner.any_gate_awaiting_review(tmp_path) is True


def test_plan_complete(tmp_path):
    assert runner.plan_complete(tmp_path) is False  # no PLAN
    _plan(tmp_path, "active")
    assert runner.plan_complete(tmp_path) is False
    _plan(tmp_path, "complete")
    assert runner.plan_complete(tmp_path) is True


def test_set_frontmatter_field_replaces_and_appends(tmp_path):
    p = tmp_path / "GATE-01.md"
    _gate(tmp_path, 1, "open")
    runner.set_frontmatter_field(p, "status", "passed")
    assert runner.parse_frontmatter(p)["status"] == "passed"
    # appends a key that wasn't present
    runner.set_frontmatter_field(p, "reviewed_by", "human")
    assert runner.parse_frontmatter(p)["reviewed_by"] == "human"
