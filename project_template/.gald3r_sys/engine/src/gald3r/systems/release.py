"""ReleaseSystem — release records over `.gald3r/releases/` + `RELEASES.md`.

A folder-backed system (cloned via `_base.FolderSystem`): each release is
`releases/release{NNN}_{slug}.md`; `RELEASES.md` is the regenerated index table.
Mirrors `g-skl-release` / `g-release-*`. Pure Mode-A (no LLM calls).

Distinguishing traits:
  * a release is **frozen once `released`** (a shipped version is a historical
    record — same C-019 freeze model the PRD system uses);
  * the index carries a SemVer/cadence configuration block;
  * cadence math (`next_target_date`) is deterministic date arithmetic.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from gald3r.config import Config
from gald3r.systems._base import FolderSystem, Item, ItemSpec

_STATUSES = ["planned", "in_progress", "released", "deferred"]
_MARKER = {"planned": "📋", "in_progress": "🔄", "released": "✅", "deferred": "⏸️"}
DEFAULT_CADENCE_DAYS = 14


SPEC = ItemSpec(
    name="release", dir_name="releases", index_name="RELEASES.md", file_prefix="release",
    id_kind="prefix", id_prefix="R-", id_pad=3,
    statuses=_STATUSES,
    status_folder={s: "" for s in _STATUSES},      # flat: releases/releaseNNN_*.md
    status_marker=_MARKER,
    terminal={"released", "deferred"}, default_status="planned",
    required=["id", "title", "status", "version"],
    frozen_statuses={"released"},                  # a shipped release is immutable
)


def _fmt_tasks(it: Item) -> str:
    tasks = it.fm.get("tasks")
    if isinstance(tasks, (list, tuple)):
        return f"{len(tasks)}" if tasks else "0"
    return str(tasks) if tasks not in (None, "") else "0"


def render_index(fs: FolderSystem, items: List[Item]) -> str:
    name = fs.cfg.project_name
    rows = "\n".join(
        f"| {it.id} | {it.fm.get('title','')} | {it.fm.get('version','—')} | "
        f"{it.fm.get('target_date','—')} | {it.status} | {_fmt_tasks(it)} |"
        for it in items
    ) or "| — | — | — | — | — | — |"
    return f"""---
gald3r_rel_version: "{fs.cfg.gald3r_rel_version}"
schema_version: "generic-v1"
---
# RELEASES.md — {name}

<!-- Release index — tracks all planned, active, and shipped releases.
     Individual release details live in releases/release{{NNN}}_{{slug}}.md.
     Cadence default: {DEFAULT_CADENCE_DAYS} days (biweekly). Override per-release in the file's cadence_days field.
     Next release target = most recent target_date + cadence_days. -->

## Configuration

| Setting | Value |
|---------|-------|
| Default cadence | {DEFAULT_CADENCE_DAYS} days |
| Version scheme | SemVer (major.minor.patch) |

## Release Index

| ID | Name | Version | Target Date | Status | Tasks |
|----|------|---------|-------------|--------|-------|
{rows}

<!-- Add releases above this line. Status: planned | in_progress | released | deferred -->

## Notes

- Use `@g-release-status` to view current release state
- Use `@g-release-ship` to mark a release as shipped
- Use `@g-release-roadmap` to generate the public roadmap
- See `releases/README.md` for the full schema reference
"""


class ReleaseSystem(FolderSystem):
    def __init__(self, config: Config):
        super().__init__(config, SPEC, render_index)

    def create(self, title: str, version: str, target_date: Optional[str] = None,
               status: Optional[str] = None, cadence_days: int = DEFAULT_CADENCE_DAYS,
               body: str = "", **fields) -> Item:
        return super().create(title=title, version=version, target_date=target_date,
                              status=status, cadence_days=cadence_days, body=body, **fields)

    def ship(self, release_id, version: Optional[str] = None) -> Item:
        """Mark a release as shipped (terminal + frozen). Optionally stamp the final version."""
        changes = {"status": "released"}
        if version is not None:
            changes["version"] = version
        return self.update(release_id, **changes)

    def roadmap(self) -> List[Item]:
        """Upcoming (non-terminal) releases, ordered by target date then id."""
        upcoming = [it for it in self.list() if it.status not in self.spec.terminal]
        return sorted(upcoming, key=lambda it: (str(it.fm.get("target_date") or "9999-99-99"),
                                                self._num(it.id)))

    def next_target_date(self, cadence_days: Optional[int] = None) -> Optional[str]:
        """Most recent target_date + cadence_days. None if no release carries a target_date."""
        dated = [str(it.fm["target_date"]) for it in self.list() if it.fm.get("target_date")]
        if not dated:
            return None
        latest = max(dated)
        try:
            base = date.fromisoformat(latest)
        except ValueError:
            return None
        return (base + timedelta(days=cadence_days or DEFAULT_CADENCE_DAYS)).isoformat()
