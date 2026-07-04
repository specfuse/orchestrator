#!/usr/bin/env python3
"""Validate shared/distribution/ownership-manifest.yaml.

Checks the vocabulary, required fields, and the load-bearing invariants:
  - every (target, install path) slot is written by exactly one upgrader;
  - no slot is claimed by two entries (one source per slot);
  - orchestrator-init ships only `stable` entries (charter §4).

Exit 0 = valid; 1 = violations; 2 = setup error.
"""
from __future__ import annotations
import sys

from specfuse.orchestrator import paths

try:
    import yaml
except ImportError:
    sys.stderr.write("error: pyyaml required (pip install specfuse-orchestrator)\n")
    sys.exit(2)


def main() -> int:
    MANIFEST = paths.substrate("distribution", "ownership-manifest.yaml")
    if not MANIFEST.is_file():
        sys.stderr.write(f"error: manifest not found at {MANIFEST}\n")
        return 2
    doc = yaml.safe_load(MANIFEST.read_text())

    categories = set(doc["categories"])
    authorities = set(doc["authorities"])
    stabilities = set(doc["stabilities"])
    upgraders = set(doc["upgraders"])
    targets = set(doc["targets"])

    errors: list[str] = []
    slot_upgraders: dict[tuple[str, str], set[str]] = {}
    slot_entries: dict[tuple[str, str], list[str]] = {}

    for e in doc["entries"]:
        eid = e.get("id", "<no-id>")
        for fld in ("id", "category", "canonical_source", "authority", "stability", "upgrader", "install"):
            if fld not in e:
                errors.append(f"{eid}: missing field `{fld}`")
        if e.get("category") not in categories:
            errors.append(f"{eid}: bad category {e.get('category')!r}")
        if e.get("authority") not in authorities:
            errors.append(f"{eid}: bad authority {e.get('authority')!r}")
        if e.get("stability") not in stabilities:
            errors.append(f"{eid}: bad stability {e.get('stability')!r}")
        if e.get("upgrader") not in upgraders:
            errors.append(f"{eid}: bad upgrader {e.get('upgrader')!r}")
        cs = e.get("canonical_source", {})
        if cs.get("repo") not in {"orchestrator", "loop"}:
            errors.append(f"{eid}: canonical_source.repo must be orchestrator|loop, got {cs.get('repo')!r}")
        # charter §4: orchestrator-init ships only stable
        if e.get("upgrader") == "orchestrator-init" and e.get("stability") != "stable":
            errors.append(f"{eid}: upgrader orchestrator-init requires stability=stable (charter §4)")
        for inst in e.get("install", []):
            if inst.get("target") not in targets:
                errors.append(f"{eid}: bad install target {inst.get('target')!r}")
            slot = (inst.get("target"), inst.get("path"))
            slot_upgraders.setdefault(slot, set()).add(e.get("upgrader"))
            slot_entries.setdefault(slot, []).append(eid)

    # invariant 1 + 2
    for slot, ups in slot_upgraders.items():
        if len(ups) > 1:
            errors.append(f"slot {slot}: multiple upgraders {sorted(ups)} (entries {slot_entries[slot]})")
        if len(slot_entries[slot]) > 1:
            errors.append(f"slot {slot}: claimed by multiple entries {slot_entries[slot]} (one source per slot)")

    if errors:
        for e in errors:
            sys.stderr.write(f"FAIL {e}\n")
        sys.stderr.write(f"\n{len(errors)} violation(s).\n")
        return 1
    n = len(doc["entries"])
    print(f"ok: {n} entries, {len(slot_upgraders)} install slots, one upgrader each.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
