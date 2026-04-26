# Operator runbook — specs-agent quickstart

This runbook walks through driving a single feature from idea to `planning` using the specs agent in an interactive Claude Code session. It is the day-one entry point for using the orchestrator on a real project.

For everything that happens *after* `planning` (PM task decomposition, component implementation, QA cycles, inbox handling, spec-issue triage, escalations), see [`operator-pipeline-reference.md`](operator-pipeline-reference.md).

## Prerequisites

The orchestrator assumes a specific multi-repo layout and tooling baseline before a session is productive. Verify each item before your first real-project session.

### Repos

- **Orchestration repo** (this one). Holds `/agents/`, `/shared/`, `/scripts/`, and is the destination for `/features/`, `/events/`, and `/inbox/` artifacts the specs agent produces. Clone it locally; the agent reads `agents/specs/CLAUDE.md` from this clone.
- **Product specs repo.** A separate git repo with a top-level `/product/` and `/business/` split (architecture §4.1). The specs agent writes spec documents into `/product/` only. `/business/` is hard never-touch ([`shared/rules/never-touch.md`](../shared/rules/never-touch.md) §4).
- **At least one component repo.** Required for the downstream pipeline; not required just to draft specs, but you cannot exercise the full pipeline without one. Each component repo has its own component-agent session and its own `/overrides/` discipline.

### Tooling

- **Claude Code CLI** installed and authenticated. The specs agent runs as a session inside Claude Code with `agents/specs/CLAUDE.md` loaded as the role prompt.
- **Specfuse validator CLI** installed and on `$PATH`. Phase 4 walkthroughs *simulated* validation because the binary wasn't installed (retrospective F4.1, marked Won't-fix at the orchestrator level — your responsibility as operator). The spec-validation skill invokes the real validator; without it, validation produces no signal.
- **Python 3 with the deps in [`scripts/requirements.txt`](../scripts/requirements.txt).** Used by `validate-event.py` and `validate-frontmatter.py`, which the agent shells out to at every event emission.
- **`gh` CLI** authenticated against the GitHub org hosting the component and generator repos. Required for spec-issue filing and (later) for the PM agent's issue creation.
- **Writable `$TMPDIR`.** The agent uses `$TMPDIR` for staging events before validation. If you run inside a sandbox that blocks `/tmp` writes, ensure `$TMPDIR` is set and writable (Phase 4 retrospective F4.2).

### Pre-session checks

Before the first session, run from the orchestration repo root:

```bash
scripts/read-agent-version.sh specs   # expect 1.0.1
specfuse --version                     # validator must be on PATH
python -c "import jsonschema, yaml"    # event/frontmatter validators import OK
gh auth status                         # gh authenticated
```

If any of those fail, fix the environment before opening a session — the agent will not paper over a missing dependency.

## Session walkthrough

A typical specs-agent session covers three skills invoked in sequence: feature intake → spec drafting → spec validation. The fourth skill (spec-issue triage) is reactive and is invoked separately when spec issues land in `/inbox/spec-issue/`; see the [pipeline reference](operator-pipeline-reference.md).

### Step 1 — Open the session

From the **product specs repo** working directory, launch Claude Code with the orchestration repo's `agents/specs/CLAUDE.md` as the role prompt. The agent expects to be able to read both the orchestration repo (for `/features/`, `/events/`, `/shared/`) and the product specs repo (for `/product/`) in the same session.

The first thing the agent does on every task is re-read the full [`/shared/rules/`](../shared/rules/) set ([`role-switch-hygiene.md`](../shared/rules/role-switch-hygiene.md)). Let it complete that load before issuing your first prompt.

### Step 2 — Feature intake

Tell the agent: *"I want to start a new feature."* It will invoke [`agents/specs/skills/feature-intake/SKILL.md`](../agents/specs/skills/feature-intake/SKILL.md) and ask you for:

- **Feature title** — a short noun phrase (e.g., "Widget Catalog API").
- **Involved repos** — the component repo(s) the feature will touch, in `org/repo` form.
- **Autonomy default** — `auto`, `review`, or `manual`. Use `review` for a real project's first features; it gates handoffs on human approval. `auto` is appropriate only after you trust the pipeline on this feature class.

The agent then:

1. Reads `/features/FEAT-YYYY-*.md` to find the next available ordinal.
2. Mints a correlation ID `FEAT-YYYY-NNNN` per [`shared/rules/correlation-ids.md`](../shared/rules/correlation-ids.md).
3. Creates `/features/FEAT-YYYY-NNNN.md` from the [feature-registry template](../shared/templates/feature-registry.md) with `state: drafting` and your inputs in frontmatter; body sections carry placeholder text.
4. Validates the frontmatter via `scripts/validate-frontmatter.py`.
5. Emits a `feature_created` event to `/events/FEAT-YYYY-NNNN.jsonl`, validated via `scripts/validate-event.py`.

**Verify before continuing.** Re-read the feature file, confirm the correlation ID, and confirm the event landed. The agent does this automatically per [`shared/rules/verify-before-report.md`](../shared/rules/verify-before-report.md), but it's worth a glance — every downstream artifact threads through this correlation ID.

### Step 3 — Spec drafting

Tell the agent: *"Let's draft the spec for FEAT-YYYY-NNNN."* It will invoke [`agents/specs/skills/spec-drafting/SKILL.md`](../agents/specs/skills/spec-drafting/SKILL.md), which structures the conversation in three phases:

1. **Feature scoping.** The agent helps you populate the registry's `Description`, `Scope`, `Out of scope`, and `Related specs` body sections with prescriptive (not confirmatory) language. Watch for the F3.32 cardinality guidance — write *"the feature adds three endpoints: list, get, create"*, not *"three endpoints are expected under the default convention."* The wording matters: the QA agent will parse `## Scope` to decide test cardinality.
2. **Spec drafting.** The agent helps you produce OpenAPI / AsyncAPI / Arazzo documents under `/product/specs/<feature-slug>.{yaml,json}`. Every acceptance criterion you write must be testable — verifiable by a command with an observable expected outcome — because the QA agent will convert it directly into a `test_id` with `covers`, `commands`, and `expected` fields.
3. **Pre-validation review.** The agent reviews the drafted specs with you for completeness and internal consistency. It does *not* run validation here — that's Step 4.

You can split this across sessions; the registry file plus `/product/` files are durable state.

### Step 4 — Spec validation

When the spec feels ready, tell the agent: *"Run validation."* It will invoke [`agents/specs/skills/spec-validation/SKILL.md`](../agents/specs/skills/spec-validation/SKILL.md), which:

1. Emits `feature_state_changed(drafting → validating)` with `trigger: "validation_requested"`.
2. Reads the registry's `Related specs` to determine which files to validate.
3. Invokes the Specfuse validator on each.
4. **On clean pass:** emits `feature_state_changed(validating → planning)` with `trigger: "validation_passed"` and reports *"FEAT-YYYY-NNNN is ready for PM planning."* The session ends here for the specs agent.
5. **On failure:** presents per-file errors in plain-language remediation form (not raw validator output) and stays in `validating`. Fix the spec, then re-run validation. The skill is idempotent — re-validating an unchanged spec produces the same result without duplicate state events.

### Step 5 — Hand off to PM

Once `validating → planning` is emitted, the feature is the PM agent's. Open a new Claude Code session with `agents/pm/CLAUDE.md` as the role prompt and tell it to pick up `FEAT-YYYY-NNNN`. The full PM/component/QA flow is in [`operator-pipeline-reference.md`](operator-pipeline-reference.md).

## Common gotchas

- **Don't bump feature state by hand.** Every transition is owned by exactly one role/skill. Manual edits to `state:` in the registry frontmatter break the event-log audit and confuse downstream agents. If you think you need to bump state manually, escalate or restart the skill.
- **`/business/` is hard off-limits.** The specs agent will refuse to write there. Don't paper over by writing for it.
- **Body sections, not frontmatter.** The spec-drafting skill writes registry body sections (`Description`, `Scope`, etc.). It never modifies frontmatter — that's owned by intake and validation. If the agent asks you about frontmatter, something's off.
- **One feature, one session at a time.** Multi-feature drafting in a single session muddles correlation IDs in the agent's working memory and risks cross-feature artifact writes.
- **Re-read the registry between sessions.** The agent does this automatically (per anti-pattern #10 in `agents/specs/CLAUDE.md`), but if you suspect drift, prompt it to re-read before issuing the next instruction.
- **`tail -1 log | json.tool` fails on a blank trailing line.** Phase 3 finding F3.33; if you inspect event logs by hand, use `grep -v '^$' log | tail -1 | json.tool` instead.

## Where to go next

- Continue through the full pipeline: [`operator-pipeline-reference.md`](operator-pipeline-reference.md).
- Specs agent role contract: [`agents/specs/CLAUDE.md`](../agents/specs/CLAUDE.md).
- Feature state machine: [`orchestrator-architecture.md`](orchestrator-architecture.md) §6.1, §6.3.
- Phase 4 walkthrough logs (worked examples): [`walkthroughs/phase-4/feature-1-log.md`](walkthroughs/phase-4/feature-1-log.md), [`walkthroughs/phase-4/feature-2-log.md`](walkthroughs/phase-4/feature-2-log.md).
