---
id: FEAT-2026-0002/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.90
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - specfuse/orchestrator/poller.py
  - tests/test_poller.py
gate_set: code
---

# Switch `poller.pm_version()` to the package resolver

**Objective.** `poller.pm_version()` resolves the pm agent version via
`resolve_agent_version("pm")` (packaged map, with T01's source-tree fallback) instead of
`read_agent_version(REPO_ROOT, "pm")`, retiring the driver's runtime dependence on a
vendored `agents/` tree.

**Context.** Feature B / gate 1, `FEAT-2026-0002/T02`, depends on T01. Accepted adoption
decision #3. Today `specfuse/orchestrator/poller.py` imports `read_agent_version` and
`pm_version()` calls `read_agent_version(REPO_ROOT, "pm")`, walking
`<REPO_ROOT>/agents/pm/version.md`. `REPO_ROOT` is `Path(__file__).resolve().parents[2]`.
After this WU, `pm_version()` calls `resolve_agent_version("pm")` and keeps its `"n/a"`
fallback only for genuine absence. Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**
- Red test: `tests/test_poller.py::test_pm_version_uses_package_resolver` fails on HEAD and
  passes after — monkeypatch `specfuse.orchestrator.poller.resolve_agent_version` (or the
  `_version.resolve_agent_version` symbol poller calls) to return a sentinel `"9.9.9"`;
  assert `poller.pm_version() == "9.9.9"`, proving it no longer walks `REPO_ROOT/agents`.
- `tests/test_poller.py::test_pm_version_na_on_missing` — the resolver raising
  `KeyError` or `FileNotFoundError` → `pm_version()` returns `"n/a"`.
- Guard test `tests/test_poller.py::test_no_driver_runtime_reads_vendored_agents` — assert
  no module source under `specfuse/orchestrator/` contains a runtime read of
  `agents/<role>/version.md`: no `read_agent_version(REPO_ROOT` call and no
  `"agents" / <var> / "version.md"` path construction outside `_version.read_agent_version`
  itself (which stays for the `--repo` dev override). Scope the scan to `specfuse/orchestrator/*.py`.
- `poller.py` no longer imports `read_agent_version`; if `REPO_ROOT` is unused after the
  change, remove it (else ruff F401/unused will fire).
- Symbol check: `python3 -c "from specfuse.orchestrator.poller import pm_version"`.
- Full `code` set green (build/pytest/ruff/bandit/coverage).

**Do not touch.** `_version.py`'s public API (T01 owns the resolver), the `--repo` CLI
path, `agents/`, `shared/`, secrets, `.git/`, `PLAN.md status`.

**Verification.** The `code` set in `.specfuse/verification.yml`; the three tests above.

**Escalation triggers.** If removing the vendored-tree read breaks another poller code
path that legitimately needs the state-repo version (grep `read_agent_version` /
`REPO_ROOT` uses before deleting), emit `status: blocked` naming the caller rather than
silently dropping a needed dependency.
