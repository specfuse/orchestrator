# Security policy

Thank you for helping keep the Specfuse Orchestrator and its downstream consumers secure.

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.** Public reports give attackers a head start while a fix is being prepared.

Instead, [**open a private security advisory**](https://github.com/specfuse/orchestrator/security/advisories/new) on this repository. The advisory is visible only to you and the maintainers until a fix is published.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (proof-of-concept welcome).
- Affected files / agents / scripts (e.g., a specific skill, a shell helper, a schema).
- Whether the issue is in scaffolding (this repo's content) or could affect a downstream's coordination state (`/features/`, `/events/`, `/inbox/`, override registry).

We aim to acknowledge reports within 7 days and provide a remediation timeline within 14 days.

## Scope

In scope:

- Vulnerabilities in the orchestrator's scaffolding: scripts under `scripts/`, schemas, agent configurations that could lead to prompt injection, escalation bypass, or unauthorized writes outside documented surfaces.
- Vulnerabilities in the bidirectional sync workflow that could leak private downstream content into upstream contributions, or upstream content into downstream private state.
- Documentation that could mislead an operator into an insecure setup (missing `never-touch.md` boundary, unsafe `gh` permission scopes, etc.).

Out of scope:

- Issues in downstream private orchestration repos (those are the downstream operator's responsibility).
- Issues in Claude Code itself, the Anthropic API, or upstream tools — please report those to the relevant project.
- Issues in the Specfuse generator or `_generated/` content in component repos — those belong to the Specfuse generator project.

## Disclosure timeline

After a fix lands, we'll publish an advisory describing the issue and credit the reporter (if desired). Until the fix is public, please keep details private.

## Existing safeguards worth knowing about

- `shared/rules/never-touch.md` enumerates filesystem paths agents must never read or write (secrets, generated directories, `/business/` in product specs, branch protection settings).
- `shared/rules/security-boundaries.md` documents what agents may and may not exfiltrate or transmit.
- `scripts/template-clone-strip.sh` and `scripts/contribute-upstream.sh` are designed to keep private downstream content out of upstream contributions; report any way to bypass that intent as a security issue.
