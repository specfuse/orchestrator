#!/usr/bin/env python3
"""Reconcile generated-code overrides after a regeneration (architecture §9.3).

The codegen generator blindly overwrites `_generated/` every run, clobbering any active override
(an authorized manual edit to a generated file, recorded in `/overrides/`). After a regen — the
`codegen-run` skill is the trigger — each active override must be reconciled:

  - tracking issue CLOSED (the regen output is now correct) -> RETIRE: status -> expired,
    emit `override_expired`, and close the tracking issue.
  - tracking issue OPEN (the problem is unfixed, the override is still needed) -> REAPPLY: if the
    record carries a `patch`, `git apply` it in the component checkout and emit `override_applied`;
    otherwise FLAG it (the metadata alone can't reconstruct the change) — a `blocked_spec`
    condition for a human/agent to reapply.

Under Model B this is the component-agent role's one retained job (the loop is codegen-free); this
script is its runtime. Run it standalone or let `codegen-run` invoke it post-generation.

    python3 scripts/reconcile-overrides.py                 # all active overrides
    python3 scripts/reconcile-overrides.py --repo RestoManagerApp/Backend
    python3 scripts/reconcile-overrides.py --dry-run

Requires `gh` (tracking-issue state) and pyyaml is not needed (records are JSON).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from specfuse.orchestrator import paths
from specfuse.orchestrator.validate_event import validate as validate_event
ROOT_RE = re.compile(r"^((?:FEAT|INIT)-\d{4}-\d{4})")


def issue_state(ref: str) -> str | None:
    """OPEN / CLOSED for an owner/repo#N tracking issue, else None."""
    m = re.match(r"^(.+)#(\d+)$", ref)
    if not m:
        return None
    r = subprocess.run(["gh", "issue", "view", m.group(2), "--repo", m.group(1),
                        "--json", "state", "-q", ".state"], capture_output=True, text=True)
    return r.stdout.strip().upper() if r.returncode == 0 and r.stdout.strip() else None


def emit_event(correlation: str, event_type: str, payload: dict, dry: bool) -> None:
    root = ROOT_RE.match(correlation).group(1)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlation_id": correlation, "event_type": event_type,
        "source": "pm", "source_version": "n/a", "payload": payload,
    }
    line = json.dumps(event)
    if dry:
        print(f"      [dry] would emit {event_type} {correlation}")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        tf.write(line + "\n")
        tmp = tf.name
    errors = validate_event(tmp)
    if errors:
        sys.stderr.write("      event failed validation, not appended: " + "\n".join(errors))
        return
    with (paths.state_root() / "events" / f"{root}.jsonl").open("a") as fh:
        fh.write(line + "\n")
    print(f"      emitted {event_type} {correlation}")


def reconcile(path: Path, rec: dict, repos_root: Path, dry: bool) -> None:
    cid = rec["task_correlation_id"]
    tracking = rec["tracking_issue"]
    state = issue_state(tracking)
    if state is None:
        print(f"    {path.name}: tracking issue {tracking} state unresolved — skip (gh failed?)")
        return

    if state == "CLOSED":
        # RETIRE: regen output is now correct
        print(f"    {path.name}: tracking {tracking} CLOSED -> retire (expired)")
        if not dry:
            rec["status"] = "expired"
            path.write_text(json.dumps(rec, indent=2) + "\n")
        emit_event(cid, "override_expired", {"tracking_issue": tracking, "files": rec["files"]}, dry)
        return

    # OPEN: still needed; regen clobbered it -> reapply or flag
    patch = rec.get("patch")
    if not patch:
        print(f"    {path.name}: tracking {tracking} OPEN, NO patch -> FLAG (blocked_spec): "
              f"override still needed but cannot auto-reapply; reapply {rec['files']} manually")
        emit_event(cid, "human_escalation",
                   {"summary": f"override {path.name} needs manual reapply after regen ({rec['files']})",
                    "reason": "spec_level_blocker"}, dry)
        return
    repo = rec.get("repo")
    checkout = repos_root / repo.split("/")[-1] if repo else None
    if dry:
        print(f"    {path.name}: tracking {tracking} OPEN, patch present -> would git apply in "
              f"{checkout or '<repo>'}")
        return
    if not checkout or not checkout.is_dir():
        print(f"    {path.name}: OPEN with patch but no checkout ({checkout}) — FLAG")
        emit_event(cid, "human_escalation",
                   {"summary": f"override {path.name} reapply blocked: no checkout for {repo}",
                    "reason": "spec_level_blocker"}, dry)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as tf:
        tf.write(patch if patch.endswith("\n") else patch + "\n")
        pf = tf.name
    r = subprocess.run(["git", "-C", str(checkout), "apply", pf], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"    {path.name}: reapplied patch in {checkout}")
        emit_event(cid, "override_applied", {"tracking_issue": tracking, "files": rec["files"]}, dry)
    else:
        print(f"    {path.name}: git apply FAILED in {checkout}: {r.stderr.strip()} -> FLAG (blocked_spec)")
        emit_event(cid, "human_escalation",
                   {"summary": f"override {path.name} reapply failed: {r.stderr.strip()[:200]}",
                    "reason": "spec_level_blocker"}, dry)


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile generated-code overrides after a regen (architecture §9.3)")
    ap.add_argument("--repo", help="only reconcile overrides whose `repo` matches owner/repo")
    ap.add_argument("--repos-root", default=None, help="dir holding component checkouts (default: orchestrator's parent)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state_root = paths.state_root()
    records = sorted(glob.glob(str(state_root / "overrides" / "*.json")))
    active = []
    for f in records:
        rec = json.loads(Path(f).read_text())
        if rec.get("status") != "active":
            continue
        if args.repo and rec.get("repo") != args.repo:
            continue
        active.append((Path(f), rec))

    print(f"reconcile-overrides{' [dry-run]' if args.dry_run else ''}: "
          f"{len(active)} active override(s)" + (f" for {args.repo}" if args.repo else ""))
    if not active:
        print("  nothing to reconcile")
        return 0
    repos_root = Path(args.repos_root) if args.repos_root else state_root.parent
    for path, rec in active:
        reconcile(path, rec, repos_root, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
