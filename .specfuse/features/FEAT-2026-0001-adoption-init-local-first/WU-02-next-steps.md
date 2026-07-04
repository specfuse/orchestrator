---
id: FEAT-2026-0001/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.70
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - specfuse/orchestrator/cli.py
gate_set: code
---

# Rewrite NEXT_STEPS.md for the three adoption shapes

**Objective.** Rewrite the `project/NEXT_STEPS.md` template `init` writes so it
presents the three adoption shapes — dedicated repo / subdir of an existing repo /
local-first — each with a one-liner for publishing when the user is ready.

**Context.** Feature A / gate 1, `FEAT-2026-0001/T02`. Depends on T01. The template is
`_NEXT_STEPS_TEMPLATE` in `cli.py` (written by `_write_next_steps`). It currently
assumes the dedicated-repo fork flow. Reframe per §6 + §1 of
`docs/design/adoption-and-collaboration.md`. Binding rules in `.specfuse/rules/`.

**Acceptance criteria.**
- Red test: `tests/test_cli.py::test_next_steps_adoption_shapes` fails on HEAD and
  passes after: after `cli.main(["init", str(tmp_path)])`, `tmp_path/project/NEXT_STEPS.md`
  exists and names all three shapes (assert the file contains "dedicated", "subdir"
  (or "subdirectory"), and "local" case-insensitively) plus the plugin-install step
  (`/plugin install specfuse-orchestrator@specfuse`).
- The NEXT_STEPS content includes: install (done), pick-where-state-lives, `/onboard`,
  and an OPTIONAL publish step (git init / gh repo create / commit-into-existing) —
  framed as optional, not a precondition.
- No `gh repo create` presented as a required step.
- Full `code` set green.

**Do not touch.** The git-flag logic (T01), other package modules, `shared/`, secrets.

**Verification.** The `code` set; the NEXT_STEPS test above.

**Escalation triggers.** If the NEXT_STEPS template is consumed by a test elsewhere
that asserts the old fork-flow wording, update that test as part of this WU (it is
the same behavioral change), or emit `status: blocked` naming the conflicting test.
