# Orchestrator Distribution Migration Plan

Status: **proposed** · Date: 2026-07-03

Migrate the orchestrator from a git-template fork model to the pip-package +
shared-marketplace-plugin model already used by `specfuse-loop` and
`specfuse-authoring`.

## Motivation

The orchestrator today is distributed as a git template: consumers
`git clone` it, run `scripts/setup.sh`, and pull upstream improvements via a
`/sync-upstream` cherry-pick protocol anchored on the `UPSTREAM` file.

Two structural costs:

1. **Driver drift.** `poller.py`, `runner.py`, `orchestrator-init.py`, the
   validators and dispatchers are *copied into* every downstream state repo,
   so tooling upgrades require cherry-picks and diverge over time.
2. **Inconsistent UX.** Install and upgrade differ from the rest of the
   Specfuse suite (`pip install` + CLI `init`/`upgrade`), raising the learning
   cost of adopting the whole methodology.

The rest of the suite already solved this. This plan brings the orchestrator
in line.

## Target model

Split the orchestrator into four concerns, mirroring loop/authoring:

| Concern | Today | Target |
|---|---|---|
| **Drivers** — poller, runner, orchestrator-init, validators, dispatchers | copied into downstream repo | `specfuse-orchestrator` PyPI wheel; upgrade via `pip install -U` |
| **Frozen substrate** — `shared/` (rules, schemas, templates, CI) | cherry-picked from upstream | wheel self-provisions into `.specfuse/orchestrator/` on each run |
| **State** — `features/`, `events/`, `project/`, `inbox/`, `overrides/` | *is* the repo | user-owned; wheel never touches |
| **Commands + agent configs** — `.claude/commands/`, `agents/` | repo-local markdown | `specfuse-orchestrator@specfuse` plugin (single, bundled) in the marketplace repo |

Bootstrap (`scripts/setup.sh`) becomes `specfuse-orchestrator init <dir>`:
git-init a fresh state repo, `gh repo create` (private), scaffold the
user-owned state dirs, wire `.claude/settings.json` (marketplace + plugin +
`deny-specs-edit` hook), write personalized `project/NEXT_STEPS.md`.

### Package layout

New PyPI package `specfuse-orchestrator`, sharing the PEP 420 `specfuse.*`
namespace with `specfuse.loop` / `specfuse.authoring`:

```
specfuse/orchestrator/
  cli.py            # init / upgrade / (re)provision entry point
  poller.py         # dependency recompute + dispatch (was scripts/poller.py)
  runner.py         # initiative runner (was scripts/runner.py)
  init.py           # substrate installer (was scripts/orchestrator-init.py)
  qa_dispatcher.py, spec_issue_dispatcher.py
  validate.py       # event + frontmatter schema validation
  _substrate/       # packaged copy of shared/ — self-provisioned to consumers
```

Console scripts:

- `specfuse-orchestrator` → `specfuse.orchestrator.cli:main`
- (optional) `specfuse-poller`, `specfuse-runner` thin wrappers for muscle memory

Zero runtime deps beyond what's already required (`jsonschema>=4.18`,
`pyyaml>=6.0`) — match loop/authoring's near-zero-dep posture.

### Umbrella integration — extra, NOT default-bundle

The orchestrator is **not** in the loop tier. Loop is bundled by default in the
umbrella because *every* Specfuse install needs the execution engine — each
component repo runs a loop gate-cycle per feature. The orchestrator is the
opposite: it runs at exactly **one** coordination point per project and
dispatches *to* components, which never run it. Bundling it by default would
drag coordination drivers + agent plugins into every component repo (and its
CI) that only needs the loop.

Install surfaces:

| | Loop | Orchestrator |
|---|---|---|
| Runs in | every component repo (N per project) | one coordination repo (1 per project) |
| Role | execution substrate | coordination layer; components never run it |
| Umbrella tier | default-bundled (core) | **opt-in extra** |

So:

- `pipx install specfuse` → loop only (universal core). **Unchanged.**
- `pipx install specfuse[orchestrator]` → adds `specfuse-orchestrator` for the
  coordination host. One command for the operator; component installs stay
  lean. (Authoring is already opt-in this way — `specfuse[authoring]`;
  orchestrator joins it as an extra, not the loop tier.)

Release order (umbrella last — it references the three):

```
specfuse-loop → specfuse-authoring → specfuse-orchestrator → specfuse (umbrella)
```

### Marketplace plugin

Add **one** plugin, `specfuse-orchestrator@specfuse`, to the
`specfuse/specfuse` marketplace repo (`plugins/specfuse-orchestrator/`):

- **agents/** — the 5 role configs (specs, PM, component, QA, onboarding),
  bundled together. They share event schemas / feature registry / ownership
  manifest and must release in lockstep, so a single plugin — not one per
  agent — is correct. Per-agent split is rejected: it invites schema skew
  between agents that must agree, and there is no standalone-agent use case
  (the runner/poller dispatch across all five).
- **skills/** — convert `/onboard`, `/sync-upstream`, `/contribute-upstream`
  from `.claude/commands/*.md`. Note `/sync-upstream` and
  `/contribute-upstream` are only meaningful under the old fork model; see
  "Retirements" below.

Plugin scoping mirrors the install-surface asymmetry: component repos enable
only `specfuse@specfuse` (loop skills). **Only the coordination repo** enables
`specfuse-orchestrator@specfuse` — no auto-enable of orchestrator agents in
every component. Consumer wiring is otherwise identical to the rest of the
suite: init registers `extraKnownMarketplaces.specfuse` and enables the plugin
in that one repo.

## Retirements

- `scripts/setup.sh` → replaced by `specfuse-orchestrator init`.
- `UPSTREAM` anchor + `/sync-upstream` cherry-pick → replaced by wheel
  self-provisioning + `pip install -U`.
- `/contribute-upstream` → re-evaluate. Under pip-scaffold, downstream no
  longer carries upstream git history, so scaffolding-patch extraction changes
  shape. Options: (a) drop it — substrate is wheel-owned, contributions go
  straight to the orchestrator repo as normal PRs; (b) keep a lightweight
  variant for the rare case a consumer improves a template. Lean (a).

## Open questions

1. **Substrate provisioning target.** Loop uses `.specfuse/`; orchestrator's
   `shared/` is larger. Confirm `.specfuse/orchestrator/` as the mount point
   and that state dirs stay outside it.
2. ~~**`orchestrator-init` composition with `loop-init`.**~~ **Resolved — see
   "Ownership manifest" below.**
3. **Existing downstreams.** One migration script to convert a template-forked
   state repo to the pip model (drop vendored drivers, add settings wiring,
   `pip install specfuse-orchestrator`). Needed for INIT-2026-000x repos
   already live.
4. **Version pinning.** Match the suite's rule: git tag + `pyproject.toml` +
   a `DRIVER_VERSION`/`__version__` constant must agree, enforced in CI.

## Ownership manifest (resolves former Q2)

Today `shared/distribution/ownership-manifest.yaml` is a single monolith that
both `orchestrator-init` and `loop-init` read to avoid clobbering the same
component-repo file — invariant: **exactly one upgrader per (install target +
path)**. Vendoring one wheel-bundled copy per package would let the two copies
drift and both claim a path → silent clobber on upgrade.

Fix: there is no shared copy to drift.

1. **Per-package ownership fragments.** Each wheel ships only its own slice —
   `specfuse-loop` → `loop.ownership.yaml` (loop-owned + its share of
   shared-core), `specfuse-orchestrator` → `orchestrator.ownership.yaml`. Each
   package is the sole author of its fragment; neither carries a copy of the
   other's data.
2. **Auto-discovery via entry-points.** Fragments register under a Python
   entry-point group (`specfuse.ownership`). The composing CLI enumerates
   installed contributors — no hardcoded list; authoring can add a fragment
   later for free.
3. **One merge+validate lib, one enforcement path.** `specfuse-orchestrator`
   already pip-depends on `specfuse-loop` (orchestrator-init invokes
   loop-init), so the merge/invariant code lives in
   `specfuse.loop.distribution` and *both* CLIs import it. The invariant is
   enforced at **merge time**: two fragments claiming one path → hard fail,
   loud. Silent clobber becomes structurally impossible.
4. **Catch drift at build, not at install.** A CI test composes the loop +
   orchestrator fragments and asserts zero overlap — fails the release, never
   the operator's laptop.

Net: the invariant stops being a convention and becomes a check that fires at
compose time.

## Phase 1 — concrete scope

Goal: `specfuse-orchestrator` builds to a wheel whose drivers run against a
consumer state repo, with substrate read from the package instead of the fork.
**No behavior change to the drivers' logic** — this is a packaging + path-seam
refactor only. `init`/`upgrade` CLI (phase 2) and the plugin (phase 3) are out
of scope.

### 1a. Module inventory + rename map

Python module names can't contain hyphens; console scripts can. Move into
`specfuse/orchestrator/`:

| Today (`scripts/`) | Module | Console script |
|---|---|---|
| `poller.py` | `poller.py` | `specfuse-poller` |
| `runner.py` | `runner.py` | `specfuse-runner` |
| `orchestrator-init.py` | `init.py` | (called by CLI, phase 2) |
| `validate-event.py` | `validate_event.py` | `specfuse-validate-event` |
| `validate-frontmatter.py` | `validate_frontmatter.py` | `specfuse-validate-frontmatter` |
| `check-manifest.py` | `check_manifest.py` | — |
| `reconcile-overrides.py` | `reconcile_overrides.py` | — |
| `qa-feature-dispatcher.py` | `qa_dispatcher.py` | — |
| `spec-issue-dispatcher.py` | `spec_issue_dispatcher.py` | — |
| `raise-spec-issue.py` | `raise_spec_issue.py` | — |
| `read-agent-version.sh` | folded into `_version.py` | — |

**Stays in the repo, not packaged** (fork-era shell, retired in phase 5):
`setup.sh`, `sync-upstream.sh`, `contribute-upstream.sh`,
`template-clone-strip.sh`, `add-upstream-remote.sh`.

### 1b. The path seam (the load-bearing change)

Replace every `REPO_ROOT = Path(__file__).resolve().parent.parent` with a
`specfuse/orchestrator/paths.py` that exposes two distinct roots:

- `state_root()` — the consumer repo. Resolved from `$SPECFUSE_ORCH_STATE`,
  else `--state-root`, else walk up from cwd for a marker (e.g.
  `project/` + `features/`). Owns `features/ events/ overrides/ project/
  inbox/ roadmap.md`.
- `substrate(*parts)` — packaged data via `importlib.resources.files(
  "specfuse.orchestrator") / "_substrate" / ...`. Owns `shared/schemas`,
  `shared/rules`, `shared/templates`, `shared/distribution`.

Every read is re-pointed to one or the other. `shared/**` is shipped as
package data under `specfuse/orchestrator/_substrate/` (see 1d).

### 1c. Tear down subprocess-by-path coupling

`poller.py` and `reconcile_overrides.py` currently `subprocess.run` sibling
scripts by filesystem path (`REPO_ROOT/scripts/validate-event.py`,
`read-agent-version.sh`). In a wheel those paths don't exist. Convert each to
a module function and call **in-process**:

- `validate_event.validate(path) -> list[error]`
- `validate_frontmatter.validate(path) -> list[error]`
- `_version.read_agent_version(repo) -> str` (ports `read-agent-version.sh`)

Keep the thin `argparse main()` on the validators for their console scripts;
the callers stop shelling out.

### 1d. `pyproject.toml`

- Build backend: **hatchling** (match `specfuse-authoring`).
- Package: `specfuse-orchestrator`, PEP 420 namespace `specfuse.*`
  (no `specfuse/__init__.py`), code under `specfuse/orchestrator/`.
- Runtime deps: `jsonschema>=4.18`, `pyyaml>=6.0`, **`specfuse-loop>=<pin>`**
  (for the shared merge lib, former Q2).
- Package data: `specfuse/orchestrator/_substrate/**` — populated from
  `shared/` at build via a hatch build hook (or a committed sync) so there's
  one source of truth, not a hand-maintained copy.
- Console scripts: the four in the table above.
- Entry-point group `specfuse.ownership` → `orchestrator.ownership.yaml`
  fragment (former Q2 wiring; the merge lib itself is phase-2 work but the
  fragment + registration land here).
- `__version__` in `specfuse/orchestrator/__init__.py`, asserted == tag in CI
  (Q4).

### 1e. Test harness (new — none exists today)

- Stand up `pytest` + `tests/`.
- Smoke test **against the built wheel** (build, install into a temp venv,
  run `specfuse-poller --help`, `specfuse-validate-event <fixture>`).
- Unit tests for `paths.py` (state vs substrate resolution) and the two
  validators against fixtures copied from `shared/schemas/examples`.
- `check_manifest.py` gains a test asserting the packaged manifest loads.

### 1f. Non-goals (explicit)

`init`/`upgrade`/self-provision CLI → phase 2. Marketplace plugin → phase 3.
Release workflow + OIDC publish → phase 4. Downstream migration script →
phase 5. Retiring the fork-era shell scripts → phase 5. `orchestrator-init`'s
hardcoded loop path is left as-is in phase 1 (its rewrite belongs with the
phase-2 merge lib); it just moves to `init.py` unchanged.

### 1g. Acceptance

- `python -m build` produces a wheel; `pip install` it into a clean venv;
  all four console scripts run.
- Drivers run against a sample state repo with `SPECFUSE_ORCH_STATE` set,
  reading substrate from the wheel — no `shared/` dir needed in the state repo.
- No script shells out to another script by filesystem path.
- CI: build + test-against-wheel green; `__version__`==tag check present.

## Phased rollout

1. **Package extraction.** Phase 1 above.
2. **CLI.** Implement `init` (replaces setup.sh) and `upgrade`/self-provision.
3. **Plugin.** Add `plugins/specfuse-orchestrator/` to the marketplace repo;
   port agents + convert commands to skills.
4. **Release wiring.** Tag-driven `.github/workflows/release.yml` with OIDC
   PyPI publish; slot orchestrator into the suite release order; pin it in the
   umbrella.
5. **Migration + docs.** Downstream migration script; rewrite
   GETTING_STARTED / README quickstarts; retire setup.sh + sync-upstream.
```
