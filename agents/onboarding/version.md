# Onboarding agent version

Current version: **0.1.0**

**Phase 4.5 interlude — pre-real-project draft.** Skills are v0.1 working drafts intended to be exercised against a real project (greenfield or brownfield) and hardened based on what surfaces. Not frozen; expect changes.

## Changelog

### 0.1.0 — 2026-04-26 (Phase 4.5 WU)

Initial draft of the onboarding agent — a meta-role that operates project-wide rather than per-feature, runs once at integration time and rarely thereafter. Adds three skills:

- `repo-inventory` — inventories the project's repos, produces per-repo readiness assessments under `/project/repos/`.
- `integration-plan` — for brownfield projects, drafts a phased transition plan at `/project/integration-plan.md`.
- `bootstrap-greenfield` — for new projects, drafts a setup checklist at `/project/bootstrap-checklist.md`.

Companion to the upcoming Phase 5 config-steward meta-role; both operate on the orchestration repo's own workspace rather than per-feature.
