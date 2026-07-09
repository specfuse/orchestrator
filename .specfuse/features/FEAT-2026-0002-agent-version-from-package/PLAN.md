---
feature_id: FEAT-2026-0002
title: Drivers resolve agent versions from the package (adoption feature B)
slug: agent-version-from-package
branch: feat/agent-version-from-package
roadmap_goal: Drivers resolve agent version markers from the installed package (`resolve_agent_version`) instead of the consumer's vendored `agents/` tree, so a consumer holds only state (adoption decision #3).
autonomy_default: review
status: active
planned_cost_usd: 2.20
---

# Plan: Drivers resolve agent versions from the package (adoption feature B)

The drivers stamp each event's `source_version` from the agent role that emitted it.
Today `poller.pm_version()` reads `<REPO_ROOT>/agents/pm/version.md` via
`read_agent_version` — the vendored-tree path — forcing every consumer to carry an
`agents/` copy at runtime. Accepted decision #3 of
`docs/design/adoption-and-collaboration.md`: a consumer should hold **only state**;
the tooling and versions ship in the wheel.

The package-side resolver already exists: `resolve_agent_version(role)` reads the
`_substrate/agent-versions.json` map baked at build time from `agents/<role>/version.md`.
This feature (a) gives that resolver a source-tree fallback so an unbuilt checkout /
editable install still reports a real version, and (b) switches the one remaining
driver caller (`poller.pm_version()`) onto it — retiring the runtime dependence on a
vendored `agents/`. `read_agent_version` and the `--repo` CLI override stay for the
dev / state-repo case; only the driver's *default* runtime path moves.

Two substantive changes → single terminal gate (ceremony proportionality, ≤4 WUs):
- **T01** — `resolve_agent_version(role)` falls back to source `agents/<role>/version.md`
  (package repo root) when the baked substrate map is absent; still raises if neither.
- **T02** — `poller.pm_version()` resolves via `resolve_agent_version("pm")`, dropping the
  `read_agent_version(REPO_ROOT, …)` read; a guard test asserts no driver module
  runtime-reads a vendored `agents/<role>/version.md`.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0002/T01
        file: WU-01-resolver-source-fallback.md
        depends_on: []
      - id: FEAT-2026-0002/T02
        file: WU-02-poller-uses-package-resolver.md
        depends_on: [FEAT-2026-0002/T01]
      - id: FEAT-2026-0002/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0002/T01, FEAT-2026-0002/T02]
```

## Notes

- The `code` gate's `pytest` set is the oracle (`tests/test_version.py`,
  `tests/test_poller.py`); `_version.py` is inside the coverage-gated set (≥90%).
- Backwards note: after T02, a driver run from a **built/installed** tree resolves the
  pm version from the packaged map; a raw source checkout with no baked
  `_substrate/agent-versions.json` falls back (T01) to source `agents/pm/version.md`.
  `read_agent_version` and `python3 -m specfuse.orchestrator._version <role> --repo …`
  are unchanged. Call this out in the close.
