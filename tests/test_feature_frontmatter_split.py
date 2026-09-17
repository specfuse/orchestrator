"""The feature-frontmatter split (#87 item 2, specfuse/specfuse#179).

The mint contract (`correlation_id`, `state`, `involved_repos`, `autonomy_default`)
is core-owned: `shared/schemas/feature-mint.schema.json` is a byte-identical
vendored copy of core's `methodology/schemas/feature-mint.schema.json`, and core's
drift test fails if they differ. `feature-frontmatter.schema.json` composes it by
`$ref` and declares only the planning fields.

What this file pins, on the orchestrator side of the seam:

- the composition itself: the `$ref` names the vendored schema's `$id`, and the
  extension neither restates the mint fields (core's
  `test_feature_mint_schema.py` fails the nightly run if it does) nor closes the
  object with `additionalProperties`, which cannot see through a `$ref`;
- resolution is local: `validate_frontmatter` resolves the `$ref` from this
  package's substrate, and a missing mint schema is a setup error, not a pass;
- reporting stays honest: a failed mint contract does not also produce an
  `unevaluatedProperties` error blaming the allowed fields, while a genuinely
  unknown key is still reported.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specfuse.orchestrator import paths, validate_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = REPO_ROOT / "shared" / "schemas"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
MINT_ID = "https://specfuse.dev/methodology/schemas/feature-mint.schema.json"
MINT_FIELDS = {"correlation_id", "state", "involved_repos", "autonomy_default"}


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


VALID = {
    "correlation_id": "FEAT-2026-0099", "state": "drafting",
    "involved_repos": ["specfuse/api"], "autonomy_default": "review",
    "task_graph": [],
}


def _errors(doc: dict) -> list[str]:
    return validate_frontmatter.errors_for(
        validate_frontmatter.load_validator(), doc, "doc")


# ---- the composition --------------------------------------------------------


def test_extension_refs_the_vendored_mint_schema_by_id():
    mint = _load("feature-mint.schema.json")
    extension = _load("feature-frontmatter.schema.json")
    assert mint["$id"] == MINT_ID
    assert {"$ref": MINT_ID} in extension["allOf"]


def test_mint_schema_owns_exactly_the_four_fields():
    mint = _load("feature-mint.schema.json")
    assert set(mint["required"]) == MINT_FIELDS
    assert set(mint["properties"]) == MINT_FIELDS
    assert "additionalProperties" not in mint


def test_extension_does_not_restate_the_mint_fields():
    extension = _load("feature-frontmatter.schema.json")
    assert not MINT_FIELDS & set(extension["properties"])
    assert not MINT_FIELDS & set(extension.get("required", []))


def test_extension_closes_the_object_in_a_way_that_sees_through_the_ref():
    extension = _load("feature-frontmatter.schema.json")
    assert extension["unevaluatedProperties"] is False
    assert "additionalProperties" not in extension


# ---- resolution -------------------------------------------------------------


def test_the_substrate_carries_the_mint_schema(substrate_ready):
    assert paths.substrate("schemas", "feature-mint.schema.json").is_file()


def test_a_missing_mint_schema_is_a_setup_error(monkeypatch):
    real = paths.substrate

    def without_mint(*parts):
        if parts[-1] == "feature-mint.schema.json":
            return Path("/nonexistent/feature-mint.schema.json")
        return real(*parts)

    monkeypatch.setattr(validate_frontmatter.paths, "substrate", without_mint)
    with pytest.raises(SystemExit) as exc:
        validate_frontmatter.load_validator()
    assert exc.value.code == 2


# ---- behaviour through the composition --------------------------------------


def test_a_valid_entry_validates():
    assert _errors(VALID) == []


def test_each_mint_constraint_still_rejects():
    cases = {
        "sub-unit correlation id": {**VALID, "correlation_id": "FEAT-2026-0099/T01"},
        "unknown state": {**VALID, "state": "paused"},
        "empty repos": {**VALID, "involved_repos": []},
        "unknown autonomy": {**VALID, "autonomy_default": "manual"},
    }
    for field in MINT_FIELDS:
        cases[f"missing {field}"] = {k: v for k, v in VALID.items() if k != field}
    for name, doc in cases.items():
        assert _errors(doc), name


def test_planning_rules_still_apply():
    no_graph = {k: v for k, v in VALID.items() if k != "task_graph"}
    assert _errors(no_graph)
    in_progress_without_next_step = {**VALID, "state": "in_progress"}
    assert any("next_step" in e for e in _errors(in_progress_without_next_step))


def test_invalid_fixture_reports_its_two_real_errors_and_no_echo():
    errors = validate_frontmatter.validate(FIXTURES / "invalid_frontmatter.md")
    assert len(errors) == 2, errors
    assert any("'autonomy_default' is a required property" in e for e in errors)
    assert any("'not-a-real-state' is not one of" in e for e in errors)
    assert not any("Unevaluated properties" in e for e in errors)


def test_an_unknown_key_is_reported_when_the_mint_fields_are_valid():
    errors = _errors({**VALID, "typo_key": 1})
    assert any("Unevaluated properties" in e and "typo_key" in e for e in errors)


def test_an_unknown_key_is_still_reported_when_the_mint_fields_are_not():
    errors = _errors({**VALID, "state": "paused", "typo_key": 1})
    assert any("typo_key" in e for e in errors)
    assert any("'paused' is not one of" in e for e in errors)
