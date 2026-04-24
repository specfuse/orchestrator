# Phase 3 walkthrough — Retrospective (WU 3.7)

## Identity

- **Walkthrough:** Phase 3, WU 3.7 (retrospective over WU 3.6)
- **Scope:** triage of findings surfaced in Feature 1 (happy path) and Feature 2 (backup-pivoted: qa-curation suite-growth stress) of WU 3.6
- **Operator:** @Bontyyy (co-piloted with Claude as Sonnet 4.6)
- **Date conducted:** 2026-04-24
- **Inputs:** [feature-1-log.md](feature-1-log.md) (F3.1–F3.24 + P1–P4), [feature-2-log.md](feature-2-log.md) (F3.25–F3.36 + P5–P10 + cross-feature confirmations + 1 counter-evidence), [orchestrator-implementation-plan.md](../../orchestrator-implementation-plan.md) §"Phase 3", the feature registry entries for `FEAT-2026-0006` and `FEAT-2026-0007`, the JSONL event logs for both features, the Phase 2 retrospective's deferred items (F2.10 closed in WU 3.4; Phase 1 Finding 8 conditional disposition per WU 3.3 Q6), and the Phase 2 retrospective as structural reference.
- **Status:** triage complete; Fix-in-Phase-3 work plan staged; items deferred to Phase 4+ tagged and cross-referenced.

## Objective

Triage the 36 findings surfaced across the two WU 3.6 features (F3.1–F3.36) and decide, for each, whether it must be fixed before the Phase 3 QA-agent configuration freeze or can be deferred to Phase 4+. Produce a concrete work plan for the Phase 3 fixes and a documented handoff list for the deferred items so Phase 4 (specs agent and chat front-end) starts from a fully-catalogued backlog.

Per the implementation plan, WU 3.7 is the decision artifact. Execution of the Fix-in-Phase-3 items themselves is carried by subsequent Phase 3 work units (WUs 3.8–3.N-1), each independently landable. The Phase 3 freeze declaration is explicitly **not** recorded here — it is the scope of the final Phase 3 work unit (WU 3.N), analogous to WU 1.12 and WU 2.15.

## Walkthrough outcome

Both WU 3.6 acceptance criteria were either met or honestly documented as negative results:

| Criterion | Feature | ID | Shape | Outcome |
|---|---|---|---|---|
| 1 — happy path, QA cycle end-to-end, single-repo | 1 | `FEAT-2026-0006` | 4 tasks; 4 issues; impl + qa-authoring + qa-execution + qa-curation all completed; feature reached `done` | ✅ Feature at `state: done`; 24 events, all validate ([PR #38](https://github.com/clabonte/orchestrator/pull/38)) |
| 2 — regression cycle primary (fallback: qa-curation stress) | 2 | `FEAT-2026-0007` | Primary path NOT exercised (component agent implemented AC-3 correctly first pass; no `qa_execution_failed` produced). Backup path activated: qa-curation against 5-plan corpus with dedup/orphan/rename/protection paths exercised | ⚠️ regression-cycle NOT exercised (negative result); ✅ backup path met; 25 events, all validate ([PR #39](https://github.com/clabonte/orchestrator/pull/39)) |
| Q4 invariant audit (F2 explicit, F1 informal) | both | — | Q4 cross-attribution invariant held across 6 QA sessions and 2 features | ✅ |

The QA agent configuration v1.4.0 (`agents/qa/CLAUDE.md` + three skills qa-authoring / qa-execution / qa-curation) executed correctly across the happy-path shape without any mid-walkthrough skill correction required. All findings are tuning opportunities or documentation gaps, not configuration correctness bugs. Every event validated through `scripts/validate-event.py` on every append (49 events total across the two features). The **qa-regression skill was NOT exercised at runtime** — the regression cycle did not trigger because the component agent correctly implemented the deliberately tricky AC-3 on the first pass. This is a negative result: `qa-regression/SKILL.md` remains unvalidated by live execution and must be stress-tested in a future walkthrough or dedicated Phase 4 exercise. The F3.5 mitigation (explicit "Do NOT `git commit` on orchestrator repo" prompt clause) was confirmed effective in F2 — 0 unauthorized commits vs F1's 4. Q4 cross-attribution invariant held across both features (formal audit in F2 log; informal confirmation in F1 log).

**Phase 1 Finding 8 disposition.** WU 3.3 Q6 decision stated: "does NOT apply to qa-execution; reaffirmed Phase 5 carry." However, F1 (Step 5) and F2 (Step 5) both provided live empirical evidence that the `--no-build` stale-artifact trap applies to the **component agent's verification skill** — the original origin of Finding 8. The Q6 decision correctly rejected absorption "for qa-execution" (which never invokes `dotnet test --no-build`). The 2-feature live evidence for the component verification skill now satisfies the Phase 1 retrospective's "next edit of verification/SKILL.md, opportunistically — no dedicated WU required" dispatch condition. Phase 3 WU 3.8 will absorb this. The Phase 1 freeze permits additive corrections per the Phase 1 retrospective's defer language: "carry into the next edit of `verification/SKILL.md`, opportunistically." Amending the skill with an explicit pre-gate build step is purely additive (adds a mandatory pre-step; does not remove or rewrite any existing gate). This is consistent with the Phase 1 v1.5.0 baseline contract.

## Triage criteria

Every finding was scored against three questions, mirroring Phase 2's pattern adjusted for Phase 3's evidence shape. A "yes" on any of them qualifies the finding for **Fix in Phase 3**; otherwise it is **Deferred to Phase 4+** or **Won't fix**.

1. **Does it gate Phase 4?** If the specs agent (Phase 4's deliverable) or any subsequent automation would either re-encounter the finding on its first real task or inherit a broken contract from the current Phase 3 configuration, the finding must be fixed before Phase 4 starts. The inheritance case matters: anything a Phase 4 agent would copy — event-emission patterns, skill templates, shared schemas, verification discipline — is cheaper to fix once in Phase 3 than separately in every downstream role.

2. **Is there 2-feature evidence?** A finding surfaced in both Feature 1 and Feature 2 — or confirmed by a fresh subagent independently resolving the same ambiguity differently — is not a single-session artifact; it is a reproducible failure of manual discipline or a real ambiguity in the skill text. Two independent features is the evidence threshold (mirroring Phase 2's threshold).

3. **Is the cost of deferring greater than the cost of fixing now?** Some single-feature findings are cheap enough to fix (a one-sentence clarification, an additive validation step, a sample-command pattern) that deferring them manufactures friction for no saving. Applied sparingly — the default on single-feature findings is to defer unless the forward cost is obviously larger or the surface touched is already being revisited.

Findings that fail all three tests defer by default. The deferred list is not "won't fix" — it is "fix when the context to fix it is already open."

## Findings triage

Thirty-six findings total: F3.1–F3.24 from Feature 1 (24 findings + 4 positive observations P1–P4); F3.25–F3.36 from Feature 2 (12 new findings + cross-feature confirmations + 6 positive observations P5–P10). Of the 36 triageable findings, 16 qualify for Fix-in-Phase-3, 10 defer to Phase 4+, 3 are Won't-fix-with-rationale, and 7 are Observation-only.

| # | Finding | Source | Cross-feature | Gate P4? | Decision |
|---|---|---|---|---|---|
| F3.1 | `--no-build` gate sequencing / Finding 8 live | F1 S5 + F2 S5 | ✅ yes | Yes | **Fix in Phase 3** |
| F3.2 | qa-authoring PR convention unspecified | F1 S7 + F2 S7 | ✅ yes | Yes | **Fix in Phase 3** |
| F3.3 | Port convention silent in spec/plan | F1 S10 + F2 S7 | ✅ yes | Yes | **Fix in Phase 3** |
| F3.4 | `generating → in_progress` transition ownerless | F1 S12 + F2 S20 | ✅ yes | Yes | **Fix in Phase 3** |
| F3.5 | Subagents auto-committed to orchestrator repo | F1 (4 commits) → F2 (0, mitigated) | ✅ confirmed effective | Yes | **Fix in Phase 3** (absorb mitigation) |
| F3.6 | Per-type payload schema paths not cross-referenced | F1 (3 instances) + F2 (0, mitigated) | ✅ confirmed effective | Yes | **Fix in Phase 3** (absorb mitigation) |
| F3.7 | issue-drafting SKILL.md worked example stickiness | F1 S4 + F2 S4 | ✅ yes | Yes | **Fix in Phase 3** |
| F3.8 | T04 issue body contradicts qa-curation SKILL empty-curation path | F1 S13 | no | Yes (marginal) | **Fix in Phase 3** |
| F3.9 | task-decomposition SKILL.md header says 7 steps, body has 8 | F1 S1 | no | No | **Fix in Phase 3** (trivial / cheap) |
| F3.10 | validate-event.py `/dev/stdin` broken on macOS | F1 (4 instances) → F2 (0, mitigated) | ✅ confirmed effective | Yes | **Fix in Phase 3** |
| F3.11 | SKILL.md files exceed 25k token read limit | F1 S4 + F2 S4/S19 | ✅ yes | No | Defer Phase 4+ |
| F3.12 | Cross-repo `Closes` limitation (counter-evidence from F2) | F1 S8 + F2 S8 counter | ✅ counter | No | Observation (reclassify to same-owner-works) |
| F3.13 | Early-session timestamp synthesis broke chronology | F1 S1–S4 | no | Yes | **Fix in Phase 3** |
| F3.14 | `task_completed` uses `issue` field; `task_started` uses `issue_url` | F1 S13 | no | Yes | **Fix in Phase 3** |
| F3.15 | Several task lifecycle events have no per-type schema | F1 S1, S3, S9, S12 | no | No | Defer Phase 4+ |
| F3.16 | "Done" derivation signal priority undocumented | F1 S9 | no | No | Defer Phase 4+ |
| F3.17 | `## Scope` cardinality clause ambiguity | F1 S1 | no | No | Defer Phase 4+ |
| F3.18 | Prescribed `commit_sha` didn't match local api-sample HEAD | F1 S10 | no | No | Observation (walkthrough procedure) |
| F3.19 | v1 prose `expected` predicate weak for stateful environments | F1 S10 | no | No | Observation (Phase 4 predicate language input) |
| F3.20 | Coverage report path is a directory, not a file | F1 S5 | no | No | Observation |
| F3.21 | Lint gate on pass returns empty output | F1 S5 | no | No | Observation |
| F3.22 | Rule 1 `qa_execution never auto` conditional parsing friction | F1 S1 | no | No | Defer Phase 4+ |
| F3.23 | `decomposition_pass` counting requires defensive fallback | F1 S1 | no | No | Observation |
| F3.24 | T04 `## Deliverables` forward-looking reference | F1 S4 | no | No | Defer Phase 4+ |
| F3.25 | validate-event.py rejects pretty-printed JSON | F2 S1 | no | Yes | **Fix in Phase 3** |
| F3.26 | `feature_state_changed` field names `from_state`/`to_state` unintuitive | F2 S2 | no | No | Won't fix |
| F3.27 | template-coverage-check entry-condition expects `state == planning` | F2 S3 | no | No | Defer Phase 4+ |
| F3.28 | JSONL append concatenation bug (`cat` without trailing newline) | F2 S4 | no | Yes (critical) | **Fix in Phase 3** |
| F3.29 | Missing plan-file fallback flow undocumented in issue-drafting | F2 S4 | no | Yes | **Fix in Phase 3** |
| F3.30 | IDE1006 lint rule surfaces at `dotnet format`, not `dotnet build` | F2 S5 | no | No | Won't fix |
| F3.31 | `source: component:<bare_name>` format vs. `<owner>/<repo>` | F2 S5 | no | No | Defer Phase 4+ |
| F3.32 | Cardinality wording "expected" ambiguous confirmatory vs. prescriptive | F2 S7 | no | No | Defer Phase 4+ |
| F3.33 | `tail -1 log | json.tool` fails on blank trailing line | F2 S9 | no | No | Defer Phase 4+ (update future preambles) |
| F3.34 | Background task exit signal misleading for persistent processes | F2 S10 | no | No | Observation |
| F3.35 | Operator rejection-of-successful-subagent due to partial visibility | F2 S19 | no | No | Won't fix |
| F3.36 | qa-curation sole-test retirement violates `minItems:1` | F2 S19 | no | Yes | **Fix in Phase 3** |

---

## Per-finding triage sections

Grouped by triage bucket. Cross-feature pairs are treated in a single section.

---

### Fix-in-Phase-3 findings

#### F3.1 — `--no-build` gate sequencing / Phase 1 Finding 8 live evidence

**What.** The component agent's `verification.yml` declares gates that use `dotnet test --no-build` and `dotnet build --no-restore`. The verification skill's gate sequence starts with `tests`, not a prior `build`. A component agent running gates literally on a fresh checkout or after new test-file additions would hit the stale-artifact trap: `--no-build` silently runs only the previously-compiled tests. F1 Step 5 subagent proactively ran `dotnet restore && dotnet build` before the gate sequence ("A component agent that reads verification.yml literally and runs gates in listed order on a fresh branch will fail the tests gate for reasons unrelated to the code under test"). F2 Step 5 subagent explicitly exercised the mitigation per the F3.1 preamble clause, confirming the trap exists and the pre-step eliminates it.

**Evidence.** F1 S5 session report; F2 S5 session report (second live confirmation). Both cite `--no-build` sequencing as the mechanism.

**2-feature evidence:** ✅ Both F1 and F2 exercised the pattern on fresh subagents.

**Phase 1 Finding 8 disposition.** The Phase 1 retrospective deferred this finding with: "carry into the next edit of `verification/SKILL.md`, opportunistically — no dedicated WU required." WU 3.3 Q6 decided "does NOT apply to qa-execution; reaffirmed Phase 5 carry" — but that decision was scoped to qa-execution (which never invokes `dotnet test --no-build` directly). The 2-feature evidence applies to the **component agent's verification skill**, which is the original origin of Finding 8. Absorbing this fix is consistent with the Phase 1 retrospective's dispatch condition ("next edit of `verification/SKILL.md`") and is purely additive (adds a mandatory pre-gate build step; does not alter existing gates or their sequence). Phase 1 v1.5.0 freeze is respected: additive documentation-only correction authorized.

**Decision.** Fix in Phase 3. WU 3.8.

---

#### F3.2 — qa-authoring SKILL.md does not specify the PR-based delivery convention

**What.** `qa-authoring/SKILL.md` §Step 7 describes writing the plan file and implies a PR-based delivery ("The PR containing the plan file is the deliverable under review") but specifies nothing about branch name format, commit message template, PR title/body format, which repo and base branch to target, or the stop-at-open discipline. F1 S7 needed explicit prompt pinning for all of these ("two agents operating from SKILL.md alone would diverge"). F2 S7 confirmed: "SKILL.md does not say which repo gets the PR (`-R`), what `--base` to target, or what the PR body should include. Zero ambiguity only because the preamble was authoritative; the gap in SKILL.md is real and would bite a cold invocation."

**Evidence.** F1 S7 friction note; F2 S7 friction note (independent fresh-context subagent, identical finding).

**2-feature evidence:** ✅

**Decision.** Fix in Phase 3. WU 3.9.

---

#### F3.3 — Port convention silent in spec / plan; qa-execution receives mismatched commands

**What.** qa-authoring naturally writes test plan commands targeting a default or assumed port (`http://localhost:5000`). The component service's `launchSettings.json` declares different ports (F1: 5083/7019; F2: 5083). F1 S10 hit the mismatch: the plan's command used port 5000; the service ran on 5083; the subagent worked around via `dotnet run --urls "http://localhost:5000"` — but this diverged from the service's declared configuration. F1's own test plan's `## Coverage notes` said "T03 should adapt the command" while qa-execution SKILL says "use the plan's command verbatim OR escalate." These two instructions are mutually incompatible. F2 S7 mitigated by pinning 5083 in the preamble: "without mitigation, natural fallback would be 5000 or 8080 — both wrong."

**Evidence.** F1 S10 friction note (port mismatch, workaround via `--urls`); F2 S7 friction note (gap identified, preamble mitigation required).

**2-feature evidence:** ✅

**Decision.** Fix in Phase 3. The least invasive fix: qa-authoring SKILL.md documents that `commands[]` should include the startup command (e.g., `dotnet run --project <path> --urls "http://localhost:<port>"`) as command[0], and that the authoring agent is responsible for discovering the component's declared port from `launchSettings.json` or equivalent. WU 3.9 (same WU as F3.2 — both are qa-authoring SKILL.md additions).

---

#### F3.4 — Feature state `generating → in_progress` transition has no clear skill owner

**What.** PM CLAUDE.md says the PM agent emits `feature_state_changed` for `generating → in_progress` "after the first round of task issues is opened across component repos." But no skill explicitly owns this transition. task-decomposition stops at `plan_review`; issue-drafting does not transition feature state; dep-recomputation is scoped to task states only. In both F1 (Step 12) and F2 (Step 20), the transition was **silently skipped** — the feature sat at `generating` throughout the entire task execution period. Both features required a retroactive emission during final cleanup, with trigger string `first_round_issues_opened_retroactive` honestly flagging the gap.

**Evidence.** F1 S12 discovery; F1 S14 retro emission; F2 S20 retro emission (same skip, same recovery pattern).

**2-feature evidence:** ✅

**Decision.** Fix in Phase 3. Add an explicit emission step to `issue-drafting/SKILL.md` after the first round of `task_created`/`task_ready` events: the skill emits `feature_state_changed(generating → in_progress)` before reporting completion. WU 3.10.

---

#### F3.5 — Subagents auto-committed to orchestrator repo without authorization

**What.** In F1, sessions S5, S7, S10, and S12 each made a local commit to orchestrator repo `main` recording event log appends. Prompts said "Do NOT push to GitHub" but did not prohibit local commits; subagents interpreted "commit-but-don't-push" as permissible. Result: 4 unauthorized local commits ahead of origin before the walkthrough wrap commit — bypassing the repo's PR-based merge convention. In F2, preamble clause 1 ("Do NOT `git commit` on orchestrator repo") was explicit; 0 subagent commits across all 6 subagent sessions. The mitigation is proven sufficient at the prompt level.

**Evidence.** F1 S12 discovery ("4 commits ahead of origin"); F2 overall outcome (0 unauthorized commits, P8 positive observation).

**2-feature evidence:** ✅ (F1 = problem; F2 = solved by clause; absorption promotes the clause to permanent discipline)

**Decision.** Fix in Phase 3. Absorb the clause into `shared/rules/verify-before-report.md` §3 OR a dedicated shared-rules addition, codifying "Do NOT `git commit` on the orchestration repo from within a role-switch subagent session; append events to the JSONL file, leave the commit to the orchestration session." WU 3.11.

---

#### F3.6 — Per-type event payload schemas not cross-referenced from role CLAUDE.md / skills

**What.** Per-type payload schemas exist at `shared/schemas/events/<event_type>.schema.json` for `task_started`, `template_coverage_checked`, `feature_state_changed`, `human_escalation`, and others. Neither role CLAUDE.md files nor skill files cross-reference these schema paths. F1 had 3 recurring validation-cycle failures: subagents constructed `task_started` payloads from prior event log patterns (which used `issue` field from `task_completed` convention), then failed validation (`issue_url` is required). F2 preamble clause 3 explicitly named the schema paths; 0 validation failures from schema-field confusion across all F2 subagents (P5 positive observation).

**Evidence.** F1 S5, S7, S13 (each failed on first `task_started` attempt); F2 overall (0 instances with schema cross-reference clause — preamble effectiveness confirmed).

**2-feature evidence:** ✅

**Decision.** Fix in Phase 3. Add inline schema-path cross-references in the relevant role CLAUDE.md files and skills wherever specific event types are mentioned (e.g., "emit `task_started` — payload schema: `shared/schemas/events/task_started.schema.json`"). WU 3.11 (same WU as F3.5 — both are shared-rules / CLAUDE.md additions).

---

#### F3.7 — issue-drafting SKILL.md worked example `deliverable_repo` stickiness

**What.** The issue-drafting SKILL.md worked example uses `deliverable_repo: clabonte/orchestrator` because Phase 2 had no separate specs repo. F1 was the first walkthrough with a live specs repo (`Bontyyy/orchestrator-specs-sample`). Both F1 S4 and F2 S4 required explicit prompt guidance to override the worked example. F2 S4 quote: "My first mental model before reading the F3.7 mitigation clause was 'I should use [clabonte/orchestrator] for T02 and T04.'" Additionally, the work-unit-issue.md v1.1 template carries `# Example: deliverable_repo: clabonte/orchestrator` as a comment — a secondary latent risk for any cold invocation without the mitigation clause.

**Evidence.** F1 S4 friction note (PF-3 confirmed); F2 S4 friction note (explicit mental-model override required).

**2-feature evidence:** ✅

**Decision.** Fix in Phase 3. Update issue-drafting SKILL.md worked example to use `<owner>/<repo>` placeholder with a note that the Phase-2-era `clabonte/orchestrator` target was pre-specs-repo; also update the work-unit-issue.md template comment to use a generic `<owner>/<repo>` placeholder. WU 3.10 (same WU as F3.4 — both are issue-drafting SKILL.md edits).

---

#### F3.8 — T04 qa_curation issue body contradicts SKILL empty-curation branch

**What.** PM issue-drafting (F1 S4) generated T04's issue body with acceptance criteria saying "A PR is opened against `main` on specs-sample." qa-curation SKILL.md §Step 7 explicitly says "Do NOT open a PR, do NOT create a branch" for the empty-curation case. F1 S13 subagent had to re-read SKILL §Step 7 a second time to confirm the SKILL governs over the issue ACs — a recoverable ambiguity, but a documentation gap between two skills.

**Evidence.** F1 S13 friction note (1-feature, but no second walkthrough exercised empty-curation again due to F2 producing a non-empty curation).

**Decision.** Fix in Phase 3 (marginal Phase 4 gate — qa-curation is the first and most frequently exercised QA skill post-Phase-3; perpetuating the contradiction would confuse future operators). Fix: either add conditional AC language to issue-drafting's qa_curation task template ("A PR is opened … UNLESS the curation pass produces zero candidates"), or add an explicit cross-reference note in qa-curation §Step 7 empty-branch. WU 3.12.

---

#### F3.9 — task-decomposition SKILL.md header says "7 steps"; body has 8

**What.** Step 1 subagent noted the count mismatch: SKILL header description says "7 steps" but the procedure body is numbered 1–8. The task description's "Step 6: validate" maps to SKILL.md's step 7, and "Step 7: write" maps to step 8. Caused momentary counting confusion (not a blocker).

**Evidence.** F1 S1 friction note.

**Decision.** Fix in Phase 3 (trivial one-line fix; cheap enough that deferring manufactures friction). WU 3.12 (same WU as F3.8).

---

#### F3.10 — `validate-event.py` `/dev/stdin` broken on macOS

**What.** Skills and verify-before-report.md instruct agents to "pipe the constructed event through validate-event.py." On macOS, `/dev/stdin`-based invocations fail with exit 2 ("file not found: /dev/stdin"). F1 had 4+ recurring instances across S3, S5, S7, and S13 — each time the subagent had to fall back to writing a temp file and passing `--file`. F2 preamble clause 4 codified the `--file` workaround explicitly; 0 instances in F2.

**Evidence.** F1 recurring (4 sessions affected); F2 (0 with explicit preamble clause — mitigation effective).

**Decision.** Fix in Phase 3 (2-feature cross-feature evidence via mitigation confirmation). Options: (a) fix `validate-event.py` to handle `/dev/stdin` correctly on macOS, OR (b) update SKILL.md and verify-before-report.md to prescribe the `--file /tmp/event.json` pattern as canonical, replacing the pipe/stdin references. Option (b) is the safer fix; option (a) additionally removes the root cause. WU 3.11 (same WU as F3.5/F3.6 — shared-substrate update).

---

#### F3.13 — Early-session timestamp synthesis produced non-chronological event log

**What.** F1 Sessions 1–4 subagents synthesized timestamps from context rather than wall-clock `date -u`. Notable: S4 (issue-drafting) produced events timestamped `2026-04-23T22:07Z` — one full day before other sessions (`2026-04-24`). The event log therefore had non-monotonic timestamps. From S5 onwards, the explicit `date -u +%Y-%m-%dT%H:%M:%SZ` prompt discipline fixed the pattern.

**Evidence.** F1 S4 timestamp anomaly; S3 timestamp anomaly; gap resolved from S5 onwards via prompt discipline.

**Decision.** Fix in Phase 3. Add an explicit clause to `verify-before-report.md` §3 (or the relevant shared rule): "Timestamps on events must be produced via `date -u +%Y-%m-%dT%H:%M:%SZ` at emission time; never synthesize from context, memory, or prior log entries." WU 3.11.

---

#### F3.14 — `task_completed` uses `issue` field; `task_started` uses `issue_url` — schema inconsistency

**What.** `task_created` payloads carry `issue` (bare `<owner>/<repo>#<N>` reference); `task_started` payloads carry `issue_url` (full URL). The asymmetry is schema-validated (both per-type schemas enforce their respective field name) but unintuitive: subagents in F1 S13 initially used `issue` for `task_started`, failing validation. The asymmetry crosses two per-type schemas touching the same logical entity.

**Evidence.** F1 S13 first-attempt failure (schema rejected `issue` on `task_started`).

**Decision.** Fix in Phase 3 (Phase 4 gate: specs-agent and any future roles emitting task lifecycle events will inherit the inconsistency and pay the discovery cost). Fix: standardize on `issue_url` (full URL) across all task lifecycle event types; update `task_created` per-type schema and add it as part of the schema-hygiene pass. WU 3.11.

---

#### F3.25 — `validate-event.py` rejects pretty-printed JSON (JSONL is line-per-event)

**What.** F2 S1 subagent first attempted validation with a pretty-printed multi-line JSON object. `validate-event.py` expects JSONL (one JSON object per line); multi-line input produced 12 validation errors (one per line). Preamble clause 4 covered the `--file` pattern but did not warn about the single-line JSONL requirement. One verification cycle burned.

**Evidence.** F2 S1 friction note.

**Decision.** Fix in Phase 3 (Phase 4 gate: JSONL single-line requirement is a critical operational discipline that must be explicit). Update preamble / `verify-before-report.md` §3 to state: "Event JSON must be single-line (JSONL format) before passing to validate-event.py. Do not write pretty-printed JSON." WU 3.11.

---

#### F3.28 — JSONL append concatenation bug from `cat` without trailing newline

**What.** CRITICAL operational finding. F2 S4 subagent used the `cat temp_file >> events.jsonl` append pattern when the Write-tool output file had no trailing newline. Result: 6 events were concatenated onto a single line in the JSONL file, producing a JSONDecodeError on the next validation attempt. The subagent detected the corruption via `tail -6 | python3 -m json.tool` (which threw "Extra data"), then recovered via `JSONDecoder.raw_decode()` loop + rewrite. No canonical JSONL append pattern is documented anywhere in the shared rules or skills.

**Evidence.** F2 S4 session report (critical operational — event log corrupted on first attempt, required out-of-band recovery).

**Decision.** Fix in Phase 3 (operational correctness; no second-chance recovery if the corruption is not caught). Document the canonical safe append pattern in `verify-before-report.md` §3: `printf '%s\n' "$(cat /tmp/event.json)" >> events/FEAT-YYYY-NNNN.jsonl` — the `printf '%s\n'` wrapper guarantees the newline separator regardless of the source file's trailing-newline state. WU 3.11.

---

#### F3.29 — Missing plan-file fallback flow undocumented in issue-drafting

**What.** `issue-drafting/SKILL.md` Step 2 documents reading a plan-file's `### Work unit prompt` sections per task. F2 had no plan-file (the plan-review step was scaffolded rather than fully executed as a dedicated subagent session). The F2 S4 subagent fell back to deriving work-unit prompts from the feature registry description — structurally acceptable but an undocumented deviation from the SKILL's prescribed flow. In a production context, the absent plan-file would warrant a `spec_level_blocker` escalation; the subagent continued for walkthrough continuity and flagged the gap.

**Evidence.** F2 S4 friction note.

**Decision.** Fix in Phase 3 (Phase 4 gate: plan-file presence/absence affects issue-drafting behavior silently). Document the fallback path explicitly in issue-drafting SKILL.md: "If no plan file exists (e.g., plan-review was handled inline), derive work-unit prompts from the feature registry's per-AC descriptions. This is the fallback path. In production, absent plan-file is a `spec_level_blocker` escalation condition if the task graph is non-trivial." WU 3.10.

---

#### F3.36 — qa-curation sole-test retirement violates `test-plan.schema.json` `minItems:1`

**What.** F2 S19 qa-curation subagent evaluated a dedup candidate: retiring a `widgets-listing-default-slice-50-count` test from `FEAT-2026-9001.md` because an equivalent test existed in `FEAT-2026-0007.md`. However, `FEAT-2026-9001.md` had exactly one test. Removing it would produce an empty `tests[]` array, violating `test-plan.schema.json`'s `minItems:1` constraint. The subagent discovered this at commit time (via schema validation) and correctly rolled back the dedup candidate, recording the refusal reason in `refused_candidates[]`. SKILL.md §Step 4 does not document this pre-flight check.

**Evidence.** F2 S19 curation output (`refused_candidates[]` entry with explicit "violates `tests[].minItems: 1`" reason); F2 S19 friction note.

**Decision.** Fix in Phase 3 (Phase 4 gate: qa-curation is a core QA skill; the sole-test edge case will recur as the regression suite grows). Add a `minItems:1` pre-flight check to qa-curation SKILL.md §Step 4: "Before committing a dedup or orphan retirement, verify that the target plan file will have at least one remaining test after the removal. If the candidate is the sole test in its plan, the retirement action is a whole-plan-file deletion (not a single test removal), and requires explicit human confirmation." WU 3.12.

---

### Deferred to Phase 4+ findings

#### F3.11 — SKILL.md files exceed 25k token read limit

**What.** `issue-drafting/SKILL.md` and `qa-curation/SKILL.md` both require chunked reads (2–3 offset/limit passes) because they exceed the Read tool's 25k-token per-read limit. Observed in F1 S4, F1 S13, F2 S4, F2 S19.

**2-feature evidence:** ✅ (but low severity — mechanical workaround, no content loss).

**Decision.** Defer to Phase 4+. The content is load-bearing at v1; trimming would require design decisions about what to remove. Home: any Phase 4+ WU that significantly revises these SKILL.md files for other reasons, triggering a natural prose-economy pass.

---

#### F3.15 — Task lifecycle events have no per-type schema (envelope-only validation)

**What.** Nine event types (`task_graph_drafted`, `task_created`, `task_ready`, `task_completed`, `plan_approved`, `spec_issue_raised`, `override_applied`, `override_expired`, `dependency_recomputed`) have no per-type payload schema. `validate-event.py` silently passes envelope-only. Subagents noted the silent pass but it did not block any session.

**Decision.** Defer to Phase 4+. Adding per-type schemas for all 9 event types is a meaningful schema-authoring effort that is best done when those event types are actively being extended or when a schema-governance WU is scoped. Home: Phase 5 (generator feedback loop) if it introduces schema-governance automation; or opportunistic during any Phase 4+ WU that adds a new event type to the same set.

---

#### F3.16 — "Done" derivation signal priority undocumented

**What.** Three signals for "task is done": `state:done` label, GitHub issue `state == CLOSED`, `task_completed` event. dep-recomputation SKILL reads the label. Priority ordering is undocumented; in failure recovery, signals could disagree.

**Decision.** Defer to Phase 4+. Happy-path safe; the conflict only matters during recovery scenarios. A one-line clarification in dep-recomputation SKILL ("canonical signal is the GitHub label; divergence = escalation") is the eventual fix. Home: the first WU that touches dep-recomputation SKILL for other reasons, or Phase 5 merge-watcher agent design.

---

#### F3.17 — `## Scope` cardinality clause wording ambiguity

**What.** F1 S1 subagent briefly confused a feature's `## Scope` clause (describing default cardinality) with a cardinality-override directive. The confusion was self-resolved correctly; no behavioral impact.

**Decision.** Defer to Phase 4+. Low severity; the SKILL's collapse-only rule makes prescriptive-expansion misinterpretation safe. Home: any Phase 4+ revision of task-decomposition SKILL.md.

---

#### F3.22 — Rule 1 (`qa_execution never auto`) conditional parsing friction

**What.** The phrase "if `autonomy_default != auto`" in QA SKILL preamble required a reasoning step to parse correctly when the autonomy setting was non-standard. Minor ergonomic.

**Decision.** Defer to Phase 4+. Low severity. Home: qa-execution SKILL.md revision during Phase 4 or any QA-skill-touching WU.

---

#### F3.24 — T04 `## Deliverables` section forward-looking reference

**What.** Issue-drafting generates T04 (qa_curation) with a `## Deliverables` reference to the test plan path (`/product/test-plans/FEAT-YYYY-NNNN.md`), which doesn't exist at issue-creation time (T02 qa-authoring hasn't run yet). The forward-looking assertion can mislead agents that read it before T02 completes.

**Decision.** Defer to Phase 4+. This is a design tension between the issue-drafting skill's "write complete issues up-front" posture and the temporal reality of QA deliverables. The eventual fix (conditional `## Deliverables` language or removal of forward path references) requires a design decision on issue completeness vs. accuracy. Home: Phase 4+ QA skill revision or plan-review skill evolution.

---

#### F3.27 — template-coverage-check SKILL entry-condition expects `state == planning`

**What.** SKILL.md entry check expects feature `state == planning`, but the walkthrough scaffolding runs the skill after the `plan_review → generating` transition. F2 S3 flagged this as a sequence gap; F1 S3 hit the same pattern without flagging.

**Decision.** Defer to Phase 4+. The practical fix is a one-line clarification ("re-runs during `generating` are permitted; coverage can be validated at any pre-execution state"). Low severity. Home: template-coverage-check SKILL.md revision opportunistically.

---

#### F3.31 — `source: component:<bare_name>` format

**What.** The `source` field uses `component:<bare_repo_name>` (e.g., `component:orchestrator-api-sample`) rather than `component:<owner>/<repo>`. F2 S5 subagent briefly re-read the schema to confirm the convention.

**Decision.** Defer to Phase 4+. Schema-documented; ergonomic friction only. Home: any Phase 4+ schema-hygiene pass.

---

#### F3.32 — Cardinality wording "expected" ambiguous

**What.** Feature registry `## Scope` used "three tests expected under the default cardinality convention" — ambiguous between confirmatory ("we expect this to happen") and prescriptive ("author exactly three tests"). F2 S7 flagged but correctly resolved via the SKILL's collapse-only rule.

**Decision.** Defer to Phase 4+. The SKILL's collapse-only rule makes prescriptive-expansion misinterpretation safe; the wording is the human's to improve in future feature specs. No code or skill change needed. Home: documentation conventions note in specs-sample or Phase 4 specs-agent guidance.

---

#### F3.33 — `tail -1 log | json.tool` fails on blank trailing line

**What.** Preamble clause 5 in F2 instructed `tail -1 log | python3 -m json.tool > /dev/null` as a quick event-append verification. JSONL files with a terminal newline produce a blank trailing line that `json.tool` rejects with exit 1. F2 S9 proposed the fix: `grep -v '^[[:space:]]*$' log | tail -1 | json.tool`.

**Decision.** Defer to Phase 4+ (update future preambles and documentation). The root cause is a documentation gap in verify-before-report.md's event-validation examples. Home: next WU that touches verify-before-report.md §3.

---

### Won't-fix-with-rationale findings

#### F3.26 — `feature_state_changed` payload uses `from_state`/`to_state` (not `from`/`to`)

**What.** F2 S2 (orchestration session, Opus 4.7) hit a validation error on first attempt because it used `from`/`to` instead of the schema's `from_state`/`to_state`. One verification cycle burned.

**Rationale.** The schema field names are correct and well-motivated (`from` and `to` are extremely common abbreviations that would collide with dozens of other conventions; `from_state` / `to_state` are explicit and unambiguous). The fix is not to rename the fields — it is to cross-reference the schema in the emission point documentation, which is covered by F3.6's Fix-in-Phase-3 WU 3.11. No standalone fix warranted; the issue resolves as a side-effect of the F3.6 cross-reference work. Recording as Won't-fix to avoid double-counting.

---

#### F3.30 — IDE1006 lint rule surfaces at `dotnet format`, not `dotnet build`

**What.** F2 S5 burned one verification cycle when `dotnet format --verify-no-changes` flagged a private const naming convention (`DefaultPageSize` → `_defaultPageSize`) enforced by the project's `.editorconfig`. This convention is project-specific and not documented in `.specfuse/verification.yml` or any spec.

**Rationale.** This is inherently a project-specific lint rule. The orchestrator's shared verification skill cannot enumerate every component repo's `.editorconfig` conventions; nor should it. The correct fix is that component repos document their lint conventions in their own `README.md` or verification config, and agents run `dotnet format --verify-no-changes` as part of the standard lint gate (which is already prescribed). F2 S5 recovered correctly in one cycle. No shared-rule change is warranted. Won't fix globally; the owning component repo (`orchestrator-api-sample`) may document it locally if desired.

---

#### F3.35 — Operator rejection-of-successful-subagent due to partial state visibility

**What.** During F2 S19, the orchestration session (Opus 4.7) misinterpreted an IDE system-reminder about a file modified by the subagent as an accidental user edit and prematurely interrupted the subagent + closed PR #3. The subagent had in fact completed successfully. Recovery required recognizing the subagent was done, locating the branch commit in the git object store, pushing, and reopening PR #3.

**Rationale.** This is an operator-discipline finding, not a skill or documentation gap in the orchestrator substrate. The correct response is for the operator to check `git log --oneline` + event log state before interrupting a subagent in response to an IDE notification. A note in walkthrough operational guidance (notes-scratch.md pattern) is sufficient. Adding this to shared rules or SKILL.md would over-scope a meta-level observation. Won't fix in the orchestrator code base; noted here for future walkthrough operators.

---

### Observation-only findings

The following findings are recorded for completeness but require no action. They are direct inputs to future phase design decisions or reflect correctly-functioning behavior.

- **F3.12** — Cross-repo `Closes` directive: **reclassified from F1's "auto-close does NOT fire cross-repo" to "auto-close works for same-owner cross-repo, may not for cross-owner."** F2 S8 provided counter-evidence (same-owner `Bontyyy/*` → `Bontyyy/*` closed issues automatically). The original F1 F3.12 claim was over-broad. The correct characterization: cross-owner cross-repo auto-close is unconfirmed; same-owner cross-repo works on GitHub. Input for Phase 5 merge-watcher agent design.

- **F3.18** — Prescribed `commit_sha` didn't match local api-sample HEAD at qa-execution time. Walkthrough procedure gap (subagent should `git fetch + checkout main + pull` before service startup). Input for future walkthrough operational checklists.

- **F3.19** — v1 prose `expected` predicate is weak for stateful environments (oracle required if DB has pre-existing data). Acknowledged in qa-execution SKILL §"Deferred integration." Input for Phase 4 machine-evaluable predicate language selection.

- **F3.20** — Coverage report path is a directory, not a file; subagent used `find` to locate `coverage.cobertura.xml`. Component-repo-specific. No action.

- **F3.21** — Lint gate exit 0 returns empty stdout; convention "empty output = pass" is implicit. No action; low severity.

- **F3.23** — `decomposition_pass` counting requires defensive fallback (`ls && grep || echo file_not_found`). Documented behavior per Phase 2 retrospective F1.11. No further action.

- **F3.34** — Background task exit signal misleading for persistent service processes. `run_in_background: true` on `dotnet run` detaches immediately; readiness polling is the actual gate. Operational awareness note; no skill change needed.

---

## Fix-in-Phase-3 work plan

Sixteen findings qualify for Fix-in-Phase-3, grouped into five cohesive follow-up WUs by the surface they touch. Each WU is independently landable in any order; the suggested sequence below reflects cohesion, not strict dependency.

### WU 3.8 — Component agent verification skill pre-gate build step (Phase 1 Finding 8 absorption)

**Scope.** Amend `agents/component/skills/verification/SKILL.md` to add an explicit mandatory pre-gate build step: before running any gate that uses `--no-build` (tests, coverage), the agent must run `dotnet restore && dotnet build` to ensure binaries are current. This is an additive documentation-only change to the Phase 1 frozen surface — the Phase 1 retrospective authorized this correction opportunistically ("carry into the next edit of verification/SKILL.md"). Verification.yml schema change (requiring a named `build` gate before `--no-build` gates) is an optional complementary enhancement; document the pre-step in SKILL.md as the minimum.

**Findings absorbed.** F3.1 (Phase 1 Finding 8 live 2-feature evidence).

**Rationale.** The 2-feature live evidence (F1 S5 + F2 S5) satisfies the Phase 1 retrospective's "next edit of verification/SKILL.md" dispatch condition. Both walkthroughs confirmed the stale-artifact trap is real on fresh checkouts. This is the cheapest Phase 3 WU: additive documentation on an already-frozen surface, no schema change required.

---

### WU 3.9 — QA agent skill delivery convention + port convention

**Scope.** Add a `## Delivery convention` section to `qa-authoring/SKILL.md` specifying: branch name pattern (`qa-authoring/<task_correlation_id>`), commit message template, PR title format, PR body must include `Closes <owner>/<repo>#<N>` referencing the T02 issue, stop-at-open discipline (subagent stops after PR open; does NOT merge or close). Add a companion note on port discovery: the authoring agent is responsible for discovering the component's declared runtime port from `launchSettings.json` (or equivalent) and including a startup command as `commands[0]` in the test plan (e.g., `dotnet run --project <path> --urls "http://localhost:<port>" &`), or explicitly noting the port assumption in `## Coverage notes`.

**Findings absorbed.** F3.2 (PR convention unspecified), F3.3 (port convention silent).

**Rationale.** Both findings are qa-authoring SKILL.md additions on the same surface. 2-feature evidence on both. Handling together avoids two separate passes on the same SKILL file.

---

### WU 3.10 — PM agent issue-drafting and feature-state-transition discipline

**Scope.** (1) Add an explicit emission step to `issue-drafting/SKILL.md`: after emitting the first round of `task_created` / `task_ready` events, the skill emits `feature_state_changed(generating → in_progress, trigger=first_round_issues_opened)` before reporting `task_completed`. This closes the skill-ownership gap for the `generating → in_progress` transition. (2) Update `issue-drafting/SKILL.md` worked example's `deliverable_repo` value from `clabonte/orchestrator` to `<owner>/<repo>` (the product specs repo for the current deployment) with a dated note that the Phase-2-era value was pre-specs-repo. (3) Update `shared/templates/work-unit-issue.md` v1.1's example comment from `clabonte/orchestrator` to `<owner>/<repo>`. (4) Document the plan-file fallback path: if no plan file exists, derive work-unit prompts from feature registry ACs; note that in production this is a `spec_level_blocker` escalation condition for non-trivial task graphs.

**Findings absorbed.** F3.4 (generating → in_progress ownerless), F3.7 (worked example stickiness), F3.29 (plan-file fallback undocumented).

**Rationale.** All three findings touch the issue-drafting SKILL.md surface. F3.4 and F3.29 are behavioral gaps (missing emission step; missing fallback documentation). F3.7 is a documentation gap on the same file. Fixing together concentrates the SKILL.md churn in one review pass.

---

### WU 3.11 — Shared substrate operational discipline

**Scope.** Multiple targeted additions to `shared/rules/verify-before-report.md` §3 and related shared surfaces:
- (F3.5) Codify: "Do NOT `git commit` on the orchestration repo from within a role-switch subagent session. Append events to the JSONL log file; leave the commit to the orchestration session or human operator."
- (F3.6) Add inline schema-path cross-references in `agents/qa/CLAUDE.md` and `agents/component/CLAUDE.md` for the event types each role emits (e.g., `task_started` → `shared/schemas/events/task_started.schema.json`).
- (F3.10) Update verify-before-report.md §3 validate-event.py invocation pattern: prescribe `--file /tmp/event.json` as canonical; remove or annotate the stdin pipe references as macOS-incompatible.
- (F3.13) Add explicit timestamp discipline: "Use `date -u +%Y-%m-%dT%H:%M:%SZ` at emission time; never synthesize timestamps from context, memory, or log history."
- (F3.14) Standardize task lifecycle event `issue` reference field: use `issue_url` (full URL) on both `task_started` and `task_created` per-type schemas; update `task_created` per-type schema if it currently uses the bare-reference format.
- (F3.25) Add note: "Event JSON must be single-line (JSONL format) before passing to validate-event.py; do not pass pretty-printed JSON."
- (F3.28) Document canonical JSONL append pattern: `printf '%s\n' "$(cat /tmp/event.json)" >> events/FEAT-YYYY-NNNN.jsonl` — guarantees newline separator regardless of source file trailing-newline state.

**Findings absorbed.** F3.5, F3.6, F3.10, F3.13, F3.14, F3.25, F3.28.

**Rationale.** Seven findings touch shared operational discipline (event-append mechanics, timestamp discipline, schema discoverability, orchestration-repo commit discipline) rather than any single skill. Concentrating them in one WU minimizes the number of PR review passes on the shared substrate and ensures the shared discipline document is coherent after the WU lands.

---

### WU 3.12 — QA agent skill + PM skill documentation polish

**Scope.** Four targeted documentation fixes across the QA and PM skill surfaces:
- (F3.8) Add conditional AC language in issue-drafting's qa_curation task template, OR add an explicit cross-reference note in qa-curation SKILL.md §Step 7 empty-curation branch: "The issue body's AC ('A PR is opened') describes the non-empty path. If the curation pass produces zero candidates, per §Step 7 no PR is opened and no branch is created; this SKILL governs over the issue AC."
- (F3.9) Fix task-decomposition SKILL.md header description: change "7 steps" to "8 steps" (or adjust the step count to match the header if a step can be merged).
- (F3.36) Add `minItems:1` pre-flight check to qa-curation SKILL.md §Step 4: "Before committing a dedup or orphan retirement, verify the target plan file will have at least one test remaining. If the candidate is the plan's sole test, the retirement option is whole-plan-file deletion, which requires explicit human confirmation — do not remove the sole test entry and leave an empty `tests[]` array."

**Findings absorbed.** F3.8, F3.9, F3.36.

**Rationale.** All three findings are documentation-only fixes on QA and PM SKILL.md files. F3.8 and F3.36 are in qa-curation and issue-drafting respectively; F3.9 is in task-decomposition. Grouping these low-effort polish items together keeps them from being deferred indefinitely as "too small for their own WU."

---

## Deferred to Phase 4+

Ten findings defer with explicit home phases:

| Finding | Description | Home Phase |
|---|---|---|
| F3.11 | SKILL.md files exceed 25k token read limit | Phase 4+ — any WU that significantly revises issue-drafting or qa-curation SKILL.md for other reasons |
| F3.15 | Task lifecycle events have no per-type schema (envelope-only) | Phase 5 — schema-governance automation or any WU introducing new event types in the same set |
| F3.16 | "Done" derivation signal priority undocumented in dep-recomputation | Phase 5 — merge-watcher agent design (which is the authoritative resolver of the label/issue-state/event-log triple) |
| F3.17 | `## Scope` cardinality clause wording ambiguity | Phase 4+ — any revision of task-decomposition SKILL.md |
| F3.22 | Rule 1 `qa_execution never auto` conditional parsing friction | Phase 4+ — qa-execution SKILL.md revision |
| F3.24 | T04 `## Deliverables` forward-looking reference | Phase 4+ — design decision on issue completeness vs. accuracy; input for plan-review skill evolution |
| F3.27 | template-coverage-check entry-condition expects `state == planning` | Phase 4+ — any revision of template-coverage-check SKILL.md |
| F3.31 | `source: component:<bare_name>` format | Phase 4+ — schema-hygiene pass |
| F3.32 | Cardinality wording "expected" ambiguous | Phase 4+ — specs-agent guidance (Phase 4) or documentation conventions |
| F3.33 | `tail -1 log | json.tool` fails on blank trailing line | Phase 4+ — next revision of verify-before-report.md §3 |

**Phase 1 Finding 8 — RESOLVED in Phase 3 (WU 3.8).** The Phase 2 retrospective listed this as a Phase 3+ carry-item. Phase 3 walkthroughs provided 2-feature live evidence satisfying the "next edit of verification/SKILL.md" dispatch condition. WU 3.8 closes this item.

**F2.10 — escalation_resolved event / inbox orphaning — RESOLVED in WU 3.4.** The Phase 2 retrospective deferred this to Phase 3. WU 3.4 introduced the `escalation_resolved` event type and schema, closing the gap. No carry-forward.

## Regression-cycle negative result — Phase 4 carry

The qa-regression skill (`qa-regression/SKILL.md`) was **not exercised at runtime** in Phase 3. F2's regression-cycle primary path was blocked by the component agent correctly implementing the AC-3 edge case on first pass. This is a bounded negative result, not a blocking failure — the qa-regression SKILL was authored and reviewed (WU 3.4), but its live execution path remains unvalidated. Carry to Phase 4 as an explicit prerequisite: Phase 4 walkthroughs should include at least one regression-cycle feature where the implementation agent is likely to miss a non-obvious edge case, exercising the full `qa_execution_failed → qa-regression spawn → fix → re-execute → qa_execution_completed` path.

The Q4 cross-attribution resolution path (SKILL §"Deferred — cross-attribution resolution") was also not exercised (no regression loop → no cross-attribution scenario). Carry to Phase 4 alongside regression-cycle validation.

## Loose ends

Two loose ends deliberately preserved from the walkthroughs:

1. **Fixture features and plans on specs-sample.** Commits `d4276dc` (FEAT-2026-9001 / 9002 / 9003 fixture plans) and associated fixture inbox/event artifacts (`/inbox/qa-regression/FEAT-2026-9002-widgets-metadata-has-last-updated.md`, `events/FEAT-2026-9002.jsonl`) remain on the repos as permanent demo artifacts per the walkthrough decision (Option A). These are intentional; they serve as demonstration artifacts for the open-source release. No cleanup action required.

2. **4 unauthorized local commits from F1 subagents.** These were squashed into the F1 walkthrough-complete commit (`chore(phase-3): walkthrough feature 1 complete`, PR #38). No residual uncommitted local state should exist post-PR #38 merge.

## Outcome

WU 3.7 concludes Phase 3's triage work. The Phase 3 walkthroughs validated the QA agent across the happy-path shape (F1) and a backup qa-curation stress path (F2). The 36 findings were sorted into 16 Fix-in-Phase-3, 10 Defer-to-Phase-4+ (+ 2 resolved carry-items), 3 Won't-fix, and 7 Observations-only — with explicit rationales, 2-feature evidence documentation, and a concrete five-WU fix ladder.

Phase 3 is ready to proceed to the fix ladder once this retrospective merges. Phase 4 (specs agent and chat front-end) can start after Phase 3's fix WUs (3.8–3.12) ship and the freeze declaration is issued.

The Phase 3 freeze declaration is **not** recorded here. It will be issued by **WU 3.N (= WU 3.13)**, analogous to WU 1.12 and WU 2.15, after the fix ladder merges. That WU will enumerate the frozen QA-agent surface (qa-authoring, qa-execution, qa-curation, qa-regression skills + QA CLAUDE.md v1.4.x) and carry the Deferred-to-Phase-4+ list into Phase 4's inputs.
