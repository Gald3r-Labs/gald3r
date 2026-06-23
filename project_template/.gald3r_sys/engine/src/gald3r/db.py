"""T597 Phase 1 — read-only SQLite projection of `.gald3r/` task/bug state.

ADDITIVE and purely read-derived: builds a SQLite snapshot FROM the markdown
files (files remain the source of truth — AC "Files remain the source of truth
for template-only offline users"). It powers SQL-based next-id + reporting +
round-trip regeneration WITHOUT touching any file-write path, so it cannot
affect existing behavior. Pure stdlib (sqlite3), no new deps.

Identity (master plan §2): the `uuid` is the real primary key (a UNIQUE partial
index — the key T631 atomic claims key on), and the numeric `id` is a human
display label served from `MAX(id)+1`. `raw` holds the verbatim file text so the
DB can regenerate the canonical file (round-trip fidelity AC).

Later slices (owned elsewhere): Phase 2 world_tree PostgreSQL projection +
atomic claims (T631), Phase 3 DuckDB analytics projection (T639 follow-up).
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY, title TEXT, status TEXT, priority TEXT,
  type TEXT, uuid TEXT, subsystems TEXT, created_date TEXT,
  completed_date TEXT, path TEXT, raw TEXT
);
CREATE TABLE IF NOT EXISTS bugs (
  id INTEGER PRIMARY KEY, title TEXT, status TEXT, severity TEXT,
  kind TEXT, uuid TEXT, subsystems TEXT, created_date TEXT,
  completed_date TEXT, path TEXT, raw TEXT
);
-- UUID is the real primary key (master plan §2): a partial UNIQUE index so it is
-- enforced for every real uuid while tolerating legacy rows that lack one.
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_uuid ON tasks(uuid) WHERE uuid != '';
CREATE UNIQUE INDEX IF NOT EXISTS idx_bugs_uuid  ON bugs(uuid)  WHERE uuid != '';
"""

# T631 — atomic task-claim layer (the ONLY write path in this module). These tables
# live in the same .gald3r/gald3r.db file; SQLite's single-writer lock makes the
# claim atomic for multiple coordinators on one machine (master plan §3.1/§5.1).
# T610 adds swarm_locks — the SQLite backend of the distributed-lock interface that
# replaces the fragile .gald3r-swarm-locks/*.json files (Redis is the team backend).
_COORDINATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS coordinator_sessions (
  session_id TEXT PRIMARY KEY, project_id TEXT, coordinator_id TEXT,
  subsystem_scope TEXT, started_at TEXT, last_heartbeat TEXT, status TEXT,
  user_id TEXT, username TEXT, display_name TEXT, machine_id TEXT  -- T636 developer identity
);
-- task_uuid PRIMARY KEY (the claim key, master plan §2) enforces exactly one claimer.
CREATE TABLE IF NOT EXISTS task_claims (
  task_uuid TEXT PRIMARY KEY, session_id TEXT, claimed_at TEXT, expires_at TEXT
);
-- T610: one row per locked file PATH (path-level conflict detection). A bucket
-- claims a SET of paths; any path held by a different bucket -> LOCK_CONFLICT.
CREATE TABLE IF NOT EXISTS swarm_locks (
  path TEXT PRIMARY KEY, bucket_id TEXT, owner TEXT, locked_at TEXT, expires_at TEXT
);
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """Shallow `key: value` frontmatter parse (tolerant; None when absent)."""
    m = re.match(r"^﻿?---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    fm: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip("\"'")
    return fm


def _int_id(value: object) -> Optional[int]:
    """Coerce an id (int, `123`, or legacy `T123`/`BUG-123`) to int; None if none."""
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else None


def build_snapshot(gald3r_dir: Path, db_path: str = ":memory:") -> sqlite3.Connection:
    """Ingest `.gald3r/tasks` + `.gald3r/bugs` files into a SQLite snapshot.

    Args:
        gald3r_dir: the project's `.gald3r` directory.
        db_path: SQLite path (default in-memory). Files are NOT modified.

    Returns:
        An open sqlite3.Connection populated with the current task/bug state.
    """
    gd = Path(gald3r_dir)
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    init_coordination_schema(conn)  # T631/T610 claim+lock tables (+ T636 col migration)

    tasks_dir = gd / "tasks"
    if tasks_dir.exists():
        for p in tasks_dir.rglob("task*.md"):
            if "inbox" in p.parts:
                continue
            raw = p.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(raw)
            tid = _int_id(fm.get("id")) if fm else None
            if tid is None:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO tasks "
                "(id, title, status, priority, type, uuid, subsystems, "
                " created_date, completed_date, path, raw) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (tid, fm.get("title", ""), fm.get("status", ""),
                 fm.get("priority", ""), fm.get("type", ""),
                 fm.get("uuid", ""), fm.get("subsystems", ""),
                 fm.get("created_date", ""), fm.get("completed_date", ""),
                 str(p), raw),
            )

    bugs_dir = gd / "bugs"
    if bugs_dir.exists():
        for p in bugs_dir.rglob("bug*.md"):
            if "inbox" in p.parts:
                continue
            raw = p.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(raw)
            bid = _int_id(fm.get("id")) if fm else None
            if bid is None:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO bugs "
                "(id, title, status, severity, kind, uuid, subsystems, "
                " created_date, completed_date, path, raw) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (bid, fm.get("title", ""), fm.get("status", ""),
                 fm.get("severity", ""), fm.get("kind", ""),
                 fm.get("uuid", ""), fm.get("subsystems", ""),
                 fm.get("created_date", ""), fm.get("completed_date", ""),
                 str(p), raw),
            )

    conn.commit()
    return conn


def task_by_uuid(conn: sqlite3.Connection, uuid: str) -> Optional[sqlite3.Row]:
    """Look up a task by its UUID (the real PK / claim key, master plan §2)."""
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT * FROM tasks WHERE uuid = ?", (uuid,)).fetchone()


def bug_by_uuid(conn: sqlite3.Connection, uuid: str) -> Optional[sqlite3.Row]:
    """Look up a bug by its UUID."""
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT * FROM bugs WHERE uuid = ?", (uuid,)).fetchone()


def regenerate_file(conn: sqlite3.Connection, table: str, numeric_id: int) -> Optional[str]:
    """Regenerate a file's canonical text from the DB (round-trip fidelity AC).

    The DB stores the verbatim source in `raw`, so regeneration is lossless: the
    DB alone can reproduce the canonical gald3r file for any ingested item.
    """
    if table not in ("tasks", "bugs"):
        raise ValueError("table must be 'tasks' or 'bugs'")
    row = conn.execute(
        f"SELECT raw FROM {table} WHERE id = ?", (numeric_id,)  # noqa: S608 (allowlisted)
    ).fetchone()
    return row[0] if row else None


def velocity_by_date(conn: sqlite3.Connection, table: str = "tasks") -> Dict[str, int]:
    """Completed-items-per-day histogram (velocity AC). Keyed on completed_date."""
    if table not in ("tasks", "bugs"):
        raise ValueError("table must be 'tasks' or 'bugs'")
    return {
        str(d): int(n)
        for d, n in conn.execute(
            f"SELECT completed_date, COUNT(*) FROM {table} "  # noqa: S608 (allowlisted)
            "WHERE completed_date != '' GROUP BY completed_date ORDER BY completed_date"
        ).fetchall()
    }


def burndown(conn: sqlite3.Connection, table: str = "tasks") -> Dict[str, int]:
    """Open vs. done burn-down snapshot (burn-down AC).

    `done` = items carrying a completed_date; `open` = the remainder. Terminal-set
    knowledge is intentionally NOT baked in (completed_date presence is the signal),
    so it never drifts from the status vocabulary.
    """
    if table not in ("tasks", "bugs"):
        raise ValueError("table must be 'tasks' or 'bugs'")
    total = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
    done = int(conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE completed_date != ''"  # noqa: S608
    ).fetchone()[0])
    return {"total": total, "done": done, "open": total - done}


# ── T631: atomic task-claim layer (SQLite — all tiers, single machine) ──────────
# Claims key on the task UUID (master plan §2). The PostgreSQL equivalent (online,
# team tier) mirrors these operations with INSERT ... ON CONFLICT (task_uuid) DO
# NOTHING + SELECT FOR UPDATE; it lives world_tree-side and is gated by T633.

def init_coordination_schema(conn: sqlite3.Connection) -> None:
    """Ensure the coordination tables exist (+ additive T636 column migration)."""
    conn.executescript(_COORDINATION_SCHEMA)
    # Additive migration for pre-existing dbs created before T636 (no data loss).
    cols = {r[1] for r in conn.execute("PRAGMA table_info(coordinator_sessions)").fetchall()}
    for col in ("user_id", "username", "display_name", "machine_id"):
        if col not in cols:
            conn.execute(f"ALTER TABLE coordinator_sessions ADD COLUMN {col} TEXT")
    conn.commit()


def register_coordinator(conn: sqlite3.Connection, session_id: str, coordinator_id: str,
                         subsystem_scope: str = "all", project_id: str = "",
                         user_id: str = "", username: str = "", display_name: str = "",
                         machine_id: str = "", now: Optional[datetime] = None) -> None:
    """Register (or refresh) a coordinator session at startup.

    Developer identity (`user_id`/`username`/`display_name`/`machine_id`, T636) makes a
    session attributable to a person across a team — empty for solo/offline use.
    """
    n = now or _utcnow()
    conn.execute(
        "INSERT OR REPLACE INTO coordinator_sessions "
        "(session_id, project_id, coordinator_id, subsystem_scope, started_at, "
        " last_heartbeat, status, user_id, username, display_name, machine_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, project_id, coordinator_id, subsystem_scope, _iso(n), _iso(n),
         "active", user_id, username, display_name, machine_id),
    )
    conn.commit()


def ping_coordinator(conn: sqlite3.Connection, session_id: str,
                     now: Optional[datetime] = None) -> None:
    """Heartbeat — refresh last_heartbeat (called every ~30s by the outer loop)."""
    conn.execute(
        "UPDATE coordinator_sessions SET last_heartbeat = ? WHERE session_id = ?",
        (_iso(now or _utcnow()), session_id),
    )
    conn.commit()


def complete_coordinator(conn: sqlite3.Connection, session_id: str) -> None:
    """Mark a coordinator session completed on clean exit (releases its scope)."""
    conn.execute(
        "UPDATE coordinator_sessions SET status = 'completed' WHERE session_id = ?",
        (session_id,),
    )
    conn.commit()


def claim_task(conn: sqlite3.Connection, task_uuid: str, session_id: str,
               ttl_min: int = 120, now: Optional[datetime] = None) -> bool:
    """Atomically claim a task by UUID. True on success, False if already held.

    Uses INSERT OR IGNORE (atomic under SQLite's write lock). An EXPIRED claim is
    taken over; a claim already held by the SAME session is idempotently re-granted.
    """
    n = now or _utcnow()
    expires = n + timedelta(minutes=ttl_min)
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO task_claims (task_uuid, session_id, claimed_at, expires_at) "
            "VALUES (?,?,?,?)", (task_uuid, session_id, _iso(n), _iso(expires)),
        )
        if cur.rowcount == 1:
            conn.commit()
            return True
        row = conn.execute(
            "SELECT session_id, expires_at FROM task_claims WHERE task_uuid = ?", (task_uuid,)
        ).fetchone()
        if row is None:
            conn.commit()
            return False
        held_by, exp = row
        if held_by == session_id:
            conn.commit()
            return True  # idempotent re-claim by the owner
        if exp and datetime.fromisoformat(exp) <= n:  # expired -> take over
            conn.execute(
                "UPDATE task_claims SET session_id = ?, claimed_at = ?, expires_at = ? "
                "WHERE task_uuid = ?", (session_id, _iso(n), _iso(expires), task_uuid),
            )
            conn.commit()
            return True
        conn.commit()
        return False
    except Exception:
        conn.rollback()
        raise


def release_task(conn: sqlite3.Connection, task_uuid: str, session_id: str) -> bool:
    """Release a claim on completion or failure. True if a claim was released."""
    cur = conn.execute(
        "DELETE FROM task_claims WHERE task_uuid = ? AND session_id = ?",
        (task_uuid, session_id),
    )
    conn.commit()
    return cur.rowcount > 0


def sweep_stale_claims(conn: sqlite3.Connection, now: Optional[datetime] = None,
                       heartbeat_grace_min: int = 5) -> int:
    """Release expired claims whose owning session's heartbeat is also stale.

    Run at coordinator startup. A claim is stale when `expires_at < now` AND the
    owning session has no heartbeat within `heartbeat_grace_min`. Returns the count.
    """
    n = now or _utcnow()
    cutoff = n - timedelta(minutes=heartbeat_grace_min)
    rows = conn.execute(
        "SELECT tc.task_uuid FROM task_claims tc "
        "LEFT JOIN coordinator_sessions cs ON cs.session_id = tc.session_id "
        "WHERE tc.expires_at < ? AND (cs.last_heartbeat IS NULL OR cs.last_heartbeat < ?)",
        (_iso(n), _iso(cutoff)),
    ).fetchall()
    for (uuid,) in rows:
        conn.execute("DELETE FROM task_claims WHERE task_uuid = ?", (uuid,))
    conn.commit()
    return len(rows)


def active_coordinators(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    """Active coordinator sessions + their claim counts (for `gald3r doctor`)."""
    conn.row_factory = sqlite3.Row
    out: List[Dict[str, object]] = []
    for r in conn.execute(
        "SELECT * FROM coordinator_sessions WHERE status = 'active' ORDER BY started_at"
    ).fetchall():
        claims = int(conn.execute(
            "SELECT COUNT(*) FROM task_claims WHERE session_id = ?", (r["session_id"],)
        ).fetchone()[0])
        out.append({
            "session_id": r["session_id"], "coordinator_id": r["coordinator_id"],
            "subsystem_scope": r["subsystem_scope"], "last_heartbeat": r["last_heartbeat"],
            "tasks_claimed": claims,
            # T636 developer identity (empty for solo/offline sessions).
            "display_name": (r["display_name"] if "display_name" in r.keys() else "") or "",
            "username": r["username"] if "username" in r.keys() else "",
        })
    return out


def request_coordinator_stop(conn: sqlite3.Connection, session_id: str) -> bool:
    """Request graceful shutdown of a coordinator (T636 `--stop`).

    Marks the session `stopping`; the owning coordinator reads this on its next
    heartbeat and exits cleanly, releasing its scope. (Admin-role authorization is
    enforced server-side by world_tree; the engine just records the request.)
    Returns True if an active session was transitioned.
    """
    cur = conn.execute(
        "UPDATE coordinator_sessions SET status = 'stopping' "
        "WHERE session_id = ? AND status = 'active'", (session_id,),
    )
    conn.commit()
    return cur.rowcount > 0


def cross_developer_collision_message(coll: Dict[str, object]) -> str:
    """Format the T636 cross-developer scope-conflict message from a collision dict."""
    return (f"Scope conflict: {coll.get('display_name') or coll.get('coordinator_id')} is "
            f"already running a coordinator on '{coll.get('subsystem_scope')}' "
            f"(since {coll.get('started_at')}).")


def stale_claims(conn: sqlite3.Connection, now: Optional[datetime] = None) -> List[str]:
    """Task UUIDs whose claim is past expiry (for `gald3r doctor` visibility)."""
    n = now or _utcnow()
    return [r[0] for r in conn.execute(
        "SELECT task_uuid FROM task_claims WHERE expires_at < ?", (_iso(n),)
    ).fetchall()]


# ── T632: subsystem partitioning policy (Pro+; count-gated by T633) ─────────────
# Owns scoping + collision detection only. Claim atomicity is delegated to T631
# (SQLite) / T610 (Redis). 'all' is the single-coordinator default scope.

def _scope_set(scope: str) -> set:
    """Parse a coordinator scope into subsystem groups; 'all' -> universal marker."""
    if not scope or scope.strip().lower() == "all":
        return {"__ALL__"}
    return {s.strip() for s in re.split(r"[,\s]+", scope) if s.strip()}


def _scopes_overlap(a: str, b: str) -> bool:
    """Two coordinator scopes collide if either is 'all' or they share a group."""
    sa, sb = _scope_set(a), _scope_set(b)
    if "__ALL__" in sa or "__ALL__" in sb:
        return True
    return bool(sa & sb)


def task_subsystem_set(raw: object) -> set:
    """Parse a task row's `subsystems` field ('[A, B]' or 'A,B') into a group set."""
    s = str(raw or "").strip().strip("[]")
    return {x.strip().strip("\"'") for x in re.split(r"[,\s]+", s) if x.strip()}


def scope_collision(conn: sqlite3.Connection, scope: str) -> Optional[Dict[str, object]]:
    """First ACTIVE coordinator session whose scope overlaps `scope`, else None.

    Cross-coordinator collision check (master plan §6). The lock atomicity itself
    is T631 (SQLite) / T610 (Redis) — this only decides whether two scopes may run.
    """
    conn.row_factory = sqlite3.Row
    for r in conn.execute(
        "SELECT * FROM coordinator_sessions WHERE status = 'active'"
    ).fetchall():
        if _scopes_overlap(scope, r["subsystem_scope"] or "all"):
            return {
                "session_id": r["session_id"], "coordinator_id": r["coordinator_id"],
                "subsystem_scope": r["subsystem_scope"], "started_at": r["started_at"],
                # T636: developer identity, so cross-developer collisions name the person.
                "display_name": (r["display_name"] if "display_name" in r.keys() else "")
                                or r["coordinator_id"],
                "username": r["username"] if "username" in r.keys() else "",
            }
    return None


def tasks_in_scope(conn: sqlite3.Connection, scope: str) -> List[str]:
    """Task UUIDs claimable under `scope`.

    'all' sees everything including the UNSCOPED pool; a specific scope sees only
    tasks whose `subsystems` intersect it (never UNSCOPED — prevents silent
    cross-scope claiming, T632 prerequisite AC).
    """
    universal = "__ALL__" in _scope_set(scope)
    sset = _scope_set(scope)
    out: List[str] = []
    for uuid, subs in conn.execute(
        "SELECT uuid, subsystems FROM tasks WHERE uuid != ''"
    ).fetchall():
        if universal or (task_subsystem_set(subs) & sset):
            out.append(uuid)
    return out


def untagged_tasks(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    """Tasks with no `subsystems` tag — the UNSCOPED pool (only an `--subsystem all`
    coordinator may claim them). Subsystem tag-quality audit (T632 prerequisite AC)."""
    return [
        {"id": r[0], "uuid": r[1]}
        for r in conn.execute(
            "SELECT id, uuid FROM tasks "
            "WHERE subsystems = '' OR subsystems IS NULL OR subsystems = '[]'"
        ).fetchall()
    ]


# ── T633: coordinator-count gate (engine side — offline / free-tier fallback) ───
# The authoritative tier check is world_tree's `can_register_coordinator(project_id,
# user_id)` against the subscription plan. THIS is the local enforcement used when
# world_tree is unreachable (master plan §6: "allow 1 coordinator max — safe default")
# and the mechanism the online check ultimately drives. Client-side; the DB layer
# enforces the limit server-side too.

def can_register_coordinator(conn: sqlite3.Connection, scope: str = "all",
                             max_coordinators: int = 1) -> Dict[str, object]:
    """Decide whether a new coordinator may register (T633).

    Two gates, both must pass:
      1. Count limit — `max_coordinators` active sessions (offline/free default 1;
         online, world_tree supplies the plan's limit: Pro=5, Team=team_size×2).
      2. Scope collision (T632) — even on a paid tier, overlapping scopes are rejected.

    Returns {allowed: bool, reason: str, code: str}. `code` ∈
    {ok, count_limit, scope_conflict}.
    """
    active = active_coordinators(conn)
    if len(active) >= max_coordinators:
        if max_coordinators <= 1:
            reason = ("Multi-coordinator blocked (Free tier). A coordinator is already "
                      "active for this project. Run `gald3r pro upgrade` or visit "
                      "https://gald3r.ai/pro to unlock parallel coordinators.")
        else:
            reason = (f"Coordinator limit reached ({len(active)}/{max_coordinators} for "
                      "this tier).")
        return {"allowed": False, "reason": reason, "code": "count_limit"}
    coll = scope_collision(conn, scope)
    if coll:
        return {
            "allowed": False, "code": "scope_conflict",
            "reason": (f"Scope conflict: an active coordinator owns scope "
                       f"'{coll['subsystem_scope']}'. Choose a non-overlapping subsystem "
                       "or stop the existing coordinator."),
        }
    return {"allowed": True, "reason": "ok", "code": "ok"}


# ── T610: swarm distributed-lock interface — SQLite backend (default, all tiers) ─
# Replaces the fragile `.gald3r-swarm-locks/*.json` files with atomic check-and-set
# + crash-safe TTL expiry. The same interface (acquire/release/list) has a Redis
# backend for multi-machine team/org use, gated by `can_use_redis_coordination`
# (T633/T641); unentitled users fall back to this SQLite backend with no loss on a
# single machine (master plan §5).

def acquire_swarm_lock(conn: sqlite3.Connection, bucket_id: str, paths: List[str],
                       owner: str, ttl_min: int = 30,
                       now: Optional[datetime] = None) -> Dict[str, object]:
    """Atomically claim a set of file paths for a bucket (the `POST /swarm/lock` op).

    Returns {status: 'GRANTED'} or {status: 'LOCK_CONFLICT', path, owner, bucket_id}.
    Expired locks are swept first (crash-safe TTL). A bucket re-locking its own paths
    is idempotent and refreshes the TTL.
    """
    n = now or _utcnow()
    expires = n + timedelta(minutes=ttl_min)
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("DELETE FROM swarm_locks WHERE expires_at < ?", (_iso(n),))  # sweep
        for p in paths:
            row = conn.execute(
                "SELECT bucket_id, owner FROM swarm_locks WHERE path = ?", (p,)
            ).fetchone()
            if row and row[0] != bucket_id:
                conn.rollback()
                return {"status": "LOCK_CONFLICT", "path": p,
                        "owner": row[1], "bucket_id": row[0]}
        for p in paths:  # all clear -> claim/refresh
            conn.execute(
                "INSERT OR REPLACE INTO swarm_locks (path, bucket_id, owner, locked_at, expires_at) "
                "VALUES (?,?,?,?,?)", (p, bucket_id, owner, _iso(n), _iso(expires)),
            )
        conn.commit()
        return {"status": "GRANTED", "bucket_id": bucket_id, "paths": list(paths)}
    except Exception:
        conn.rollback()
        raise


def release_swarm_lock(conn: sqlite3.Connection, bucket_id: str,
                       owner: Optional[str] = None) -> int:
    """Release all paths held by a bucket (the `DELETE /swarm/lock/{bucket_id}` op).

    Returns the number of paths released. If `owner` is given, only that owner's locks.
    """
    if owner is None:
        cur = conn.execute("DELETE FROM swarm_locks WHERE bucket_id = ?", (bucket_id,))
    else:
        cur = conn.execute(
            "DELETE FROM swarm_locks WHERE bucket_id = ? AND owner = ?", (bucket_id, owner)
        )
    conn.commit()
    return cur.rowcount


def list_swarm_locks(conn: sqlite3.Connection,
                     now: Optional[datetime] = None) -> List[Dict[str, object]]:
    """Active (non-expired) locks grouped by bucket (the `GET /swarm/locks` op).

    Coordinators call this for conflict detection before reconciliation.
    """
    n = now or _utcnow()
    buckets: Dict[str, Dict[str, object]] = {}
    for path, bucket_id, owner, exp in conn.execute(
        "SELECT path, bucket_id, owner, expires_at FROM swarm_locks "
        "WHERE expires_at >= ? ORDER BY bucket_id, path", (_iso(n),)
    ).fetchall():
        b = buckets.setdefault(bucket_id, {"bucket_id": bucket_id, "owner": owner,
                                           "expires_at": exp, "paths": []})
        b["paths"].append(path)
    return list(buckets.values())


def next_task_id(conn: sqlite3.Connection) -> int:
    """SQL next task id (AC: `next_task_id` via SQL — no folder scan)."""
    return int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM tasks").fetchone()[0])


def next_bug_id(conn: sqlite3.Connection) -> int:
    """SQL next bug id."""
    return int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM bugs").fetchone()[0])


def counts_by_status(conn: sqlite3.Connection, table: str) -> Dict[str, int]:
    """Status histogram for reporting (AC: counts/burn-down/velocity foundation)."""
    if table not in ("tasks", "bugs"):
        raise ValueError("table must be 'tasks' or 'bugs'")
    return {
        str(s): int(n)
        for s, n in conn.execute(
            f"SELECT status, COUNT(*) FROM {table} GROUP BY status"  # noqa: S608 (fixed allowlist)
        ).fetchall()
    }


def backlog_summary(conn: sqlite3.Connection) -> Dict[str, object]:
    """Aggregate counts for reporting (T597 Phase-1 AC: counts foundation).

    Returns raw status/priority/severity histograms + totals from the projection
    (consumers derive open/burn-down from these — no terminal-set knowledge is
    baked in here, so it never drifts from the T519 status vocabulary).
    """
    def hist(sql: str) -> Dict[str, int]:
        return {str(k): int(v) for k, v in conn.execute(sql).fetchall()}

    return {
        "total_tasks": int(conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]),
        "total_bugs": int(conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]),
        "tasks_by_status": hist("SELECT status, COUNT(*) FROM tasks GROUP BY status"),
        "tasks_by_priority": hist("SELECT priority, COUNT(*) FROM tasks GROUP BY priority"),
        "bugs_by_status": hist("SELECT status, COUNT(*) FROM bugs GROUP BY status"),
        "bugs_by_severity": hist("SELECT severity, COUNT(*) FROM bugs GROUP BY severity"),
    }
