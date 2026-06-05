"""Tests for ConstraintSystem (single-file table) and SubsystemSystem (name-keyed folder)."""
from __future__ import annotations

import pytest

from gald3r.store import split_doc


# ---- constraints ----

def test_constraint_add_list_archive(project):
    a = project.constraints.add("No secrets in git", scope="security", summary="never commit keys")
    b = project.constraints.add("UV only for venvs", scope="python")
    assert a.id == "C-001" and b.id == "C-002" and a.status == "active"
    md = project.config.gald3r_dir.joinpath("CONSTRAINTS.md").read_text(encoding="utf-8")
    assert "| C-001 | active | No secrets in git | security | never commit keys |" in md
    project.constraints.archive("C-002")
    assert project.constraints.get("C-002").status == "archived"
    with pytest.raises(ValueError):
        project.constraints.update("C-001", status="bogus")


# ---- subsystems ----

def test_subsystem_register_and_index(project):
    s = project.subsystems.register("TASK_MANAGEMENT", locations=["src/tasks/", "tests/"],
                                    owner="core-team")
    assert s.name == "TASK_MANAGEMENT" and s.status == "active"
    assert s.path.name == "TASK_MANAGEMENT.md"
    fm, body = split_doc(s.path.read_text(encoding="utf-8"))
    assert fm["name"] == "TASK_MANAGEMENT" and fm["locations"] == ["src/tasks/", "tests/"]
    md = project.config.gald3r_dir.joinpath("SUBSYSTEMS.md").read_text(encoding="utf-8")
    assert "| TASK_MANAGEMENT | active | `subsystems/TASK_MANAGEMENT.md` |" in md
    assert "src/tasks/, tests/" in md


def test_subsystem_get_update_remove(project):
    project.subsystems.register("VAULT", locations=["src/vault/"])
    project.subsystems.update("vault", owner="data-team", dependencies=["STORE"])
    s = project.subsystems.get("VAULT")
    assert s.owner == "data-team" and s.dependencies == ["STORE"]
    assert project.subsystems.remove("VAULT") is True
    assert project.subsystems.get("VAULT") is None


def test_subsystem_requires_locations(project):
    with pytest.raises(ValueError):
        project.subsystems.register("EMPTY", locations=[])
