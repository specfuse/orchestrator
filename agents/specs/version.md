# Specs agent version

Current version: **1.0.2**

## Changelog

- `1.0.2` — OSS publication scrub. Replaced `Bontyyy/orchestrator-api-sample` and related personal-handle references in `skills/feature-intake/SKILL.md` worked examples with generic `acme/api-sample` placeholders so the upstream's normative documentation does not advertise the orchestrator's development fixture repos as canonical patterns. Doc-only change: no procedural step body, contract, or schema is modified. Phase 4 freeze contract preserved. Patch-level bump.
- `1.0.1` — Post-retrospective fix ladder (WU 4.8). Spec-validation SKILL.md trigger values standardized to match CLAUDE.md (`validation_requested`, `validation_passed`). Spec-drafting SKILL.md: `## Related specs` path format guidance added (repo-relative paths as primary reference); `## Delivery convention` section added (spec files must be committed to specs repo after human approval).
- `1.0.0` — Production v1 configuration (WU 4.1). Session-driven interaction model documented; four Phase 4 skills referenced (feature-intake, spec-drafting, spec-validation, spec-issue-triage); multi-repo output surfaces with write boundaries; entry transitions, verification, escalation, and anti-patterns aligned with the Phase 1–3 downstream agent pattern; role-switch hygiene inherited.
- `0.1.0` — Initial Phase 0 draft.
