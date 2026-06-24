"""T639 Phase-3 — read-only DuckDB analytics projection over the SQLite snapshot.

Columnar OLAP layer for reporting ONLY. It reads from the T597 SQLite snapshot
(`build_snapshot` -> `.gald3r/gald3r.db`) and exposes analytic views — burn-down,
velocity, coordinator throughput, and a cross-project portfolio roll-up.

STRICTLY READ-ONLY (master plan §9 Q4):
  * It NEVER writes to the SQLite snapshot or the markdown files.
  * It is NEVER on a claim / transaction / id-assignment path — those are SQLite
    (T631) / PostgreSQL (T631) row-level atomic writes; columnar storage is the
    wrong tool for them and is deliberately kept off that path.
  * The DuckDB database itself is in-memory by default (an on-demand, disposable
    projection refreshed from SQLite), so there is no durable analytics write path.

DuckDB is an OPTIONAL dependency (`pip install gald3r[analytics]`). The import is
gated: when duckdb is absent the engine's pure Mode-A core still runs, and any
attempt to use this projection raises a clean, actionable error instead of an
ImportError traceback.

@subsystems: TASK_MANAGEMENT
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

try:  # gated optional import — keep the pure core dependency-free
    import duckdb as _duckdb
    _HAVE_DUCKDB = True
except ImportError:  # pragma: no cover - exercised only when duckdb is absent
    _duckdb = None  # type: ignore[assignment]
    _HAVE_DUCKDB = False

_MISSING_MSG = (
    "DuckDB analytics projection requires the optional 'duckdb' dependency. "
    "Install it with:  uv add duckdb   (or:  pip install gald3r[analytics]). "
    "The rest of the engine runs without it."
)

# The SQLite snapshot tables this read-only projection reads from. tasks/bugs/features
# carry completed_date (used for burn-down + velocity); coordinator_sessions/task_claims
# back coordinator throughput. All are read-only here.
_PROJECTED_TABLES = (
    "tasks", "bugs", "features",
    "coordinator_sessions", "task_claims",
)

ProjectSource = Union[str, Path, Tuple[str, Union[str, Path]]]


def duckdb_available() -> bool:
    """True when the optional `duckdb` package is importable."""
    return _HAVE_DUCKDB


def _require_duckdb() -> None:
    if not _HAVE_DUCKDB:
        raise RuntimeError(_MISSING_MSG)


def _normalize_sources(sources: Sequence[ProjectSource]) -> List[Tuple[str, str]]:
    """Coerce mixed source specs into [(project_id, sqlite_path), ...].

    Each source is either a bare SQLite path (project_id derived from the file's
    parent-of-`.gald3r` / file stem) or an explicit `(project_id, path)` tuple.
    """
    out: List[Tuple[str, str]] = []
    for i, src in enumerate(sources):
        if isinstance(src, tuple):
            pid, path = src
            out.append((str(pid), str(Path(path))))
        else:
            p = Path(src)
            # Derive a stable id: the project dir name (parent of `.gald3r`) when the
            # snapshot lives at `.gald3r/<db>`, else the file stem; de-dup by index.
            if p.parent.name == ".gald3r":
                pid = p.parent.parent.name or p.stem
            else:
                pid = p.stem
            out.append((pid or f"project_{i}", str(p)))
    return out


class DuckDBProjection:
    """An on-demand, read-only DuckDB view over one or more SQLite snapshots.

    Build with :meth:`from_sqlite_paths` (the snapshot file path(s) produced by
    `build_snapshot(..., db_path=...)`). The projection ATTACHes each SQLite db
    read-only and unions its tables with a `project_id` column, so the same view
    methods serve a single project and the cross-project portfolio.
    """

    def __init__(self, con: "_duckdb.DuckDBPyConnection", project_ids: List[str]):
        self._con = con
        self._project_ids = project_ids

    # ---- construction ----
    @classmethod
    def from_sqlite_paths(cls, sources: Sequence[ProjectSource]) -> "DuckDBProjection":
        """Build a read-only projection from one or more SQLite snapshot files.

        `sources` is a sequence of snapshot paths or `(project_id, path)` tuples.
        Each snapshot is attached READ_ONLY; the projection's tables are unioned
        across all of them, tagged with `project_id`.
        """
        _require_duckdb()
        if not sources:
            raise ValueError("at least one SQLite snapshot source is required")
        norm = _normalize_sources(sources)
        for _pid, path in norm:
            if not Path(path).exists():
                raise FileNotFoundError(f"SQLite snapshot not found: {path}")

        con = _duckdb.connect(database=":memory:")
        con.execute("INSTALL sqlite; LOAD sqlite;")
        union_parts: Dict[str, List[str]] = {t: [] for t in _PROJECTED_TABLES}
        for idx, (pid, path) in enumerate(norm):
            alias = f"src{idx}"
            # READ_ONLY attach — the projection can never write back to the snapshot.
            con.execute(f"ATTACH '{path}' AS {alias} (TYPE sqlite, READ_ONLY);")
            # DuckDB surfaces an attached catalog's tables via information_schema, not
            # the sqlite-side `sqlite_master`. Query the catalog (alias) we just attached.
            present = {
                r[0] for r in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_catalog = ?", [alias],
                ).fetchall()
            }
            for t in _PROJECTED_TABLES:
                if t in present:
                    union_parts[t].append(
                        f"SELECT '{_sql_lit(pid)}' AS project_id, * FROM {alias}.{t}"
                    )

        # Materialize each unioned table as a read-only DuckDB VIEW. Empty tables
        # (no attached source had them) get an empty typed shell so views still resolve.
        for t, parts in union_parts.items():
            if parts:
                con.execute(f"CREATE VIEW v_{t} AS " + " UNION ALL ".join(parts))
            else:
                con.execute(_empty_view_sql(t))
        return cls(con, [pid for pid, _ in norm])

    @classmethod
    def from_sqlite_path(cls, path: Union[str, Path],
                         project_id: Optional[str] = None) -> "DuckDBProjection":
        """Single-project convenience wrapper over :meth:`from_sqlite_paths`."""
        src: ProjectSource = (project_id, path) if project_id else path
        return cls.from_sqlite_paths([src])

    # ---- read-only analytic views ----
    def burndown(self, table: str = "tasks") -> Dict[str, int]:
        """Open vs. done totals (aggregated across all attached projects).

        `done` = items carrying a non-empty completed_date (the same terminal-set-free
        signal the SQLite `burndown` uses), `open` = the remainder.
        """
        self._check_dated_table(table)
        row = self._con.execute(
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN completed_date IS NOT NULL AND completed_date <> '' "
            f"         THEN 1 ELSE 0 END) AS done "
            f"FROM v_{table}"
        ).fetchone()
        total = int(row[0] or 0)
        done = int(row[1] or 0)
        return {"total": total, "done": done, "open": total - done}

    def velocity(self, table: str = "tasks") -> Dict[str, int]:
        """Completed-items-per-day histogram (aggregated across projects).

        Keyed on completed_date (ascending); mirrors the SQLite `velocity_by_date`
        but computed columnar-side and unioned across the portfolio.
        """
        self._check_dated_table(table)
        rows = self._con.execute(
            f"SELECT completed_date, COUNT(*) FROM v_{table} "
            f"WHERE completed_date IS NOT NULL AND completed_date <> '' "
            f"GROUP BY completed_date ORDER BY completed_date"
        ).fetchall()
        return {str(d): int(n) for d, n in rows}

    def coordinator_throughput(self) -> List[Dict[str, object]]:
        """Per-coordinator-session claim throughput (active claim counts).

        Joins coordinator sessions to their task_claims; one row per session with the
        number of tasks currently claimed. Read-only — never modifies a claim.
        """
        rows = self._con.execute(
            "SELECT cs.project_id, cs.session_id, cs.coordinator_id, "
            "       cs.status, COUNT(tc.task_uuid) AS tasks_claimed "
            "FROM v_coordinator_sessions cs "
            "LEFT JOIN v_task_claims tc "
            "  ON tc.project_id = cs.project_id AND tc.session_id = cs.session_id "
            "GROUP BY cs.project_id, cs.session_id, cs.coordinator_id, cs.status "
            "ORDER BY tasks_claimed DESC, cs.session_id"
        ).fetchall()
        return [
            {"project_id": r[0], "session_id": r[1], "coordinator_id": r[2],
             "status": r[3], "tasks_claimed": int(r[4] or 0)}
            for r in rows
        ]

    def portfolio(self) -> List[Dict[str, object]]:
        """Cross-project roll-up: per project_id, task/bug/feature totals + done.

        The portfolio view that the single-project tables cannot give — one row per
        attached project with open vs. done across the three dated doc types.
        """
        rows = self._con.execute(
            """
            WITH t AS (
              SELECT project_id, COUNT(*) AS total,
                     SUM(CASE WHEN completed_date IS NOT NULL AND completed_date <> ''
                              THEN 1 ELSE 0 END) AS done
              FROM v_tasks GROUP BY project_id
            ),
            b AS (
              SELECT project_id, COUNT(*) AS total,
                     SUM(CASE WHEN completed_date IS NOT NULL AND completed_date <> ''
                              THEN 1 ELSE 0 END) AS done
              FROM v_bugs GROUP BY project_id
            ),
            f AS (
              SELECT project_id, COUNT(*) AS total,
                     SUM(CASE WHEN completed_date IS NOT NULL AND completed_date <> ''
                              THEN 1 ELSE 0 END) AS done
              FROM v_features GROUP BY project_id
            ),
            ids AS (
              SELECT project_id FROM t
              UNION SELECT project_id FROM b
              UNION SELECT project_id FROM f
            )
            SELECT ids.project_id,
                   COALESCE(t.total, 0) AS tasks_total,
                   COALESCE(t.done, 0)  AS tasks_done,
                   COALESCE(b.total, 0) AS bugs_total,
                   COALESCE(b.done, 0)  AS bugs_done,
                   COALESCE(f.total, 0) AS features_total,
                   COALESCE(f.done, 0)  AS features_done
            FROM ids
            LEFT JOIN t ON t.project_id = ids.project_id
            LEFT JOIN b ON b.project_id = ids.project_id
            LEFT JOIN f ON f.project_id = ids.project_id
            ORDER BY ids.project_id
            """
        ).fetchall()
        out: List[Dict[str, object]] = []
        for r in rows:
            tasks_total, tasks_done = int(r[1]), int(r[2])
            bugs_total, bugs_done = int(r[3]), int(r[4])
            feat_total, feat_done = int(r[5]), int(r[6])
            out.append({
                "project_id": r[0],
                "tasks_total": tasks_total, "tasks_done": tasks_done,
                "tasks_open": tasks_total - tasks_done,
                "bugs_total": bugs_total, "bugs_done": bugs_done,
                "bugs_open": bugs_total - bugs_done,
                "features_total": feat_total, "features_done": feat_done,
                "features_open": feat_total - feat_done,
            })
        return out

    # ---- housekeeping ----
    @property
    def project_ids(self) -> List[str]:
        return list(self._project_ids)

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "DuckDBProjection":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @staticmethod
    def _check_dated_table(table: str) -> None:
        if table not in ("tasks", "bugs", "features"):
            raise ValueError("table must be one of 'tasks', 'bugs', 'features'")


def _sql_lit(s: str) -> str:
    """Escape a string for a single-quoted SQL literal (project_id tag)."""
    return str(s).replace("'", "''")


def _empty_view_sql(table: str) -> str:
    """An empty, correctly-typed DuckDB view for a table no attached source had.

    Keeps the four analytic queries resolvable even when a snapshot lacks a table
    (e.g. a brand-new project with no features yet).
    """
    cols = {
        "tasks": "project_id, id, title, status, priority, type, uuid, subsystems, "
                 "created_date, completed_date, path, raw",
        "bugs": "project_id, id, title, status, severity, kind, uuid, subsystems, "
                "created_date, completed_date, path, raw",
        "features": "project_id, id, fid, title, status, priority, uuid, subsystems, "
                    "created_date, completed_date, path, raw",
        "coordinator_sessions": "project_id, session_id, project_id2, coordinator_id, "
                                "subsystem_scope, started_at, last_heartbeat, status, "
                                "user_id, username, display_name, machine_id",
        "task_claims": "project_id, task_uuid, session_id, claimed_at, expires_at",
    }[table]
    select = ", ".join(
        f"CAST(NULL AS VARCHAR) AS {c.strip()}" for c in cols.split(",")
    )
    return f"CREATE VIEW v_{table} AS SELECT {select} WHERE 1=0"
