---
description: Run the periodic upstream sync — review and cherry-pick upstream commits since the UPSTREAM anchor
---

The user wants to sync improvements from the upstream Specfuse-orchestrator into this downstream orchestration repo.

Before they invoke the script, briefly explain what's about to happen:

- The script lists upstream commits since the `UPSTREAM` anchor, path-scoped to scaffolding paths only (`agents/`, `shared/`, `scripts/`, `docs/` excluding `docs/walkthroughs/`, `project/README.md`, `README.md`).
- For each commit, it prompts: take **[y]es**, **[n]o**, view **[d]iff**, or **[q]uit**.
- Cherry-picks chosen commits one at a time. On conflict, halts with clear resume instructions.
- At the end, offers to advance the `UPSTREAM` anchor automatically.

Then ask the user to run:

```
! ./scripts/sync-upstream.sh
```

For a read-only review (no prompts, no cherry-picks):

```
! ./scripts/sync-upstream.sh --list
```

**Do not run the script yourself via Bash** — its interactive prompts need a real terminal. The `!` prefix is what runs it in the user's session and lets the prompts work.

After the script runs, help interpret the output:

- If commits were cherry-picked, remind the user to validate the event log and frontmatter against the synced schemas (`scripts/validate-event.py`, `scripts/validate-frontmatter.py`) and to review per-agent versions for any behavioral changes.
- If a cherry-pick conflicted, walk them through the resolution: read the conflicted file, understand both sides, decide, run `git cherry-pick --continue` or `--abort`, then re-run the sync script if more commits remain.
- If the `UPSTREAM` file was advanced, suggest committing it: `git add UPSTREAM && git commit -m 'chore: sync upstream to <sha>'`.
- If the user picked nothing, that's fine — they may have wanted just a review pass.

Reference: [`docs/upstream-downstream-sync.md`](../../docs/upstream-downstream-sync.md) for the full workflow.
