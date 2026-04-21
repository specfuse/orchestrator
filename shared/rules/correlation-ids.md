# Correlation IDs

Every unit of work in the orchestrator carries a correlation ID that threads it across repositories, agents, and events. This rule defines the format, the surfaces the ID must appear on, how the next ID is chosen, and what to do when you see — or are about to produce — a malformed one.

Architecture §3 is normative. This file is the pulled-in operational reference every role reads before emitting an ID.

## Format

Two shapes, and only two:

- **Feature-level:** `FEAT-YYYY-NNNN`
  - `YYYY` is the four-digit calendar year in which the feature was created.
  - `NNNN` is a zero-padded four-digit ordinal, unique within that year's feature registry.
  - Example: `FEAT-2026-0042`.
- **Task-level:** `FEAT-YYYY-NNNN/TNN`
  - The feature-level ID, a literal `/`, then `T` followed by a zero-padded two-digit task ordinal, unique within the feature.
  - Example: `FEAT-2026-0042/T07`.

The regex enforced by `shared/schemas/event.schema.json` for any correlation ID field is `^FEAT-\d{4}-\d{4}(/T\d{2})?$`. A string that does not match is malformed. Feature-frontmatter and override records use stricter patterns that pin the shape to feature-level or task-level specifically (see `shared/schemas/feature-frontmatter.schema.json` and `shared/schemas/override.schema.json`).

## Where correlation IDs must appear

For every feature, the ID appears in:

- The feature registry filename: `/features/FEAT-YYYY-NNNN.md`.
- The `correlation_id` field in that file's YAML frontmatter.
- The event log filename: `/events/FEAT-YYYY-NNNN.jsonl`.
- Every `correlation_id` field on every event appended to that log.

For every task, the ID appears in:

- The task's entry in the feature's `task_graph` (as the `id` sub-field `TNN`, combined with the feature ID to form the full task-level ID).
- The GitHub issue title in the assigned component repo. Conventional form: `[FEAT-YYYY-NNNN/TNN] <task summary>`.
- The branch name for the implementation PR. Conventional form: `feat/FEAT-YYYY-NNNN-TNN-<slug>` (the `/` is replaced with `-` for filesystem and git-ref safety; the ID is still reconstructible).
- Every commit on that branch carries a `Feature: FEAT-YYYY-NNNN/TNN` trailer in the commit message.
- The PR description includes the task-level correlation ID on its own line near the top.
- Every `correlation_id` field on events emitted about that task.

A single ID threads an entire work unit from spec to merge. If you are writing to a surface not listed above but that materially describes the work — for example, an escalation inbox file or an override record — include the correlation ID there too. When in doubt, err toward including it.

## Generating the next ID

**Feature-level.** The next ordinal for year `YYYY` is one greater than the largest `NNNN` that currently appears in `/features/FEAT-YYYY-*.md`. If no feature for `YYYY` exists yet, start at `0001`. Padding is always four digits: `0001`, `0042`, `1234`. Year rollover does not continue the previous year's counter — each year starts fresh at `0001`. The agent creating the feature registry entry is the one that picks the ID.

**Task-level.** The next ordinal within a feature is one greater than the largest `TNN` currently in that feature's `task_graph`. Tasks start at `T01`. Padding is always two digits, which caps a feature at `T99`; that ceiling has never been close to being hit and if it is, raise an escalation rather than inventing a new format. The PM agent is the only role that mints task-level IDs.

Do not reuse an ordinal even after a feature or task is abandoned. Once an ID has appeared in the event log, it is spent. Reusing it would make history ambiguous.

## Concrete examples

- A feature created in early 2026, 42nd of the year:
  - Registry file: `/features/FEAT-2026-0042.md`
  - Frontmatter: `correlation_id: FEAT-2026-0042`
  - Event log: `/events/FEAT-2026-0042.jsonl`
- The seventh task in that feature, living in the API repo:
  - Task-graph entry: `{ id: T07, type: implementation, depends_on: [T03], assigned_repo: acme/api }`
  - Issue title: `[FEAT-2026-0042/T07] Implement POST /orders validation`
  - Branch: `feat/FEAT-2026-0042-T07-orders-validation`
  - Commit trailer: `Feature: FEAT-2026-0042/T07`
  - Event entries carry `correlation_id: FEAT-2026-0042/T07`.

## Failure modes

A malformed ID is a correctness bug, not a cosmetic one. Downstream tools filter, join, and route on these IDs; a typo breaks the thread.

- **Schema-level rejection.** An event whose `correlation_id` fails the schema regex is invalid JSON Schema output. The validator rejects it; the event does not land in the log. Treat this as a stop condition — fix the ID, then retry. Do not edit the schema to admit the malformed value.
- **Cross-surface mismatch.** If an ID is well-formed on its own but disagrees with the feature or task it describes (for example, an issue titled `FEAT-2026-0042/T07` that references task `T08` in the body), the event log can no longer be threaded cleanly. Stop and raise an escalation with reason `spec_level_blocker` if the mismatch is in someone else's artifact; correct your own artifact immediately if it is yours.
- **Duplicate ordinal.** If you are about to mint an ID that already exists, you have read the registry stale. Re-read the current state of `/features/` or the feature's `task_graph` and pick the next unused ordinal. Never overwrite an existing feature file or task entry to claim its ID.
- **Year drift.** An ID whose `YYYY` does not match the year the feature was created is still valid syntactically but wrong semantically. The year in the ID is the year of creation, not the year of any subsequent work. Do not "refresh" the year when a feature crosses a calendar boundary.

When any of these is detected, the verify-before-report discipline (see `verify-before-report.md`) requires that you catch it before the event or artifact is reported complete. If you catch a malformed ID in an artifact already committed, raise an escalation rather than silently rewriting history.
