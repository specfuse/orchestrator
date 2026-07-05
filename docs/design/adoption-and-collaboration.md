# Adoption & collaboration model (post-pip) — design proposal

Status: **proposal / for review** · Audience: broader OSS users with varied setups
(solo, small team, monorepo, multi-repo, mixed CI).

The pip migration decoupled the *tooling* (wheel + marketplace plugin) from the
*orchestration state*. The quickstart docs were translated into pip commands but
still describe the **fork-era shape**: "one dedicated orchestration git repo per
product, created up-front via `init` + `gh repo create` + push." That shape was
*forced* by the fork model (the upstream repo you cloned **was** your orchestration
repo). It is no longer forced — and for varied OSS adopters it's often wrong. This
doc re-decides the adoption unit, collaboration, topology, and versioning, and lets
the onboarding flow follow from those decisions rather than from inherited habit.

## Principle: the consumer holds *state*, the suite provides *tooling*

- **Tooling** (drivers, CLI, agents, frozen substrate) → the wheel + the
  `specfuse-orchestrator@specfuse` plugin. Versioned, upgraded via `pip install -U`.
- **State** (initiatives/features, events, project config, inbox, overrides) → the
  consumer's own files, wherever they choose to keep them.

The remaining coupling that violates this — the consumer still vendoring `agents/`
and `shared/` — is transitional, not designed (see §5). The target: **a consumer
holds only state.**

## 1. Adoption unit — three shapes, all first-class

Do not assume a dedicated repo. Support three topologies from one location-agnostic
`init <dir>`:

| Shape | Where state lives | Best for | Notes |
|---|---|---|---|
| **A. Dedicated repo** | its own `git` repo | multi-repo products, larger teams wanting clean separation + independent access control | today's only shape |
| **B. Subdirectory** | `orchestration/` (or `.orchestrator/`) inside an existing repo | monorepos, solo/small projects, "keep it near the code" | no second repo to manage |
| **C. Local-first** | a plain directory, `git`/GitHub deferred | evaluation, "just try it", offline | promote to A or B later |

**Recommendation: `init` becomes local-first and location-agnostic.** It scaffolds
the user-owned state dirs into `<dir>` and stops there — **no forced `git init`, no
`gh repo create`, no GitHub requirement.** If `<dir>` is already inside a git repo,
it does not re-init; if not, it leaves git as the user's choice. Publishing (own
repo vs commit-into-existing) and remote creation become explicit, optional, *later*
steps — with a one-liner for each shape in `NEXT_STEPS.md`. This directly answers
"no need to create a git repo to start."

## 2. Collaboration — plain-git-native, automation opt-in

Orchestration state is just tracked files, so collaboration = whatever the project
already does (branch + PR, or commit-to-main for solo). Nothing bespoke.

- **The `merge-watcher` CI is opt-in**, not part of adoption. It automates the
  `in_review → done` transition via a GitHub App/Action; a solo user or a GitLab
  user should never need it to get value. Document it as an optional add-on.
- **Human ↔ agent writes**: the CLI drivers + the plugin agents both operate on the
  state files. Keep the "one writer per fact" discipline the architecture already
  has; nothing about pip changes it. Document who writes what once, plainly.

## 3. Multi-repo topology — configured, not assumed

The orchestrator coordinates a project's *component repos*. Varied adopters split
differently:

- **Multi-repo** (e.g. separate backend/frontend/specs GitHub repos) — current
  assumption.
- **Monorepo** — the "repos" are packages/paths inside one repo.
- **Single repo** — one component, trivially.

**Recommendation:** the component topology is **project config captured at
onboarding** (`project/`), not a hardcoded assumption. `involved_repos` should
accept both `org/repo` (multi-repo) and in-repo path/package identifiers
(monorepo). The onboarding agent asks and records it; drivers read it. This is
mostly already true (drivers read `involved_repos` from initiative registries) —
make it explicit + monorepo-aware and stop implying separate GitHub repos in docs.

## 4. Versioning & upgrade — one suite line, a stated contract

Consumers now pin `specfuse-orchestrator`. Three version streams exist: the **pip
package**, the **marketplace plugin**, and (today) **vendored `agents/`**.

**Recommendation:**
- Package + plugin release **together on one suite version line**; the plugin's
  `plugin.json` version tracks the package. Document "package X ⇒ plugin X".
- `specfuse-orchestrator upgrade <dir>` is the single upgrade action: re-provisions
  substrate from the newly-installed wheel and re-asserts the plugin config. State
  is never touched.
- Publish a short **compat contract**: what a state repo scaffolded at version X
  needs, and the deprecation policy for state-file shapes (the INIT-schema reframe
  is the model — additive, old files still validate).
- Eliminating the vendored `agents/` stream (§5) collapses three streams to two.

## 5. Enabling change: move `agents/` + substrate fully into the tooling

The one thing forcing a consumer to still vendor files:

- Drivers read `<state_repo>/agents/<role>/version.md` at runtime (event
  `source_version`) → forces vendored `agents/`.
- Agent `CLAUDE.md` files `@-include` `shared/rules/` → forces vendored `shared/`
  (though `upgrade` keeps it in sync).

**Recommendation (package-side follow-up):** have the drivers resolve agent
versions from the installed package/plugin (like they resolve substrate via
`paths.substrate()`), and let the plugin be the sole home of the agent role prompts.
Then a consumer holds **only state** — no vendored `agents/`, no vendored `shared/`,
zero drift, and the "what do I keep vs delete" migration question disappears. This
is the clean end-state the pip model was for; the current vendoring is a bridge.

## 6. Revised onboarding shape (follows from the above)

Rewrite `GETTING_STARTED` around the decision, not the command sequence:

1. `pip install specfuse-orchestrator` (or `pipx install specfuse[orchestrator]`).
2. `/plugin install specfuse-orchestrator@specfuse` in Claude Code.
3. **Pick where state lives** — dedicated repo / a subdir of your repo / just a
   local folder — and `specfuse-orchestrator init <that path>`. No git or GitHub
   required yet.
4. `/onboard` — the agent captures your repo topology (mono/multi/single) and
   product layout.
5. *Optional, when ready:* put the state under version control / its own repo /
   wire `merge-watcher` CI. Each is a documented one-liner, not a precondition.

Same five minutes, but the shape is the adopter's choice and the git/GitHub step is
deferred — matching how varied OSS users actually start.

## Decisions

1. **✅ ACCEPTED (2026-07-04).** `init` → local-first + location-agnostic: drop the
   forced `git init` / `gh repo create`; git & GitHub become deferred, optional steps.
2. Support all three adoption shapes as first-class, documented paths. **(recommend yes)**
3. **✅ ACCEPTED (2026-07-04).** Commit to the §5 end-state — a consumer holds *only*
   state; the agent role prompts + version markers and the frozen substrate move fully
   into the wheel/plugin, so the drivers stop reading vendored `agents/`/`shared/`. This
   is the payoff and it retires the "what do I vendor vs delete" migration question.
4. One suite version line + a written compat contract. **(recommend yes)**

Decisions 1 & 3 are accepted; 2 & 4 recommended, pending. The work splits cleanly:
a fast doc rewrite (follows §6) + two bounded package features — **(a)** `init`
local-first, and **(b)** drivers resolve agent versions from the installed package
(the enabling change for §5). Each should be its own loop feature in this repo.
