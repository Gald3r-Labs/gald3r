"""Tests for canonical->mirror parity (systems/sync.py)."""
from __future__ import annotations

from pathlib import Path


def _canonical(root: Path):
    c = root / ".claude"
    (c / "skills" / "g-skl-a").mkdir(parents=True)
    (c / "skills" / "g-skl-a" / "SKILL.md").write_text("name: a\ndescription: a\n", encoding="utf-8")
    (c / "commands").mkdir(); (c / "commands" / "g-go.md").write_text("# go\n", encoding="utf-8")
    (c / "rules").mkdir(); (c / "rules" / "g-rl-00.md").write_text("rule\n", encoding="utf-8")
    (c / "hooks").mkdir()
    (c / "hooks" / "g-hk-generic.ps1").write_text("# generic\n", encoding="utf-8")
    (c / "hooks" / "g-hk-claude-chat-logger.ps1").write_text("# claude only\n", encoding="utf-8")
    (c / "CLAUDE.md").write_text("claude only\n", encoding="utf-8")


def _stale_cursor(root: Path):
    cur = root / ".cursor"
    (cur / "skills" / "g-skl-a").mkdir(parents=True)
    (cur / "skills" / "g-skl-a" / "SKILL.md").write_text("name: a\ndescription: a\n", encoding="utf-8")
    (cur / "rules").mkdir(); (cur / "rules" / "g-rl-00.mdc").write_text("OLD\n", encoding="utf-8")
    (cur / "cursor_instructions.md").write_text("per-platform keep me\n", encoding="utf-8")
    (cur / "commands").mkdir(); (cur / "commands" / "g-stray.md").write_text("# stray\n", encoding="utf-8")


def test_check_detects_missing_drift_extra(project):
    root = project.config.root
    _canonical(root); _stale_cursor(root)
    rep = project.sync.check(platform="cursor")
    cur = rep["platforms"][0]
    # projected = SKILL.md, g-go.md, g-hk-generic.ps1, g-rl-00.mdc  (claude-logger dropped)
    assert cur["projected"] == 4
    assert "commands/g-go.md" in cur["missing"] and "hooks/g-hk-generic.ps1" in cur["missing"]
    assert "rules/g-rl-00.mdc" in cur["drift"]
    assert "commands/g-stray.md" in cur["extra"]
    assert rep["in_parity"] is False


def test_apply_heals_to_parity_and_respects_preserve_drop(project):
    root = project.config.root
    _canonical(root); _stale_cursor(root)
    project.sync.apply(platform="cursor")
    after = project.sync.check(platform="cursor")
    assert after["in_parity"] is True
    cur = root / ".cursor"
    assert (cur / "cursor_instructions.md").exists()                 # per-platform preserved
    assert not (cur / "hooks" / "g-hk-claude-chat-logger.ps1").exists()  # source-specific dropped
    assert not (cur / "CLAUDE.md").exists()                          # source top-level not carried
    assert not (cur / "commands" / "g-stray.md").exists()            # extra pruned
    assert (cur / "rules" / "g-rl-00.mdc").read_text(encoding="utf-8") == "rule\n"  # healed
    assert (cur / "commands" / "g-go.md").exists()                   # projected


def test_default_targets_only_present_mirrors(project):
    root = project.config.root
    _canonical(root); _stale_cursor(root)            # only .cursor present
    rep = project.sync.check()
    assert [r["platform"] for r in rep["platforms"]] == ["cursor"]


def test_apply_bom_protects_non_ascii_ps1(project):
    root = project.config.root
    _canonical(root)
    scr = root / ".claude" / "skills" / "g-skl-a" / "scripts"
    scr.mkdir(parents=True)
    scr.joinpath("marker.ps1").write_bytes("Write-Host '📋 pending'\n".encode("utf-8"))  # NO BOM
    project.sync.apply(platform="cursor")
    out = (root / ".cursor" / "skills" / "g-skl-a" / "scripts" / "marker.ps1").read_bytes()
    assert out.startswith(b"\xef\xbb\xbf")          # BOM added so PS 5.1 can parse it
    assert "📋".encode("utf-8") in out               # functional emoji preserved
    # idempotent: a second apply reports no further drift on that file
    assert "skills/g-skl-a/scripts/marker.ps1" not in project.sync.check(platform="cursor")["platforms"][0]["drift"]
