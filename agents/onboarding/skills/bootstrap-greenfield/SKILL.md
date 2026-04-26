# SKILL: bootstrap-greenfield — v0.1.0

For a greenfield project (one with no pre-existing code, specs, or in-flight features), draft a setup checklist at `/project/bootstrap-checklist.md`. The checklist guides the operator from "I have an idea for a new product" to "the orchestrator is wired and ready for feature 1."

This is a v0.1 working draft. Brownfield projects use [`integration-plan`](../integration-plan/SKILL.md) instead.

## When to invoke

- Once at the start of a new project, before any repos exist (or before more than the orchestration repo exists).
- The output is intentionally a one-time checklist; subsequent project changes are handled by `repo-inventory` (incremental) and, if needed, `integration-plan` (if the project grows brownfield characteristics).

## Inputs the agent reads

- The orchestration repo's `/agents/`, `/shared/`, `/scripts/` for current orchestrator capabilities.
- [`docs/operator-runbook.md`](../../../../docs/operator-runbook.md) and its prereqs section (this checklist's environment-setup phase mirrors those prereqs).
- [`docs/operator-pipeline-reference.md`](../../../../docs/operator-pipeline-reference.md) for the operational target state.
- Conversation with the human: product vision, anticipated repo set, team size, autonomy preferences.

## Procedure

### Step 1 — Conversation: project shape

Ask the human:

- **Product vision** — one paragraph: what is being built, who is the user, what's the value proposition. (For routing — *not* for capture in `/project/`. Product-discussion artifacts belong in the product reference repo, not the orchestration repo.)
- **Anticipated component repos** — at this stage, names and rough purposes; concrete repos may not exist yet. Examples: "API service", "web frontend", "background workers".
- **Team size and roles** — solo, small team, larger team — affects autonomy defaults and human-review cadence.
- **Autonomy preference for early features** — almost always `review` for greenfield; the recommendation is explicit.
- **Deadlines or milestones** — informs early-feature scoping guidance.

If the conversation drifts into product brainstorming (which is natural at greenfield), the agent acknowledges and routes: *"that's product-discussion content — once your product reference repo exists, capture it there. For now I'll only note it as 'product context' and move on with the bootstrap."*

### Step 2 — Draft the checklist

Produce `/project/bootstrap-checklist.md` with the structure below. The checklist is sequenced — each phase depends on the prior phase's completion.

The standard sequence:

1. **Environment prereqs** (operator's local machine).
2. **Orchestration repo creation** (template-clone the upstream Specfuse-orchestrator scaffolding).
3. **Product reference repo creation** with the `/product/` + `/business/` split.
4. **Component repo creation** — anticipated repos, in dependency order.
5. **Per-component-repo conventions** — `.specfuse/templates.yaml`, root `CLAUDE.md`, `_generated/` boundary, branch protection.
6. **First feature scoping** — pick a small, single-repo, low-risk feature to exercise the full pipeline before committing to the workflow.

### Step 3 — Initial project manifest

Create a stub `/project/manifest.md` with the human's project-level inputs (name, operator, autonomy default, target cadence, product reference repo location). The repo list is empty at this stage; `repo-inventory` will fill it in as repos are created.

### Step 4 — Verification

- Re-read the checklist after writing.
- Confirm every prereq matches the operator-runbook's prereqs section (no drift between docs).
- Confirm the repo-creation steps are sequenced (e.g., the product reference repo is created before component repos, since component repos may reference specs from it).
- Confirm the first-feature scoping guidance is concrete (a candidate feature is named, not just "pick something simple").

### Step 5 — Optional event emission

Append an `onboarding_artifact_produced` event to `/events/PROJ-<slug>.jsonl` for the bootstrap-checklist creation.

## Checklist template

```markdown
# Bootstrap checklist — <project name>

**Drafted:** <YYYY-MM-DD>
**Checklist version:** v0.1
**Type:** Greenfield

## Project context

- **Product vision:** <one paragraph from Step 1; this is for orienting the operator, not for capturing product-discussion artifacts>
- **Operator(s):** <names>
- **Team size:** <solo / small / larger>
- **Autonomy preference for early features:** review (recommended for greenfield)
- **Anticipated component repos:** <list with one-line purposes>

> Product brainstorming, business decisions, and feature ideation belong in the product reference repo (created in step 3 below), not in this checklist or anywhere under `/project/`. The orchestrator engages downstream of those discussions.

## Phase 1 — Environment prereqs (operator's local machine)

- [ ] Claude Code CLI installed and authenticated.
- [ ] Specfuse validator CLI installed and on `$PATH` (`specfuse --version` works).
- [ ] Python 3 + `pip install -r scripts/requirements.txt` succeeds in the orchestration repo.
- [ ] `gh` CLI authenticated against the org that will host the project's repos (`gh auth status`); confirm `repo` and `workflow` scopes.
- [ ] `$TMPDIR` is writable.

(Mirrors `docs/operator-runbook.md` §Prerequisites — keep aligned.)

## Phase 2 — Orchestration repo creation

- [ ] Template-clone the upstream Specfuse-orchestrator scaffolding to `<your-org>/<your-product>-orchestration` (or chosen name).
- [ ] Strip any upstream walkthrough artifacts (`docs/walkthroughs/`, prior `/features/`, `/events/`, `/inbox/` content) — keep `/agents/`, `/shared/`, `/scripts/`, `/docs/` (the operator runbook and pipeline reference).
- [ ] Verify the four operational agents and the onboarding agent are at expected versions: `scripts/read-agent-version.sh specs|pm|component|qa|onboarding`.
- [ ] First commit on your downstream repo's `main`: "chore: initial template clone from Specfuse-orchestrator vX.Y.Z".

## Phase 3 — Product reference repo creation

- [ ] Create `<your-org>/<your-product>-specs` (or chosen name) — this is the project's product reference repo.
- [ ] Initialize the top-level split:
  - `/product/` — specs, test plans, feature descriptions, agent-readable.
  - `/business/` — brand, marketing, support, sales — agent never-touch.
  - `/product/specs/` — placeholder for OpenAPI / AsyncAPI / Arazzo files.
  - `/product/features/` — placeholder for narrative feature descriptions.
  - `/product/test-plans/` — placeholder, populated by QA agent during qa_authoring.
- [ ] Add a root README explaining the split.
- [ ] (Recommended) Establish the convention that product brainstorming and design-discussion notes also live under `/product/` (e.g., `/product/discovery/`) — that is where the team's product habit funnels into the specs agent's feature-intake.
- [ ] Update the orchestration repo's `/project/manifest.md` with the product reference repo location.

## Phase 4 — Component repo creation

For each anticipated component repo, in dependency order (lower-level services before consumers):

- [ ] Create `<your-org>/<repo-name>`.
- [ ] Establish the `_generated/` (or equivalent) boundary in the repo's directory layout — generated code goes here; hand-written code goes elsewhere.
- [ ] Add `.specfuse/templates.yaml` declaring the templates this repo provides (initially empty or minimal; populated as the project's generator templates evolve).
- [ ] Add a root `CLAUDE.md` documenting repo-specific conventions: build/test/lint commands, framework idioms, package manager, PR conventions.
- [ ] Configure branch protection: required reviews, required status checks (CI must run on every PR — the merge watcher relies on these gates).
- [ ] (After first regenerated work) seed `/overrides/` registry per `shared/rules/override-registry.md`.

## Phase 5 — Per-component-repo onboarding (run `repo-inventory` after each creation)

- [ ] After each component repo is created, open an onboarding-agent session and run `repo-inventory` for that repo.
- [ ] The skill produces `/project/repos/<repo-slug>.md`; review and confirm.
- [ ] The manifest's repo list is updated; confirm.

## Phase 6 — First feature

- [ ] Open the product reference repo and capture the first feature idea under `/product/discovery/` (or wherever your team's habit lives).
- [ ] Pick a feature small enough to exercise the full pipeline in one or two operator sessions. Single repo, single endpoint or single component, low-risk. Candidate: <agent-suggested feature based on Step 1 conversation>.
- [ ] Open a specs-agent session at the orchestration repo per `docs/operator-runbook.md` and run feature-intake → spec-drafting → spec-validation.
- [ ] Hand off to the PM agent. Run end-to-end through the operator-pipeline-reference.
- [ ] On completion, retro: what worked, what didn't, what conventions to harden before feature 2.

## Success criteria

- [ ] All five repos (orchestration, product reference, component repos) exist and are correctly configured.
- [ ] First feature is delivered end-to-end through the orchestrator.
- [ ] Operator can describe the day-2 cadence (where product discussions happen, when feature-intake runs, how merge gates work) without re-reading docs.

## Notes / open questions

<things the human deferred during the bootstrap conversation — explicit list, not buried in prose>
```

## Worked example

For a new project "Acme Widget Tracker" with anticipated repos `acme-api`, `acme-web`, and `acme-specs`:

- Phase 1: operator confirms tooling.
- Phase 2: clones to `acme/widget-tracker-orchestration`. Strips upstream walkthrough artifacts.
- Phase 3: creates `acme/acme-specs`, sets up `/product/` + `/business/` split. Updates manifest.
- Phase 4: creates `acme/acme-api` first (lower-level), then `acme/acme-web` (consumer). Each gets `.specfuse/templates.yaml`, root `CLAUDE.md`, branch protection.
- Phase 5: runs `repo-inventory` for each component repo as it's created.
- Phase 6: first feature candidate "GET /widgets endpoint" — single repo, single endpoint, ideal pilot.

## Friction the v0.1 expects

- **Anticipated repos may differ from realized repos.** The human's plan in Phase 1 is provisional; component repos may merge or split during creation. The checklist accommodates this — re-run `repo-inventory` for actual repos as they materialize.
- **Greenfield discipline drift.** Without an existing project's friction to push against, teams often skip steps (e.g., branch protection "we'll add it later"). The checklist makes this explicit; the operator decides what's acceptable to defer.
- **Product reference repo conventions.** Greenfield is the right time to establish where product discussions live — but it's also when the team's habits aren't formed yet. The checklist recommends, doesn't force.

## Anti-patterns

- Capturing product-vision content in `/project/` artifacts instead of routing it to the product reference repo (anti-pattern #1 in the role config). The checklist's project-context section names the product vision but does not host the discussion of it.
- Sequencing component repos before the product reference repo (component repos reference specs that live in the product reference repo).
- Skipping the first-feature retrospective (Phase 6's last item) — it's the most valuable signal in the bootstrap.

## Where this v0.1 is likely to evolve

- Templates for component-repo scaffolding (a "fresh component repo" skeleton with `.specfuse/templates.yaml`, root `CLAUDE.md`, sample `_generated/` boundary, sample CI). Currently the human writes these by hand.
- Programmatic checks instead of human-judged checklist completion ("does the orchestration repo's `/agents/onboarding/version.md` exist?" → scriptable; "is branch protection configured correctly?" → scriptable).
- Multi-product orchestration repos — v0.1 assumes one product per orchestration repo.
