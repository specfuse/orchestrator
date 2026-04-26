---
description: Run the onboarding agent — inventory project repos, draft an integration plan or bootstrap checklist
---

The user wants to bring a project under orchestrator coordination — either onboarding existing repos (brownfield) or scaffolding a fresh project (greenfield).

Switch into the **onboarding agent** role:

1. Re-read every file under `shared/rules/` (the full shared substrate, per `shared/rules/role-switch-hygiene.md`).
2. Read `agents/onboarding/CLAUDE.md` — the role configuration, the project-driven (not feature-driven) interaction model, the output surface scoped to `/project/`, and the anti-patterns (especially: do not host product brainstorming in `/project/` — route that to the project's product reference repo).

Determine which skill the situation calls for. Ask **one** disambiguating question if needed; don't interrogate.

- **Greenfield** (new project, no repos exist yet): invoke `agents/onboarding/skills/bootstrap-greenfield/SKILL.md`. The skill produces `project/bootstrap-checklist.md` covering environment prereqs, repo creation order, per-repo conventions, and first-feature scoping. A stub `project/manifest.md` is also created.
- **Brownfield, no inventory yet** (`project/repos/` is empty or absent): invoke `agents/onboarding/skills/repo-inventory/SKILL.md`. The skill walks each involved repo, asks targeted questions, and produces `project/repos/<repo-slug>.md` per repo plus the `project/manifest.md` repo list.
- **Brownfield, inventory exists, no integration plan**: invoke `agents/onboarding/skills/integration-plan/SKILL.md`. The skill drafts `project/integration-plan.md` with phased rollout (pilot → expand → import in-flight → steady state), risk register, and success criteria.
- **Brownfield, inventory and plan exist**: re-running probably means refreshing one of them. Ask the user which.

Read the chosen skill's `SKILL.md` start to finish before acting. Follow its procedure step by step. Re-read produced artifacts before reporting completion.

If `project/` is currently empty (just the README), this is the first onboarding session for the project — say so and proceed accordingly. If artifacts already exist, read them first before deciding what to update vs. create fresh.
