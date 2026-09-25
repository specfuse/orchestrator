# PM agent — receive-handoff skill (v0.1)

## Purpose

Receive a handoff manifest published by a specs repo, mint the `INIT-YYYY-NNNN`, and create the initiative registry entry from it.

This is the **consumer half of the specs seam**. The producer half (`prepare-handoff`, in the specs repo) composes the manifest and stops: it writes one artifact inside its own repository and mints nothing. Everything that lands in this repo is written here, by this skill.

## Why the seam is shaped this way

Through `specfuse-authoring` 0.20.x the producer did both halves: it wrote `/features/<id>.md` into this repo through a sibling filesystem path, and picked the correlation ID by globbing that directory for the highest ordinal.

Both were wrong in ways that only show up across repos.

- **The write** violated this repo's own invariant that it is *a SOURCE, never a target*. It also required a specs repo to hold write access here, and to know this repo's on-disk location — the dependency inversion `specfuse/authoring#26` exists to remove.
- **The mint** was a distributed counter read over another repo's working tree. The producer's own output documented the race it could not avoid: *"if the push is rejected, re-run."* A counter with one writer has no race to document.

Resolved in `specfuse/authoring#79` and `#117`: **the producer produces, the receiver registers.** The manifest is a one-way artifact, and this repo is the only writer of its own registry.

## Scope

In scope:

- Reading a handoff manifest at a path the operator supplies, and the dossier it names when one exists.
- Minting the next `INIT-YYYY-NNNN` from **this** repo's `/features/` — the only registry this skill reads or writes.
- Creating `/features/INIT-YYYY-NNNN.md` from `shared/templates/feature-registry.md`, recording the manifest as the initiative's spec provenance.
- Validating the result before it is written.

Out of scope:

- **Decomposing the initiative into features.** That is `task-decomposition`, after `planning`. This skill records the manifest's component inventory as the *input* to that, and infers nothing from it.
- **Editing anything in the specs repo.** Including the dossier: flipping the idea to `minted` is the specs repo's own act, and this skill prints what to run rather than reaching across.
- **Re-validating the specs.** They were authored and validated upstream under gates; re-running validation here would duplicate an oracle this repo does not own.

## Procedure

### Step 1 — Read the manifest

Take the manifest path from the operator. Read §1 (identity, including the authoring feature id), §3–§6 (operations, async surface, entities, cross-domain dependencies) and §9 (the consumer-repo hint).

If the path does not resolve, STOP and say so. Do not search for it: a manifest is published deliberately, and guessing which file was meant is how the wrong initiative gets minted.

### Step 2 — Mint the ordinal

Glob `/features/INIT-{currentYear}-*.md` in **this** repo. Take the largest `NNNN`, add one; `0001` when there is none. Per-year-resetting, per `correlation-ids.md`.

One writer, one registry, no race.

### Step 3 — Derive `involved_repos` from the manifest, and confirm it

The manifest's §9 Tier-B hint names the generation groups and the consumer repos they target. Propose that set; **the operator confirms or corrects it before anything is written.** The hint is advisory in the contract, and an initiative dispatched at the wrong repos is expensive to unpick.

### Step 4 — Write the registry entry

`/features/INIT-YYYY-NNNN.md`, from `shared/templates/feature-registry.md`:

```yaml
---
correlation_id: INIT-YYYY-NNNN
state: planning
involved_repos:
  - <confirmed in Step 3>
autonomy_default: <the operator's choice>
feature_graph: []
next_step:
  summary: Decompose the manifest's component inventory into per-repo features.
  owner: pm
  updated: <today>
specs_source: <manifest path, repo-relative in the producing specs repo>
specs_authored_by: FEAT-YYYY-NNNN
---
```

**`state: planning`, not `drafting`.** The specs exist and were validated before this entry did; `drafting` and `validating` are transitions this initiative has no work left in. Skipping them is the point of spec-before-mint, not a shortcut around it.

`state: planning` makes `next_step` required — see the root `allOf` in `feature-frontmatter.schema.json`. It is an object (`summary`, `owner`, `updated`), not a string.

`specs_source` and `specs_authored_by` are written **together or not at all**; the schema's `dependentRequired` enforces it, because half a provenance record is worse than none.

### Step 5 — Validate before committing

```sh
specfuse validate-frontmatter --file features/INIT-YYYY-NNNN.md
```

A schema failure here is a hard error — do not commit a registry entry that does not validate.

> **Version floor.** `specs_source` and `specs_authored_by` were added to `feature-frontmatter.schema.json` for this skill. The CLI validates against the copy **vendored into the core wheel**, not against this repo's copy, so a core release carrying them is required before Step 5 passes. Until then the validator reports them as unevaluated properties. That is a real failure, not a warning to route around: if you hit it, the receiving side is ahead of the installed core.

### Step 6 — Tell the operator what is left

This skill does not touch the specs repo. Print:

> Registered `INIT-YYYY-NNNN` from `<manifest>`.
> In the specs repo, flip the idea's dossier and backlog row to `minted` with this
> ID — or to `delivered` if no component repo will implement it.
> Next here: `task-decomposition` reads the manifest's component inventory.

## Anti-patterns

- **Writing into the specs repo.** The inversion this skill exists to remove, in the other direction. Print instructions; do not reach across.
- **Inferring `involved_repos` without confirmation.** The Tier-B hint is advisory in the contract and says so.
- **Minting before the manifest is read.** An `INIT-` id is not reusable. Resolve and read first, mint second — the same ordering `initiative-intake` uses.
- **Re-validating the specs.** They passed upstream under gates. Repeating that here claims an oracle this repo does not own, and a disagreement between the two would have no owner.
