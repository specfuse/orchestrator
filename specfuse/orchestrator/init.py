#!/usr/bin/env python3
"""Orchestrator init — scaffold the orchestrator-owned + shared-core (frozen) substrate into
a COMPONENT or SPECS repo, driven by shared/distribution/ownership-manifest.yaml.

Per-repo, ships the `orchestrator-init` + `manual`-stub entries (the orchestrator's frozen
substrate); the manifest's one-upgrader-per-slot invariant lets it overlay the same repo as
loop's init.sh without clobbering. In **--all** mode it also invokes the loop repo's `init.sh`
to install the loop kit into each component (the gate cycle is proven), so `--all` deploys
everything to every known repo.

Overlay semantics (loop init.sh tradition): managed files are overwritten with the canonical
copy; everything else in the target is preserved. `manual` stubs are seeded only if absent.
Re-running is an in-place upgrade. Use --dry-run to preview.

    python3 -m specfuse.orchestrator.init --target component /path/to/component-repo
    python3 -m specfuse.orchestrator.init --target specs     /path/to/specs-repo --dry-run
    python3 -m specfuse.orchestrator.init --all --dry-run     # every known repo (loop kit + substrate)
    python3 -m specfuse.orchestrator.init --all               # deploy everything (init; refuses where already installed)
    python3 -m specfuse.orchestrator.init --all --upgrade     # overlay an existing deploy (passes --upgrade to loop init too)

`--all` discovers component repos from `project/repos/*.md` (their `**Repo:**` slug) + the product
specs repo, resolves each checkout under `--repos-root` (default: the orchestrator's parent), and
for each component runs loop `init.sh` (from `--loop-root`) then the substrate install; specs gets
the substrate only.

Requires pyyaml (bundled with the specfuse-orchestrator package); `gh` for label-sync; `bash` + the loop checkout for --all.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("error: pyyaml required (pip install specfuse-orchestrator)\n")
    sys.exit(2)

from specfuse.orchestrator import paths

MANIFEST = paths.substrate("distribution", "ownership-manifest.yaml")
# orchestrator-init ships the orchestrator's frozen substrate + manual stubs, AND the
# core-methodology (`methodology` upgrader) entries — the shared substrate the orchestrator
# vendors from specfuse/methodology and re-ships to component/specs repos (Track C2).
SHIP_UPGRADERS = {"orchestrator-init", "manual", "methodology"}


def _resolve_source(cs: dict) -> Path:
    """Filesystem path to an entry's source inside the packaged substrate.

    The wheel ships the substrate under `specfuse/orchestrator/_substrate/` (a build-time
    mirror of `shared/`), resolved via `paths.substrate()`. Entry `canonical_source.path`
    values are repo-relative, so strip the leading `shared/` prefix.

    Core-methodology entries declare `repo: specfuse, path: methodology/...` — their
    canonical home is the specfuse/methodology core, but the orchestrator vendors that
    substrate into its own `shared/` tree (rules → shared/rules, schemas → shared/schemas,
    the gate-cycle doc → shared/docs). Remap those onto the local vendored copy so init can
    ship them without a checkout of the core repo.
    """
    path = cs["path"]
    if cs.get("repo") == "specfuse":
        if path.startswith("methodology/rules/"):
            rel = "rules/" + path[len("methodology/rules/"):]
        elif path.startswith("methodology/schemas/"):
            rel = "schemas/" + path[len("methodology/schemas/"):]
        elif path in ("methodology/methodology.md", "methodology/glossary.md"):
            rel = "docs/" + path[len("methodology/"):]
        else:
            rel = path[len("methodology/"):]
    else:
        rel = path[len("shared/"):] if path.startswith("shared/") else path
    return paths.substrate(*rel.split("/"))

# Stub content seeded for `manual` entries, keyed by entry id.
MANUAL_STUBS = {
    "codegen-coverage-declaration": """\
# .specfuse/templates.yaml — this component's codegen template-coverage declaration.
# Read by the PM template-coverage-check skill at plan time. List the generator template
# tokens this repo can satisfy. Seeded as a stub by orchestrator-init; fill it in.
templates: []
""",
}


def log(msg: str) -> None:
    print(msg)


# --------------------------------------------------------------------------- #
# copy helpers (overlay; preserve extras)
# --------------------------------------------------------------------------- #

def copy_file(src: Path, dst: Path, dry: bool) -> None:
    verb = "update" if dst.exists() else "add"
    if dry:
        log(f"    would {verb}: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"    {verb}: {dst}")


def copy_tree(src: Path, dst: Path, dry: bool, exclude: set[str]) -> None:
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        # prune excluded top-level names
        if rel == Path("."):
            dirs[:] = [d for d in dirs if d not in exclude]
            files = [f for f in files if f not in exclude]
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for f in files:
            copy_file(Path(root) / f, dst / rel / f, dry)


def install_entry(entry: dict, install: dict, dry: bool) -> None:
    cs = entry["canonical_source"]
    src = _resolve_source(cs)
    dst = Path(install["_target_repo"]) / install["path"]

    if entry["upgrader"] == "manual":
        stub = MANUAL_STUBS.get(entry["id"])
        if stub is None:
            log(f"    skip {entry['id']}: manual entry without a known stub")
            return
        if dst.exists():
            log(f"    preserve: {dst} (manual stub already present)")
            return
        if dry:
            log(f"    would seed stub: {dst}")
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(stub)
        log(f"    seed stub: {dst}")
        return

    if not src.exists():
        log(f"    MISSING source {src} for {entry['id']} — skipped")
        return

    if src.is_file():
        copy_file(src, dst, dry)
    elif "files" in cs:
        for name in cs["files"]:
            copy_file(src / name, dst / name, dry)
    else:
        copy_tree(src, dst, dry, set(cs.get("exclude", [])))


# --------------------------------------------------------------------------- #
# Claude Code wiring
# --------------------------------------------------------------------------- #

MARKER = "## Specfuse binding context"


def wire_claude(target_repo: Path, rule_paths: list[str], target: str, dry: bool) -> None:
    """Bridge the `.specfuse/` config tree into `.claude/` (loop wire_claude_code pattern):
    @import the binding rules + the role's CLAUDE.md, and symlink the role's skills into
    .claude/skills/. `.specfuse/` is the single config home; `.claude/` holds only bridges."""
    claude = target_repo / ".claude"
    md = claude / "CLAUDE.md"
    role = target  # component | specs
    role_md_rel = f".specfuse/agents/{role}/CLAUDE.md"
    role_skills = target_repo / ".specfuse" / "agents" / role / "skills"

    # 1. @import block: binding rules (if any installed locally) + the role config.
    imports = [f"@{p}" for p in sorted(rule_paths)]
    if dry or (target_repo / role_md_rel).exists():
        imports.append(f"@{role_md_rel}")
    if imports:
        block = MARKER + " (read before any work-unit dispatch)\n" + "\n".join(imports)
        if not md.exists():
            if dry:
                log(f"    would create {md} with the @import block")
            else:
                claude.mkdir(parents=True, exist_ok=True)
                md.write_text(f"# Project notes\n\n{block}\n")
                log(f"    created {md} with @import block")
        elif MARKER in md.read_text():
            log(f"    {md} already has the @import block — left alone")
        else:
            log(f"    {md} exists without the @import block — append:")
            for line in block.splitlines():
                log(f"      {line}")
    else:
        log("    nothing to @import for this target")

    # 2. role skill symlinks: .specfuse/agents/<role>/skills/* -> .claude/skills/
    #    (settings.json allowlists for the executable kit are loop-init's concern.)
    if role_skills.is_dir() or dry:
        skills_dir = claude / "skills"
        existing = sorted(role_skills.iterdir()) if role_skills.is_dir() else []
        for d in existing:
            if not d.is_dir():
                continue
            link = skills_dir / d.name
            rel = os.path.relpath(d, skills_dir)
            if link.exists() or link.is_symlink():
                log(f"    skill link {link.name} present — left alone")
            elif dry:
                log(f"    would link .claude/skills/{d.name} -> {rel}")
            else:
                skills_dir.mkdir(parents=True, exist_ok=True)
                link.symlink_to(rel)
                log(f"    linked .claude/skills/{d.name} -> {rel}")


GITIGNORE_PATTERNS = [".specfuse/state/", ".specfuse/.scratch-logs/"]
GITIGNORE_HEADER = "# Specfuse runtime (generated by loop/orchestrator — not tracked)"


def ensure_gitignore(target_repo: Path, dry: bool) -> None:
    """Ensure the target .gitignore ignores the specfuse runtime dirs (state, scratch-logs).
    Idempotent: only missing patterns are appended; .specfuse/ itself stays tracked."""
    gi = target_repo / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    present = {ln.strip() for ln in text.splitlines()}
    missing = [p for p in GITIGNORE_PATTERNS if p not in present]
    if not missing:
        log("    .gitignore already ignores the specfuse runtime dirs")
        return
    if dry:
        for p in missing:
            log(f"    would add to .gitignore: {p}")
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + GITIGNORE_HEADER + "\n" + "\n".join(missing) + "\n"
    gi.write_text(text)
    log(f"    .gitignore: added {', '.join(missing)}")


def repo_slug(target_repo: Path) -> str | None:
    """owner/repo from the target's `origin` remote (network-free), else None."""
    r = subprocess.run(["git", "-C", str(target_repo), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", r.stdout.strip())
    return m.group(1) if m else None


def sync_labels(doc: dict, target_repo: Path, target: str, dry: bool) -> None:
    """Create the manifest's non-templated labels for this target on the target's GitHub repo
    (idempotent via `gh label create --force`). Templated labels (per-initiative) are skipped."""
    wanted = [lbl for lbl in doc.get("labels", [])
              if target in lbl.get("targets", []) and not lbl.get("templated")]
    skipped = [lbl["name"] for lbl in doc.get("labels", [])
               if target in lbl.get("targets", []) and lbl.get("templated")]
    if not wanted and not skipped:
        return
    slug = repo_slug(target_repo)
    if not slug:
        log("    label-sync skipped — no owner/repo resolvable from the origin remote")
        return
    for lbl in wanted:
        if dry:
            log(f"    would ensure label {lbl['name']} on {slug}")
            continue
        r = subprocess.run(
            ["gh", "label", "create", lbl["name"], "--repo", slug,
             "--color", lbl.get("color", "ededed"),
             "--description", lbl.get("description", ""), "--force"],
            capture_output=True, text=True)
        if r.returncode == 0:
            log(f"    ensured label {lbl['name']} on {slug}")
        else:
            log(f"    label {lbl['name']} FAILED on {slug}: {r.stderr.strip()}")
    for name in skipped:
        log(f"    templated label {name} — create per-initiative (not synced here)")


def gitignore_guard(target_repo: Path) -> None:
    try:
        r = subprocess.run(["git", "-C", str(target_repo), "check-ignore", "-q", ".specfuse"],
                           capture_output=True)
        if r.returncode == 0:
            log("  WARNING: .specfuse/ is gitignored in the target — orchestrator config and "
                "event/state writes will be invisible to git. Un-ignore .specfuse/.")
    except Exception:
        pass


# --------------------------------------------------------------------------- #

def install_into(target: str, target_repo: Path, doc: dict, upgrade: bool, dry: bool) -> None:
    """Scaffold the orchestrator substrate for one target repo (the per-repo install).
    Default (init) refuses if the substrate is already present (the role config exists) and points
    at --upgrade — mirroring loop init.sh. --upgrade overlays in place (managed files overwritten,
    extras preserved)."""
    role_config = target_repo / ".specfuse" / "agents" / target / "CLAUDE.md"
    if role_config.exists() and not upgrade:
        log(f"orchestrator-init {target} {target_repo}: substrate already present "
            f"({role_config.relative_to(target_repo)}) — re-run with --upgrade to overlay. Skipping.")
        return
    log(f"orchestrator-init --target {target} {target_repo}"
        f"{' --upgrade' if upgrade else ''}{' [dry-run]' if dry else ''}")
    rule_paths: list[str] = []
    log("  install:")
    for entry in doc["entries"]:
        if entry["upgrader"] not in SHIP_UPGRADERS:
            continue
        for install in entry.get("install", []):
            if install["target"] != target:
                continue
            install = {**install, "_target_repo": str(target_repo)}
            install_entry(entry, install, dry)
            if entry["category"] == "shared-core" and install["path"].startswith(".specfuse/rules/"):
                rule_paths.append(install["path"])
    log("  claude wiring:")
    wire_claude(target_repo, rule_paths, target, dry)
    log("  gitignore:")
    ensure_gitignore(target_repo, dry)
    if not dry:
        gitignore_guard(target_repo)
    log("  labels:")
    sync_labels(doc, target_repo, target, dry)


def discover_repos(state_root: Path) -> list[tuple[str, str]]:
    """[(target, owner/repo)] from <state_root>/project/repos/*.md (components) + the product specs repo.

    The repo list lives in the orchestration STATE repo (project/, features/), not in the
    installed package — so it is resolved from `state_root`, not the package dir.
    """
    out: list[tuple[str, str]] = []
    repos_dir = state_root / "project" / "repos"
    for f in sorted(repos_dir.glob("*.md")):
        m = re.search(r"\*\*Repo:\*\*\s*`([^`]+)`", f.read_text())
        if m:
            out.append(("component", m.group(1)))
    out.append(("specs", "acme/specs-sample"))
    return out


def run_loop_init(loop_root: Path, checkout: Path, upgrade: bool, dry: bool) -> None:
    """Install/upgrade the loop kit into a component checkout via the loop repo's init.sh.
    `upgrade` is passed through as loop's `--upgrade` (loop init refuses an init over an existing
    .specfuse/ and points at --upgrade — same contract on both sides)."""
    init = loop_root / "init.sh"
    if not init.is_file():
        log(f"  loop init.sh not found at {init} — skip loop kit (set --loop-root)")
        return
    mode = ["--upgrade"] if upgrade else []
    if dry:
        log(f"  [dry] would run loop init.sh {' '.join(mode)} {checkout}".rstrip())
        return
    r = subprocess.run(["bash", str(init), *mode, str(checkout)], capture_output=True, text=True)
    print((r.stdout or "").rstrip())
    if r.returncode != 0:
        sys.stderr.write(f"  loop init.sh failed for {checkout}: {r.stderr.strip()}\n")
    else:
        log(f"  loop kit installed in {checkout}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Orchestrator init — scaffold the substrate (+ loop kit) into target repos via the ownership manifest")
    ap.add_argument("--target", choices=["component", "specs"], help="single-repo mode: target kind")
    ap.add_argument("target_repo", nargs="?", help="single-repo mode: path to the target repo")
    ap.add_argument("--all", action="store_true",
                    help="deploy to every known repo (components from project/repos/ + the specs repo); installs the loop kit into components too")
    ap.add_argument("--repos-root", default=None,
                    help="dir holding the sibling repo checkouts (default: the orchestration repo's parent)")
    ap.add_argument("--loop-root", default=None,
                    help="path to the specfuse/loop checkout (default: <orchestration-repo-parent>/loop)")
    ap.add_argument("--upgrade", action="store_true",
                    help="upgrade mode: overlay an existing install (default refuses if already present), and pass --upgrade to loop init.sh")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    doc = yaml.safe_load(MANIFEST.read_text())

    if args.all:
        # --all reads the repo list from the orchestration STATE repo and deploys to sibling
        # checkouts; resolve those roots from state_root() unless explicitly overridden.
        try:
            sroot = paths.state_root()
        except RuntimeError as e:
            sys.stderr.write(f"error: --all must run from the orchestration repo: {e}\n")
            return 2
        repos_root = Path(args.repos_root) if args.repos_root else sroot.parent
        loop_root = Path(args.loop_root) if args.loop_root else sroot.parent / "loop"
        log(f"orchestrator-init --all{' [dry-run]' if args.dry_run else ''}  "
            f"(repos-root={repos_root}, loop-root={loop_root})")
        for target, slug in discover_repos(sroot):
            checkout = repos_root / slug.split("/")[-1]
            log(f"\n=== {slug}  [{target}] -> {checkout} ===")
            if not checkout.is_dir():
                log(f"  SKIP — checkout not found at {checkout}")
                continue
            if target == "component":
                run_loop_init(loop_root, checkout, args.upgrade, args.dry_run)  # loop kit first
            install_into(target, checkout, doc, args.upgrade, args.dry_run)
        log("\nall done.")
        return 0

    if not args.target or not args.target_repo:
        sys.stderr.write("error: pass --all, or --target <component|specs> <repo-path>\n")
        return 2
    target_repo = Path(args.target_repo).resolve()
    if not target_repo.is_dir():
        sys.stderr.write(f"error: target repo not a directory: {target_repo}\n")
        return 2
    install_into(args.target, target_repo, doc, args.upgrade, args.dry_run)
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
