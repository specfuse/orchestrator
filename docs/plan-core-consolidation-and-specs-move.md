# Work plan — core consolidation + specs→authoring move

**Status:** Ready to execute, gate-ordered.
**Decisions (locked):** single source of truth = existing `specfuse` repo,
substrate subtree named **`methodology/`**, distributed by **vendoring** (no new
plugin); definition-plane **event payloads → core**; **sequence:** core →
loop → orchestrator → specs move.
**Companion notes:** `decision-authoring-execution-boundary.md`,
`decision-core-consolidation.md`.

The gates are dependency-ordered: each depends on the one before. Do not start a
gate until the prior gate's verification passes.

---

## Gate 1 — Stand up core substrate in the `specfuse` repo

Create the single source of truth. No sibling changes yet.

1. Create `specfuse/methodology/` with subtrees `rules/`, `schemas/`,
   `schemas/events/`, `templates/`, and `methodology.md`.
2. Land the **CORE rule set** (author once, canonical). *Refined during
   execution:* only the surface-neutral rules belong in core; the loop rule set
   turned out to be internally loop-flavored (RESULT `status: blocked` vocab,
   "driver owns git"), so each landed rule was genericized to name both surfaces.
   - `correlation-ids.md` — **took loop's superset** (FEAT + INIT namespaces,
     full regex). Fixed the `methodology.md` link to `../methodology.md`. **[done]**
   - `never-touch.md`, `security-boundaries.md` — landed + genericized: `status:
     blocked` → "signal blocked" with a surface note; `.git`/driver clause made
     surface-aware; dangling `result-contract.md` links repointed to
     `verification-discipline.md`. **[done]**
   - `verification-discipline.md` — **newly authored** surface-neutral core rule:
     the four-step cycle (state intent → act → verify → report), verification as
     exit oracle, "blocked is respectable," honesty over optimism. The loop's
     `result-contract.md` and the orchestrator's `verify-before-report.md` are its
     two surface expressions and stay in their home repos. **[done]**
   - **NOT core (stay surface-specific):** `verify-before-report.md` (orchestrator
     event-log operational detail — `validate-event`, `task_completed`,
     `source_version`, Phase-3 findings) and `escalation-protocol.md`
     (orchestrator inbox model; the loop uses `blocked_human`/RESULT) stay in
     orchestrator. `role-switch-hygiene.md` leans orchestrator (multi-agent
     role-switching) — hold in orchestrator pending a genericization decision.
3. Land the **CORE schemas**: **[done]**
   - `event.schema.json` (envelope loop already reads cross-repo) — already the
     FEAT+INIT superset pattern. **Watch-item:** its `source` enum lists
     orchestrator roles; if loop needs its own `source` values when it repoints,
     extend the enum in **Gate 2**. Two cosmetic `$comment` residuals (a
     `shared/schemas/events/` path ref, Phase-history prose) — clean in Gate 3.
   - Definition-plane payloads → core: `initiative_created`, `spec_validated`,
     `spec_issue_resolved`, `spec_issue_routed`. (`spec_issue_raised` is emitted
     by execution agents → stays orchestrator.)
   - **Lifecycle spine:** the `glossary.md` lifecycle-states table already serves
     as the core spine reference; the formal `state-vocabulary.md` file split
     (spine→core, task-machine→orchestrator) is **Gate 3** work.
4. **[adjusted]** Gate 1 only *copies* `methodology.md` + its concepts addendum
   into `specfuse/methodology/` (establishes the source of truth). Loop keeps its
   working copy until **Gate 2** repoints it (leaving a pointer then) — avoids
   breaking loop's current reads mid-Gate-1. **[done]**
5. Land the **glossary** — `specfuse/methodology/glossary.md` (units: initiative,
   feature, gate, task, work-unit, per surface + lifecycle states). **Done ahead
   of the rest of the gate** as the canonical concept reference. Wire it as
   vendored core substrate alongside the rules.
6. **Verify:** every core file has exactly one home; `correlation-ids.md` is the
   FEAT+INIT superset; glossary concepts agree with `rules/correlation-ids.md`
   format; no core file references a sibling repo by path.

## Gate 2 — Repoint `loop` to vendor from core  **[DONE — PR specfuse/loop#130, CI green]**

Loop stops carrying its own copies; consumes core. Outcome: `validate_event.py`
resolves the schema via `importlib.resources` from the packaged vendored copy
(cross-repo `orchestrator/shared` read deleted); 9 shared files vendored
byte-identical to core; core gained `driver` in the event `source` enum (closing
a latent gap where loop's own events failed validation); loop opted out of
`role-switch-hygiene` (link-closed, surface-N/A). Suite 1095 green, cov 93%.

1. Point `init.sh` / `specfuse upgrade` at `specfuse/methodology/` as the source
   for the four `.specfuse/rules/` and templates loop vendors.
2. **Delete the cross-repo path dependency**: `validate_event.py` reads
   `orchestrator/shared/schemas/event.schema.json` today → repoint to the vendored
   core `event.schema.json`.
3. Re-vendor into `specfuse/loop/data/` from core (keep the package-data mechanism;
   only the source changed).
4. Keep loop-specific substrate in loop: `gate_eval.py` predicate, `PLAN/GATE/WU`
   templates, `verification.yml`, `attempt_outcome` schema, WU/gate status
   constants, gate-cycle skills.
5. **Verify:** loop test suite green; `grep -r "orchestrator/shared"` in loop
   returns nothing; vendored rules match core byte-for-byte.

## Gate 3 — Repoint `orchestrator` to consume core; split state vocab  **[DONE — branch `gate3-repoint-orchestrator-to-core`, all gates green]**

Outcome: 5 core rules vendored into `shared/rules/` (incl. new
`verification-discipline.md`); `event.schema.json` + 4 definition payloads
vendored from core; `state-vocabulary.md` points to the core glossary for the
spine (task-machine + ownership stay local); `verification-discipline` added to
all 5 agent substrate blocks; `shared/rules/README.md` provenance section.

**Key finding — the ownership charter pre-planned this.** `shared/distribution/
ownership-manifest.yaml` reserved an unused `methodology` upgrader with notes
"loop-init owns them until … `specfuse/methodology` is extracted (then upgrader →
methodology)". Gate 3 triggered that reserved extraction: added `specfuse` to the
canonical-repo vocabulary (manifest + `check_manifest.py`) and a `core-canonical`
authority; repointed correlation-ids / never-touch / security-boundaries /
role-switch-hygiene / verification-discipline / methodology-gate-cycle and a new
`schemas-methodology` fragment to `repo: specfuse, upgrader: methodology`; retired
the §3 hand-sync content-master model for them. `role-switch-hygiene` set to
`install: []` (loop opted out, orchestrator-resident).

Gates: pytest 87 pass (incl. `test_ownership`, wheel-smoke); `check_manifest`
valid (24 entries, 20 slots, one upgrader each); ruff clean; bandit exit 0;
coverage 92%; wheel builds. **Follow-up:** the `methodology` upgrader/distributor
is declared but not yet *implemented* (Track C2) — the manifest is declaratively
correct; actual scaffolding of core files into targets awaits that distributor.

### Original Gate 3 checklist (all satisfied above)

1. **Split `state-vocabulary.md`** at the seam:
   - Lifecycle spine (`drafting → … → done`, feature-level) → already in core
     (Gate 1). Orchestrator references the core copy.
   - **Task state machine** (`pending → ready → in_progress → in_review → done`,
     `blocked_spec`/`blocked_human`) + per-role transition ownership → **stays**
     in orchestrator; layer it under the spine.
2. Retire the orchestrator `shared/rules/` files that are now core (the seven);
   vendor them from core instead. Keep **execution-only** substrate local:
   - `override-registry.md`, `override.schema.json`
   - `template-coverage.schema.json`, `labels.md`
   - execution event payloads: `task_*`, `qa_*`, `feature_graph_drafted`,
     `plan_*`, `feature_state_changed`, `feature_created`
   - work-unit-issue / feature-registry / human-escalation templates
3. Re-vendor `specfuse/orchestrator/_substrate/` from core (source change only).
4. Update every agent `CLAUDE.md`'s "Shared substrate" include list to point at
   the vendored core paths.
5. **Verify:** orchestrator agents resolve every shared-rule include; no
   duplicated-but-drifted copy of a core file remains; architecture doc's §6 still
   agrees with the split (see Gate 5 doc fix).

## Gate 4 — Move the specs agent + 7 skills to `authoring`

Depends on Gates 1–3: authoring vendors the core rules, so the specs agent's
"pull the full shared rule set" resolves against **core**, not the orchestrator.

1. **Source of truth = the 7-skill `restomanager-specs` version** (initiative
   model, `initiative-intake`), NOT the stale 4-skill orchestrator copy
   (`feature-intake`, no ideation).
2. Create in the `authoring` repo:
   - `.claude-plugin/plugin.json` (if packaging authoring as its own plugin), and
   - `.claude/agents/specs.md` + `.claude/skills/<kebab>/SKILL.md` for all seven:
     `ideation-capture`, `ideation-shape`, `backlog-groom`, `initiative-intake`,
     `spec-drafting`, `spec-validation`, `spec-issue-triage`.
3. Point authoring's vendoring at core for the rules the specs agent pulls.
4. **Remove `agents/specs.md`** (and `agents/specs/`) from the
   `specfuse-orchestrator` plugin and the orchestrator repo's canonical
   `agents/specs/` — it is authoring-plane now. Leave a redirect note.
5. Update the marketplace `plugins/specfuse-authoring/` to ship the specs agent +
   7 skills alongside the existing spec-craft skills.
6. **Verify:** all 7 skills invocable under authoring; specs agent's rule includes
   resolve to vendored core; orchestrator no longer ships specs; the initiative
   lifecycle still hands to pm at `planning`.

**[Gate 4a DONE — PR specfuse/specfuse#25 merged]** specs agent + 7 skills landed
in `plugins/specfuse-authoring/` (Option A — marketplace, where the authoring
plugin lives). 89 cross-repo substrate links → prose; examples → `acme/*`; helper
ref fixed. **Gate 4b (removal from orchestrator) DEFERRED → Option C** (see below):
specs is a cross-seam substrate actor; full removal needs the emission mechanics
built. Tracked by specfuse/orchestrator#62. Follow-ups: specfuse/specfuse#24
(complete Model-B reframe in spec-drafting/validation), #23 (unify plugin sourcing).

## Gate 5 — Docs + cleanup  **[DONE — the doc reframe; physical cleanup deferred]**

1. **[done]** `orchestrator-architecture.md` §5.1/§5.2: specs reframed as the
   **authoring-plane** role (configured in `specfuse-authoring`, not `/agents/`);
   the plane boundary = `validating → planning`; mint = deploy-decision; the
   registry is a cross-seam write. State ownership (§6.3) is unchanged (still
   correct: specs owns `drafting → validating → planning`).
2. **[done]** `orchestrator-vision.md`: `specfuse/authoring` = product-definition
   plane; **mint** = deploy-decision moment; `planning` = plane handoff.
3. **[done]** `agents/specs/README.md`: deprecation banner (stale 4-skill copy;
   real one is in `specfuse-authoring`).
4. **[deferred]** Physical removal of the deprecated `agents/specs/` +
   dead-duplicate cleanup → specfuse/orchestrator#62 (needs cross-seam emission
   mechanics first). Core-vs-vendored `diff` identity was verified per-gate as the
   vendoring landed (Gates 2/3).

---

## One-look summary

| Gate | Repo | Outcome | Status |
| --- | --- | --- | --- |
| 1 | `specfuse` | `methodology/` core stood up; correlation-ids = FEAT+INIT superset | ✅ merged (#22) |
| 2 | `loop` | vendors core; cross-repo `event.schema.json` read deleted; `driver` gap closed | ✅ merged (#130) |
| 3 | `orchestrator` | vendors core; manifest `methodology` upgrader triggered; state-vocab split | ✅ merged (#61) |
| 4a | `authoring` | specs agent + 7 skills land (path-independent) | ✅ merged (#25) |
| 4b | `orchestrator` | remove stale in-repo specs | ✅ done (#62) — cleaner than feared: specs already emits `source_version: n/a`, so no cross-seam mechanics to build; deleted `agents/specs/` + plugin copy, retired the `specs-agent-config` manifest fragment, rewired `spec_issue_dispatcher` to the plugin skill. `source: specs`/transition-ownership kept. |
| 5 | docs | specs reframed authoring-plane; mint/handoff documented | ✅ this PR (deprecation banner + arch/vision) |

Open follow-ups: specfuse/specfuse#23 (unify plugin sourcing), #24 (Model-B
reframe), specfuse/orchestrator#62 (specs removal + cross-seam mechanics), and the
`methodology` distributor (Track C2, declared but unbuilt).
