# Feature intake — v1.0

Creates a new feature's registry entry in the orchestration repo, mints the correlation ID, emits the `feature_created` event, and sets the feature state to `drafting`. This is the entry point for every feature's lifecycle — no downstream skill (spec drafting, validation, planning) can operate until a valid registry entry exists.

When this file and [`../../CLAUDE.md`](../../CLAUDE.md) disagree, **the role config wins and this file is wrong.** Raise an escalation rather than reconciling silently.

## Trigger

The human opens a Claude Code session and says they want to create a new feature. There is no structured-event trigger — this is a session-driven, conversational entry point.

## Inputs from the human

The skill collects three pieces of information from the human before proceeding. All three are required; the skill does not assume defaults for title or repos.

1. **Feature title** (string) — free-form prose describing the feature. Used in the registry file's Description heading and in the `feature_created` event payload. Not a machine identifier.
2. **Involved repos** (array of `owner/repo` strings) — the component repositories this feature touches. At least one is required. Each string must match the `owner/repo` format used across the orchestrator (e.g. `Bontyyy/orchestrator-api-sample`).
3. **Autonomy default** (enum: `auto`, `review`, `supervised`) — the feature-level autonomy setting that governs how much latitude downstream agents have. If the human does not specify, prompt for it explicitly — do not silently default to `review`.

## Procedure

### Step 1 — Determine the next available ordinal

Read all existing feature registry files matching `/features/FEAT-YYYY-*.md` for the current year (use `YYYY` = the four-digit current year at execution time).

Extract the four-digit ordinal `NNNN` from each filename. Identify the largest ordinal `max_NNNN` among the existing files.

Compute the candidate ordinal: `candidate = max_NNNN + 1`. If no files exist for the current year, `candidate = 1`.

Zero-pad the candidate to four digits: `printf '%04d' $candidate`.

The candidate correlation ID is `FEAT-YYYY-NNNN` where `YYYY` is the current year and `NNNN` is the zero-padded candidate.

### Step 2 — Handle ordinal collision

Check whether `/features/FEAT-YYYY-NNNN.md` already exists at the computed path. This can happen if a file was created between the directory listing and the write, or if a non-standard filename (e.g. `FEAT-2026-0004-plan.md`) inflated the max without occupying the ordinal.

**Collision-handling logic (deterministic):**

```
while /features/FEAT-{YYYY}-{NNNN}.md exists:
    NNNN = NNNN + 1   (re-pad to four digits)
```

The loop terminates when a free ordinal is found. The resulting `FEAT-YYYY-NNNN` is the minted correlation ID.

This guarantees that two invocations observing the same directory state will not produce the same ID: the first invocation creates the file, so the second invocation's existence check finds it occupied and increments. The increment is unbounded (no wrap-around at 9999 within the scope of this skill; the four-digit format supports ordinals 0001–9999 per year, which is sufficient for the foreseeable feature volume).

### Step 3 — Create the feature registry file

Create `/features/FEAT-YYYY-NNNN.md` using the [`feature-registry.md`](../../../../shared/templates/feature-registry.md) template. Populate the frontmatter with:

```yaml
---
correlation_id: FEAT-YYYY-NNNN
state: drafting
involved_repos:
  - <each repo the human provided, one per line>
autonomy_default: <the human's choice>
task_graph: []
---
```

The `task_graph` is an empty array — task decomposition is the PM agent's concern after `planning`.

**Body sections** carry honest placeholder text. The feature-intake skill does not draft spec content — that is the spec-drafting skill's concern (WU 4.3). The body is:

```markdown
## Description

To be drafted during spec authoring.

## Scope

- To be drafted during spec authoring.

## Out of scope

- To be drafted during spec authoring.

## Related specs

- To be drafted during spec authoring.
```

The placeholders make the file valid markdown and honestly incomplete. They are replaced during spec drafting — never by this skill.

### Step 4 — Validate the frontmatter

Before writing the file to disk, validate the frontmatter against [`feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) using [`scripts/validate-frontmatter.py`](../../../../scripts/validate-frontmatter.py).

Write the file content to a temporary location first, then validate:

```sh
# Write the complete file (frontmatter + body) to a temp file
cat > /tmp/feature-registry-candidate.md << 'REGISTRY_EOF'
---
correlation_id: FEAT-2026-0008
state: drafting
involved_repos:
  - Bontyyy/orchestrator-api-sample
autonomy_default: review
task_graph: []
---

## Description

To be drafted during spec authoring.

## Scope

- To be drafted during spec authoring.

## Out of scope

- To be drafted during spec authoring.

## Related specs

- To be drafted during spec authoring.
REGISTRY_EOF

# Validate
python3 scripts/validate-frontmatter.py --file /tmp/feature-registry-candidate.md
```

**Exit 0:** Frontmatter is valid. Proceed to copy the temp file to `/features/FEAT-YYYY-NNNN.md`.

**Exit 1 or 2:** Frontmatter is invalid. Do not write the file. Diagnose the validation error, correct the frontmatter, and re-validate. This counts as one corrective cycle per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md). Three consecutive failures → escalate with `spinning_detected`.

### Step 5 — Emit the `feature_created` event

Construct the event JSON object with the following fields:

| Field | Value |
|---|---|
| `timestamp` | `date -u +%Y-%m-%dT%H:%M:%SZ` — captured at emission time, never synthesized |
| `correlation_id` | The minted `FEAT-YYYY-NNNN` |
| `event_type` | `feature_created` |
| `source` | `specs` |
| `source_version` | Output of `scripts/read-agent-version.sh specs` — never eye-cached from `version.md` |
| `payload.feature_title` | The human-provided title |
| `payload.involved_repos` | The human-provided repo array |
| `payload.autonomy_default` | The human-provided autonomy choice |
| `payload.correlation_id` | The minted `FEAT-YYYY-NNNN` (duplicated for payload self-containment) |

Write the event as minified single-line JSON to `/tmp/event.json`. Validate through [`scripts/validate-event.py`](../../../../scripts/validate-event.py) using the canonical invocation:

```sh
python3 scripts/validate-event.py --file /tmp/event.json
```

**Exit 0:** Event is valid. Append to the feature's event log using the canonical safe append pattern:

```sh
printf '%s\n' "$(cat /tmp/event.json)" >> events/FEAT-YYYY-NNNN.jsonl
```

The `printf '%s\n'` wrapper guarantees the trailing newline. Plain `cat >> file` is unsafe and corrupts JSONL if the source lacks a trailing newline.

**Exit 1 or 2:** Event is invalid. Do not append. Diagnose, correct, re-validate. Three consecutive failures → escalate with `spinning_detected`.

### Step 6 — Verify

Per [`verify-before-report.md`](../../../../shared/rules/verify-before-report.md), re-read the produced artifacts and confirm:

1. `/features/FEAT-YYYY-NNNN.md` exists and its frontmatter round-trips through `validate-frontmatter.py` with exit 0.
2. `/events/FEAT-YYYY-NNNN.jsonl` exists, contains exactly one line, and that line round-trips through `validate-event.py` with exit 0.
3. The correlation ID in the filename, the frontmatter `correlation_id` field, the event envelope `correlation_id`, and the event `payload.correlation_id` all match.
4. The feature state is `drafting`.
5. No path written is in [`never-touch.md`](../../../../shared/rules/never-touch.md).

Only after all checks pass does the skill report completion.

## Worked example

**Human input:**

- Feature title: "Widget Catalog API"
- Involved repos: `Bontyyy/orchestrator-api-sample`
- Autonomy default: `review`

**Step 1 — Ordinal resolution:**

The specs agent lists `/features/FEAT-2026-*.md` and finds:

```
FEAT-2026-0001.md
FEAT-2026-0002.md
FEAT-2026-0003.md
FEAT-2026-0004-plan.md
FEAT-2026-0004.md
FEAT-2026-0005-plan.md
FEAT-2026-0005.md
FEAT-2026-0006.md
FEAT-2026-0007.md
```

Ordinals extracted from filenames matching `FEAT-2026-NNNN.md` exactly: 0001, 0002, 0003, 0004, 0005, 0006, 0007. The `*-plan.md` files do not match the `FEAT-YYYY-NNNN.md` pattern and are excluded from ordinal extraction.

`max_NNNN` = 0007. Candidate = 0008.

**Step 2 — Collision check:**

`/features/FEAT-2026-0008.md` does not exist. No collision. Minted correlation ID: `FEAT-2026-0008`.

**Step 3 — Registry file created at `/features/FEAT-2026-0008.md`:**

```yaml
---
correlation_id: FEAT-2026-0008
state: drafting
involved_repos:
  - Bontyyy/orchestrator-api-sample
autonomy_default: review
task_graph: []
---
```

```markdown
## Description

To be drafted during spec authoring.

## Scope

- To be drafted during spec authoring.

## Out of scope

- To be drafted during spec authoring.

## Related specs

- To be drafted during spec authoring.
```

**Step 4 — Frontmatter validation:**

```sh
python3 scripts/validate-frontmatter.py --file /tmp/feature-registry-candidate.md
# Exit 0 — valid
```

File copied to `/features/FEAT-2026-0008.md`.

**Step 5 — Event emission:**

```sh
# Capture timestamp and version at emission time
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SOURCE_VERSION=$(scripts/read-agent-version.sh specs)

# Write minified event to temp file
cat > /tmp/event.json << EOF
{"timestamp":"${TIMESTAMP}","correlation_id":"FEAT-2026-0008","event_type":"feature_created","source":"specs","source_version":"${SOURCE_VERSION}","payload":{"feature_title":"Widget Catalog API","involved_repos":["Bontyyy/orchestrator-api-sample"],"autonomy_default":"review","correlation_id":"FEAT-2026-0008"}}
EOF

# Validate
python3 scripts/validate-event.py --file /tmp/event.json
# Exit 0 — valid

# Append with safe pattern
printf '%s\n' "$(cat /tmp/event.json)" >> events/FEAT-2026-0008.jsonl
```

**Step 6 — Verification:**

```sh
# Re-read and re-validate the registry file
python3 scripts/validate-frontmatter.py --file features/FEAT-2026-0008.md
# Exit 0

# Re-read and re-validate the event log
python3 scripts/validate-event.py --file events/FEAT-2026-0008.jsonl
# Exit 0

# Confirm correlation ID consistency
# Filename: FEAT-2026-0008 ✓
# Frontmatter correlation_id: FEAT-2026-0008 ✓
# Event envelope correlation_id: FEAT-2026-0008 ✓
# Event payload correlation_id: FEAT-2026-0008 ✓
```

Intake complete. The feature is now in `drafting` state with a valid registry entry and a validated `feature_created` event. The spec-drafting skill can proceed.

## Artifacts produced

| Artifact | Path | Validated against |
|---|---|---|
| Feature registry entry | `/features/FEAT-YYYY-NNNN.md` | `feature-frontmatter.schema.json` via `validate-frontmatter.py` |
| Feature event log | `/events/FEAT-YYYY-NNNN.jsonl` | `event.schema.json` + `feature_created.schema.json` via `validate-event.py` |

## Schemas consumed

- [`shared/schemas/feature-frontmatter.schema.json`](../../../../shared/schemas/feature-frontmatter.schema.json) — frontmatter validation.
- [`shared/schemas/event.schema.json`](../../../../shared/schemas/event.schema.json) — event envelope validation.
- [`shared/schemas/events/feature_created.schema.json`](../../../../shared/schemas/events/feature_created.schema.json) — per-type payload validation (additive; authored in WU 4.2).

## Rules absorbed

- [`shared/rules/correlation-ids.md`](../../../../shared/rules/correlation-ids.md) — ID format, minting rules, uniqueness guarantee.
- [`shared/rules/verify-before-report.md`](../../../../shared/rules/verify-before-report.md) — four-step cycle, event-emission operational discipline (timestamps at emission time, canonical `--file` invocation, JSONL single-line requirement, safe append pattern), corrective cycle limit.
- [`shared/rules/never-touch.md`](../../../../shared/rules/never-touch.md) — path prohibition check on every write.
- [`shared/rules/state-vocabulary.md`](../../../../shared/rules/state-vocabulary.md) — `drafting` is the initial feature state; no transition occurs during intake (the feature is created in `drafting`).
- [`shared/rules/escalation-protocol.md`](../../../../shared/rules/escalation-protocol.md) — `spinning_detected` escalation after three consecutive validation failures.

## Anti-patterns

1. **Skipping the collision check.** Even if the directory listing shows a clear gap, the existence check at the computed path is mandatory. A race between listing and writing, or a non-standard filename inflating the max ordinal, can produce a collision.
2. **Defaulting autonomy without asking.** The skill must not silently assume `review`. The human's autonomy choice is load-bearing for downstream agent behavior; an undeclared default hides the decision.
3. **Drafting body content.** The body sections carry placeholder text ("To be drafted during spec authoring"), not fabricated descriptions. Drafting spec content is the spec-drafting skill's concern (WU 4.3).
4. **Populating the task graph.** The `task_graph` is `[]` at intake. Task decomposition is the PM agent's responsibility after the feature reaches `planning`.
5. **Eye-caching `source_version`.** The `source_version` field must be read at emission time via `scripts/read-agent-version.sh specs`, not copied from `version.md` or remembered from a prior emission.
6. **Appending the event before validation.** The event must pass `validate-event.py` with exit 0 before it is appended to the JSONL file. An invalid event in the log corrupts the audit trail.
7. **Using `cat >>` instead of the safe append pattern.** The `printf '%s\n' "$(cat /tmp/event.json)" >> file` pattern guarantees the trailing newline. Plain `cat >>` is unsafe.
