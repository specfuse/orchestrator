# Distribution migration — Phase 1 work-unit decomposition

Status: **proposed** · Date: 2026-07-03 · Parent: `distribution-migration-plan.md` §Phase 1

Decomposes Phase 1 (package extraction) into the orchestrator's native dispatch
unit — **features** — and, under each, the **work-units** the loop would mint
per gate. Not yet an initiative: no `INIT-` id minted, not written to
`features/`. Registration is an `initiative-intake` decision (see notes at end).

All work lands in one repo: `Specfuse/orchestrator` (this repo becomes the
`specfuse-orchestrator` pip-package source, mirroring the loop repo). Marketplace
and merge-lib work are phases 3/2 and excluded here.

## Feature graph

```yaml
involved_repos:
  - Specfuse/orchestrator
autonomy_default: review
feature_graph:
  - id: F01
    type: implementation
    depends_on: []
    assigned_repo: Specfuse/orchestrator
    required_templates: []   # infra/packaging — no codegen templates apply
  - id: F02
    type: implementation
    depends_on: [F01]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
  - id: F03
    type: implementation
    depends_on: [F02]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
  - id: F04
    type: implementation
    depends_on: [F03]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
  - id: F05
    type: implementation
    depends_on: [F03]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
  - id: F06
    type: implementation
    depends_on: [F04, F05]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
  - id: F07
    type: implementation
    depends_on: [F06]
    assigned_repo: Specfuse/orchestrator
    required_templates: []
```

Critical path: **F01 → F02 → F03 → (F04, F05) → F06 → F07**. F04 and F05 fan
out from F03 and run in parallel; F06 joins them.

## Features + work-units

### F01 — Package skeleton (plan §1d)

Standalone foundation. Nothing importable moves yet.

- **WU-01** `pyproject.toml`: hatchling backend, `specfuse-orchestrator`, PEP 420
  namespace `specfuse.*` (no `specfuse/__init__.py`), runtime deps
  `jsonschema>=4.18`, `pyyaml>=6.0`. (Loop dep deferred to F05.)
- **WU-02** Create empty `specfuse/orchestrator/__init__.py` with `__version__`.
- **WU-03** Hatch build hook that populates `specfuse/orchestrator/_substrate/`
  from `shared/**` at build time (one source of truth, not a committed copy).
- **WU-04** `python -m build` produces a wheel containing `_substrate/`;
  verified by `unzip -l` in the WU's own check.

Gate exit: wheel builds, ships substrate, installs into a clean venv (imports,
does nothing yet).

### F02 — Path seam (plan §1b)

The load-bearing refactor. No driver moved yet — build the seam they'll use.

- **WU-01** `specfuse/orchestrator/paths.py`: `state_root()` — resolves
  `$SPECFUSE_ORCH_STATE` → `--state-root` → walk-up-from-cwd for a marker
  (`project/` + `features/`); raises a clear error if unresolved.
- **WU-02** `substrate(*parts)` — `importlib.resources.files("specfuse.orchestrator")
  / "_substrate" / ...`, returning a real path (via `as_file`) for callers that
  need one.
- **WU-03** Unit tests for both resolvers (env / flag / walk-up / missing).

Gate exit: `paths` resolves state and substrate independently, tested.

### F03 — Module migration + rename (plan §1a, §1b)

Move the 10 drivers; repoint every read through `paths`.

- **WU-01** Move + rename per the table (`orchestrator-init.py→init.py`,
  `validate-event.py→validate_event.py`, `qa-feature-dispatcher.py→qa_dispatcher.py`,
  etc.). `git mv` to preserve history.
- **WU-02** Replace every `REPO_ROOT = Path(__file__).parent.parent` with
  `paths.state_root()` for state reads (`features/ events/ overrides/
  roadmap.md project/`).
- **WU-03** Repoint substrate reads (`shared/schemas/*`, `shared/distribution/
  ownership-manifest.yaml`) to `paths.substrate(...)`.
- **WU-04** `init.py`: leave the hardcoded loop path (`../../Specfuse/loop`)
  **as-is** — its rewrite is phase 2. Just make it import-clean under the new
  module name.
- **WU-05** Smoke-run each driver's `--help` from the installed package.

Gate exit: all drivers import and read state-vs-substrate from the correct root;
no `parent.parent`.

### F04 — Tear down subprocess-by-path coupling (plan §1c)

Depends on F03 (modules exist). Parallel with F05.

- **WU-01** Give `validate_event` and `validate_frontmatter` an importable
  `validate(path) -> list[error]`, keeping their `argparse main()` as a thin
  wrapper.
- **WU-02** Port `read-agent-version.sh` → `specfuse/orchestrator/_version.py`
  `read_agent_version(repo) -> str`.
- **WU-03** Rewrite `poller.py` + `reconcile_overrides.py` to call those
  functions **in-process** instead of `subprocess.run(REPO_ROOT/scripts/...)`.
- **WU-04** Grep-gate: no `subprocess` call targets a sibling `.py`/`.sh` by
  filesystem path.

Gate exit: zero path-based subprocess between drivers.

### F05 — Console scripts + ownership fragment (plan §1a, §1d)

Depends on F03. Parallel with F04.

- **WU-01** `[project.scripts]`: `specfuse-poller`, `specfuse-runner`,
  `specfuse-validate-event`, `specfuse-validate-frontmatter`.
- **WU-02** Add `specfuse-loop>=<pin>` runtime dep (for the phase-2 merge lib).
- **WU-03** Ship `orchestrator.ownership.yaml` (orchestrator's slice of the
  ownership manifest) and register it under the `specfuse.ownership`
  entry-point group. (Merge/validate lib is phase 2 — here we only publish the
  fragment.)

Gate exit: four console scripts run post-install; ownership fragment is
discoverable via entry-points.

### F06 — Test harness (plan §1e)

Depends on F04 + F05. None exists today — bootstrap from zero.

- **WU-01** Stand up `pytest` + `tests/`; wire into `pyproject` dev extra.
- **WU-02** Wheel smoke test: build → install into temp venv → run each
  console script (`--help`, `validate-event <fixture>`).
- **WU-03** Fixtures from `shared/schemas/examples`; unit tests for both
  validators (valid + invalid cases).
- **WU-04** `check_manifest` test: packaged manifest + ownership fragment load.

Gate exit: `pytest` green locally, including the against-the-wheel smoke test.

### F07 — CI (plan §1e, Q4)

Depends on F06.

- **WU-01** CI workflow: build wheel → install → run `pytest` against it.
- **WU-02** Version-pin check: `__version__` == git tag (assert step; the
  release workflow itself is phase 4).

Gate exit: CI green on a PR; version check present.

## Acceptance (rolls up plan §1g)

- `pip install` the wheel into a clean venv → all four console scripts run.
- Drivers run against a sample state repo (`SPECFUSE_ORCH_STATE` set), reading
  substrate from the wheel — no `shared/` in the state repo.
- No driver shells out to another by filesystem path.
- CI build + test-against-wheel green; version==tag check present.

## Notes for intake / registration

1. **Schema fit.** `required_templates` and the `qa_*` feature types are
   product-codegen concepts (OpenAPI-spec-driven). Suite-infra work has neither.
   Either (a) accept `type: implementation` + empty `required_templates` as the
   infra convention, or (b) decide suite-repo work is tracked outside the
   product feature registry. This is a genuine methodology gap — worth a call
   before minting.
2. **Dogfooding question.** If `Specfuse/orchestrator` is to run the loop on
   itself, these features dispatch normally. If not, this doc is a plain
   checklist and the loop layer (gates/WUs) is advisory only.
3. **No `INIT-` minted here.** Route through `initiative-intake` (or decide it's
   out-of-band suite maintenance) before anything writes to `features/` or
   `roadmap.md`.
