---
id: FEAT-2026-0002/T01
type: implementation
status: blocked_human
attempts: 0
planned_cost_usd: 0.90
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - specfuse/orchestrator/_version.py
  - tests/test_version.py
gate_set: code
duration_seconds: 364.868
cost_usd: 1.534192
input_tokens: 13295
output_tokens: 16975
---

# Give `resolve_agent_version` a source-tree fallback

**Objective.** `resolve_agent_version(role)` resolves from source
`agents/<role>/version.md` (the package's own repo root) when the baked
`_substrate/agent-versions.json` map is absent, so an unbuilt checkout / editable
install still reports a real agent version instead of nothing.

**Context.** Feature B / gate 1, `FEAT-2026-0002/T01`. Accepted adoption decision #3
(`docs/design/adoption-and-collaboration.md`). Today
`specfuse/orchestrator/_version.py::resolve_agent_version` raises `FileNotFoundError`
when `paths.substrate("agent-versions.json")` is missing (see the map-absent branch).
The build hook (`hatch_build.py`) bakes that map from `agents/<role>/version.md`; a raw
source tree has no baked map. The marker parser already exists as `read_agent_version`
— reuse it against the package repo root `Path(__file__).resolve().parents[2]`. Binding
rules in `.specfuse/rules/` apply. `paths.substrate` is monkeypatchable (see the
`packaged_map` fixture in `tests/test_version.py`) — keep the new path hermetically
testable the same way.

**Acceptance criteria.**
- Red test: `tests/test_version.py::test_resolve_source_tree_fallback` fails on HEAD and
  passes after — with `paths.substrate` monkeypatched to a nonexistent map AND
  `resolve_agent_version` pointed at a repo root whose `agents/demo/version.md` carries
  `Current version: **7.7.7**`, `resolve_agent_version("demo")` returns `"7.7.7"`.
- `tests/test_version.py::test_resolve_no_map_no_source_raises` — map absent AND no
  source marker → `resolve_agent_version` still raises `FileNotFoundError`.
- Existing `tests/test_version.py::test_resolve_agent_version_from_packaged_map` stays
  green: when the baked map is present it wins; the source fallback is not consulted.
- Symbol check: `python3 -c "from specfuse.orchestrator._version import resolve_agent_version"`.
- Full `code` set green (build/pytest/ruff/bandit/coverage); `_version.py` coverage ≥ 90%.

**Do not touch.** `poller.py` (that is T02), `read_agent_version`'s existing behavior
and the `--repo` CLI path, `agents/`, `shared/`, secrets, `.git/`, `PLAN.md status`.

**Verification.** The `code` set in `.specfuse/verification.yml`; the three tests above.
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the source-tree repo root cannot be located deterministically
from `_version.py` (e.g. the module is imported from an install layout where
`parents[2]` is not the repo root), emit `status: blocked` rather than shipping a
fallback that reads the wrong directory — the packaged-map path must remain the primary,
and the fallback must not misfire in an installed wheel.
