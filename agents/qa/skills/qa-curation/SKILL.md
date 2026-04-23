# QA agent — qa-curation skill (v1.0)

## Purpose

This skill maintains the regression test suite under `/product/test-plans/` in the product specs repo against unbounded growth. It does three kinds of structural work on the plan corpus, each proposed through a reviewable PR and never through destructive inline edits:

- **Dedup** — detect tests whose `covers` fields overlap on the same acceptance-criterion fragment and merge them into one.
- **Retire orphans** — detect tests whose `covers` cites an acceptance-criterion fragment that has been removed from the feature spec and propose retirement.
- **Consolidate by failure pattern** — detect tests that co-fail on the same `qa_execution_failed` events with high frequency and surface them as consolidation candidates.

It enforces the **open-regression protection rule** codified in [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification" and §"Anti-patterns" #7: a test whose `test_id` has an open `qa_regression_filed` event without a matching `qa_regression_resolved` is never retired, renamed, or consolidated away. The refusal is a deliberate safety-check outcome recorded in the merged PR's `regression_suite_curated` payload, not a silent skip.

The skill also handles **`test_id` renames** (forward-referenced from [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) §"Step 5" and §"What this skill does not do") by modeling them as "retire-old + add-new" for protection purposes. This preserves the `test_id` stability contract qa-regression relies on without introducing an event-log-patching mechanism at v1.

It is the last skill in the Phase 3 QA pipeline. Its siblings (`qa-authoring`, `qa-execution`, `qa-regression`) operate on a single feature per invocation; this skill operates on the suite as a whole and has two invocation modes (drafting and post-merge) rather than one.

## Scope

In scope:

- Scanning `/product/test-plans/*.md` in the product specs repo for dedup, orphan, and consolidation candidates within a bounded scan budget (see §"Scan budget discipline").
- Reading every affected feature's event log (`/events/<feature>.jsonl`) end-to-end to apply the open-regression protection per candidate.
- Proposing the curation changes as a single PR against the product specs repo on a branch named `qa-curation/<qa_curation_task_correlation_id>`. The PR body is a human-readable curation report; the plan file diff is the machine-readable deliverable.
- Flipping the `qa_curation` task's label `state:in-progress → state:in-review` when the PR is opened.
- On the PR's merge (detected externally; see §"Trigger — external invocation"), emitting `regression_suite_curated` to `/events/<feature_of_qa_curation_task>.jsonl` with the envelope `correlation_id` task-level on the `qa_curation` task and `affected_feature_correlation_ids[]` in the payload carrying the cross-feature fanout.

Out of scope (each belongs to a sibling skill, a later phase, or another role):

- **Authoring test plans from scratch** — [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md), WU 3.2.
- **Running test plans** — [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md), WU 3.3.
- **Filing and resolving regressions** — [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md), WU 3.4. This skill reads the `qa_regression_filed` / `qa_regression_resolved` event pairs that skill produces for the open-regression protection check; it does not emit either.
- **Transitioning the `qa_curation` task to `done`.** `in_review → done` belongs to the merge watcher on the task issue's repo (architecture §6.3). The qa-curation skill emits the curated event and stops; the merge watcher closes the task separately.
- **Minting task-level correlation IDs.** The `qa_curation` task's correlation ID is minted by the PM agent during task decomposition (WU 2.2); this skill only consumes it.
- **Writes to any implementation task, to any component-repo code path, to `/product/` outside `/product/test-plans/`, or to `/overrides/`.** The single-owner state invariant (architecture §6.3) and the "Output artifacts" section of [`../../CLAUDE.md`](../../CLAUDE.md) forbid all of these.
- **Machine-learning-based clustering, cross-repo static analysis, or embedding-similarity grouping.** Phase 4+ — see §"Deferred integration".

## Inputs

Per invocation (either mode):

1. The `qa_curation` task's correlation ID (`FEAT-YYYY-NNNN/TNN`) from the invoker. In drafting mode, this is the task the skill picks up; in post-merge mode, this is the task whose PR just merged, passed to the skill by the merge-detection mechanism.
2. The `/product/test-plans/*.md` corpus in the product specs repo. The skill reads plan files fresh each invocation; no caching across invocations.
3. The `/features/FEAT-YYYY-NNNN.md` registry files in the orchestration repo for every feature whose plan is in the scan cohort (read for `## Acceptance criteria` and the task graph's `assigned_repo` mapping used to locate event logs).
4. The `/events/FEAT-YYYY-NNNN.jsonl` event logs for every feature whose plan is in the scan cohort. Read **end-to-end, fresh per candidate**, for the open-regression protection check and the failure-pattern clustering inputs. No cached snapshots per anti-pattern #12.
5. [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — the plan file frontmatter schema the skill reads and validates the proposed diff against.
6. [`../../CLAUDE.md`](../../CLAUDE.md), this skill, and [`/shared/rules/`](../../../../shared/rules/) — reloaded per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

The skill does **not** read component-repo code, does **not** open GitHub issues, and does **not** write to any path outside `/product/test-plans/*.md` (on a branch in the specs repo) and `/events/<feature>.jsonl` (in the orchestration repo).

## Outputs

Per invocation, depending on mode:

### Drafting mode

- A new branch `qa-curation/<qa_curation_task_correlation_id>` in the product specs repo (e.g. `qa-curation/FEAT-2026-0070-T05`).
- A PR against the specs repo's `main` branch containing the proposed diffs to one or more `/product/test-plans/FEAT-YYYY-NNNN.md` files. Ready for review (not a draft PR).
- A PR body formatted as a **curation report**: one section per candidate (accepted or refused), with rationale, evidence, and for consolidation candidates a co-failure table. The curation report is the human's review surface.
- One GitHub label rotation on the `qa_curation` task issue: `state:in-progress` removed, `state:in-review` added.
- One `task_started` event (on task pickup) and one `task_completed` event (on successful PR open) on the qa_curation task's feature event log, both with task-level correlation ID. Standard QA-task-lifecycle events per [`../../CLAUDE.md`](../../CLAUDE.md) §"Output artifacts".
- If the scan returns no candidates (or all candidates are refused), a no-op PR is not opened; the skill emits `task_completed` with a payload summary and flips the task to `state:in-review` with an empty-curation rationale in the task issue's comment trail. `regression_suite_curated` is not emitted (no PR to merge).

### Post-merge mode

- One `regression_suite_curated` event appended to `/events/<feature_of_qa_curation_task>.jsonl`, with envelope `correlation_id` task-level on the qa_curation task and payload per [`events/regression_suite_curated.schema.json`](../../../../shared/schemas/events/regression_suite_curated.schema.json).
- No label writes. No transitions. The merge watcher owns `in_review → done` on the qa_curation task issue.

No writes to any other task, no writes to feature frontmatter, no writes to component-repo code paths, no writes to `/overrides/`, no writes to `/product/` outside `/product/test-plans/`. Every event round-trips through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) before append; every file written on the curation branch is re-read after write per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3.

## Trigger — external invocation

The skill exposes two procedures; the trigger-detection mechanism for each is **outside this skill**, same posture as [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) §"Trigger — external invocation" and [`../../../pm/skills/dependency-recomputation/SKILL.md`](../../../pm/skills/dependency-recomputation/SKILL.md) §"Trigger — external invocation".

### Drafting-mode trigger

A `qa_curation` task reaches `state:ready`. Candidate invokers (any acceptable, deployment choice):

- A polling loop that lists GitHub issues with the `type:qa_curation` and `state:ready` labels across the orchestration repo's declared component repos, and calls the skill on the first one it finds idle.
- A CLI (`scripts/run-qa-curation.sh <feature_correlation_id>/<TNN>`) the human runs to kick off a curation pass.
- A scheduled cron that runs the skill's drafting mode on a fixed cadence (weekly, monthly) regardless of whether any `qa_curation` task is open — would require the invoker to mint the task first via the PM agent.

The skill takes one input from the invoker: the qa_curation task's correlation ID. It re-reads everything else from the filesystem.

### Post-merge-mode trigger

A PR on the product specs repo whose branch name matches `^qa-curation/FEAT-\d{4}-\d{4}-T\d{2}$` has been merged into main. Candidate invokers:

- A GitHub webhook on `pull_request.closed` with `merged == true` on the specs repo, routed to the skill when the branch name matches the pattern.
- A polling loop tailing recent merges across repos the orchestrator watches.
- A CLI (`scripts/emit-regression-suite-curated.sh <merged_pr_url>`) the human runs after approving and merging a curation PR.

The skill takes two inputs: the qa_curation task's correlation ID (derivable from the branch name) and the merged PR's URL.

### Cross-repo linkage caveat

The qa_curation task issue lives in a component repo (per `assigned_repo` in the feature's task graph), but the curation PR lives in the product specs repo. The merge watcher that transitions the task issue's `in_review → done` must observe merges on the specs repo and match them to the qa_curation task via the branch name convention or an explicit `Closes clabonte/api-sample#<N>` line in the PR body. The effective configuration — which mechanism the deployment uses — is **deferred** to the Phase 3 walkthrough (WU 3.6) and retrospective (WU 3.7); this skill documents the invariant and leaves the wiring detail to the merge-watcher implementation.

The skill does not schedule itself, does not poll, and does not persist state across invocations — every invocation reads the plan corpus, the feature registries, and the event logs fresh.

## Scan budget discipline

**Threshold: 50 plan files per drafting pass.** Priority: ascending by the plan file's last-modified time (git log `-1 --format=%at`) — the stalest plans scanned first.

Rationale:

- A pass reading 50 plans at an average of ~10 tests each is ~500 test entries. Tractable within a single agent session's token budget, including per-candidate event-log reads.
- **Stalest-first ordering** is the staleness proxy: a plan not touched in months is more likely to have drifted from its feature's current spec (orphan-coverage probability grows with age). A plan touched last week has just been re-authored by qa-authoring and is the least likely to contain orphans.
- When the suite exceeds 50 plans, this pass handles the 50 stalest; the next `qa_curation` task pickup captures the new stalest cohort by the same rule (`mtime` changes naturally as plans are touched). No cursor to persist.

**Why not larger (e.g., 100 or the full corpus):**

- Failure-pattern clustering is O(n²) on the number of distinct `test_id`s observed in `qa_execution_failed` events; doubling the cohort quadruples the per-candidate comparison work. The 50-plan threshold keeps the clustering step tractable in a single session.
- Per-candidate event-log reads scale with both cohort size and per-feature event-log length. A 100-plan cohort against suites with long event-log history blows past token budgets within one session.

**Why not smaller (e.g., 10 or 20):**

- A single feature can have 10+ tests; a cohort of 10 plans is too narrow to surface cross-feature consolidation opportunities, which is the main reason curation exists at the suite level rather than at the plan level.
- Dedup and orphan detection benefit from seeing a diverse cohort. 20-30 plans is below the threshold where orphan hit-rate becomes meaningful for a realistic open-source adopter.

**Time / token bounds rejected as alternatives.** They are non-deterministic under replay: the same invocation with the same inputs can produce different cohorts depending on token-counting heuristics or wall-clock jitter. The plan-count cap is deterministic and greppable in §"Verification" below.

**Phase 4+ tuning.** The threshold is ajustable based on walkthrough (WU 3.6) and retrospective (WU 3.7) evidence. Cross-plan fingerprinting, a cursor-backed incremental scan, and priority schemes beyond `mtime` (e.g., weighted by feature's recent failure density) are Phase 4 candidates. See §"Deferred integration".

## The curation procedure (drafting mode)

### Step 1 — State intent and reload hygiene

Per [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1, state the intent: "I will curate the regression suite on behalf of `<qa_curation_task_correlation_id>`." Reload [`/shared/rules/*`](../../../../shared/rules/), this skill file, and [`../../CLAUDE.md`](../../CLAUDE.md) per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — unconditional.

Flip the qa_curation task's label `state:ready → state:in-progress` (role-owned transition per [`../../CLAUDE.md`](../../CLAUDE.md) §"Entry transitions owned") and emit `task_started` on the feature event log with task-level correlation ID.

### Step 2 — Enumerate the scan cohort

List `/product/test-plans/*.md` in the product specs repo. Sort ascending by last-modified timestamp (`git log -1 --format=%at -- <path>`, falling back to the filesystem mtime if the file is unstaged — unstaged curation branches should not exist at this point, but the fallback keeps the sort robust). Take the first 50.

If the corpus has fewer than 50 plans, take all of them. The scan-cohort size is recorded in `scan_summary.plans_scanned` of the emitted event (post-merge mode).

### Step 3 — Classify candidates

For each plan file in the cohort, read it fresh (no caching across plan files) and parse the YAML frontmatter against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json). A plan that fails schema validation is an upstream drafting bug — log the failure, skip the plan (do not attempt to correct it), and continue; do **not** escalate, the broken plan will surface through qa-execution or the specs repo's own lint.

Scan the parsed plans for four kinds of candidate:

- **Dedup candidate.** Two tests within the same plan OR across two plans whose `covers` strings share a common AC identifier substring (`AC-N` pattern) and cover the same operation or behavior. The skill surfaces the pair and proposes merging into the one with the earlier `test_id` alphabetically, union-ing the `commands` and preserving the richer `expected` predicate (the longer of the two, by character count — deterministic tiebreaker).
- **Orphan candidate.** A test whose `covers` string cites an AC fragment (by `AC-N` identifier or by quoted substring match against the feature's `## Acceptance criteria` section) that **no longer appears** in the current feature registry file at `/features/<feature>.md`. The feature registry is the SOT for AC; if the AC has been edited or removed, the test's coverage is orphaned.
- **Consolidation candidate.** A pair of `test_id`s (possibly across features) whose co-failure count in recent `qa_execution_failed` events meets the failure-pattern clustering threshold (see §"Failure-pattern clustering"). Surfaced as a proposal for human review — the skill does not auto-merge consolidation candidates.
- **Rename candidate.** A test whose current `test_id` violates a newer naming convention or was flagged as badly-named in prior walkthrough notes (v1: only explicit rename requests embedded in `## Coverage notes` prose under the frontmatter trigger this — e.g., a prose line `rename-request: old-id → new-id`). Modeled internally as "retire-old + add-new" for the open-regression protection check. v1 has no automatic rename-detection heuristic; rename candidates appear only on explicit request.

Each candidate records: the candidate kind, the affected `test_id`(s), the affected `feature_correlation_id`(s), and the evidence (AC fragment, co-failure counts, `covers` overlap span, rename-request line).

### Step 4 — Open-regression protection per candidate

For each candidate, before drafting its diff into the PR, run the protection check:

**4.1 — Enumerate the `test_id`s being retired or renamed.** For a dedup or consolidate candidate, the merged-away test_ids are "retired" from the pair's perspective (the merged-into test_id survives). For an orphan candidate, the test_id is retired. For a rename candidate, the old test_id is retired (the new test_id is added).

**4.2 — For each retired test_id, for each feature whose plan contains it:**

1. Read `/events/<feature>.jsonl` end-to-end, fresh. No caching across candidates — even for the same feature scanned multiple times in one pass, the read is re-issued per candidate to preserve the anti-pattern #12 posture against cached event-log snapshots.
2. Collect every `qa_regression_filed` entry where `payload.test_id == <retired test_id>`. (The payload's `implementation_task_correlation_id` is irrelevant to curation — a retirement kills the test regardless of the impl task it was regressing against; `test_id` uniqueness within a feature's plan, enforced by qa-authoring, means `(feature, test_id)` is the unambiguous protection key.)
3. For each filed entry, check for a matching `qa_regression_resolved` entry on the same feature event log where both (a) `payload.test_id` matches and (b) `payload.filed_event_ts` equals the filed entry's timestamp.
4. The **open set** for this test_id on this feature = filed entries without a matching resolved entry.

**4.3 — Decide:**

- **Empty open set across every feature the retired test_id appears in** — the candidate proceeds to the PR draft.
- **Non-empty open set on any feature** — the candidate is **refused**. Record a `refused_candidates[]` entry: `{test_id, feature_correlation_id, reason}` with `reason` quoting the filed event's timestamp and the implementation task from its payload (e.g. `"open qa_regression_filed at 2026-04-23T18:44:00Z on FEAT-2026-0061/T02 without matching qa_regression_resolved"`). The refusal is logged in the PR's curation report under a dedicated **## Refused candidates** section; other candidates in the pass continue normally.

A refusal is **not** an escalation. It is expected safety-check behavior and does not block the pass. The refused test_id becomes retireable automatically in a future pass once the open regression resolves; no manual intervention needed to unblock.

**Cross-feature retirement.** A consolidation candidate spanning two features retires test_ids on both plan files. The protection check runs against **both** feature event logs; the candidate is refused if **either** has an open regression on **its** retired test_id. This is conservative: a candidate may be refused even when only one half of the consolidation is blocked. Alternative (allow half-consolidation) was rejected — partial consolidation would leave the surviving half pointing at a test_id that no longer exists in the source plan, breaking downstream qa-regression backlinks.

### Step 5 — Classify candidates that survived protection into scope

Once Step 4 has filtered the candidate list, the surviving candidates determine the PR's `scope` field:

- Exactly one kind (all dedup, all orphan, all consolidate, all rename) → `scope` = that kind.
- More than one kind → `scope: "mixed"`.
- Zero surviving candidates → no PR; skip to Step 7 "empty-curation" branch.

### Step 6 — Draft the curation PR

1. Create the branch `qa-curation/<qa_curation_task_correlation_id>` in the specs repo, branching from `main`'s current HEAD. Branch-name format is the task correlation ID with `/` replaced by `-` (e.g. `qa-curation/FEAT-2026-0070-T05`).
2. Apply the diffs for every surviving candidate to the affected plan files. For each diff:
   - Dedup / consolidate: remove the merged-away `tests[]` entries, add/update the merged-into entry with unioned `commands` and the preserved `expected`. The merged-into `covers` field becomes a concatenation of both sources (`; `-joined) so traceability to the original AC fragments is preserved.
   - Orphan: remove the retired `tests[]` entry. If removing brings the plan's `tests[]` array to length 0 (the feature has no remaining tests), **do not delete the plan file** — leave `tests[]` empty; plan-file retirement is a separate concern (Phase 4+).
   - Rename: replace the old `test_id` with the new one, unchanged `covers` / `commands` / `expected`.
3. Re-validate each modified plan file's frontmatter against [`test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json). A failed validation means the diff was malformed — roll back the change on that plan file, record the candidate as refused (with `reason: "schema validation failed on candidate's target plan"`), and continue.
4. Compose the PR body as a structured curation report with these sections:
   - **## Summary** — one line naming the scope and the count of accepted vs. refused candidates.
   - **## Accepted candidates** — one subsection per accepted candidate, with kind, affected test_ids, affected features, rationale, and (for consolidate) the co-failure evidence table.
   - **## Refused candidates** — one subsection per refused candidate, with kind, affected test_id, affected feature, and the refusal reason quoting the blocking filed event.
   - **## Scan summary** — plans scanned, regression events consulted, wall-clock duration (informational).
   - **## How to review** — one short paragraph pointing the human at the plan-file diff and at the per-candidate rationale.
5. Open the PR against `main`. Include `Closes <orchestration_repo_owner>/<qa_curation_task_repo>#<N>` in the body so the merge watcher can match the PR to the qa_curation task issue.
6. Flip the qa_curation task's label `state:in-progress → state:in-review` (role-owned transition).
7. Emit `task_completed` on the qa_curation task's feature event log with task-level correlation ID. Payload shape inherited from the Phase 1 baseline (`{issue: "<owner>/<repo>#<N>"}`; no per-type schema required — the bare envelope is sufficient).

### Step 7 — Empty-curation branch

If Step 5 produced zero surviving candidates:

1. Do **not** open a PR, do **not** create a branch. An empty PR is noise on the specs repo and on the merge watcher.
2. Add a comment to the qa_curation task issue describing the pass: "Curation pass complete. 0 accepted candidates, N refused (enumerated below). Scan covered <plans_scanned> plans." The comment is the human-visible record; the event log is the machine record.
3. Flip the qa_curation task's label `state:in-progress → state:in-review`. The merge watcher (or the human) will `in_review → done` the task issue without a PR to watch — a special case documented in the cross-repo linkage caveat above.
4. Emit `task_completed` on the feature event log, same shape as Step 6 sub-step 7 but with `payload: {issue: "<owner>/<repo>#<N>", empty_curation: true}` (additive field, no per-type schema required — envelope-only).
5. **No `regression_suite_curated` event is emitted** on the empty-curation branch. The event signals "a curation PR landed"; with no PR, there is nothing to signal.

## The post-merge procedure

### Step PM.1 — State intent and reload hygiene

"I will emit `regression_suite_curated` for the merged curation PR `<pr_url>` on behalf of `<qa_curation_task_correlation_id>`." Reload rules per [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md).

### Step PM.2 — Read the merged PR's diff

Use `gh pr view <pr_url> --json files,mergeCommit,body,state` or equivalent. Confirm:

- `state == "MERGED"`. A not-yet-merged PR routed to this mode is an invoker bug — return an error to the invoker, emit nothing.
- The PR's merge commit SHA is resolvable on the specs repo's `main` branch (`git log --format=%H main` contains it).
- The PR's changed files are all under `/product/test-plans/`. A PR with files outside that path is suspicious — log and emit nothing; the invoker matched a non-curation PR to this skill.

Parse the PR body's curation report sections to recover the skill's own prior decisions: accepted candidates, refused candidates, scan summary. The PR body is the authoritative record of what the drafting mode emitted; re-deriving from the diff alone loses the refused-candidates record.

### Step PM.3 — Idempotence check

Read `/events/<feature_of_qa_curation_task>.jsonl` end-to-end, fresh. If a `regression_suite_curated` event already exists with envelope `correlation_id == <qa_curation_task_correlation_id>` and `payload.curation_pr_url == <pr_url>`, the emission has already been performed — log "idempotent skip: regression_suite_curated already emitted at <ts>" and return. No second emission.

### Step PM.4 — Compose and validate the event

Construct:

```json
{
  "timestamp": "<ISO-8601 now>",
  "correlation_id": "<qa_curation_task_correlation_id>",
  "event_type": "regression_suite_curated",
  "source": "qa",
  "source_version": "<from scripts/read-agent-version.sh qa>",
  "payload": {
    "curation_pr_url": "<pr_url>",
    "scope": "<from the PR body's recovered scope>",
    "affected_test_ids": ["<union of accepted candidates' test_ids>"],
    "affected_feature_correlation_ids": ["<union of accepted candidates' features>"],
    "scan_summary": {
      "plans_scanned": "<from PR body>",
      "regression_events_consulted": "<from PR body>"
    },
    "refused_candidates": [
      "<one entry per refused candidate>"
    ]
  }
}
```

Pipe through [`scripts/validate-event.py`](../../../../scripts/validate-event.py). Require exit `0` on both the envelope and the per-type payload schema [`events/regression_suite_curated.schema.json`](../../../../shared/schemas/events/regression_suite_curated.schema.json). Append to the feature event log. Re-read the appended line to confirm JSON integrity.

### Step PM.5 — Return

The invocation is complete. The skill does **not** transition the qa_curation task issue; that is the merge watcher's responsibility. No summary event, no comment on the PR, no comment on the task issue.

## Failure-pattern clustering (v1 algorithm)

The consolidation-candidate surface in Step 3 uses a simple co-failure count algorithm, chosen deliberately over graph-based or embedding-based alternatives (see §"Deferred integration"):

### Inputs

Across all features in the scan cohort, read each feature's event log and extract every `qa_execution_failed` event whose timestamp is in the more restrictive of:

- Last 30 days from now, OR
- Last 50 `qa_execution_failed` events across the cohort, regardless of feature.

The window exists to keep clustering relevant to current system behavior. A regression pattern from 6 months ago on a since-refactored surface is not informative for today's consolidation decisions.

### Computation

For each pair of distinct `test_id`s `(A, B)` that appear in the window's `qa_execution_failed` events:

- `co_fail_count(A, B)` = count of events where both A and B appear in `payload.failed_tests[].test_id`.
- `total_fail_count(A)` = count of events where A appears.
- `total_fail_count(B)` = count of events where B appears.

`(A, B)` is a **consolidation candidate** if all three hold:

- `co_fail_count(A, B) >= 3` (noise floor — one or two co-failures is coincidence).
- `co_fail_count(A, B) / total_fail_count(A) >= 0.7` (A almost always fails when B does).
- `co_fail_count(A, B) / total_fail_count(B) >= 0.7` (B almost always fails when A does).

### Output

Each candidate `(A, B)` is surfaced in the PR's curation report with:

- The co-failure count, the two total-fail counts, and the two ratios.
- The AC fragments A and B cover (for the human to assess whether they're measuring the same underlying behavior).
- The plan files A and B live in (same feature or cross-feature).

The skill does **not** auto-merge consolidation candidates. It surfaces them; the human reviews the PR and decides which to merge (possibly editing the PR to accept some and reject others before merge). This is distinct from dedup and orphan candidates, which the skill proposes as concrete diffs.

### Thresholds (0.7 / 3 / 30d / 50-events)

- **0.7 ratio on both sides** — two tests that co-fail <70% of the time on either side are likely measuring different things that happen to break together (e.g., common dependency, shared fixture); consolidating them would silently lose coverage of one of the behaviors.
- **3 co-failures minimum** — 1 or 2 is below the signal/noise threshold.
- **30 days / 50 events** — tuned for a realistic open-source adopter's velocity (a handful of regressions per week); adjustable from walkthrough evidence.

The thresholds are recorded here, not hardcoded into the schema. Phase 4+ tuning is straightforward; a walkthrough (WU 3.6) that finds these produce too many false positives or miss real patterns is the signal to revise.

## Idempotence discipline

Idempotence under replay is a load-bearing correctness bar in both modes.

### Drafting mode

A replayed drafting invocation on the same qa_curation task should produce no duplicate PR. Three mechanisms:

- **Branch-name uniqueness.** The branch `qa-curation/<qa_curation_task_correlation_id>` is derived from the task correlation ID. A second invocation on the same task finds the branch already present — the skill checks for the branch and, if it exists, aborts drafting with "idempotent skip: curation branch already exists at `<branch>`; PR state = `<gh pr view state>`". No second PR, no second diff.
- **Task label.** A second invocation finds the task already `state:in-progress` (from the first invocation's Step 1). The skill treats an already-in-progress task as a resumption attempt and follows the branch-existence check to decide whether to continue drafting (if the branch exists, assume the prior invocation crashed mid-Step-6 — read the branch's existing commits, diff against main, compare to the current candidate set, and either resume the PR open or abort).
- **Deterministic candidate order.** Plan-file sort is by mtime (stable within a millisecond resolution across two invocations happening within the same scan window). Per-candidate iteration is in stable alphabetical order on `test_id`. A replay produces the same candidate set in the same order, simplifying the branch-existence comparison.

### Post-merge mode

The Step PM.3 idempotence check is the primary guard: a `regression_suite_curated` event already on the feature log with matching correlation_id + PR URL causes the replay to skip. The event log is authoritative; no cached "already emitted" flag is persisted.

### What idempotence does NOT require

- **Cross-invocation state.** The skill persists nothing. Every invocation re-reads the filesystem and the event log.
- **Transactional PR creation.** If the drafting mode crashes after creating the branch but before opening the PR, the next invocation finds the branch, diffs it, and opens the PR from the existing commits. No rollback.
- **Cross-feature coordination.** One invocation = one qa_curation task = one drafting pass. The skill does not batch across multiple qa_curation tasks.

## Verification

Before returning from any invocation, the skill confirms the following. **The first bullet is the grep-able Q4 invariant clause** — codified verbatim in [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific verification" for this skill.

- **No write to labels or state on any task other than the QA task itself.** Specifically: no write to labels or state on any implementation task, no write to labels or state on any other QA task, no write to labels or state on any PM-owned task. The skill's writes are confined to (a) the curation branch in the specs repo, (b) files under `/product/test-plans/*.md` on that branch, (c) event lines appended to `/events/<feature_of_qa_curation_task>.jsonl`, and (d) the `state:in-progress → state:in-review` transition on the qa_curation task's own issue (role-owned). A review of every write path in this skill confirms no `gh issue edit` or label-mutation call exists on any task-level correlation ID other than the qa_curation task this invocation owns.
- The bounded-growth discipline held: the drafting pass scanned at most 50 plan files (recorded in `scan_summary.plans_scanned` on the emitted event). A pass that scanned more is a skill bug and fails this check.
- Every refused candidate is recorded in `refused_candidates[]` on the emitted payload with a concrete `reason` that quotes the source evidence (filed event timestamp, impl task correlation ID for open-regression refusals; schema validation error for the schema-validation-failed branch). A refusal without a concrete reason fails this check.
- The `regression_suite_curated` event's envelope `correlation_id` is task-level on the qa_curation task (`FEAT-YYYY-NNNN/TNN` pattern per [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md)). A feature-level correlation_id fails this check.
- The event's `payload.affected_feature_correlation_ids[]` contains every feature whose plan file was modified by the merged PR, with no duplicates. Cross-validated against the PR's `gh pr view --json files` output: every changed `/product/test-plans/FEAT-YYYY-NNNN.md` path's FEAT identifier appears in the array.
- On every emission path: every event round-trips through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) with exit `0` (envelope + per-type payload for `regression_suite_curated`), was appended to the feature event log, and was re-read as a valid JSONL line.
- `source_version` on the emitted event was produced by [`scripts/read-agent-version.sh qa`](../../../../scripts/read-agent-version.sh) at emission time, not eye-cached from `version.md`.
- Every file modified on the curation branch is re-read after write; its post-write content matches the intended frontmatter and the test-plan schema validates it.
- No path written is in [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md). Specifically: `/product/test-plans/*.md` is QA-owned per [`../../CLAUDE.md`](../../CLAUDE.md) §"Output artifacts", and `/events/<feature>.jsonl` is the feature event log.
- The curation branch's name matches `^qa-curation/FEAT-\d{4}-\d{4}-T\d{2}$` exactly. A malformed branch name breaks the post-merge trigger's matcher and is rejected.
- The PR body contains the five required sections (`## Summary`, `## Accepted candidates`, `## Refused candidates`, `## Scan summary`, `## How to review`) — a missing section means the curation report is unreviewable and fails this check.

Failure handling follows [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §3: locally correctable (e.g., `source_version` emission script returned a stale value) → retry once with re-read; three failed cycles on the same invocation → escalate `spinning_detected` **on the qa_curation task itself** (authoring-style task-level escalation per [`../../CLAUDE.md`](../../CLAUDE.md) §"Role-specific escalation"), NOT on any implementation task; spec-level blocker (e.g., a scan-cohort plan file is fundamentally unparseable at a level beyond per-plan skip) → escalate `spec_level_blocker` at the qa_curation task level.

**Verifying the curation work is not the same as verifying every test it touched.** The skill does not re-run tests it retires or consolidates — that is qa-execution's concern, not curation's. The skill's verification confirms the **curation decisions** were made correctly (open-regression protection honored, scan budget respected, event payload accurate), not that the underlying tests still exercise correct behavior.

## Worked example 1 — Dedup consolidation (AC #4)

Fictional feature pair used for illustration. The suite currently contains two plans: `FEAT-2026-0062 — Widgets bulk-import` and `FEAT-2026-0063 — Widgets bulk-import idempotency`. During independent authoring passes, two tests ended up covering the same acceptance criterion — both check that `POST /widgets/bulk` returns HTTP 409 on duplicate submission.

### Pre-invocation state

`/product/test-plans/FEAT-2026-0062.md` frontmatter excerpt:

```yaml
---
schema_version: 1
feature_correlation_id: FEAT-2026-0062
tests:
  - test_id: widgets-bulk-duplicate-returns-409
    covers: "AC-3: POST /widgets/bulk returns 409 Conflict when the submission's idempotency-key matches a prior successful submission within the last 24h."
    commands:
      - "curl -sS -X POST -H 'Content-Type: application/json' -H 'Idempotency-Key: abc-123' -d @seed.json -o body.json -w '%{http_code}' http://localhost:8080/widgets/bulk"
      - "curl -sS -X POST -H 'Content-Type: application/json' -H 'Idempotency-Key: abc-123' -d @seed.json -o body.json -w '%{http_code}' http://localhost:8080/widgets/bulk"
    expected: "First request returns 201, second request with same idempotency-key returns 409 Conflict with body.error.code == 'duplicate_submission'."
---
```

`/product/test-plans/FEAT-2026-0063.md` frontmatter excerpt:

```yaml
---
schema_version: 1
feature_correlation_id: FEAT-2026-0063
tests:
  - test_id: widgets-bulk-idempotency-conflict
    covers: "AC-3: POST /widgets/bulk with a repeated Idempotency-Key returns 409 Conflict."
    commands:
      - "curl -sS -X POST -H 'Content-Type: application/json' -H 'Idempotency-Key: xyz-789' -d @seed.json -o body.json -w '%{http_code}' http://localhost:8080/widgets/bulk"
      - "curl -sS -X POST -H 'Content-Type: application/json' -H 'Idempotency-Key: xyz-789' -d @seed.json -o body.json -w '%{http_code}' http://localhost:8080/widgets/bulk"
    expected: "First request returns 201, second request with same idempotency-key returns 409 Conflict with body.error.code == 'duplicate_submission'."
---
```

Event logs at `/events/FEAT-2026-0062.jsonl` and `/events/FEAT-2026-0063.jsonl` have no open `qa_regression_filed` for either test_id.

### Triggering invocation

Drafting mode invoked on qa_curation task `FEAT-2026-0070/T05`. Feature registry `/features/FEAT-2026-0070.md` has T05 with `assigned_repo: clabonte/api-sample`.

**Step 1** — intent stated; rules reloaded; T05 label `state:ready → state:in-progress`; `task_started` emitted on `/events/FEAT-2026-0070.jsonl` with correlation_id `FEAT-2026-0070/T05`.

**Step 2** — Cohort enumeration. The suite has 7 plans total; all 7 fit in the 50-plan budget. Sorted by mtime ascending: `[FEAT-2026-0060, FEAT-2026-0061, FEAT-2026-0062, FEAT-2026-0063, ...]`.

**Step 3** — Candidate classification. Scanning `covers` fields across the cohort:

- Dedup: `widgets-bulk-duplicate-returns-409` (FEAT-2026-0062) and `widgets-bulk-idempotency-conflict` (FEAT-2026-0063) both cite `AC-3` and the behavior `"POST /widgets/bulk returns 409 … Idempotency-Key … duplicate"`. Text-overlap heuristic (shared substring on `POST /widgets/bulk`, `409`, `Idempotency-Key`, `duplicate`) flags the pair. Candidate recorded: merge the later test_id into the earlier (`widgets-bulk-duplicate-returns-409` wins alphabetically).
- No orphans (every test's `covers` AC fragment is present in the respective feature registry's `## Acceptance criteria`).
- No consolidation candidates (no qa_execution_failed events in the 30-day window have co-failure counts crossing the threshold).
- No rename requests in `## Coverage notes` bodies.

**Step 4** — Open-regression protection. For the dedup's retired test_id `widgets-bulk-idempotency-conflict` (on FEAT-2026-0063):

- Read `/events/FEAT-2026-0063.jsonl` fresh.
- No `qa_regression_filed` entries with `payload.test_id == "widgets-bulk-idempotency-conflict"`.
- Open set empty. Candidate proceeds.

**Step 5** — One surviving candidate, kind=dedup → `scope: "dedup"`.

**Step 6** — Draft the PR.

1. Create branch `qa-curation/FEAT-2026-0070-T05` off `main` in the specs repo.
2. Diffs:
   - `FEAT-2026-0062.md`: the surviving test's `covers` becomes `"AC-3: POST /widgets/bulk returns 409 Conflict when the submission's idempotency-key matches a prior successful submission within the last 24h.; AC-3: POST /widgets/bulk with a repeated Idempotency-Key returns 409 Conflict."` (semicolon-joined). `commands` union: the 4 curl commands from both sources, deduplicated. `expected` preserved (both had identical `expected` prose).
   - `FEAT-2026-0063.md`: `widgets-bulk-idempotency-conflict` removed from `tests[]`.
3. Re-validate both frontmatter against the test-plan schema. Both pass.
4. Compose the PR body:

```markdown
## Summary

Curation pass on behalf of FEAT-2026-0070/T05. Scope: dedup. 1 accepted, 0 refused.

## Accepted candidates

### Dedup: `widgets-bulk-idempotency-conflict` → `widgets-bulk-duplicate-returns-409`

- Affected features: FEAT-2026-0062, FEAT-2026-0063
- Both tests cite AC-3 and cover the same behavior (POST /widgets/bulk returning 409 on repeated Idempotency-Key). Merged into the earlier-sorted test_id; `covers` retained both sources, `commands` unioned, `expected` preserved identically across sources.
- No open `qa_regression_filed` on either test_id; protection passed.

## Refused candidates

(none)

## Scan summary

- Plans scanned: 7
- Regression events consulted: 14
- Wall-clock duration: 2.1s

## How to review

The diff on `product/test-plans/FEAT-2026-0062.md` is the surviving test's merged form; the diff on `product/test-plans/FEAT-2026-0063.md` is the removal. Confirm the merged `covers` reads cleanly and the `commands` union does not drop any unique request shape.

Closes clabonte/api-sample#87
```

5. PR opened against specs repo `main`. Issue #87 in `clabonte/api-sample` is the qa_curation task's GitHub issue.
6. Flip `state:in-progress → state:in-review` on issue #87.
7. Emit `task_completed`:

```json
{
  "timestamp": "2026-04-23T17:20:00Z",
  "correlation_id": "FEAT-2026-0070/T05",
  "event_type": "task_completed",
  "source": "qa",
  "source_version": "1.4.0",
  "payload": {
    "issue": "clabonte/api-sample#87"
  }
}
```

Validates, appended.

### Post-merge invocation

Time passes: the human reviews the PR, approves, and merges. The external trigger (webhook / polling loop / CLI) detects the merge and invokes the skill in post-merge mode with PR URL `https://github.com/clabonte/specs-sample/pull/24` and task correlation ID `FEAT-2026-0070/T05`.

**Step PM.1** — intent stated, rules reloaded.

**Step PM.2** — `gh pr view` confirms `state: MERGED`, merge commit resolvable, changed files all under `/product/test-plans/`. PR body parsed: scope=dedup, 1 accepted (the pair above), 0 refused, scan_summary {plans_scanned: 7, regression_events_consulted: 14}.

**Step PM.3** — Read `/events/FEAT-2026-0070.jsonl` fresh. No prior `regression_suite_curated` with correlation_id `FEAT-2026-0070/T05`. Proceed.

**Step PM.4** — Compose:

```json
{
  "timestamp": "2026-04-23T18:05:00Z",
  "correlation_id": "FEAT-2026-0070/T05",
  "event_type": "regression_suite_curated",
  "source": "qa",
  "source_version": "1.4.0",
  "payload": {
    "curation_pr_url": "https://github.com/clabonte/specs-sample/pull/24",
    "scope": "dedup",
    "affected_test_ids": [
      "widgets-bulk-duplicate-returns-409",
      "widgets-bulk-idempotency-conflict"
    ],
    "affected_feature_correlation_ids": [
      "FEAT-2026-0062",
      "FEAT-2026-0063"
    ],
    "scan_summary": {
      "plans_scanned": 7,
      "regression_events_consulted": 14
    }
  }
}
```

`refused_candidates` omitted — no refusals in this pass.

Validates through `scripts/validate-event.py` (envelope + per-type payload). Appended to `/events/FEAT-2026-0070.jsonl`. Re-read confirms.

**Step PM.5** — Return. Merge watcher (separately) transitions `clabonte/api-sample#87` from `state:in-review → state:done` on detecting the specs repo merge linked to the task issue via the `Closes` line in the PR body.

Cycle complete. No state write on any implementation task, no state write on any other QA task. Q4 invariant holds.

## Worked example 2 — Orphan retirement with a refused candidate (AC #5 + Verification #2)

A second scene exercising the **open-regression protection rule** required by Verification step #2 of the WU. The suite contains two candidate orphans — one with a clean open-regression slate (retires cleanly) and one with an open `qa_regression_filed` blocking retirement (refused).

### Pre-invocation state

The two candidate orphans:

1. **`widgets-export-legacy-v1-content-type`** on `FEAT-2026-0060 — Widgets export pagination`. The test's `covers` cites `AC-4: Responses carry Content-Type: application/vnd.widgets.v1+json`. But the feature registry's `## Acceptance criteria` section no longer contains `AC-4` — a recent spec revision (reflected in the current feature file) dropped the v1 content-type mandate. Orphan.

2. **`widgets-export-rate-limit-enforced-429`** on `FEAT-2026-0061 — Widgets export rate-limit`. The test's `covers` cites `AC-2` ("101st request in a rolling minute window returns HTTP 429"). A revision dropped the rate-limit mandate entirely, so AC-2 is gone. Orphan. **However**, the feature's event log has an open `qa_regression_filed` on this test_id — the one from [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) §"Worked example 1 — Full resolution loop (FEAT-2026-0061)" before Invocation B resolved it.

For this example, we diverge from the qa-regression Example 1 timeline: assume the resolving `qa_execution_completed` **has not yet happened**. The filed event is still open on the log.

Relevant event-log excerpt from `/events/FEAT-2026-0061.jsonl`:

```json
{"timestamp":"2026-04-23T18:44:00Z","correlation_id":"FEAT-2026-0061","event_type":"qa_regression_filed","source":"qa","source_version":"1.3.0","payload":{"implementation_task_correlation_id":"FEAT-2026-0061/T02","test_id":"widgets-export-rate-limit-enforced-429","failing_qa_execution_event_ts":"2026-04-23T18:42:00Z","failing_commit_sha":"def56789abcdef0123456789abcdef0123456789","regression_inbox_file":"inbox/qa-regression/FEAT-2026-0061-widgets-export-rate-limit-enforced-429.md"}}
```

No matching `qa_regression_resolved` for this `test_id` with `filed_event_ts: 2026-04-23T18:44:00Z`.

### Triggering invocation

Drafting mode invoked on `FEAT-2026-0070/T05`.

**Step 1** — intent stated; task label flipped; `task_started` emitted.

**Step 2** — Cohort: same 7 plans as Example 1.

**Step 3** — Candidate classification:

- Dedup: no same-feature or cross-feature `covers` overlaps.
- **Orphan 1**: `widgets-export-legacy-v1-content-type` on FEAT-2026-0060 — `AC-4` not present in `/features/FEAT-2026-0060.md`. Candidate.
- **Orphan 2**: `widgets-export-rate-limit-enforced-429` on FEAT-2026-0061 — `AC-2` not present in `/features/FEAT-2026-0061.md`. Candidate.
- No consolidation candidates in the window.
- No rename requests.

**Step 4** — Open-regression protection, per candidate:

**Candidate 1** (`widgets-export-legacy-v1-content-type`, FEAT-2026-0060):

- Read `/events/FEAT-2026-0060.jsonl` fresh.
- No `qa_regression_filed` with `payload.test_id == "widgets-export-legacy-v1-content-type"`.
- Open set empty. **Proceed** to PR draft.

**Candidate 2** (`widgets-export-rate-limit-enforced-429`, FEAT-2026-0061):

- Read `/events/FEAT-2026-0061.jsonl` fresh.
- One `qa_regression_filed` with `payload.test_id == "widgets-export-rate-limit-enforced-429"`, `filed_event_ts: 2026-04-23T18:44:00Z`, `implementation_task_correlation_id: FEAT-2026-0061/T02`.
- Scan for matching `qa_regression_resolved`: none found.
- Open set non-empty. **Refuse.** Record `refused_candidates[]` entry:

```json
{
  "test_id": "widgets-export-rate-limit-enforced-429",
  "feature_correlation_id": "FEAT-2026-0061",
  "reason": "open qa_regression_filed at 2026-04-23T18:44:00Z on FEAT-2026-0061/T02 without matching qa_regression_resolved"
}
```

**The refusal is NOT an escalation.** It is a deliberate safety-check outcome. The skill continues with the remaining candidates; no `spec_level_blocker`, no `spinning_detected`, no comment on the qa_curation task issue beyond the PR body's `## Refused candidates` section.

**Step 5** — One surviving candidate (Candidate 1), kind=retire_orphan → `scope: "retire_orphan"`.

**Step 6** — Draft the PR.

1. Create branch `qa-curation/FEAT-2026-0070-T05`. (Same branch name as Example 1 if this were a re-invocation; in this example it's a fresh invocation.)
2. Diff on `FEAT-2026-0060.md`: remove the `widgets-export-legacy-v1-content-type` entry from `tests[]`. The plan retains its other tests (`widgets-export-default-page-size`, `widgets-export-page-size-over-limit-rejected` from WU 3.2's worked example), so `tests[]` is not empty.
3. Re-validate `FEAT-2026-0060.md` frontmatter — passes.
4. PR body:

```markdown
## Summary

Curation pass on behalf of FEAT-2026-0070/T05. Scope: retire_orphan. 1 accepted, 1 refused.

## Accepted candidates

### Orphan: `widgets-export-legacy-v1-content-type` on FEAT-2026-0060

- The test's `covers` cites `AC-4: Responses carry Content-Type: application/vnd.widgets.v1+json`, which is no longer present in `/features/FEAT-2026-0060.md` as of the current registry read. A recent spec revision dropped the v1 content-type mandate.
- No open `qa_regression_filed` on this test_id on FEAT-2026-0060's event log; protection passed.
- Retirement removes this one `tests[]` entry; the plan retains 2 other tests.

## Refused candidates

### Orphan: `widgets-export-rate-limit-enforced-429` on FEAT-2026-0061 — REFUSED

- The test's `covers` cites `AC-2` which is no longer present in the feature registry; orphan per the detection rule.
- However, `/events/FEAT-2026-0061.jsonl` carries an open `qa_regression_filed` for this test_id, filed at 2026-04-23T18:44:00Z against implementation task `FEAT-2026-0061/T02`, with no matching `qa_regression_resolved`. Retirement is refused per the open-regression protection rule (`agents/qa/CLAUDE.md` §"Anti-patterns" #7).
- Not an escalation. A future curation pass will propose retirement again once the regression resolves.

## Scan summary

- Plans scanned: 7
- Regression events consulted: 28
- Wall-clock duration: 3.4s

## How to review

The diff on `product/test-plans/FEAT-2026-0060.md` retires one orphaned test. The refused candidate on FEAT-2026-0061 is recorded for audit but not touched. Confirm the retired test's covered behavior is genuinely absent from the feature spec; if the AC was renamed rather than dropped, the curation should be aborted and the rename handled instead.

Closes clabonte/api-sample#87
```

5. PR opened.
6. Label flip on #87 `state:in-progress → state:in-review`.
7. `task_completed` emitted.

### Post-merge invocation

Human reviews, approves, merges. External trigger invokes post-merge mode.

**Step PM.1–3** as Example 1.

**Step PM.4** — Compose:

```json
{
  "timestamp": "2026-04-23T22:45:00Z",
  "correlation_id": "FEAT-2026-0070/T05",
  "event_type": "regression_suite_curated",
  "source": "qa",
  "source_version": "1.4.0",
  "payload": {
    "curation_pr_url": "https://github.com/clabonte/specs-sample/pull/17",
    "scope": "retire_orphan",
    "affected_test_ids": [
      "widgets-export-legacy-v1-content-type"
    ],
    "affected_feature_correlation_ids": [
      "FEAT-2026-0060"
    ],
    "scan_summary": {
      "plans_scanned": 7,
      "regression_events_consulted": 42
    },
    "refused_candidates": [
      {
        "test_id": "widgets-export-rate-limit-enforced-429",
        "feature_correlation_id": "FEAT-2026-0061",
        "reason": "open qa_regression_filed at 2026-04-23T18:44:00Z on FEAT-2026-0061/T02 without matching qa_regression_resolved"
      }
    ]
  }
}
```

See [`/shared/schemas/examples/regression_suite_curated.json`](../../../../shared/schemas/examples/regression_suite_curated.json) for the fixture.

Validates through `scripts/validate-event.py` (envelope + per-type payload, which enforces the refused_candidates object shape). Appended to `/events/FEAT-2026-0070.jsonl`. Re-read confirms.

**Step PM.5** — Return.

Note: `affected_test_ids` contains only `widgets-export-legacy-v1-content-type` — the accepted retirement. The refused candidate `widgets-export-rate-limit-enforced-429` appears in `refused_candidates[]`, NOT in `affected_test_ids[]`. A consumer reading `affected_test_ids` gets the set of test_ids actually touched by the merged diff; `refused_candidates` is the audit surface for decisions-not-taken.

### Why this scene exercises the protection

- The skill saw an orphaned test (objective criterion for retirement by the scan).
- The skill refused to retire it (open `qa_regression_filed` without matching resolved).
- The refusal is a **machine-readable record** in the emitted event, not a silent skip.
- The other orphan in the same pass retired cleanly, demonstrating the protection is per-candidate, not all-or-nothing.
- No label was flipped on any task other than the qa_curation task itself; no event was emitted on any feature event log other than the qa_curation task's feature (FEAT-2026-0070) for the `regression_suite_curated` event, and the standard task-lifecycle events (`task_started`, `task_completed`). The Q4 invariant holds.

## Deferred integration — Phase 4 + Phase 5 brief

The v1 skill is deliberately simple. Concrete evolutions expected:

### Phase 4 — richer scan and clustering

- **Scan-budget tuning.** 50 plans is a walkthrough-informed starting point. Retrospective evidence (WU 3.7) should adjust the threshold up or down. A cursor-backed incremental scan (persist the "stalest unscanned plan" across invocations) is a Phase 4 candidate if retrospective shows the cohort rotation is too slow.
- **Consolidation-candidate surfacing upgrade.** The 0.7 / 3 / 30d / 50-events thresholds in the v1 co-failure count algorithm are simple. Phase 4 can replace or augment with:
  - Connected-components clustering on the co-failure graph (surfaces groups of 3+ tests that fail together, not just pairs).
  - Weighted edges by recency (more-recent co-failures count more).
  - Exclusion of tests that co-fail only because they share a fixture / upstream dependency (detected via plan-file metadata).
- **Automatic rename detection.** v1 requires an explicit `rename-request: old-id → new-id` line in plan prose. Phase 4 could detect candidate renames via `test_id` convention drift (walk the codebase for convention patterns and propose renames conforming to the newer one).
- **Cross-repo rename propagation.** If a renamed `test_id` appears in closed-regression inbox artifacts or in resolved event payloads, those historical records should be rewritten as part of the rename PR — carefully, since event logs are append-only. Phase 4 can introduce a compensating mechanism (e.g., a `test_id_renamed` event that indexes old → new without rewriting history).

### Phase 5 — generator-emitted skeletons

When the Specfuse generator emits test plan skeletons (Phase 5), curation's job shifts:

- **Orphan detection** becomes largely automatic: the generator knows which operations it emitted and can tag skeleton tests with a machine-readable `covers` that points at the OpenAPI response path. Curation compares the tagged `covers` against the current OpenAPI; a missing operation = an orphan with zero ambiguity.
- **Dedup across features** can piggyback on generator provenance (two features that end up emitting tests against the same operation are a curation signal).
- **Failure-pattern clustering** can cross-reference the shared fixtures and generated harness code to distinguish "fail together because they share a fixture" from "fail together because they measure the same behavior" — the former is not a consolidation opportunity.

The v1 scan-and-propose structure is preserved; Phase 5 changes the inputs' richness, not the procedure's shape.

### What Phase 4 / Phase 5 do NOT change

- **The open-regression protection rule.** Retiring a test with an open filed regression hides an in-flight problem at every phase; no richer input or better clustering relaxes the rule.
- **The PR-mediation discipline.** All curation changes land via reviewable PR across every phase. Auto-merging curation is explicitly not a goal.
- **The two-mode (drafting + post-merge) structure.** The event emission on PR merge is load-bearing for the audit trail; collapsing it into the drafting pass would emit the event before the human's review.
- **The `regression_suite_curated` event's envelope correlation_id = task-level on the qa_curation task.** The cross-feature fanout belongs in `affected_feature_correlation_ids[]`, not in the envelope.

## What this skill does not do

- It does **not** author test plans. That is [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) (WU 3.2).
- It does **not** run test plans. That is [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) (WU 3.3).
- It does **not** file or resolve regressions. That is [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) (WU 3.4).
- It does **not** destructively edit test plan files. All curation changes flow through a reviewable PR — anti-pattern #8 in [`../../CLAUDE.md`](../../CLAUDE.md).
- It does **not** retire a test with an open `qa_regression_filed` lacking a matching `qa_regression_resolved` — anti-pattern #7 in [`../../CLAUDE.md`](../../CLAUDE.md). The open-regression protection in Step 4 is the enforcement.
- It does **not** rewrite historical event-log entries. Rename is modeled as "retire-old + add-new" with no event-log patching. Phase 4+ can introduce cross-reference indexing if walkthrough evidence shows it's needed.
- It does **not** transition any state on any task other than the qa_curation task it owns. Specifically: no transition on implementation tasks, no transition on any other QA task, no transition on the merge watcher's domain (`in_review → done`).
- It does **not** mint task-level correlation IDs. The qa_curation task's correlation ID is minted by the PM agent during task decomposition; this skill consumes it.
- It does **not** emit `test_plan_authored`, `qa_execution_*`, `qa_regression_*`, or `escalation_resolved`. Those belong to sibling skills. This skill emits `task_started`, `task_completed`, and `regression_suite_curated` (the last only in post-merge mode).
- It does **not** auto-merge consolidation candidates. Consolidation candidates are surfaced in the PR for human review; dedup and orphan candidates are proposed as concrete diffs. The distinction reflects the confidence level: dedup / orphan are deterministic given the scan rules; consolidation is heuristic and needs human judgment.
- It does **not** cache plan files, feature registries, event logs, or candidate sets across invocations. Every pickup re-reads fresh per anti-pattern #12.
- It does **not** delete a plan file even when its `tests[]` becomes empty. Plan-file lifecycle (retirement of entire plans) is a separate concern deferred to Phase 4+.
- It does **not** swallow schema validation failures on modified plans. A post-diff schema-validation failure rolls back the change and records the candidate as refused.
- It does **not** self-schedule, poll, or persist state. The trigger-detection mechanism is external for both modes.

## References

- [`/docs/orchestrator-architecture.md`](../../../../docs/orchestrator-architecture.md) §4.3 (test plan location), §6.3 (transition ownership — the Q4 invariant's architectural basis; `in_review → done` on the qa_curation task is the merge watcher's, not this skill's), §7.3 (event log semantics), §7.4 (inbox extensibility — unused here; this skill has no inbox).
- [`/docs/orchestrator-implementation-plan.md`](../../../../docs/orchestrator-implementation-plan.md) §"Work unit 3.5" — the work unit that authored this skill.
- [`../../CLAUDE.md`](../../CLAUDE.md) — the QA role config; §"Role-specific verification" names the grep-able clause this skill's §"Verification" reproduces, §"Anti-patterns" #7 (open-regression protection) and #8 (destructive inline edits bypassing PR) are the hard stops enforced here, §"Cross-task regression semantics" is the invariant context.
- [`../qa-authoring/SKILL.md`](../qa-authoring/SKILL.md) — upstream skill (WU 3.2) that authors the plans this skill curates. Forward-references this skill as the home for `test_id` renames.
- [`../qa-execution/SKILL.md`](../qa-execution/SKILL.md) — upstream skill (WU 3.3) whose `qa_execution_failed` events feed the failure-pattern clustering in §"Failure-pattern clustering".
- [`../qa-regression/SKILL.md`](../qa-regression/SKILL.md) — upstream skill (WU 3.4) whose `qa_regression_filed` / `qa_regression_resolved` event pairs this skill reads for the open-regression protection check. The idempotence key `(implementation_task_correlation_id, test_id)` is the same shape, but this skill matches on `test_id` alone within a feature's event log because `(feature, test_id)` is sufficient for the curation decision.
- [`../../../pm/skills/dependency-recomputation/SKILL.md`](../../../pm/skills/dependency-recomputation/SKILL.md) — pattern reference for the "skill is a function, trigger is external, live-reads over cached state" posture. This skill diverges: it modifies plan files via PR rather than rotating labels via `gh issue edit`, and it has two invocation modes rather than one.
- [`../../../pm/skills/task-decomposition/SKILL.md`](../../../pm/skills/task-decomposition/SKILL.md) — pattern reference for the structured walk + validation posture. This skill diverges: it writes changes via PR rather than to the feature registry.
- [`/shared/schemas/test-plan.schema.json`](../../../../shared/schemas/test-plan.schema.json) — plan frontmatter contract this skill reads and writes (the skill's diff must keep every touched plan schema-valid).
- [`/shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — envelope; `regression_suite_curated` added to the enum in this WU.
- [`/shared/schemas/events/regression_suite_curated.schema.json`](../../../../shared/schemas/events/regression_suite_curated.schema.json) — per-type payload contract authored in this WU.
- [`/shared/schemas/events/qa_regression_filed.schema.json`](../../../../shared/schemas/events/qa_regression_filed.schema.json) — upstream event payload the open-regression protection reads.
- [`/shared/schemas/events/qa_regression_resolved.schema.json`](../../../../shared/schemas/events/qa_regression_resolved.schema.json) — upstream event payload that closes an open regression (matched by `(test_id, filed_event_ts)` within a feature log).
- [`/shared/schemas/events/qa_execution_failed.schema.json`](../../../../shared/schemas/events/qa_execution_failed.schema.json) — upstream event payload the failure-pattern clustering reads (`payload.failed_tests[].test_id`).
- [`/shared/schemas/examples/regression_suite_curated.json`](../../../../shared/schemas/examples/regression_suite_curated.json) — worked-example fixture for the Example 2 (orphan retirement + refused candidate) scene.
- [`/shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) §1, §3 — universal discipline; re-read artifact and round-trip events, applied in every step.
- [`/shared/rules/role-switch-hygiene.md`](../../../../shared/rules/role-switch-hygiene.md) — re-read unconditionally per invocation.
- [`/shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — the task-level pattern (`FEAT-YYYY-NNNN/TNN`) the envelope correlation_id uses.
- [`/shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — the escalation surface for the locally-correctable-failure and spec-level-blocker branches in §"Verification".
- [`/shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md) — re-confirmed: no written path in this skill is in the never-touch list.
- [`/scripts/validate-event.py`](../../../../scripts/validate-event.py) — applies the per-type payload schema additively.
- [`/scripts/read-agent-version.sh`](../../../../scripts/read-agent-version.sh) — produces `source_version` at emission time.
