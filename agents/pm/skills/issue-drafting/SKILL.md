# PM agent — issue-drafting skill (v1.0)

## Purpose

This skill is the PM agent's outgoing contract with every downstream component and QA agent. It takes the approved task graph materialized by [`../plan-review/SKILL.md`](../plan-review/SKILL.md) and, for each task, drafts a work-unit issue body against [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md), opens the issue on the correct component repo, and emits the corresponding event. For tasks with no dependencies, the skill additionally flips the issue's `state:pending` label to `state:ready` and emits `task_ready` in the same pass.

The skill's core discipline is inherited — not negotiated. Every factual claim about the target component repo's state that appears in an issue body must be re-verified against the repo at drafting time, with the verification recorded on a durable surface so a reviewer reading the issue later can reconstruct what was checked and how. This is the Phase 1 retrospective's Finding 3 response to the WU 1.5 Task B failure mode: an issue whose "Out of scope" bullet excluded controller-level tests "by symmetry with the other widget endpoints" when `WidgetsControllerTests.cs` already existed on `main`, forcing an in-flight body amendment mid-task. The contract lives in [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) and must not be paraphrased away here.

## Scope

In scope:

- Reading the approved task graph from the feature registry frontmatter and the per-task work unit prompt from the plan-review file.
- Re-reading the target component repo's state at drafting time for every claim the body is about to make — no transitive trust on earlier reads in the session, including reads performed during decomposition (WU 2.2) or plan-review re-ingest (WU 2.3).
- Drafting a `work-unit-issue.md`-compliant body for each task and recording the verification evidence inline at the end of the `## Context` section.
- Performing an idempotency check against the target repo before creating any issue.
- Opening the GitHub issue with the correct title, body, and labels.
- Emitting `task_created` for every opened issue; for tasks whose `depends_on` is empty, additionally flipping the state label `pending → ready` and emitting `task_ready` in the same pass.

Out of scope (belongs to another skill or WU):

- Producing the task graph — [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) (WU 2.2).
- Drafting, re-ingesting, or approving the plan-review file — [`../plan-review/SKILL.md`](../plan-review/SKILL.md) (WU 2.3).
- Flipping `pending → ready` for tasks with one or more dependencies — [`../dependency-recomputation/SKILL.md`](../dependency-recomputation/SKILL.md) (WU 2.5). The issue-drafting skill owns the `pending → ready` flip **only** when `depends_on: []`, as a simultaneous operation with issue creation. Every other ready-flip in the feature's lifetime is WU 2.5's.
- Verifying Specfuse template coverage for any task — [`../template-coverage/SKILL.md`](../template-coverage/SKILL.md) (WU 2.6).
- Verifying claims about orchestrator-internal state (event log, feature registry, labels). Those surfaces have their own disciplines ([`verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3, the feature-frontmatter and event schemas). The `issue-drafting-spec.md` contract scopes out orchestrator-internal claims explicitly.
- Co-authoring the work unit prompt with the human. That co-authorship happens during `plan_review` in [`../plan-review/SKILL.md`](../plan-review/SKILL.md); this skill consumes the approved prompt and reshapes it into a template-compliant issue body.

## Inputs

The skill reads, in order, per task it drafts:

1. The feature registry file at `/features/<feature_correlation_id>.md` — the `task_graph` entry for the target task (`id`, `type`, `depends_on`, `assigned_repo`, optional per-task `autonomy`), plus `involved_repos` and `autonomy_default` for fallback.
2. The plan-review file at `/features/<feature_correlation_id>-plan.md` — the `### Work unit prompt` section for the target task, which is the free-form prose the issue-drafting skill reshapes into the five-section `work-unit-issue.md` structure.
3. [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) — the template whose five mandatory `##` sections the body must match. Frozen at v1; the skill does not extend it with additional top-level sections.
4. [`/shared/templates/work-unit-issue.example.md`](../../../../shared/templates/work-unit-issue.example.md) — the fully-worked example, used as a shape reference for tone and section fill.
5. [`/shared/schemas/labels.md`](../../../../shared/schemas/labels.md) — the label taxonomy (`state:*`, `type:*`, `autonomy:*`).
6. [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — the event contract. Both `task_created` and `task_ready` are already in the `event_type` enum; no schema extension is required.
7. [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) — the inherited contract. Re-read per invocation; the skill implements its §Discipline clauses literally.
8. **The target component repo, at drafting time.** This is the load-bearing re-read. The skill uses `gh` / `git` / direct filesystem reads against the freshly-fetched `main` branch of `<assigned_repo>` to resolve every claim the draft body is about to make.
9. This skill and [`../../CLAUDE.md`](../../CLAUDE.md) — re-read on every invocation per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

## Outputs

Per task drafted:

- A GitHub issue in `<assigned_repo>`, title `[FEAT-YYYY-NNNN/TNN] <summary>`, body conforming to [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) v1, labels `state:pending` (or `state:ready` for no-dep tasks) + the applicable `type:*` + `autonomy:*` entry.
- One `task_created` event appended to `/events/<feature_correlation_id>.jsonl`, validated by [`scripts/validate-event.py`](../../../../scripts/validate-event.py) with exit `0`.
- For no-dep tasks only: one `task_ready` event appended to the same log, emitted after the label flip and after re-reading the labels back.

No writes to component-repo code paths. No writes to `/product/`, `/overrides/`, or `/business/`. No other state transitions on the feature — the feature stays in whatever state the invoking pass placed it in (typically `generating` during initial issue creation).

## Inherited contract — the three Discipline clauses

Restated verbatim from [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) §Discipline as operative requirements. Each is a hard constraint on this skill; paraphrasing or weakening is forbidden.

### Per-claim verification

Every assertion in the issue body about target-repo state is paired with a verification action — a command, a file read, a grep — performed at drafting time. The action's result is captured. No claim reaches the body without a corresponding evidence item in the §Context block (see §"Evidence logging" below).

### No transitive trust

The skill does **not** infer "X is still true" from an earlier observation in the same session, even if the earlier observation is documented in the feature registry, a sibling task's body, or the plan-review file. A read performed during decomposition (WU 2.2) has already gone stale for drafting purposes: other tasks may have merged in the interim, the feature's own earlier tasks may have committed to the target repo, or an unrelated PR on the target repo may have landed. Every claim is re-verified at the drafting moment, not imported from earlier context. This clause is the direct response to the Task B session-caching failure mode.

### Reformulate-or-escalate

When a claim cannot be verified, the skill has exactly two legitimate outcomes:

1. **Reformulate** — if the claim is decorative or scope-informing and the verification is inconclusive or contradicted without being load-bearing, the skill rewrites the claim to what *is* verifiable. "The other widget endpoints also only have service-level tests" becomes "Controller-level tests exist for Widget endpoints; the new DELETE action's coverage will be asserted at controller level as well." Accuracy over elegance.
2. **Escalate `spec_level_blocker`** — if the claim is load-bearing (the task's shape depends on it; removing it changes scope) and verification contradicts it, the skill stops drafting, writes an escalation file per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md), appends a `human_escalation` event, and returns. The feature returns to `plan_review` at the human's initiative; the task is not shipped as a malformed issue.

The skill **never** papers over an unverifiable claim with a hedge. "Should be", "I think", "per convention", "typically" — none of these belong in a work-unit issue body. A claim that cannot be stated as a verified fact is removed, reformulated to what *is* fact, or escalated.

## What counts as "a claim about target-repo state"

The categories below enumerate the scope of claims the skill must verify. They are load-bearing but not exhaustive — if the body asserts something about the target repo that does not fit one of these categories, the skill still verifies it. A useful rule of thumb: any sentence whose truth value depends on the repo's current state is a claim.

| Category | Examples | Verification verb at draft time |
|---|---|---|
| **File existence / non-existence** | "`WidgetsControllerTests.cs` already exists." "There is no existing `Rate*` module." | `ls <path>` / `gh api repos/:owner/:repo/contents/<path>` |
| **Existing conventions** | "Tests live under `tests/<module>/`." "All controllers inherit from `BaseController`." | `ls` a representative sample (multiple files, not one outlier) + `grep` for the pattern |
| **File contents** | "`OrderRequestValidator` exposes a presence-check hook." "`appsettings.Production.json` does not carry credentials." | `cat <path>` or targeted `grep` on the named symbol |
| **Build / test / tooling commands** | "Coverage threshold is 0.90." "The suite runs via `pytest -x`." | `cat .specfuse/verification.yml` or the package manifest (`*.csproj`, `package.json`, `pyproject.toml`) or the CI workflow |
| **Dependency and call relationships** | "`WidgetsController` delegates to `WidgetService`." "`OrdersHandler` does not currently read from `UserRepository`." | `grep` for the symbol, scoped to the relevant directory |
| **Prior related work** | "T03 extracted the shared `OrderRequestValidator` this task hooks into." "FEAT-2026-0001 landed the quantity ceiling this task extends." | `git log` on the relevant path, `gh pr view <number>` on the named PR, or a direct read of the resulting files |

Out of scope for this skill's verification (per [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) §"What must be verified"): claims about the specs repo, the generator, or orchestrator-internal state (event log, feature registry, labels). Those are governed by their own disciplines and the issue-drafting skill does not re-validate them.

## The drafting procedure

Invoked per task, after plan approval and the feature's flip to `generating`. The procedure is a single pass through one task — for a feature with `N` tasks, the skill runs `N` times.

### Step 1 — State intent

Per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1: "I will draft and open the work-unit issue for `<feature_correlation_id>/<TNN>` on `<assigned_repo>`."

If the task's `depends_on` is empty, extend the intent: "…and flip the issue to `state:ready` on creation." Distinguishing the no-dep path from the dep-carrying path in the stated intent makes a later audit of the event log unambiguous about which skill owns which label transition.

### Step 2 — Read inputs

Read the feature registry's frontmatter and the target task's `task_graph` entry. Read the plan-review file's `### Work unit prompt` section for the target task. Re-read [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) and this skill.

**Do not** read the target component repo yet. Read it in step 4, per-claim, after the draft has been written and the claims identified. Reading it at this step would tempt the skill into session-caching target-repo state across the whole drafting pass — the pattern no-transitive-trust forbids.

### Step 3 — Draft the body against the template

Shape the §Context, §Acceptance criteria, §Do not touch, §Verification, and §Escalation triggers sections of the body from the plan-review work unit prompt, using [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) as the structural contract. Fill the YAML frontmatter block (`correlation_id`, `task_type`, `autonomy`, `component_repo`, `depends_on`, `generated_surfaces`) from the task graph entry.

As each sentence or bullet is written, **identify and enumerate** every factual claim about target-repo state it contains, per the category table above. Hold this list in working memory; it drives step 4.

### Step 4 — Per-claim verification (no transitive trust)

For every claim identified in step 3, perform its verification action against the target component repo **at this moment**. Fresh reads only — ignore observations made during decomposition, plan review, or a sibling task's drafting pass, even if they are documented in the feature registry. Capture the action (command or tool call) and the result (command output or read content) as a pair.

Concrete sequence per claim:

- Ensure the local checkout of `<assigned_repo>` is at a current `main` (or fetch fresh via `gh api` if the skill reads via API rather than a local clone).
- Issue the verification verb per category (see the table above).
- Capture the verification's `(action, result)` pair alongside the claim.

A claim whose verification fails to complete (the path is inaccessible, the command errors, the tool call times out) is not verified. Treat it as contradicted in step 5 — do not retry endlessly; three failed attempts against the same claim triggers `spinning_detected` per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md).

### Step 5 — Reconcile every claim

For each `(claim, action, result)` triple:

- **Verified and matches the draft**: keep the claim as drafted. Record the `(action, result)` pair in the evidence list (step 6).
- **Verified and contradicts the draft, claim is decorative or scope-informing**: reformulate the claim in the draft to what the verification *does* support. Re-read the reformulated sentence to confirm it no longer asserts the contradicted content. Record the `(action, result)` pair with a `**Reformulated:**` note in the evidence list.
- **Verified and contradicts the draft, claim is load-bearing**: stop. The task's shape rests on a fact that is not true. Do not attempt to reshape the task inside the skill — escalate per [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) with reason `spec_level_blocker`, file `/inbox/human-escalation/<feature_correlation_id>-<TNN>-draft-claim.md`, append a `human_escalation` event, and return. The task goes into `blocked_spec`; the feature returns to `plan_review` at the human's initiative.

A claim is **load-bearing** when removing or inverting it changes the task's acceptance criteria or scope boundary. A claim is **decorative or scope-informing** when removing or inverting it only changes the body's framing or a non-load-bearing "Out of scope" hint. If the distinction is genuinely unclear, treat as load-bearing and escalate — the cost of an over-cautious escalation is small; the cost of shipping a malformed body is the Task B incident.

### Step 6 — Append the evidence block to §Context

Append the verification log to the end of the `## Context` section, using the exact format declared in §"Evidence logging" below. This is the skill's designated durable surface per [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) §"Evidence logging" — a reviewer reading the issue later reconstructs what was verified from this block alone, without access to the drafting transcript.

### Step 7 — Idempotency check

Before opening an issue, confirm no issue already exists for this task-level correlation ID on the target repo:

```sh
gh issue list --repo <owner>/<repo> --state all \
  --search "[FEAT-YYYY-NNNN/TNN] in:title" \
  --json number,title,state
```

- **Empty result** → proceed to step 8.
- **One or more matches** → an issue already exists. Skip creation. Log the matching issue number(s) and state(s) in the drafting transcript. Do **not** emit `task_created`; do **not** emit `task_ready`. This is the normal re-run case and is not an error. Return without error.

Title-prefix uniqueness is a consequence of [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — `[FEAT-YYYY-NNNN/TNN]` is a deterministic per-task identifier, so a title-based search is sufficient. `--state all` catches issues that were opened and then closed (abandoned, duplicate) — re-opening over a closed issue is worse than a no-op skip.

### Step 8 — Open the issue

Create the issue via `gh issue create`:

```sh
gh issue create \
  --repo <owner>/<repo> \
  --title "[FEAT-YYYY-NNNN/TNN] <summary>" \
  --body-file <path-to-drafted-body.md> \
  --label state:pending \
  --label type:<implementation|qa-authoring|qa-execution|qa-curation> \
  --label autonomy:<auto|review|supervised>
```

For no-dep tasks (`depends_on: []`), pass `--label state:ready` instead of `state:pending`. The simultaneous creation with `state:ready` is the single case where the issue-drafting skill owns the flip — all other `pending → ready` transitions belong to [`../dependency-recomputation/SKILL.md`](../dependency-recomputation/SKILL.md) (WU 2.5).

Label slug mapping is fixed by [`/shared/schemas/labels.md`](../../../../shared/schemas/labels.md): `qa_authoring` → `qa-authoring`, `qa_execution` → `qa-execution`, `qa_curation` → `qa-curation`, `blocked_spec` → `blocked-spec`, etc.

### Step 9 — Re-read the issue

Immediately after creation, fetch the issue back and confirm the round-trip:

```sh
gh issue view <number> --repo <owner>/<repo> --json number,title,body,labels,state
```

Verify:

- Title matches the constructed string exactly.
- Body matches the drafted file byte-for-byte (no tool-side truncation, no encoding surprises).
- Labels include exactly one `state:*` (the intended one), exactly one `type:*`, and exactly one `autonomy:*` per [`/shared/schemas/labels.md`](../../../../shared/schemas/labels.md).
- State is `open`.

If any mismatch: do **not** emit `task_created`. Fix the mismatch (close and re-open with corrected content, or edit via `gh issue edit`) and retry the re-read. Three failed re-read cycles triggers `spinning_detected`.

### Step 10 — Emit `task_created`

Construct the event per §"Event payloads" below. Pipe through [`scripts/validate-event.py`](../../../../scripts/validate-event.py); require exit `0`. Append to `/events/<feature_correlation_id>.jsonl`. Re-read the appended line to confirm JSON integrity.

`source_version` is produced by [`scripts/read-agent-version.sh pm`](../../../../scripts/read-agent-version.sh) at emission time per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3. Never eye-cache from [`../../version.md`](../../version.md).

### Step 11 — For no-dep tasks only: `task_ready`

If `depends_on: []`:

1. Confirm the label on the just-created issue is already `state:ready` (it was set at step 8). Re-read via `gh issue view` if not already confirmed in step 9.
2. Construct the `task_ready` event per §"Event payloads" below, with `trigger: "no_dep_creation"` to distinguish this flip's provenance from the flips WU 2.5 will emit (which use a different trigger tag).
3. Pipe through `scripts/validate-event.py`; require exit `0`. Append to the event log. Re-read.

`task_created` and `task_ready` are emitted in that order; the dependency-recomputation skill's consumers rely on `task_created` as the issue-exists signal and `task_ready` as the agent-may-pick-up signal. Emitting them out of order, or emitting `task_ready` without a preceding `task_created` on the same task, is a correctness bug.

## Evidence logging — the §Context inline block

The skill's durable evidence surface is an inline prose block appended to the end of the `## Context` section of every issue body. Per [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) §"Evidence logging", the skill picks one surface and uses it consistently; silent drafting is forbidden. The choice of Context inline was made for this skill because it makes the verification visible to a reviewer reading the issue cold, without access to the drafting transcript or a separate event payload.

### Format

```
**Drafted <ISO-8601 timestamp>; verified at draft time:**

1. <claim paraphrase>: `<command or action>` → <result summary>.
2. <claim paraphrase>: `<command>` → <result summary>.
3. <claim paraphrase>: `<command>` → <result summary>. **Reformulated:** <what changed in body>.
```

### Why this surface

- **Visible at review time.** A reviewer opens the issue on GitHub, reads the §Context, sees exactly what was verified and how. No separate artifact to fetch.
- **Compatible with the frozen template.** No new `##` top-level section is added; the block lives inside the existing §Context. [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) v1 is frozen against top-level additions; any template adjustment emerging from this skill's design is explicitly deferred to the Phase 2 retrospective (WU 2.8).
- **Single surface, not mixed.** The spec requires a single designated surface. The event `task_created.payload` carries only `verification_count` (an integer metadata pointer), not the claims themselves — duplicating evidence across §Context prose and event payload would be mixed surfaces, and the spec forbids silent diffs between them.

### What does NOT belong in this block

- Claims about orchestrator-internal state. Scoped out of the spec.
- Claims the skill chose to remove entirely rather than reformulate. If a claim was cut from the body, no evidence item is needed (there is no longer a claim to evidence).
- Generic checks (schema round-trip, correlation-ID pattern). Those are universal `verify-before-report.md` checks performed by the skill and logged through the normal event emission path, not in the issue body.
- Verifications that succeeded but whose claim never made it into the body. Only claims *in the posted body* carry evidence items.

## Reformulate-or-escalate — decision tree

```
A claim about target-repo state did not verify cleanly.
│
├─ Verification contradicted the claim.
│   │
│   ├─ The claim is decorative (framing) or scope-informing
│   │   (non-load-bearing "Out of scope" hint, mention of a
│   │   related file, etc.).
│   │   → REFORMULATE. Rewrite to what the verification
│   │     supports. Record **Reformulated:** in the evidence
│   │     list. Continue.
│   │
│   └─ The claim is load-bearing. Removing or inverting it
│       changes an Acceptance criterion or a Verification command
│       or the task's scope boundary.
│       → ESCALATE `spec_level_blocker`. Stop drafting.
│         Write inbox file. Emit `human_escalation`. Return.
│
└─ Verification was inconclusive (command errored, path
    inaccessible, ambiguous output).
    │
    ├─ Three attempts already made.
    │   → ESCALATE `spinning_detected`. Stop drafting.
    │     Write inbox file. Emit `human_escalation`. Return.
    │
    └─ Fewer than three attempts.
        → Retry the verification once with a tightened
          invocation (more specific path, narrower grep).
          Count the attempt. If still inconclusive, treat as
          contradicted and apply the upper branch of this tree.
```

### Hedging is forbidden

A claim stated with "should be", "I think", "probably", "per convention", "typically", or any semantic equivalent is a hedge. Hedges mark the skill's uncertainty about a claim; the uncertainty is the signal that the claim is either unverifiable or load-bearingly contradicted. Resolving the uncertainty is the skill's job — pass through the decision tree until the claim is either verified (plain statement, no hedge) or reformulated (different plain statement) or escalated.

Task B shipped its false claim as a plain statement, not a hedge — the hedge is not the bug it primarily prevents. The hedge rule is the secondary safeguard against the same failure mode reappearing in a softer form (a pattern where the skill correctly senses the claim's fragility but ships it anyway with "should" in front).

## Idempotency check

The check runs before issue creation, once per drafting pass. It is a title-prefix search against the target repo, covering all issue states:

```sh
gh issue list \
  --repo <owner>/<repo> \
  --state all \
  --search "[FEAT-YYYY-NNNN/TNN] in:title" \
  --json number,title,state
```

### Behavior on a non-empty result

- Log the matching issue number(s) and state(s) in the drafting transcript.
- Do **not** open a new issue. Do **not** emit `task_created`. Do **not** emit `task_ready`. Do **not** touch labels on the existing issue.
- Return. This is the normal re-run outcome; the dependency-recomputation skill (WU 2.5) or a future re-planning pass will handle label drift on existing issues through its own channels.

### Behavior on an empty result

- Proceed to step 8 (open the issue).

### Why a title-based search is sufficient

Per [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md), `FEAT-YYYY-NNNN/TNN` is a globally unique task identifier, and [`orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §8 fixes the issue title prefix as `[FEAT-YYYY-NNNN/TNN]`. Two distinct tasks cannot share the prefix, and one task cannot have two compliant issues without at least one violating the uniqueness invariant. The title search relies on those invariants rather than reimplementing a separate registry.

### Why `--state all`

An issue closed as "abandoned" or "duplicate" is still an existing issue for the correlation ID. Re-opening a second issue over a closed one produces a confusing history on the repo and desynchronizes the feature's event log. The skill treats a closed match the same as an open match — skip creation — and surfaces the closed state in the transcript so the human can decide whether to re-open or abandon.

## Event payloads

Both event types are already in the `event_type` enum of [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json). The schema itself needs no extension; only the payload shapes below are declared here.

Per-type payload schemas under `/shared/schemas/events/` are explicit Phase 2+ territory (Finding 5, scheduled for WU 2.5). Until those land, the payload shapes below are documented here and must remain stable. A future per-type schema for `task_created` or `task_ready` will retro-validate against these shapes.

### `task_created`

```json
{
  "issue": "<owner>/<repo>#<number>",
  "issue_url": "https://github.com/<owner>/<repo>/issues/<number>",
  "title": "[FEAT-YYYY-NNNN/TNN] <summary>",
  "task_type": "implementation",
  "autonomy": "review",
  "component_repo": "<owner>/<repo>",
  "depends_on": [],
  "verification_count": 3
}
```

- `issue` — short form `<owner>/<repo>#<number>`, for logs and human scanning.
- `issue_url` — full URL, for tooling that wants to link out.
- `title` — the full issue title, including the `[FEAT-YYYY-NNNN/TNN]` prefix.
- `task_type` — one of `implementation`, `qa_authoring`, `qa_execution`, `qa_curation` (the canonical underscore forms from the task graph schema, not the label slug forms).
- `autonomy` — one of `auto`, `review`, `supervised`.
- `component_repo` — `<owner>/<repo>`, matching the task's `assigned_repo`.
- `depends_on` — the `depends_on` array verbatim from the task graph (possibly empty).
- `verification_count` — integer, the number of claim-verifications performed and recorded in the §Context evidence block. **Not** the list of claims itself (that lives in the §Context block, the designated single surface).

The top-level `correlation_id` field on the event is the task-level `FEAT-YYYY-NNNN/TNN`; the schema regex admits it. The payload does not duplicate the correlation ID.

### `task_ready` (no-dep case only)

```json
{
  "issue": "<owner>/<repo>#<number>",
  "trigger": "no_dep_creation"
}
```

- `issue` — same short form as `task_created`. The `issue_url`, title, and other metadata are already on the preceding `task_created` event; consumers cross-reference by the shared `correlation_id` + `issue` pair.
- `trigger` — `"no_dep_creation"` for this skill's emissions. The dependency-recomputation skill (WU 2.5) will emit `task_ready` with a different `trigger` value (e.g. `"task_completed:<TNN>"`) so the provenance of every flip is unambiguous.

`task_ready` is emitted **after** `task_created` on the same task, never before and never without. Consumers parsing the event log chronologically rely on that order.

## Verification

The skill performs the universal checks from [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3 on every emission, plus the skill-local checks below.

### Before returning from a drafting pass (issue creation path)

- Every claim in the posted body has a matching evidence item in the §Context inline block.
- The §Context evidence block is present, non-empty, and uses the format declared in §"Evidence logging".
- No hedge (`should be`, `I think`, `per convention`, `typically`, or semantic equivalent) appears in any claim in the body.
- The issue's title exactly matches `[FEAT-YYYY-NNNN/TNN] <summary>`.
- The issue's body round-trips against [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) — all five mandatory `##` sections present, no additional `##` top-level sections, YAML frontmatter complete.
- The issue carries exactly one `state:*`, one `type:*`, and one `autonomy:*` label.
- `task_created` passed `scripts/validate-event.py` (exit 0) and is the last — or second-to-last, if `task_ready` follows — line of the feature's event log.
- `source_version` on every emitted event was produced by `scripts/read-agent-version.sh pm` at emission time.
- For no-dep tasks: the issue's `state:*` label is `state:ready`; `task_ready` passed validation and is the last line of the event log; `trigger` in its payload is `"no_dep_creation"`.
- No path written is in [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md). The skill writes only to `/events/` (event log append) and indirectly to GitHub (issue creation) — neither is never-touched — but the check runs anyway per the universal discipline.
- No state-machine transition was performed on the feature. The feature stays in its invoking state (typically `generating`). Issue-level `state:ready` on a no-dep task is not a feature-level transition.

### Before returning from a drafting pass (idempotency skip path)

- The `gh issue list` search was performed and returned a non-empty result.
- Matching issue number(s) and state(s) logged in the transcript.
- No `task_created` and no `task_ready` emitted on this pass.
- No label changes on the matching issue.

### Before returning from a drafting pass (escalation path)

- The escalation file at `/inbox/human-escalation/<feature_correlation_id>-<TNN>-draft-claim.md` (or `-spinning.md` for the spinning case) was written per [`/shared/templates/human-escalation.md`](../../../../shared/templates/human-escalation.md).
- The task's GitHub issue — if one was ever created — is labeled `state:blocked-spec` (for `spec_level_blocker`) or `state:blocked-human` (for `spinning_detected`). If no issue was ever created, the task's `blocked_*` state lives only in the escalation file until the human creates it.
- A `human_escalation` event was appended to the feature's event log, payload carrying the `reason`, the inbox filename, and a one-sentence summary.
- No `task_created` or `task_ready` was emitted on this pass.

Failure handling per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable failures retry; three consecutive verification failures on the same claim → `spinning_detected`; fundamentally blocked → `spec_level_blocker`.

## Worked example — FEAT-2026-0002/T01 reconstructed

This example reconstructs how the issue-drafting skill would have drafted the real Phase 1 walkthrough Task B (`FEAT-2026-0002/T01 — Add DELETE /widgets/{id} endpoint` on `Bontyyy/orchestrator-api-sample`) with the discipline correctly applied. The original run, documented in [`/docs/walkthroughs/phase-1/task-B-log.md`](../../../../docs/walkthroughs/phase-1/task-B-log.md), shipped an "Out of scope" bullet claiming controller-level tests were excluded "by symmetry" — a claim that was false, as `WidgetsControllerTests.cs` already existed on `main`. The reconstruction below shows the skill catching that claim at step 4 (per-claim verification) and reformulating it at step 5 before posting, so the coverage-gate failure that forced the mid-task amendment never occurs.

### Input state

Frontmatter entry from `/features/FEAT-2026-0002.md`:

```yaml
task_graph:
  - id: T01
    type: implementation
    depends_on: []
    assigned_repo: Bontyyy/orchestrator-api-sample
```

(Single-repo, single-task feature. `autonomy_default: review`. `depends_on: []` → the skill owns the `pending → ready` flip in the same pass and will emit `task_ready` with trigger `no_dep_creation`.)

Work unit prompt from `/features/FEAT-2026-0002-plan.md` (approved and unchanged):

> Add a DELETE endpoint for widgets at `DELETE /widgets/{id}`. Policy A: idempotent, return `204 NoContent` on both existing-id and unknown-id; return `400 BadRequest` on blank id via the existing `ValidationException` pattern. The repository, service, and controller all get a new `DeleteAsync` method; service-level tests must cover the three cases and controller-level tests must cover the HTTP status mapping. Document policy A vs. B tradeoff in the PR.

### Step 1 — Intent

"I will draft and open the work-unit issue for FEAT-2026-0002/T01 on Bontyyy/orchestrator-api-sample, and flip it to `state:ready` on creation (`depends_on: []`)."

### Step 2 — Inputs read

Task graph entry, plan-review prompt (above), this skill, `issue-drafting-spec.md`. **Target repo not yet read.**

### Step 3 — Draft with claim enumeration

The skill shapes the body against `work-unit-issue.md`. As it drafts, it enumerates the claims about target-repo state it is about to make:

1. **Convention claim** (§Context) — the repo follows a port/adapter split: repository interfaces live in `src/OrchestratorApiSample.Application/Interfaces/`, in-memory adapters in `src/OrchestratorApiSample.Api/Persistence/`. The new `DeleteAsync` goes into both.
2. **File-existence claim** (§Acceptance criteria and §Verification) — controller-level tests already exist for Widget endpoints in `tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs`, so the new DELETE action's controller tests are added there rather than creating a new test file.
3. **Tooling-command claim** (§Verification) — the repo's verification contract declares `dotnet test` as the test-gate command and `minimum_line_coverage: 0.90` as the coverage threshold in `.specfuse/verification.yml`.

### Step 4 — Per-claim verification (fresh reads against target repo)

Three actions, each against a freshly-fetched `main` on `Bontyyy/orchestrator-api-sample`:

```sh
# Claim 1
ls src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs \
   src/OrchestratorApiSample.Api/Persistence/InMemoryWidgetRepository.cs
# → both paths present

# Claim 2
ls tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs
# → present; contains WidgetsControllerTests class with Create_* and GetById_* tests

# Claim 3
cat .specfuse/verification.yml
# → emits (among other gates):
#     tests:
#       command: "dotnet test --no-build --nologo --verbosity normal"
#     coverage:
#       command: "dotnet test --no-build --nologo --collect:'XPlat Code Coverage' ..."
#       minimum_line_coverage: 0.90
```

### Step 5 — Reconcile

- **Claim 1 — verified.** Both files present. Keep as drafted.
- **Claim 2 — verified with a twist.** The file exists (verification succeeded). But the original Phase 1 Task B operator's intent had been to *exclude* controller tests "by symmetry"; the verification here supports the claim "controller tests exist" but would contradict "symmetry excludes controller tests" if the latter had been in the draft. Since the correctly-applied discipline included "controller-level tests exist" rather than the symmetry exclusion, no reformulation is required at step 5 — the draft is already aligned with the verification. For the reconstruction, this claim's evidence item nevertheless carries a `**Reformulated:**` note, because the *contrast* with the original walkthrough's malformed body is the teaching moment: the skill is explicit about having chosen controller-test-inclusion over symmetry-based exclusion.
- **Claim 3 — verified.** Exact command and threshold match. Keep as drafted.

None of the three claims is contradicted by its verification. No escalation. No load-bearing failure. Proceed.

### Step 6 — Append evidence to §Context

```
**Drafted 2026-04-21T20:29:14Z; verified at draft time:**

1. Port/adapter split (interfaces in `Application/Interfaces/`, adapters in `Api/Persistence/`): `ls src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs && ls src/OrchestratorApiSample.Api/Persistence/InMemoryWidgetRepository.cs` → both present.
2. Controller-level tests for Widget endpoints: `ls tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs` → present, covers `Create_*` and `GetById_*`. **Reformulated:** new DELETE action adds its controller tests into the existing file rather than being excluded by symmetry; controller-level tests are in scope for this task.
3. Verification tooling: `cat .specfuse/verification.yml` → `tests.command: "dotnet test --no-build --nologo --verbosity normal"`; `coverage.minimum_line_coverage: 0.90`.
```

### Full drafted body

```markdown
---
correlation_id: FEAT-2026-0002/T01
task_type: implementation
autonomy: review
component_repo: Bontyyy/orchestrator-api-sample
depends_on: []
generated_surfaces: []
---

## Context

This task adds the `DELETE /widgets/{id}` HTTP endpoint to the sample Widget API. It is the sole task of **FEAT-2026-0002 — Widget deletion**, a single-capability feature layered on top of the existing Widget resource. Feature registry: `features/FEAT-2026-0002.md`. The repository follows a port/adapter split: `IWidgetRepository` lives in `src/OrchestratorApiSample.Application/Interfaces/`, and `InMemoryWidgetRepository` lives in `src/OrchestratorApiSample.Api/Persistence/`. `DeleteAsync` is a new method on both, plus a new action in `WidgetsController` and a new method on `WidgetService`.

Policy A (idempotent, return `204 NoContent` on both existing-id and unknown-id) is the spec'd behavior. Policy B (strict `404` on unknown-id) is the reversible alternative; the PR description documents the tradeoff per §Escalation triggers below.

**Drafted 2026-04-21T20:29:14Z; verified at draft time:**

1. Port/adapter split (interfaces in `Application/Interfaces/`, adapters in `Api/Persistence/`): `ls src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs && ls src/OrchestratorApiSample.Api/Persistence/InMemoryWidgetRepository.cs` → both present.
2. Controller-level tests for Widget endpoints: `ls tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs` → present, covers `Create_*` and `GetById_*`. **Reformulated:** new DELETE action adds its controller tests into the existing file rather than being excluded by symmetry; controller-level tests are in scope for this task.
3. Verification tooling: `cat .specfuse/verification.yml` → `tests.command: "dotnet test --no-build --nologo --verbosity normal"`; `coverage.minimum_line_coverage: 0.90`.

## Acceptance criteria

1. `DELETE /widgets/{id}` with an existing `id` returns `204 NoContent` and the widget is subsequently absent from `GET /widgets/{id}` (which returns the repository's existing missing-id response shape).
2. `DELETE /widgets/{id}` with an unknown `id` returns `204 NoContent` (policy A: idempotent). Repeated calls on the same unknown `id` return `204` indefinitely.
3. `DELETE /widgets/{id}` with a blank or whitespace `id` returns `400 BadRequest` via the existing `ValidationException` pattern, matching `GetByIdAsync`'s validation shape.
4. `IWidgetRepository` exposes a new `DeleteAsync(string id, CancellationToken ct)` method; `InMemoryWidgetRepository` implements it using `ConcurrentDictionary.TryRemove`. Both signatures match the existing port's async style.
5. `WidgetService.DeleteAsync(string id, CancellationToken ct)` mirrors `WidgetService.GetByIdAsync`'s input-validation shape and delegates to the repository.
6. `WidgetServiceTests.cs` covers the three cases (known-id delegation, unknown-id idempotence, blank-id validation) in three distinct test methods.
7. `WidgetsControllerTests.cs` covers the three HTTP status mappings (existing-id returns `NoContent`, unknown-id returns `NoContent`, blank-id returns `BadRequest`) in three distinct test methods.

## Do not touch

- Files owned by any other task in the feature graph. FEAT-2026-0002 has only T01, so this bullet is formally vacuous for this task; kept for contract symmetry with multi-task features.
- `.specfuse/verification.yml` — the verification gates are the inherited contract. A task that needs to change them is misscoped and requires `spec_level_blocker`.
- `.github/settings.yml` and any workflow declared as a required check — branch protection configuration is never touched.
- Secrets (`.env`, `*.pem`, `*.key`, `appsettings.Production.json` if it carries credentials). The sample repo does not currently carry credentials in `appsettings.Production.json`; leave the file's contents unchanged regardless.
- `.git/` internals.
- `/business/` in any product specs repo (not reachable from this repo, bullet retained for contract symmetry).

## Verification

Per-task commands, run from `Bontyyy/orchestrator-api-sample` root. These sit on top of the six mandatory gates declared in `.specfuse/verification.yml`.

```sh
dotnet test tests/OrchestratorApiSample.Tests --filter "FullyQualifiedName~WidgetServiceTests" --no-build --verbosity normal
dotnet test tests/OrchestratorApiSample.Tests --filter "FullyQualifiedName~WidgetsControllerTests" --no-build --verbosity normal
grep -F "HttpDelete" src/OrchestratorApiSample.Api/Controllers/WidgetsController.cs
grep -F "DeleteAsync" src/OrchestratorApiSample.Application/Interfaces/IWidgetRepository.cs
grep -F "TryRemove" src/OrchestratorApiSample.Api/Persistence/InMemoryWidgetRepository.cs
```

## Escalation triggers

- If, at pickup time, `IWidgetRepository` already exposes a `DeleteAsync` method, escalate `spec_level_blocker` — the task's shape assumes a fresh addition and its acceptance criteria are incoherent over an existing implementation.
- If the PR reviewer prefers policy B (strict `404` on unknown-id), implement B as a mechanical change: surface `TryRemove`'s bool return through the service, controller maps `false → NotFound()`. Document the decision in the PR description regardless of which policy lands.
- None beyond the four universal triggers in `shared/rules/escalation-protocol.md` apply otherwise.
```

### Step 7 — Idempotency check

```sh
gh issue list --repo Bontyyy/orchestrator-api-sample --state all \
  --search "[FEAT-2026-0002/T01] in:title" --json number,title,state
# → [] (empty)
```

Empty — no existing issue for this task. Proceed.

### Step 8 — Create the issue

```sh
gh issue create \
  --repo Bontyyy/orchestrator-api-sample \
  --title "[FEAT-2026-0002/T01] Add DELETE /widgets/{id} endpoint" \
  --body-file /tmp/FEAT-2026-0002-T01.md \
  --label state:ready \
  --label type:implementation \
  --label autonomy:review
# → https://github.com/Bontyyy/orchestrator-api-sample/issues/5
```

Note: `state:ready` (not `state:pending`) because `depends_on: []`.

### Step 9 — Re-read

```sh
gh issue view 5 --repo Bontyyy/orchestrator-api-sample --json number,title,body,labels,state
# → title, body, labels match. State `open`. Round-trip ✓.
```

### Step 10 — Emit `task_created`

```json
{
  "timestamp": "2026-04-21T20:30:01Z",
  "correlation_id": "FEAT-2026-0002/T01",
  "event_type": "task_created",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "issue": "Bontyyy/orchestrator-api-sample#5",
    "issue_url": "https://github.com/Bontyyy/orchestrator-api-sample/issues/5",
    "title": "[FEAT-2026-0002/T01] Add DELETE /widgets/{id} endpoint",
    "task_type": "implementation",
    "autonomy": "review",
    "component_repo": "Bontyyy/orchestrator-api-sample",
    "depends_on": [],
    "verification_count": 3
  }
}
```

Passes `scripts/validate-event.py` (exit 0). Appended to `/events/FEAT-2026-0002.jsonl`. Re-read confirms the JSON line parses.

### Step 11 — Emit `task_ready` (no-dep case)

```json
{
  "timestamp": "2026-04-21T20:30:02Z",
  "correlation_id": "FEAT-2026-0002/T01",
  "event_type": "task_ready",
  "source": "pm",
  "source_version": "1.0.0",
  "payload": {
    "issue": "Bontyyy/orchestrator-api-sample#5",
    "trigger": "no_dep_creation"
  }
}
```

Passes validation, appended, re-read.

### Contrast with the original Phase 1 Task B run

In the original run, the issue body carried this "Out of scope" bullet (paraphrasing [`/docs/walkthroughs/phase-1/task-B-log.md`](../../../../docs/walkthroughs/phase-1/task-B-log.md) §"Friction surfaced" finding 1):

> Controller-level tests. Out of scope by symmetry with the other widget endpoints, which also only have service-level tests in this repo.

That claim was false — `WidgetsControllerTests.cs` already existed and covered `Create` and `GetById`. The component agent implemented the spec'd change, hit the coverage gate at 0.8604 (below 0.90), and required an in-flight issue body amendment plus three added controller tests before closing the task.

The reconstruction above would catch the same claim at step 4:

```sh
ls tests/OrchestratorApiSample.Tests/WidgetsControllerTests.cs
# → present
```

…and apply step 5's reformulate branch (claim is scope-informing and contradicted, not load-bearing on a cancellation) to rewrite the body so controller-level tests are *included* rather than excluded. The mid-task scope correction never happens because the scope was correct at drafting time. That is the failure mode this skill prevents, and it prevents it by doing exactly what `issue-drafting-spec.md` §Discipline mandates: verify at drafting time, record the evidence on a durable surface, reformulate-or-escalate on contradiction.

## What this skill does not do

- It does **not** construct the task graph. [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) owns that.
- It does **not** re-ingest plan-file edits. [`../plan-review/SKILL.md`](../plan-review/SKILL.md) owns that.
- It does **not** verify Specfuse template coverage. [`../template-coverage/SKILL.md`](../template-coverage/SKILL.md) owns that.
- It does **not** flip `pending → ready` for tasks with non-empty `depends_on`. [`../dependency-recomputation/SKILL.md`](../dependency-recomputation/SKILL.md) owns every such flip. The no-dep case handled here is the single exception where issue creation and ready-flipping are the same operation.
- It does **not** modify [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md). The template is frozen at v1; any adjustment emerging from this skill's design is a retrospective (WU 2.8) candidate, not a silent edit.
- It does **not** modify [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md). The spec is the inherited contract; revising it requires the level of justification of a shared-rule amendment.
- It does **not** verify orchestrator-internal claims (event log, feature registry, labels). The spec scopes those out.
- It does **not** author the work unit prompt. The plan-review skill (WU 2.3) co-authors the prompt with the human during `plan_review`; the issue-drafting skill reshapes the approved prompt into a template-compliant body.
- It does **not** flip feature state. Feature state is unchanged across any drafting pass; the invoking actor (typically the `plan_approved → generating` flow) sets feature state before this skill runs.
- It does **not** close issues, comment on issues, or re-open closed issues on idempotency skip. The idempotency skip is silent and non-destructive.

## References

- [`../../issue-drafting-spec.md`](../../issue-drafting-spec.md) — the inherited contract this skill implements. Authored in WU 1.9; re-read per invocation.
- [`/docs/walkthroughs/phase-1/task-B-log.md`](../../../../docs/walkthroughs/phase-1/task-B-log.md) §"Friction surfaced" finding 1 — the originating incident (symmetry assertion proved false mid-task).
- [`/docs/walkthroughs/phase-1/retrospective.md`](../../../../docs/walkthroughs/phase-1/retrospective.md) §"Finding 3" — the retrospective decision to fix in Phase 1 via a forward spec, then implement in Phase 2.
- [`/shared/templates/work-unit-issue.md`](../../../../shared/templates/work-unit-issue.md) — the frozen v1 template this skill produces bodies against.
- [`/shared/templates/work-unit-issue.example.md`](../../../../shared/templates/work-unit-issue.example.md) — fully-worked template example, referenced for shape and tone.
- [`/shared/schemas/labels.md`](../../../../shared/schemas/labels.md) — the label taxonomy (`state:*`, `type:*`, `autonomy:*`) this skill applies.
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — event contract; `task_created` and `task_ready` already in the enum.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) — universal four-step discipline; §3 carries the per-emission event and version-read checks this skill inherits.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally at the start of every invocation.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation surface used on step 5's escalate branch.
- [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — the `FEAT-YYYY-NNNN/TNN` format the title-prefix search relies on.
- [`../task-decomposition/SKILL.md`](../task-decomposition/SKILL.md) — upstream skill whose task graph this one consumes.
- [`../plan-review/SKILL.md`](../plan-review/SKILL.md) — upstream skill whose approved work unit prompts this one reshapes.
- [`../dependency-recomputation/SKILL.md`](../dependency-recomputation/SKILL.md) — downstream skill that owns every non-creation `pending → ready` flip.
- [`../template-coverage/SKILL.md`](../template-coverage/SKILL.md) — sibling skill that runs before plan approval and is therefore not in the issue-drafting pass.
- [`../../CLAUDE.md`](../../CLAUDE.md) — PM role config that orchestrates this skill alongside its siblings; the "Role-specific verification" clause names this skill as the place the inherited contract is implemented.
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 2.4 — Issue-drafting skill" — the work unit that authored this skill.
