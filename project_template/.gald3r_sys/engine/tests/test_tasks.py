"""Unit tests for the task state machine (systems/tasks.py)."""
from __future__ import annotations

import pytest

from gald3r.schema import task as T


def test_sequential_ids(project):
    a = project.tasks.create(title="First real task")
    b = project.tasks.create(title="Second real task")
    c = project.tasks.create(title="Third real task")
    assert [a.id, b.id, c.id] == [1, 2, 3]


def test_create_lands_in_open_folder(project):
    t = project.tasks.create(title="A pending task", priority="high", type="feature")
    assert t.status == "pending"
    assert t.path.parent.name == "open"
    assert t.path.name.startswith("task001_")
    assert t.marker == "📋"


def test_frontmatter_fields_and_validation(project):
    t = project.tasks.create(title="Wire up the thing", type="bug_fix",
                             priority="critical", created_date="2026-06-03")
    fm = t.to_frontmatter()
    assert T.validate(fm) == []
    assert fm["id"] == 1 and fm["type"] == "bug_fix" and fm["priority"] == "critical"
    assert fm["created_date"] == "2026-06-03"
    assert fm["schema_version"] == "task-file-v1"


@pytest.mark.parametrize("status,folder,marker", [
    ("in-progress", "in-progress", "🔄"),
    ("awaiting-verification", "awaiting-verification", "🔍"),
    ("verification-in-progress", "awaiting-verification", "🕵️"),
    ("completed", "completed", "✅"),
    ("paused", "paused", "⏸️"),
    ("cancelled", "cancelled", "❌"),
    ("failed", "failed", "❌"),
])
def test_status_transitions_move_folders(project, status, folder, marker):
    t = project.tasks.create(title="Some task to move")
    old_path = t.path
    t2 = project.tasks.update(t.id, status=status)
    assert t2.status == status
    assert t2.path.parent.name == folder
    assert t2.marker == marker
    # the old file was moved, not duplicated
    assert not old_path.exists()
    assert len(project.tasks.list()) == 1


def test_claim_sets_in_progress_with_owner(project):
    t = project.tasks.create(title="Claimable task")
    c = project.tasks.claim(t.id, owner="agent-x")
    assert c.status == "in-progress"
    assert c.extra["worktree_owner"] == "agent-x"
    assert "status_changed" in c.extra


def test_validation_rejects_bad_input(project):
    with pytest.raises(ValueError):
        project.tasks.create(title="bad")  # title < 5 chars
    with pytest.raises(ValueError):
        project.tasks.create(title="Good title here", type="nonsense")
    with pytest.raises(ValueError):
        project.tasks.create(title="Good title here", priority="urgent")


def test_get_and_list_filter(project):
    project.tasks.create(title="Task one alpha")
    b = project.tasks.create(title="Task two beta")
    project.tasks.update(b.id, status="in-progress")
    assert project.tasks.get(b.id).status == "in-progress"
    assert project.tasks.get(999) is None
    assert {t.id for t in project.tasks.list(status="pending")} == {1}
    assert {t.id for t in project.tasks.list(status="in-progress")} == {2}
    assert len(project.tasks.list()) == 2
