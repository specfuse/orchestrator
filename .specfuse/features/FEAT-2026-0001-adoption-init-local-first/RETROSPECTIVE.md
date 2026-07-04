---
feature_id: FEAT-2026-0001
gate: 1
verdict: met
---

# Retrospective — FEAT-2026-0001 (local-first, location-agnostic `init`)

## Gate 1

Terminal single-gate feature. Two substantive WUs (T01, T02) plus this terminal
close (G1-CLOSE). Both substantive WUs reached `status: done`; the `code` gate set
(build / pytest / ruff / bandit / coverage) is green and `tests/test_cli.py` passes
(22 tests). The gate's Definition of Done is met:

- `init <dir>` no longer `git init`s by default; `--git` opts in; walk-up detection
  (`_inside_existing_repo`) prevents a nested `.git` when `<dir>` sits inside an
  existing repo (`cli.py:202` `_git_init`, guarded at `cli.py:305`). Covered by
  `test_init_no_git_by_default`, `test_init_git_flag`,
  `test_init_inside_existing_repo_skips`.
- No `gh repo create` anywhere in the init path.
- `project/NEXT_STEPS.md` template presents the three adoption shapes (dedicated
  repo / subdir / local-first), each with a publish one-liner, plus the plugin
  install step. Covered by `test_next_steps_adoption_shapes`.

### Failure-class breakdown

One attempt failed across the feature (T01 attempt 1).

| WU  | Attempt | Outcome | failure_class | signature | Note |
|-----|---------|---------|---------------|-----------|------|
| T01 | 1 | failed | lint | F401 | Unused imports flagged by ruff; the same run also tripped the coverage gate (total 88 < fail-under 90). Attempt touched `.coverage` and an unrelated `pm/SKILL.md`. |
| T01 | 2 | passed | — | — | Clean `code` set; final diff in `cli.py`, `tests/test_cli.py`, plus test housekeeping. |
| T02 | 1 | passed | — | — | First-try pass. |

Root cause of the T01 miss: the first attempt left dangling imports (F401) and did
not add enough test coverage to clear the 90% floor. Both are mechanical gate
failures caught by the `code` set — no spec ambiguity, no boundary violation. The
fresh second attempt corrected both.

## Cost analysis

Costs reconciled from `events.jsonl` (`attempt_outcome` / `attempts_usage`).

| WU | planned_cost_usd | actual_cost_usd | Δ |
|----|------------------|-----------------|---|
| T01 | 1.00 | 2.0942 (0.8441 failed + 1.2502 passed) | +1.09 |
| T02 | 0.70 | 0.6584 | −0.04 |
| G1-CLOSE | 0.40 | (this session; not yet in events.jsonl) | — |
| **Substantive total (T01+T02)** | **1.70** | **2.7526** | **+1.05 (+62%)** |
| **Feature total (PLAN planned)** | **2.10** | **2.7526 + close** | — |

The overrun is entirely T01: the wasted failed attempt ($0.84) plus a second
attempt that itself ran 25% over its $1.00 estimate ($1.25). T02 came in under.
Estimate for T01 was too optimistic for a change that had to satisfy both a lint
floor and a coverage floor in one shot — see the lesson below.

## What the loop did NOT verify

- **Real-shell `git init` behavior.** Tests exercise `init` against a `tmp_path`;
  the loop did not run `specfuse-orchestrator init` in a real user working
  directory / real terminal. Behavior is asserted via filesystem state
  (`.git` present/absent), not via an end-to-end operator run.
- **Walk-up detection edge cases.** `_inside_existing_repo` is verified for the
  direct nested-subdir case; symlinked repos, worktrees, and bare/`GIT_DIR`-env
  cases are not covered.
- **GETTING_STARTED.md still describes the old flow.** Its "5-minute path" and
  "Create and push the GitHub repo" step still present `gh repo create` as the
  path; it was NOT updated by this feature (out of scope — see backwards-compat
  note). Rendered NEXT_STEPS content was validated by substring assertions, not
  by human prose review.

Sizing: 3 entries → at the flag threshold (>2). Read together they are one theme
(no end-to-end operator verification of the init UX), not three independent gaps;
none blocks the gate verdict, but the GETTING_STARTED follow-up should be armed.

## Backwards-compat note

**`init` no longer auto-git-inits.** Before this feature, `specfuse-orchestrator
init <dir>` ran `git init` unconditionally (no-op only when `<dir>/.git` existed).
After: the default scaffolds state with NO `git init`. Callers/scripts that relied
on `init` producing a repo must now:

- pass `--git` (opts in; still a no-op when `<dir>` is already inside a repo via
  walk-up), or
- run `git init` themselves.

`gh repo create` was never and is still never invoked by `init`.

**GETTING_STARTED §6 rewrite — separate follow-up (needed).** `GETTING_STARTED.md`
still teaches the dedicated-repo/`gh repo create` flow as the primary path and does
not mention `--git` or the local-first default. It needs the §6-style rewrite (per
`docs/design/adoption-and-collaboration.md` §6) to reflect the three adoption
shapes. This is out of scope for this gate and should be armed as a follow-up WU/
feature.

## Verdict

**`met`.** Both substantive WUs are `done`; the `code` gate set is green;
`tests/test_cli.py` passes (22 tests) and covers all three gate-DoD behaviors
(git opt-in default, `--git` flag, walk-up skip) plus the NEXT_STEPS three-shapes
rewrite. No `gh repo create` in the init path. The plannext gate (`specfuse-lint`)
passes once this close WU carries its `verdict` frontmatter. The one failed attempt
(T01/1) was a mechanical lint+coverage miss corrected by a clean re-attempt, not a
design or boundary problem. Remaining gaps are follow-ups (GETTING_STARTED rewrite,
end-to-end operator verification), none of which contradicts the gate DoD.
