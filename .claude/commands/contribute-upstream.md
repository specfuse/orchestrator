---
description: Extract scaffolding-only patches from downstream commits to contribute back to the upstream Specfuse-orchestrator
---

The user wants to contribute downstream improvements back to the upstream Specfuse-orchestrator.

Before they invoke the script, briefly explain what's about to happen:

- The script reviews downstream commits since the `UPSTREAM` anchor.
- Each commit is categorized: **scaffolding-only** (clean candidate), **mixed** (touches both scaffolding and private paths), or **private-only** (silently skipped).
- For mixed commits, the script extracts a path-scoped patch where private file diffs are dropped automatically.
- Commit-message sanitization is flagged where common patterns appear (FEAT-YYYY-NNNN correlation IDs, ticket prefixes like `WIDG-NN`, `JIRA-NN`).
- Chosen commits are extracted as `git format-patch` files into `./upstream-contributions/<timestamp>/`.

Then ask the user to run:

```
! ./scripts/contribute-upstream.sh
```

For a read-only categorized review (no extraction):

```
! ./scripts/contribute-upstream.sh --list
```

**Do not run the script yourself via Bash** — its interactive prompts need a real terminal.

After the script runs, help with:

- **Patch review.** Walk through each `.patch` file in the output directory. Confirm no private references survive in the commit message bodies (the path scope drops private *files*, not private *names* in messages). Flag anything that looks downstream-specific.
- **PR composition.** Help draft the PR title and body. The title should match upstream commit conventions (`feat(<scope>):`, `fix(<scope>):`, etc. — see [`CONTRIBUTING.md`](../../CONTRIBUTING.md)). The body should explain the change in upstream-agnostic terms; downstream context goes in the cover letter, not the PR body.
- **Workflow execution.** If the user wants help with the rest (fork creation, `git am`, message rebase, push, `gh pr create`), walk them through each step. The script's "Next steps" output prints the absolute path to the patch directory and template commands.

Reference: [`docs/upstream-downstream-sync.md`](../../docs/upstream-downstream-sync.md) §"Contributing back to upstream" and [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
