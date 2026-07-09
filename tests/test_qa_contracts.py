"""Contract tests for shared/schemas/test-plan.schema.json (FEAT-2026-0003/T01).

Loads the schema directly from shared/schemas/, not paths.substrate(...), which
can be a stale build artifact in a source checkout.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "test-plan.schema.json"
EXAMPLE_PATH = REPO_ROOT / "shared" / "schemas" / "examples" / "test-plan.json"


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text())
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture
def example_plan():
    return json.loads(EXAMPLE_PATH.read_text())


def test_plan_tier_components_validate(validator, example_plan):
    plan = copy.deepcopy(example_plan)
    plan["tests"][0]["tier"] = "journey"
    plan["tests"][0]["components"] = ["api", "web"]
    validator.validate(plan)


def test_plan_existing_example_still_valid(validator, example_plan):
    validator.validate(example_plan)


def test_plan_bad_tier_rejected(validator, example_plan):
    plan = copy.deepcopy(example_plan)
    plan["tests"][0]["tier"] = "e2e"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(plan)
