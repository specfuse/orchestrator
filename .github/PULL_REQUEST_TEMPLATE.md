<!--
Thanks for contributing to the Specfuse Orchestrator. Please fill in the sections below.
For commit conventions and the contribution flow, see CONTRIBUTING.md.
-->

## Summary

<!-- One paragraph describing the change. -->

## Why

<!-- Motivation or upstream-relevance. Reference issues, retrospective findings,
     or carry items if applicable. -->

## Type of change

- [ ] Bug fix
- [ ] New feature / capability
- [ ] Documentation
- [ ] Refactor / cleanup
- [ ] Phase 5+ scope (formal phase work)

## Checklist

- [ ] Change touches package/scaffolding paths (`agents/`, `shared/`, `scripts/`, `docs/`, `project/README.md`, `README.md`, `LICENSE`, `NOTICE`, `.github/`).
- [ ] No project-specific references in the diff or commit messages (no product feature names, private repo URLs, ticket IDs, customer references) — keep contributions project-agnostic.
- [ ] Validators pass on any schema or event-format changes:
  - `specfuse-validate-event --file events/<file>.jsonl`
  - `specfuse-validate-frontmatter --file features/<file>.md`
- [ ] Per-agent `version.md` bumped + changelog entry added if the change modifies a role's `CLAUDE.md`, skills, or rules. See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for commit conventions.
- [ ] Architecture-conflicting changes are escalated to the architecture document, not silently reconciled. (Per each agent's CLAUDE.md: "When this file and `orchestrator-architecture.md` disagree, **the architecture wins and this file is wrong**.")

## Notes for review

<!-- Anything reviewers should pay particular attention to. Surprising trade-offs,
     intentional deviations from existing patterns, deferred follow-ups, etc. -->
