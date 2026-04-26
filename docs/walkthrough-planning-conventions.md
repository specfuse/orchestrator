# Walkthrough planning conventions

A walkthrough work unit (e.g., WU 1.5, 2.7, 3.6, 4.6) exercises a phase's deliverables end-to-end on real features. Before execution, the operator drafts a planning document — informally, the "walkthrough scratch" — that pre-computes expected outcomes, anticipates friction, and scripts subagent prompts so the live execution can focus on observation rather than improvisation.

This file captures the structural pattern those planning documents have shared across Phases 1–4, so the next walkthrough can adopt the same shape cold rather than reverse-engineering it from a prior scratch doc. **It is a reference for the shape, not a fill-in-the-blanks template.** The actual content is always feature- and phase-specific.

## Five-zone structure

Every walkthrough planning doc is organized into five zones, in this order:

1. **Pre-computed task graphs.** A table per feature listing the expected tasks (id, type, depends_on, assigned_repo, required_templates) before any agent runs. This is the operator's hypothesis of what the PM agent's task-decomposition skill will produce — divergence becomes a finding.
2. **Pre-findings from skill dry-read.** Numbered hypotheses (PF-1, PF-2, …) about friction the operator anticipates by reading the relevant SKILL.md files cold. Each entry: *what* the friction is, *expected friction* (severity, where it bites), *surfaces at* (which session is most likely to surface it). After execution, each pre-finding is graded — was it observed, missed, or a false alarm? This is the highest-value zone and the most often skipped.
3. **Session prompts — Feature 1.** The full set of subagent prompts plus interleaved manual steps. See "Prompt skeleton" below.
4. **Session prompts — Feature 2.** Same shape as Feature 1, with the second feature's content. The two features are deliberately chosen to exercise different paths — typically one happy path and one designed to surface a specific friction (e.g., regression cycle, multi-repo, ambiguous scope).
5. **Real-time walkthrough notes.** Empty at planning time; appended *during* execution as observations land. The presence of this zone — even when empty in the planning draft — is the prompt to the operator to record friction in the moment rather than reconstruct it after the fact.

The walkthrough's *outcome* artifacts (per-feature logs and the retrospective) are separate documents and live in `docs/walkthroughs/phase-N/`. The planning doc is a private working artifact that does not need to survive the phase.

## Subagent prompt skeleton

Every prompt invoking the `Agent` tool to play an operational role follows the same skeleton. Read the agent's `CLAUDE.md` for the role-specific framing; the skeleton below is the wrapper that makes the prompt walkthrough-ready.

```
You are acting as the <role> agent (v<version>, frozen Phase <N> baseline) performing
the <skill-name> skill. This is a Phase <N> walkthrough session — honesty about
friction is required.

Setup discipline (re-read before acting, per shared/rules/role-switch-hygiene.md):
1. Read every file under <orchestrator-repo>/shared/rules/.
2. Read <orchestrator-repo>/agents/<role>/CLAUDE.md.
3. Read <orchestrator-repo>/agents/<role>/skills/<skill-name>/SKILL.md.
4. Read any other inputs the skill requires (feature registry, event log, schemas).

Preamble clauses: P1, P2, …, Pk. (See "Preamble clauses" section of this planning doc.)

Task:
<concrete task description: feature ID, inputs, expected outputs, where to write>

Do NOT:
<role-boundary violations relevant to this session — typically inherited from the
agent's anti-patterns plus walkthrough-specific constraints>

Report:
- The artifacts produced (file paths, content excerpts).
- All events emitted (full JSON).
- Verification evidence (validator exit codes, re-read confirmations).
- All friction encountered, unsanitized.
```

Sessions that only the human operator can perform (PR merges, plan_review approval, escalation resolution, Q4 audits, regression-fallback induction) are written as `### F<n> S<m> — <name> (manual, no subagent)` with a numbered checklist instead of a prompt block.

## Preamble clauses

A walkthrough's preamble clauses are short, numbered rules pre-pended to every subagent prompt. Each clause **absorbs a specific finding from prior phases** so the agent does not re-encounter friction the operator has already cataloged. The pattern, not the specific clauses, is what carries forward.

A clause typically takes one of these shapes:

- **Surface boundary**: *"Do NOT run `git commit` or `git add` on the orchestrator repo. The operator owns those commits."* (Prevents subagents from racing the operator on the orchestration repo's history.)
- **Tooling discipline**: *"All timestamps must be produced by `date -u +"%Y-%m-%dT%H:%M:%SZ"` at emission time."* (Prevents synthesized timestamps that drift from wall clock.)
- **Schema discipline**: *"Before constructing an event payload, read the per-type schema at `shared/schemas/events/<event_type>.schema.json` if it exists."* (Prevents envelope-only validation when a per-type schema is available.)
- **Safe-pattern reference**: *"To emit an event, follow the safe-append pattern in `shared/rules/verify-before-report.md` §3."* (Replaces a fragile inline shell snippet with a pointer to the shared rule.)
- **Reporting discipline**: *"Report every friction point, surprise, or workaround unsanitized."* (Without this, subagents tend to produce sanitized success reports that erase the most valuable retrospective signal.)

Authoring discipline:

1. Each clause cites the phase or finding that motivated it (e.g., "absorbs F3.10").
2. Clauses are versioned per walkthrough — the next phase's planning doc reviews the prior set, drops clauses that have been absorbed into shared rules or skill bodies, and adds new clauses for findings that have not yet been absorbed.
3. Clauses that recur across two consecutive walkthroughs unchanged are a signal that the underlying finding belongs in `shared/rules/` or a skill body, not in walkthrough preambles.

## Feature selection

Two features per walkthrough is the established pattern. The first exercises the happy path; the second is chosen to exercise one or more specific friction surfaces the operator wants evidence on. Phase-specific guidance lives in each phase's WU prompt in the implementation plan. General principles:

- Prefer features small enough to walk in one or two operator sessions. A walkthrough that takes a week erodes the operator's memory of what happened in session 1 by the time session N is logged.
- The second feature's friction surface should be picked before the first feature is run, not after. Picking it after biases the design.
- If the feature class doesn't naturally exercise the target friction, plan a fallback path (e.g., manually inducing a regression). Document the fallback honestly when it triggers; a fallback path is not a failure to validate, but it is a qualified validation.

## At the end

The planning doc is not a formal artifact. When the walkthrough completes:

- Per-feature logs (`feature-N-log.md`) are the durable outcome record.
- The retrospective dispositions findings into Fix-in-Phase-N, Defer-to-Phase-N+1+, Won't-fix, and Observation-only.
- The planning doc itself can be deleted once the retrospective is committed. Git history preserves it if you ever want to study how that phase's walkthrough was scoped before execution.
