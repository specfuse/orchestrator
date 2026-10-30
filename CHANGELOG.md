# Changelog

Consumer-visible changes to this project, newest first.

<!--
How entries get here. Two collection points, because bugs have no close
ceremony:

  - a feature's close appends its "Consumer-visible contract changes"
    enumeration (close-discipline.md §3) to Unreleased, one entry per change;
  - `fix-bug` appends one line carrying the issue number before opening its PR.

Every entry carries a `FEAT-YYYY-NNNN` or `#<issue>` trace in trailing
parentheses, and sits under one of four class headings: Breaking, Added,
Changed, Fixed. An entry without a trace is a lint finding — a changelog line
nobody can trace back to the work that produced it is a line nobody can act on.

No backfill. This file starts empty on purpose. Reconstructing history from
commit subjects produces entries that read plausibly and describe the wrong
thing; the enumeration a close already wrote is the source, and work that
predates this file has none to lift.

Cutting a release stamps Unreleased with the version and freezes it. Appends
only ever go to Unreleased.
-->

## [Unreleased]

### Changed

- **Project-keyed feature IDs, `FEAT-<KEY>-YYYY-NNNN`, are accepted wherever an unkeyed `FEAT-YYYY-NNNN` is.** The `[FEAT-…]` issue-title lookups in `poller` and `qa_dispatcher`, the `Correlation ID:` and root parsing in `raise_spec_issue` and `reconcile_overrides`, every orchestrator-owned schema pattern (feature frontmatter `specs_authored_by`, overrides, test plans, `feature_created` and the `qa_*`, `test_plan_authored` and `regression_suite_curated` events), the QA skills' branch-name matchers and `correlation-ids.md` now use core's grammar (specfuse/specfuse#232), spelled once in `specfuse.orchestrator.ids`. Before, a keyed ID passed event-envelope validation but was then rejected by these schemas or skipped silently by the Python matchers. Every unkeyed ID stays valid; `INIT-` IDs take no key. A keyed feature cannot be minted yet: `feature-mint.schema.json` is core's and is widened there first. (#111)
