---
correlation_id: FEAT-YYYY-NNNN
state: drafting
involved_repos:
  - <owner/repo>
autonomy_default: review
task_graph: []
# Task graph entries are added by the PM agent during planning. Shape of each:
#   - id: T01                    # ^T\d{2}$, unique within this feature
#     type: implementation       # implementation | qa_authoring | qa_execution | qa_curation
#     depends_on: []             # task-local IDs within this feature
#     assigned_repo: <owner/repo>
---

<!--
Feature registry template. v0.1.

One file per feature under `/features/<correlation_id>.md`. The YAML
frontmatter above is the machine-readable contract validated against
`shared/schemas/feature-frontmatter.schema.json` — fields and shapes are
governed there, not here. The prose below is for humans: it captures intent
the schema intentionally does not carry.

Fill in every placeholder and delete these HTML comments before committing.
Keep the frontmatter first in the file; tooling reads YAML from the leading
fence.
-->

## Description

<!-- One or two paragraphs stating what this feature is and why it exists.
Written in product language, not task-graph language. The reader should
understand the user-facing value after this section. -->

<description>

## Scope

<!-- A bulleted list of the capabilities this feature delivers. Each bullet
should map to at least one task in the graph above. -->

- <capability>
- <capability>

## Out of scope

<!-- A bulleted list of adjacent concerns this feature explicitly does not
cover. This is the place to fence off work that belongs to a future feature
or to a different part of the product. -->

- <exclusion>
- <exclusion>

## Related specs

<!-- Links into the product specs repo for the specifications this feature
is driven by: OpenAPI/AsyncAPI/Arazzo documents, test plans under
`/product/test-plans/`, feature descriptions under `/product/`. Use repo-
relative paths. -->

- <product/path/to/spec.yaml>
- <product/test-plans/path.md>
