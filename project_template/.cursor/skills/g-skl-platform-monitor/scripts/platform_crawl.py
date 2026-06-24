#!/usr/bin/env python3
"""platform_crawl.py — host-side crawl exporter (T646): the freshness-loop PRODUCER.

This is the missing **host-side** producer the T514 ``spec_refresh.py`` and T515
``generate_status.py`` consumers read from. Those two consumers are pure file
writers that read their inputs from two JSON exports (C-001 parity — there is no
live per-request DB session on the host); the exporter that WRITES those exports
did not exist in-tree (``scripts/platform_crawl.py`` is referenced throughout the
crawl pipeline — ``platform_crawl_trigger`` returns "Run the crawl host-side:
scripts/platform_crawl.py" — but was never authored). This closes that loop so the
freshness pipeline runs end-to-end without a hand-built JSON.

It produces the SAME two shapes the backend MCP tools emit (so the consumers, the
MCP tools, and this exporter can never drift):

  * ``--crawl-snapshot`` — a ``platform_docs_search`` dump of the per-platform
    crawled-doc corpus, shaped::

        {"results": [{"content": ..., "title": ..., "url": ..., "platform": ...}, ...]}

    sourced READ-ONLY from ``platform_ext.memory_captures`` (subject =
    ``platform_docs``; ``title`` / ``url`` / ``platform`` read from the JSONB
    ``metadata`` column). This is the exact result-row shape
    ``platform_docs_search.execute`` builds.

  * ``--crawl-ledger`` — a ``platform_crawl_status`` registry dump, shaped::

        {"registry": [{"platform": ..., "last_crawled_at": ...,
                       "pages_count": ..., "crawl_status": ...}, ...]}

    sourced READ-ONLY from ``platform_ext.platform_docs_crawl_registry``. This is
    the exact registry-row shape ``platform_crawl_status.execute`` builds (and the
    shape ``platform_spec_io.load_crawl_ledger`` parses).

SOURCE MODES (C-001 parity — no per-request backend tenant session here):

  * ``--source db`` (default when ``--db-url`` / ``GALD3R_DATABASE_URL`` is set):
    read the crawl tables directly over a host-side SQLAlchemy connection. This is
    a plain, read-only host connection to the shared corpus — NOT the backend's
    per-request multi-tenant session. SQLAlchemy is imported lazily so the script
    compiles and the sample path runs with zero non-stdlib dependencies.

  * ``--source sample`` (or ``--dry-run``): emit a small, self-contained, non-empty
    fixture snapshot + ledger for at least one platform WITHOUT a live DB. This is
    the smoke-test / offline path the AC requires; the fixture is clearly named
    sample data, not fabricated production rows.

The exporter is **deterministic and model-free** (g-rl-37 "Model for Judgment
Only"): it is pure SQL/JSON plumbing — no LLM is consulted to shape, route, or
filter anything.

Usage::

    # offline smoke test (no DB): write both JSON exports from sample data
    python platform_crawl.py --source sample \
        --crawl-snapshot snap.json --crawl-ledger ledger.json

    # snapshot for one platform only (the spec_refresh --crawl-snapshot input)
    python platform_crawl.py --source sample --platform cursor \
        --crawl-snapshot cursor_docs.json

    # live host-side DB export (read-only) of the real corpus + registry
    python platform_crawl.py --source db --db-url "$GALD3R_DATABASE_URL" \
        --crawl-snapshot snap.json --crawl-ledger ledger.json
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Subject key for the shared platform-docs corpus in platform_ext.memory_captures
# (parity with platform_docs_search.RAG_SUBJECT — keep these in lockstep).
RAG_SUBJECT = "platform_docs"

# Schema the crawl tables live in (alembic 0018_platform_ext_docs_crawl).
SCHEMA = "platform_ext"

# Sample data for the offline smoke-test path. Deliberately small, clearly sample
# (not fabricated production rows), and non-empty for at least one platform so the
# AC's "smoke test produces a non-empty snapshot" check passes without a live DB.
# The doc text positively evidences the gald3r primitives so the spec_refresh
# consumer derives a meaningful (non-empty) signal end-to-end.
_SAMPLE_DOCS: Dict[str, List[Dict[str, str]]] = {
    "cursor": [
        {
            "content": (
                "Cursor supports lifecycle hooks via hooks.json (sessionStart, "
                "preToolUse, PostToolUse). Rules live in .cursor/rules and AGENTS.md. "
                "SKILL.md agent skills and custom slash commands are supported. "
                "MCP servers are configured via mcp.json."
            ),
            "title": "Cursor — Hooks, Rules, Skills, Commands, MCP",
            "url": "https://docs.cursor.com/configuration",
        },
    ],
    "claude": [
        {
            "content": (
                "Claude Code supports hooks (PreToolUse/PostToolUse/SessionStart) via "
                "settings.json, rules through CLAUDE.md, agent skills (SKILL.md), "
                "slash commands, and MCP servers (mcpServers)."
            ),
            "title": "Claude Code — capabilities overview",
            "url": "https://docs.anthropic.com/claude-code",
        },
    ],
    "gemini": [
        {
            "content": (
                "Gemini CLI supports settings.json lifecycle hooks, GEMINI.md memory, "
                "TOML custom commands, markdown subagents, SKILL.md agent skills, and "
                "MCP servers."
            ),
            "title": "Gemini CLI — configuration",
            "url": "https://ai.google.dev/gemini-api/docs",
        },
    ],
}

# Sample crawl-ledger registry (parity with the 0018 seed rows). Uses the registry
# platform keys (claude -> claude_code, as the backend registry stores them).
_SAMPLE_REGISTRY: List[Dict[str, object]] = [
    {
        "platform": "cursor",
        "last_crawled_at": "2026-06-21T08:30:00+00:00",
        "pages_count": 42,
        "crawl_status": "success",
    },
    {
        "platform": "claude_code",
        "last_crawled_at": "2026-06-20T11:00:00+00:00",
        "pages_count": 37,
        "crawl_status": "success",
    },
    {
        "platform": "gemini",
        "last_crawled_at": None,
        "pages_count": 0,
        "crawl_status": "never",
    },
]


# --------------------------------------------------------------------------- #
# Snapshot row shaping (shared by both source modes)                          #
# --------------------------------------------------------------------------- #
def _snapshot_row(content: str, title: str, url: str, platform: str) -> Dict[str, str]:
    """Shape one crawled-doc chunk into a ``platform_docs_search`` result row.

    Mirrors ``platform_docs_search.execute`` exactly so the snapshot the consumers
    read is byte-for-byte the same shape the MCP tool returns. ``similarity`` is
    omitted (it is a per-query score the freshness consumers do not read).

    Args:
        content: The crawled doc chunk text.
        title: The doc title (from metadata, may be empty).
        url: The source URL (from metadata, may be empty).
        platform: The platform key (from metadata, may be empty).

    Returns:
        A dict with ``content`` / ``title`` / ``url`` / ``platform`` keys.
    """
    return {
        "content": content or "",
        "title": title or "",
        "url": url or "",
        "platform": platform or "",
    }


# --------------------------------------------------------------------------- #
# Sample source (offline smoke-test path — no DB)                             #
# --------------------------------------------------------------------------- #
def sample_snapshot(platform: Optional[str]) -> Dict[str, List[Dict[str, str]]]:
    """Build a non-empty sample ``{"results": [...]}`` snapshot offline.

    Args:
        platform: Restrict to one platform key, or None for the whole sample corpus.

    Returns:
        A ``platform_docs_search``-shaped snapshot dict.
    """
    results: List[Dict[str, str]] = []
    for plat, docs in _SAMPLE_DOCS.items():
        if platform and plat != platform.strip().lower():
            continue
        for d in docs:
            results.append(_snapshot_row(d["content"], d["title"], d["url"], plat))
    return {"results": results}


def sample_ledger(platform: Optional[str]) -> Dict[str, List[Dict[str, object]]]:
    """Build a sample ``{"registry": [...]}`` ledger offline.

    Args:
        platform: Restrict to one registry platform key, or None for all rows.

    Returns:
        A ``platform_crawl_status``-shaped ledger dict.
    """
    want = platform.strip().lower() if platform else None
    rows = [
        dict(r) for r in _SAMPLE_REGISTRY
        if want is None or str(r["platform"]).lower() == want
    ]
    return {"registry": rows}


# --------------------------------------------------------------------------- #
# DB source (live host-side read-only export)                                 #
# --------------------------------------------------------------------------- #
def _connect(db_url: str):
    """Open a read-only host-side SQLAlchemy connection (lazy import).

    SQLAlchemy is imported here, not at module import time, so the sample path and
    ``--help`` work with zero non-stdlib dependencies (the AC's offline smoke test
    must not require a DB driver). C-001 parity: this is a plain host connection to
    the SHARED corpus, never the backend's per-request multi-tenant session.

    Args:
        db_url: A SQLAlchemy/psycopg connection URL.

    Returns:
        A live SQLAlchemy ``Engine``.

    Raises:
        RuntimeError: If SQLAlchemy is not installed.
    """
    try:
        from sqlalchemy import create_engine
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "SQLAlchemy is required for --source db; install it or use "
            "--source sample for the offline path."
        ) from exc
    # future=True for SQLAlchemy 2.0 semantics; the export is read-only.
    return create_engine(db_url, future=True)


def db_snapshot(db_url: str, platform: Optional[str]) -> Dict[str, List[Dict[str, str]]]:
    """Export the per-platform crawled-doc snapshot from ``memory_captures`` (read-only).

    Reads subject = ``platform_docs`` chunks and pulls ``title`` / ``url`` /
    ``platform`` from the JSONB ``metadata`` column, shaping each row exactly like
    ``platform_docs_search.execute`` does.

    Args:
        db_url: A SQLAlchemy/psycopg connection URL.
        platform: Optional platform-key filter (matches ``metadata->>'platform'``).

    Returns:
        A ``platform_docs_search``-shaped snapshot dict.
    """
    from sqlalchemy import text

    sql = (
        "SELECT content, "
        "metadata->>'title'  AS title, "
        "metadata->>'url'    AS url, "
        "metadata->>'platform' AS platform "
        f"FROM {SCHEMA}.memory_captures "
        "WHERE subject = :subject"
    )
    params: Dict[str, object] = {"subject": RAG_SUBJECT}
    if platform:
        sql += " AND metadata->>'platform' = :platform"
        params["platform"] = platform.strip().lower()
    sql += " ORDER BY id"

    engine = _connect(db_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
    finally:
        engine.dispose()

    results = [
        _snapshot_row(r["content"], r["title"], r["url"], r["platform"])
        for r in rows
    ]
    return {"results": results}


def db_ledger(db_url: str, platform: Optional[str]) -> Dict[str, List[Dict[str, object]]]:
    """Export the crawl-ledger registry from ``platform_docs_crawl_registry`` (read-only).

    Shapes each row exactly like ``platform_crawl_status.execute`` does
    (``last_crawled_at`` as an ISO string or None).

    Args:
        db_url: A SQLAlchemy/psycopg connection URL.
        platform: Optional registry-platform filter.

    Returns:
        A ``platform_crawl_status``-shaped ledger dict.
    """
    from sqlalchemy import text

    sql = (
        "SELECT platform, last_crawled_at, pages_count, crawl_status "
        f"FROM {SCHEMA}.platform_docs_crawl_registry"
    )
    params: Dict[str, object] = {}
    if platform:
        sql += " WHERE platform = :platform"
        params["platform"] = platform.strip().lower()
    sql += " ORDER BY platform"

    engine = _connect(db_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
    finally:
        engine.dispose()

    registry: List[Dict[str, object]] = []
    for r in rows:
        last = r["last_crawled_at"]
        registry.append(
            {
                "platform": r["platform"],
                "last_crawled_at": last.isoformat() if last is not None else None,
                "pages_count": int(r["pages_count"] or 0),
                "crawl_status": r["crawl_status"] or "never",
            }
        )
    return {"registry": registry}


# --------------------------------------------------------------------------- #
# Export orchestration                                                        #
# --------------------------------------------------------------------------- #
def export(
    source: str,
    db_url: Optional[str],
    platform: Optional[str],
    snapshot_path: Optional[Path],
    ledger_path: Optional[Path],
) -> dict:
    """Write the requested JSON export(s) and return a small report dict.

    Args:
        source: ``"db"`` or ``"sample"``.
        db_url: Connection URL (required when ``source == "db"``).
        platform: Optional single-platform filter for both exports.
        snapshot_path: Where to write the ``--crawl-snapshot`` JSON (or None to skip).
        ledger_path: Where to write the ``--crawl-ledger`` JSON (or None to skip).

    Returns:
        ``{"snapshot": {path, results}, "ledger": {path, registry}}`` (each present
        only when written).

    Raises:
        ValueError: If neither output path is given, or ``source == "db"`` with no URL.
    """
    if snapshot_path is None and ledger_path is None:
        raise ValueError(
            "Nothing to export: pass --crawl-snapshot and/or --crawl-ledger."
        )
    if source == "db" and not db_url:
        raise ValueError(
            "--source db requires --db-url or GALD3R_DATABASE_URL."
        )

    report: dict = {}
    if snapshot_path is not None:
        snap = (
            db_snapshot(db_url, platform) if source == "db"
            else sample_snapshot(platform)
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report["snapshot"] = {
            "path": str(snapshot_path),
            "results": len(snap["results"]),
        }
    if ledger_path is not None:
        led = (
            db_ledger(db_url, platform) if source == "db"
            else sample_ledger(platform)
        )
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            json.dumps(led, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report["ledger"] = {
            "path": str(ledger_path),
            "registry": len(led["registry"]),
        }
    return report


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for the host-side crawl exporter."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="T646: host-side crawl exporter — write the platform_docs "
                    "snapshot + crawl-ledger JSON the T514/T515 freshness "
                    "consumers read (read-only over the crawl tables; "
                    "C-001 parity, no per-request backend session).",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--source", dest="source", choices=["db", "sample"], default=None,
        help="Where to read from: 'db' (live host-side read-only) or 'sample' "
             "(offline fixture). Defaults to 'db' when a --db-url/env URL is "
             "present, else 'sample'.",
    )
    parser.add_argument(
        "--db-url", dest="db_url", default=None,
        help="SQLAlchemy/psycopg connection URL for --source db "
             "(falls back to GALD3R_DATABASE_URL / DATABASE_URL).",
    )
    parser.add_argument(
        "--platform", dest="platform", default=None,
        help="Restrict both exports to one platform key (e.g. cursor, claude_code).",
    )
    parser.add_argument(
        "--crawl-snapshot", dest="snapshot", default=None,
        help="Output path for the platform_docs_search snapshot JSON "
             "({'results': [...]}) — the spec_refresh --crawl-snapshot input.",
    )
    parser.add_argument(
        "--crawl-ledger", dest="ledger", default=None,
        help="Output path for the platform_crawl_status ledger JSON "
             "({'registry': [...]}) — the --crawl-ledger input for both consumers.",
    )
    parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Alias for --source sample (offline fixture export, no DB).",
    )
    args = parser.parse_args(argv)

    db_url = (
        args.db_url
        or os.environ.get("GALD3R_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if args.dry_run:
        source = "sample"
    elif args.source:
        source = args.source
    else:
        source = "db" if db_url else "sample"

    snapshot_path = Path(args.snapshot) if args.snapshot else None
    ledger_path = Path(args.ledger) if args.ledger else None

    try:
        report = export(source, db_url, args.platform, snapshot_path, ledger_path)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - surface DB/driver errors honestly
        print(f"ERROR: export failed ({type(exc).__name__}): {exc}")
        return 1

    print(f"\n=== platform_crawl export (T646) — source={source} ===")
    if "snapshot" in report:
        s = report["snapshot"]
        print(f"  snapshot : {s['path']} ({s['results']} results)")
    if "ledger" in report:
        l = report["ledger"]
        print(f"  ledger   : {l['path']} ({l['registry']} registry rows)")
    if source == "sample":
        print("  NOTE: sample/offline data (not a live crawl); use --source db "
              "with --db-url for the real corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
