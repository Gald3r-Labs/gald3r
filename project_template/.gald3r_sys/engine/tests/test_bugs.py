"""Tests for BugSystem (folder-backed pattern via _base.FolderSystem)."""
from __future__ import annotations

import pytest

from gald3r.store import split_doc


def test_create_assigns_prefixed_ids(project):
    a = project.bugs.create(title="First real bug here", severity="high", kind="code")
    b = project.bugs.create(title="Second real bug here", severity="low", kind="spec_defect")
    assert a.id == "BUG-001" and b.id == "BUG-002"
    assert a.fm["kind"] == "code" and a.fm["severity"] == "high"
    assert a.path.parent.name == "open"
    assert a.path.name.startswith("bug001_")


def test_status_moves_to_done_and_marker(project):
    b = project.bugs.create(title="Bug to be resolved", severity="medium", kind="code")
    old = b.path
    b2 = project.bugs.update(b.id, status="resolved")
    assert b2.path.parent.name == "done"
    assert project.bugs.marker("resolved") == "✅"
    assert not old.exists()


def test_validation(project):
    with pytest.raises(ValueError):
        project.bugs.create(title="bug", severity="high", kind="code")        # title < 5
    with pytest.raises(ValueError):
        project.bugs.create(title="Valid title here", severity="huge", kind="code")  # bad severity
    with pytest.raises(ValueError):
        project.bugs.create(title="Valid title here", severity="high", kind="nope")  # bad kind


def test_bugs_md_index_and_roundtrip(project):
    project.bugs.create(title="Index bug alpha here", severity="critical", kind="code")
    raw = project.bugs.get("BUG-001").path.read_text(encoding="utf-8")
    fm, _ = split_doc(raw)
    assert fm["id"] == "BUG-001" and fm["kind"] == "code"
    md = project.config.gald3r_dir.joinpath("BUGS.md").read_text(encoding="utf-8")
    assert "## Status Indicators" in md
    assert "| BUG-001 |" in md and "critical" in md
    assert "## Next Bug ID: BUG-002" in md


def test_sync_clean_after_ops(project):
    project.bugs.create(title="Clean bug one here", severity="low", kind="code")
    project.bugs.create(title="Clean bug two here", severity="low", kind="code")
    rep = project.bugs.sync()
    assert rep["count"] == 2 and rep["phantom"] == [] and rep["orphan"] == []


def test_get_accepts_id_variants(project):
    project.bugs.create(title="Variant id bug here", severity="low", kind="code")
    assert project.bugs.get("BUG-001").id == "BUG-001"
    assert project.bugs.get("BUG-1").id == "BUG-001"
    assert project.bugs.get(1).id == "BUG-001"
