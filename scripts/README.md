# scripts/

This directory now holds only this `README.md` and `requirements.txt`.

The Python drivers that used to live here — event/frontmatter validators, the
agent-version reader, and the rest — have moved **into the `specfuse-orchestrator`
package** and are exposed through the CLI and the installed wheel. Install the
package to get them:

```sh
pip install specfuse-orchestrator
```

The fork-era shell scripts (the old interactive setup, upstream-sync, and
contribute-back helpers) have been **deleted** along with the git-template
distribution model. Scaffolding a project's orchestration repo is now
`specfuse-orchestrator init <dir>`, and keeping it current is
`pip install -U specfuse-orchestrator` followed by
`specfuse-orchestrator upgrade <dir>`. See [`../GETTING_STARTED.md`](../GETTING_STARTED.md).

## requirements.txt

Declares the Python package dependencies used by the validators and other
drivers now shipped inside `specfuse-orchestrator`:

- `jsonschema>=4.18` — JSON Schema Draft 2020-12 validation.
- `pyyaml>=6.0` — YAML parsing for feature frontmatter.
</content>
