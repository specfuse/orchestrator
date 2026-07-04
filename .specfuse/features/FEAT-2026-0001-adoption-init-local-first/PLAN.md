---
feature_id: FEAT-2026-0001
title: Local-first, location-agnostic init (adoption feature A)
slug: adoption-init-local-first
branch: feat/adoption-init-local-first
roadmap_goal: Make `specfuse-orchestrator init` local-first — scaffold state into any dir without forcing git/GitHub — per accepted adoption decision #1.
autonomy_default: review
status: active
planned_cost_usd: 2.10
---

# Plan: Local-first, location-agnostic `init` (adoption feature A)

`specfuse-orchestrator init <dir>` currently calls `_git_init(target_dir)`
unconditionally, git-initializing a fresh repo — the fork-era "one dedicated repo
up front" assumption. Accepted decision #1 of `docs/design/adoption-and-collaboration.md`:
make `init` **local-first and location-agnostic** so broader OSS adopters can scaffold
state into an existing repo's subdirectory, or a plain local folder, with git/GitHub
deferred.

Two substantive changes → single terminal gate (ceremony proportionality, ≤4 WUs):
- **T01** — git becomes opt-in: default `init` does NOT `git init`; add a `--git`
  flag to request it; if `<dir>` is already inside a git repo (walk up, not just
  `<dir>/.git`), never init. Still never `gh repo create`.
- **T02** — rewrite `project/NEXT_STEPS.md` to present the three adoption shapes
  (dedicated repo / subdir / local-first) with a publish one-liner for each.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0001/T01
        file: WU-01-git-opt-in.md
        depends_on: []
      - id: FEAT-2026-0001/T02
        file: WU-02-next-steps.md
        depends_on: [FEAT-2026-0001/T01]
      - id: FEAT-2026-0001/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0001/T01, FEAT-2026-0001/T02]
```

## Notes

- The `code` gate's `pytest` set (via `tests/test_cli.py`) is the oracle for the
  init behavior; build/ruff/bandit/coverage unaffected.
- Backwards note: existing callers who relied on `init` auto-git-initializing must
  now pass `--git` (or run `git init` themselves). Call this out in the close.
