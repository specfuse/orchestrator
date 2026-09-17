#!/usr/bin/env python3
"""Validate the YAML frontmatter of a feature registry file against
shared/schemas/feature-frontmatter.schema.json.

Supported invocation patterns (only two):

    # Stdin — pipe the full content of a feature file:
    cat features/FEAT-2026-0004.md | specfuse validate-frontmatter
    specfuse validate-frontmatter --stdin   # explicit alias (same behaviour)

    # File — pass a path to a feature .md file:
    specfuse validate-frontmatter --file features/FEAT-2026-0004.md

Any other form (positional arguments, --feature, --input, etc.) is rejected with
an error pointing at the two supported patterns above.

Exit codes:
    0 — frontmatter present and validated successfully against the schema
    1 — frontmatter validation failed (details on stderr)
    2 — setup error (missing dependency, schema not found, no frontmatter block,
        YAML parse failure, bad input, etc.)

The script is the parallel helper to specfuse validate-event for feature
frontmatter validation, per shared/rules/verify-before-report.md §3 (any
feature frontmatter that fails feature-frontmatter.schema.json is invalid;
verify before committing).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from specfuse.orchestrator import paths

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "error: the 'pyyaml' package is required.\n"
        "       install it with: pip install specfuse-orchestrator\n"
    )
    sys.exit(2)

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    sys.stderr.write(
        "error: the 'jsonschema' package is required.\n"
        "       install it with: pip install specfuse-orchestrator\n"
    )
    sys.exit(2)

# The core mint contract feature-frontmatter.schema.json composes by `$ref`
# (specfuse/specfuse#179). A byte-identical vendored copy of core's file, resolved
# from this package's substrate by its `$id` — never fetched over the network.
MINT_SCHEMA_FILE = "feature-mint.schema.json"

_UNSUPPORTED_HINT = (
    "Supported invocation patterns:\n"
    "  cat features/FEAT-XXXX-NNNN.md | specfuse validate-frontmatter          # stdin\n"
    "  specfuse validate-frontmatter --stdin                                     # stdin (explicit)\n"
    "  specfuse validate-frontmatter --file features/FEAT-XXXX-NNNN.md          # file\n"
)


def _load_schema(name: str) -> dict:
    schema_path = paths.substrate("schemas", name)
    if not schema_path.is_file():
        sys.stderr.write(f"error: schema not found at {schema_path}\n")
        sys.exit(2)
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return schema


def load_validator() -> Draft202012Validator:
    schema = _load_schema("feature-frontmatter.schema.json")
    mint = _load_schema(MINT_SCHEMA_FILE)
    registry = Registry().with_resource(mint["$id"], Resource.from_contents(mint))
    return Draft202012Validator(schema, registry=registry)


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


def _is_mint_echo(err, validator: Draft202012Validator, frontmatter: dict) -> bool:
    """Whether *err* is the misleading echo of a failed mint contract.

    When the `$ref`'d mint schema fails (a bad `state`, a missing field), jsonschema
    counts none of its properties as evaluated, so the root `unevaluatedProperties`
    also reports `correlation_id`, `state`, … as unexpected — pointing at fields that
    are allowed, next to the real error. Drop that error unless the frontmatter has a
    key neither schema declares, in which case the report is genuine.
    """
    if err.validator != "unevaluatedProperties" or list(err.absolute_path):
        return False
    declared = set(validator.schema.get("properties", {}))
    declared |= set(_load_schema(MINT_SCHEMA_FILE).get("properties", {}))
    return set(frontmatter) <= declared


def errors_for(validator: Draft202012Validator, frontmatter: dict, source: str) -> list[str]:
    """Error strings for *frontmatter*, sorted by path; empty means it validated."""
    errors = sorted(
        validator.iter_errors(frontmatter), key=lambda e: list(e.absolute_path)
    )
    return [
        f"{source} at {'/'.join(str(p) for p in err.absolute_path) or '(root)'}: {err.message}"
        for err in errors
        if not _is_mint_echo(err, validator, frontmatter)
    ]


def validate(path: Path | str) -> list[str]:
    """Validate a feature file's YAML frontmatter against feature-frontmatter.schema.json.

    Returns a list of error strings; empty means the frontmatter validated.
    """
    path = Path(path)
    validator = load_validator()
    content = read_content_from_file(path)
    frontmatter = extract_frontmatter(content, str(path))
    return errors_for(validator, frontmatter, str(path))


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

    if args.file is not None:
        source = str(args.file)
        errors = validate(args.file)
    else:
        source = "<stdin>"
        content = read_content_from_stdin()
        validator = load_validator()
        frontmatter = extract_frontmatter(content, source)
        errors = errors_for(validator, frontmatter, source)

    if errors:
        for err in errors:
            sys.stderr.write(err + "\n")
        sys.stderr.write(
            f"\n{len(errors)} validation error(s) in frontmatter of {source}.\n"
        )
        return 1

    sys.stdout.write(f"ok: {source} frontmatter validated against feature-frontmatter.schema.json\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
