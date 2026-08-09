#!/usr/bin/env python3
"""Raise a spec issue as a GitHub issue in the product specs repo.

The authorized path to a spec change (never-touch.md §6): instead of editing the specs, any
non-specs actor (component / QA / PM / a general session) files a structured spec issue. This
producer turns a filled spec-issue template (shared/templates/spec-issue.md — Observation /
Location / Triggering task / Suggested resolution) into a GitHub issue in the specs repo,
labelled `specfuse:spec-issue` (+ `initiative:INIT-…` when the triggering task is orchestrated),
and records a `spec_issue_raised` event in the orchestration event log for the audit thread.

The specs agent then monitors/acts on `specfuse:spec-issue` issues (gh-pick + spec-issue-triage).

    python3 -m specfuse.orchestrator.raise_spec_issue --file filled-spec-issue.md
    python3 -m specfuse.orchestrator.raise_spec_issue --file x.md --specs-repo acme/specs-sample --dry-run

Filing a GitHub issue does NOT touch /product/ — it is the routing step, not a spec edit.
Requires the `gh` CLI authenticated (for non-dry runs) and pyyaml is not needed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from specfuse.orchestrator import paths
from specfuse.orchestrator.validate_event import validate as validate_event

DEFAULT_SPECS_REPO = "acme/specs-sample"

REQUIRED_SECTIONS = ["## Observation", "## Location", "## Triggering task", "## Suggested resolution"]
CORRELATION_RE = re.compile(r"Correlation ID:\s*((?:FEAT|INIT)-\d{4}-\d{4}(?:/F\d{2})?(?:/T\d{2})?)")
ROOT_RE = re.compile(r"^((?:FEAT|INIT)-\d{4}-\d{4})")

LABEL_SPEC_ISSUE = ("specfuse:spec-issue", "D93F0B", "Spec change request routed to the specs agent")
LABEL_INITIATIVE_COLOR = "5319E7"


def section_text(body: str, heading: str) -> str:
    """Text under a `## Heading` up to the next `## `."""
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        return ""
    # strip HTML comments + blank lines
    txt = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    return "\n".join(ln for ln in (raw.rstrip() for raw in txt.splitlines()) if ln.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="File a spec issue as a GitHub issue in the specs repo")
    ap.add_argument("--file", required=True, help="filled spec-issue template (Observation/Location/Triggering task/Suggested resolution)")
    ap.add_argument("--specs-repo", default=DEFAULT_SPECS_REPO, help=f"owner/repo (default {DEFAULT_SPECS_REPO})")
    ap.add_argument("--title", help="issue title (default derived from Observation)")
    ap.add_argument("--source", default="human", help="event source: human|pm|qa|component:<name> (default human)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.file)
    if not src.is_file():
        sys.stderr.write(f"error: spec-issue file not found: {src}\n")
        return 2
    body = src.read_text()

    missing = [h for h in REQUIRED_SECTIONS if not re.search(rf"^{re.escape(h)}\s*$", body, re.M)]
    if missing:
        sys.stderr.write(f"error: spec-issue missing section(s): {', '.join(missing)}\n")
        return 2

    cm = CORRELATION_RE.search(body)
    if not cm:
        sys.stderr.write("error: no `Correlation ID: FEAT-/INIT-…` found in the Triggering task section\n")
        return 2
    correlation = cm.group(1)
    root = ROOT_RE.match(correlation).group(1)
    initiative = root if root.startswith("INIT-") else None

    title = args.title or ("[spec-issue] " + (section_text(body, "## Observation").splitlines() or ["(no observation)"])[0][:80])
    labels = [LABEL_SPEC_ISSUE[0]] + ([f"initiative:{initiative}"] if initiative else [])

    if args.dry_run:
        print(f"[dry-run] would file spec-issue on {args.specs_repo}")
        print(f"  title:   {title}")
        print(f"  labels:  {', '.join(labels)}")
        print(f"  thread:  {correlation}  (event log: events/{root}.jsonl)")
        print(f"  ensure labels: {LABEL_SPEC_ISSUE[0]}" + (f", initiative:{initiative}" if initiative else ""))
        return 0

    # ensure labels exist (idempotent)
    subprocess.run(["gh", "label", "create", LABEL_SPEC_ISSUE[0], "--repo", args.specs_repo,
                    "--color", LABEL_SPEC_ISSUE[1], "--description", LABEL_SPEC_ISSUE[2], "--force"],
                   capture_output=True, text=True)
    if initiative:
        subprocess.run(["gh", "label", "create", f"initiative:{initiative}", "--repo", args.specs_repo,
                        "--color", LABEL_INITIATIVE_COLOR, "--description", "Links an issue to its initiative", "--force"],
                       capture_output=True, text=True)

    # create the issue
    cmd = ["gh", "issue", "create", "--repo", args.specs_repo, "--title", title, "--body", body]
    for lbl in labels:
        cmd += ["--label", lbl]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"error: gh issue create failed: {r.stderr.strip()}\n")
        return 1
    issue_url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    print(f"filed spec-issue: {issue_url}")

    # record spec_issue_raised in the orchestration event log (audit thread)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlation_id": correlation,
        "event_type": "spec_issue_raised",
        "source": args.source,
        "source_version": "n/a",
        "payload": {
            "specs_repo": args.specs_repo,
            "issue_url": issue_url,
            "location": (section_text(body, "## Location").splitlines() or [""])[0],
        },
    }
    line = json.dumps(event)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        tf.write(line + "\n")
        tmp = tf.name
    errors = validate_event(tmp)
    if errors:
        sys.stderr.write(
            "warning: spec_issue_raised event failed validation, not appended:\n" + "\n".join(errors)
        )
        return 0  # the GitHub issue is filed; the event is the audit nicety
    state_root = paths.state_root()
    log = state_root / "events" / f"{root}.jsonl"
    with log.open("a") as fh:
        fh.write(line + "\n")
    print(f"recorded spec_issue_raised {correlation} -> {log.relative_to(state_root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
