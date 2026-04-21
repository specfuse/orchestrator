# Component agent version

Current version: **1.1.0**

## Changelog

- `1.1.0` — WU 1.2: added `skills/verification/SKILL.md` v1 as the normative verification skill for the role. Defines the six mandatory gates (tests, coverage ≥ 90%, compiler-warnings, lint, security-scan, build) aligned with architecture §10, the `.specfuse/verification.yml` repo contract, the per-gate and `task_completed` payload shapes, and the failure-handling flow (local correction, spinning detection, spec-level escalation). Replaced the 1.0.0 verification placeholder in `CLAUDE.md` with a pointer to the skill.
- `1.0.0` — Phase 1 v1 baseline. Rewrite from v0.1 Phase 0 draft: tightened role definition with explicit non-responsibilities; enumerated entry transitions owned with ownership rationale; expanded output artifact list to name the exact events the role emits; added explicit anti-patterns section covering the ten failure modes that regress the orchestrator's trust model; added role-specific skill placeholders pointing at `skills/verification/SKILL.md` (WU 1.2) and `skills/pr-submission/SKILL.md` + `skills/escalation/SKILL.md` (WU 1.3); declared `/agents/component/rules/` intentionally empty at v1.0.0 with the override procedure documented. Added `README.md` for directory cold-open.
- `0.1.0` — Initial Phase 0 draft.
