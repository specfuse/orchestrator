---
id: FEAT-2026-0001/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.00
model: sonnet
effort: medium
generated_surfaces: []
oracle_env: macos_local
produces:
  - specfuse/orchestrator/cli.py
gate_set: code
---

# Make `init`'s git initialization opt-in + location-aware

**Objective.** Change `specfuse-orchestrator init` so it is local-first: by default
it scaffolds state WITHOUT running `git init`, adds a `--git` flag to request repo
initialization, and detects when `<dir>` is already inside a git repository (walking
up parent directories) so it never re-inits.

**Context.** Feature A / gate 1, `FEAT-2026-0001/T01`. Accepted adoption decision #1
(`docs/design/adoption-and-collaboration.md`). Today `cli.py`'s init flow calls
`_git_init(target_dir)` unconditionally (only no-oping when `target_dir/.git` exists).
`_git_init` must become opt-in and repo-aware. Do NOT add `gh repo create`. Binding
rules in `.specfuse/rules/` apply.

**Acceptance criteria.**
- Red test: `tests/test_cli.py::test_init_no_git_by_default` fails on HEAD and passes
  after: `cli.main(["init", str(tmp_path)])` scaffolds state but leaves NO `.git` in
  `tmp_path` (`not (tmp_path/".git").exists()`).
- `tests/test_cli.py::test_init_git_flag` — `cli.main(["init", "--git", str(tmp_path)])`
  creates `tmp_path/.git`.
- `tests/test_cli.py::test_init_inside_existing_repo_skips` — when `<dir>` is a subdir
  of an existing git repo, `init` (even with `--git`) does not create a nested `.git`
  in `<dir>` (walk-up detection): pre-`git init` a parent, run `init` on a child dir,
  assert no `child/.git`.
- The init subparser accepts `--git` (argparse); state scaffold + `.claude` wiring +
  NEXT_STEPS still run regardless of the flag.
- Full `code` set green (build/pytest/ruff/bandit/coverage).

**Do not touch.** `_write_next_steps` content (that is T02), other package modules,
`shared/`, `agents/`, secrets, `.git/`. Do not add `gh repo create`.

**Verification.** The `code` set; the three tests above. Symbol check:
`python3 -c "from specfuse.orchestrator import cli"`.

**Escalation triggers.** If walk-up repo detection can't be done safely without
shelling to `git rev-parse` from within `<dir>` (which could resolve the wrong repo
when `<dir>` doesn't exist yet), scaffold first then detect, and emit `status: blocked`
if the ordering can't be made correct rather than shipping a detector that misfires.
