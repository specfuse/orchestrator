# Umbrella `specfuse` package: `orchestrator` extra

Target repo: **`specfuse/specfuse`** (the `specfuse` umbrella package). This
edit is out of scope for this repo — the loop driver does not clone, edit, or
PR `specfuse/specfuse`. This file stages the exact edit for the operator to
apply there by hand, the same cross-repo pattern as
[`marketplace-publish-runbook.md`](marketplace-publish-runbook.md).

## Prerequisite

`specfuse-orchestrator` must already be published on PyPI (see
[`release-runbook.md`](release-runbook.md)) before this extra is added — the
extra installs it by name from PyPI, not from a path or git ref.

## The edit

In `specfuse/specfuse`'s `pyproject.toml`, add an `orchestrator` entry to
`[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
orchestrator = ["specfuse-orchestrator"]
```

If `[project.optional-dependencies]` already exists with other extras (e.g. a
`codegen` or `loop` extra for the suite's other components), add `orchestrator`
as an additional key in that same table rather than a second
`[project.optional-dependencies]` block — TOML does not merge duplicate table
headers.

## Result

Once merged and released from `specfuse/specfuse`, operators can install the
orchestrator component through the umbrella package:

```
pipx install specfuse[orchestrator]
```

which resolves to installing `specfuse-orchestrator` from PyPI as a
dependency.

## Confirmation flag

This file documents the *intended* edit based on the standard PEP 621
`[project.optional-dependencies]` shape. The exact current structure of
`specfuse/specfuse`'s `pyproject.toml` (e.g. whether it already has other
extras, or uses a different dependency-manager convention) has not been
confirmed against that repo. Before applying, the operator should open
`specfuse/specfuse`'s `pyproject.toml` and verify this shape still applies;
adjust the added key only (do not restructure existing extras) if the table
already exists in a different form.
