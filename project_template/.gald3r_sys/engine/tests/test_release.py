"""Tests for ReleaseSystem (folder-backed, frozen-on-ship, cadence math)."""
from __future__ import annotations

import pytest

from gald3r.store import split_doc


def test_release_create_and_index(project):
    r = project.release.create("Spring milestone", version="1.0.0",
                               target_date="2026-07-01", status="planned")
    assert r.id == "R-001" and r.status == "planned"
    assert r.path.name == "release001_spring_milestone.md"
    md = project.config.gald3r_dir.joinpath("RELEASES.md").read_text(encoding="utf-8")
    assert "| R-001 | Spring milestone | 1.0.0 | 2026-07-01 | planned | 0 |" in md
    assert "Default cadence | 14 days" in md       # config block preserved


def test_release_ship_freezes(project):
    project.release.create("Beta cut", version="0.9.0", status="in_progress")
    shipped = project.release.ship("R-001", version="1.0.0")
    assert shipped.status == "released" and shipped.fm["version"] == "1.0.0"
    # a shipped release is immutable (C-019-style freeze)
    with pytest.raises(PermissionError):
        project.release.update("R-001", status="deferred")


def test_release_roadmap_and_cadence(project):
    project.release.create("Cut A", version="1.0.0", target_date="2026-06-01", status="released")
    project.release.create("Cut B", version="1.1.0", target_date="2026-07-15", status="planned")
    project.release.create("Cut C", version="1.2.0", target_date="2026-07-01", status="in_progress")
    roadmap = project.release.roadmap()
    # only non-terminal, ordered by target_date
    assert [r.id for r in roadmap] == ["R-003", "R-002"]
    # most recent target (2026-07-15) + 14 days
    assert project.release.next_target_date() == "2026-07-29"


def test_release_requires_version(project):
    with pytest.raises(ValueError):
        project.release.create("No version here", version="")


def test_release_tasks_count_renders(project):
    project.release.create("With tasks", version="2.0.0", tasks=[12, 13, 14])
    md = project.config.gald3r_dir.joinpath("RELEASES.md").read_text(encoding="utf-8")
    assert "| R-001 | With tasks | 2.0.0 | — | planned | 3 |" in md
    fm, _ = split_doc(project.release.get("R-001").path.read_text(encoding="utf-8"))
    assert fm["tasks"] == [12, 13, 14]
