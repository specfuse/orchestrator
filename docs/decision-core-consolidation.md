# Decision — What consolidates into the core `specfuse` plugin/repo

**Status:** Proposed — cross-repo audit complete (loop, orchestrator, authoring).
**Date:** 2026-07-04
**Companion to:** `decision-authoring-execution-boundary.md`. That note put the
specs agent on the authoring side and named "shared substrate in core" as a
prerequisite. This note says concretely *what* moves to core.

---

## Why

Three sibling repos — `loop` (gate-cycle execution), `authoring` (spec
definition), `orchestrator` (multi-repo execution) — each carry overlapping
methodology substrate. The audit found:

1. **Triple-duplicated dev-binding rules.** `.specfuse/rules/` (four files:
   `correlation-ids`, `never-touch`, `result-contract`, `security-boundaries`)
   exists in **all three** repos and is **effectively byte-identical**
   (loop = orchestrator exactly; authoring differs only by trailing whitespace).
   Every repo self-hosts on the gate-cycle to build itself, so each vendored the
   same four rules. No real drift yet — but three copies guarantee eventual drift.
2. **A hard cross-repo path dependency.** loop's `validate_event.py` reads
   `orchestrator/shared/schemas/event.schema.json` directly. The event envelope
   is already shared in practice, via a fragile filesystem path.
3. **Two things both named "rules".** `.specfuse/rules/` (the four gate-cycle
   dev-binding rules, above) is a *different set* from the orchestrator's
   `shared/rules/` (eight files it *ships to its downstream agents*). They
   overlap on four names. The overlap is the core.
4. **loop's `correlation-ids.md` is the superset** — it defines both the `FEAT-`
   (component-local) and `INIT-` (orchestrated) namespaces with the full regex.
   It is the canonical version; the orchestrator's feature-only framing is behind.
5. **Authoring's own substrate is orthogonal** — handbooks, Spectral rulesets,
   Arazzo `x-*` extensions, project templates. Spec-craft mechanics. **Not** core
   candidates; they stay in authoring.

## The layering

```
                         specfuse (CORE)
   correlation-ids · never-touch · security-boundaries · result-contract
   verify-before-report · role-switch-hygiene · escalation-protocol
   base lifecycle vocabulary · event envelope schema · methodology.md
        ▲                      ▲                        ▲
        │                      │                        │
   loop                   authoring                orchestrator
   (gate-cycle,           (definition plane:       (execution engine:
    single-repo)           specs agent + 7          pm/component/qa/merge)
                           spec skills)
   + PLAN/GATE/WU        + handbooks, Spectral,    + override-registry
     templates             Arazzo x-*, spec          + task/feature state
   + gate_eval            -craft skills               machine + event payloads
     predicate                                       + work-unit/label templates
   + attempt_outcome                                 + template-coverage schema
```

Everything depends on core; **no sibling imports another sibling.** That kills
both the triple-duplication and the loop→orchestrator path dependency.

## What moves to CORE

Single source of truth, consumed (vendored at scaffold/upgrade) by all three:

| Item | Today's home(s) | Note |
| --- | --- | --- |
| `correlation-ids.md` | `.specfuse/rules/` ×3 | Adopt **loop's superset** (FEAT + INIT). Retire the orchestrator `shared/rules/` feature-only copy. |
| `never-touch.md` | `.specfuse/rules/` ×3 + orch `shared/rules/` | One copy. |
| `security-boundaries.md` | `.specfuse/rules/` ×3 + orch `shared/rules/` | One copy. |
| `result-contract.md` | `.specfuse/rules/` ×3 | The agent→driver contract; same shape as the orchestrator's `task_completed`. |
| `verify-before-report.md` | orch `shared/rules/` | Methodology-wide; every agent verifies before reporting. |
| `role-switch-hygiene.md` | orch `shared/rules/` | Re-read rules on every task/role switch — universal. |
| `escalation-protocol.md` | orch `shared/rules/` | Every plane escalates (loop `blocked_human`, specs, pm). Core with a shared reason enum; planes may extend. |
| Base lifecycle vocabulary | orch `shared/rules/state-vocabulary.md` + loop `methodology.md` | The shared `drafting → validating → planning → … → done` spine. See split note below. |
| `event.schema.json` (envelope) | orch `shared/schemas/` | Already cross-consumed by loop. |
| `methodology.md` (gate-cycle canonical) | `loop/docs/` | The methodology definition itself — belongs to core, not to one execution surface. |

## What STAYS put

**Orchestrator (execution plane only):**
- `override-registry.md`, `override.schema.json` — overrides are a codegen /
  component-repo concept, meaningless to loop and authoring.
- `template-coverage.schema.json`, `labels.md` (GitHub taxonomy).
- The **task/feature state machine** portion of `state-vocabulary.md`
  (`pending → ready → in_progress → …`) and the execution event payload schemas
  (`task_*`, `qa_*`, `feature_graph_drafted`, `plan_*`, …).
- Work-unit-issue / feature-registry / human-escalation templates.

**Authoring (definition plane only):**
- Handbooks, Spectral rulesets, Arazzo `x-*` extensions, project templates,
  the Python authoring CLI.
- **The specs agent + its 7 skills** (arriving per the companion note).
- Authoring's own definition event payloads (`initiative_created`,
  `spec_validated`, `spec_issue_*`) — or these move to core if pm consumes them.
  Decide per-consumer (see open questions).

**Loop (gate-cycle single-repo surface):**
- `gate_eval.py` auto-close predicate, `PLAN/GATE/WU` templates,
  `verification.yml`, `attempt_outcome` schema, WU/gate status constants,
  the gate-cycle skills.

## The one genuine split: state vocabulary

`state-vocabulary.md` is not cleanly one-plane. It holds:
- **Initiative/feature lifecycle** `drafting → validating → planning → … → done`
  — the shared spine both planes reference (specs owns `drafting→planning`, pm
  owns onward). → **core.**
- **Task state machine** `pending → ready → in_progress → in_review → done` and
  its per-role ownership — pure execution. → **orchestrator.**

Split the file at the seam: core owns the lifecycle spine, orchestrator owns the
task machine and layers it under the spine.

## Distribution is vendoring, not a plugin — so "core" is a repo, not a new plugin

The shared substrate does **not** travel through the plugin marketplace. Rules
and schemas are distributed by **vendoring**: `init.sh` / `specfuse upgrade`
copies them from package data into each repo's `.specfuse/`, exactly as loop
already does (`specfuse/loop/data/rules|templates|docs`). Claude Code plugins
ship *skills / agents / hooks / commands* — a plugin whose only payload is
markdown rules + JSON schemas, with no skills, is an anti-pattern. So the
consolidation question is **not** "which plugin owns the substrate" but "**which
repo is the single source of truth**" for the vendored files.

**Decision: the existing `specfuse` (gate-cycle) repo is that source. No new
plugin.** It already holds `methodology.md` + the four `.specfuse/rules/` and is
the surface every repo self-hosts on; it *is* the methodology core. Loop,
authoring, and orchestrator vendor the CORE set from it. The `specfuse` **plugin**
is unchanged — it keeps shipping only the gate-cycle skills.

**Keep it namespaced within that repo.** The gate-cycle surface is single-repo
execution-flavored; put the shared substrate in its own subtree (e.g.
`substrate/` or `methodology/`) rather than tangling it into the loop's gate
mechanics. One source of truth, no second plugin, gate-cycle skills stay clean.

Each repo continues to copy its vendored substrate into its Python package data
dir (`specfuse/orchestrator/_substrate/`, etc.) for packaging — that mechanism
stays; only the **source** consolidates. Core is authored once; siblings vendor,
never fork.

## Substrate cross-links must be layout-stable (learned in Gate 2)

Core substrate files reference each other. When vendored into a consumer whose
directory layout differs from core's, relative-path markdown links break. Rules:

- **Inter-file links to targets *inside* the same vendored set** (e.g. one rule
  linking another rule in `rules/`) are fine — **provided the vendored subset is
  link-closed** (everything a vendored file links to is also vendored). The
  binding constraint is *link-closure, not completeness*: a consumer may
  surface-opt-out of a rule whose subject it does not have, **as long as nothing
  in its vendored set links to that rule.** (Gate 2: the loop vendored 4 of 5,
  hitting a dangling link to `verification-discipline.md` → added it, reaching 5.
  It then deliberately skipped `role-switch-hygiene.md` — the loop runs a fresh
  session per WU, so in-session role-switching does not occur, and nothing links
  to it. Correct opt-out.)
- **Links to targets *outside* the vendored subtree** (e.g. a rule linking
  `../methodology.md`, which consumers place differently — loop keeps it at
  `docs/methodology.md`) are fragile and must be **plain prose references, not
  relative links.** Fixed in `correlation-ids.md`.

## The event `source` enum spans surfaces (learned in Gate 2)

The core event envelope's `source` pattern must admit every emitter across all
surfaces. Gate 2 found the loop emits every event with `source: "driver"`, which
the (orchestrator-derived) pattern rejected — so loop-emitted events failed
validation against the loop's own vendored schema (a pre-existing latent gap).
Core now includes `driver`; consumers that asserted driver-rejection must flip to
driver-acceptance on re-vendor. Lesson: when a surface repoints to core, audit its
actual emitter `source` values against the core enum before merge.

## Sequencing (dependency order)

1. **Stand up core** as a real rules/schema-shipping surface (the `specfuse`
   plugin today ships only README + skills). Land the CORE set above, taking
   loop's `correlation-ids.md` as canonical.
2. **Repoint loop** to vendor `event.schema.json` + the four rules from core;
   delete the direct `orchestrator/shared/schemas/...` path read.
3. **Repoint orchestrator** to consume core; split `state-vocabulary.md`; keep
   only the execution-plane substrate locally.
4. **Then** do the specs→authoring move (companion note): authoring vendors the
   core rules, so the specs agent's "pull the full shared rule set" resolves
   against core, not against the orchestrator — preserving the dependency
   direction.

Step 4 depends on steps 1–3. Do not move specs before core ships the rules, or
authoring inherits a dependency on the orchestrator.

## Open questions

1. **Definition-plane event payloads** (`initiative_created`, `spec_validated`,
   `spec_issue_*`): core, or authoring? They are emitted by the specs agent
   (authoring) but consumed by pm (orchestrator) across the seam. Lean: **core**,
   since both planes touch them (same argument as the event envelope).
2. **`methodology.md` home**: move the file to the core repo, or keep it in loop
   and have core reference it? Moving is cleaner but touches loop's docs tree.
3. **~~New `specfuse-core` plugin?~~ Resolved: no.** Substrate travels by
   vendoring, not by the plugin mechanism, so a data-only plugin is the wrong
   tool. The existing `specfuse` (gate-cycle) **repo** is the single source of
   truth; siblings vendor from it; the `specfuse` plugin is unchanged. See
   "Distribution is vendoring" above. Remaining sub-decision: the in-repo subtree
   name for the substrate (`substrate/` vs `methodology/`).
