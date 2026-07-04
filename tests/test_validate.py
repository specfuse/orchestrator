"""Deferred red tests for `validate_event.py` / `validate_frontmatter.py` (T05),
greened here, plus `main()` CLI coverage for the scoped `coverage` gate
(GATE-03-REVIEW.md open decision #2 — these two modules are in-scope).
"""

from __future__ import annotations

import io
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
