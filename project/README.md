# Project

This directory holds the orchestration repo's **project-level coordination artifacts** — the things that describe the project as a whole rather than any individual feature. Produced and maintained by the [onboarding agent](../agents/onboarding/) (a meta-role); read by humans and other agents.

In a fresh template-clone of the orchestrator scaffolding, this directory contains only this README. The onboarding agent populates it during integration.

## What lives here

- **`manifest.md`** — top-level project metadata: name, primary operator(s), default autonomy, target cadence, list of involved repos with one-line summaries, link to the product reference repo. Created by the [`repo-inventory`](../agents/onboarding/skills/repo-inventory/SKILL.md) skill (or the [`bootstrap-greenfield`](../agents/onboarding/skills/bootstrap-greenfield/SKILL.md) skill at greenfield time).
- **`repos/<repo-slug>.md`** — one file per involved component repo, capturing purpose, tech surface, current state, spec coverage, orchestrator-readiness gaps, and onboarding actions. Maintained by [`repo-inventory`](../agents/onboarding/skills/repo-inventory/SKILL.md).
- **`integration-plan.md`** — brownfield only: phased adoption plan, risk register, success criteria. Created by [`integration-plan`](../agents/onboarding/skills/integration-plan/SKILL.md).
- **`bootstrap-checklist.md`** — greenfield only: setup checklist from "I have an idea" to "feature 1 ready to draft." Created by [`bootstrap-greenfield`](../agents/onboarding/skills/bootstrap-greenfield/SKILL.md).

## What does *not* live here

- **Product brainstorming, business decisions, feature ideation.** Those live in the project's **product reference repo** (the `/product/` subtree), upstream of orchestrator engagement. The orchestrator picks up at feature-intake when a discussed idea crystallizes into a feature; product discussion happens elsewhere.
- **Per-feature artifacts.** `/features/`, `/events/`, `/inbox/` hold those.
- **Agent configurations.** `/agents/` holds those.
- **Cross-cutting rules and schemas.** `/shared/` holds those.

## Reading order

If you've just cloned an orchestration repo and want to understand the project it manages:

1. Read `manifest.md` for the project overview.
2. Skim `repos/*.md` for the component-repo landscape.
3. If brownfield: read `integration-plan.md` for current rollout state.
4. If greenfield mid-bootstrap: read `bootstrap-checklist.md` for current setup state.
