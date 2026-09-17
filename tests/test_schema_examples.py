"""Every file in shared/schemas/examples/ validates against its schema (#98).

An example is what a reader copies. `feature-frontmatter.json` went stale when
`next_step` became required for mid-lifecycle states (2026-06-08) and nothing
noticed, because no test read the examples as a set. This one does:

- an event example (it has `event_type` and `payload`) validates as an envelope
  against `event.schema.json`, and its payload against
  `events/<event_type>.schema.json`;
- any other example validates against the schema its file name names, looked up
  as `<stem>.schema.json`, then `events/<stem>.schema.json`.

An example with no schema to check it against fails rather than being skipped:
a new example that nothing validates is the same gap this closes.

Loads from shared/schemas/, not paths.substrate(...), which can be a stale build
artifact in a source checkout.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = REPO_ROOT / "shared" / "schemas"
EXAMPLES = sorted((SCHEMAS / "examples").glob("*.json"))


def _schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_for_stem(stem: str) -> Path | None:
    for candidate in (SCHEMAS / f"{stem}.schema.json",
                      SCHEMAS / "events" / f"{stem}.schema.json"):
        if candidate.is_file():
            return candidate
    return None


def _errors(schema_path: Path, instance) -> list[str]:
    validator = jsonschema.Draft202012Validator(_schema(schema_path))
    return [f"{schema_path.relative_to(SCHEMAS)}: {e.message} at "
            f"/{'/'.join(map(str, e.absolute_path))}"
            for e in validator.iter_errors(instance)]


def test_there_are_examples_to_check():
    # A glob that silently matches nothing would pass every test below forever.
    assert len(EXAMPLES) > 5


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.name)
def test_example_validates_against_its_schema(example: Path):
    doc = json.loads(example.read_text(encoding="utf-8"))
    if isinstance(doc, dict) and "event_type" in doc and "payload" in doc:
        payload_schema = SCHEMAS / "events" / f"{doc['event_type']}.schema.json"
        assert payload_schema.is_file(), (
            f"{example.name}: no payload schema for event_type {doc['event_type']!r}")
        errors = (_errors(SCHEMAS / "event.schema.json", doc)
                  + _errors(payload_schema, doc["payload"]))
    else:
        schema_path = _schema_for_stem(example.stem)
        assert schema_path is not None, (
            f"{example.name}: no schema named {example.stem}.schema.json to validate it")
        errors = _errors(schema_path, doc)
    assert errors == [], "\n".join(errors)
