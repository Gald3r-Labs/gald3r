"""Tests for inbox intake (systems/inbox.py) — absorbs hot_inbox_intake.ps1 (T1573)."""
from __future__ import annotations

from pathlib import Path


def _drop(dir_: Path, name: str, text: str) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / name).write_text(text, encoding="utf-8")


def _task_inbox(project) -> Path:
    return project.config.tasks_dir / "inbox"


def _bug_inbox(project) -> Path:
    return project.config.gald3r_dir / "bugs" / "inbox"


TASK_DRAFT = """---
title: "Add login rate limiting"
priority: high
type: feature
subsystems: [AUTH]
---
## Requirements
Throttle repeated failed logins.
"""

BUG_DRAFT = """---
title: "Null deref on empty cart"
priority: critical
subsystems: [CART]
---
## Description
Crashes when cart is empty.
"""


def test_intake_creates_tasks_and_bugs_and_drains_inbox(project):
    _drop(_task_inbox(project), "add-login.md", TASK_DRAFT)
    _drop(_bug_inbox(project), "null-deref.md", BUG_DRAFT)

    rep = project.inbox.intake()

    assert rep["tasks_ingested"] == 1 and rep["bugs_ingested"] == 1 and rep["total"] == 2
    # live state created
    t = project.tasks.list()[0]
    assert t.title == "Add login rate limiting" and t.priority == "high" and t.status == "pending"
    assert t.extra.get("source") == "inbox_intake"
    assert len(project.bugs.list()) == 1
    # drafts removed
    assert list(_task_inbox(project).glob("*.md")) == []
    assert list(_bug_inbox(project).glob("*.md")) == []


def test_dry_run_writes_nothing(project):
    _drop(_task_inbox(project), "add-login.md", TASK_DRAFT)

    rep = project.inbox.intake(dry_run=True)

    assert rep["total"] == 1 and rep["dry_run"] is True
    assert project.tasks.list() == []                     # no live task
    assert (_task_inbox(project) / "add-login.md").exists()  # draft preserved


def test_empty_inbox_is_a_noop(project):
    rep = project.inbox.intake()
    assert rep == {"tasks_ingested": 0, "bugs_ingested": 0, "total": 0,
                   "created": [], "removed_drafts": [], "dry_run": False}


def test_title_falls_back_to_filename_when_unset(project):
    _drop(_task_inbox(project), "fix-the-thing.md", "## Requirements\nno frontmatter here\n")
    project.inbox.intake()
    assert project.tasks.list()[0].title == "fix the thing"


def test_sequential_ids_continue_from_existing(project):
    project.tasks.create(title="Pre-existing task")        # T1
    _drop(_task_inbox(project), "second.md", TASK_DRAFT)
    project.inbox.intake()
    ids = sorted(t.id for t in project.tasks.list())
    assert ids == [1, 2]                                   # intake assigned T2, not T1
