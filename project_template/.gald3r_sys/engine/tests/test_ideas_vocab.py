"""Tests for IdeaSystem and VocabSystem (single-file table systems)."""
from __future__ import annotations

import pytest


# ---- ideas ----

def test_idea_capture_and_list(project):
    a = project.ideas.capture("Add a dark mode toggle", category="ux")
    b = project.ideas.capture("Cache the heavy query")
    assert a.id == "I-001" and b.id == "I-002"
    assert a.status == "new" and a.category == "ux"
    md = project.config.gald3r_dir.joinpath("IDEA_BOARD.md").read_text(encoding="utf-8")
    assert "| I-001 | [💡] | Add a dark mode toggle | ux |" in md


def test_idea_update_status_roundtrips(project):
    project.ideas.capture("Promote me to a task")
    project.ideas.update("I-001", status="promoted")
    assert project.ideas.get("I-001").status == "promoted"
    # re-read from disk via a fresh system call
    assert project.ideas.get("I-1").status == "promoted"
    with pytest.raises(ValueError):
        project.ideas.update("I-001", status="bogus")


# ---- vocab ----

def test_vocab_add_get_remove(project):
    project.vocab.add("MVP", "Minimum Viable Product", "scope")
    project.vocab.add("WIP", "Work In Progress")
    assert project.vocab.get("mvp").expansion == "Minimum Viable Product"
    md = project.config.gald3r_dir.joinpath("vocab.md").read_text(encoding="utf-8")
    assert "| `MVP` | Minimum Viable Product | scope |" in md
    assert project.vocab.remove("WIP") is True
    assert project.vocab.get("WIP") is None
    assert project.vocab.remove("NOPE") is False


def test_vocab_upsert(project):
    project.vocab.add("API", "Application Programming Interface")
    project.vocab.add("API", "A Precise Interface", "redefined")   # upsert, not duplicate
    terms = [t for t in project.vocab.list() if t.abbr == "API"]
    assert len(terms) == 1 and terms[0].context == "redefined"
