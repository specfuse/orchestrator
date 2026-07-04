# Marketplace publish runbook

Operator steps to publish the `specfuse-orchestrator` plugin (gate 1) into the
`specfuse/specfuse` marketplace. This is a cross-repo, human-run flow — the loop
driver does not clone, edit, or PR `specfuse/specfuse`; it only stages the inputs
this runbook consumes (`plugins/specfuse-orchestrator/` and
`docs/publish/marketplace-orchestrator-entry.json`).

## Prerequisites

- Local clone of `specfuse/specfuse` (the marketplace repo), up to date with its
  default branch.
- Local clone of this repo (`specfuse-orchestrator`) at the commit that carries
  the gate-1 plugin tree and the staged publish delta.
- `plugins/specfuse-orchestrator/` present and validated in this repo (gate 1
  artifact — do not regenerate or edit it as part of this runbook).
- `docs/publish/marketplace-orchestrator-entry.json` present in this repo (T04
  artifact — the exact `plugins[]` entry to insert; do not rewrite it here).
- Push access to a fork or branch of `specfuse/specfuse`, and permission to open
  a pull request against it.

## Steps

1. Copy the plugin directory from this repo into the marketplace repo checkout:
   copy `plugins/specfuse-orchestrator/` (the full tree, unmodified) into
   `specfuse/specfuse` at the path the marketplace expects for plugin sources.
2. Open `.claude-plugin/marketplace.json` in the `specfuse/specfuse` checkout and
   insert the entry staged at
   `docs/publish/marketplace-orchestrator-entry.json` into its `plugins` array.
   Use the staged entry verbatim — it already carries the `name` and `source`
   fields the marketplace manifest expects.
3. Validate the edited manifest is well-formed JSON and that the new entry's
   `source` path resolves to the copied plugin directory in step 1.
4. Commit the copied plugin directory and the manifest edit on a branch in the
   `specfuse/specfuse` checkout, push the branch, and open a pull request against
   `specfuse/specfuse`. Reference the `specfuse-orchestrator` gate-1 release in
   the PR description.
5. Wait for `specfuse/specfuse` review and merge. Do not force-merge or bypass
   that repo's own review process — this runbook only covers staging correct
   inputs, not overriding the target repo's controls.

## Post-merge verification

After the PR above merges into `specfuse/specfuse`:

1. In a Claude Code session, run `/plugin marketplace add specfuse/specfuse` (or
   refresh it if already added) so the marketplace index picks up the merged
   entry.
2. Run `/plugin install specfuse-orchestrator@specfuse` and confirm the plugin
   installs without error.
3. Confirm the installed plugin's commands/agents/skills are discoverable in the
   session (e.g. list available skills and check for the orchestrator's
   entries).
4. If installation fails, treat it as a publish defect: re-check the manifest
   entry and copied plugin tree in the merged PR before re-attempting — do not
   patch around the failure locally.
