# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#111 — project-keyed feature IDs (FEAT-<KEY>-YYYY-NNNN) are accepted wherever
unkeyed ones are: the Python matchers, the orchestrator-owned schemas, the QA
skills' branch matchers and the correlation-ID rule."""

import json
import re
from pathlib import Path

import pytest

from specfuse.orchestrator import poller, qa_dispatcher, raise_spec_issue, reconcile_overrides

ROOT = Path(__file__).resolve().parent.parent
KEYED = "FEAT-ACME-2026-0042"

# Core-owned and vendored byte for byte: widened in core first, then re-vendored.
CORE_PENDING = {"feature-mint.schema.json"}

# An unkeyed-only FEAT pattern: FEAT immediately followed by the year, with no
# optional key group anywhere in the same alternative.
UNKEYED_ONLY = re.compile(r"\(FEAT\|INIT\)-|FEAT-\\+d\{4\}")


@pytest.mark.parametrize("title_re", [poller.TITLE_ID_RE, qa_dispatcher.TITLE_ID_RE])
@pytest.mark.parametrize("cid", [KEYED, "FEAT-2026-0042", "INIT-2026-0001/F06"])
def test_title_matchers_accept_keyed_and_unkeyed(title_re, cid):
    m = title_re.search(f"[{cid}] Some title")
    assert m and m.group(1) == cid


@pytest.mark.parametrize("bad", ["FEAT-acme-2026-0042", "FEAT-TOOLONG-2026-0042", "FEAT-1A-2026-0042"])
def test_title_matchers_reject_malformed_keys(bad):
    assert poller.TITLE_ID_RE.search(f"[{bad}] x") is None


def test_spec_issue_correlation_and_root_accept_keyed():
    m = raise_spec_issue.CORRELATION_RE.search(f"Correlation ID: {KEYED}/G1-CLOSE")
    assert m and m.group(1) == f"{KEYED}/G1-CLOSE"
    assert raise_spec_issue.ROOT_RE.match(f"{KEYED}/T03").group(1) == KEYED


def test_reconcile_overrides_root_accepts_keyed():
    assert reconcile_overrides.ROOT_RE.match(f"{KEYED}/T03").group(1) == KEYED


def _patterns(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "pattern" and isinstance(v, str):
                yield v
            else:
                yield from _patterns(v)
    elif isinstance(node, list):
        for v in node:
            yield from _patterns(v)


def test_no_orchestrator_schema_pattern_is_unkeyed_only():
    stale = []
    for path in sorted((ROOT / "shared" / "schemas").rglob("*.json")):
        if path.name in CORE_PENDING:
            continue
        for pat in _patterns(json.loads(path.read_text())):
            if UNKEYED_ONLY.search(pat):
                stale.append(f"{path.relative_to(ROOT)}: {pat}")
    assert stale == []


@pytest.mark.parametrize("path", sorted((ROOT / "shared" / "schemas").rglob("*.json")), ids=lambda p: p.name)
def test_feat_patterns_accept_a_keyed_id(path):
    if path.name in CORE_PENDING:
        pytest.skip("core-owned; widened in core first")
    for pat in _patterns(json.loads(path.read_text())):
        if "FEAT" not in pat:
            continue
        # The unkeyed sample each pattern already accepts, keyed.
        for unkeyed in _samples():
            if re.search(pat, unkeyed):
                assert re.search(pat, unkeyed.replace("FEAT-", "FEAT-ACME-", 1)), (path.name, pat)


def _samples():
    return [
        "FEAT-2026-0042",
        "FEAT-2026-0042/T03",
        "FEAT-2026-0042/G1-CLOSE",
        "/product/test-plans/FEAT-2026-0042.md",
        "inbox/qa-regression/FEAT-2026-0042-login-fails.md",
    ]


def test_qa_skill_branch_matchers_accept_keyed():
    pats = []
    for skill in ("qa-authoring", "qa-curation"):
        text = (ROOT / "agents" / "qa" / "skills" / skill / "SKILL.md").read_text()
        pats += re.findall(r"`(\^qa-[a-z]+/FEAT[^`]*\$)`", text)
    assert len(pats) == 3
    for pat in pats:
        prefix = pat[1:].split("/", 1)[0]
        assert re.match(pat, f"{prefix}/{KEYED}-T03"), pat
        assert re.match(pat, f"{prefix}/FEAT-2026-0042-T03"), pat


def test_correlation_ids_rule_grammar_accepts_keyed():
    text = (ROOT / "shared" / "rules" / "correlation-ids.md").read_text()
    grammar = next(ln for ln in text.splitlines() if ln.startswith("^(FEAT"))
    for cid in (KEYED, f"{KEYED}/T03", f"{KEYED}/G2-PLAN", "FEAT-2026-0042/T03H1", "INIT-2026-0001/F02/T01"):
        assert re.fullmatch(grammar, cid), cid
    assert "FEAT-<KEY>-YYYY-NNNN" in text
