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

## scripts/requirements.txt

Declares the Python package dependencies for the scripts in this directory:

- `jsonschema>=4.18` — JSON Schema Draft 2020-12 validation (used by both
  validate-event.py and validate-frontmatter.py).
- `pyyaml>=6.0` — YAML parsing for feature frontmatter (used by
  validate-frontmatter.py).
