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

EVENTS_DIR = REPO_ROOT / "shared" / "schemas" / "events"
EXAMPLES_DIR = REPO_ROOT / "shared" / "schemas" / "examples"
COMPLETED_SCHEMA_PATH = EVENTS_DIR / "qa_execution_completed.schema.json"
FAILED_SCHEMA_PATH = EVENTS_DIR / "qa_execution_failed.schema.json"
COMPLETED_EXAMPLE_PATH = EXAMPLES_DIR / "qa_execution_completed.json"
FAILED_EXAMPLE_PATH = EXAMPLES_DIR / "qa_execution_failed.json"
COMPLETED_MANIFEST_EXAMPLE_PATH = EXAMPLES_DIR / "qa_execution_completed_manifest.json"


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


def _event_validator(schema_path):
    schema = json.loads(schema_path.read_text())
    return jsonschema.Draft202012Validator(schema)


def test_event_stack_manifest_validates():
    validator = _event_validator(COMPLETED_SCHEMA_PATH)
    event = json.loads(COMPLETED_MANIFEST_EXAMPLE_PATH.read_text())
    payload = event["payload"]
    assert "commit_sha" not in payload
    validator.validate(payload)


def test_event_commit_sha_only_still_valid():
    completed_validator = _event_validator(COMPLETED_SCHEMA_PATH)
    completed_event = json.loads(COMPLETED_EXAMPLE_PATH.read_text())
    completed_validator.validate(completed_event["payload"])

    failed_validator = _event_validator(FAILED_SCHEMA_PATH)
    failed_event = json.loads(FAILED_EXAMPLE_PATH.read_text())
    failed_validator.validate(failed_event["payload"])


def test_event_neither_key_rejected():
    completed_validator = _event_validator(COMPLETED_SCHEMA_PATH)
    completed_payload = copy.deepcopy(
        json.loads(COMPLETED_EXAMPLE_PATH.read_text())["payload"]
    )
    del completed_payload["commit_sha"]
    with pytest.raises(jsonschema.ValidationError):
        completed_validator.validate(completed_payload)

    failed_validator = _event_validator(FAILED_SCHEMA_PATH)
    failed_payload = copy.deepcopy(
        json.loads(FAILED_EXAMPLE_PATH.read_text())["payload"]
    )
    del failed_payload["commit_sha"]
    with pytest.raises(jsonschema.ValidationError):
        failed_validator.validate(failed_payload)


def test_event_short_sha_rejected():
    completed_validator = _event_validator(COMPLETED_SCHEMA_PATH)
    completed_payload = copy.deepcopy(
        json.loads(COMPLETED_EXAMPLE_PATH.read_text())["payload"]
    )
    completed_payload["commit_sha"] = "abc123"
    with pytest.raises(jsonschema.ValidationError):
        completed_validator.validate(completed_payload)

    failed_validator = _event_validator(FAILED_SCHEMA_PATH)
    failed_payload = copy.deepcopy(
        json.loads(FAILED_EXAMPLE_PATH.read_text())["payload"]
    )
    failed_payload["commit_sha"] = "abc123"
    with pytest.raises(jsonschema.ValidationError):
        failed_validator.validate(failed_payload)
