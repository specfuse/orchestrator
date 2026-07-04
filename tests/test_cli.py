"""specfuse-orchestrator CLI dispatch (FEAT-2026-0002/T01, gate 1)."""

from __future__ import annotations

import json
import subprocess

import pytest

from specfuse.orchestrator import cli


def test_cli_help_lists_subcommands(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "init" in out
    assert "upgrade" in out


def test_cli_no_command_errors():
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_cli_init_dispatches_to_init_module(capsys):
    # Forward --help through to specfuse.orchestrator.init's own parser rather
    # than running a real scaffold.
    with pytest.raises(SystemExit) as exc:
        cli.main(["init", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--target" in out


def test_cli_upgrade_no_target_dir_errors():
    rc = cli.main(["upgrade"])
    assert rc == 2


def test_upgrade_syncs_substrate(tmp_path):
    from specfuse.orchestrator import paths

    rc = cli.main(["upgrade", str(tmp_path)])
    assert rc == 0

    mount = tmp_path / "shared"
    assert (mount / "rules" / "never-touch.md").is_file()
    assert (mount / "schemas" / "event.schema.json").is_file()
    assert (mount / "rules" / "never-touch.md").read_text() == paths.substrate(
        "rules", "never-touch.md"
    ).read_text()
    assert (mount / "schemas" / "event.schema.json").read_text() == paths.substrate(
        "schemas", "event.schema.json"
    ).read_text()


def test_self_provision_if_stale(tmp_path):
    from specfuse.orchestrator import __version__

    (tmp_path / "features").mkdir()
    (tmp_path / "features" / "keep.md").write_text("do not clobber")

    provisioned = cli.self_provision_if_stale(tmp_path)
    assert provisioned is True

    mount = tmp_path / cli._substrate_mount_name()
    assert (mount / "rules" / "never-touch.md").is_file()
    stamp = mount / cli._SUBSTRATE_VERSION_STAMP
    assert stamp.read_text(encoding="utf-8").strip() == __version__
    assert (tmp_path / "features" / "keep.md").read_text() == "do not clobber"

    sentinel = mount / "rules" / "never-touch.md"
    sentinel.write_text("mutated-to-detect-overwrite")

    provisioned_again = cli.self_provision_if_stale(tmp_path)
    assert provisioned_again is False
    assert sentinel.read_text() == "mutated-to-detect-overwrite"


def test_upgrade_mount_matches_claude_wiring_sentinel(tmp_path):
    rc = cli.main(["upgrade", str(tmp_path)])
    assert rc == 0

    sentinel_rel = cli._RULES_SENTINEL.lstrip("@")
    assert (tmp_path / sentinel_rel).is_file()


def test_upgrade_preserves_user_owned_state(tmp_path):
    (tmp_path / "features").mkdir()
    (tmp_path / "features" / "keep.md").write_text("do not clobber")
    (tmp_path / "roadmap.md").write_text("my roadmap\n")

    rc = cli.main(["upgrade", str(tmp_path)])

    assert rc == 0
    assert (tmp_path / "features" / "keep.md").read_text() == "do not clobber"
    assert (tmp_path / "roadmap.md").read_text() == "my roadmap\n"


def test_upgrade_overwrites_stale_substrate_file(tmp_path):
    from specfuse.orchestrator import paths

    stale = tmp_path / "shared" / "rules" / "never-touch.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale content from an older wheel")

    rc = cli.main(["upgrade", str(tmp_path)])

    assert rc == 0
    assert stale.read_text() != "stale content from an older wheel"
    assert stale.read_text() == paths.substrate("rules", "never-touch.md").read_text()


def test_upgrade_refreshes_claude_wiring(tmp_path):
    rc = cli.main(["upgrade", str(tmp_path)])
    assert rc == 0

    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert (
        settings["extraKnownMarketplaces"]["specfuse"]["source"]["repo"]
        == "specfuse/specfuse"
    )
    assert settings["enabledPlugins"]["specfuse@specfuse"] is True
    pre_tool_use = settings["hooks"]["PreToolUse"]
    assert any(
        "deny-specs-edit.py" in hook["command"]
        for entry in pre_tool_use
        for hook in entry["hooks"]
    )

    claude_md = (tmp_path / ".claude" / "CLAUDE.md").read_text()
    assert cli._RULES_SENTINEL in claude_md


def test_upgrade_settings_merge_preserves_existing_keys(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(
        json.dumps({"unrelated": {"keep": "me"}}) + "\n"
    )

    rc = cli.main(["upgrade", str(tmp_path)])
    assert rc == 0

    settings = json.loads(settings_path.read_text())
    assert settings["unrelated"] == {"keep": "me"}
    assert "specfuse" in settings["extraKnownMarketplaces"]


def test_upgrade_claude_wiring_idempotent(tmp_path):
    cli.main(["upgrade", str(tmp_path)])
    rc = cli.main(["upgrade", str(tmp_path)])
    assert rc == 0

    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    pre_tool_use = settings["hooks"]["PreToolUse"]
    deny_entries = [
        entry
        for entry in pre_tool_use
        for hook in entry["hooks"]
        if "deny-specs-edit.py" in hook["command"]
    ]
    assert len(deny_entries) == 1


def test_init_scaffolds_state_dirs(tmp_path):
    rc = cli.main(["init", str(tmp_path)])
    assert rc == 0
    for name in ("features", "events", "project", "inbox", "overrides"):
        assert (tmp_path / name).is_dir()
    assert (tmp_path / "roadmap.md").is_file()


def test_init_scaffold_is_idempotent(tmp_path):
    assert cli.main(["init", str(tmp_path)]) == 0

    marker = tmp_path / "project" / "keep-me.md"
    marker.write_text("do not clobber")
    roadmap_before = (tmp_path / "roadmap.md").read_text()

    rc = cli.main(["init", str(tmp_path)])

    assert rc == 0
    assert marker.read_text() == "do not clobber"
    assert (tmp_path / "roadmap.md").read_text() == roadmap_before


def test_init_no_target_dir_errors():
    rc = cli.main(["init"])
    assert rc == 2


def test_init_git_and_claude_wiring(tmp_path):
    rc = cli.main(["init", str(tmp_path)])
    assert rc == 0

    assert (tmp_path / ".git").is_dir()

    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert (
        settings["extraKnownMarketplaces"]["specfuse"]["source"]["repo"]
        == "specfuse/specfuse"
    )
    assert settings["enabledPlugins"]["specfuse@specfuse"] is True
    pre_tool_use = settings["hooks"]["PreToolUse"]
    assert any(
        "deny-specs-edit.py" in hook["command"]
        for entry in pre_tool_use
        for hook in entry["hooks"]
    )

    assert (tmp_path / "project" / "NEXT_STEPS.md").is_file()


def test_init_settings_merge_preserves_existing_keys(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(
        json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}) + "\n"
    )

    rc = cli.main(["init", str(tmp_path)])
    assert rc == 0

    settings = json.loads(settings_path.read_text())
    assert settings["permissions"]["allow"] == ["Bash(ls:*)"]
    assert "specfuse" in settings["extraKnownMarketplaces"]


def test_init_existing_git_repo_is_not_reinitialized(tmp_path):
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True)
    original_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    rc = cli.main(["init", str(tmp_path)])
    assert rc == 0

    new_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert new_head == original_head
