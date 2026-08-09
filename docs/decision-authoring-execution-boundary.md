# Decision — The authoring / execution boundary

**Status:** Accepted — formalizes existing RestoManager operating practice.
**Date:** 2026-07-04
**Scope:** Specfuse methodology plane split across the product-specs repo,
the orchestrator repo, and the `specfuse-authoring` / `specfuse-orchestrator`
plugins. Supersedes the implicit assumption (in `orchestrator-architecture.md`)
that the specs agent is an orchestrator-plane role.

> **Revision (2026-07-04):** an earlier draft of this note placed the plane seam
> at the **mint** and split the specs agent's skills across the two planes. That
> was wrong. The RestoManager layout (`restomanager-specs/.specfuse/agents/specs/`)
> holds the **entire** specs agent — all seven skills, `initiative-intake`
> included — on the authoring side. The seam is the **specs → pm handoff**
> (`validating → planning`); the mint is a *cross-seam write*, not the seam.

---

## Context

Two Specfuse plugins now exist alongside the core: `specfuse-authoring`
(spec-craft mechanics — `design-*`, `validate`, `bundle`, `preview`, handbooks)
and `specfuse-orchestrator` (the multi-agent execution engine — pm, component,
qa, merge, onboarding). That raised the question: which plane owns *turning a
product idea into a validated specification*? The `specs` agent does that work.

The answer is settled by how we already run RestoManager, not by a fresh design
choice. This note writes that practice down.

## Ground truth (RestoManager layout)

The specs agent and all seven of its skills physically live in the **product-specs
repo**:

```
restomanager-specs/.specfuse/agents/specs/CLAUDE.md          # role config
restomanager-specs/.specfuse/agents/specs/skills/            # all 7 SKILL.md
restomanager-specs/.claude/skills/                           # same 7, invocable
    ideation-capture  ideation-shape  backlog-groom          #   pre-mint
    initiative-intake  spec-drafting  spec-validation  spec-issue-triage
```

`specs` is the only agent under `.specfuse/agents/` in that repo. Everything from
raw idea to validated, planning-ready initiative runs there, from an interactive
session. The initiative **registry** it mints into lives in the **orchestration
repo** — the specs agent writes that entry across the seam as the handoff artifact.

## How we operate

1. **Ideas live in the product-specs repo**, as a thin index at
   `docs/product/INITIATIVE_BACKLOG.md` plus one dossier per idea under
   `docs/product/backlog/IDEA-NNN-<slug>.md`. All authoring happens here. Unit of
   work is the **idea**; managed as a backlog (capture, shape, groom). `IDEA-NNN`
   ids are transient, not correlation IDs — no initiative number yet.
2. **When an idea is picked for deployment, the specs agent mints an initiative
   number (`INIT-YYYY-NNNN`).** The mint (`initiative-intake` skill) runs *from
   the specs repo* and writes the registry entry *into the orchestration repo*.
   Minting promotes an idea into a tracked initiative; it is a cross-seam write,
   still authoring-plane work.
3. **The specs agent performs the detailed analysis, drafts and validates the
   specs** (OpenAPI / AsyncAPI / Arazzo under `/product/`), driving the initiative
   through `drafting → validating → planning`.
4. **At `planning`, work transfers to the execution engine.** The pm agent (in the
   orchestrator) decomposes the initiative into a feature graph, component agents
   build, qa tests, the merge watcher closes.

## Decision

**Two planes, divided at the specs → pm handoff (`validating → planning`).**

### Plane 1 — Product definition (authoring)
- **Home:** the product-specs repo (`restomanager-specs`), `product/specs/`.
- **Powered by:** the specs agent + the `specfuse-authoring` plugin + Specfuse
  handbooks.
- **Spans:** idea → validated, planning-ready initiative. Includes ideation
  *and* the mint *and* detailed spec definition/validation.
- **Owns skills:** ideation-capture, ideation-shape, backlog-groom,
  initiative-intake, spec-drafting, spec-validation, spec-issue-triage
  (all seven).

### Plane 2 — Execution engine (orchestrator)
- **Home:** the orchestrator repo (initiative registry, event log, inbox) plus
  the component repos it drives.
- **Powered by:** the `specfuse-orchestrator` plugin (pm, component, qa, merge,
  onboarding).
- **Spans:** `planning` → merged. Feature decomposition, implementation, QA,
  merge closure.

### The seam is the specs → pm handoff
`idea → drafting → validating → planning` is **all authoring**. At `planning`
the initiative transfers to pm. The **mint** happens *before* the seam, on the
authoring side, and reaches across to write the registry entry — it is not the
boundary.

## Where each responsibility lives

| Responsibility | Plane | Home |
| --- | --- | --- |
| Vision, product direction | Definition | specs repo |
| Ideation capture / shape / groom (idea backlog) | Definition | specs repo, `docs/product/INITIATIVE_BACKLOG.md` + `docs/product/backlog/` |
| Spec-craft mechanics (design endpoints/events/flows, validate, bundle, preview) | shared toolkit | `specfuse-authoring` plugin — used inside the definition plane's authoring |
| **Mint `INIT-YYYY-NNNN`** (initiative-intake) | Definition | specs agent; **writes the registry entry into the orchestration repo** |
| Detailed analysis, spec drafting, validation | Definition | specs agent; documents in specs-repo `/product/` |
| Spec-issue triage (feedback from downstream agents) | Definition | specs agent |
| Feature decomposition, dependency graph | Execution | pm agent |
| Implementation, PRs, override reconciliation | Execution | component agents |
| Test plans, execution, regression suite | Execution | qa agent |
| Merge closure | Execution | merge watcher |

## The initiative registry is shared substrate straddling the seam

The registry, event log, and correlation-ID scheme physically reside in the
**orchestration repo**, but the authoring-plane specs agent **writes into them**
at mint and on every `drafting → validating → planning` transition. So the
registry is not orchestrator-*exclusive*; it is the **shared coordination
substrate** both planes touch — authoring writes the initiative record and its
pre-`planning` lifecycle, execution owns everything from `planning` onward. This
is a data-artifact dependency (the specs agent appends to a git-tracked registry),
not a code dependency of authoring on the orchestrator.

## Consequences

### The specs agent is authoring-plane, whole and undivided
Do not split it at the mint. All seven skills — ideation, intake/mint, drafting,
validation, triage — belong together on the authoring side, exactly as the
RestoManager layout has them. They stay in the product-specs repo.

### The orchestrator plugin must NOT carry a `/specs` skill
specs is authoring-plane; its skills already live in the specs repo (and, for
distribution, belong with the authoring surface, not the orchestrator plugin).
Adding `/specs` to `specfuse-orchestrator` would duplicate the boundary in the
wrong plane. **Do not scaffold it there.** (The `agents/specs.md` currently
bundled in the orchestrator plugin is a flattened role *description* only — no
skills bundled — and is itself a candidate to move to the authoring plane.)

### Authoring is definition-plane surface, not merely a toolkit
Earlier framing called `specfuse-authoring` a plane-neutral toolkit used on both
sides of the seam. With the seam at `planning`, the spec-craft mechanics are
used **only** inside the definition plane (the specs agent's drafting/validation).
The execution plane consumes a finished spec; it does not author. `specfuse-authoring`
is therefore squarely a definition-plane dependency.

### Plugin-skill placement follows the seam
- `/onboard`, `/pm` — execution plane → **orchestrator plugin.** (Correctly
  placed; `/pm` was scaffolded this way.)
- `/specs` and the seven specs skills — definition plane → **specs repo / authoring
  surface.** Not the orchestrator plugin.
- `/component`, `/qa` execution — remain agents, no human-entry skill.

## Distribution home for the specs agent (decided)

The specs agent + its seven skills move to the **`specfuse-authoring` plugin**
(and the `specfuse/authoring` repo). They leave the `specfuse-orchestrator`
plugin entirely — `agents/specs.md` is removed from it. This puts the whole
definition plane on one distributable surface.

**Guard the dependency direction.** The specs agent writes orchestrator-resident
artifacts at mint (initiative registry, event log, correlation IDs) and follows
the `/shared/rules/` contract (correlation-ids, state-vocabulary, never-touch,
escalation-protocol, …). If that contract ships from the `specfuse-orchestrator`
plugin, moving specs into `specfuse-authoring` would make **authoring depend on
the orchestrator** — the wrong direction. To prevent that, the shared substrate
contract must ship from the **core `specfuse` plugin**, so both planes depend on
core and neither imports the other:

```
        specfuse (core)  ── correlation-ids, state-vocabulary, registry/event schema, never-touch
         ▲            ▲
         │            │
 specfuse-authoring   specfuse-orchestrator
 (specs: idea → planning)   (pm/component/qa/merge: planning → merged)
```

## Follow-ups (not done here)

1. Update `orchestrator-architecture.md`: describe specs as a definition-plane
   (authoring) role that hands the initiative to pm at `planning`, and mark the
   registry as shared substrate the specs agent writes into at mint.
2. **Move** the specs agent + its seven skills into the `specfuse-authoring`
   plugin / `specfuse/authoring` repo; **remove** `agents/specs.md` from the
   `specfuse-orchestrator` plugin. Source today:
   `restomanager-specs/.specfuse/agents/specs/`.
3. Ensure the shared substrate contract (`/shared/rules/*`, correlation-ID
   scheme, registry/event schema, state vocabulary) ships from the **core
   `specfuse` plugin** — a prerequisite for #2 so the move doesn't invert the
   dependency direction.
4. Document the mint as the formal deploy-decision moment (still authoring-side)
   and `planning` as the plane handoff in the vision doc.
