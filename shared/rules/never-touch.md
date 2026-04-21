# Never-touch list

Five categories of path and configuration are off-limits to every operational agent in the orchestrator, regardless of role or task type. Writes to these surfaces happen only through the specific protocols named below — never inline from a task. Architecture §5.3 and §9.1, and the design summary's "Shared vs role-specific" section, are the sources for this list.

If a task's acceptance criteria or verification steps appear to require modifying something in this list, that is an escalation condition, not a license to proceed. Stop and raise a `spec_level_blocker` or `override_expiry_needs_review` escalation per `escalation-protocol.md`.

## 1. Generated code directories

Any path under a component repo's generated directory — `_generated/`, `gen-src/`, or the equivalent directory that the component repo declares as generated — must not be modified by any agent other than the Specfuse generator. This applies to every operational role without exception.

Matching rules:

- The canonical names are `_generated/` and `gen-src/`, but the authoritative list is what the component repo itself declares as generated (typically in its root README or a `specfuse.yaml`-style config). If your task is in a repo whose generated directory uses a different name, treat that name with identical prohibition.
- The rule applies to every file under the directory, recursively, including subdirectories, configuration fragments, and anything that was produced by a generator run.
- The rule applies regardless of whether the file currently exists. Creating a new file inside a generated directory is still a write to that directory.

When a generated file is wrong, the response is to raise a spec issue (template `shared/templates/spec-issue.md`) against the product specs repo or the generator project, not to edit the file. The only authorized path to modifying a generated file is the override protocol in `override-registry.md`.

## 2. Branch protection configuration

GitHub branch protection rules on any repo — orchestration, product specs, or component — are the enforcement boundary for merge gating (architecture §10). Merges require all tests passing, coverage ≥ 90%, zero compiler warnings, clean OWASP scan, clean linting, and required reviewers. These gates are enforced by infrastructure so that neither an agent nor a human on the merge button can bypass them.

Agents must not:

- Modify `.github/settings.yml` or equivalent files that configure branch protection.
- Modify GitHub Actions workflows whose purpose is to enforce a required check (listed in the branch protection ruleset).
- Request or accept changes to branch-protection settings via the API or `gh` CLI.
- Argue for weakening a required check as a shortcut to unblocking a failing verification — the correct response to a failing check is to fix what the check is flagging.

Changes to branch protection are human-only changes, made deliberately and reviewed as the sensitive infrastructure changes they are.

## 3. Secrets and credentials

Secrets include, at minimum: API tokens, deploy keys, SSH private keys, OAuth client secrets, webhook signing secrets, database passwords, `.env` files, cloud credentials (AWS, GCP, Azure), and any file conventionally holding a credential (`*.pem`, `*.key`, `id_rsa*`, `credentials.json`, `.npmrc` tokens, `gh auth` tokens).

Agents must not:

- Read the contents of a secrets file. If a task requires one, see `security-boundaries.md` for the escalation path.
- Write any value that looks like a credential into a commit, an issue body, a PR description, an event log entry, an inbox file, or a log line. This holds whether the value came from a real secret or was invented.
- Echo the contents of environment variables that hold secrets. Prefer referencing them by name (`$GITHUB_TOKEN`) over reading their values.
- Commit secret files to any repo under any circumstance, including as examples or fixtures.

The `security-boundaries.md` rule expands on this category and defines the response when a verification step appears to require secret access.

## 4. `/business/` in the product specs repo

The product specs repo is split at the top level: `/product/` is agent-accessible, `/business/` is not (architecture §4.1). The `/business/` subtree contains brand guidelines, marketing collateral, sales assets, and support documentation. Non-technical teams commit there frequently; exposing agents to that churn would confuse planning and waste context without producing any orchestrator value.

Agents must not read from, write to, glob across, or reference files under `/business/`. If a task's description appears to point into `/business/`, that is a description bug — stop and raise an escalation rather than following the pointer.

## 5. `.git/` contents

The `.git/` directory is the git repository's internal state. Writing to it directly — rather than via the plumbing or porcelain git commands an agent is expected to use — corrupts the repository and destroys audit trail.

Agents must not:

- Write to any file under `.git/` (hooks, config, refs, packed objects, reflog, index, hook scripts).
- Edit `.git/hooks/*` to bypass checks. If a hook is failing, diagnose the underlying issue rather than removing the hook.
- Modify `.git/config` to change remotes, user identity, or signing settings.
- Invoke `git` with flags that skip hooks or signing (`--no-verify`, `--no-gpg-sign`, `-c commit.gpgsign=false`) unless the human has explicitly asked for that specific action.

Ordinary git operations — `git add`, `git commit`, `git push`, branch and tag management — are allowed and expected. The prohibition is against reaching under the porcelain layer to bypass its guarantees.

## Applying this rule

Before writing to any path, confirm it is not in one of the five categories above. If you are uncertain whether a path is "generated" or "hand-written," the component repo's declaration is authoritative; if the declaration is missing or ambiguous, treat the path as generated and raise an escalation rather than writing. Silence at a boundary is not permission.
