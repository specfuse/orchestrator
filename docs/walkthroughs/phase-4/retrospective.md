# Phase 4 walkthrough — Retrospective (WU 4.7)

## Identity

- **Walkthrough:** Phase 4, WU 4.7 (retrospective over WU 4.6)
- **Scope:** triage of findings surfaced in Feature 1 (happy path) and Feature 2 (regression cycle + qa-regression runtime validation) of WU 4.6; disposition of Phase 3 carry items
- **Operator:** @Bontyyy (co-piloted with Claude as Opus 4.6)
- **Date conducted:** 2026-04-25
- **Inputs:** [feature-1-log.md](feature-1-log.md) (F4.1–F4.12 + P1–P5), [feature-2-log.md](feature-2-log.md) (F4.13–F4.16 + P6–P10 + regression path documentation + Q4 audit), [orchestrator-implementation-plan.md](../../orchestrator-implementation-plan.md) §"Phase 4", the feature registry entries for `FEAT-2026-0008` and `FEAT-2026-0009`, the JSONL event logs for both features (27 + 34 events), the Phase 3 retrospective's carry list (10 deferred findings + 3 negative-result carry items), and the Phase 3 retrospective as structural reference.
- **Status:** triage complete; Fix-in-Phase-4 work plan staged; items deferred to Phase 5+ tagged and cross-referenced; Phase 3 carry items dispositioned.

## Objective

Triage the 16 findings surfaced across the two WU 4.6 features (F4.1–F4.16) and decide, for each, whether it must be fixed before the Phase 4 specs-agent configuration freeze or can be deferred to Phase 5+. Produce a concrete work plan for the Phase 4 fixes and a documented handoff list for the deferred items.

Additionally, disposition the 13 Phase 3 carry items that Phase 4 was supposed to exercise or absorb: F3.32 (absorbed by WU 4.3 — verify it landed correctly); the three negative-result carry items (qa-regression runtime validation, Q4 cross-attribution resolution, "first round" semantics refinement); and the nine re-deferred findings (F3.11, F3.15, F3.16, F3.17, F3.22, F3.24, F3.27, F3.31, F3.33).

Per the implementation plan, WU 4.7 is the decision artifact. Execution of the Fix-in-Phase-4 items themselves is carried by subsequent Phase 4 work units (WU 4.8), each independently landable. The Phase 4 freeze declaration is explicitly **not** recorded here — it is the scope of the final Phase 4 work unit (WU 4.9), analogous to WU 1.12, WU 2.15, and WU 3.13.

## Walkthrough outcome

Both WU 4.6 acceptance criteria were met, with one qualification on the regression-cycle path:

| Criterion | Feature | ID | Shape | Outcome |
|---|---|---|---|---|
| 1 — happy path, specs-to-QA full pipeline, single-repo | 1 | `FEAT-2026-0008` | Specs intake + drafting + validation + PM decomposition + issue-drafting + component impl + QA authoring + execution + curation; feature reached `done` | Feature at `state: done`; 27 events, all validate |
| 2 — regression cycle + qa-regression runtime validation | 2 | `FEAT-2026-0009` | Happy-path block (S1–S9) + induced regression (S9 fallback) + qa-execution FAIL (S13) + qa-regression FIRST RUNTIME (S14) + fix (S16) + re-execution PASS (S18) + regression resolution (S19) + curation + close | Feature at `state: done`; 34 events, all validate; qa-regression exercised via fallback; Q4 invariant held |
| Specs-to-PM handoff — first-ever runtime exercise | both | — | `validating → planning` transition clean in both features; PM agent picked up without manual state-bumping | P1 confirmed |
| Q4 cross-attribution invariant | 2 | — | Zero writes to T01 issue #29 during full regression cycle (filing, fix, re-execution, resolution) | P7 confirmed |

The specs agent configuration v1.0.0 (`agents/specs/CLAUDE.md` + four skills feature-intake / spec-drafting / spec-validation / spec-issue-triage) executed correctly across both the happy-path shape and the regression-cycle shape. The specs-to-PM handoff — the first runtime exercise of the `validating → planning` transition — worked as designed in both features without manual state-bumping. All findings are documentation gaps in the Phase 4 skills or cross-phase observations, not configuration correctness bugs. Every event validated through `scripts/validate-event.py` on every append (61 events total across the two features).

**Regression-cycle qualification.** The qa-regression skill was exercised via the **fallback path**: the component agent (Sonnet 4.6) implemented AC-3's atomicity correctly on first pass — the same outcome as Phase 3. The walkthrough operator manually introduced a regression (commit `bba7afa`) by refactoring `BulkCreateAsync` to interleave validation and persistence. The qa-regression skill then executed cleanly on its first-ever runtime invocation, producing correct artifacts (inbox file + `qa_regression_filed` event + `qa_regression_resolved` event). Q4 invariant held throughout. The finding is qualified: "validated via induced regression, not organic."

**"First round" semantics observation.** F1 and F2 provided contrasting evidence:
- F1: `generating → in_progress` fired at 15:36:30Z, **after all 4 task_created events** (last T04 at 15:36:07Z). Trigger: `first_round_issues_opened`. Effectively "all tasks opened."
- F2: `generating → in_progress` fired at 16:42:31Z, **after T01's task_created (16:42:29Z) + task_ready (16:42:30Z) but BEFORE T02/T03/T04**. This is "first task opened."

**Conclusion:** The v1 "first-task-opened" semantics is what the SKILL.md §Step 12 guard specifies and F2 demonstrates. F1's "all tasks opened" was coincidental timing in a batched session — the guard checked after all 4 issues had been opened, not because of a different semantic. No finding; no refinement needed at this time.

## Triage criteria

Every finding was scored against three questions, mirroring Phase 3's pattern adjusted for Phase 4's evidence shape. A "yes" on any of them qualifies the finding for **Fix in Phase 4**; otherwise it is **Deferred to Phase 5+**, **Won't fix**, or **Observation only**.

1. **Does it gate Phase 5?** If the generator feedback loop (Phase 5's deliverable), the merge-watcher agent, or any subsequent automation would either re-encounter the finding on its first real task or inherit a broken contract from the current Phase 4 configuration, the finding must be fixed before Phase 5 starts. The inheritance case matters: anything a Phase 5 agent would copy — event-emission patterns, skill templates, shared schemas, spec-drafting conventions — is cheaper to fix once in Phase 4 than separately in every downstream role.

2. **Is there 2-feature evidence?** A finding surfaced in both Feature 1 and Feature 2 — or confirmed by a second walkthrough feature independently resolving the same ambiguity — is not a single-session artifact; it is a reproducible failure of convention or a real ambiguity in the skill text. Two independent features is the evidence threshold (mirroring Phase 2 and Phase 3 thresholds).

3. **Is the cost of deferring greater than the cost of fixing now?** Some single-feature findings are cheap enough to fix (a one-sentence clarification, a trigger value standardization) that deferring them manufactures friction for no saving. Applied sparingly — the default on single-feature findings is to defer unless the forward cost is obviously larger or the surface touched is already being revisited.

Findings that fail all three tests defer by default. The deferred list is not "won't fix" — it is "fix when the context to fix it is already open."

**Phase 4 surface boundary.** Findings that require changes to Phase 1, 2, or 3 frozen surfaces (component agent, PM agent, QA agent, shared rules) are deferred regardless of severity — the freeze contract requires architectural justification for changes. Findings on the Phase 4 active surface (specs agent CLAUDE.md + four skills) are evaluated on the three criteria above.

## Findings triage

Sixteen findings total: F4.1–F4.12 from Feature 1 (12 findings + 5 positive observations P1–P5); F4.13–F4.16 from Feature 2 (4 findings + 5 positive observations P6–P10). Of the 16 triageable findings, 4 qualify for Fix-in-Phase-4, 4 defer to Phase 5+, 4 are Won't-fix-with-rationale, and 4 are Observation-only.

| # | Finding | Source | Cross-feature | Gate P5? | Decision |
|---|---|---|---|---|---|
| F4.3 | `trigger` field value discrepancy between SKILL.md and CLAUDE.md | F1 S3 + F2 S3 | F4.16 confirms | Yes | **Fix in Phase 4** |
| F4.5 | `## Related specs` contains GitHub URL only, no local path | F1 S4 + F2 S7 | yes | Yes | **Fix in Phase 4** |
| F4.12 | Spec-drafting session does not commit to specs-sample | F1 S10 + F2 S10 | yes | Yes | **Fix in Phase 4** |
| F4.16 | F4.3 confirmed cross-feature | F2 S3 | — | — | **Fix in Phase 4** (merged with F4.3) |
| F4.6 | Capability-counting rule unclear for narrative specs | F1 S4 + F2 S4 | yes | No (PM frozen) | Defer Phase 5+ |
| F4.7 | template-coverage-check expects `state == planning` (= F3.27) | F1 S6 | no | No (PM frozen) | Defer Phase 5+ |
| F4.10 | Issue path bug: `product/features/test-plans/` vs `product/test-plans/` | F1 S10 | no | No (PM frozen) | Defer Phase 5+ |
| F4.13 | `dotnet test --no-build` false-green in qa-execution context | F2 S13 | no | No (QA frozen) | Defer Phase 5+ |
| F4.1 | `specfuse` CLI not installed — validation simulated | F1 S3 + F2 S3 | yes | No | Won't fix |
| F4.2 | Sandbox blocks `/tmp` writes; use `$TMPDIR` | F1 (recurring) + F2 (recurring) | yes | No | Won't fix |
| F4.8 | GitHub label and push permissions blocked pipeline | F1 S7 + F1 S8 | no | No | Won't fix |
| F4.15 | Branch protection blocks regression fallback | F2 S9 | no | No | Won't fix |
| F4.4 | Narrative-only spec (no OpenAPI file) — precondition satisfied | F1 S3 | no | No | Observation |
| F4.9 | Plan file absent — F3.29 fallback path correctly exercised | F1 S7 + F2 S7 | yes | No | Observation |
| F4.11 | Validation tests cite Scope clauses, not formal ACs | F1 S10 | no | No | Observation |
| F4.14 | Sonnet 4.6 implements explicit ACs correctly — regression trap design | F2 S8 | no | No | Observation |

---

## Per-finding triage sections

Grouped by triage bucket. Cross-feature pairs are treated in a single section.

---

### Fix-in-Phase-4 findings

#### F4.3 / F4.16 — `trigger` field value discrepancy between spec-validation SKILL.md and specs CLAUDE.md

**What.** The spec-validation SKILL.md worked example and procedure tables use `trigger: "human_requested_validation"` (Step 2) and `trigger: "validation_clean"` (Step 8c). The specs CLAUDE.md §Output surfaces uses `trigger: "validation_requested"` and `trigger: "validation_passed"`. The `feature_state_changed.schema.json` allows freeform trigger strings, so both pass validation — but subagents reading SKILL.md produce different trigger values than subagents reading CLAUDE.md. F1 S3 followed the preamble's values (`validation_requested` / `validation_passed`). F2 S3 confirmed the same discrepancy cross-feature.

**Evidence.** F1 S3 friction note; F2 S3 friction note (independent fresh-context subagent, identical finding — F4.16 is the cross-feature confirmation).

**2-feature evidence:** F4.16 confirms.

**Decision.** Fix in Phase 4. Standardize spec-validation SKILL.md's trigger values to match the CLAUDE.md values (`validation_requested` and `validation_passed`) — the role config is authoritative per the SKILL.md's own hierarchy clause ("When this file and CLAUDE.md disagree, the role config wins"). Update the worked example's event JSON and the Step 2/Step 8c tables. WU 4.8.

---

#### F4.5 — `## Related specs` contains GitHub URL only, no local-path reference

**What.** Spec-drafting produces a `## Related specs` section in the feature registry with GitHub URLs (e.g., `https://github.com/Bontyyy/orchestrator-specs-sample/blob/main/product/features/FEAT-2026-0008.md`). The PM agent's task-decomposition subagent operates on local clones, not GitHub URLs. F1 S4 subagent had to use `find` to locate the local clone after encountering the GitHub URL. F2 S7 friction notes include "spec path search" — same pattern.

**Evidence.** F1 S4 friction note (one failed Read + `find` workaround); F2 S7 friction note ("spec path search").

**2-feature evidence:** yes.

**Decision.** Fix in Phase 4. Update spec-drafting SKILL.md Phase 1 §"Output of Phase 1" to specify the `## Related specs` format: use repository-relative paths (e.g., `product/features/FEAT-2026-0008.md`) rather than full GitHub URLs. Repository-relative paths are portable across local clones and GitHub views. Add a note that full URLs can be used in addition to the relative path for human readers, but the primary reference must be a relative path consumable by downstream agents on local clones. WU 4.8.

---

#### F4.12 — Spec-drafting session does not commit to specs-sample

**What.** The spec-drafting skill produces spec files under `/product/` in the product specs repo but is silent on whether/how those files reach the repo via commit or PR. F1 S2 subagent was told "Do NOT push to GitHub" and left the feature narrative uncommitted. F1 S10 (qa-authoring) discovered the spec narrative was untracked in specs-sample — requiring a manual commit before the test plan PR could merge. F2 had the same pattern: spec narrative created by S2 but not committed.

**Evidence.** F1 S10 friction note (spec narrative never committed — manual correction required); F2 implicitly (same walkthrough pattern, same manual commit before T02 merge).

**2-feature evidence:** yes.

**Decision.** Fix in Phase 4. Add a `## Delivery convention` section to spec-drafting SKILL.md specifying: after the human approves the spec content (Phase 3 pre-validation review), the spec files should be committed to the product specs repo's `main` branch (or a feature branch with a PR, per the repo's convention). The spec-drafting skill's output is the committed spec files — uncommitted drafts are not a valid output state. This mirrors the PM agent's issue-drafting convention (WU 3.9) and the QA agent's qa-authoring convention (same WU). WU 4.8.

---

### Deferred to Phase 5+ findings

#### F4.6 — Capability-counting rule unclear for narrative specs without `### Behavior` headings

**What.** Task-decomposition SKILL.md v1.2's capability-counting rules are designed for OpenAPI specs (one operation = one capability). For narrative specs without `### Behavior` headings, the mapping from ACs to capabilities is ambiguous. F1 S4: 2 ACs treated as 1 behavior (single endpoint, two response branches). F2 S4: 3 ACs treated as 1 behavior (same reasoning). Both subagents resolved correctly but noted the gap.

**2-feature evidence:** yes.

**Decision.** Defer to Phase 5+. Fixing this requires amending task-decomposition SKILL.md, which is on the PM frozen surface (v1.2, frozen in Phase 3). The finding is a friction point, not a blocker — both subagents resolved the ambiguity correctly using sound reasoning. Home: Phase 5 task-decomposition SKILL.md revision, alongside any changes driven by multi-repo feature support.

---

#### F4.7 — template-coverage-check SKILL.md expects `state == planning` (= Phase 3 F3.27)

**What.** Same as Phase 3 F3.27. SKILL.md entry check expects feature `state == planning`, but walkthroughs run the skill after the `plan_review → generating` transition. F1 S6 flagged this; F2 S6 was skipped for efficiency (identical template surface). Phase 3 F3.27 documented the same pattern.

**Decision.** Defer to Phase 5+ (reaffirmed from Phase 3 disposition). The fix is a one-line clarification in template-coverage-check SKILL.md, but the SKILL.md is on the PM frozen surface (v1.1, frozen in Phase 2). Low severity — operator-directed invocation proceeds regardless. Home: any Phase 5+ revision of template-coverage-check SKILL.md.

---

#### F4.10 — Issue path bug: `product/features/test-plans/` vs `product/test-plans/`

**What.** Issue #25's Deliverables/Verification sections reference `product/features/test-plans/FEAT-2026-0008.md` — wrong path. The correct path per `test-plan.schema.json` and the specs-sample directory structure is `product/test-plans/FEAT-2026-0008.md`. The extra `features/` segment in the path is an issue-drafting bug — the PM agent constructed the path incorrectly.

**Evidence.** F1 S10 friction note.

**Decision.** Defer to Phase 5+. Fixing this requires amending the PM agent's issue-drafting SKILL.md or its worked example, which is on the PM frozen surface (v1.4, frozen in Phase 3). The qa-authoring subagent found the correct path anyway (schema-guided). Low severity. Home: Phase 5+ issue-drafting SKILL.md revision.

---

#### F4.13 — `dotnet test --no-build` false-green in qa-execution context

**What.** F2 S13 qa-execution subagent ran `dotnet test --no-build` against the regression commit (`bba7afa`). The stale binary from the pre-regression build was still present, producing 91/91 pass (false green). The HTTP-based atomicity test correctly caught the regression. This is Phase 1 Finding 8 manifesting in the qa-execution context — the component agent's verification skill has the pre-gate build step (WU 3.8), but the qa-execution skill does not prescribe build commands.

**Evidence.** F2 S13 friction note.

**Decision.** Defer to Phase 5+. Fixing this requires amending qa-execution SKILL.md, which is on the QA frozen surface (v1.0, frozen in Phase 3). The HTTP-based test plan approach is the correct execution method per qa-execution SKILL.md — the agent's choice to use `dotnet test --no-build` as an "authorized equivalent" was a deviation from the prescribed flow that happened to produce a false green. Home: Phase 5+ qa-execution SKILL.md revision, potentially adding a note that unit-test shortcuts require a fresh build.

---

### Won't-fix-with-rationale findings

#### F4.1 — `specfuse` CLI not installed — validation simulated

**What.** The Specfuse CLI was not installed on the walkthrough machine. Both F1 S3 and F2 S3 simulated clean validation passes with `validator_version: "simulated-1.0"`. The spec-validation SKILL.md's procedure was followed (attempt `specfuse validate`, report not-found, proceed with simulated pass per walkthrough protocol).

**Rationale.** This is a walkthrough infrastructure gap, not an orchestrator code or configuration issue. The spec-validation SKILL.md correctly handles the case where the validator is available — the procedure invokes `specfuse validate <file>` and interprets its output. The CLI's absence on the walkthrough machine is an operational setup task. Pre-walkthrough checklists for future walkthroughs should verify `specfuse` CLI availability. No code or skill change warranted.

---

#### F4.2 — Sandbox blocks `/tmp` writes; use `$TMPDIR`

**What.** Claude Code's sandbox environment blocks direct `/tmp` writes. Subagents across both features (recurring in every session) had to use `$TMPDIR` instead of `/tmp`. The SKILL.md examples and preamble clauses that reference `/tmp/event.json` or `/tmp/event-check.json` do not match the sandbox's write restrictions.

**Rationale.** This is a Claude Code environment constraint, not an orchestrator design issue. The SKILL.md examples use `/tmp/` as a conventional temp-file path that is correct on standard Unix systems. The sandbox's `$TMPDIR` remapping is a Claude Code-specific behavior that operators handle at the prompt level (preamble clause P4). Rewriting all SKILL.md examples to use `$TMPDIR` would couple the orchestrator's documentation to a specific execution environment. Won't fix globally; preamble clauses handle the adaptation.

---

#### F4.8 — GitHub label and push permissions blocked pipeline

**What.** CRITICAL operational finding during F1. `clabonte` had only `pull` access to `Bontyyy/orchestrator-api-sample`. Labels could not be created or applied (S7); branch push was blocked (S8). Resolved by human granting write access mid-walkthrough. F2 ran with correct permissions (no recurrence).

**Rationale.** This is a repo access configuration issue, not an orchestrator code or skill bug. The issue-drafting and pr-submission skills correctly attempted label application and push — the failure was at the GitHub API permission layer. Pre-walkthrough checklists should verify that the operating user has `write` (or `triage` for labels) access to all `involved_repos`. No code change warranted; the skills' behavior was correct.

---

#### F4.15 — Branch protection blocks regression fallback

**What.** F2's regression fallback required pushing a direct commit (`bba7afa`) to `main` on `Bontyyy/orchestrator-api-sample`. Branch protection temporarily disabled to push the regression. Operational overhead for the walkthrough.

**Rationale.** This is a walkthrough procedure constraint, not an orchestrator design issue. The regression fallback path is inherently an operator intervention — it requires pushing a known-bad commit to main, which conflicts with branch protection by design. Future walkthroughs that use the regression fallback should document the branch-protection-disable step in their preamble. No code change warranted.

---

### Observation-only findings

The following findings are recorded for completeness but require no action. They are direct inputs to future phase design decisions or reflect correctly-functioning behavior.

- **F4.4** — Narrative-only spec (no OpenAPI file). The spec-validation SKILL.md's precondition (`## Related specs` has >= 1 file) was satisfied by the feature narrative alone. Spec-drafting correctly produced a narrative-only spec when the feature did not warrant a machine-readable spec document. No gap — narrative specs are an explicitly supported spec type per spec-drafting SKILL.md §"Choosing the right spec type."

- **F4.9** — Plan file absent — F3.29 fallback correctly exercised. Both features used inline plan-review (no dedicated plan-review subagent session), so no `FEAT-YYYY-NNNN-plan.md` was produced. The issue-drafting subagent correctly fell back to deriving work-unit prompts from feature registry ACs per the F3.29 fix (WU 3.10). The fallback path is validated across 2 features.

- **F4.11** — Validation tests cite Scope clauses, not formal ACs. F1 S10 qa-authoring produced 3 tests covering Scope-described validation edge cases (blank name, blank sku, quantity out of range) — not formal ACs but legitimate coverage of explicitly scoped behavior. The `covers` fields correctly cited "Scope: blank name → 400" rather than fabricating an AC reference. Correct behavior per qa-authoring SKILL.md.

- **F4.14** — Sonnet 4.6 implements explicit ACs correctly. Both F1 (PATCH with partial update) and F2 (bulk creation with AC-3 atomicity) were implemented correctly on first pass. The regression trap (AC-3's atomicity requirement) did not trigger a natural regression. **Design observation for future walkthroughs:** regression traps should target IMPLICIT behavior (ordering, concurrency, resource cleanup) rather than explicitly described edge cases, since Sonnet 4.6 faithfully implements well-specified ACs.

---

## Fix-in-Phase-4 work plan

Four findings qualify for Fix-in-Phase-4, grouped into one cohesive follow-up WU on the Phase 4 active surface (specs agent skills).

### WU 4.8 — Specs agent SKILL.md documentation fixes

**Scope.** Three targeted documentation fixes on the specs agent's Phase 4 active surface:

1. **(F4.3 / F4.16) Standardize spec-validation SKILL.md trigger field values.** Update Step 2's table entry from `trigger: "human_requested_validation"` to `trigger: "validation_requested"` and Step 8c's table entry from `trigger: "validation_clean"` to `trigger: "validation_passed"`, matching the authoritative values in specs CLAUDE.md §Output surfaces. Update the worked example's event JSON to use the standardized trigger values. The CLAUDE.md is the authoritative source per the SKILL.md's own hierarchy clause.

2. **(F4.5) Specify `## Related specs` path format in spec-drafting SKILL.md.** Update Phase 1 §"Output of Phase 1" to specify that `## Related specs` entries must use repository-relative paths (e.g., `product/features/FEAT-2026-0008.md`) as the primary reference. Full GitHub URLs may appear as supplementary links for human readers, but the first reference in each list item must be a relative path consumable by downstream agents operating on local clones. Update the worked example in Phase 2 to demonstrate the format.

3. **(F4.12) Add delivery convention to spec-drafting SKILL.md.** Add a `## Delivery convention` section (or a subsection of Phase 2) specifying that after the human approves the spec content (Phase 3 pre-validation review), the spec files should be committed to the product specs repo. The skill's output is committed spec files — uncommitted drafts are not a valid output state. The convention mirrors the downstream agents' delivery patterns (qa-authoring's PR convention from WU 3.9). Specify: branch name format, commit convention, and whether a PR is required or direct-to-main is acceptable (per the repo's branch-protection posture).

**Findings absorbed.** F4.3, F4.5, F4.12, F4.16.

**Rationale.** All four findings touch the Phase 4 active surface (spec-validation SKILL.md and spec-drafting SKILL.md). F4.3/F4.16 is a doc-consistency bug with 2-feature evidence. F4.5 is a cross-feature friction point (PM agent needs local paths, spec-drafting provides GitHub URLs). F4.12 is a delivery-convention gap that forced manual intervention in both walkthroughs. Grouping all three in one WU minimizes review passes on the specs agent's skill files and ensures the skills are coherent after the WU lands.

---

## Deferred to Phase 5+

Four new Phase 4 findings defer with explicit home phases:

| Finding | Description | Home Phase |
|---|---|---|
| F4.6 | Capability-counting rule unclear for narrative specs without `### Behavior` headings | Phase 5+ — task-decomposition SKILL.md revision (PM frozen surface) |
| F4.7 | template-coverage-check expects `state == planning` (= F3.27, cross-phase reconfirmation) | Phase 5+ — template-coverage-check SKILL.md revision (PM frozen surface) |
| F4.10 | Issue path bug: `product/features/test-plans/` vs `product/test-plans/` | Phase 5+ — issue-drafting SKILL.md revision (PM frozen surface) |
| F4.13 | `dotnet test --no-build` false-green in qa-execution context (Finding 8 variant) | Phase 5+ — qa-execution SKILL.md revision (QA frozen surface) |

Re-deferred Phase 3 findings (carried forward with updated dispositions):

| Finding | Description | Home Phase | Phase 4 status |
|---|---|---|---|
| F3.11 | SKILL.md files exceed 25k token read limit | Phase 5+ — any WU revising issue-drafting, qa-curation, or specs SKILL.md files for other reasons | Reaffirmed — Phase 4 SKILL.md files (spec-drafting, spec-validation, spec-issue-triage) are also long |
| F3.15 | Task lifecycle events have no per-type schema (envelope-only) | Phase 5 — schema-governance automation | Reaffirmed — Phase 4 added per-type schemas for feature_created, spec_validated, spec_issue_resolved, spec_issue_routed; task lifecycle schemas remain deferred |
| F3.16 | "Done" derivation signal priority undocumented in dep-recomputation | Phase 5 — merge-watcher agent design | Reaffirmed — not touched in Phase 4 |
| F3.17 | `## Scope` cardinality clause wording ambiguity in task-decomposition | Phase 5+ — task-decomposition SKILL.md revision | Reaffirmed — partially mitigated by F3.32 absorption in spec-drafting (upstream language is now better), but the task-decomposition SKILL.md's parsing guidance is unchanged |
| F3.22 | Rule 1 `qa_execution never auto` conditional parsing friction | Phase 5+ — qa-execution SKILL.md revision | Reaffirmed — not touched in Phase 4 |
| F3.24 | T04 `## Deliverables` forward-looking reference | Phase 5+ — plan-review skill evolution | Reaffirmed — not touched in Phase 4 |
| F3.27 | template-coverage-check entry-condition expects `state == planning` | Phase 5+ — template-coverage-check SKILL.md revision | Reaffirmed — confirmed again by Phase 4 F4.7; third cross-phase manifestation |
| F3.31 | `source: component:<bare_name>` format | Phase 5+ — schema-hygiene pass | Reaffirmed — not touched in Phase 4 |
| F3.33 | `tail -1 log \| json.tool` fails on blank trailing line | Phase 5+ — verify-before-report.md §3 revision | Reaffirmed — not touched in Phase 4 |

---

## Phase 3 carry-item disposition

This section addresses all 13 Phase 3 carry items per the WU AC.

### F3.32 — Cardinality wording "expected" ambiguous (absorbed by WU 4.3)

**Status: CLOSED — absorbed correctly.**

WU 4.3 (spec-drafting SKILL.md v1.0) includes a dedicated §"Scope and cardinality conventions" section (lines 161–216) that directly addresses F3.32. The section:

1. Names the F3.32 finding explicitly: "During Phase 3 walkthroughs, the feature registry for FEAT-2026-0007 used the phrase 'three tests expected under the default cardinality convention' in its `## Scope` section."
2. Documents the failure mode: prescriptive misread on a confirmatory clause or vice versa.
3. Provides concrete prescriptive language examples and "avoid" examples.
4. Documents cardinality clause templates with explicit override language.
5. Specifies when the guidance applies (Phase 1 — Feature scoping, `## Scope` bullets).

**Verification:** Re-read `/agents/specs/skills/spec-drafting/SKILL.md` lines 161–216. Content matches the F3.32 disposition's requirements. The Phase 3 retrospective's home clause ("Phase 4+ — specs-agent guidance") is satisfied.

---

### Negative-result carry item 1 — qa-regression runtime validation

**Status: CLOSED (qualified).**

F2 S14 exercised the qa-regression skill for the first time. The skill:

1. Correctly identified T01 as the regression target via the Q4 algorithm (T03 depends_on=[T01,T02] → filter type=implementation → T01).
2. Passed the idempotence check (no prior `qa_regression_filed` for this test_id).
3. Produced a correct inbox artifact at `/inbox/qa-regression/FEAT-2026-0009-widgets-bulk-create-atomicity.md`.
4. Emitted a correct `qa_regression_filed` event (validates against per-type schema).
5. Later emitted a correct `qa_regression_resolved` event (validates against per-type schema, chronological post-dating confirmed).
6. Correctly omitted `escalation_resolved` (no prior `human_escalation`).

**Qualification.** The regression was induced (fallback path), not organic. The component agent (Sonnet 4.6) implemented AC-3's atomicity correctly on first pass. The walkthrough operator manually introduced the regression. The skill's runtime validation is complete — but the evidence is "validated via induced regression, not organic." A future walkthrough that produces a natural regression would remove this qualification.

---

### Negative-result carry item 2 — Q4 cross-attribution resolution

**Status: CLOSED (qualified).**

The full Q4 cross-attribution cycle was exercised in F2:

1. **qa_regression_filed** (S14): inbox artifact + event. Zero writes to T01 issue #29.
2. **Human Q4 audit** (S15): `gh issue view #29` confirmed 0 comments, labels unchanged. Only outputs from qa-regression session: inbox file + event.
3. **Fix task spawned** (S15): issue #34 created by human (simulating PM inbox consumer), not by QA agent.
4. **qa_regression_resolved** (S19): links filed event → resolving qa_execution_completed. `escalation_resolved` correctly omitted.

**Q4 compliance table** (from F2 log):

| Artifact | Wrote to T01 issue #29? | Q4 compliant? |
|---|---|---|
| Inbox artifact | NO | YES |
| qa_regression_filed event | NO | YES |
| qa_regression_resolved event | NO | YES |
| T05 issue #34 | NO (human-created) | YES |
| T05 fix PR #35 | NO (component agent) | YES |

**Qualification.** Same as carry item 1: validated via induced regression, not organic.

---

### Negative-result carry item 3 — "First round" semantics refinement

**Status: OBSERVATION RECORDED — no finding produced.**

F1 and F2 provided contrasting but complementary evidence:

- **F1:** `generating → in_progress` fired after all 4 `task_created` events. The guard in issue-drafting SKILL.md §Step 12 checked for "first invocation to successfully append a `task_created`" — in F1's batched session, all 4 task_created events were appended before the guard ran. The guard found the first `task_created` and was satisfied. The "all tasks opened" appearance was coincidental timing.
- **F2:** `generating → in_progress` fired after T01's `task_created` only — before T02/T03/T04. The guard checked after T01 was appended and was satisfied immediately. The transition fired before the remaining issues were opened.

**Conclusion.** The v1 "first-task-opened" semantics is what the SKILL.md specifies and F2 demonstrates. F1's "all tasks opened" was not a different semantic — it was a timing artifact. No refinement needed. The Phase 3 carry item proposed "Phase 4+ may tighten to 'all tasks opened' if walkthrough experience dictates." Phase 4 experience shows the current semantic is correct and unambiguous. No finding enters the table.

---

### Re-deferred Phase 3 findings (9 items)

#### F3.11 — SKILL.md files exceed 25k token read limit

**Status: Reaffirmed. Re-defer to Phase 5+.**

Phase 4's own SKILL.md files (spec-drafting at ~530 lines, spec-validation at ~634 lines, spec-issue-triage at ~559 lines) are similarly long. No natural fix surface emerged in Phase 4's fix ladder (WU 4.8 is scoped to targeted fixes, not prose-economy passes). The finding applies to a growing set of SKILL.md files across all four agent roles. Home: Phase 5+ — any WU that significantly revises these files for other reasons.

#### F3.15 — Task lifecycle events have no per-type schema (envelope-only)

**Status: Reaffirmed. Re-defer to Phase 5.**

Phase 4 added per-type schemas for four new event types (`feature_created`, `spec_validated`, `spec_issue_resolved`, `spec_issue_routed`) — but the nine task-lifecycle event types identified in F3.15 remain envelope-only. The Phase 4 walkthrough validated 61 events; all task-lifecycle events passed envelope-only validation without incident. Home unchanged: Phase 5 schema-governance automation.

#### F3.16 — "Done" derivation signal priority undocumented in dep-recomputation

**Status: Reaffirmed. Re-defer to Phase 5.**

Not touched in Phase 4. The happy-path safe condition holds. Home unchanged: Phase 5 merge-watcher agent design.

#### F3.17 — `## Scope` cardinality clause wording ambiguity in task-decomposition

**Status: Reaffirmed with partial upstream mitigation. Re-defer to Phase 5+.**

F3.32's absorption into spec-drafting SKILL.md (WU 4.3) provides upstream mitigation: the spec-drafting skill now guides humans toward prescriptive scope language, reducing the likelihood of ambiguous clauses reaching task-decomposition. However, the task-decomposition SKILL.md's own parsing guidance is unchanged (PM frozen surface). Home: Phase 5+ task-decomposition SKILL.md revision.

#### F3.22 — Rule 1 `qa_execution never auto` conditional parsing friction

**Status: Reaffirmed. Re-defer to Phase 5+.**

Not touched in Phase 4. Both Phase 4 features used `autonomy_default: review`, so the conditional was not exercised. Home unchanged: Phase 5+ qa-execution SKILL.md revision.

#### F3.24 — T04 `## Deliverables` forward-looking reference

**Status: Reaffirmed. Re-defer to Phase 5+.**

Not touched in Phase 4. The same pattern occurred (T04 issue body references a test plan path that doesn't exist at issue-creation time). Home unchanged: Phase 5+ plan-review skill evolution.

#### F3.27 — template-coverage-check entry-condition expects `state == planning`

**Status: Reaffirmed (third cross-phase manifestation). Re-defer to Phase 5+.**

Phase 4 F4.7 is the third manifestation of this finding (Phase 3 F1 S3, Phase 3 F2 S3, Phase 4 F1 S6). Still low severity — operator-directed invocation proceeds regardless. Home unchanged: Phase 5+ template-coverage-check SKILL.md revision (PM frozen surface).

#### F3.31 — `source: component:<bare_name>` format

**Status: Reaffirmed. Re-defer to Phase 5+.**

Not touched in Phase 4. The convention continues to work as documented. Home unchanged: Phase 5+ schema-hygiene pass.

#### F3.33 — `tail -1 log | json.tool` fails on blank trailing line

**Status: Reaffirmed. Re-defer to Phase 5+.**

Not touched in Phase 4. Home unchanged: Phase 5+ verify-before-report.md §3 revision.

---

## Loose ends

Two loose ends deliberately preserved from the walkthroughs:

1. **Fixture features and plans on specs-sample.** Commits from Phase 3 walkthroughs (FEAT-2026-9001/9002/9003 fixture plans and associated artifacts) remain on the repos as permanent demo artifacts per the Phase 3 decision (Option A). Phase 4 walkthroughs added FEAT-2026-0008 and FEAT-2026-0009 artifacts to both api-sample (PRs #28, #33, #35) and specs-sample (PRs #4, #5). These are intentional demonstration artifacts.

2. **Induced regression commit on api-sample.** Commit `bba7afa` (the deliberately broken `BulkCreateAsync`) was pushed to main and subsequently fixed by commit `c6a9138` (PR #35). The regression commit remains in the git history as an honest record of the walkthrough's fallback path. No cleanup action required — the fix commit restores correctness.

3. **Specfuse CLI availability.** The `specfuse` CLI was not installed on the walkthrough machine. Both features simulated validation with `validator_version: "simulated-1.0"`. Future walkthroughs that exercise the spec-validation skill's failure-feedback path (Step 6) will require the CLI to be installed. This is a pre-walkthrough setup task, not a code fix.

## Outcome

WU 4.7 concludes Phase 4's triage work. The Phase 4 walkthroughs validated the specs agent across the happy-path shape (F1) and the regression-cycle shape (F2), including the first-ever runtime exercise of the specs-to-PM handoff (`validating → planning`) and the qa-regression skill. The 16 findings were sorted into 4 Fix-in-Phase-4, 4 Defer-to-Phase-5+ (+ 9 re-deferred Phase 3 findings), 4 Won't-fix, and 4 Observations-only — with explicit rationales, 2-feature evidence documentation, and a concrete one-WU fix ladder.

The 13 Phase 3 carry items were dispositioned:
- **F3.32** — absorbed by WU 4.3 (verified landed correctly).
- **qa-regression runtime validation** — closed (qualified: induced regression, not organic).
- **Q4 cross-attribution resolution** — closed (qualified: induced regression, not organic).
- **"First round" semantics** — observation recorded; no finding; v1 semantics confirmed correct.
- **9 re-deferred findings** (F3.11, F3.15, F3.16, F3.17, F3.22, F3.24, F3.27, F3.31, F3.33) — all reaffirmed and carried forward to Phase 5+ with home phases unchanged or updated.

Phase 4 is ready to proceed to the fix ladder once this retrospective merges. Phase 5 (generator feedback loop and merge-watcher agent) can start after the fix WU (4.8) ships and the freeze declaration is issued.

## Phase 4 freeze declaration

**Declared on 2026-04-25 as part of WU 4.9.**

All four Fix-in-Phase-4 items identified by the WU 4.7 triage have shipped to `main` in one post-retrospective fix WU:

| # | Finding(s) | WU | Commit |
|---|---|---|---|
| F4.3 + F4.16 | Spec-validation SKILL.md trigger value standardization (`validation_requested`, `validation_passed`) | WU 4.8 | `7a7483d` |
| F4.5 | Spec-drafting SKILL.md `## Related specs` path format guidance (repo-relative paths) | WU 4.8 | `7a7483d` |
| F4.12 | Spec-drafting SKILL.md `## Delivery convention` section | WU 4.8 | `7a7483d` |

Additionally, **one carry-item from Phase 3** was absorbed during Phase 4's skill-authoring WUs:

- **F3.32 (cardinality wording "expected" ambiguous)** — absorbed via WU 4.3 (spec-drafting SKILL.md §"Scope and cardinality conventions"). The Phase 3 retrospective's home clause ("Phase 4+ — specs-agent guidance") is satisfied. Verified in WU 4.7.

And **three negative-result carry items from Phase 3** were closed during Phase 4 walkthroughs:

- **qa-regression runtime validation** — closed (qualified: induced regression). F2 S14 exercised the skill for the first time; correct artifacts produced.
- **Q4 cross-attribution resolution** — closed (qualified: induced regression). Full cycle exercised in F2 (S14 filing → S15 audit → S16 fix → S18 re-execution → S19 resolution). Q4 invariant held.
- **"First round" semantics refinement** — observation recorded; no finding. V1 "first-task-opened" semantics confirmed correct by F2 S7; F1's "all tasks opened" was coincidental timing.

With WU 4.8 landed, the specs agent configuration plus the post-fix-ladder skills are declared frozen for Phase 5 consumption:

> **Specs agent v1.0.1 is the baseline Phase 5 depends on. The Phase 1 + Phase 2 + Phase 3 frozen surfaces, as amended by their respective post-freeze additive fix ladders, remain the orchestrator's operational foundation. Changes to any frozen surface during Phase 5+ require architectural justification.**

### Frozen specs-agent surface (v1.0.1)

- [`agents/specs/CLAUDE.md`](../../../agents/specs/CLAUDE.md) — role config (v1.0.0 file version; specs agent v1.0.1).
- [`agents/specs/skills/feature-intake/SKILL.md`](../../../agents/specs/skills/feature-intake/SKILL.md) — v1.0 (unchanged since WU 4.2).
- [`agents/specs/skills/spec-drafting/SKILL.md`](../../../agents/specs/skills/spec-drafting/SKILL.md) — v1.0 post-WU 4.8 (Related specs path format guidance + delivery convention section added).
- [`agents/specs/skills/spec-validation/SKILL.md`](../../../agents/specs/skills/spec-validation/SKILL.md) — v1.0 post-WU 4.8 (trigger values standardized to `validation_requested` / `validation_passed`).
- [`agents/specs/skills/spec-issue-triage/SKILL.md`](../../../agents/specs/skills/spec-issue-triage/SKILL.md) — v1.0 (unchanged since WU 4.5 — **spec-issue-triage's runtime path remains unvalidated**; no spec issue was filed during Phase 4 walkthroughs; Phase 5 carry).
- [`agents/specs/rules/`](../../../agents/specs/rules/) — intentionally empty at freeze; no role-specific overrides needed at v1.

### Prior phase frozen surfaces (unchanged by Phase 4)

Phase 4 did **not** amend any Phase 1, 2, or 3 frozen surface. The full prior-phase baseline is:

- **Component agent v1.5.2** (Phase 1 frozen, Phase 3 amended) — `agents/component/CLAUDE.md`, `agents/component/skills/verification/SKILL.md` v1.2, `agents/component/skills/pr-submission/SKILL.md` v1.1, `agents/component/skills/escalation/SKILL.md` v1.2.
- **PM agent v1.6.3** (Phase 2 frozen, Phase 3 amended) — `agents/pm/CLAUDE.md`, `agents/pm/skills/task-decomposition/SKILL.md` v1.2, `agents/pm/skills/plan-review/SKILL.md` v1.2, `agents/pm/skills/issue-drafting/SKILL.md` v1.4, `agents/pm/skills/dependency-recomputation/SKILL.md` v1.1, `agents/pm/skills/template-coverage-check/SKILL.md` v1.1.
- **QA agent v1.5.2** (Phase 3 frozen) — `agents/qa/CLAUDE.md`, `agents/qa/skills/qa-authoring/SKILL.md` v1.1, `agents/qa/skills/qa-execution/SKILL.md` v1.0, `agents/qa/skills/qa-regression/SKILL.md` v1.0, `agents/qa/skills/qa-curation/SKILL.md` v1.1.
- **Shared substrate** — `shared/rules/*` (8 files, post-WU 3.11), `shared/templates/*` (post-WU 3.10), `shared/schemas/*` (plus Phase 4 per-type schemas: `feature_created`, `spec_validated`, `spec_issue_resolved`, `spec_issue_routed`).

### The freeze does **not** cover

- The config-steward or merge-watcher role configs. Those remain Phase 0 v0.1 drafts (or non-existent) pending Phase 5 per the implementation plan.
- The thirteen findings deferred to Phase 5+ by this retrospective (4 new Phase 4 findings + 9 re-deferred Phase 3 findings). They are scheduled carry-items, not part of the frozen surface. Each has a named home phase in §"Deferred to Phase 5+" above.
- The **Phase 5 carry items** that emerged from Phase 4:
  - (a) The spec-issue-triage skill's runtime validation (the skill was authored in WU 4.5 but never exercised at runtime — no spec issue was filed during Phase 4 walkthroughs). Phase 5 walkthroughs should include at least one spec-issue routing exercise.
  - (b) The qa-regression / Q4 qualification: validated via induced regression, not organic. A future walkthrough that produces a natural regression would remove this qualification. Low priority — the skill's correctness is demonstrated; only the trigger mechanism is qualified.
  - (c) Specfuse CLI installation: the spec-validation skill's failure-feedback path (Step 6) was not exercised because the CLI was not installed. Future walkthroughs should install the CLI to exercise the full validation flow.

### Carry list for Phase 5 inputs

**New Phase 4 findings deferred to Phase 5+:**

| # | Finding | Home |
|---|---|---|
| F4.6 | Capability-counting rule unclear for narrative specs | Phase 5+ — task-decomposition SKILL.md revision (PM frozen surface) |
| F4.7 | template-coverage-check expects `state == planning` (= F3.27) | Phase 5+ — template-coverage-check SKILL.md revision (PM frozen surface) |
| F4.10 | Issue path bug: `product/features/test-plans/` vs `product/test-plans/` | Phase 5+ — issue-drafting SKILL.md revision (PM frozen surface) |
| F4.13 | `dotnet test --no-build` false-green in qa-execution context | Phase 5+ — qa-execution SKILL.md revision (QA frozen surface) |

**Re-deferred Phase 3 findings (carried forward from Phase 3 → Phase 4 → Phase 5+):**

| # | Finding | Home |
|---|---|---|
| F3.11 | SKILL.md files exceed 25k token read limit | Phase 5+ — any WU revising long SKILL.md files for other reasons |
| F3.15 | Task lifecycle events have no per-type schema (envelope-only) | Phase 5 — schema-governance automation |
| F3.16 | "Done" derivation signal priority undocumented in dep-recomputation | Phase 5 — merge-watcher agent design |
| F3.17 | `## Scope` cardinality clause wording ambiguity in task-decomposition | Phase 5+ — task-decomposition SKILL.md revision |
| F3.22 | Rule 1 `qa_execution never auto` conditional parsing friction | Phase 5+ — qa-execution SKILL.md revision |
| F3.24 | T04 `## Deliverables` forward-looking reference | Phase 5+ — plan-review skill evolution |
| F3.27 | template-coverage-check entry-condition expects `state == planning` | Phase 5+ — template-coverage-check SKILL.md revision |
| F3.31 | `source: component:<bare_name>` format | Phase 5+ — schema-hygiene pass |
| F3.33 | `tail -1 log \| json.tool` fails on blank trailing line | Phase 5+ — verify-before-report.md §3 revision |

**Phase 5 carry items (new from Phase 4):**

- **spec-issue-triage runtime validation.** The skill was authored but never exercised at runtime. Phase 5 walkthroughs should include at least one spec-issue routing exercise.
- **qa-regression / Q4 organic trigger qualification.** Validated via induced regression; a natural regression would remove this qualification.
- **Specfuse CLI installation.** Spec-validation failure-feedback path (Step 6) not exercised.

Phase 5 (generator feedback loop and merge-watcher agent) can now start. The four Fix-in-Phase-4 items and their rationales are the contract Phase 5 inherits, alongside the frozen specs + QA + PM + component + shared surfaces above and the thirteen Deferred-to-Phase-5+ findings + three Phase 5 carry items documented in this section.
