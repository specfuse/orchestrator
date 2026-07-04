#!/usr/bin/env python3
"""Orchestrator poller — coordination driver (MVP).

A "dumb driver" in the loop.py tradition: it holds no business logic beyond
reading state, recomputing dependencies, dispatching ready work, and recording
what happened. Per orchestrator-architecture.md §7.2 the poller is a dispatcher,
not a brain; per the architecture addendum §A.10 the loop's dispatch/verify/retry
semantics are the *reference* the poller honors — they decompose across the poller
(this file), PM dependency recomputation (here, automating
agents/pm/skills/dependency-recomputation), and the merge watcher (separate
GitHub Action).

Unit model (docs/naming-convention.md, Model B): the orchestrator coordinates an
INITIATIVE and dispatches each FEATURE to a component repo's loop, which owns the
feature's internal gates and work units. The dispatched unit is the feature
(one GitHub issue labelled `specfuse:feature`); its open/closed state plus its
`state:*` label are the canonical state (architecture §3).

What this MVP does, per pass, for one initiative registry:
  1. Parse the registry frontmatter (feature_graph or legacy task_graph).
  2. Read live GitHub state of every feature issue (state:* label + open/closed),
     matched by the [INIT-YYYY-NNNN/FNN] title prefix across involved_repos.
  3. Dependency recomputation: flip every `state:pending` feature whose
     depends_on targets are all `state:done` to `state:ready`, emitting one
     `task_ready` event per flip. Idempotent under replay; malformed graph state
     escalates rather than clobbers (mirrors the PM skill's correctness bar).
  4. Dispatch: hand each `state:ready` feature to the dispatch backend. The real
     backend (invoke the component-loop on the feature issue) lands with the loop
     GitHub feature-pick (Track B); until then StubDispatch records intent only.
  5. Completion: a feature whose issue is closed or carries `state:done` is
     treated as done (drives the next pass's recomputation).

Explicitly NOT in this MVP (owned elsewhere / later):
  - The actual grind (component-loop; Track B).
  - in_review -> done merge (merge watcher GitHub Action; architecture §10).
  - Spinning detection, wall-clock/token budgets (architecture §6.4).
  - feature_state_changed / feature close on last feature done.

State writers respected: this poller is the single writer of the feature-level
`pending -> ready` transition (acting as the PM agent; source: pm). It does not
perform any transition it does not own.

Invocation:
    specfuse-poller                      # newest INIT-*.md registry, one pass
    specfuse-poller --feature features/INIT-2026-0001.md
    specfuse-poller --dry-run            # no label writes, no events, no dispatch
    specfuse-poller --interval 60        # loop every 60s (Ctrl-C to stop)

Requires: pyyaml (bundled with the specfuse-orchestrator package) and the `gh` CLI authenticated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from specfuse.orchestrator import paths
from specfuse.orchestrator._version import read_agent_version
from specfuse.orchestrator.cli import self_provision_if_stale
from specfuse.orchestrator.validate_event import validate as validate_event
from specfuse.orchestrator.validate_frontmatter import validate as validate_frontmatter_content

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "error: pyyaml required. install: pip install specfuse-orchestrator\n"
    )
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parents[2]

# States that schema-require a `next_step` block per feature-frontmatter.schema.json root allOf.
STATES_REQUIRING_NEXT_STEP = {"planning", "plan_review", "generating", "in_progress", "blocked"}

# State-default next_step blocks used by /initiative-status (mirrored here so the poller, as the
# runtime writer for the two transitions it owns, can satisfy the schema without caller input).
# Mirrors agents/pm/skills/initiative-status/SKILL.md §Inputs catalog. Keep in sync.
NEXT_STEP_DEFAULTS = {
    "planning": {
        "summary": "PM session — run `/feature-decomposition` to draft the feature_graph.",
        "owner": "pm-agent",
    },
    "plan_review": {
        "summary": "Review `features/<INIT>-plan.md`; approve via `/plan-approve` (or request edits).",
        "owner": "human",
        "blocking_on": "human approval of plan",
    },
    "generating": {
        "summary": "PM session — run `/codegen-run` for the involved repos.",
        "owner": "pm-agent",
    },
    "in_progress": {
        "summary": "Re-run `specfuse-runner`; dispatch any ready `qa_*` features via `python3 -m specfuse.orchestrator.qa_dispatcher`.",
        "owner": "runner",
    },
    "blocked": {
        "summary": "Resolve the open `/inbox/` blocker, then `/initiative-status` back to `in_progress`.",
        "owner": "human",
        "blocking_on": "open inbox file (see most recent human_escalation event payload)",
    },
}

TITLE_ID_RE = re.compile(r"\[((?:FEAT|INIT)-\d{4}-\d{4}(?:/F\d{2})?)\]")
SUBID_RE = re.compile(r"^(F\d{2}|T\d{2})$")

STATE_LABELS = {
    "state:pending", "state:ready", "state:in-progress", "state:in-review",
    "state:blocked-spec", "state:blocked-human", "state:done", "state:abandoned",
}


# --------------------------------------------------------------------------- #
# gh helpers
# --------------------------------------------------------------------------- #

def gh_json(args: list[str]) -> object:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def list_feature_issues(repo: str, initiative: str) -> list[dict]:
    """All issues for `initiative` in `repo` that carry either the impl-feature
    pick label (`specfuse:feature`) or the QA-feature pick label
    (`specfuse:qa-feature`). Returned deduped by issue number so the poller can
    project state for both impl and QA features in one pass.
    """
    out: dict[int, dict] = {}
    for label in ("specfuse:feature", "specfuse:qa-feature"):
        data = gh_json([
            "issue", "list", "--repo", repo, "--state", "all",
            "--label", label, "--search", initiative,
            "--json", "number,title,state,labels", "--limit", "200",
        ]) or []
        for issue in data:
            out[issue["number"]] = issue
    return list(out.values())


# --------------------------------------------------------------------------- #
# registry model
# --------------------------------------------------------------------------- #

@dataclass
class Feature:
    fid: str                      # e.g. "F06"
    ftype: str
    depends_on: list[str]
    assigned_repo: str
    # filled from GitHub:
    issue_number: int | None = None
    issue_repo: str | None = None
    gh_state: str | None = None   # OPEN / CLOSED
    state_label: str | None = None  # state:ready ...
    autonomy_label: str | None = None  # autonomy:review ...


@dataclass
class Initiative:
    correlation_id: str
    involved_repos: list[str]
    autonomy_default: str
    state: str = ""               # frontmatter feature/initiative state
    features: dict[str, Feature] = field(default_factory=dict)
    registry_path: Path | None = None


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: no frontmatter block")
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end])


def load_initiative(path: Path) -> Initiative:
    fm = parse_frontmatter(path)
    graph = fm.get("feature_graph") or fm.get("task_graph") or []
    init = Initiative(
        correlation_id=fm["correlation_id"],
        involved_repos=fm.get("involved_repos", []),
        autonomy_default=fm.get("autonomy_default", "review"),
        state=fm.get("state", ""),
        registry_path=path,
    )
    for entry in graph:
        f = Feature(
            fid=entry["id"],
            ftype=entry["type"],
            depends_on=list(entry.get("depends_on", [])),
            assigned_repo=entry["assigned_repo"],
        )
        init.features[f.fid] = f
    return init


def hydrate_from_github(init: Initiative) -> None:
    """Match each feature to its issue and read live state."""
    by_id: dict[str, dict] = {}
    for repo in init.involved_repos:
        for issue in list_feature_issues(repo, init.correlation_id):
            m = TITLE_ID_RE.search(issue["title"])
            if not m:
                continue
            cid = m.group(1)  # INIT-2026-0001/F06
            if "/" not in cid:
                continue
            fid = cid.split("/", 1)[1]
            issue["_repo"] = repo
            by_id[fid] = issue
    for fid, feat in init.features.items():
        issue = by_id.get(fid)
        if not issue:
            continue
        feat.issue_number = issue["number"]
        feat.issue_repo = issue["_repo"]
        feat.gh_state = issue["state"].upper()
        labels = {lbl["name"] for lbl in issue.get("labels", [])}
        state = labels & STATE_LABELS
        feat.state_label = next(iter(state)) if state else None
        auton = {lbl for lbl in labels if lbl.startswith("autonomy:")}
        feat.autonomy_label = next(iter(auton)) if auton else None


# --------------------------------------------------------------------------- #
# state helpers
# --------------------------------------------------------------------------- #

def is_done(feat: Feature) -> bool:
    return feat.state_label == "state:done" or feat.gh_state == "CLOSED"


def feature_autonomy(init: Initiative, feat: Feature) -> str:
    """Effective autonomy level for a feature (label overrides feature default)."""
    if feat.autonomy_label:
        return feat.autonomy_label.split(":", 1)[1]
    return init.autonomy_default


def read_event_log(init: Initiative) -> list[dict]:
    log = paths.state_root() / "events" / f"{init.correlation_id}.jsonl"
    if not log.is_file():
        return []
    out = []
    for line in log.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def current_initiative_state(init: Initiative) -> str:
    """Authoritative state: the last initiative-level feature_state_changed in the
    log, else the registry frontmatter value."""
    last = init.state
    for ev in read_event_log(init):
        if (ev.get("event_type") == "feature_state_changed"
                and ev.get("correlation_id") == init.correlation_id):
            to = ev.get("payload", {}).get("to_state")
            if to:
                last = to
    return last


FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)


def _today_iso() -> str:
    return dt.date.today().isoformat()


def _default_next_step(to_state: str) -> dict:
    """State-default next_step block for the transitions this poller owns.

    The PM skill catalog (initiative-status SKILL §Inputs) is the source of
    record; this function mirrors it so the runtime can satisfy the schema
    without caller input. Always stamps `updated` to today.
    """
    base = NEXT_STEP_DEFAULTS.get(to_state)
    if not base:
        raise RuntimeError(f"no default next_step for to_state={to_state!r}")
    return {**base, "updated": _today_iso()}


def _validate_frontmatter(path: Path) -> None:
    errors = validate_frontmatter_content(path)
    if errors:
        raise RuntimeError(
            f"frontmatter validation failed for {path.name}: " + "\n".join(errors)
        )


def _yaml_dump_block(data: dict) -> str:
    """Dump a next_step block as YAML with the `updated` field force-quoted (else
    PyYAML emits an unquoted date that re-parses as a date object and fails the
    JSON-schema string type check)."""
    out_lines = ["next_step:"]
    for key in ("summary", "owner", "owner_repo", "blocking_on", "updated"):
        if key not in data:
            continue
        val = data[key]
        if key == "updated":
            out_lines.append(f'  updated: "{val}"')
        else:
            # double-quote summaries / blocking_on (may contain colons, backticks)
            escaped = str(val).replace("\\", "\\\\").replace('"', '\\"')
            out_lines.append(f'  {key}: "{escaped}"')
    return "\n".join(out_lines) + "\n"


def _rewrite_registry(path: Path, new_state: str, next_step: dict | None) -> None:
    """Rewrite the registry frontmatter with the new state and next_step block.

    Preserves field ordering by editing in place: rewrites the `state:` line,
    then strips any existing `next_step:` block, then inserts the new block
    (or omits it for terminal/pre-planning transitions).
    """
    text = path.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise RuntimeError(f"no YAML frontmatter found in {path.name}")
    fm = m.group(1)

    # 1. state line
    if not re.search(r"^state: .*$", fm, flags=re.MULTILINE):
        raise RuntimeError(f"registry state line not found in {path.name}")
    new_fm = re.sub(r"^state: .*$", f"state: {new_state}", fm, count=1, flags=re.MULTILINE)

    # 2. strip any existing next_step block (next_step: followed by indented lines)
    new_fm = re.sub(
        r"^next_step:\n(?:[ \t]+.*\n)*",
        "",
        new_fm,
        count=1,
        flags=re.MULTILINE,
    )

    # 3. insert new block before feature_graph: (or task_graph:) if required
    if next_step is not None:
        block = _yaml_dump_block(next_step)
        anchor = re.search(r"^(feature_graph|task_graph):", new_fm, flags=re.MULTILINE)
        if not anchor:
            # no graph field: append at end of frontmatter
            new_fm = new_fm.rstrip("\n") + "\n" + block
        else:
            new_fm = new_fm[:anchor.start()] + block + new_fm[anchor.start():]

    path.write_text("---\n" + new_fm + "---\n" + text[m.end():])


# Roadmap section markers.
def ROADMAP_HEADING_RE(cid):
    return re.compile(rf"^## {re.escape(cid)}\b.*$", re.MULTILINE)


def _project_next_step_to_roadmap(correlation_id: str, next_step: dict | None) -> None:
    """Rewrite the `**Next step.** / **Owner.** / **Blocking on.** / **Updated.**`
    block in the matching roadmap section.

    Block lives immediately after the section's `**State: ...**` paragraph.
    A `## Notes` heading or the next `## ` heading bounds the section. When
    `next_step` is None (terminal/pre-planning), the existing block is stripped.
    Registry → roadmap projection; never the reverse.
    """
    roadmap_path = paths.state_root() / "roadmap.md"
    if not roadmap_path.is_file():
        return  # roadmap optional; skip silently
    text = roadmap_path.read_text()
    heading = ROADMAP_HEADING_RE(correlation_id).search(text)
    if not heading:
        print(f"    WARN roadmap: no `## {correlation_id}` section — skipping projection")
        return
    # find section bounds: from heading line to next `## ` (or EOF)
    sec_start = heading.start()
    next_h = re.search(r"^## ", text[heading.end():], flags=re.MULTILINE)
    sec_end = heading.end() + next_h.start() if next_h else len(text)
    section = text[sec_start:sec_end]

    # Bound stripping to just the four labelled paragraphs (don't eat unrelated trailing prose).
    stripped = re.sub(
        r"\n\n\*\*Next step\.\*\*[^\n]*"
        r"(?:\n\n\*\*Owner\.\*\*[^\n]*)?"
        r"(?:\n\n\*\*Blocking on\.\*\*[^\n]*)?"
        r"(?:\n\n\*\*Updated\.\*\*[^\n]*)?",
        "",
        section,
        count=1,
    )

    if next_step is None:
        new_section = stripped
    else:
        owner = next_step["owner"]
        owner_str = f"`{owner}`"
        if "owner_repo" in next_step:
            owner_str += f" — repo `{next_step['owner_repo']}`"
        parts = [
            "",
            f"**Next step.** {next_step['summary']}",
            "",
            f"**Owner.** {owner_str}",
        ]
        if "blocking_on" in next_step:
            parts += ["", f"**Blocking on.** {next_step['blocking_on']}"]
        parts += ["", f"**Updated.** {next_step['updated']}"]
        block = "\n".join(parts)
        # Insert after the section's `**State: ...**` paragraph (matches up to next blank line).
        state_para = re.search(r"\*\*State:[^\n]*(?:\n[^\n]+)*", stripped)
        if state_para:
            insert_at = state_para.end()
            new_section = stripped[:insert_at] + block + stripped[insert_at:]
        else:
            # no **State:** paragraph — append after heading line
            after_heading = stripped.find("\n") + 1
            new_section = stripped[:after_heading] + block.lstrip("\n") + "\n" + stripped[after_heading:]

    if new_section != section:
        roadmap_path.write_text(text[:sec_start] + new_section + text[sec_end:])
        print(f"    roadmap: projected next_step to `## {correlation_id}` section")


def update_registry_state(init: Initiative, old: str, new: str, dry_run: bool,
                          next_step: dict | None) -> None:
    if dry_run:
        print(f"    [dry-run] would set registry state: {old} -> {new}"
              + (f" + write next_step (owner={next_step['owner']})" if next_step else " + strip next_step"))
        return
    path = init.registry_path
    _rewrite_registry(path, new, next_step)
    _validate_frontmatter(path)
    init.state = new
    msg = f"    registry state: {old} -> {new}"
    if next_step:
        msg += f" + next_step (owner={next_step['owner']}, updated={next_step['updated']})"
    elif new in {"done", "abandoned", "drafting", "validating"}:
        msg += " + stripped next_step"
    print(msg)
    _project_next_step_to_roadmap(init.correlation_id, next_step)


def transition_initiative(init: Initiative, frm: str, to: str, trigger: str,
                          dry_run: bool, version: str) -> None:
    # Compute next_step for the target state: required mid-lifecycle, stripped at terminal.
    next_step = _default_next_step(to) if to in STATES_REQUIRING_NEXT_STEP else None
    update_registry_state(init, frm, to, dry_run, next_step)
    payload = {"from_state": frm, "to_state": to, "trigger": trigger}
    if next_step is not None:
        payload["next_step"] = next_step
    emit_event(init, event_skeleton(
        init.correlation_id, "feature_state_changed", "pm", version, payload,
    ), dry_run)


def event_skeleton(correlation_id: str, event_type: str, source: str,
                   source_version: str, payload: dict) -> dict:
    return {
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlation_id": correlation_id,
        "event_type": event_type,
        "source": source,
        "source_version": source_version,
        "payload": payload,
    }


def pm_version() -> str:
    try:
        return read_agent_version(REPO_ROOT, "pm")
    except (FileNotFoundError, ValueError):
        return "n/a"


def emit_event(init: Initiative, event: dict, dry_run: bool) -> None:
    """Validate via validate_event.validate(), then append to the event log."""
    if dry_run:
        print(f"    [dry-run] would emit {event['event_type']} {event['correlation_id']}")
        return
    line = json.dumps(event)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        tf.write(line + "\n")
        tmp = tf.name
    errors = validate_event(tmp)
    if errors:
        raise RuntimeError("event failed validation, not appended: " + "\n".join(errors))
    log = paths.state_root() / "events" / f"{init.correlation_id}.jsonl"
    with log.open("a") as fh:
        fh.write(line + "\n")
    print(f"    emitted {event['event_type']} {event['correlation_id']}")


def set_state_label(feat: Feature, new_state: str, dry_run: bool) -> None:
    assert feat.issue_repo and feat.issue_number
    if dry_run:
        print(f"    [dry-run] would set {feat.issue_repo}#{feat.issue_number} "
              f"{feat.state_label} -> {new_state}")
        return
    args = ["issue", "edit", str(feat.issue_number), "--repo", feat.issue_repo,
            "--add-label", new_state]
    if feat.state_label:
        args += ["--remove-label", feat.state_label]
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"label flip failed: {proc.stderr.strip()}")
    print(f"    {feat.issue_repo}#{feat.issue_number} {feat.state_label} -> {new_state}")
    feat.state_label = new_state


# --------------------------------------------------------------------------- #
# dispatch backend (seam — real impl lands with loop GitHub feature-pick, Track B)
# --------------------------------------------------------------------------- #

def executor_for(feat: Feature) -> str:
    """Dispatch routing by feature type (docs/naming-convention.md §"Dispatch by feature type",
    resolved 2026-06-06): implementation features go to the component repo's LOOP (single-repo
    grind via the loop GitHub feature-pick); qa_* features go to the QA AGENT (a distinct
    cross-repo role — the loop is single-repo + edit-and-commit, QA is cross-repo and
    edit-free for execution). QA is the deliberate exception to uniform-loop dispatch."""
    return "qa-agent" if feat.ftype.startswith("qa_") else "component-loop"


class DispatchBackend:
    """Hands a ready feature to its execution surface, routed by `executor_for(feat)`:
    implementation features -> a component-repo loop (arrives with the loop GitHub feature-pick,
    Track B); qa_* features -> the QA agent (cross-repo; not a loop). Subclass and implement
    `dispatch`."""

    def dispatch(self, init: Initiative, feat: Feature, dry_run: bool) -> None:
        raise NotImplementedError


class StubDispatch(DispatchBackend):
    """Records intent only. No grind is started."""

    def dispatch(self, init: Initiative, feat: Feature, dry_run: bool) -> None:
        target = executor_for(feat)
        pending = ("loop adopt not invoked (stub)" if target == "component-loop"
                   else "handled by specfuse.orchestrator.qa_dispatcher")
        print(f"    [stub] ready to dispatch {init.correlation_id}/{feat.fid} ({feat.ftype}) "
              f"-> {target} @ {feat.assigned_repo} (#{feat.issue_number}); {pending}")


class LoopDispatch(DispatchBackend):
    """Real dispatch (Track B delivered the loop side). For an `implementation` feature it ADOPTS
    the feature into its component repo's loop (`adopt_feature.py <slug> <issue#>` → a runnable
    feature folder seeded from the issue body). QA features are not loop-dispatchable (→ QA agent;
    not wired). Idempotent: skips a feature whose loop feature-folder already exists.

    SCOPE (MVP): adopt only. The grind RUN (`loop.py`, which honors autonomy at gate-arm
    checkpoints) is the next increment and MUST take a per-repo driver lock first — the
    concurrent-driver scar (two drivers racing corrupted gate state) makes that lock mandatory
    before any auto-run is wired here.
    """

    def __init__(self, repos_root: Path):
        self.repos_root = repos_root

    def _checkout(self, slug: str) -> Path:
        return self.repos_root / slug.split("/")[-1]

    def dispatch(self, init: Initiative, feat: Feature, dry_run: bool) -> None:
        if executor_for(feat) != "component-loop":
            print(f"    [skip] {init.correlation_id}/{feat.fid} ({feat.ftype}) -> qa-agent: "
                  f"not loop-dispatchable; handled by specfuse.orchestrator.qa_dispatcher")
            return
        slug = feat.issue_repo or feat.assigned_repo
        path = self._checkout(slug)
        adopt = path / ".specfuse" / "scripts" / "adopt_feature.py"
        if not adopt.is_file():
            print(f"    [skip] {init.correlation_id}/{feat.fid}: loop not installed at {path} "
                  f"(.specfuse/scripts/adopt_feature.py missing — run loop init.sh there)")
            return
        feats_dir = path / ".specfuse" / "features"
        prefix = f"{init.correlation_id}-{feat.fid}"  # loop encodes INIT-…/FNN -> INIT-…-FNN-<slug>
        if feats_dir.is_dir() and any(d.name.startswith(prefix) for d in feats_dir.iterdir()):
            print(f"    [done] {init.correlation_id}/{feat.fid} already adopted in {path} — skip")
            return
        if dry_run:
            print(f"    [dry] would adopt {slug}#{feat.issue_number} into loop @ {path}")
            return
        r = subprocess.run(["python3", str(adopt), slug, str(feat.issue_number)],
                           cwd=str(path), capture_output=True, text=True)
        if r.returncode == 0:
            print(f"    adopted {init.correlation_id}/{feat.fid} -> loop @ {path} "
                  f"(status: planned; arm to run)")
        else:
            print(f"    adopt FAILED {init.correlation_id}/{feat.fid}: {r.stderr.strip()}")


# --------------------------------------------------------------------------- #
# the pass
# --------------------------------------------------------------------------- #

def run_pass(init: Initiative, backend: DispatchBackend, dry_run: bool) -> None:
    hydrate_from_github(init)
    version = pm_version()

    # Report current state
    print(f"  {init.correlation_id}: {len(init.features)} features")
    for fid, f in sorted(init.features.items()):
        loc = f"{f.issue_repo}#{f.issue_number}" if f.issue_number else "(no issue)"
        deps = ",".join(f.depends_on) or "-"
        print(f"    {fid} {f.state_label or '?':16} deps={deps:12} {loc}")

    # 1. Dependency recomputation (single-writer pending -> ready)
    print("  recompute:")
    for fid, feat in sorted(init.features.items()):
        if feat.state_label != "state:pending":
            continue
        # malformed-graph guard: every dep must exist
        missing = [d for d in feat.depends_on if d not in init.features]
        if missing:
            print(f"    ESCALATE {fid}: orphan depends_on {missing} (spec_level_blocker)")
            continue
        deps_done = all(is_done(init.features[d]) for d in feat.depends_on)
        if not deps_done:
            continue
        set_state_label(feat, "state:ready", dry_run)
        trigger = "no_dep_creation" if not feat.depends_on else "deps_done"
        emit_event(init, event_skeleton(
            f"{init.correlation_id}/{fid}", "task_ready", "pm", version,
            {"issue": f"{feat.issue_repo}#{feat.issue_number}", "trigger": trigger},
        ), dry_run)

    # 2. Dispatch ready features, gated by autonomy.
    #    supervised -> hold for human "go" (architecture §3); auto/review -> dispatch.
    print("  dispatch:")
    any_ready = False
    for fid, feat in sorted(init.features.items()):
        if feat.state_label != "state:ready":
            continue
        any_ready = True
        level = feature_autonomy(init, feat)
        if level == "supervised":
            print(f"    [hold] {init.correlation_id}/{fid} is supervised — "
                  f"awaiting human go before dispatch (autonomy_requires_approval)")
            continue
        backend.dispatch(init, feat, dry_run)
    if not any_ready:
        print("    (no features in state:ready)")

    # 3. Initiative-level state progression (PM-owned; architecture §6.3).
    print("  initiative:")
    cur = current_initiative_state(init)
    if cur != init.state:
        print(f"    WARN registry/log drift: frontmatter state={init.state!r} but "
              f"event log last feature_state_changed.to_state={cur!r}; trusting the log. "
              f"Reconcile the registry frontmatter (not auto-rewritten — may be intentional).")
    has_issues = any(f.issue_number for f in init.features.values())
    all_done = bool(init.features) and all(is_done(f) for f in init.features.values())
    if cur == "generating" and has_issues:
        # issues are open across component repos => first round dispatched
        transition_initiative(init, "generating", "in_progress",
                              "first_round_issues_opened", dry_run, version)
    elif cur == "in_progress" and all_done:
        transition_initiative(init, "in_progress", "done",
                              "all_features_done", dry_run, version)
    else:
        done_n = sum(1 for f in init.features.values() if is_done(f))
        print(f"    state={cur}; {done_n}/{len(init.features)} features done — no transition")


def find_default_registry() -> Path:
    candidates = sorted((paths.state_root() / "features").glob("INIT-*.md"))
    candidates = [p for p in candidates if not p.name.endswith(("-plan.md", "-issues-dryrun.md"))]
    if not candidates:
        sys.stderr.write("error: no features/INIT-*.md registry found; pass --feature\n")
        sys.exit(2)
    return candidates[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Orchestrator poller (coordination MVP)")
    ap.add_argument("--feature", help="path to an initiative registry .md (default: newest INIT-*.md)")
    ap.add_argument("--dry-run", action="store_true", help="no label writes, no events, no dispatch")
    ap.add_argument("--interval", type=int, default=0, help="loop every N seconds (default: one pass)")
    ap.add_argument("--backend", choices=["loop", "stub"], default="loop",
                    help="dispatch backend: loop = adopt impl features into the component-loop (default); stub = log intent only")
    ap.add_argument("--repos-root", default=None,
                    help="dir holding component-repo checkouts (default: the orchestrator repo's parent)")
    args = ap.parse_args()
    self_provision_if_stale(paths.state_root())
    if args.repos_root is None:
        args.repos_root = str(paths.state_root().parent)

    registry = Path(args.feature) if args.feature else find_default_registry()
    if not registry.is_file():
        sys.stderr.write(f"error: registry not found: {registry}\n")
        return 2

    backend: DispatchBackend = (LoopDispatch(Path(args.repos_root)) if args.backend == "loop"
                                else StubDispatch())

    def one() -> None:
        init = load_initiative(registry)
        print(f"poller pass @ {dt.datetime.now(dt.timezone.utc).isoformat()} "
              f"({registry.name}){' [dry-run]' if args.dry_run else ''}")
        run_pass(init, backend, args.dry_run)

    if args.interval > 0:
        print(f"polling {registry.name} every {args.interval}s — Ctrl-C to stop")
        while True:
            try:
                one()
            except Exception as e:  # noqa: BLE001 — driver keeps polling on transient errors
                sys.stderr.write(f"pass error: {e}\n")
            time.sleep(args.interval)
    else:
        one()
    return 0


if __name__ == "__main__":
    sys.exit(main())
