# Shared templates

Human-readable document shapes that ride on top of the machine contracts in `/shared/schemas/`. Every role produces or consumes these, so they live here rather than under `/agents/<role>/`.

## Contents

- `work-unit-issue.md` — body template for implementation and QA task issues in component repos. Enforces the five mandatory sections from orchestrator-architecture.md §8 (Context, Acceptance criteria, Do not touch, Verification, Escalation triggers) and the v1.0 frontmatter contract (correlation_id, task_type, autonomy, component_repo, depends_on, generated_surfaces). PM agent rejects issues that are missing any of them.
- `work-unit-issue.example.md` — fully-worked companion to the template above, using the fictional task `FEAT-2026-0042/T07` as a consistent example across the component agent's skills. Not a real task in this repo.
- `spec-issue.md` — body template for an issue raised against the product specs repo or the Specfuse generator project when a component or QA agent finds a spec-level problem. Filed instead of editing generated files.
- `qa-regression-issue.md` — body template for a QA regression issue filed against an implementation task when a QA-execution run fails. Regression count drives the first-failure-vs-repeat escalation rule in §6.4.
- `human-escalation.md` — content template for files dropped into `/inbox/human-escalation/` when an agent needs a human decision. Reason field is a closed enum so the polling loop can route without parsing free text.
- `feature-registry.md` — template for a feature file under `/features/<correlation_id>.md`. Frontmatter mirrors `shared/schemas/feature-frontmatter.schema.json`; the prose body captures intent the schema deliberately omits.

## Revision

This is the v0.1 revision of the shared templates. They will evolve as the agents exercise them; changes land as normal commits, version-stewarded alongside `/shared/` like everything else in this repo.
