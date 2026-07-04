# shared/distribution — the ownership manifest

`ownership-manifest.yaml` is the single source of truth for **what the init distributors
scaffold into component and specs repos**, from which canonical source, who may upgrade it,
and whether it ships now or is deferred. It exists so the loop's `init.sh` and the
orchestrator's init (Track C2, not yet built) can overlay the same repo without clobbering
each other.

This is the prerequisite for Track C. The init scripts *consume* it; they are not built yet.

## The model

Every distributable artifact is exactly one of three **categories** (collaboration-charter §2):

- **shared-core** — methodology contracts that mean the same on both surfaces (the WU
  five-section contract, correlation IDs, verify/result discipline, never-touch, security,
  the schemas, the gate-cycle vocabulary).
- **loop-owned** — single-repo execution implementation (`loop.py`, `_miniyaml.py`,
  `lint_plan.py`, gate templates, loop skills).
- **orchestrator-owned** — agent role configs, CI (merge-watcher), codegen wiring, issue
  templates.

Each entry also carries:

- **authority** (charter §3 — who governs the *content*): `orchestrator-frozen` for any
  artifact already frozen in the orchestrator (the loop aligns down to it); `loop-authored`
  for the gate layer, which the loop authors and proves first.
- **stability** (charter §4 — *when* it ships): `stable` ships now; `moving` is deferred
  until the gate cycle is proven and `specfuse/methodology` is extracted. Charter §4 is
  explicit: do not build a vendoring graph around contracts still being revised by real runs.
- **upgrader** — exactly one of `orchestrator-init` | `loop-init` | `methodology` (future) |
  `manual`.
- **install** — the target repo(s) (`component`, `specs`) and the path in each. The
  orchestrator repo is always a *source*, never a target.

## Invariants

1. **One upgrader per install slot.** Every `(target, install path)` pair across the whole
   manifest is written by exactly one `upgrader`. This is what lets loop-init and
   orchestrator-init overlay one component repo's `.specfuse/`/`.claude/`/`.github/` without
   fighting — each only touches the slots it owns. (Validated by `check-manifest.py` below.)
2. **Overlap resolves to one canonical source.** Where an artifact exists on both surfaces
   (e.g. correlation-ids, never-touch, security-boundaries, the verify/result discipline),
   the orchestrator's frozen copy is canonical and is the single shipped source; the loop's
   local copy aligns to it and is not also shipped into the same slot.
3. **Moving artifacts are not shipped by orchestrator-init.** The gate layer
   (`methodology-gate-cycle`, `result-contract`, `authoring-work-units`, the loop kit) is
   `moving` and owned by `loop-init` until proven. orchestrator-init ships only `stable`
   entries. This is the charter §4 "ship the stable substrate now, defer the moving layer."

## What lands where (summary)

**Layout (loop convention):** everything specfuse lives under `.specfuse/` (rules, scripts,
templates, issue-templates, `agents/<role>/`); `.claude/` holds only *bridges* — a `CLAUDE.md`
that `@import`s the binding rules + the role config, and `.claude/skills/` symlinks into the
role's `.specfuse/agents/<role>/skills/`. Both inits target `.specfuse/`; the one-upgrader
invariant keeps them from colliding. (`merge-watcher.yml` is the lone exception — GitHub
mandates `.github/workflows/`.) orchestrator-init also ensures the target `.gitignore` ignores
the specfuse runtime dirs `.specfuse/state/` and `.specfuse/.scratch-logs/` (loop's logs) while
keeping `.specfuse/` itself tracked — idempotent, appends only what's missing. It also runs a
**label-sync** step: the non-templated labels in the `labels:` block whose `targets` include this
target are created on the target's GitHub repo (`gh label create --force`, idempotent; slug from
the `origin` remote). The templated `initiative:` label is minted per initiative, not here.

**Component repo** (`stable` now; `moving` once Track B/methodology land):
- orchestrator-init ships only the genuinely-orchestrator surface: the orchestrator-specific
  rules (`override-registry`; `verify-before-report`/`escalation-protocol`/`state-vocabulary`/
  `role-switch-hygiene` are **Model-B-review** — see below), `.specfuse/issue-templates/`,
  `.specfuse/templates.yaml` (stub), `.specfuse/agents/component/` (Model-B-review),
  `.github/workflows/merge-watcher.yml` — then bridges into `.claude/`.
- loop-init ships the loop-needed shared rules (`correlation-ids`, `never-touch`,
  `security-boundaries`, `result-contract`) and the loop kit (`loop.py` etc., gate templates,
  loop skills, gate-cycle docs). The rules are `stable`; the kit/gate-layer is `moving` (Track B).

**Specs repo:** `.specfuse/agents/specs/` (config + skills), bridged into `.claude/`. The specs
agent reads shared rules + issue templates from orchestrator context — no local copies.

**Orchestrator-resident, NOT distributed:** the schemas (`schemas-core`) and the event/
frontmatter validators (`event-validators`) live in the orchestration repo and are used from
there — an agent emitting an event appends to the orchestration repo's `/events` log and
validates in that checkout (the merge-watcher does exactly this). They are shared-core for
authority, but their `install` is empty by design. Only human/agent-readable *context* (rules,
templates) is distributed local; programmatic tooling + schemas stay orchestrator-resident.

## Authority vs upgrader (the Model-B audit)

`authority` and `upgrader` are independent axes:

- **authority** governs the *content* (charter §3): an artifact frozen in the orchestrator is
  `orchestrator-frozen`; the loop's copy must align to it (hand-synced per §4).
- **upgrader** is who *physically ships* it into a target repo.

So `authority: orchestrator-frozen` + `upgrader: loop-init` is valid and correct for the shared
rules a **standalone** loop needs (`correlation-ids`, `never-touch`, `security-boundaries`,
`result-contract`): loop is independently adoptable (charter §1), so loop owns their
distribution; their content still answers to the orchestrator master. orchestrator-init no
longer double-ships them (that was the loop↔orchestrator overlap this audit removed).

Distribution principle surfaced by the audit: **only the component repo needs LOCAL rule
copies** — loop loads `.specfuse/rules/` as session context for the grind. The specs / PM / QA
agents run with orchestrator-repo access and read the masters from there, so no shared-rule (or
schema, or template) copies install to the specs target.

Entries tagged **MODEL-B REVIEW** in the manifest are kept (not deleted) pending Track B
evidence, because Model B itself is unproven (charter §6): `verify-before-report`,
`escalation-protocol`, `state-vocabulary`, `role-switch-hygiene` (likely orchestrator-resident —
managed by the poller/merge-watcher/agents, not the component-loop), and `component-agent-config`
+ `shared-issue-templates` (likely subsumed by loop's grind). When Track B settles how the
component-loop verifies / escalates / reports, trim or confirm these.

## Open knobs (do not block the manifest; resolved at init time)

- **Concurrent-driver lock** — may a component repo run grind-mode loop (local state) while
  it also has open orchestrator-dispatched features (issue-label state)? A "repo busy" guard
  is an init/runtime config, not a manifest entry.
- **Grind-mode footprint** — which component repos get the loop kit at all. A per-repo
  install flag, decided when init runs against each repo.

## Next (Track C2)

Build the orchestrator `init.sh` that consumes this manifest: overlay `stable` +
`orchestrator-init`/`manual` entries into a target repo (reusing the loop `init.sh` overlay /
`--upgrade` / `--dry-run` / Claude-Code-wiring / gitignore-guard patterns), and compose with
loop's `init.sh` for the `loop-init` entries. Defer all `moving` entries until the gate cycle
is proven.
