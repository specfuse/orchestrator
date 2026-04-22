# PM agent version

Current version: **1.0.0**

## Changelog

- `1.0.0` — WU 2.1: PM agent configuration rewritten to production v1 quality. `CLAUDE.md` restructured around the five Phase 2 skills (task decomposition, plan review, issue drafting, dependency recomputation, template coverage), with role-specific verification clauses pointing to each skill, an anti-patterns section codifying the PM-side failure modes from Phase 1 walkthroughs, explicit output-artifact definitions, and a preserved "Phase 2 specification inputs" list for any additional inherited specs that later Phase 2 WUs may append. Finding 6 of the Phase 1 walkthrough retrospective (shared-rules re-read discipline at role-switch) absorbed into the new shared rule `shared/rules/role-switch-hygiene.md` rather than duplicated per-role, so every operational role (component, QA, specs, future meta-agents) inherits the discipline without drift. The shared edit is authorized against the Phase 1 freeze by the retrospective's explicit carve-out for Finding 6. `agents/pm/README.md` added for cold-open navigation. `agents/pm/rules/` remains empty by design; no role-specific overrides are needed at v1. Closes WU 2.1 of Phase 2.
- `0.2.0` — WU 1.9: added forward specification `issue-drafting-spec.md` as an inherited contract for the Phase 2 WU that will author the issue-drafting skill. The skill must re-verify every claim about target-repo state at drafting time and capture the verification in a durable surface. Added pointer from `CLAUDE.md` under new "Phase 2 specification inputs" section. Closes Finding 3 of the Phase 1 walkthrough retrospective — the last Fix-in-Phase-1 before freeze.
- `0.1.0` — Initial Phase 0 draft.
