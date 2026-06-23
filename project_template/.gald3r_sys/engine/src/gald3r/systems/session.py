"""SessionSystem (T601) — persistent agent session-state + insights.

An agent's working memory resets every context window. This file-backed store
(under `.gald3r/sessions/`) lets an agent write "where I left off" mid-run and
the next turn/session read it back without re-reading every source file. It is
DISTINCT from the vault (permanent knowledge): this is operational, per-session,
prunable state. Pure Mode-A — stdlib only, no LLM, no network.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(name))[:80] or "session"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SessionSystem:
    """Per-session JSON state + a dedup'd insights log under `.gald3r/sessions/`."""

    def __init__(self, cfg: Config):
        self.cfg = cfg

    @property
    def dir(self) -> Path:
        return self.cfg.gald3r_dir / "sessions"

    @property
    def _insights(self) -> Path:
        return self.dir / "insights.jsonl"

    # ---- session state ----
    def set_state(self, session_id: str, summary: str = "",
                  state: Optional[Dict[str, Any]] = None,
                  now: Optional[str] = None) -> Dict[str, Any]:
        """Write/replace a session's state ('where I left off')."""
        self.dir.mkdir(parents=True, exist_ok=True)
        doc = {"session_id": session_id, "summary": summary,
               "state": state or {}, "updated": now or _now()}
        (self.dir / f"{_safe(session_id)}.json").write_text(
            json.dumps(doc, indent=2), encoding="utf-8")
        return doc

    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        p = self.dir / f"{_safe(session_id)}.json"
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None

    def recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Most-recently-updated session summaries (newest first)."""
        if not self.dir.is_dir():
            return []
        files = sorted(self.dir.glob("*.json"),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        out: List[Dict[str, Any]] = []
        for f in files[:limit]:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            out.append({"session_id": d.get("session_id"),
                        "summary": d.get("summary", ""),
                        "updated": d.get("updated")})
        return out

    def delete_state(self, session_id: str) -> bool:
        p = self.dir / f"{_safe(session_id)}.json"
        if p.is_file():
            p.unlink()
            return True
        return False

    # ---- insights (structured, dedup'd) ----
    def add_insight(self, category: str, topic: str, content: str) -> Dict[str, Any]:
        """Append a structured insight, dedup'd by category|topic|content hash."""
        self.dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(
            f"{category}|{topic}|{content}".encode("utf-8")).hexdigest()[:16]
        if self._insights.is_file():
            for line in self._insights.read_text(encoding="utf-8").splitlines():
                try:
                    if json.loads(line).get("key") == key:
                        return {"deduped": True, "key": key}
                except ValueError:
                    continue
        rec = {"key": key, "category": category, "topic": topic,
               "content": content, "created": _now()}
        with self._insights.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        return {"deduped": False, **rec}

    def list_insights(self) -> List[Dict[str, Any]]:
        if not self._insights.is_file():
            return []
        out: List[Dict[str, Any]] = []
        for line in self._insights.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out
