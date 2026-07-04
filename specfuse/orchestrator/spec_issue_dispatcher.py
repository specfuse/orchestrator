#!/usr/bin/env python3
"""Auto-dispatch the specs agent on new spec-issue GitHub issues.

The dispatch half of the GitHub spec-issue flow (never-touch.md §6). The producer
(specfuse.orchestrator.raise_spec_issue) files spec change requests as `specfuse:spec-issue` GitHub issues
in the product specs repo; the specs agent's spec-issue-triage skill resolves them. This loop
removes the manual step in between: per pass it finds open `specfuse:spec-issue` issues not yet
being triaged and spawns a fresh specs-agent session (`claude -p`) in the specs repo to run
spec-issue-triage on each.

A `specfuse:in-triage` label is added when an issue is dispatched so a polling tick does not
re-spawn on the same issue; the triage skill closes the issue on resolution (removing it from
the open set). The dispatched session edits /product/ — that is allowed because it runs IN the
specs repo (its own project; the orchestrator's deny-specs-edit hook is scoped to the
orchestrator project, not here).

    python3 -m specfuse.orchestrator.spec_issue_dispatcher                 # one pass, defaults
    python3 -m specfuse.orchestrator.spec_issue_dispatcher --dry-run       # list what would dispatch
    python3 -m specfuse.orchestrator.spec_issue_dispatcher --interval 300  # poll loop

Requires the `gh` CLI authenticated and a local checkout of the specs repo with the specs-agent
config installed (orchestrator-init --target specs).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from specfuse.orchestrator import paths

DEFAULT_SLUG = "RestoManagerApp/restomanager-specs"
SPEC_LABEL = "specfuse:spec-issue"
BUSY_LABEL = "specfuse:in-triage"
TRIAGE_SKILL = ".specfuse/agents/specs/skills/spec-issue-triage/SKILL.md"


def open_spec_issues(slug: str) -> list[dict]:
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", slug, "--state", "open", "--label", SPEC_LABEL,
         "--json", "number,title,labels,url", "--limit", "200"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh issue list failed: {r.stderr.strip()}")
    return json.loads(r.stdout or "[]")


def dispatch_one(slug: str, specs_path: Path, issue: dict, model: str | None, dry: bool) -> None:
    num = issue["number"]
    labels = [lbl["name"] for lbl in issue.get("labels", [])]
    if BUSY_LABEL in labels:
        print(f"  #{num} already {BUSY_LABEL} — skip")
        return
    if dry:
        print(f"  would dispatch specs agent on #{num}: {issue['title']}")
        return
    subprocess.run(["gh", "issue", "edit", str(num), "--repo", slug, "--add-label", BUSY_LABEL],
                   capture_output=True, text=True)
    prompt = (
        f"You are the specs agent for {slug}. Triage spec issue #{num} (label {SPEC_LABEL}). "
        f"Read {TRIAGE_SKILL} and follow it exactly: read the issue body (Observation / Location / "
        f"Triggering task / Suggested resolution), decide spec-content-fix-in-/product vs "
        f"route-to-generator, execute, emit the spec_issue_resolved/routed event, and close issue "
        f"#{num} with a resolution comment. If anything is ambiguous or needs a human decision, "
        f"escalate per the skill's case (d) — do not guess."
    )
    cmd = ["claude"] + (["--model", model] if model else []) + ["-p", prompt]
    proc = subprocess.run(cmd, cwd=str(specs_path))
    print(f"  dispatched #{num} -> specs agent (exit {proc.returncode})")


def run_pass(slug: str, specs_path: Path, model: str | None, dry: bool) -> None:
    try:
        issues = open_spec_issues(slug)
    except RuntimeError as e:
        sys.stderr.write(f"pass error: {e}\n")
        return
    todo = [i for i in issues if BUSY_LABEL not in [lbl["name"] for lbl in i.get("labels", [])]]
    print(f"  {len(issues)} open {SPEC_LABEL}; {len(todo)} to dispatch")
    for issue in todo:
        dispatch_one(slug, specs_path, issue, model, dry)


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-dispatch the specs agent on new spec-issues")
    ap.add_argument("--specs-repo", default=DEFAULT_SLUG, help=f"owner/repo (default {DEFAULT_SLUG})")
    ap.add_argument("--specs-path", default=None, help="local checkout of the specs repo")
    ap.add_argument("--model", help="model for the spawned specs-agent session")
    ap.add_argument("--interval", type=int, default=0, help="poll every N seconds (default: one pass)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    specs_path = Path(args.specs_path) if args.specs_path else paths.state_root().parent / "restomanager-specs"
    if not args.dry_run:
        if not specs_path.is_dir():
            sys.stderr.write(f"error: specs checkout not found: {specs_path}\n")
            return 2
        if not (specs_path / TRIAGE_SKILL).is_file():
            sys.stderr.write(
                f"error: {TRIAGE_SKILL} missing in {specs_path} — run "
                f"orchestrator-init --target specs first\n")
            return 2

    def one() -> None:
        print(f"spec-issue-dispatcher @ {args.specs_repo}{' [dry-run]' if args.dry_run else ''}")
        run_pass(args.specs_repo, specs_path, args.model, args.dry_run)

    if args.interval > 0:
        print(f"polling {args.specs_repo} every {args.interval}s — Ctrl-C to stop")
        while True:
            one()
            time.sleep(args.interval)
    else:
        one()
    return 0


if __name__ == "__main__":
    sys.exit(main())
