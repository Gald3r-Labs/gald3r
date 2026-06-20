"""Tests for g_pt.py — the @g-pt workflow-profile management CLI (T417).

Every test builds an isolated tmp fixture project (`tmp_path`) with its own
`.gald3r/config/workflow_profiles/` and PROJECT.md — the real repo `.gald3r/`
is never touched.

Run via:
    uv run --extra dev python -m pytest \
        .claude/skills/g-skl-project-types/scripts/test_g_pt.py -v

or directly:
    python -m pytest test_g_pt.py
"""
# @subsystems: TASK_MANAGEMENT
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import g_pt  # noqa: E402


SOFTWARE_DEV_YAML = """\
# header comment that must survive a copy
id: software_dev
name: Software Development
description: >
  Default gald3r workflow.
task_statuses:
  - id: pending
    symbol: "[📋]"
    description: "Ready for pickup."
    skip_in_pipeline: false
  - id: in-progress
    symbol: "[🔄]"
    description: "Claimed."
    skip_in_pipeline: false
  - id: done
    symbol: "[✅]"
    description: "Reviewer PASS."
    skip_in_pipeline: true
transitions:
  pending: [in-progress]
  in-progress: [done]
task_types:
  - feature
  - bug_fix
"""

CONTENT_YAML = """\
id: content_creation
name: Content Creation
task_statuses:
  - id: concept
    symbol: "[💡]"
  - id: published
    symbol: "[✅]"
"""

PROJECT_MD_NO_PROFILE = """\
---
gald3r_rel_version: "1.11.0"
schema_version: "PROJECT-md-v1"
---
# PROJECT.md — fixture project

Some body text.
"""


@pytest.fixture()
def proj(tmp_path: Path) -> Path:
    """Build an isolated fixture project root with two profiles + PROJECT.md.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        The fixture repo root (contains a `.gald3r/` tree).
    """
    gald3r = tmp_path / ".gald3r"
    profiles = gald3r / "config" / "workflow_profiles"
    profiles.mkdir(parents=True)
    (profiles / "software_dev.yaml").write_text(SOFTWARE_DEV_YAML, encoding="utf-8")
    (profiles / "content_creation.yaml").write_text(CONTENT_YAML, encoding="utf-8")
    (gald3r / "PROJECT.md").write_text(PROJECT_MD_NO_PROFILE, encoding="utf-8")
    return tmp_path


def _run(proj: Path, *cli_args: str, capsys) -> tuple[int, str, str]:
    """Invoke g_pt.main with --project-root pinned to the fixture.

    Args:
        proj: Fixture repo root.
        *cli_args: Subcommand + its arguments.
        capsys: pytest capsys fixture.

    Returns:
        A ``(exit_code, stdout, stderr)`` tuple.
    """
    code = g_pt.main(["--project-root", str(proj), *cli_args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------
def test_list_shows_all_profiles(proj: Path, capsys) -> None:
    """`list` shows every profile in the directory.

    With no PROJECT.md `workflow_profile:` field and no `.identity`, the
    loader's hybrid chain falls back to `freeform` (not present in this
    fixture), so no line is marked active — and that is correct behavior.
    """
    code, out, _ = _run(proj, "list", capsys=capsys)
    assert code == 0
    assert "software_dev" in out
    assert "content_creation" in out
    # freeform fallback isn't in the dir, so nothing is marked active here.
    assert "(active)" not in out


def test_list_marks_active_when_present(proj: Path, capsys) -> None:
    """When the resolved active profile exists in the dir, it is marked."""
    profiles = proj / ".gald3r" / "config" / "workflow_profiles"
    # Provide a freeform.yaml so the fallback resolves to a present file.
    (profiles / "freeform.yaml").write_text(
        "id: freeform\nname: Freeform\n"
        "task_statuses:\n  - id: open\n  - id: done\n",
        encoding="utf-8",
    )
    code, out, _ = _run(proj, "list", capsys=capsys)
    assert code == 0
    active_line = next(ln for ln in out.splitlines() if "freeform" in ln)
    assert "*" in active_line and "(active)" in active_line


def test_list_active_follows_project_md(proj: Path, capsys) -> None:
    """After `use`, `list` marks the newly-activated profile as active."""
    _run(proj, "use", "content_creation", capsys=capsys)
    code, out, _ = _run(proj, "list", capsys=capsys)
    assert code == 0
    # The content_creation line should carry the active marker.
    active_line = next(
        ln for ln in out.splitlines() if "content_creation" in ln
    )
    assert "*" in active_line and "(active)" in active_line


# --------------------------------------------------------------------------
# use
# --------------------------------------------------------------------------
def test_use_updates_project_md(proj: Path, capsys) -> None:
    """`use` writes workflow_profile: into PROJECT.md frontmatter."""
    code, out, _ = _run(proj, "use", "content_creation", capsys=capsys)
    assert code == 0
    text = (proj / ".gald3r" / "PROJECT.md").read_text(encoding="utf-8")
    assert "workflow_profile: content_creation" in text
    # Inserted into the frontmatter block (before the body heading).
    assert text.index("workflow_profile:") < text.index("# PROJECT.md")


def test_use_alias_normalized(proj: Path, capsys) -> None:
    """`use software_development` resolves via alias to software_dev."""
    code, _, _ = _run(proj, "use", "software_development", capsys=capsys)
    assert code == 0
    text = (proj / ".gald3r" / "PROJECT.md").read_text(encoding="utf-8")
    assert "workflow_profile: software_dev" in text


def test_use_idempotent_no_duplicate(proj: Path, capsys) -> None:
    """Running `use` twice updates in place, never duplicating the field."""
    _run(proj, "use", "content_creation", capsys=capsys)
    _run(proj, "use", "software_dev", capsys=capsys)
    text = (proj / ".gald3r" / "PROJECT.md").read_text(encoding="utf-8")
    assert text.count("workflow_profile:") == 1
    assert "workflow_profile: software_dev" in text


def test_use_unknown_profile_fails(proj: Path, capsys) -> None:
    """`use` on a non-existent profile exits non-zero and changes nothing."""
    code, _, err = _run(proj, "use", "nope_not_here", capsys=capsys)
    assert code == 1
    assert "not found" in err
    text = (proj / ".gald3r" / "PROJECT.md").read_text(encoding="utf-8")
    assert "workflow_profile:" not in text


# --------------------------------------------------------------------------
# copy
# --------------------------------------------------------------------------
def test_copy_creates_file_and_rewrites_id(proj: Path, capsys) -> None:
    """`copy` creates <new>.yaml with id/name rewritten, comments preserved."""
    code, out, _ = _run(proj, "copy", "software_dev", "my_workflow", capsys=capsys)
    assert code == 0
    new_path = proj / ".gald3r" / "config" / "workflow_profiles" / "my_workflow.yaml"
    assert new_path.exists()
    body = new_path.read_text(encoding="utf-8")
    assert "id: my_workflow" in body
    assert "name: My Workflow" in body
    assert "id: software_dev" not in body
    # Original comment survives the line-oriented rewrite.
    assert "header comment that must survive a copy" in body


def test_copy_refuses_existing_target(proj: Path, capsys) -> None:
    """`copy` refuses to overwrite an existing profile."""
    code, _, err = _run(proj, "copy", "software_dev", "content_creation", capsys=capsys)
    assert code == 1
    assert "already exists" in err


def test_copy_missing_source_fails(proj: Path, capsys) -> None:
    """`copy` from a non-existent source exits non-zero."""
    code, _, err = _run(proj, "copy", "ghost", "new_one", capsys=capsys)
    assert code == 1
    assert "not found" in err
    assert not (proj / ".gald3r" / "config" / "workflow_profiles" / "new_one.yaml").exists()


# --------------------------------------------------------------------------
# edit
# --------------------------------------------------------------------------
def test_edit_prints_absolute_path(proj: Path, capsys) -> None:
    """`edit` prints the resolved absolute path to the profile YAML."""
    code, out, _ = _run(proj, "edit", "software_dev", capsys=capsys)
    assert code == 0
    printed = Path(out.strip())
    assert printed.is_absolute()
    assert printed.name == "software_dev.yaml"
    assert printed.exists()


def test_edit_missing_fails(proj: Path, capsys) -> None:
    """`edit` on a missing profile exits non-zero."""
    code, _, err = _run(proj, "edit", "ghost", capsys=capsys)
    assert code == 1
    assert "not found" in err


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------
def test_validate_ok(proj: Path, capsys) -> None:
    """A well-formed profile validates clean (exit 0)."""
    code, out, _ = _run(proj, "validate", "software_dev", capsys=capsys)
    assert code == 0
    assert "OK" in out


def test_validate_catches_missing_field(proj: Path, capsys) -> None:
    """A profile missing a required field (name) fails validation."""
    profiles = proj / ".gald3r" / "config" / "workflow_profiles"
    (profiles / "broken.yaml").write_text(
        "id: broken\n"
        "task_statuses:\n"
        "  - id: open\n",
        encoding="utf-8",
    )
    code, _, err = _run(proj, "validate", "broken", capsys=capsys)
    assert code == 1
    assert "missing required field: name" in err


def test_validate_catches_duplicate_status(proj: Path, capsys) -> None:
    """Duplicate status ids are reported."""
    profiles = proj / ".gald3r" / "config" / "workflow_profiles"
    (profiles / "dup.yaml").write_text(
        "id: dup\nname: Dup\n"
        "task_statuses:\n"
        "  - id: open\n"
        "  - id: open\n",
        encoding="utf-8",
    )
    code, _, err = _run(proj, "validate", "dup", capsys=capsys)
    assert code == 1
    assert "duplicate status id: open" in err


def test_validate_catches_unknown_transition_target(proj: Path, capsys) -> None:
    """A transition referencing an undefined status id is reported."""
    profiles = proj / ".gald3r" / "config" / "workflow_profiles"
    (profiles / "badtrans.yaml").write_text(
        "id: badtrans\nname: Bad Trans\n"
        "task_statuses:\n"
        "  - id: open\n"
        "  - id: done\n"
        "transitions:\n"
        "  open: [shipped]\n",  # 'shipped' is not a defined status
        encoding="utf-8",
    )
    code, _, err = _run(proj, "validate", "badtrans", capsys=capsys)
    assert code == 1
    assert "unknown status id: shipped" in err


def test_copy_then_validate_round_trip(proj: Path, capsys) -> None:
    """A copied profile still validates clean (id/name rewrite stays valid)."""
    rc_copy, _, _ = _run(proj, "copy", "software_dev", "round_trip", capsys=capsys)
    assert rc_copy == 0
    rc_val, out, _ = _run(proj, "validate", "round_trip", capsys=capsys)
    assert rc_val == 0
    assert "OK round_trip" in out
