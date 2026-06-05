"""Tests for GoalSystem (PROJECT.md ## Goals section)."""
from __future__ import annotations

import pytest

PROJECT_MD = """---
schema_version: "PROJECT-md-v1"
---
# PROJECT.md — test_proj

## Vision

A grand vision statement that must survive edits.

## Goals

- **G-01**: ship the thing

## Non-Goals (Explicitly Out of Scope)

- boiling the ocean
"""


def test_add_assigns_sequential_ids(project):
    a = project.goals.add("Ship the MVP")
    b = project.goals.add("Write the docs")
    assert a.id == "G-01" and b.id == "G-02"
    assert [g.id for g in project.goals.list()] == ["G-01", "G-02"]


def test_update_and_remove(project):
    project.goals.add("First goal here")
    project.goals.add("Second goal here")
    project.goals.update("G-01", "Revised first goal")
    assert project.goals.get("G-01").text == "Revised first goal"
    assert project.goals.remove("G-02") is True
    assert [g.id for g in project.goals.list()] == ["G-01"]
    assert project.goals.remove("G-99") is False


def test_edits_preserve_rest_of_project_md(project):
    project.config.gald3r_dir.joinpath("PROJECT.md").write_text(PROJECT_MD, encoding="utf-8")
    # existing goal parsed
    assert [g.text for g in project.goals.list()] == ["ship the thing"]
    project.goals.add("a second measurable goal")
    md = project.config.gald3r_dir.joinpath("PROJECT.md").read_text(encoding="utf-8")
    # the other sections are untouched
    assert "A grand vision statement that must survive edits." in md
    assert "boiling the ocean" in md
    # both goals are present, in order
    assert "**G-01**: ship the thing" in md
    assert "**G-02**: a second measurable goal" in md


def test_id_normalization(project):
    project.goals.add("Some real goal text")
    assert project.goals.get("G-1").id == "G-01"
    assert project.goals.get("1").id == "G-01"
    assert project.goals.get("g-01").id == "G-01"
