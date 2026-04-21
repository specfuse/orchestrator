# Component agent — PR submission skill (v1)

## Purpose

This skill defines how the component agent produces its outgoing delivery artifact — the pull request — with the correlation-ID discipline, commit structure, and PR shape the orchestrator depends on. It governs the span from "verification is green, ready to deliver" to "PR is open and the task is in `in_review`."

Merge itself is out of scope: the merge watcher (a GitHub Action, not an agent) owns `in_review → done` gated on branch protection (architecture §10). The component agent never merges its own PRs.

## Entry condition

Before this skill runs, the [verification skill](../verification/SKILL.md) must have produced a green overall result. A PR opened ahead of green verification is a trust-model regression — see anti-pattern 2 in [`../../CLAUDE.md`](../../CLAUDE.md#anti-patterns). If verification failed, the correct next skill is [`../escalation/SKILL.md`](../escalation/SKILL.md), not this one.

## Branch naming

The branch the agent delivers on follows the convention in [`correlation-ids.md`](../../../../shared/rules/correlation-ids.md):

```
feat/FEAT-YYYY-NNNN-TNN-<slug>
```

- `feat/` is the literal prefix. Use it even when the task is a fix or refactor — the prefix denotes "feature-driven work unit," not change category. The change category lives in the conventional-commit headline (below).
- `FEAT-YYYY-NNNN-TNN` is the task-level correlation ID with the `/` replaced by `-` for git-ref safety. The `/` is reconstructible because the ID format is fixed.
- `<slug>` is a kebab-case short summary (3–6 words) of the task. It is human-readable context, not part of the machine contract — the correlation ID is the identity.

Examples:

- `feat/FEAT-2026-0042-T07-orders-validation`
- `feat/FEAT-2026-0003-T01-add-auth-middleware`

Branches that do not match this pattern are malformed and will not thread correctly through the event log. If an agent finds itself about to push a non-conforming branch, it stops and escalates with `spec_level_blocker` rather than renaming mid-flight (renaming a pushed branch invalidates the PR URL and can lose review history).

## Commit structure

### Headline

Conventional Commits shape:

```
<type>(<scope>): <imperative summary>
```

- `<type>` is one of `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `perf`, `build`, `ci`. The agent picks the type that best describes the commit's net effect.
- `<scope>` is optional. When present, it names the component area (e.g., `feat(api): ...`, `fix(auth): ...`). Not the repo name — the repo is implicit.
- `<imperative summary>` is a short imperative phrase (no trailing period), under 72 characters.

The headline is for humans scanning git log. It is not the correlation thread — that lives in the trailer.

### Body (optional)

Prose explaining the **why**, not the what. Omit when the headline and diff together already make the why obvious. Never narrate the task or reference the agent — those belong in the PR description.

### Trailer (mandatory)

Every commit on the feature branch — including verification-cycle correction commits — carries:

```
Feature: FEAT-YYYY-NNNN/TNN
```

This trailer is how the correlation thread follows the commit into the merge commit and, via `git log --grep`, into retrospective queries. The trailer format matches the pattern in [`correlation-ids.md`](../../../../shared/rules/correlation-ids.md) exactly; a malformed trailer breaks the thread.

### Full commit example

```
feat(api): reject POST /orders with missing email

Bring POST /orders in line with OpenAPI spec: respond 400 when the
request body lacks `email` instead of silently coercing to null and
400-ing later on persistence constraint.

Feature: FEAT-2026-0042/T07
```

### Correction commits during verification cycles

When a verification cycle fails and the agent corrects its own change (see [`../verification/SKILL.md`](../verification/SKILL.md) §"Failure handling"), the correction commit uses:

- `<type>` matching the net effect of the correction (often `fix` within the same feature).
- A headline that names the correction, not "fix verification" or "cycle 2."
- The same `Feature:` trailer.

Do **not** amend the original commit to hide the cycle. The history is part of the audit trail.

## PR title

The PR title mirrors the commit headline of the commit that delivers the task's value (typically the first or primary commit). It does **not** repeat the correlation ID — the ID goes in the description. The result is a PR title that reads as a clean conventional-commit line, which the merge commit can then adopt verbatim on squash-merge.

Examples:

- `feat(api): reject POST /orders with missing email`
- `refactor(persistence): extract OrderRow mapper`

## PR description

The description is a stable shape the skill produces top-down:

```markdown
FEAT-YYYY-NNNN/TNN

## Summary

<one short paragraph: what changed and why it is the right next step>

## Task

- Issue: <owner/repo>#<N>
- Feature: [FEAT-YYYY-NNNN](<link to feature registry entry if known>)

## Verification

All six mandatory gates passing. Evidence in the `task_completed`
event payload on the orchestration repo's `/events/FEAT-YYYY-NNNN.jsonl`.

- tests: pass
- coverage: <value> (threshold 0.90)
- compiler_warnings: pass (0 warnings)
- lint: pass
- security_scan: pass (0 high, 0 critical)
- build: pass

## Spec issues raised during execution

<bulleted list of spec-issue links filed during the task, or "none">

## Overrides applied

<bulleted list of override records touched during the task, or "none">
```

Field semantics:

- **First line** — the task-level correlation ID on its own line, no markdown decoration. Tooling that greps PR bodies for correlation IDs relies on this placement (per [`correlation-ids.md`](../../../../shared/rules/correlation-ids.md) §"Where correlation IDs must appear").
- **Summary** — present-tense, factual, one paragraph. Not a changelog; the diff is the changelog.
- **Task** — links back to the issue and, when known, the feature registry. These links are how a human reviewer reaches the upstream context cold.
- **Verification** — a compressed echo of the `task_completed` payload. Detailed evidence stays in the event log; the PR surface carries the summary a reviewer reads before diving in.
- **Spec issues raised** — mandatory section, with "none" written out explicitly when empty. An unfilled section reads as "I skipped this," which is not the truth.
- **Overrides applied** — same shape and same "none" discipline.

The description does not contain: agent narration ("I implemented..."), attributions to tooling, caveats that belong in the task escalation path, or any secret-looking value.

## The `in_progress → in_review` transition

The transition happens **at the same logical moment** as the PR being opened. Order of operations:

1. Push the branch to `origin` (with upstream tracking).
2. Open the PR via `gh pr create` or equivalent, using the title and description above.
3. Rotate the task issue's label: remove `state:in-progress`, add `state:in-review`.
4. Append a `task_completed` event to `/events/FEAT-YYYY-NNNN.jsonl` with the payload shape from [`../verification/SKILL.md`](../verification/SKILL.md) §"Reporting", including the `pr_url` returned by step 2.
5. Stop.

Steps 2, 3, and 4 are a logical unit. The event is the durable record of the handoff; the label is what other agents filter on; the PR is what the human reviews. If any one of the three fails to land, the task is in an inconsistent state and the agent escalates with `spec_level_blocker` — it does not retry partially-applied transitions on its own.

The `task_completed` event marks this role's handoff point. Dependency recomputation (done by the PM agent) flips downstream `pending` tasks to `ready` on the strength of this event, so the payload must be accurate.

## Anti-patterns specific to PR submission

These overlap with the role-wide anti-patterns in [`../../CLAUDE.md`](../../CLAUDE.md#anti-patterns) but deserve restatement at the PR boundary because it is where they most often surface:

- **Opening a PR before verification is green.** Re-read [`../verification/SKILL.md`](../verification/SKILL.md) §"Failure handling"; the correct path is correction cycle → escalation, never PR.
- **Pushing with `--force` on a shared branch.** The agent's feature branch is its own; within-task force-push to reshape commits is acceptable if the branch has not yet been reviewed. Never force-push after a reviewer has commented — that rewrites the review target under their feet.
- **Amending a commit to hide a verification cycle.** The cycle is part of the audit trail.
- **Omitting the `Feature:` trailer on a correction commit.** Every commit on the branch carries it — no exceptions.
- **Filing the PR against a branch other than the repo's default target.** Unless the task issue explicitly names a non-default target (rare; usually a release-branch scenario), the PR targets the default branch.
- **Self-approving or self-merging.** The component agent does neither. Reviewers are humans (or, later, a QA agent for specific task types); merge is the merge watcher's transition.

## Worked example

Task `FEAT-2026-0042/T07` adds the email validation described earlier. The agent has just finished verification with the full six gates green.

1. Branch name: `feat/FEAT-2026-0042-T07-orders-email-validation`. The `/` in the correlation ID became `-`.
2. Commits on the branch:
   - `feat(api): reject POST /orders with missing email` + body + `Feature: FEAT-2026-0042/T07`.
   - `fix(api): handle empty string email distinctly from missing` + `Feature: FEAT-2026-0042/T07` (this was the verification cycle-1 correction; it is kept in history).
3. `git push -u origin feat/FEAT-2026-0042-T07-orders-email-validation`.
4. `gh pr create` with:
   - Title: `feat(api): reject POST /orders with missing email`.
   - Body: the shape in §"PR description" above, first line `FEAT-2026-0042/T07`, Summary one paragraph, Task pointing at the task issue, Verification echoing the green gates, "Spec issues raised: none", "Overrides applied: none".
5. Label rotation on the task issue: `state:in-progress` → `state:in-review`.
6. Event append on `/events/FEAT-2026-0042.jsonl`: `task_completed`, source `component:api`, payload containing `pr_url`, `branch`, and the `verification` object with all six gates `pass`.
7. Stop.

From here, the human reviewer works against the PR. If they request changes, the task stays in `state:in-review`; the agent may continue pushing correction commits on the same branch (each with the `Feature:` trailer) until the reviewer approves and the merge watcher closes the loop.

## Version

- `1.0` — Phase 1 initial.
