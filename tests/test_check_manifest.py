"""Unit tests for `specfuse/orchestrator/check_manifest.py`.

Not a deferred red-test nodeid from GATE-02-REVIEW.md / T07 — added because
`check_manifest` is one of the six modules `.specfuse/verification.yml`'s
scoped `coverage` gate measures (GATE-03-REVIEW.md open decision #2), and its
happy path alone does not exercise the validator's error branches.
"""

from __future__ import annotations

import textwrap

from specfuse.orchestrator import check_manifest

_INVALID_MANIFEST = textwrap.dedent(
    """\
    categories: [shared-core]
    authorities: [orchestrator-frozen]
    stabilities: [stable, experimental]
    upgraders: [orchestrator-init, manual]
    targets: [component]
    entries:
      - id: missing-field-entry
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        upgrader: orchestrator-init
        install:
          - {target: component, path: p1}
      - id: bad-category-entry
        category: bogus-category
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: stable
        upgrader: orchestrator-init
        install:
          - {target: component, path: p2}
      - id: bad-authority-entry
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: bogus-authority
        stability: stable
        upgrader: orchestrator-init
        install:
          - {target: component, path: p3}
      - id: bad-upgrader-entry
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: stable
        upgrader: bogus-upgrader
        install:
          - {target: component, path: p4}
      - id: bad-repo-entry
        category: shared-core
        canonical_source: {repo: nowhere}
        authority: orchestrator-frozen
        stability: stable
        upgrader: manual
        install:
          - {target: component, path: p5}
      - id: charter-violation-entry
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: experimental
        upgrader: orchestrator-init
        install:
          - {target: component, path: p6}
      - id: bad-install-target-entry
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: stable
        upgrader: manual
        install:
          - {target: bogus-target, path: p7}
      - id: dup-slot-entry-a
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: stable
        upgrader: orchestrator-init
        install:
          - {target: component, path: dup/slot}
      - id: dup-slot-entry-b
        category: shared-core
        canonical_source: {repo: orchestrator}
        authority: orchestrator-frozen
        stability: stable
        upgrader: manual
        install:
          - {target: component, path: dup/slot}
    """
)


def test_check_manifest_valid(substrate_ready):
    assert check_manifest.main() == 0


def test_check_manifest_invalid(tmp_path, monkeypatch):
    bad_manifest = tmp_path / "ownership-manifest.yaml"
    bad_manifest.write_text(_INVALID_MANIFEST, encoding="utf-8")
    monkeypatch.setattr(check_manifest.paths, "substrate", lambda *parts: bad_manifest)
    assert check_manifest.main() == 1


def test_check_manifest_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        check_manifest.paths, "substrate", lambda *parts: tmp_path / "missing.yaml"
    )
    assert check_manifest.main() == 2
