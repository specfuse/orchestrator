#!/usr/bin/env python3
#
# Copyright 2026 RestoManager contributors.
#
"""runner.py — initiative runner.

Drives a full INIT-YYYY-NNNN initiative end-to-end:

  1. Poller pass: adopt all state:ready impl features into component loop folders.
  2. Run loop.py in each component repo (sequential, one repo then the next) for
     every adopted feature that is not yet done.
  3. Stop on:
       - gate awaiting review (loop exit 0, human must arm next gate then re-run),
       - blocker (loop exit 1, work unit needs human attention),
       - unarmed gate (loop exit 2, arm draft WUs then re-run),
       - initiative complete (all impl features done).
  4. After each feature completes, re-poll to unblock newly-unblocked deps then
     continue to the next feature.

QA features (qa_authoring / qa_execution / qa_curation / qa_regression) are NOT
driven here — loop.py is single-repo + edit-and-commit; QA is cross-repo and
edit-free. When QA features become ready the runner lists them and exits cleanly
so you can drive them via specfuse.orchestrator.qa_dispatcher.

Exit codes:
  0  clean stop: gate awaiting_review OR all impl features done.
  1  work unit blocked (spinning / agent escalation) — human attention needed.
  2  gate not armed — use --approve or flip draft WUs to pending then re-run.
  3  poller / adopt error or missing prerequisite.

Usage:
    specfuse runner                              # newest INIT-*.md
    specfuse runner --feature features/INIT-2026-0001.md
    specfuse runner --dry-run                    # no writes, no dispatch
    specfuse runner --approve                    # approve gate then continue
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from specfuse.orchestrator import paths
from specfuse.orchestrator.cli import self_provision_if_stale

try:
    import yaml
except ImportError:
    sys.stderr.write("error: pyyaml required. install: pip install specfuse-orchestrator\n")
    sys.exit(3)

POLLER = Path(__file__).resolve().parent / "poller.py"

FM_RE = re.compile(r"^---\s*$", re.MULTILINE)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def parse_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def find_default_registry() -> Path:
    candidates = sorted(
        p for p in (paths.state_root() / "features").glob("INIT-*.md")
        if not p.name.endswith(("-plan.md", "-issues-dryrun.md"))
    )
    if not candidates:
        sys.stderr.write("error: no features/INIT-*.md found; pass --feature\n")
        sys.exit(3)
    return candidates[-1]


def repo_checkout(repos_root: Path, repo_slug: str) -> Path:
    return repos_root / repo_slug.split("/")[-1]


def encode_id(feature_id: str) -> str:
    """INIT-YYYY-NNNN/FNN -> INIT-YYYY-NNNN-FNN (matches adopt_feature.py)."""
    return feature_id.replace("/", "-")


def find_feature_branch(repo_path: Path, correlation_id: str, fid: str) -> str | None:
    """Locate the feature branch for `INIT-YYYY-NNNN/FNN` in `repo_path`.

    Convention (adopt_feature.py): `feat/<encoded-id>-<slug>`. Scans local
    branches first, falls back to remote-tracking branches. Returns the first
    match or None if no branch exists yet (feature has not been adopted).
    """
    encoded = f"{correlation_id}-{fid}"
    pattern = f"feat/{encoded}-*"
    for ref_filter in (("--list", pattern), ("--remote", "--list", f"origin/{pattern}")):
        r = subprocess.run(
            ["git", "-C", str(repo_path), "branch", *ref_filter, "--format=%(refname:short)"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue
        for line in r.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # strip `origin/` prefix from remote-tracking refs
            return line[len("origin/"):] if line.startswith("origin/") else line
    return None


def feature_worktree(repos_root: Path, repo_slug: str, correlation_id: str,
                     fid: str) -> tuple[Path | None, str]:
    """Return (worktree_path, status) for a `repo_slug` feature.

    status is one of:
      - `worktree`        — worktree exists / was created on the feature branch (path returned)
      - `main`            — adopted-in-main-but-no-branch-yet; loop's first run will create
                            the branch via ensure_feature_branch. Returns the main checkout
                            path so the loop runs there once; subsequent runs use a worktree.
      - `not_adopted`     — no branch, no .specfuse/features/<dir> in main — adoption never
                            happened. Path is None.
      - `repo_missing`    — main checkout absent or not a git repo. Path is None.
    """
    main_checkout = repo_checkout(repos_root, repo_slug)
    if not (main_checkout / ".git").exists() and not main_checkout.is_dir():
        return None, "repo_missing"

    branch = find_feature_branch(main_checkout, correlation_id, fid)
    if branch is None:
        # No branch yet — was the feature at least adopted in the main checkout?
        if find_adopted_dir(main_checkout, correlation_id, fid) is not None:
            # Loop will create the branch on first run (ensure_feature_branch).
            # Subsequent passes will see the branch and switch to worktree mode.
            print(f"    [bootstrap] {repo_slug} {fid} adopted in main but no branch yet — "
                  f"first loop pass runs in main checkout (loop creates the branch)")
            return main_checkout, "main"
        return None, "not_adopted"

    # If the main checkout is currently on the feature branch (e.g. loop's first pass
    # ran there to bootstrap the branch), use main directly — git won't let us create
    # a second worktree on a branch already checked out.
    main_on_branch = subprocess.run(
        ["git", "-C", str(main_checkout), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    if main_on_branch == branch:
        print(f"    [main] {repo_slug} {fid}: main checkout is on feature branch — "
              f"dispatching loop in main (worktree blocked by git)")
        return main_checkout, "main"

    wt_root = repos_root / f"{repo_slug.split('/')[-1]}-wt"
    wt_path = wt_root / f"{correlation_id}-{fid}"
    if wt_path.is_dir():
        r = subprocess.run(
            ["git", "-C", str(wt_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
        )
        on_branch = r.stdout.strip() if r.returncode == 0 else ""
        if on_branch != branch:
            print(f"    [warn] worktree {wt_path.name} on {on_branch!r}, expected {branch!r}")
        return wt_path, "worktree"
    wt_root.mkdir(parents=True, exist_ok=True)
    print(f"    [worktree] {repo_slug} {fid} -> creating {wt_path} on {branch}")
    r = subprocess.run(
        ["git", "-C", str(main_checkout), "worktree", "add", str(wt_path), branch],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        # If git refuses because the branch is already checked out somewhere, fall
        # back to whichever existing worktree carries it.
        stderr = (r.stderr or "").strip()
        m = re.search(r"already used by worktree at '([^']+)'", stderr)
        if m:
            existing = Path(m.group(1))
            print(f"    [main] {repo_slug} {fid}: branch already checked out at {existing} — "
                  f"reusing that worktree")
            return existing, "main"
        print(f"    [worktree] FAILED for {fid}: {stderr}")
        return None, "dispatch_failed"
    return wt_path, "worktree"


def find_adopted_dir(repo_path: Path, correlation_id: str, fid: str) -> Path | None:
    """Return the .specfuse/features/<dir> for a given initiative feature, or None."""
    feats = repo_path / ".specfuse" / "features"
    if not feats.is_dir():
        return None
    prefix = f"{correlation_id}-{fid}-"
    for d in feats.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            return d
    return None


def all_gates_passed(feature_dir: Path) -> bool:
    """True iff every GATE-NN.md in the feature dir has status: passed."""
    gates = sorted(feature_dir.glob("GATE-*.md"))
    if not gates:
        return False
    for g in gates:
        fm = parse_frontmatter(g)
        if fm.get("status") != "passed":
            return False
    return True


def any_gate_awaiting_review(feature_dir: Path) -> bool:
    for g in sorted(feature_dir.glob("GATE-*.md")):
        if parse_frontmatter(g).get("status") == "awaiting_review":
            return True
    return False


def plan_complete(feature_dir: Path) -> bool:
    """True iff loop.py has fired on_feature_complete for this feature.

    loop.py writes `status: complete` to PLAN.md inside on_feature_complete
    (after opening the PR and flipping the GitHub issue label). This is the
    canonical signal that the feature is fully done — not just gates-passed,
    but the close-out side-effects have run.
    """
    plan = feature_dir / "PLAN.md"
    if not plan.is_file():
        return False
    return parse_frontmatter(plan).get("status") == "complete"


def set_frontmatter_field(path: Path, key: str, value: str) -> None:
    """Replace a single key's value in a file's YAML frontmatter."""
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path} has no frontmatter")
    end = text.index("\n---", 3)
    block = text[3:end].splitlines()
    pat = re.compile(rf"^{re.escape(key)}:")
    for i, line in enumerate(block):
        if pat.match(line):
            block[i] = f"{key}: {value}"
            break
    else:
        block.append(f"{key}: {value}")
    path.write_text("---\n" + "\n".join(block) + text[end:])


# Display labels for the per-feature post-pass statuses tracked in feature_status.
# Keep terse: one line per feature in the summary table.
STATUS_LABELS = {
    "done": "done (PR opened)",
    "complete_now": "completed this pass (PR opened)",
    "awaiting_review": "awaiting human gate review",
    "awaiting_review_now": "awaiting human gate review (this pass)",
    "unarmed": "draft WUs not armed",
    "unarmed_now": "draft WUs not armed (this pass)",
    "pending": "in-progress (gates not all passed)",
    "blocked": "blocked — needs human attention",
    "loop_missing": "loop not installed in repo",
    "not_adopted": "not adopted (no branch, no feature dir)",
    "main": "adopted in main but no branch yet",
    "dispatch_failed": "loop dispatch failed",
    "unclear": "loop exited 0 in unclear state",
    "loop_error": "loop crashed (rc!=0,1,2)",
    "dry_run": "would dispatch (dry-run)",
    "repo_missing": "component repo checkout missing",
}


def emit_summary(correlation_id: str, impl_entries: list[dict],
                 feature_status: dict[str, str], qa_ready: list[dict],
                 all_impl_done: bool, any_ran: bool) -> None:
    """Final status block + recommended-next-action line.

    Replaces the old `[idle] ... QA features ready ...` blob with a grouped
    summary the operator can scan in one glance, followed by a concrete
    recommendation (or a clean "nothing to do" when the initiative is done).
    """
    print()
    print("=" * 60)
    print(f"PASS SUMMARY — {correlation_id}")
    print("=" * 60)

    if not impl_entries:
        print("  (no impl features in registry)")
    else:
        # Group by status for a quick visual scan.
        from collections import defaultdict
        groups: dict[str, list[str]] = defaultdict(list)
        for entry in impl_entries:
            fid = entry["id"]
            s = feature_status.get(fid, "pending")
            groups[s].append(fid)
        print(f"  IMPL: {len(impl_entries)} features total")
        # Order: done first, then live-progress, then problems.
        order = ["done", "complete_now", "awaiting_review", "awaiting_review_now",
                 "unarmed", "unarmed_now", "pending", "main", "blocked",
                 "dispatch_failed", "unclear", "loop_error", "not_adopted",
                 "loop_missing", "dry_run", "repo_missing"]
        for s in order:
            ids = sorted(groups.get(s, []))
            if not ids:
                continue
            print(f"    [{s:>20}] {len(ids):>2} — {', '.join(ids)}")

    if qa_ready:
        print(f"  QA  : {len(qa_ready)} features (not driven by runner)")
        for f in qa_ready:
            print(f"    {f['fid']:>3} ({f['ftype']:>13}) — {f['repo']}")
    else:
        print("  QA  : (no QA features in registry)")

    # ---- recommended-next ----
    print()
    print("RECOMMENDED NEXT")
    print("-" * 60)
    actions = _recommended_actions(impl_entries, feature_status, qa_ready,
                                   all_impl_done, any_ran)
    if not actions:
        print("  Nothing to do — every feature is done or awaiting a downstream actor.")
    else:
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")
    print()


def _recommended_actions(impl_entries: list[dict], feature_status: dict[str, str],
                         qa_ready: list[dict], all_impl_done: bool,
                         any_ran: bool) -> list[str]:
    """Compose a prioritized list of concrete next-action strings.

    Each string starts with a verb and ends with the exact command or pointer
    the operator needs. Highest-priority blockers first.
    """
    actions: list[str] = []
    by_status: dict[str, list[str]] = {}
    for entry in impl_entries:
        s = feature_status.get(entry["id"], "pending")
        by_status.setdefault(s, []).append(entry["id"])

    # Blocked: human must unblock before anything else moves.
    for fid in sorted(by_status.get("blocked", [])):
        actions.append(
            f"UNBLOCK {fid}: read the feature's events.jsonl + work/ for failure detail; "
            f"resolve the blocker, then re-run `specfuse runner`."
        )
    # Awaiting human gate review.
    review_fids = sorted(by_status.get("awaiting_review_now", []) + by_status.get("awaiting_review", []))
    for fid in review_fids:
        actions.append(
            f"REVIEW {fid}: read the feature's GATE-NN-REVIEW.md (or the most-recent WU-93 "
            f"plan-next body), then re-run `specfuse runner --approve` to pass the gate."
        )
    # Unarmed draft WUs.
    unarmed_fids = sorted(by_status.get("unarmed_now", []) + by_status.get("unarmed", []))
    for fid in unarmed_fids:
        actions.append(
            f"ARM {fid}: re-run `specfuse runner --approve` to arm the draft WUs."
        )
    # Adopted-in-main features (loop's first pass needs to run to create the branch).
    main_fids = sorted(by_status.get("main", []))
    for fid in main_fids:
        actions.append(
            f"BOOTSTRAP {fid}: re-run `specfuse runner` — the loop's first pass will "
            f"create the feature branch in the component repo's main checkout and commit the "
            f"adoption."
        )
    # Not adopted at all.
    not_adopted = sorted(by_status.get("not_adopted", []))
    for fid in not_adopted:
        actions.append(
            f"ADOPT {fid}: the poller should have adopted this feature; "
            f"re-run `specfuse runner` to retry, or invoke "
            f"`.specfuse/scripts/adopt_feature.py <slug> <issue#>` manually in the component repo."
        )
    # Loop missing in a repo.
    loop_missing = sorted(by_status.get("loop_missing", []))
    if loop_missing:
        actions.append(
            f"INSTALL LOOP: features {', '.join(loop_missing)} are in a component repo whose "
            f"loop install is missing (no `.specfuse/scripts/loop.py`). Run the loop's `init.sh` "
            f"in that repo."
        )
    # In-progress (gates not all passed) — runner just needs to keep going.
    pending = sorted(by_status.get("pending", []))
    if pending and not (review_fids or unarmed_fids):
        actions.append(
            f"GRIND {len(pending)} feature(s) — {', '.join(pending)}: re-run "
            f"`specfuse runner` to advance their gates."
        )
    # QA dispatcher needed. A QA feature is "unblocked now" iff every dep FID is in
    # `done` or `complete_now` (impl feature) — QA deps reference sibling FIDs in
    # the same initiative graph.
    done_fids = {fid for fid, s in feature_status.items() if s in ("done", "complete_now")}
    unblocked_qa = [f for f in qa_ready if all(d in done_fids for d in f["depends_on"])]
    blocked_qa = [f for f in qa_ready if f not in unblocked_qa]
    if unblocked_qa:
        ids = ", ".join(f["fid"] for f in unblocked_qa)
        actions.append(
            f"DISPATCH {len(unblocked_qa)} unblocked QA feature(s) ({ids}) — "
            f"`python3 -m specfuse.orchestrator.qa_dispatcher` (runner does not drive QA)."
        )
    if blocked_qa:
        ids = ", ".join(f["fid"] for f in blocked_qa)
        actions.append(
            f"WAIT on {len(blocked_qa)} QA feature(s) blocked by impl deps ({ids}) — "
            f"they unblock automatically as their depends_on impl features reach `done`."
        )
    if all_impl_done and not qa_ready:
        actions.append(
            "INITIATIVE COMPLETE — `specfuse poller` will emit the "
            "`in_progress → done` transition (or run `/initiative-status` manually)."
        )
    return actions


def approve_gate(feature_dir: Path) -> bool:
    """Approve the current pending gate in a feature dir.

    Handles two cases:
      - Draft WUs (unarmed gate): flip all WU-*.md with status: draft -> pending.
      - Gate awaiting review: set the awaiting_review gate to passed, arm any
        draft WUs in the next gate so the runner can continue immediately.

    Returns True if anything was changed.
    """
    changed = False

    # Case 1: pass any gate that is awaiting_review.
    for gate_file in sorted(feature_dir.glob("GATE-*.md")):
        fm = parse_frontmatter(gate_file)
        if fm.get("status") == "awaiting_review":
            set_frontmatter_field(gate_file, "status", "passed")
            print(f"  [approve] {gate_file.name}: awaiting_review -> passed")
            changed = True

    # Case 2: arm any draft WUs (covers both unarmed-gate and next-gate drafts).
    for wu_file in sorted(feature_dir.glob("WU-*.md")):
        fm = parse_frontmatter(wu_file)
        if fm.get("status") == "draft":
            set_frontmatter_field(wu_file, "status", "pending")
            print(f"  [approve] {wu_file.name}: draft -> pending")
            changed = True

    return changed


# --------------------------------------------------------------------------- #
# Poller pass
# --------------------------------------------------------------------------- #

def run_poller(registry: Path, repos_root: Path, dry_run: bool) -> int:
    cmd = [
        sys.executable, str(POLLER),
        "--feature", str(registry),
        "--backend", "loop",
        "--repos-root", str(repos_root),
    ]
    if dry_run:
        cmd.append("--dry-run")
    print(f"\n{'='*60}")
    print("POLLER PASS")
    print(f"{'='*60}")
    result = subprocess.run(cmd)
    return result.returncode


# --------------------------------------------------------------------------- #
# Loop runner
# --------------------------------------------------------------------------- #

def run_loop(repo_path: Path, feature_dir_name: str, dry_run: bool) -> int:
    cmd = [sys.executable, ".specfuse/scripts/loop.py", "--feature", feature_dir_name]
    if dry_run:
        cmd.append("--dry-run")
    print(f"\n{'='*60}")
    print(f"LOOP  {repo_path.name} / {feature_dir_name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(repo_path))
    return result.returncode


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Initiative runner — poller + loop for each repo.")
    ap.add_argument("--feature", help="Path to an initiative registry .md (default: newest).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Pass --dry-run to both poller and loop; no writes, no dispatch.")
    ap.add_argument("--approve", action="store_true",
                    help="Approve the current gate (arm draft WUs / pass awaiting_review) "
                         "then continue running.")
    ap.add_argument("--repos-root", default=None,
                    help="Parent dir holding component repo checkouts.")
    args = ap.parse_args()
    self_provision_if_stale(paths.state_root())
    if args.repos_root is None:
        args.repos_root = str(paths.state_root().parent)

    registry = Path(args.feature) if args.feature else find_default_registry()
    if not registry.is_file():
        sys.stderr.write(f"error: registry not found: {registry}\n")
        return 3

    repos_root = Path(args.repos_root)
    fm = parse_frontmatter(registry)
    correlation_id = fm["correlation_id"]
    involved_repos: list[str] = fm.get("involved_repos", [])

    print(f"runner: {correlation_id}  repos={[r.split('/')[-1] for r in involved_repos]}")
    if args.dry_run:
        print("(dry-run mode — no writes)")

    # Outer loop: poller + one loop pass per cycle.
    # Exits on any non-clean state; re-run after human intervention.
    while True:
        # 1. Poller pass — adopt newly-ready impl features, flip pending→ready labels.
        rc = run_poller(registry, repos_root, args.dry_run)
        if rc != 0:
            sys.stderr.write(f"error: poller exited {rc}\n")
            return 3

        # 2. Re-read registry to get current graph (poller may have changed labels).
        fm = parse_frontmatter(registry)

        # Partition features by type and collect impl features per repo.
        impl_by_repo: dict[str, list[dict]] = {r: [] for r in involved_repos}
        qa_ready: list[dict] = []

        for entry in fm.get("feature_graph") or fm.get("task_graph") or []:
            ftype: str = entry["type"]
            fid: str = entry["id"]
            repo: str = entry["assigned_repo"]
            if ftype.startswith("qa_"):
                # QA readiness is reported; runner does not drive them.
                qa_ready.append({
                    "fid": fid, "ftype": ftype, "repo": repo,
                    "depends_on": entry.get("depends_on", []) or [],
                })
                continue
            if repo in impl_by_repo:
                impl_by_repo[repo].append(entry)

        # 3. Run loop for each impl feature in each repo, sequential.
        # Each feature lives on its own branch (`feat/<encoded-id>-*`) with the
        # .specfuse/features/<dir> populated by adopt_feature.py. We materialize
        # one git worktree per feature so the loop sees the right tree without
        # branch-juggling in the main checkout.
        any_ran = False
        retry = False  # set to True by --approve to skip the completion check and re-poll
        # Per-feature post-pass status for the final summary. Key: fid; value: one of:
        #   done, complete_now, awaiting_review, awaiting_review_now, unarmed, unarmed_now,
        #   blocked, loop_missing, not_adopted, dispatch_failed.
        feature_status: dict[str, str] = {}
        for repo_slug in involved_repos:
            main_path = repo_checkout(repos_root, repo_slug)
            loop_script = main_path / ".specfuse" / "scripts" / "loop.py"
            if not loop_script.is_file():
                print(f"[skip] {repo_slug}: loop not installed (.specfuse/scripts/loop.py missing)")
                for entry in impl_by_repo.get(repo_slug, []):
                    feature_status[entry["id"]] = "loop_missing"
                continue

            for entry in sorted(impl_by_repo.get(repo_slug, []), key=lambda e: e["id"]):
                fid = entry["id"]
                wt_path, wt_status = feature_worktree(repos_root, repo_slug, correlation_id, fid)
                if wt_path is None:
                    feature_status[fid] = wt_status or "not_adopted"
                    print(f"[skip] {correlation_id}/{fid}: {wt_status} in {repo_slug}")
                    continue
                feature_dir = find_adopted_dir(wt_path, correlation_id, fid)
                if feature_dir is None:
                    print(f"[skip] {correlation_id}/{fid}: branch found but no "
                          f".specfuse/features/{correlation_id}-{fid}-* dir in worktree {wt_path}")
                    feature_status[fid] = "not_adopted"
                    continue

                if plan_complete(feature_dir):
                    print(f"[done] {correlation_id}/{fid} — complete (PR opened)")
                    feature_status[fid] = "done"
                    continue
                # all_gates_passed but not yet complete: fall through to run loop once
                # more so on_feature_complete fires (opens PR, writes status: complete).

                # Run the loop for this feature inside its worktree (or main, when wt_status == "main").
                any_ran = True
                rc = run_loop(wt_path, feature_dir.name, args.dry_run)

                if rc == 0:
                    if args.dry_run:
                        feature_status[fid] = "dry_run"
                        # In dry-run, no real grind happens — annotate and continue.
                        continue
                    if plan_complete(feature_dir):
                        print(f"\n[complete] {correlation_id}/{fid} — feature done (PR opened).")
                        feature_status[fid] = "complete_now"
                    elif any_gate_awaiting_review(feature_dir):
                        if args.approve:
                            print(f"\n[approve] Approving gate for {correlation_id}/{fid}:")
                            approve_gate(feature_dir)
                            retry = True
                            break
                        feature_status[fid] = "awaiting_review_now"
                    else:
                        feature_status[fid] = "unclear"

                elif rc == 1:
                    feature_status[fid] = "blocked"

                elif rc == 2:
                    if args.approve:
                        print(f"\n[approve] Arming draft WUs for {correlation_id}/{fid}:")
                        approve_gate(feature_dir)
                        retry = True
                        break
                    feature_status[fid] = "unarmed_now"

                else:
                    sys.stderr.write(f"loop exited {rc} for {fid} — unexpected\n")
                    feature_status[fid] = "loop_error"

        # If --approve triggered a gate approval, skip completion check and re-poll.
        if retry:
            continue

        # 4. Check overall completion + emit the final summary.
        # Backfill feature_status for impl features whose dispatch loop didn't touch them
        # this pass (already done before the pass started, etc.). Then group + report.
        impl_entries = [
            entry for repo_slug in involved_repos
            for entry in impl_by_repo.get(repo_slug, [])
        ]
        for repo_slug in involved_repos:
            for entry in impl_by_repo.get(repo_slug, []):
                fid = entry["id"]
                if fid in feature_status:
                    continue
                wt, wt_status = feature_worktree(repos_root, repo_slug, correlation_id, fid)
                if wt is None:
                    feature_status[fid] = wt_status or "not_adopted"
                    continue
                fdir = find_adopted_dir(wt, correlation_id, fid)
                if fdir is None:
                    feature_status[fid] = "not_adopted"
                elif plan_complete(fdir):
                    feature_status[fid] = "done"
                elif any_gate_awaiting_review(fdir):
                    feature_status[fid] = "awaiting_review"
                else:
                    feature_status[fid] = "pending"

        done_total = sum(1 for s in feature_status.values() if s in ("done", "complete_now"))
        all_impl_done = bool(impl_entries) and done_total == len(impl_entries)
        emit_summary(correlation_id, impl_entries, feature_status, qa_ready,
                     all_impl_done, any_ran)
        return 0


if __name__ == "__main__":
    sys.exit(main())
