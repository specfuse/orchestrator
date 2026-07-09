---
gate: 1
status: awaiting_review
---

# Gate 1 — drivers resolve pm agent version from the package (terminal)

## Definition of done

- `resolve_agent_version(role)` falls back to source `agents/<role>/version.md` (package
  repo root) when the baked `_substrate/agent-versions.json` is absent; still raises
  `FileNotFoundError` when neither the map nor the source marker exists.
- `poller.pm_version()` resolves via `resolve_agent_version("pm")`; the
  `read_agent_version(REPO_ROOT, …)` runtime read is gone.
- No driver module under `specfuse/orchestrator/` runtime-reads a vendored
  `agents/<role>/version.md` (guard test).
- `read_agent_version` and the `--repo` CLI override remain unchanged.
- Covered by `tests/test_version.py` and `tests/test_poller.py`; the full `code` set passes.

Terminal gate — single `close`. Substantive WUs T01, T02.

## Reflection notes

<Written at review time / recorded by auto-close.>
