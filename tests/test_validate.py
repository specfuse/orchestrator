"""Deferred red tests for `validate_event.py` / `validate_frontmatter.py` (T05),
greened here, plus `main()` CLI coverage for the scoped `coverage` gate
(GATE-03-REVIEW.md open decision #2 — these two modules are in-scope).
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pytest

from specfuse.orchestrator import validate_event, validate_frontmatter

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# validate_event.validate() — the deferred red tests
# ---------------------------------------------------------------------------


def test_validate_event_valid(substrate_ready):
    errors = validate_event.validate(FIXTURES / "valid_event.jsonl")
    assert errors == []


def test_validate_event_invalid(substrate_ready):
    errors = validate_event.validate(FIXTURES / "invalid_event.jsonl")
    assert len(errors) >= 3


def test_validate_event_missing_file(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_event.validate(FIXTURES / "does-not-exist.jsonl")
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# correlation_id shapes (issue #81)
#
# The envelope pattern accepted `/TNN` and nothing else, so every event a
# closing-sequence or hygiene work unit emitted failed validation against a
# contract (.specfuse/rules/correlation-ids.md) that has documented those shapes
# as valid all along. These tests pin the widened set from both directions: the
# shapes that must now pass, and the rejections that must survive the widening.
# ---------------------------------------------------------------------------


def _event_with(correlation_id: str) -> dict:
    return {
        "timestamp": "2026-08-09T12:00:00Z",
        "correlation_id": correlation_id,
        "event_type": "task_started",
        "source": "component:orchestrator-api-sample",
        "source_version": "1.2.0",
        # task_started has a per-type payload schema; these are the fixture's
        # values, so the only thing varying across these cases is the ID.
        "payload": {
            "issue_url": "https://github.com/acme/api-sample/issues/3",
            "branch": "feat/FEAT-2026-0001-T01-widget-quantity-ceiling",
        },
    }


def _validate_correlation_id(tmp_path: Path, correlation_id: str) -> list[str]:
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps(_event_with(correlation_id)) + "\n", encoding="utf-8")
    return validate_event.validate(log)


VALID_CORRELATION_IDS = [
    # feature-level, both namespaces
    "FEAT-2026-0042",
    "INIT-2026-0011",
    "INIT-2026-0001/F06",
    # substantive work units — the only shape the pattern accepted before
    "FEAT-2026-0042/T07",
    "INIT-2026-0001/F06/T01",
    # hygiene units: target ordinal, literal H, optional disambiguating ordinal
    "FEAT-2026-0042/T07H",
    "FEAT-2026-0042/T07H2",
    "INIT-2026-0001/F06/T02H",
    # closing-sequence units, every documented NAME
    "FEAT-2026-0042/G1-RETRO",
    "FEAT-2026-0042/G1-LESSONS",
    "FEAT-2026-0042/G1-DOCS",
    "FEAT-2026-0042/G1-PLAN",
    "FEAT-2026-0042/G1-CLOSE",
    "FEAT-2026-0042/G1-CLOSE-INTERMEDIATE",
    "INIT-2026-0001/F06/G1-RETRO",
    # multi-digit gate numbers
    "FEAT-2026-0042/G12-CLOSE",
]


@pytest.mark.parametrize("correlation_id", VALID_CORRELATION_IDS)
def test_validate_event_accepts_documented_correlation_id(substrate_ready, tmp_path, correlation_id):
    assert _validate_correlation_id(tmp_path, correlation_id) == []


INVALID_CORRELATION_IDS = [
    "",                                  # empty
    "FEAT-2026-0042/",                   # empty task segment
    "FEAT-2026-0042/G1-FOO",             # undocumented closing name
    "FEAT-2026-0042/G-CLOSE",            # closing without a gate number
    "FEAT-2026-0042/T7",                 # unpadded ordinal
    "FEAT-2026-0042/T007",               # over-padded ordinal
    "FEAT-2026-0042/TH",                 # hygiene without a target ordinal
    "FEAT-2026-042/T07",                 # short feature ordinal
    "BUG-2026-0042/T07",                 # unknown namespace
    "FEAT-2026-0042/T07/T08",            # two task segments
    "feat-2026-0042/t07",                # lowercase
]


@pytest.mark.parametrize("correlation_id", INVALID_CORRELATION_IDS)
def test_validate_event_rejects_malformed_correlation_id(substrate_ready, tmp_path, correlation_id):
    errors = _validate_correlation_id(tmp_path, correlation_id)
    assert errors, f"{correlation_id!r} should not validate"
    assert any("correlation_id" in e for e in errors), errors


# Task-level payload fields carry the same widening, with one deliberate
# asymmetry: the two `implementation_task_correlation_id` fields name the unit
# whose delivered code a regression is attributed against, so they take hygiene
# units (which do deliver code) but not closing units (which do not).
GENERIC_TASK_FIELDS = [
    ("override.schema.json", "task_correlation_id"),
    ("events/qa_execution_completed.schema.json", "task_correlation_id"),
    ("events/qa_execution_failed.schema.json", "task_correlation_id"),
    ("events/spec_issue_resolved.schema.json", "original_issue_correlation_id"),
    ("events/spec_issue_routed.schema.json", "original_issue_correlation_id"),
]
IMPLEMENTATION_TASK_FIELDS = [
    ("events/qa_regression_filed.schema.json", "implementation_task_correlation_id"),
    ("events/qa_regression_resolved.schema.json", "implementation_task_correlation_id"),
]


def _field_pattern(substrate: Path, relative: str, field: str) -> re.Pattern:
    schema = json.loads((substrate / "schemas" / relative).read_text(encoding="utf-8"))
    return re.compile(schema["properties"][field]["pattern"])


@pytest.mark.parametrize(("relative", "field"), GENERIC_TASK_FIELDS)
def test_generic_task_fields_accept_every_documented_shape(substrate_ready, relative, field):
    pattern = _field_pattern(substrate_ready, relative, field)
    for value in ("FEAT-2026-0042/T07", "FEAT-2026-0042/T07H", "FEAT-2026-0042/T07H2",
                  "FEAT-2026-0042/G1-CLOSE", "FEAT-2026-0042/G1-CLOSE-INTERMEDIATE",
                  "INIT-2026-0001/F06/G1-RETRO"):
        assert pattern.match(value), f"{relative}:{field} should accept {value}"
    for value in ("FEAT-2026-0042", "INIT-2026-0001/F06", "FEAT-2026-0042/G1-FOO"):
        assert not pattern.match(value), f"{relative}:{field} should reject {value}"


@pytest.mark.parametrize(("relative", "field"), IMPLEMENTATION_TASK_FIELDS)
def test_implementation_task_fields_take_hygiene_but_not_closing(substrate_ready, relative, field):
    pattern = _field_pattern(substrate_ready, relative, field)
    for value in ("FEAT-2026-0042/T07", "FEAT-2026-0042/T07H", "INIT-2026-0001/F06/T02H2"):
        assert pattern.match(value), f"{relative}:{field} should accept {value}"
    for value in ("FEAT-2026-0042/G1-CLOSE", "FEAT-2026-0042/G1-RETRO", "FEAT-2026-0042"):
        assert not pattern.match(value), f"{relative}:{field} should reject {value}"


# ---------------------------------------------------------------------------
# validate_frontmatter.validate() — the deferred red tests
# ---------------------------------------------------------------------------


def test_validate_frontmatter_valid(substrate_ready):
    errors = validate_frontmatter.validate(FIXTURES / "valid_frontmatter.md")
    assert errors == []


def test_validate_frontmatter_invalid(substrate_ready):
    errors = validate_frontmatter.validate(FIXTURES / "invalid_frontmatter.md")
    assert len(errors) >= 2


def test_validate_frontmatter_no_fence(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.validate(FIXTURES / "frontmatter_no_fence.md")
    assert exc.value.code == 2


def test_validate_frontmatter_unclosed(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.validate(FIXTURES / "frontmatter_unclosed.md")
    assert exc.value.code == 2


def test_validate_frontmatter_bad_yaml(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.validate(FIXTURES / "frontmatter_bad_yaml.md")
    assert exc.value.code == 2


def test_validate_frontmatter_non_dict(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.validate(FIXTURES / "frontmatter_non_dict.md")
    assert exc.value.code == 2


def test_validate_frontmatter_missing_file(substrate_ready):
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.validate(FIXTURES / "does-not-exist.md")
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# validate_event.main() — CLI argument handling
# ---------------------------------------------------------------------------


def test_validate_event_main_file_valid(substrate_ready, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["specfuse-validate-event", "--file", str(FIXTURES / "valid_event.jsonl")]
    )
    assert validate_event.main() == 0
    assert "ok:" in capsys.readouterr().out


def test_validate_event_main_file_invalid(substrate_ready, monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["specfuse-validate-event", "--file", str(FIXTURES / "invalid_event.jsonl")]
    )
    assert validate_event.main() == 1


def test_validate_event_main_stdin_explicit(substrate_ready, monkeypatch):
    content = (FIXTURES / "valid_event.jsonl").read_text(encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["specfuse-validate-event", "--stdin"])
    monkeypatch.setattr("sys.stdin", io.StringIO(content))
    assert validate_event.main() == 0


def test_validate_event_main_stdin_default(substrate_ready, monkeypatch):
    content = (FIXTURES / "invalid_event.jsonl").read_text(encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["specfuse-validate-event"])
    monkeypatch.setattr("sys.stdin", io.StringIO(content))
    assert validate_event.main() == 1


def test_validate_event_main_file_and_stdin_mutually_exclusive(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["specfuse-validate-event", "--file", str(FIXTURES / "valid_event.jsonl"), "--stdin"],
    )
    assert validate_event.main() == 2


def test_validate_event_main_unsupported_arg(monkeypatch):
    monkeypatch.setattr("sys.argv", ["specfuse-validate-event", "--bogus"])
    assert validate_event.main() == 2


def test_validate_event_main_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.argv", ["specfuse-validate-event", "--stdin"])
    monkeypatch.setattr("sys.stdin", io.StringIO("   \n"))
    with pytest.raises(SystemExit) as exc:
        validate_event.main()
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# validate_frontmatter.main() — CLI argument handling
# ---------------------------------------------------------------------------


def test_validate_frontmatter_main_file_valid(substrate_ready, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        ["specfuse-validate-frontmatter", "--file", str(FIXTURES / "valid_frontmatter.md")],
    )
    assert validate_frontmatter.main() == 0
    assert "ok:" in capsys.readouterr().out


def test_validate_frontmatter_main_file_invalid(substrate_ready, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["specfuse-validate-frontmatter", "--file", str(FIXTURES / "invalid_frontmatter.md")],
    )
    assert validate_frontmatter.main() == 1


def test_validate_frontmatter_main_stdin_explicit(substrate_ready, monkeypatch):
    content = (FIXTURES / "valid_frontmatter.md").read_text(encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["specfuse-validate-frontmatter", "--stdin"])
    monkeypatch.setattr("sys.stdin", io.StringIO(content))
    assert validate_frontmatter.main() == 0


def test_validate_frontmatter_main_stdin_default(substrate_ready, monkeypatch):
    content = (FIXTURES / "invalid_frontmatter.md").read_text(encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["specfuse-validate-frontmatter"])
    monkeypatch.setattr("sys.stdin", io.StringIO(content))
    assert validate_frontmatter.main() == 1


def test_validate_frontmatter_main_file_and_stdin_mutually_exclusive(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "specfuse-validate-frontmatter",
            "--file",
            str(FIXTURES / "valid_frontmatter.md"),
            "--stdin",
        ],
    )
    assert validate_frontmatter.main() == 2


def test_validate_frontmatter_main_unsupported_arg(monkeypatch):
    monkeypatch.setattr("sys.argv", ["specfuse-validate-frontmatter", "--bogus"])
    assert validate_frontmatter.main() == 2


def test_validate_frontmatter_main_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.argv", ["specfuse-validate-frontmatter", "--stdin"])
    monkeypatch.setattr("sys.stdin", io.StringIO("   \n"))
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.main()
    assert exc.value.code == 2
