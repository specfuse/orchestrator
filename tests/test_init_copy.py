# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""copy_file reports by content, not existence: identical files are not updates (#92)."""
from __future__ import annotations

import os

from specfuse.orchestrator import init


def _pair(tmp_path, src_text, dst_text=None):
    src = tmp_path / "src.md"
    src.write_text(src_text)
    dst = tmp_path / "out" / "dst.md"
    if dst_text is not None:
        dst.parent.mkdir()
        dst.write_text(dst_text)
    return src, dst


def test_dry_run_is_silent_for_identical_file(tmp_path, capsys):
    src, dst = _pair(tmp_path, "same\n", "same\n")
    init.copy_file(src, dst, dry=True)
    assert "would" not in capsys.readouterr().out


def test_identical_file_is_not_rewritten(tmp_path, capsys):
    src, dst = _pair(tmp_path, "same\n", "same\n")
    os.utime(dst, (0, 0))
    init.copy_file(src, dst, dry=False)
    assert dst.stat().st_mtime == 0
    assert "update" not in capsys.readouterr().out


def test_dry_run_reports_update_for_changed_file(tmp_path, capsys):
    src, dst = _pair(tmp_path, "new\n", "old\n")
    init.copy_file(src, dst, dry=True)
    assert f"would update: {dst}" in capsys.readouterr().out
    assert dst.read_text() == "old\n"


def test_dry_run_reports_add_for_missing_file(tmp_path, capsys):
    src, dst = _pair(tmp_path, "new\n")
    init.copy_file(src, dst, dry=True)
    assert f"would add: {dst}" in capsys.readouterr().out
    assert not dst.exists()


def test_changed_file_is_updated(tmp_path, capsys):
    src, dst = _pair(tmp_path, "new\n", "old\n")
    init.copy_file(src, dst, dry=False)
    assert dst.read_text() == "new\n"
    assert f"update: {dst}" in capsys.readouterr().out
