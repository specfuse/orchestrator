"""Feature and initiative ID patterns — the one place the orchestrator spells them.

A feature ID is `FEAT-YYYY-NNNN`, or, when its repository sets a project key,
`FEAT-<KEY>-YYYY-NNNN` with `KEY` matching `[A-Z][A-Z0-9]{1,5}`
(core's `methodology/rules/correlation-ids.md`, specfuse/specfuse#232). An
initiative ID is `INIT-YYYY-NNNN` and takes no key. Unkeyed IDs stay valid.
"""

FEATURE_ID = r"FEAT-(?:[A-Z][A-Z0-9]{1,5}-)?\d{4}-\d{4}"
INITIATIVE_ID = r"INIT-\d{4}-\d{4}"
ROOT_ID = rf"(?:{FEATURE_ID}|{INITIATIVE_ID})"
