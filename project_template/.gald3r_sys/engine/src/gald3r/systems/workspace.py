"""WorkspaceSystem — cross-project coordination over `.gald3r/linking/`.

The deterministic core of the WPAC / Workspace-Control subsystem (`g-skl-wpac-*`,
`g-skl-workspace`, `g-rl-36`), in code. It does the three things the workspace
review (`reviews/REVIEW_workspace_system.md`) found were *sound in concept but broken
in wiring*:

  1. **topology** — read/update this project's place in the ecosystem
     (`linking/topology.md`; falls back to the runtime's `link_topology.md` /
     `PROJECT_TOPOLOGY.md` so it edits the file that actually ships);
  2. **inbox** — the WPAC INBOX + the CONFLICT gate (`linking/INBOX.md`). The review's
     headline defect was that the gate keyed off `.gald3r/workspace/topology.md`, a
     folder that never exists, so it could never fire. Here it keys off the file that
     does exist, so `has_conflicts()` actually works;
  3. **manifest** — the authoritative Workspace-Control VALIDATE
     (`linking/workspace_manifest.yaml`). The review found *two validators, two
     contracts* (the hook checked 6 top-level keys; the skill's deep VALIDATE checked
     more, and would reject the shipped stub). This is the one contract, in one place.

Controller-tier (the facade gate refuses it below `controller`). Read/validate-heavy:
it never rewrites the hand-authored manifest YAML. No LLM calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from gald3r.config import Config
from gald3r.store import Store

ROLES = ["parent", "child", "standalone", "sibling-only"]
INBOX_SECTIONS = ["CONFLICT", "REQUEST", "BROADCAST", "SYNC", "RESOLVED"]
_TOPOLOGY_NAMES = ["topology.md", "link_topology.md", "PROJECT_TOPOLOGY.md"]
# Workspace-Control manifest contract (PARSE_MANIFEST / VALIDATE in g-skl-workspace).
_MANIFEST_TOP_KEYS = ["schema", "workspace", "repositories", "controlled_members",
                      "routing_policy", "wpac_relationship"]
_MANIFEST_WORKSPACE_KEYS = ["id", "display_name", "lifecycle_status",
                            "owner_repository_id", "bootstrap_member_ids"]


@dataclass
class InboxItem:
    section: str
    done: bool
    text: str
    date: str = ""
    from_project: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"section": self.section, "done": self.done, "date": self.date,
                "from_project": self.from_project, "summary": self.summary, "text": self.text}


class WorkspaceSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.dir = config.gald3r_dir / "linking"

    # ============================ topology ============================

    def _topology_path(self) -> Path:
        for name in _TOPOLOGY_NAMES:
            p = self.dir / name
            if p.exists():
                return p
        return self.dir / "topology.md"          # canonical name when creating fresh

    def read_topology(self) -> Dict[str, Any]:
        p = self._topology_path()
        if not p.exists():
            return {"project_name": self.cfg.project_name, "role": "standalone",
                    "parent": None, "children": [], "siblings": []}
        fm, _ = self.store.read_doc(p)
        fm.setdefault("role", "standalone")
        fm.setdefault("children", [])
        fm.setdefault("siblings", [])
        return fm

    def set_role(self, role: str) -> Dict[str, Any]:
        if role not in ROLES:
            raise ValueError(f"role must be one of {ROLES}")
        return self._update_topology(role=role)

    def add_child(self, project_name: str, project_path: str = "", project_id: str = "") -> Dict[str, Any]:
        return self._append_relation("children", project_name, project_path, project_id, role="parent")

    def add_sibling(self, project_name: str, project_path: str = "", project_id: str = "") -> Dict[str, Any]:
        return self._append_relation("siblings", project_name, project_path, project_id)

    def set_parent(self, project_name: str, project_path: str = "", project_id: str = "") -> Dict[str, Any]:
        parent = {"project_name": project_name, "project_path": project_path, "project_id": project_id}
        return self._update_topology(parent=parent, role="child")

    def _append_relation(self, key: str, project_name: str, project_path: str,
                         project_id: str, role: Optional[str] = None) -> Dict[str, Any]:
        fm = self.read_topology()
        rel = list(fm.get(key) or [])
        if any((r.get("project_name") if isinstance(r, dict) else r) == project_name for r in rel):
            raise ValueError(f"{project_name} already in {key}")
        rel.append({"project_name": project_name, "project_path": project_path,
                    "project_id": project_id})
        changes: Dict[str, Any] = {key: rel}
        if role:
            changes["role"] = role
        return self._update_topology(**changes)

    def _update_topology(self, **changes: Any) -> Dict[str, Any]:
        p = self._topology_path()
        if p.exists():
            fm, body = self.store.read_doc(p)
        else:
            fm, body = self._topology_default_fm(), "# Topology — {}\n".format(self.cfg.project_name)
        fm.update(changes)
        fm["last_updated"] = date.today().isoformat()
        self._write_doc_yaml(p, fm, body)
        return fm

    def _topology_default_fm(self) -> Dict[str, Any]:
        return {"project_id": self.cfg.identity.get("project_id", ""),
                "project_name": self.cfg.project_name,
                "role": "standalone", "parent": None, "children": [], "siblings": []}

    def _write_doc_yaml(self, path: Path, fm: Dict[str, Any], body: str) -> None:
        """Write a doc whose frontmatter may be nested (topology) — uses yaml.safe_dump
        rather than Store.emit_frontmatter (which is flat-key only)."""
        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                               default_flow_style=False).rstrip()
        self.store.write_text(path, f"---\n{front}\n---\n\n{body.strip()}\n")

    # ============================= inbox =============================

    def _inbox_path(self) -> Path:
        return self.dir / "INBOX.md"

    def _inbox_text(self) -> str:
        t = self.store.read_text(self._inbox_path())
        return t if t.strip() else self._inbox_scaffold()

    @staticmethod
    def _parse_item(section: str, line: str) -> Optional[InboxItem]:
        m = re.match(r"^- \[( |x|X)\]\s*(.*)$", line.strip())
        if not m:
            return None
        done = m.group(1).lower() == "x"
        rest = m.group(2).strip()
        parts = [c.strip() for c in rest.split("|")]
        if len(parts) >= 3:
            return InboxItem(section=section, done=done, text=rest,
                             date=parts[0], from_project=parts[1], summary="|".join(parts[2:]).strip())
        return InboxItem(section=section, done=done, text=rest, summary=rest)

    def list_items(self, section: Optional[str] = None) -> List[InboxItem]:
        items: List[InboxItem] = []
        cur = None
        for line in self._inbox_text().splitlines():
            hm = re.match(r"^##\s*\[([A-Z]+)\]", line)
            if hm:
                cur = hm.group(1)
                continue
            if cur and (section is None or cur == section):
                it = self._parse_item(cur, line)
                if it:
                    items.append(it)
        return items

    def conflicts(self) -> List[InboxItem]:
        """Unresolved CONFLICT items — the WPAC gate. Non-empty ⇒ block session work."""
        return [it for it in self.list_items("CONFLICT") if not it.done]

    def has_conflicts(self) -> bool:
        return bool(self.conflicts())

    def add_item(self, section: str, from_project: str, summary: str,
                 when: Optional[str] = None) -> InboxItem:
        section = section.upper()
        if section not in INBOX_SECTIONS:
            raise ValueError(f"section must be one of {INBOX_SECTIONS}")
        stamp = when or date.today().isoformat()
        line = f"- [ ] {stamp} | {from_project} | {summary}"
        self._insert_under_section(section, line)
        return InboxItem(section=section, done=False, text=line.split("] ", 1)[1],
                         date=stamp, from_project=from_project, summary=summary)

    def resolve(self, summary_fragment: str, resolution: str,
                when: Optional[str] = None) -> InboxItem:
        """Mark the first matching unresolved item done and archive it under [RESOLVED]."""
        stamp = when or date.today().isoformat()
        lines = self._inbox_text().splitlines()
        cur = None
        target_idx = None
        target = None
        for i, line in enumerate(lines):
            hm = re.match(r"^##\s*\[([A-Z]+)\]", line)
            if hm:
                cur = hm.group(1)
                continue
            if cur and cur != "RESOLVED":
                it = self._parse_item(cur, line)
                if it and not it.done and summary_fragment.lower() in it.text.lower():
                    target_idx, target = i, it
                    break
        if target_idx is None:
            raise KeyError(f"no unresolved inbox item matching {summary_fragment!r}")
        archived = f"- [x] {target.text} → {resolution} {stamp}"
        del lines[target_idx]
        text = self._insert_into("RESOLVED", "\n".join(lines), archived)
        self.store.write_text(self._inbox_path(), text if text.endswith("\n") else text + "\n")
        target.done = True
        return target

    def _insert_under_section(self, section: str, line: str) -> None:
        text = self._insert_into(section, self._inbox_text(), line)
        self.store.write_text(self._inbox_path(), text if text.endswith("\n") else text + "\n")

    @staticmethod
    def _insert_into(section: str, text: str, line: str) -> str:
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            hm = re.match(r"^##\s*\[([A-Z]+)\]", ln)
            if hm and hm.group(1) == section:
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("<!--"):
                    j += 1
                lines.insert(j, line)
                return "\n".join(lines)
        # section missing — append it
        lines += [f"\n## [{section}]", line]
        return "\n".join(lines)

    def _inbox_scaffold(self) -> str:
        return f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "generic-v1"
---
# INBOX — {self.cfg.project_name}

> Managed by `g-skl-wpac-read`. Session-start hook checks this file automatically.
> CONFLICT items block session work until resolved.

## [CONFLICT] — Items That Block Work

## [REQUEST] — Incoming Asks From Children

## [BROADCAST] — Orders From Parent

## [SYNC] — Peer Contract Updates From Siblings

## [RESOLVED] — Archive
"""

    # ============================ manifest ============================

    def _manifest_path(self) -> Path:
        return self.dir / "workspace_manifest.yaml"

    def read_manifest(self) -> Optional[Dict[str, Any]]:
        p = self._manifest_path()
        if not p.exists():
            return None
        data = yaml.safe_load(self.store.read_text(p))
        return data if isinstance(data, dict) else None

    def validate_manifest(self) -> List[str]:
        """The single authoritative Workspace-Control VALIDATE. Returns [] when valid."""
        m = self.read_manifest()
        if m is None:
            return ["no workspace_manifest.yaml found"]
        errs: List[str] = []
        for k in _MANIFEST_TOP_KEYS:
            if k not in m:
                errs.append(f"missing top-level key: {k}")
        ws = m.get("workspace")
        if not isinstance(ws, dict):
            errs.append("workspace block missing or not a mapping")
        else:
            for k in _MANIFEST_WORKSPACE_KEYS:
                if k not in ws:
                    errs.append(f"missing workspace.{k}")
            sot = ws.get("source_of_truth")
            if not isinstance(sot, dict) or "canonical_machine_registry" not in sot:
                errs.append("missing workspace.source_of_truth.canonical_machine_registry")
        return errs

    def member_list(self) -> List[Any]:
        m = self.read_manifest() or {}
        cm = m.get("controlled_members") or {}
        ids = cm.get("repository_ids") if isinstance(cm, dict) else None
        if ids:
            return list(ids)
        repos = m.get("repositories")
        return list(repos) if isinstance(repos, list) else []

    def status(self) -> Dict[str, Any]:
        m = self.read_manifest()
        if m is None:
            return {"active": False, "role": "standalone", "member_count": 0,
                    "valid": False, "summary": "no manifest — current repository only"}
        members = self.member_list()
        rel = m.get("wpac_relationship") or {}
        role = rel.get("role", "standalone") if isinstance(rel, dict) else "standalone"
        errs = self.validate_manifest()
        active = bool(members) or role != "standalone"
        return {
            "active": active, "role": role, "member_count": len(members),
            "valid": not errs, "errors": errs,
            "summary": (f"{role}: {len(members)} member(s)" if active
                        else "inactive / current repository only"),
        }
