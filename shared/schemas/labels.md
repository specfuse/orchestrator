# GitHub issue label taxonomy

Component repos use GitHub issues to represent tasks. A task's open/closed state plus the labels below constitute its canonical state (see orchestrator-architecture.md §3 and §6.2). The PM agent applies state and type labels at issue creation; state labels are rotated by whichever role owns the relevant transition (§6.3).

Every task issue carries exactly one `state:*` label, exactly one `type:*` label, and exactly one `autonomy:*` label. Additional labels (area, priority, etc.) are out of scope for this taxonomy and may be added by individual component repos without coordination.

Colors are suggestions meant to keep related labels visually grouped; repos may adjust them, but consistency across the org makes cross-repo triage easier.

## State labels

Mirror the task state machine in §6.2.

| Label | Meaning | Color (hex) |
|---|---|---|
| `state:pending` | Exists, dependencies unmet | `#c2c2c2` |
| `state:ready` | Dependencies met, prompt attached, agent may pick up | `#0e8a16` |
| `state:in-progress` | Component/QA agent actively working | `#1d76db` |
| `state:in-review` | PR open, awaiting review | `#5319e7` |
| `state:blocked-spec` | Spec or generator issue raised; escalated upstream | `#d93f0b` |
| `state:blocked-human` | Spinning detected or autonomy requires intervention | `#b60205` |
| `state:done` | PR merged | `#2ea44f` |
| `state:abandoned` | Task explicitly killed | `#6a737d` |

Note: GitHub label slugs do not allow underscores in the conventional style used here, so `blocked_spec` and `blocked_human` in the state machine render as `blocked-spec` and `blocked-human` on labels. The mapping is one-to-one.

## Type labels

Mirror the four task types from §3.

| Label | Meaning | Color (hex) |
|---|---|---|
| `type:implementation` | Code written by a component agent | `#fbca04` |
| `type:qa-authoring` | Test plan authored by the QA agent | `#f9d0c4` |
| `type:qa-execution` | Test plan executed by the QA agent | `#fef2c0` |
| `type:qa-curation` | Regression suite curated by the QA agent | `#e4b400` |

Slug mapping: `qa_authoring` → `qa-authoring`, etc.

## Autonomy labels

Mirror the autonomy levels from §3. The PM agent stamps one at plan approval; the human may override it per task during plan review.

| Label | Meaning | Color (hex) |
|---|---|---|
| `autonomy:auto` | Agent executes end to end; merge automation gated on §10 | `#bfd4f2` |
| `autonomy:review` | Agent executes; human approves merge | `#7f8fb0` |
| `autonomy:supervised` | Agent proposes plan as a comment before writing code | `#3b4252` |
