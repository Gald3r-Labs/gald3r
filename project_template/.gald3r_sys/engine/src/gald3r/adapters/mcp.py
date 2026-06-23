"""MCP surface — exposes the same task operations as MCP tools so any MCP-speaking
IDE (Claude Code, Cursor, OpenCode, …) calls the engine directly. This is the
34-platform unlock: one engine, N tool stubs, no copied trees.

The tool *implementations* are plain functions (testable without the `mcp` package);
the FastMCP server is a thin registration layer over them. `mcp` is an optional
dependency — install with `uv sync --extra mcp` (or it's in the dev group).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional

from gald3r.core import Gald3r


def tool_impls(g: Gald3r) -> Dict[str, Callable[..., Any]]:
    """The MCP tool functions, bound to a Gald3r core. Pure — directly unit-testable."""

    def gald3r_task_new(title: str, type: str = "feature", priority: str = "medium",
                        status: str = "pending") -> Dict[str, Any]:
        """Create a task; returns the created task."""
        return g.tasks.create(title=title, type=type, priority=priority, status=status).to_dict()

    def gald3r_task_list(status: Optional[str] = None) -> Dict[str, Any]:
        """List tasks, optionally filtered by status."""
        return {"tasks": [t.to_dict() for t in g.tasks.list(status=status)]}

    def gald3r_task_update(id: int, status: Optional[str] = None, title: Optional[str] = None,
                           priority: Optional[str] = None, type: Optional[str] = None) -> Dict[str, Any]:
        """Update a task's status/title/priority/type."""
        return g.tasks.update(id, status=status, title=title, priority=priority, type=type).to_dict()

    def gald3r_task_set_release_hold(id: int, hold: str, reason: str = "",
                                     sync_with: Optional[list] = None) -> Dict[str, Any]:
        """Set a task's release-staging hold (T419). hold: none|manual|sync_required.
        sync_with is a list of {project, task, reason} dicts (sync_required only)."""
        return g.tasks.set_release_hold(id, hold, reason=reason, sync_with=sync_with).to_dict()

    def gald3r_task_clear_release_hold(id: int) -> Dict[str, Any]:
        """Clear a task's release-staging hold (T419) — equivalent to release_hold: none."""
        return g.tasks.clear_release_hold(id).to_dict()

    def gald3r_task_sync() -> Dict[str, Any]:
        """Regenerate TASKS.md from the task files; report phantom/orphan drift."""
        return g.tasks.sync()

    # ---- goals ----
    def gald3r_goal_add(text: str) -> Dict[str, Any]:
        """Add a project goal (PROJECT.md ## Goals)."""
        return g.goals.add(text).to_dict()

    def gald3r_goal_list() -> Dict[str, Any]:
        """List project goals."""
        return {"goals": [x.to_dict() for x in g.goals.list()]}

    # ---- bugs ----
    def gald3r_bug_new(title: str, severity: str = "medium", kind: str = "code",
                       status: str = "open") -> Dict[str, Any]:
        """File a bug (kind: code|spec_defect|policy_incongruity|design_gap)."""
        return g.bugs.create(title=title, severity=severity, kind=kind, status=status).to_dict()

    def gald3r_bug_list(status: Optional[str] = None) -> Dict[str, Any]:
        """List bugs, optionally filtered by status."""
        return {"bugs": [b.to_dict() for b in g.bugs.list(status=status)]}

    def gald3r_bug_update(id: str, status: Optional[str] = None,
                          severity: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Update a bug's status/severity/title."""
        return g.bugs.update(id, status=status, severity=severity, title=title).to_dict()

    # ---- features ----
    def gald3r_feature_new(title: str, priority: Optional[str] = None,
                           status: str = "staging") -> Dict[str, Any]:
        """Stage a feature (status: staging|specced|committed|shipped)."""
        return g.features.create(title=title, priority=priority, status=status).to_dict()

    def gald3r_feature_list(status: Optional[str] = None) -> Dict[str, Any]:
        """List features, optionally filtered by staging status."""
        return {"features": [x.to_dict() for x in g.features.list(status=status)]}

    def gald3r_feature_update(id: str, status: Optional[str] = None,
                              title: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
        """Promote/update a feature."""
        return g.features.update(id, status=status, title=title, priority=priority).to_dict()

    # ---- prds ----
    def gald3r_prd_new(title: str, status: str = "draft") -> Dict[str, Any]:
        """Create a PRD (draft)."""
        return g.prds.create(title=title, status=status).to_dict()

    def gald3r_prd_list(status: Optional[str] = None) -> Dict[str, Any]:
        """List PRDs."""
        return {"prds": [x.to_dict() for x in g.prds.list(status=status)]}

    def gald3r_prd_update(id: str, status: Optional[str] = None,
                          title: Optional[str] = None) -> Dict[str, Any]:
        """Update a PRD (blocked once released/superseded — C-019)."""
        return g.prds.update(id, status=status, title=title).to_dict()

    # ---- ideas ----
    def gald3r_idea_capture(title: str, category: str = "general") -> Dict[str, Any]:
        """Capture an idea to the idea board."""
        return g.ideas.capture(title=title, category=category).to_dict()

    def gald3r_idea_list() -> Dict[str, Any]:
        """List ideas on the board."""
        return {"ideas": [x.to_dict() for x in g.ideas.list()]}

    # ---- vocab ----
    def gald3r_vocab_add(abbr: str, expansion: str, context: str = "") -> Dict[str, Any]:
        """Add/update a project abbreviation."""
        return g.vocab.add(abbr=abbr, expansion=expansion, context=context).to_dict()

    def gald3r_vocab_list() -> Dict[str, Any]:
        """List project abbreviations."""
        return {"vocab": [x.to_dict() for x in g.vocab.list()]}

    # ---- constraints ----
    def gald3r_constraint_add(name: str, scope: str = "project", summary: str = "") -> Dict[str, Any]:
        """Add an active project constraint."""
        return g.constraints.add(name=name, scope=scope, summary=summary).to_dict()

    def gald3r_constraint_list() -> Dict[str, Any]:
        """List project constraints."""
        return {"constraints": [x.to_dict() for x in g.constraints.list()]}

    # ---- subsystems ----
    def gald3r_subsystem_register(name: str, locations: list, owner: str = "") -> Dict[str, Any]:
        """Register a subsystem with its boundary locations."""
        return g.subsystems.register(name=name, locations=locations, owner=owner).to_dict()

    def gald3r_subsystem_list() -> Dict[str, Any]:
        """List registered subsystems."""
        return {"subsystems": [x.to_dict() for x in g.subsystems.list()]}

    # ---- vault ----
    def gald3r_vault_ingest(title: str, type: str, source: str, tags: Optional[list] = None,
                            ingestion_type: str = "manual", body: str = "") -> Dict[str, Any]:
        """Ingest a note into the vault (routed by type); reindexes. tags is canonical."""
        return g.vault.ingest(title=title, type=type, source=source, tags=tags or [],
                              ingestion_type=ingestion_type, body=body).to_dict()

    def gald3r_vault_list(type: Optional[str] = None) -> Dict[str, Any]:
        """List vault notes, optionally filtered by type."""
        return {"notes": [n.to_dict() for n in g.vault.list(type=type)]}

    def gald3r_vault_reindex() -> Dict[str, Any]:
        """Regenerate the vault catalog (_index.yaml + index.md) from note frontmatter."""
        return g.vault.reindex()

    def gald3r_vault_lint() -> Dict[str, Any]:
        """Deterministic vault lint (missing frontmatter, empty tags, legacy topics:)."""
        return {"issues": g.vault.lint()}

    def gald3r_vault_search(query: str, limit: int = 20) -> Dict[str, Any]:
        """Keyword search across vault notes (title/body/tags), ranked by match
        count (T609). Local/offline; semantic embedding search is the cloud RAG layer."""
        return {"results": [n.to_dict() for n in g.vault.search(query, limit=limit)]}

    def gald3r_vault_note_get(path: str) -> Dict[str, Any]:
        """Fetch one vault note as structured JSON (parsed frontmatter `metadata` + `body`)
        by vault-relative path or slug (T609). Returns {"found": false} when no match —
        agents query the note without reading the raw .md file."""
        note = g.vault.note_get(path)
        return note if note is not None else {"found": False, "path": path}

    def gald3r_vault_backlinks(path: str) -> Dict[str, Any]:
        """List vault notes that `[[wikilink]]`-reference the given note (T609), by its
        vault-relative path or slug. Local/offline scan over note bodies."""
        return {"target": path,
                "backlinks": [n.to_dict() for n in g.vault.backlinks(path)]}

    def gald3r_vault_context(budget: int = 8000) -> Dict[str, Any]:
        """Token-budgeted project context block assembled from the vault — newest notes
        first until the budget (~4 chars/token) is hit (T609, the memory_context pattern,
        vault-scoped). Offline; no embedding/model call."""
        return g.vault.context(budget=budget)

    # ---- release ----
    def gald3r_release_new(title: str, version: str, target_date: Optional[str] = None,
                           status: str = "planned") -> Dict[str, Any]:
        """Create a release record (status: planned|in_progress|released|deferred)."""
        return g.release.create(title=title, version=version, target_date=target_date,
                                status=status).to_dict()

    def gald3r_release_list() -> Dict[str, Any]:
        """List release records."""
        return {"releases": [r.to_dict() for r in g.release.list()]}

    def gald3r_release_ship(id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Mark a release shipped (terminal + frozen); optionally stamp final version."""
        return g.release.ship(id, version=version).to_dict()

    def gald3r_release_roadmap() -> Dict[str, Any]:
        """Upcoming (non-terminal) releases ordered by target date, plus next cadence target."""
        return {"upcoming": [r.to_dict() for r in g.release.roadmap()],
                "next_target_date": g.release.next_target_date()}

    # ---- workspace (controller-tier; tools raise below that tier) ----
    def gald3r_workspace_status() -> Dict[str, Any]:
        """Workspace-Control status (active/role/member_count/manifest validity)."""
        return g.workspace.status()

    def gald3r_workspace_validate() -> Dict[str, Any]:
        """Validate the workspace manifest against the single PARSE/VALIDATE contract."""
        errs = g.workspace.validate_manifest()
        return {"valid": not errs, "errors": errs}

    def gald3r_workspace_conflicts() -> Dict[str, Any]:
        """List unresolved CONFLICT inbox items — the WPAC gate (non-empty ⇒ block work)."""
        return {"conflicts": [c.to_dict() for c in g.workspace.conflicts()]}

    def gald3r_workspace_inbox_add(section: str, from_project: str, summary: str) -> Dict[str, Any]:
        """Add an item to the linking INBOX (section: CONFLICT|REQUEST|BROADCAST|SYNC)."""
        return g.workspace.add_item(section, from_project, summary).to_dict()

    # ---- prompts (judgment layer; served, never executed) ----
    def gald3r_prompt_list(kind: Optional[str] = None) -> Dict[str, Any]:
        """List judgment/prompt assets (kind: persona|role|rubric|playbook|voice|rule)."""
        return {"prompts": [a.meta() for a in g.prompts.list(kind=kind)]}

    def gald3r_prompt_get(id: str, inputs: Optional[dict] = None) -> Dict[str, Any]:
        """Fetch a prompt asset's rendered text (binds any ${slot} inputs)."""
        return {"id": id, "text": g.prompts.render(id, **(inputs or {}))}

    # ---- plugins (lifecycle ops over .gald3r_sys/plugins/; T663) ----
    def gald3r_plugin_install(source: str, dry_run: bool = False) -> Dict[str, Any]:
        """Install a plugin from a local source dir (validate manifest+compat, copy
        components, stamp provenance, record installed.yaml). Idempotent; D6 conflict-abort."""
        return g.plugins.install(source, dry_run=dry_run)

    def gald3r_plugin_remove(id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Uninstall a plugin cleanly (ledger + provenance-owned files). Safe on missing."""
        return g.plugins.remove(id, dry_run=dry_run)

    def gald3r_plugin_list() -> Dict[str, Any]:
        """List installed plugins (id, version, source, components, live compat verdict)."""
        return g.plugins.list()

    def gald3r_plugin_new(id: str, name: str = "", author: str = "",
                          subsystem: str = "PLATFORM_INTEGRATION") -> Dict[str, Any]:
        """Scaffold a new plugin skeleton (manifest + CHANGELOG + empty component dirs)."""
        return g.plugins.new(id, name=name, author=author, subsystem=subsystem)

    def gald3r_plugin_check_compat(source: str) -> Dict[str, Any]:
        """Validate a plugin manifest vs schema + host gald3r_min_version floor (pass/fail+reasons)."""
        from gald3r.systems.plugins import PluginError
        try:
            return g.plugins.check_compat(Path(source))
        except PluginError as e:
            return {"ok": False, "id": None, "version": None, "reasons": [str(e)]}

    def gald3r_plugin_update(id: str, source: Optional[str] = None,
                             force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Re-apply/move an installed plugin to a source version (local source; re-materializes)."""
        return g.plugins.update(id, source=source, force=force, dry_run=dry_run)

    # ---- project representative: health + status (T598 Option-A / T608 local half) ----
    def gald3r_project_health() -> Dict[str, Any]:
        """Structured project-health snapshot: task/bug totals + histograms by
        status / priority / severity, and the active-constraint count. Computed
        from the file engine (real-time, no DB needed). The cross-project Throne
        topology map is the cloud half (paused epic)."""
        from collections import Counter
        tasks = g.tasks.list()
        bugs = g.bugs.list()
        return {
            "tasks_total": len(tasks),
            "bugs_total": len(bugs),
            "tasks_by_status": dict(Counter(t.status for t in tasks)),
            "tasks_by_priority": dict(Counter(t.priority for t in tasks)),
            "bugs_by_status": dict(Counter(b.status for b in bugs)),
            "bugs_by_severity": dict(Counter(str(b.fm.get("severity", "")) for b in bugs)),
            "constraints_active": len(g.constraints.list()),
        }

    def gald3r_project_status() -> Dict[str, Any]:
        """Current focus: the in-progress (active) tasks plus pending/awaiting
        counts and the open-bug count — the at-a-glance 'where is this project'."""
        tasks = g.tasks.list()
        active = [t.to_dict() for t in tasks if t.status == "in-progress"]
        return {
            "active_tasks": active,
            "active_count": len(active),
            "pending_count": sum(1 for t in tasks if t.status == "pending"),
            "awaiting_verification_count": sum(
                1 for t in tasks if t.status == "awaiting-verification"
            ),
            "open_bugs": sum(1 for b in g.bugs.list() if b.status in ("open", "in-progress")),
        }

    # ---- coordination visibility (T598 Option-A; surfaces T631/T632 state) ----
    def gald3r_coordinators() -> Dict[str, Any]:
        """Active coordinator sessions on this project — their subsystem scopes,
        tasks-claimed counts, last heartbeat — plus any stale (past-TTL) claims.
        Read-only from `.gald3r/gald3r.db` (T631/T632); empty when no coordinator
        has run. The project-representative view of who is working this project."""
        import sqlite3
        from gald3r import db as _db
        dbf = g.config.gald3r_dir / "gald3r.db"
        if not dbf.exists():
            return {"active": [], "stale_claims": [], "note": "no coordinator has run"}
        conn = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True)
        try:
            return {
                "active": _db.active_coordinators(conn),
                "stale_claims": _db.stale_claims(conn),
            }
        finally:
            conn.close()

    # ---- swarm distributed locks (T610; SQLite backend, replaces file-locks) ----
    def _coord_conn():
        """Open the persistent .gald3r/gald3r.db and ensure the coordination tables."""
        import sqlite3
        from gald3r import db as _db
        conn = sqlite3.connect(str(g.config.gald3r_dir / "gald3r.db"))
        _db.init_coordination_schema(conn)
        return conn

    def gald3r_swarm_lock(bucket_id: str, paths: list, owner: str,
                          ttl_min: int = 30) -> Dict[str, Any]:
        """Claim a set of file paths for a swarm bucket (POST /swarm/lock). Returns
        GRANTED, or LOCK_CONFLICT with the conflicting path + owner. Atomic
        check-and-set with crash-safe TTL expiry (T610; SQLite backend)."""
        from gald3r import db as _db
        conn = _coord_conn()
        try:
            return _db.acquire_swarm_lock(conn, bucket_id, list(paths), owner, ttl_min=ttl_min)
        finally:
            conn.close()

    def gald3r_swarm_unlock(bucket_id: str, owner: Optional[str] = None) -> Dict[str, Any]:
        """Release all paths held by a bucket (DELETE /swarm/lock/{bucket_id})."""
        from gald3r import db as _db
        conn = _coord_conn()
        try:
            return {"released": _db.release_swarm_lock(conn, bucket_id, owner=owner)}
        finally:
            conn.close()

    def gald3r_swarm_locks() -> Dict[str, Any]:
        """List active (non-expired) swarm locks grouped by bucket (GET /swarm/locks).
        Coordinators use this for conflict detection before reconciliation."""
        from gald3r import db as _db
        conn = _coord_conn()
        try:
            return {"locks": _db.list_swarm_locks(conn)}
        finally:
            conn.close()

    # ---- session state (T601 — agent memory across context resets) ----
    def gald3r_session_set(session_id: str, summary: str = "",
                           state: Optional[dict] = None) -> Dict[str, Any]:
        """Persist a session's 'where I left off' state (survives context resets)."""
        return g.session.set_state(session_id, summary=summary, state=state)

    def gald3r_session_get(session_id: str) -> Dict[str, Any]:
        """Retrieve a session's prior state (null if none)."""
        return {"session": g.session.get_state(session_id)}

    def gald3r_session_recent(limit: int = 5) -> Dict[str, Any]:
        """Most-recent session summaries (newest first)."""
        return {"recent": g.session.recent(limit=limit)}

    def gald3r_session_insight(category: str, topic: str, content: str) -> Dict[str, Any]:
        """Store a structured insight (dedup'd by category|topic|content)."""
        return g.session.add_insight(category, topic, content)

    def gald3r_session_delete(session_id: str) -> Dict[str, Any]:
        """Delete a session's state (cleanup after task completion)."""
        return {"deleted": g.session.delete_state(session_id)}

    return {
        "gald3r_session_set": gald3r_session_set,
        "gald3r_session_get": gald3r_session_get,
        "gald3r_session_recent": gald3r_session_recent,
        "gald3r_session_insight": gald3r_session_insight,
        "gald3r_session_delete": gald3r_session_delete,
        "gald3r_project_health": gald3r_project_health,
        "gald3r_project_status": gald3r_project_status,
        "gald3r_coordinators": gald3r_coordinators,
        "gald3r_swarm_lock": gald3r_swarm_lock,
        "gald3r_swarm_unlock": gald3r_swarm_unlock,
        "gald3r_swarm_locks": gald3r_swarm_locks,
        "gald3r_task_new": gald3r_task_new,
        "gald3r_task_list": gald3r_task_list,
        "gald3r_task_update": gald3r_task_update,
        "gald3r_task_set_release_hold": gald3r_task_set_release_hold,
        "gald3r_task_clear_release_hold": gald3r_task_clear_release_hold,
        "gald3r_task_sync": gald3r_task_sync,
        "gald3r_goal_add": gald3r_goal_add,
        "gald3r_goal_list": gald3r_goal_list,
        "gald3r_bug_new": gald3r_bug_new,
        "gald3r_bug_list": gald3r_bug_list,
        "gald3r_bug_update": gald3r_bug_update,
        "gald3r_feature_new": gald3r_feature_new,
        "gald3r_feature_list": gald3r_feature_list,
        "gald3r_feature_update": gald3r_feature_update,
        "gald3r_prd_new": gald3r_prd_new,
        "gald3r_prd_list": gald3r_prd_list,
        "gald3r_prd_update": gald3r_prd_update,
        "gald3r_idea_capture": gald3r_idea_capture,
        "gald3r_idea_list": gald3r_idea_list,
        "gald3r_vocab_add": gald3r_vocab_add,
        "gald3r_vocab_list": gald3r_vocab_list,
        "gald3r_constraint_add": gald3r_constraint_add,
        "gald3r_constraint_list": gald3r_constraint_list,
        "gald3r_subsystem_register": gald3r_subsystem_register,
        "gald3r_subsystem_list": gald3r_subsystem_list,
        "gald3r_vault_ingest": gald3r_vault_ingest,
        "gald3r_vault_list": gald3r_vault_list,
        "gald3r_vault_reindex": gald3r_vault_reindex,
        "gald3r_vault_lint": gald3r_vault_lint,
        "gald3r_vault_search": gald3r_vault_search,
        "gald3r_vault_note_get": gald3r_vault_note_get,
        "gald3r_vault_backlinks": gald3r_vault_backlinks,
        "gald3r_vault_context": gald3r_vault_context,
        "gald3r_release_new": gald3r_release_new,
        "gald3r_release_list": gald3r_release_list,
        "gald3r_release_ship": gald3r_release_ship,
        "gald3r_release_roadmap": gald3r_release_roadmap,
        "gald3r_workspace_status": gald3r_workspace_status,
        "gald3r_workspace_validate": gald3r_workspace_validate,
        "gald3r_workspace_conflicts": gald3r_workspace_conflicts,
        "gald3r_workspace_inbox_add": gald3r_workspace_inbox_add,
        "gald3r_prompt_list": gald3r_prompt_list,
        "gald3r_prompt_get": gald3r_prompt_get,
        "gald3r_plugin_install": gald3r_plugin_install,
        "gald3r_plugin_remove": gald3r_plugin_remove,
        "gald3r_plugin_list": gald3r_plugin_list,
        "gald3r_plugin_new": gald3r_plugin_new,
        "gald3r_plugin_check_compat": gald3r_plugin_check_compat,
        "gald3r_plugin_update": gald3r_plugin_update,
    }


def build_server(root: Optional[Path] = None):
    """Build a FastMCP server registering the task tools. Requires the `mcp` extra."""
    from mcp.server.fastmcp import FastMCP  # lazy import (optional dependency)

    g = Gald3r(root=root)
    server = FastMCP("gald3r")
    for name, fn in tool_impls(g).items():
        server.add_tool(fn, name=name, description=(fn.__doc__ or "").strip())
    return server


def run(root: Optional[Path] = None) -> None:
    build_server(root=root).run()  # stdio transport
