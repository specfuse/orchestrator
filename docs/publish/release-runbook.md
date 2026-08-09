# Release runbook

Operator steps to cut a release of `specfuse-orchestrator` to PyPI. Publishing
runs from the upstream **`specfuse/orchestrator`** repo, not this fork
(`RestoManagerApp/orchestrator`): development happens here, but the tag that
triggers `.github/workflows/release.yml` (FEAT-2026-0004/T01) must be pushed on
`specfuse/orchestrator`. This is a cross-repo, human-run flow — the loop driver
does not push tags or touch PyPI; it only stages `release.yml` and this runbook.

## 1. PyPI trusted-publisher setup (one-time, BEFORE the first tag)

The release workflow publishes via OIDC trusted publishing — no stored API
token. This must be configured on PyPI **before** the first `v*` tag is pushed;
if it is missing, the `publish` job's OIDC exchange fails and the release is
left as a built-but-unpublished artifact.

1. Sign in to PyPI as an owner/maintainer of the `specfuse-orchestrator`
   project (create the project first if it does not exist yet).
2. Go to the project's **Publishing** settings and add a new trusted publisher
   with:
   - Owner: `specfuse`
   - Repository name: `orchestrator`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. Save. No token is generated or copied — the trust relationship is the
   `(owner, repo, workflow, environment)` tuple above, matched against the
   OIDC claims GitHub Actions presents at publish time.

## 2. Version bump + tag + push

1. On `specfuse/orchestrator`, bump `__version__` in
   `specfuse/orchestrator/__init__.py` to the new version, e.g. `1.0.0`.
2. Commit the version bump.
3. Tag the commit `v<version>` (the tag must match `__version__` exactly — the
   workflow's tag/version agreement check fails the build otherwise):
   ```
   git tag v1.0.0
   ```
4. Push the commit and the tag to `specfuse/orchestrator`:
   ```
   git push origin main
   git push origin v1.0.0
   ```
5. Pushing the `v*` tag triggers `release.yml`: `build-test` builds the wheel +
   sdist, installs the wheel into a clean venv, runs the full test suite
   against the installed package, and checks tag/version agreement; `publish`
   then runs only if `build-test` passed and only on a tag, publishing to PyPI
   via OIDC.

## 3. Post-publish verification

After the workflow's `publish` job succeeds:

1. Confirm the new version is visible on PyPI for `specfuse-orchestrator`.
2. Verify a plain install works from a clean environment:
   ```
   pip install specfuse-orchestrator
   ```
3. Verify the suite install path works. The umbrella (`specfuse`, in
   `specfuse/specfuse`) hard-depends on this package, so a fresh install or an
   upgrade re-resolves and picks the new version up on its own — no umbrella
   floor bump is needed unless the umbrella's own code requires it (see
   [`umbrella-orchestrator-extra.md`](umbrella-orchestrator-extra.md)):
   ```
   uv tool install specfuse       # or: pipx install specfuse
   uv tool upgrade specfuse       # or: pipx upgrade specfuse / specfuse upgrade
   ```
4. Confirm the subcommands run: `specfuse pm --help`, `specfuse poller --help`,
   `specfuse runner --help`, `specfuse validate-event --help`,
   `specfuse validate-frontmatter --help`. `specfuse --version` should report
   the new orchestrator version alongside the other components.
5. Confirm the deprecated flat console scripts still work from a standalone
   `pip install specfuse-orchestrator` — they remain aliases until the 1.0.0
   release train drops them: `specfuse-orchestrator --help`,
   `specfuse-poller --help`, `specfuse-runner --help`,
   `specfuse-validate-event --help`, `specfuse-validate-frontmatter --help`.
6. If any check fails, treat it as a release defect: do not re-tag the same
   version (PyPI rejects re-uploads of an existing version) — fix the issue,
   bump to the next version, and repeat from step 2 of section 2.
