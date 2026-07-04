---
gate: 1
status: awaiting_review
---

# Gate 1 — `init` is local-first + location-agnostic (terminal)

## Definition of done

- `specfuse-orchestrator init <dir>` does NOT `git init` by default; a `--git` flag
  opts in; `<dir>` already inside a git repo is detected (walk-up) and never re-init.
- No `gh repo create` anywhere.
- `project/NEXT_STEPS.md` presents the three adoption shapes with a publish one-liner each.
- Covered by `tests/test_cli.py`; the full `code` set passes.

Terminal gate — single `close`. Substantive WUs T01, T02.

## Reflection notes

<Written at review time / recorded by auto-close.>
