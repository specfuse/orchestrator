# scripts/

This directory now holds only this `README.md`.

The Python drivers that used to live here — event/frontmatter validators, the
agent-version reader, and the rest — have moved **into the `specfuse-orchestrator`
package** and are exposed as `specfuse` subcommands (`specfuse pm`, `specfuse
poller`, `specfuse runner`, `specfuse validate-event`, `specfuse
validate-frontmatter`). Install the suite to get them:

```sh
uv tool install specfuse    # or: pipx install specfuse
```

The fork-era shell scripts (the old interactive setup, upstream-sync, and
contribute-back helpers) have been **deleted** along with the git-template
distribution model. Scaffolding a project's orchestration repo is now
`specfuse pm init <dir>`, and keeping it current is `specfuse upgrade`
followed by `specfuse pm upgrade <dir>`. See [`../GETTING_STARTED.md`](../GETTING_STARTED.md).
