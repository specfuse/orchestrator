#!/usr/bin/env python3
"""Auto-dispatch the QA agent on ready QA-feature GitHub issues.

The QA half of the dispatch surface (docs/naming-convention.md §"Dispatch by feature type").
`qa_*` features are dispatched to the **QA agent** (a distinct cross-repo role), NOT a loop — the
loop is single-repo + edit-and-commit while QA is cross-repo (test plans in the specs repo, run
against component code, events to the orchestrator log). PM issue-drafting labels QA feature
issues `specfuse:qa-feature`; the poller recomputes their `pending → ready`. This loop then, per
pass, finds READY `specfuse:qa-feature` issues, claims each (`state:ready → state:in-progress`,
the dedup marker), and spawns a fresh QA-agent session to do the work.

The spawned session runs in the orchestrator project (sibling repos accessible). It may write
test plans under `specs-sample/product/test-plans/` — allowed by the deny-specs-edit hook's
carve-out (never-touch.md §6); the rest of the specs repo stays blocked.

    python3 -m specfuse.orchestrator.qa_dispatcher                 # scan the initiative's involved_repos
    python3 -m specfuse.orchestrator.qa_dispatcher --repo acme/api-sample --dry-run
    python3 -m specfuse.orchestrator.qa_dispatcher --interval 300

Requires the `gh` CLI authenticated and `claude` available (for non-dry runs).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from specfuse.orchestrator import paths

try:
    import yaml
except ImportError:
    sys.stderr.write("error: pyyaml required (pip install specfuse-orchestrator)\n")
    sys.exit(2)

QA_LABEL = "specfuse:qa-feature"
QA_CLAUDE = "agents/qa/CLAUDE.md"
TITLE_ID_RE = re.compile(r"\[((?:FEAT|INIT)-\d{4}-\d{4}(?:/F\d{2})?)\]")


def involved_repos(registry: Path) -> list[str]:
    text = registry.read_text()
    fm = yaml.safe_load(text[3:text.index("\n---", 3)])
    return fm.get("involved_repos", [])


def default_registry() -> Path | None:
    c = sorted(p for p in (paths.state_root() / "features").glob("INIT-*.md")
               if not p.name.endswith(("-plan.md", "-issues-dryrun.md")))
    return c[-1] if c else None


def ready_qa_issues(slug: str) -> list[dict]:
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", slug, "--state", "open", "--label", QA_LABEL,
         "--json", "number,title,labels,url", "--limit", "200"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh issue list failed on {slug}: {r.stderr.strip()}")
    out = []
    for it in json.loads(r.stdout or "[]"):
        labels = [lbl["name"] for lbl in it.get("labels", [])]
        if "state:ready" not in labels:  # only ready features (poller set this); in-progress = already dispatched
            continue
        it["_repo"] = slug
        it["_labels"] = labels
        out.append(it)
    return out


def dispatch_one(issue: dict, dry: bool) -> None:
    slug = issue["_repo"]
    num = issue["number"]
    m = TITLE_ID_RE.search(issue["title"])
    cid = m.group(1) if m else f"{slug}#{num}"
    if dry:
        print(f"    would dispatch QA agent on {slug}#{num} ({cid}): {issue['title']}")
        return
    # claim: state:ready -> state:in-progress (dedup marker)
    subprocess.run(["gh", "issue", "edit", str(num), "--repo", slug,
                    "--remove-label", "state:ready", "--add-label", "state:in-progress"],
                   capture_output=True, text=True)
    prompt = (
        f"You are the QA agent. Handle QA feature {cid} (GitHub issue {slug}#{num}, label "
        f"{QA_LABEL}). Read {QA_CLAUDE} and the matching skill "
        f"(agents/qa/skills/qa-authoring | qa-execution | qa-curation per the issue's type:qa-* "
        f"label) and follow it: do the work (author the test plan under "
        f"specs-sample/product/test-plans/ for qa_authoring; run it against the component "
        f"code for qa_execution; curate for qa_curation), emit the QA events, honor the "
        f"cross-feature regression invariant (write no labels/state to a feature you do not own — "
        f"file a regression as a NEW feature), set this feature's state labels via the canonical "
        f"state:* scheme, and close/PR per the skill. Escalate per the skill if in doubt."
    )
    proc = subprocess.run(["claude", "-p", prompt], cwd=str(paths.state_root()))
    print(f"    dispatched {cid} ({slug}#{num}) -> QA agent (exit {proc.returncode})")


def run_pass(repos: list[str], dry: bool) -> None:
    total = 0
    for slug in repos:
        try:
            issues = ready_qa_issues(slug)
        except RuntimeError as e:
            sys.stderr.write(f"  pass error: {e}\n")
            continue
        if issues:
            print(f"  {slug}: {len(issues)} ready {QA_LABEL}")
        for issue in issues:
            dispatch_one(issue, dry)
            total += 1
    if total == 0:
        print(f"  no ready {QA_LABEL} issues")


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-dispatch the QA agent on ready qa-features")
    ap.add_argument("--repo", action="append", help="owner/repo to scan (repeatable; default: the initiative's involved_repos)")
    ap.add_argument("--feature", help="initiative registry to read involved_repos from (default: newest INIT-*.md)")
    ap.add_argument("--interval", type=int, default=0, help="poll every N seconds (default: one pass)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repos = args.repo or []
    if not repos:
        reg = Path(args.feature) if args.feature else default_registry()
        if not reg or not reg.is_file():
            sys.stderr.write("error: no --repo given and no INIT-*.md registry found\n")
            return 2
        repos = involved_repos(reg)
        if not repos:
            sys.stderr.write(f"error: no involved_repos in {reg}\n")
            return 2

    def one() -> None:
        print(f"qa-feature-dispatcher{' [dry-run]' if args.dry_run else ''} — repos: {', '.join(repos)}")
        run_pass(repos, args.dry_run)

    if args.interval > 0:
        print(f"polling every {args.interval}s — Ctrl-C to stop")
        while True:
            one()
            time.sleep(args.interval)
    else:
        one()
    return 0


if __name__ == "__main__":
    sys.exit(main())
