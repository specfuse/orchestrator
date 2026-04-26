# scripts/

Helper scripts for the Specfuse Orchestrator. All scripts are designed to be
invoked from the **orchestration repo root** (the parent of this directory).

---

## Bootstrap (first use / cold-open)

The Python scripts require `pyyaml` and `jsonschema`. Install them once into a
virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
```

Then replace `python3 scripts/...` with `.venv/bin/python scripts/...` in the
commands below, or activate the venv first:

```sh
source .venv/bin/activate
# now `python3` resolves to the venv interpreter
```

If you are on a system without PEP 668 restrictions (e.g. a CI container), you
can install globally:

```sh
pip install -r scripts/requirements.txt
```

---

## scripts/validate-event.py

Validates one or more JSONL event log entries against
`shared/schemas/event.schema.json` (top-level envelope) and the matching
per-type payload schema under `shared/schemas/events/` (if one exists).

**Two supported invocation patterns:**

```sh
# Stdin — pipe a single event or a full .jsonl file:
echo '{"timestamp": "..."}' | python3 scripts/validate-event.py
cat events/FEAT-2026-0004.jsonl | python3 scripts/validate-event.py
python3 scripts/validate-event.py --stdin   # explicit alias

# File — pass a path:
python3 scripts/validate-event.py --file events/FEAT-2026-0004.jsonl
```

Exit codes: `0` = all events valid, `1` = validation failure, `2` = setup error.

Every event appended to `events/*.jsonl` **must** pass this validator with exit
`0` before the append, per `shared/rules/verify-before-report.md` §3.

---

## scripts/validate-frontmatter.py

Validates the YAML frontmatter of a feature registry file against
`shared/schemas/feature-frontmatter.schema.json`.

**Two supported invocation patterns:**

```sh
# Stdin — pipe the full content of a feature .md file:
cat features/FEAT-2026-0004.md | python3 scripts/validate-frontmatter.py
python3 scripts/validate-frontmatter.py --stdin   # explicit alias

# File — pass a path:
python3 scripts/validate-frontmatter.py --file features/FEAT-2026-0004.md
```

Exit codes: `0` = frontmatter valid, `1` = validation failure, `2` = setup error.

Run this before committing any change to `features/*.md` that touches the YAML
frontmatter block, per `shared/rules/verify-before-report.md` §3.

---

## scripts/read-agent-version.sh

Reads the current version string from `agents/<role>/version.md`. Used to
populate the `source_version` field on agent-emitted events at emission time.

```sh
scripts/read-agent-version.sh pm          # → e.g. "1.6.0"
scripts/read-agent-version.sh component   # → e.g. "1.2.0"
```

Exit codes: `0` = version on stdout, `1` = parse failure, `2` = setup error.

Never eye-cache the version from an earlier read; invoke this script at the
moment each event is constructed, per `shared/rules/verify-before-report.md` §3.

---

## scripts/template-clone-strip.sh

Strips walkthrough/feature/event content from a fresh template clone of the
orchestrator scaffolding, preparing it for use as a downstream project's
private orchestration repo. **Also captures the upstream anchor** (URL +
commit SHA at clone time) into a top-level `UPSTREAM` file — the durable
record of where the downstream diverged from upstream, used as the diff
base for future syncs and read by `add-upstream-remote.sh` to configure
the remote.

```sh
# from inside a fresh clone of the orchestrator scaffolding:
./scripts/template-clone-strip.sh . --dry-run        # preview
./scripts/template-clone-strip.sh .                  # strip + capture UPSTREAM
./scripts/template-clone-strip.sh . --strip-impl-plan  # also remove the
                                                       # orchestrator's own
                                                       # implementation plan
```

The script removes Phase 1–4 walkthrough features, events, inbox artifacts,
and `docs/walkthroughs/`, then seeds `.gitkeep` in the directories that must
remain. It does **not** touch `.git` — the caller re-initializes git history
after running. **Run it before `rm -rf .git`** so the upstream URL and HEAD
can be captured from the clone's `.git` directory.

Refuses to run if the target's `.git` remote points at the upstream
`Specfuse/orchestrator`. Verify with `--dry-run` before applying.

See `docs/upstream-downstream-sync.md` for the full template-clone workflow,
including how to pull upstream improvements over time and how to contribute
fixes back upstream.

---

## scripts/sync-upstream.sh

Interactive helper for the periodic upstream sync. Lists upstream commits
since the downstream's `UPSTREAM` anchor (path-scoped to scaffolding paths
only, excluding `docs/walkthroughs/` and downstream-private dirs), then
walks the operator through each one with a take / skip / diff / quit prompt
and cherry-picks the chosen commits. Halts on conflict with clear resume
instructions; offers to advance the `UPSTREAM` anchor at the end.

```sh
# from the root of a downstream orchestration repo:
./scripts/sync-upstream.sh                  # interactive
./scripts/sync-upstream.sh --list           # read-only review (no prompts)
./scripts/sync-upstream.sh --target <ref>   # compare against a different ref
```

Pre-conditions: clean working tree, `upstream` remote configured, valid
`UPSTREAM` file. The script enforces these and errors out clearly if any
are missing.

See `docs/upstream-downstream-sync.md` for the full sync workflow,
including manual alternatives and follow-up steps (validator runs,
per-agent version review).

---

## scripts/add-upstream-remote.sh

Configures the upstream Specfuse-orchestrator remote on a downstream
orchestration repo as **read-only** (push URL set to `DISABLE` so accidental
pushes to upstream cannot happen). Reads the upstream URL from the
top-level `UPSTREAM` file (created by `template-clone-strip.sh`).

```sh
# run once after `gh repo create ... --source=. --push`:
./scripts/add-upstream-remote.sh

# if upstream is already configured, the script reports its current state
# and exits without changes; pass --reset to reconfigure:
./scripts/add-upstream-remote.sh --reset
```

Idempotent. Errors out if `UPSTREAM` is missing or contains placeholder
values; fill in `UPSTREAM` first (the file's header documents its format).

---

## scripts/requirements.txt

Declares the Python package dependencies for the scripts in this directory:

- `jsonschema>=4.18` — JSON Schema Draft 2020-12 validation (used by both
  validate-event.py and validate-frontmatter.py).
- `pyyaml>=6.0` — YAML parsing for feature frontmatter (used by
  validate-frontmatter.py).
