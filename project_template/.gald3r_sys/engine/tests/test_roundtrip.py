"""Integration tests: on-disk format parity, the TASKS.md index, sync drift, MCP tools."""
from __future__ import annotations

import re

import pytest

from gald3r.adapters import mcp as mcp_adapter
from gald3r.store import split_doc


def test_frontmatter_roundtrips_through_disk(project):
    t = project.tasks.create(title="Persisted task title", type="refactor",
                             priority="low", created_date="2026-06-03")
    raw = t.path.read_text(encoding="utf-8")
    # controlled key order: id first, then title/type/status/priority/created_date
    assert raw.startswith("---\nid: 1\ntitle: ")
    fm, body = split_doc(raw)
    assert fm["id"] == 1 and fm["title"] == "Persisted task title"
    assert fm["type"] == "refactor" and fm["status"] == "pending"
    # YAML parses an unquoted ISO date into a date object; the engine normalizes to str on load
    assert str(fm["created_date"]) == "2026-06-03"
    assert "## Status History" in body
    # a fresh engine reading the same disk gets an identical task
    again = project.tasks.get(1)
    assert again.title == t.title and again.status == t.status and again.priority == t.priority


def test_tasks_md_has_legend_and_resolving_rows(project):
    project.tasks.create(title="Index row one")
    b = project.tasks.create(title="Index row two")
    project.tasks.update(b.id, status="in-progress")
    md = project.config.tasks_md.read_text(encoding="utf-8")
    # legend section preserved (agents parse it)
    assert "## Status Indicators" in md
    assert "[🔄]" in md and "[🔍]" in md and "[✅]" in md
    # every task file has a resolving T<id> row
    assert "**T1**" in md and "**T2**" in md
    # the in-progress task renders with its marker
    assert re.search(r"\[🔄\] \*\*T2\*\* Index row two", md)
    # footer counts reflect reality
    assert "completed / 2 total" in md


def test_sync_reports_clean_after_engine_ops(project):
    project.tasks.create(title="Clean sync task a")
    project.tasks.create(title="Clean sync task b")
    rep = project.tasks.sync()
    assert rep["tasks"] == 2
    assert rep["phantom"] == [] and rep["orphan"] == []


def test_sync_detects_phantom_index_rows(project):
    project.tasks.create(title="Real backed task")           # T1 with a file
    # simulate an externally-edited index referencing a non-existent T999
    project.config.tasks_md.write_text("# TASKS.md\n- **T999** ghost\n", encoding="utf-8")
    rep = project.tasks.sync()
    assert 999 in rep["phantom"]          # in index, no file
    assert 1 in rep["orphan"]             # file present, was not in that index


def test_completed_task_moves_to_completed_section(project):
    a = project.tasks.create(title="Will be completed task")
    project.tasks.update(a.id, status="completed")
    md = project.config.tasks_md.read_text(encoding="utf-8")
    backlog, _, completed = md.partition("## Completed Tasks")
    assert "**T1**" in completed and "**T1**" not in backlog
    assert "1 completed / 1 total" in md


# ---- MCP surface ----

def test_mcp_tool_impls_drive_the_core(project):
    tools = mcp_adapter.tool_impls(project)
    created = tools["gald3r_task_new"](title="Created via MCP tool", priority="high")
    assert created["id"] == 1 and created["status"] == "pending"
    listed = tools["gald3r_task_list"](status="pending")
    assert [t["id"] for t in listed["tasks"]] == [1]
    updated = tools["gald3r_task_update"](id=1, status="in-progress")
    assert updated["status"] == "in-progress" and updated["marker"] == "🔄"
    rep = tools["gald3r_task_sync"]()
    assert rep["tasks"] == 1


def test_mcp_server_registers_four_tools(project):
    pytest.importorskip("mcp")
    server = mcp_adapter.build_server(root=project.config.root)
    import asyncio
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert {"gald3r_task_new", "gald3r_task_list",
            "gald3r_task_update", "gald3r_task_sync"} <= names
