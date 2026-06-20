"""TaskSystem — the task state machine over `.gald3r/tasks/` + `TASKS.md`.

Pure Mode-A logic: deterministic file operations, no LLM calls, no host assumptions.
Reproduces the behavior of the markdown `g-skl-tasks` / `g-task-*` / `g-agnt-task-manager`
surface against the existing on-disk formats.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.ids import new_uuid
from gald3r.schema import task as T
from gald3r.store import Store


@dataclass
class Task:
    id: int
    title: str
    type: str = "feature"
    status: str = "pending"
    priority: str = "medium"
    created_date: str = ""
    body: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    path: Optional[Path] = None

    @property
    def marker(self) -> str:
        return T.marker_for(self.status)

    @property
    def folder(self) -> str:
        return T.folder_for(self.status)

    def to_frontmatter(self) -> Dict[str, Any]:
        fm: Dict[str, Any] = {
            "id": self.id, "title": self.title, "type": self.type,
            "status": self.status, "priority": self.priority,
            "created_date": self.created_date,
        }
        fm.update(self.extra)
        fm.setdefault("schema_version", T.SCHEMA_VERSION)
        return fm

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "type": self.type,
            "status": self.status, "priority": self.priority,
            "created_date": self.created_date, "marker": self.marker,
            "folder": self.folder, **self.extra,
        }


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return (s or "task")[:40]


def _coerce_id(value) -> int:
    """Task ids are ints, but a few migrated files carry a legacy `T###` string id
    (T521). Tolerate both — extract the integer — instead of crashing `task list`."""
    if isinstance(value, int):
        return value
    m = re.search(r"\d+", str(value))
    if not m:
        raise ValueError(f"task id has no integer component: {value!r}")
    return int(m.group())


class TaskSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)

    # ---- file <-> Task ----
    def _task_files(self) -> List[Path]:
        d = self.cfg.tasks_dir
        return sorted(p for p in d.rglob("task*.md")) if d.exists() else []

    def _load(self, path: Path) -> Optional[Task]:
        try:
            fm, body = self.store.read_doc(path)
        except Exception:
            # Malformed YAML frontmatter must not crash `task list` for the whole store
            # (T521). Skip it here; `gald3r validate` reports it as a violation to repair.
            return None
        if "id" not in fm:
            return None
        known = {"id", "title", "type", "status", "priority", "created_date"}
        extra = {k: v for k, v in fm.items() if k not in known and k != "schema_version"}
        return Task(
            id=_coerce_id(fm["id"]), title=str(fm.get("title", "")),
            type=str(fm.get("type", "feature")), status=str(fm.get("status", "pending")),
            priority=str(fm.get("priority", "medium")),
            created_date=str(fm.get("created_date", "")),
            body=body.strip(), extra=extra, path=path,
        )

    def _all(self) -> List[Task]:
        out = []
        for p in self._task_files():
            t = self._load(p)
            if t:
                out.append(t)
        return sorted(out, key=lambda t: t.id)

    def _path_for(self, t: Task) -> Path:
        return self.cfg.tasks_dir / t.folder / f"task{t.id:03d}_{_slug(t.title)}.md"

    def _write(self, t: Task) -> Task:
        new_path = self._path_for(t)
        # if the task already exists elsewhere (status/title change), remove the old file
        if t.path and Path(t.path) != new_path:
            self.store.remove(t.path)
        self.store.write_doc(new_path, t.to_frontmatter(), t.body or self._default_body(t))
        t.path = new_path
        return t

    @staticmethod
    def _default_body(t: Task) -> str:
        return (
            f"## Description\n{t.title}\n\n"
            f"## Acceptance Criteria\n- [ ] TODO\n\n"
            f"## Status History\n"
            f"| Timestamp | From | To | Message |\n|---|---|---|---|\n"
            f"| {t.created_date} | — | {t.status} | created |\n"
        )

    # ---- ids ----
    def _next_id(self) -> int:
        ids = [t.id for t in self._all()]
        return (max(ids) + 1) if ids else 1

    # ---- public API ----
    def create(self, title: str, type: str = "feature", priority: str = "medium",
               status: str = "pending", created_date: Optional[str] = None,
               body: str = "", **extra: Any) -> Task:
        extra.setdefault("uuid", new_uuid())  # stable cross-project primary key (T522)
        t = Task(
            id=self._next_id(), title=title, type=type, priority=priority,
            status=status, created_date=created_date or date.today().isoformat(),
            body=body, extra=extra,
        )
        errs = T.validate(t.to_frontmatter())
        if errs:
            raise ValueError("invalid task: " + "; ".join(errs))
        self._write(t)
        self.sync()
        return t

    def get(self, task_id: int) -> Optional[Task]:
        for t in self._all():
            if t.id == task_id:
                return t
        return None

    def list(self, status: Optional[str] = None) -> List[Task]:
        tasks = self._all()
        return [t for t in tasks if t.status == status] if status else tasks

    def update(self, task_id: int, **changes: Any) -> Task:
        t = self.get(task_id)
        if not t:
            raise KeyError(f"task {task_id} not found")
        for k in ("title", "type", "status", "priority", "body"):
            if k in changes and changes[k] is not None:
                setattr(t, k, changes.pop(k))
        t.extra.update({k: v for k, v in changes.items() if v is not None})
        errs = T.validate(t.to_frontmatter())
        if errs:
            raise ValueError("invalid task: " + "; ".join(errs))
        self._write(t)
        self.sync()
        return t

    def claim(self, task_id: int, owner: str) -> Task:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self.update(task_id, status="in-progress", status_changed=ts, worktree_owner=owner)

    def set_release_hold(self, task_id: int, hold: str, reason: str = "",
                         sync_with: Optional[List[Dict[str, Any]]] = None) -> Task:
        """Set the release-staging hold (T419). hold ∈ {none, manual, sync_required}.
        `sync_with` is a list of {project, task, reason} dicts, only meaningful for
        sync_required. Setting hold='none' is equivalent to clear_release_hold."""
        if hold not in T.RELEASE_HOLD_VALUES:
            raise ValueError(f"release_hold must be one of {T.RELEASE_HOLD_VALUES}")
        if hold == "none":
            return self.clear_release_hold(task_id)
        t = self.get(task_id)
        if not t:
            raise KeyError(f"task {task_id} not found")
        t.extra["release_hold"] = hold
        if reason:
            t.extra["release_hold_reason"] = reason
        if hold == "sync_required" and sync_with:
            t.extra["sync_with"] = sync_with
        errs = T.validate(t.to_frontmatter())
        if errs:
            raise ValueError("invalid task: " + "; ".join(errs))
        self._write(t)
        self.sync()
        return t

    def clear_release_hold(self, task_id: int) -> Task:
        """Clear the release-staging hold (T419) — removes release_hold, its reason,
        and any sync_with list. Equivalent to release_hold: none."""
        t = self.get(task_id)
        if not t:
            raise KeyError(f"task {task_id} not found")
        for k in ("release_hold", "release_hold_reason", "sync_with"):
            t.extra.pop(k, None)
        self._write(t)
        self.sync()
        return t

    def delete(self, task_id: int) -> bool:
        t = self.get(task_id)
        if not t:
            return False
        self.store.remove(t.path)
        self.sync()
        return True

    # ---- sync / index ----
    # T521 decision: TASKS.md is owned by custom_scripts/regenerate_tasks_md.ps1 (lossless,
    # link-format). The engine renders its own TASKS.md only for fresh/test projects; it must
    # NOT clobber a PS1-generated index (the split-brain the task calls out).
    _PS1_TASKS_MARKER = "AUTO-GENERATED by custom_scripts/regenerate_tasks_md"
    _ENGINE_TASKS_MARKER = 'schema_version: "TASKS-md-v1"'

    def _index_is_externally_owned(self, text: str) -> bool:
        if not text.strip():
            return False
        if self._ENGINE_TASKS_MARKER in text:
            return False  # engine-generated -> safe to regenerate
        return self._PS1_TASKS_MARKER in text  # PS1 generator owns it -> preserve

    def sync(self) -> Dict[str, Any]:
        tasks = self._all()
        ids = {t.id for t in tasks}
        old = self.store.read_text(self.cfg.tasks_md)
        # tolerate BOTH index formats: engine `**T123**` and the PS1 `[123](tasks/…)` link
        referenced = {int(m) for m in re.findall(r"\bT(\d+)\b", old)}
        referenced |= {int(m) for m in re.findall(r"\[(\d+)\]\(tasks/", old)}
        phantom = sorted(referenced - ids)   # in index, no file
        orphan = sorted(ids - referenced)    # file, not in index (pre-regen)
        if self._index_is_externally_owned(old):
            return {"tasks": len(ids), "phantom": phantom, "orphan": orphan,
                    "index_preserved": True,
                    "warning": ("TASKS.md is generated by custom_scripts/regenerate_tasks_md.ps1; "
                                "engine left it untouched (T521). Run that script to regenerate.")}
        self.store.write_text(self.cfg.tasks_md, self._render(tasks))
        return {"tasks": len(ids), "phantom": phantom, "orphan": orphan}

    def _render(self, tasks: List[Task]) -> str:
        active = [t for t in tasks if t.status not in T.TERMINAL]
        done = [t for t in tasks if t.status in T.TERMINAL]
        today = date.today().isoformat()
        name = self.cfg.project_name

        def rows(ts: List[Task]) -> str:
            if not ts:
                return "*(none)*"
            return "\n".join(
                f"- [{t.marker}] **T{t.id}** {t.title} ({t.priority})" for t in sorted(ts, key=lambda x: x.id)
            )

        return f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "TASKS-md-v1"
---
# TASKS.md — {name}

**Project**: {name}
**Plan**: `PLAN.md`
**Project overview**: `PROJECT.md`
**Constraints**: `CONSTRAINTS.md`
**Bugs**: `BUGS.md`
**Subsystems**: `SUBSYSTEMS.md`

---

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Pending (no task file yet) — CODING BLOCKED
- `[📋]` = Task file created, ready to start
- `[📝]` = Spec being written (TTL: 1 hour)
- `[🔄]` = In Progress (claimed by agent, has TTL)
- `[🔍]` = Awaiting Verification (impl done, reviewer pending — different agent required)
- `[🕵️]` = Verification In Progress (claimed by verifier, has TTL; YAML: `verification-in-progress`)
- `[⏳]` = Resource-Gated (waiting on GPU/storage/API credits/external service)
- `[✅]` = Completed (verified by different agent)
- `[❌]` = Failed/Cancelled
- `[⏸️]` = Paused

---

## Task backlog (sequential IDs)

{rows(active)}

---

## Completed Tasks
*(Tasks moved here when fully verified)*

{rows(done)}

---

**Last Updated**: {today}
**Open Tasks**: {len(active)}
**Overall Progress**: {len(done)} completed / {len(tasks)} total
"""
