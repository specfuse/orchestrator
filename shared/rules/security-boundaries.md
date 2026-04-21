# Security boundaries

Agents in the orchestrator operate inside a privilege model that is narrower than "do whatever the shell will let you do." This rule defines the read and write surfaces agents are authorized to touch, how secrets are handled, and how to respond when a task appears to require privileged access. It complements `never-touch.md` (which lists specific paths off-limits) by describing the generic posture every role takes on every task.

## Read surfaces

Agents may read, by default:

- Anything under `/product/` in the product specs repo (specs, test plans, feature descriptions).
- Anything inside the orchestration repo, subject to role scoping (the PM agent does not need to read another agent's skills, but is not prohibited from doing so).
- Anything outside generated directories in a component repo the agent is assigned to (hand-written code, tests, configuration, documentation).
- Generated directories in component repos, read-only — agents must understand generated code to reason about the consuming code, but may not modify it (`never-touch.md`).

Agents may not read, without explicit authorization:

- Anything under `/business/` in the product specs repo (architecture §4.1).
- Secrets files or the contents of environment variables known to hold secrets.
- Files outside the repositories the task identifies. If a task implies crossing into a repo the agent was not assigned to, that is an escalation condition.
- `.git/` internals (see `never-touch.md`).

## Write surfaces

Agents may write, by default:

- Their own outputs: issues they are authorized to open, PRs against branches they created, event log entries on features they touch, inbox files for escalation or cross-agent handoff, and role-specific artifacts (the QA agent writes test plans; the PM agent writes feature registry entries; the component agent writes hand-written code in its assigned repo).
- The orchestration repo's designated surfaces: `/features/`, `/events/`, `/inbox/`, `/overrides/` (with the restrictions in `override-registry.md`).
- Component repo hand-written code paths in the assigned repo.

Agents may not write to:

- Any path in the `never-touch.md` list: generated directories (except via the override protocol), branch protection configuration, secrets, `/business/`, `.git/`.
- Roles or repos outside the agent's assignment. A component agent for `acme/api` does not open PRs or modify code in `acme/mobile`.
- Schemas under `/shared/schemas/` during ordinary task execution. Schema changes are orchestration-repo-level changes, made deliberately as their own commits by a human (or by the config-steward when it is part of a coordinated change set).

## Secrets

Secrets — including API tokens, deploy keys, SSH private keys, OAuth client secrets, webhook signing secrets, database passwords, `.env` files, cloud credentials, and anything conventionally treated as a credential (see the enumeration in `never-touch.md` §3) — get a stricter posture than other restricted files:

- **Never read.** Do not open a secrets file to inspect its contents, not even "just to see the format." If a task's verification step requires reading one, stop and escalate (see below).
- **Never log.** Do not echo a secret value, print it to a command log, include it in an event payload, or describe it in an issue body. This applies whether the value was retrieved from a real secret or constructed by the agent.
- **Never commit.** Secrets files are excluded from commits categorically. A `.env` in a staging area is a mistake; remove it before committing, not after. If you discover a secret already committed, raise an escalation immediately — do not attempt remediation (history rewriting) on your own authority.
- **Reference by name, not by value.** When a command needs a secret, pass it via environment variable reference (`$GITHUB_TOKEN`) rather than substituting its value into the command line. Do not expand secret variables into log output; prefer tool invocations that read the variable themselves.
- **Do not exfiltrate.** Do not send secrets — or anything that might be a secret — to external services (web renderers, pastebins, diagnostic endpoints) even when debugging. External services cache and index input; a "deleted" paste is not deleted. This includes services marketed as secure.

Treat suspected-secret values with the same care as confirmed-secret values. A 40-character hex string is a credential until proven otherwise.

## When a task appears to require privileged access

A task whose acceptance criteria or verification steps appear to require reading a secret, writing to branch protection, editing generated code directly, or any other privileged action is almost always a task-definition problem, not a license to break the rule. Response:

1. **Stop.** Do not attempt the privileged action. Do not attempt to work around the requirement (for example, by running a command that reads the secret implicitly).
2. **Re-read the task.** Verify you have understood the step correctly. Often the task is describing how the *human* will verify, with the agent doing an upstream-only step.
3. **If the requirement is genuine, escalate.** Raise a human escalation per `escalation-protocol.md`:
   - For secret access needed by a verification step: reason `spec_level_blocker`, with the inbox file naming the specific step that requires privilege. The human either adjusts the task, runs the step, or provides a scoped credential via an out-of-band mechanism.
   - For branch protection changes: reason `spec_level_blocker`. The human makes the change; the agent does not.
   - For generated-code modification: follow the override protocol (`override-registry.md`) — escalation with reason `override_expiry_needs_review` if an existing override is the right answer, `spec_level_blocker` if the generator output needs to change.
4. **Do not report the task complete.** A verification that could not be run is not a verification; a task whose verification cannot be run is not complete (`verify-before-report.md`).

The common mistake here is to "helpfully" substitute a weaker check for a privileged one — "I couldn't run the secret-requiring verification, so I inspected the diff visually and it looks right." That is a verification-bypass, not a verification, and it produces `task_completed` events the orchestrator cannot trust.

## Authenticated tooling

Some tools the agent legitimately uses — `gh` for GitHub, `git` over SSH, package registries — rely on credentials configured on the host. Interaction with those tools is authorized without qualification: the credentials are the host's, not the agent's, and the agent is not expected to inspect or transmit them. The prohibition is on *reading the credentials themselves* and on *using them for anything outside the task's scope*, not on using a credentialed tool to do the work the task names.

If an authenticated tool returns an error that implies a credential problem (expired token, permission denied, 401/403), stop and escalate. Do not attempt to re-authenticate, reconfigure the credential, or swap accounts.

## Log hygiene

Every line an agent emits may end up in the event log, a PR description, a commit message, or a human's review screen. Treat them as public. Specifically:

- Redact suspected secrets from any command output reproduced in an issue body or event payload. If you cannot redact cleanly, do not reproduce the output — link to it instead, or describe it abstractly.
- Do not paste stack traces that include environment variables or config file contents without inspecting them first.
- Commit messages and PR descriptions are part of the eventual public product (the orchestrator is slated for open release; see `orchestrator-design-summary.md`). Write them accordingly: no customer names, no internal-only references, no leaked URLs.

## Scope creep

A task that grants a specific privilege — "you may modify the generated test harness" — grants that specific privilege, not the surrounding category. The authorization is for the scope named, not for adjacent scopes that are similar. If a task authorizes a write to a file and an adjacent change looks obvious and useful, that adjacent change is a separate task. Scope creep is how small privilege grants turn into broad ones, and it is the class of failure this rule exists to prevent.
