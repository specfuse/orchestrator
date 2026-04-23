#!/usr/bin/env python3
"""Validate the YAML frontmatter of a feature registry file against
shared/schemas/feature-frontmatter.schema.json.

Supported invocation patterns (only two):

    # Stdin — pipe the full content of a feature file:
    cat features/FEAT-2026-0004.md | python3 scripts/validate-frontmatter.py
    python3 scripts/validate-frontmatter.py --stdin   # explicit alias (same behaviour)

    # File — pass a path to a feature .md file:
    python3 scripts/validate-frontmatter.py --file features/FEAT-2026-0004.md

Any other form (positional arguments, --feature, --input, etc.) is rejected with
an error pointing at the two supported patterns above.

Exit codes:
    0 — frontmatter present and validated successfully against the schema
    1 — frontmatter validation failed (details on stderr)
    2 — setup error (missing dependency, schema not found, no frontmatter block,
        YAML parse failure, bad input, etc.)

The script is the parallel helper to scripts/validate-event.py for feature
frontmatter validation, per shared/rules/verify-before-report.md §3 (any
feature frontmatter that fails feature-frontmatter.schema.json is invalid;
verify before committing).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "error: the 'pyyaml' package is required.\n"
        "       install it with: pip install -r scripts/requirements.txt\n"
    )
    sys.exit(2)

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
    / "feature-frontmatter.schema.json"
)

_UNSUPPORTED_HINT = (
    "Supported invocation patterns:\n"
    "  cat features/FEAT-XXXX-NNNN.md | scripts/validate-frontmatter.py          # stdin\n"
    "  scripts/validate-frontmatter.py --stdin                                     # stdin (explicit)\n"
    "  scripts/validate-frontmatter.py --file features/FEAT-XXXX-NNNN.md          # file\n"
)


def load_validator() -> Draft202012Validator:
    if not SCHEMA_PATH.is_file():
        sys.stderr.write(f"error: schema not found at {SCHEMA_PATH}\n")
        sys.exit(2)
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def extract_frontmatter(content: str, source: str) -> dict:
    """Extract and parse the YAML frontmatter block from a markdown file.

    Frontmatter is a `---`-fenced block at the top of the file (the first line
    must be `---`; the block ends at the next `---` line). Returns the parsed
    dict on success; exits with code 2 on any error.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        sys.stderr.write(
            f"error: {source}: no YAML frontmatter block found "
            "(file must start with a `---` fence)\n"
        )
        sys.exit(2)

    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        sys.stderr.write(
            f"error: {source}: frontmatter block opened with `---` but never closed\n"
        )
        sys.exit(2)

    frontmatter_text = "\n".join(lines[1:end_index])
    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        sys.stderr.write(f"error: {source}: YAML parse failure — {exc}\n")
        sys.exit(2)

    if not isinstance(data, dict):
        sys.stderr.write(
            f"error: {source}: frontmatter parsed to a non-object type "
            f"({type(data).__name__}); expected a YAML mapping\n"
        )
        sys.exit(2)

    return data


def read_content_from_file(path: Path) -> str:
    if not path.is_file():
        sys.stderr.write(f"error: file not found: {path}\n")
        sys.exit(2)
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def read_content_from_stdin() -> str:
    data = sys.stdin.read()
    if not data.strip():
        sys.stderr.write("error: no input on stdin\n")
        sys.exit(2)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate feature frontmatter against shared/schemas/feature-frontmatter.schema.json.",
        epilog=_UNSUPPORTED_HINT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=Path,
        metavar="PATH",
        help="Path to a feature .md file whose frontmatter will be validated.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        default=False,
        help="Explicitly read the feature file from stdin (same behaviour as omitting --file).",
    )

    known, unknown = parser.parse_known_args()
    if unknown:
        sys.stderr.write(
            f"error: unsupported argument(s): {' '.join(unknown)}\n\n"
            + _UNSUPPORTED_HINT
        )
        return 2

    args = known

    if args.file is not None and args.stdin:
        sys.stderr.write(
            "error: --file and --stdin are mutually exclusive.\n\n"
            + _UNSUPPORTED_HINT
        )
        return 2

    validator = load_validator()

    if args.file is not None:
        source = str(args.file)
        content = read_content_from_file(args.file)
    else:
        source = "<stdin>"
        content = read_content_from_stdin()

    frontmatter = extract_frontmatter(content, source)

    errors = sorted(
        validator.iter_errors(frontmatter), key=lambda e: list(e.absolute_path)
    )

    if errors:
        for err in errors:
            path = "/".join(str(p) for p in err.absolute_path) or "(root)"
            sys.stderr.write(f"{source} at {path}: {err.message}\n")
        sys.stderr.write(
            f"\n{len(errors)} validation error(s) in frontmatter of {source}.\n"
        )
        return 1

    sys.stdout.write(f"ok: {source} frontmatter validated against {SCHEMA_PATH.name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
