# Umbrella `specfuse` package: the orchestrator dependency

Target repo: **`specfuse/specfuse`** (the `specfuse` umbrella package). Edits
there are out of scope for this repo — the loop driver does not clone, edit, or
PR `specfuse/specfuse`. This file records what the umbrella already carries for
this component, and the (rare) cases where a release here needs an edit there.

## Current shape (specfuse 0.11.0+)

The umbrella **hard-depends** on every component. `specfuse-orchestrator` sits
in `[project.dependencies]`, not in an extra:

```toml
dependencies = [
  "specfuse-loop>=<floor>",
  "specfuse-authoring>=<floor>",
  "specfuse-orchestrator>=<floor>",
]
```

The `[orchestrator]`, `[authoring]` and `[all]` extras are **deleted**. Extras
broke against the pipx/uv tool model three ways:

- tool installers link only the main package's entry points, so an extra's
  commands needed `--include-deps` / `--with-executables-from` and the obvious
  install was silently incomplete;
- extras resolve once at install time and are never re-resolved, so
  `pipx upgrade specfuse` could not pull a newer component;
- an extra's console scripts share names with the standalone package's, so two
  installs fought over one name in `~/.local/bin`.

## What this means for releasing this package

**Version floors in the umbrella are minimums, not upgrade levers.** A new
`specfuse-orchestrator` release reaches users through
`uv tool upgrade specfuse` / `pipx upgrade specfuse` / `specfuse upgrade`,
which re-resolve the dependency. Do **not** ask for a floor bump as part of a
routine release.

Ask the umbrella maintainer for a floor bump only when the umbrella's own code
requires the new version.

## When a release here *does* need an umbrella edit

The umbrella dispatches subcommands into this package by dotted path — e.g.
`specfuse.orchestrator.cli:main`, `specfuse.orchestrator.poller:main`. Treat
those targets as public API:

- **Renaming a module or a `main()`** turns a subcommand into a run-time
  `ImportError`. Tell the umbrella in the same PR. Its CI resolves every target
  on each run, so it will catch a rename — but only after the release is on
  PyPI.
- **Adding a new command** requires an entry in `DELEGATED_COMMANDS` in the
  umbrella's `specfuse/cli.py`. Adding a console script here alone does not put
  it on `specfuse`.

## Result

Operators install and upgrade the whole suite with one command, no extras and
no bracket quoting:

```
uv tool install specfuse      # or: pipx install specfuse
specfuse upgrade
```

`specfuse --version` prints the resolved version of every component, which is
the fastest post-release check that a new orchestrator build landed.
