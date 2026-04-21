# Shared schemas

Machine-readable contracts that every agent reads from and writes to. The prose rules around these contracts (who emits what, when to escalate) live in `/shared/rules/` and the per-role `CLAUDE.md` files; this directory is the data contract only.

## Contents

- `event.schema.json` — one entry in a feature's JSONL event log (`/events/FEAT-YYYY-NNNN.jsonl`). Architecture §7.3.
- `feature-frontmatter.schema.json` — YAML frontmatter on each `/features/<id>.md`. Architecture §3 and §6.1.
- `override.schema.json` — one record under `/overrides/`. Architecture §9.3.
- `labels.md` — GitHub issue label taxonomy (state, type, autonomy). Not a JSON Schema: GitHub labels are not structured data the agents parse programmatically from a file, but they are a contract nonetheless.
- `examples/` — one valid instance of each JSON schema, used both as human reference and as regression fixtures for the validator.

## Versioning

Schemas are versioned with the orchestration repo itself. There is no independent version field on schema files — git history is the version history. A change to a schema is a commit like any other, and agents that consume it run against whatever the repo's current HEAD is.

Reasoning: the agents are tightly coupled to the orchestration repo they boot against; there is no publish/subscribe boundary that would justify independent schema versions. Adding one would create drift between the schema field and the git state with nothing useful bought in exchange.

If a schema change is breaking for historical data (e.g. renaming a required field), the migration is a separate commit that rewrites existing `/events/` and `/features/` files to match; events are append-only in normal operation but not immutable across schema migrations.

## Validation

Every `.schema.json` file is valid JSON Schema draft 2020-12. Validate with any draft-2020-12 capable tool, e.g.:

```sh
npx ajv-cli@5 compile --spec=draft2020 -s shared/schemas/event.schema.json
npx ajv-cli@5 validate --spec=draft2020 \
  -s shared/schemas/event.schema.json \
  -d shared/schemas/examples/event.json
```

Running the same validation pair for each schema/example under `examples/` is the minimum regression check before landing a schema change.
