---
feature_id: FEAT-2026-0002
gate: 1
verdict: met
---

# Retrospective — FEAT-2026-0002 (Drivers resolve agent versions from the package)

## Gate 1

Terminal single gate. Two substantive WUs (T01, T02) + this close. Goal: retire the
driver's runtime dependence on a consumer-vendored `agents/` tree by resolving the pm
agent version from the packaged map (`resolve_agent_version`), with a source-tree
fallback for unbuilt checkouts. Realizes accepted adoption decision #3 (§5,
`docs/design/adoption-and-collaboration.md`) — for the pm `source_version` read.

**Outcome:** both WUs landed and passed the full `code` gate (build/pytest/ruff/
bandit/coverage). `resolve_agent_version("role")` now falls back to source
`agents/<role>/version.md` (package repo root, `parents[2]`) when the baked
`_substrate/agent-versions.json` map is absent, still raising `FileNotFoundError`
when neither exists (T01). `poller.pm_version()` calls `resolve_agent_version("pm")`,
keeps a `"n/a"` fallback on `KeyError`/`FileNotFoundError`/`ValueError`, no longer
imports `read_agent_version`, and no driver module under `specfuse/orchestrator/`
runtime-reads a vendored `agents/<role>/version.md` (guard test) (T02).

**DoD check (GATE-01):**
- ✅ `resolve_agent_version` source-tree fallback + still-raises behavior — T01,
  `tests/test_version.py`.
- ✅ `poller.pm_version()` via `resolve_agent_version("pm")`; `read_agent_version(
  REPO_ROOT, …)` runtime read gone — T02, `specfuse/orchestrator/poller.py:474`.
- ✅ Guard test: no driver-module runtime read of vendored `agents/<role>/version.md`
  — `tests/test_poller.py::test_no_driver_runtime_reads_vendored_agents`.
- ✅ `read_agent_version` + `--repo` CLI override unchanged — `_version.py` public
  API intact.
- ✅ Covered by `tests/test_version.py` + `tests/test_poller.py`; full `code` set
  green on the passing attempts.

### Failure-class breakdown

T01 consumed **5 attempts across 3 dispatch cycles** (2 `human_escalation` events,
both `spinning_signature_repeat`) before passing; T02 passed on attempt 1.

| WU  | Attempts | Failure class | Signature | Root cause |
|-----|----------|---------------|-----------|------------|
| T01 | 5 (2 esc.) | `tests` | `test_wheel_smoke.py` — 8 ERRORs (console-script subprocess / `test_substrate_resolves_packaged_file`) | **Environment, not code.** The `code` gate's `tests` step builds a wheel (`python3 -m build --wheel`), installs it into a venv, and shells console-script `--help` subprocesses. Under the loop sandbox those subprocesses/build errored — `93 passed, 8 errors` — an identical signature every attempt, which tripped `spinning_signature_repeat`. The re-arm after disabling the sandbox (commit `33c6429`) passed first try with the same code approach. |
| T02 | 1 | — | — | Clean. |

The escalations were **false negatives against the code**: the repeated signature was
a sandboxed wheel-build/console-script env failure, confirmed by the re-arm note
("prior block was sandboxed wheel-build env failure, not code") and the immediate pass
once the sandbox was off. No T01 code defect was ever the blocker.

## Cost analysis

`planned_cost_usd` — PLAN.md `2.20`; per-WU frontmatter T01 `0.90` + T02 `0.90` +
G1-CLOSE `0.40` = `2.20` (consistent).

Actual spend (sum of `attempt_outcome.cost_usd` in `events.jsonl`):

| WU  | Planned | Actual | Attempts | Delta |
|-----|---------|--------|----------|-------|
| T01 | 0.90 | 4.0041 | 5 (2 esc.) | **+3.10 (+345%)** |
| T02 | 0.90 | 0.6445 | 1 | −0.26 (−28%) |
| **Substantive total** | **1.80** | **4.6486** | 6 | **+2.85 (+158%)** |
| G1-CLOSE | 0.40 | (this session; not in events yet) | — | — |

**Delta named:** the entire ~$2.85 substantive overrun is T01's spin. Its final passing
attempt ($0.60) was in line with the $0.90 estimate; the extra ~$3.40 was four wasted
attempts re-running an environment-broken gate. T02 came in under estimate. The plan's
per-code-delta sizing was accurate; what it did not price was a gate that misfires under
the sandbox and drives the driver to burn its full escalation budget twice.

## What the loop did NOT verify

(nothing — every acceptance criterion was verified in-loop.) The full `code` set
(build/pytest/ruff/bandit/coverage, incl. `_version.py` ≥90%) ran and passed on the
final T01 attempt and the sole T02 attempt; the three named red tests per WU and the
guard test all executed in-loop.

**Environment caveat (not a deferred criterion):** the `tests` gate's wheel build +
console-script subprocesses only run correctly with the loop sandbox disabled. The
criteria WERE verified — but only in the sandbox-off environment. See
`## What I'd change`.

## Backwards note

- Drivers now resolve the pm agent version from the **packaged** map: a built/installed
  tree reads `_substrate/agent-versions.json` (baked from `agents/pm/version.md` at
  build time).
- An **unbuilt source tree / editable install** (no baked map) falls back (T01) to
  source `agents/pm/version.md` at the package repo root (`parents[2]`); if neither the
  map nor the source marker exists, `resolve_agent_version` raises `FileNotFoundError`
  and `pm_version()` returns `"n/a"`.
- **Unchanged:** `read_agent_version(repo, role)` and
  `python3 -m specfuse.orchestrator._version <role> --repo …` — the dev / state-repo
  `--repo` override path is untouched.
- A consumer no longer needs a vendored `agents/` tree at runtime **for the pm
  `source_version` read**. This is one driver read of one role; the full "consumer holds
  only state" end-state (all roles, `shared/`, agent role prompts homed in the wheel)
  is not yet complete — see docs note.

### Docs

- `GETTING_STARTED.md` does **not** reference `agents/<role>/version.md`,
  `read_agent_version`, or the runtime version read — no stale-doc contradiction to
  fix there (unlike FEAT-2026-0001, where a changed default left the doc teaching the
  old flow).
- `docs/design/adoption-and-collaboration.md` §5 / decision #3 already documents this
  as the recommended end-state; it remains accurate. **Follow-up row (not this
  feature):** decision #3's end-state is only partially realized — this feature moved
  the pm `source_version` driver read; still open are the other roles' reads (if any),
  the `shared/` `@-include` coupling (§5), and homing the agent role prompts in the
  wheel. No doc rewrite required now; a "consumer holds only state" GETTING_STARTED
  rewrite (§6) should wait until that coupling is fully retired, else it would promise
  an end-state the tooling has not reached.

## What I'd change

- **Price sandbox-fragile gates into the WU's attempt budget.** T01's code was one
  attempt of work; the plan under-sized it because the `code` gate's wheel-build +
  console-script `tests` step misfires under the loop sandbox and produces a stable,
  code-independent failure signature. A WU whose gate builds a wheel or spawns
  console-script subprocesses should either (a) declare the sandbox-off run requirement
  up front, or (b) budget for the escalation churn a misfiring env gate causes.
- **Teach the driver (or the WU note) that a repeated `test_wheel_smoke.py` ERROR
  signature means "suspect env, not code."** `spinning_signature_repeat` fired twice on
  what was never a code problem; a stable wheel-smoke ERROR block is a strong
  env-misconfiguration tell and should be checked before spending the escalation budget.
- **Single-gate sizing:** appropriate. Two bounded, dependent code changes + terminal
  close, ≤4 WUs. Nothing was deferred and the "What the loop did NOT verify" list is
  empty, so the sizing flag (>2 entries or >30% of criteria) does **not** fire. The
  overrun was an environment problem, not a decomposition problem.

## Verdict

**met.** Both substantive WUs landed and passed the full `code` gate; every GATE-01
Definition-of-Done item is satisfied and verified in-loop; the source once implemented,
`agents/`, `shared/`, and `PLAN.md status` were untouched by the close. The +158%
substantive cost overrun is fully attributed to an environment (sandbox / wheel-build)
gate misfire on T01, not to unmet scope or unverified behavior — it is a cost lesson,
not a correctness gap. The driver owns the `PLAN.md status -> done` flip (gated on this
`verdict: met`); it is not written here.
