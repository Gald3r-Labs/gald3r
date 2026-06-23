"""Health check — `gald3r doctor`. Absorbs the deterministic, read-only half of
custom_scripts/gald3r_system_test.ps1.

Runs per-system integrity probes and reports a PASS/PARTIAL/FAIL/SKIP per group plus an
overall "N% functional" score. Pure Mode-A: **read-only** (never mutates state — it
recomputes the phantom/orphan integrity that `sync()` would, without writing) and contains
none of the script's impure checks (git hooks, subprocess parity, random byte sampling) —
those belong to the maintainer script / caller, not the engine.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Probe = Tuple[str, str, str]  # (check_name, status: pass|fail|skip, detail)


def _num(v: Any) -> Optional[int]:
    """First integer in an id (handles int task ids and 'BUG-001'-style string ids)."""
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


class DoctorSystem:
    def __init__(self, g):
        self.g = g
        self.cfg = g.config

    # ---- probe groups -------------------------------------------------------
    def _structure(self) -> List[Probe]:
        gd = self.cfg.gald3r_dir
        checks: List[Probe] = []
        for label, p in [("`.gald3r/` present", gd),
                         ("tasks dir", self.cfg.tasks_dir),
                         ("TASKS.md index", self.cfg.tasks_md),
                         ("BUGS.md index", gd / "BUGS.md")]:
            checks.append((label, "pass" if p.exists() else "fail",
                           "" if p.exists() else f"missing: {p.name}"))
        return checks

    def _integrity(self, system, index_path: Path, id_re: str, prefix: str) -> List[Probe]:
        """Read-only phantom/orphan check for an index-backed system."""
        if not index_path.exists():
            return [(f"{prefix} index present", "skip", f"no {index_path.name}")]
        try:
            live = {n for it in system.list() if (n := _num(getattr(it, "id", None))) is not None}
        except Exception as e:  # a system that can't list is itself a finding
            return [(f"{prefix} listable", "fail", f"list() failed: {e}")]
        text = index_path.read_text(encoding="utf-8", errors="replace")
        # Match the engine's own reconciliation (_table._index_ref_ids): ignore only the
        # "## Next <X> ID:" counter HEADING (it names the not-yet-created id). Anchored to a
        # heading so a table row / title that merely mentions an id (e.g. a bug titled
        # "...'Next Bug ID'...") is still counted — otherwise it reads as a false orphan.
        body = "\n".join(ln for ln in text.splitlines()
                         if not re.match(r"\s*#+\s*Next\b.*\bID\b", ln))
        referenced = {int(m) for m in re.findall(id_re, body)}
        phantom = sorted(referenced - live)   # in index, no file
        orphan = sorted(live - referenced)    # file, not in index
        return [
            (f"{prefix} no phantom rows", "pass" if not phantom else "fail",
             "" if not phantom else f"{len(phantom)} indexed id(s) have no file: {phantom[:5]}"),
            (f"{prefix} no orphan files", "pass" if not orphan else "fail",
             "" if not orphan else f"{len(orphan)} file(s) missing from index: {orphan[:5]}"),
        ]

    def _skills(self) -> List[Probe]:
        root = next((self.cfg.root / d / "skills" for d in (".gald3r_sys", ".claude", ".cursor")
                     if (self.cfg.root / d / "skills").is_dir()), None)
        if root is None:
            return [("skills present", "skip", "no skills/ dir found")]
        skill_files = list(root.rglob("SKILL.md"))
        if not skill_files:
            return [("skills present", "skip", "no SKILL.md files")]
        malformed = []
        for sf in skill_files:
            head = "\n".join(sf.read_text(encoding="utf-8", errors="replace").splitlines()[:15])
            if not (re.search(r"(?m)^name:\s*\S", head) and re.search(r"(?m)^description:\s*\S", head)):
                malformed.append(sf.parent.name)
        return [
            ("skills discoverable", "pass", f"{len(skill_files)} SKILL.md under {root.name}/skills"),
            ("skills have name+description", "pass" if not malformed else "fail",
             "" if not malformed else f"{len(malformed)} malformed: {malformed[:5]}"),
        ]

    def _encoding(self) -> List[Probe]:
        """Every non-ASCII .ps1 must carry a UTF-8 BOM, or Windows PowerShell 5.1
        (powershell.exe) misreads it as cp1252 and fails to parse."""
        skip = {".venv", "__pycache__", "site-packages", ".git", "node_modules"}
        ps1 = [p for p in self.cfg.root.rglob("*.ps1")
               if not any(part in skip for part in p.parts)]
        if not ps1:
            return [("ps1 present", "skip", "no .ps1 files")]
        hazards = []
        for p in ps1:
            data = p.read_bytes()
            if not data.startswith(b"\xef\xbb\xbf") and any(b > 0x7F for b in data):
                hazards.append(str(p.relative_to(self.cfg.root)).replace("\\", "/"))
        return [("ps1 BOM-safe for PowerShell 5.1", "pass" if not hazards else "fail",
                 "" if not hazards else
                 f"{len(hazards)} non-ASCII .ps1 lack a UTF-8 BOM: {hazards[:5]}")]

    def _coordinators(self) -> List[Probe]:
        """T631/T632: surface active coordinator sessions + stale claims (read-only).

        Opens `.gald3r/gald3r.db` in read-only mode so doctor never mutates state.
        Skips cleanly when no coordinator has ever run (no db / no claim tables).
        """
        import sqlite3
        from gald3r import db as _db
        dbf = self.cfg.gald3r_dir / "gald3r.db"
        if not dbf.exists():
            return [("coordinator sessions", "skip",
                     "no .gald3r/gald3r.db (no coordinator has run)")]
        try:
            conn = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True)
            active = _db.active_coordinators(conn)
            stale = _db.stale_claims(conn)
            conn.close()
        except sqlite3.OperationalError:
            return [("coordinator sessions", "skip",
                     "gald3r.db predates the T631 claim tables")]
        except Exception as e:  # noqa: BLE001 - doctor must never crash on a probe
            return [("coordinator sessions", "fail", f"db read failed: {e}")]
        summary = (", ".join(
            f"{a['coordinator_id']}[{a['subsystem_scope']}]x{a['tasks_claimed']}"
            for a in active) if active else "0 active")
        probes: List[Probe] = [("coordinator sessions readable", "pass", summary)]
        probes.append(("no stale claims", "pass" if not stale else "fail",
                       "none" if not stale else
                       f"{len(stale)} past-expiry claim(s): {stale[:5]}"))
        return probes

    # ---- public API ---------------------------------------------------------
    def check(self, only: Optional[List[str]] = None) -> Dict[str, Any]:
        groups: Dict[str, List[Probe]] = {
            "structure": self._structure(),
            "tasks": self._integrity(self.g.tasks, self.cfg.tasks_md, r"\bT(\d+)\b", "task"),
            "bugs": self._integrity(self.g.bugs, self.cfg.gald3r_dir / "BUGS.md",
                                    r"\bBUG-(\d+)\b", "bug"),
            "skills": self._skills(),
            "encoding": self._encoding(),
            "coordinators": self._coordinators(),
        }
        if only:
            groups = {k: v for k, v in groups.items() if k in only}

        systems_out, scores = [], []
        for name, probes in groups.items():
            passed = sum(1 for _, s, _ in probes if s == "pass")
            failed = sum(1 for _, s, _ in probes if s == "fail")
            skipped = sum(1 for _, s, _ in probes if s == "skip")
            denom = passed + failed
            score = None if denom == 0 else round(passed / denom * 100)
            status = ("SKIP" if denom == 0 else "PASS" if failed == 0
                      else "FAIL" if passed == 0 else "PARTIAL")
            if score is not None:
                scores.append(score)
            systems_out.append({
                "name": name, "status": status, "score": score,
                "passed": passed, "failed": failed, "skipped": skipped,
                "failures": [f"{c}: {d}" for c, s, d in probes if s == "fail"],
                "checks": [{"check": c, "status": s, "detail": d} for c, s, d in probes],
            })
        overall = round(sum(scores) / len(scores)) if scores else 0
        return {
            "overall_score": overall,
            "systems_passing": sum(1 for s in systems_out if s["status"] == "PASS"),
            "systems_tested": sum(1 for s in systems_out if s["status"] != "SKIP"),
            "systems": systems_out,
        }
