#!/usr/bin/env python3
"""Validate orchestrator event log entries against shared/schemas/event.schema.json.

Usage:
    # Single event on stdin (one JSON object, trailing newline optional):
    echo '{"timestamp": "...", ...}' | python3 scripts/validate-event.py

    # Multiple events on stdin (JSONL, one event per line, blank lines ignored):
    cat candidate-events.jsonl | python3 scripts/validate-event.py

    # A committed events file (same JSONL format):
    python3 scripts/validate-event.py --file events/FEAT-2026-0001.jsonl

Exit codes:
    0 — every event validated successfully
    1 — at least one event failed validation (details on stderr)
    2 — setup error (missing dependency, schema not found, bad input, etc.)

The script is the normative gate for appending to events/*.jsonl per
shared/rules/verify-before-report.md §3.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write(
        "error: the 'jsonschema' package is required.\n"
        "       install it with: pip install -r scripts/requirements.txt\n"
    )
    sys.exit(2)

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "shared"
    / "schemas"
    / "event.schema.json"
)


def load_validator() -> Draft202012Validator:
    if not SCHEMA_PATH.is_file():
        sys.stderr.write(f"error: schema not found at {SCHEMA_PATH}\n")
        sys.exit(2)
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def format_error(source: str, line_number: int, path: str, message: str) -> str:
    location = f"{source}:{line_number}" if line_number else source
    prefix = f"{location}"
    if path:
        prefix += f" at {path}"
    return f"{prefix}: {message}"


def validate_line(
    validator: Draft202012Validator,
    source: str,
    line_number: int,
    raw: str,
) -> list[str]:
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [format_error(source, line_number, "", f"invalid JSON — {exc.msg} (line {exc.lineno}, col {exc.colno})")]

    errors: list[str] = []
    for err in sorted(validator.iter_errors(event), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(format_error(source, line_number, path, err.message))
    return errors


def iter_lines_from_file(path: Path) -> list[tuple[int, str]]:
    if not path.is_file():
        sys.stderr.write(f"error: file not found: {path}\n")
        sys.exit(2)
    lines: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            stripped = raw.strip()
            if stripped:
                lines.append((lineno, stripped))
    return lines


def iter_lines_from_stdin() -> list[tuple[int, str]]:
    data = sys.stdin.read()
    if not data.strip():
        sys.stderr.write("error: no input on stdin\n")
        sys.exit(2)
    lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(data.splitlines(), start=1):
        stripped = raw.strip()
        if stripped:
            lines.append((lineno, stripped))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate events against shared/schemas/event.schema.json.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to a .jsonl file of events. If omitted, events are read from stdin.",
    )
    args = parser.parse_args()

    validator = load_validator()

    if args.file is not None:
        source = str(args.file)
        entries = iter_lines_from_file(args.file)
    else:
        source = "<stdin>"
        entries = iter_lines_from_stdin()

    all_errors: list[str] = []
    for lineno, raw in entries:
        all_errors.extend(validate_line(validator, source, lineno, raw))

    if all_errors:
        for msg in all_errors:
            sys.stderr.write(msg + "\n")
        sys.stderr.write(
            f"\n{len(all_errors)} validation error(s) across {len(entries)} event(s).\n"
        )
        return 1

    sys.stdout.write(f"ok: {len(entries)} event(s) validated against {SCHEMA_PATH.name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
