#!/usr/bin/env python3
"""Deterministic per-territory / per-dev drift score (T195 / D15, drift_score_version=1).

Computes a code-only drift score for each claimed task from real, on-disk `.gald3r/`
state -- no model call is ever part of the score. Three signals feed the composite:

  1. **claim_staleness**  -- how far past `claim_expires_at` a task's claim is (the
     `claimed_by`/`claim_expires_at` task-frontmatter pair is the real lease-like
     primitive this repo has today; see the "Territory vs. task-claim" note in
     SKILL.md for why this v1 does NOT key off `g-skl-territory`'s documented
     `territory_leases` table -- that backend was not found anywhere in this repo).
  2. **worktree_staleness** -- age of the matching `.gald3r-worktree.json` marker
     (g-rl-02), halved when `last_checkpoint_sha` differs from `base_sha` (i.e. the
     worktree has made committed progress since it was created).
  3. **uncommitted_footprint** -- `git status --porcelain` file count inside that
     worktree, relative to a configurable cap.

Each signal is normalized to 0-100 and combined with fixed weights into a single
0-100 `drift_score`, then banded (low/medium/high). Records are additionally rolled
up **by territory** (task frontmatter `subsystems:`) and **by dev** (`claimed_by`),
per the task's "per-territory / per-dev" requirement.

Output is either a human-readable text report (default) or a JSON envelope matching
the `g-skl-json-output` convention (`gald3r_version`/`generated_at`/`command`/
`schema`/`data` -- see g-skl-json-output/SKILL.md), so the JSON form is directly
consumable as a local report or as an event payload a future WPAC-v2 transport could
forward to `world_tree` (no such transport is built or invoked here -- out of v1
scope per the task).

Offline-capable, zero DB dependency (C-011): reads only markdown/YAML/JSON files
already on disk plus a `git status` shell-out scoped to a single worktree directory.

Usage:
    uv run python drift_score.py [--root <repo_root>] [--status in-progress ...] [--json]

Exit codes: 0 = no high-band subject · 2 = at least one high-band subject · 1 = usage/IO error.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations
# --- gald3r calltrace bootstrap (T268) -- injected; inert unless gald3r call tracing is
# enabled. Strip everywhere: python scripts/inject_calltrace_bootstrap.py --strip
import os as _g3ct_os
_g3ct_home = _g3ct_os.environ.get("GALD3R_HOME") or _g3ct_os.path.join(
    _g3ct_os.path.expanduser("~"), ".gald3r")
_g3ct_env = (_g3ct_os.environ.get("GALD3R_TRACE_CALLS") or "").strip().lower()
if _g3ct_env not in ("", "0", "off", "false", "no") or _g3ct_os.path.isfile(
        _g3ct_os.path.join(_g3ct_home, "calltrace.json")):
    try:
        _g3ct_bs = _g3ct_os.path.join(_g3ct_home, "calltrace_bootstrap.py")
        if _g3ct_os.path.isfile(_g3ct_bs):
            with open(_g3ct_bs, "r", encoding="utf-8") as _g3ct_fh:
                exec(compile(_g3ct_fh.read(), _g3ct_bs, "exec"),
                     {"__g3ct_script__": __file__,
                      "__name__": "_gald3r_calltrace_exec"})
    except Exception:
        pass
# --- end gald3r calltrace bootstrap ---

import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

DRIFT_SCORE_VERSION = 1

DEFAULT_WEIGHTS: Dict[str, float] = {"claim": 0.5, "worktree": 0.3, "uncommitted": 0.2}
DEFAULT_CAPS: Dict[str, float] = {"claim": 120.0, "worktree": 240.0, "uncommitted": 25.0}
BAND_HIGH = 60.0
BAND_MEDIUM = 25.0


# --------------------------------------------------------------------------- #
# Optional reuse of gald3r_core's real frontmatter/worktree-marker parsers
# (g-rl-04 DRY). Falls back to a small dependency-light parser so this script
# still runs standalone, matching every other neutral_source skill script.
#
# BUG[BUG-531] kind=design_gap: flagged by the new BUG-356
# neutral_source engine-import IP-leak audit (parity_harness.
# KNOWN_ENGINE_IMPORT_EXCEPTIONS currently allowlists this exact path pending
# an owner ruling: ratify these guarded, ImportError-caught dev-convenience
# imports below as permanently allowed, or refactor to always use the
# dependency-light fallback parser instead) -- see draft queued at
# .gald3r/bugs/inbox/bug_bug-356-ip-leak-audit-flags-two-guarded-_d7f2812e.md
# (numeric BUG-NNN id pending coordinator flush at time of writing).
# --------------------------------------------------------------------------- #
def _bootstrap_gald3r_core() -> bool:
    try:
        import gald3r_core.project.gald3r_integration.local_ops_parsing  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / "src"
        if (cand / "gald3r_core" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r_core.project.gald3r_integration.local_ops_parsing  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_CORE = _bootstrap_gald3r_core()

_core_parse_frontmatter = None
_core_read_worktree_metadata = None
if _HAS_CORE:
    try:
        from gald3r_core.project.gald3r_integration.local_ops_parsing import (
            parse_frontmatter as _core_parse_frontmatter,
        )
    except ImportError:
        _core_parse_frontmatter = None
    try:
        from gald3r_core.core.worktree.manifest import read_metadata as _core_read_worktree_metadata
    except ImportError:
        _core_read_worktree_metadata = None


_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LIST_RE = re.compile(r"^\[(.*)\]$")


def _fallback_parse_frontmatter(text: str) -> Dict[str, Any]:
    """Minimal `key: value` / `key: [a, b]` YAML-frontmatter reader (no yaml dep)."""
    m = _FM_RE.match(text.lstrip("﻿"))
    if not m:
        return {}
    out: Dict[str, Any] = {}
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        lm = _LIST_RE.match(val)
        if lm:
            items = [i.strip().strip("'\"") for i in lm.group(1).split(",") if i.strip()]
            out[key] = items
        else:
            out[key] = val.strip("'\"")
    return out


def _read_frontmatter(text: str) -> Dict[str, Any]:
    if _core_parse_frontmatter is not None:
        try:
            return dict(_core_parse_frontmatter(text))
        except Exception:
            pass
    return _fallback_parse_frontmatter(text)


def _read_worktree_marker(path: Path) -> Optional[Dict[str, Any]]:
    if _core_read_worktree_metadata is not None:
        try:
            data = _core_read_worktree_metadata(path)
            if data:
                return dict(data)
        except Exception:
            pass
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Project-root / version discovery (matches g-skl-json-output's json_output.py)
# --------------------------------------------------------------------------- #
def _find_root(start: Optional[Path] = None) -> Path:
    here = (start or Path.cwd()).resolve()
    d = here
    while not (d / ".gald3r").exists():
        if d.parent == d:
            break
        d = d.parent
    return d


def _read_gald3r_version(root: Path) -> str:
    idf = root / ".gald3r" / ".identity"
    if idf.is_file():
        for line in idf.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*gald3r_version=(.+)$", line)
            if m:
                return m.group(1).strip()
    return "unknown"


def _parse_iso8601(value: Any) -> Optional[datetime]:
    if not value:
        return None
    s = str(value).strip().strip("'\"")
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# --------------------------------------------------------------------------- #
# Task-file discovery + frontmatter extraction
# --------------------------------------------------------------------------- #
def iter_task_files(root: Path, statuses: Sequence[str]) -> List[Path]:
    base = root / ".gald3r" / "tasks"
    if not base.is_dir():
        return []
    if "all" in statuses:
        dirs = [d for d in sorted(base.iterdir()) if d.is_dir()]
    else:
        dirs = [base / s for s in statuses if (base / s).is_dir()]
    out: List[Path] = []
    for d in dirs:
        out.extend(sorted(p for p in d.rglob("*.md") if p.is_file()))
    return out


def _normalize_task_id(raw: Any) -> Optional[str]:
    if raw in (None, ""):
        return None
    s = str(raw).strip()
    return s if s.upper().startswith("T") else f"T{s}"


def parse_task_frontmatter(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = _read_frontmatter(text)
    subsystems = fm.get("subsystems") or fm.get("subsystem_memberships") or []
    if isinstance(subsystems, str):
        subsystems = [subsystems]
    territory = ", ".join(str(s) for s in subsystems) if subsystems else None
    claimed_by = fm.get("claimed_by") or None
    if isinstance(claimed_by, str) and not claimed_by.strip():
        claimed_by = None
    return {
        "task_id": _normalize_task_id(fm.get("id")),
        "status": fm.get("status"),
        "claimed_by": claimed_by,
        "claim_expires_at_raw": fm.get("claim_expires_at"),
        "claim_expires_at_dt": _parse_iso8601(fm.get("claim_expires_at")),
        "territory": territory,
    }


# --------------------------------------------------------------------------- #
# Worktree marker discovery (g-rl-02: <repo-parent>/.gald3r-worktrees/<repo-name>)
# --------------------------------------------------------------------------- #
def _candidate_worktree_roots(root: Path, override: Optional[str]) -> List[Path]:
    cands: List[Path] = []
    if override:
        cands.append(Path(override))
    env = os.environ.get("GALD3R_WORKTREE_ROOT")
    if env:
        cands.append(Path(env))
    cands.append(root.parent / ".gald3r-worktrees" / root.name)
    cands.append(root.parent)
    out: List[Path] = []
    seen = set()
    for c in cands:
        key = str(c)
        if key in seen:
            continue
        seen.add(key)
        if c.is_dir():
            out.append(c)
    return out


def find_worktree_marker(
    root: Path, task_id: Optional[str], worktree_root_override: Optional[str]
) -> Optional[Dict[str, Any]]:
    if not task_id:
        return None
    bare = task_id[1:] if task_id.upper().startswith("T") else task_id
    for wroot in _candidate_worktree_roots(root, worktree_root_override):
        for marker_path in sorted(wroot.glob("*/.gald3r-worktree.json")):
            data = _read_worktree_marker(marker_path)
            if not data:
                continue
            mtid = str(data.get("task_id") or "").strip()
            if mtid and (mtid == task_id or mtid == bare or f"T{mtid}" == task_id):
                data["_marker_path"] = str(marker_path)
                return data
    return None


# --------------------------------------------------------------------------- #
# Signal computation (each returns a 0-100 float)
# --------------------------------------------------------------------------- #
def compute_claim_staleness(
    claim_expires_at: Optional[datetime], now: datetime, cap_minutes: float
) -> float:
    if claim_expires_at is None:
        return 0.0
    delta_min = (now - claim_expires_at).total_seconds() / 60.0
    if delta_min <= 0:
        return 0.0
    if cap_minutes <= 0:
        return 100.0
    return min(100.0, (delta_min / cap_minutes) * 100.0)


def compute_worktree_staleness(
    marker: Optional[Dict[str, Any]], now: datetime, cap_minutes: float
) -> float:
    if not marker:
        return 0.0
    created_at = _parse_iso8601(marker.get("created_at"))
    if created_at is None:
        return 0.0
    age_min = (now - created_at).total_seconds() / 60.0
    if age_min <= 0:
        return 0.0
    base = 100.0 if cap_minutes <= 0 else min(100.0, (age_min / cap_minutes) * 100.0)
    base_sha = marker.get("base_sha")
    checkpoint_sha = marker.get("last_checkpoint_sha")
    has_progress = bool(checkpoint_sha) and checkpoint_sha != base_sha
    return base * 0.5 if has_progress else base


def compute_uncommitted_footprint(
    worktree_path: Optional[str], cap_files: float
) -> Tuple[int, float]:
    if not worktree_path:
        return 0, 0.0
    path = Path(worktree_path)
    if not path.is_dir():
        return 0, 0.0
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return 0, 0.0
    if proc.returncode != 0:
        return 0, 0.0
    count = len([ln for ln in proc.stdout.splitlines() if ln.strip()])
    if cap_files <= 0:
        pct = 100.0 if count else 0.0
    else:
        pct = min(100.0, (count / cap_files) * 100.0)
    return count, pct


def band_for(score: float) -> str:
    if score >= BAND_HIGH:
        return "high"
    if score >= BAND_MEDIUM:
        return "medium"
    return "low"


def compute_drift_record(
    fm: Dict[str, Any],
    marker: Optional[Dict[str, Any]],
    now: datetime,
    weights: Dict[str, float],
    caps: Dict[str, float],
) -> Dict[str, Any]:
    claim_score = compute_claim_staleness(fm.get("claim_expires_at_dt"), now, caps["claim"])
    worktree_score = compute_worktree_staleness(marker, now, caps["worktree"])
    wt_path = marker.get("worktree_path") if marker else None
    uncommitted_count, uncommitted_score = compute_uncommitted_footprint(wt_path, caps["uncommitted"])
    composite = (
        claim_score * weights["claim"]
        + worktree_score * weights["worktree"]
        + uncommitted_score * weights["uncommitted"]
    )
    composite = round(min(100.0, max(0.0, composite)), 1)
    owner = fm.get("claimed_by") or (marker.get("owner") if marker else None) or "unclaimed"
    return {
        "task_id": fm.get("task_id"),
        "owner": owner,
        "territory": fm.get("territory") or "UNASSIGNED",
        "status": fm.get("status"),
        "claim_staleness": round(claim_score, 1),
        "worktree_staleness": round(worktree_score, 1),
        "uncommitted_files": uncommitted_count,
        "uncommitted_footprint": round(uncommitted_score, 1),
        "drift_score": composite,
        "band": band_for(composite),
        "worktree_path": wt_path,
    }


def _aggregate(
    records: List[Dict[str, Any]], key_fn: Callable[[Dict[str, Any]], str], label: str
) -> List[Dict[str, Any]]:
    groups: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for r in records:
        k = key_fn(r) or "UNASSIGNED"
        groups.setdefault(k, []).append(r)
    out: List[Dict[str, Any]] = []
    for k in sorted(groups):
        items = groups[k]
        avg = round(sum(i["drift_score"] for i in items) / len(items), 1)
        mx = max(i["drift_score"] for i in items)
        out.append(
            {label: k, "task_count": len(items), "avg_drift_score": avg,
             "max_drift_score": mx, "band": band_for(mx)}
        )
    return out


def run(
    root: Path,
    worktree_root: Optional[str] = None,
    statuses: Sequence[str] = ("in-progress",),
    now: Optional[datetime] = None,
    weights: Optional[Dict[str, float]] = None,
    caps: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    weights = weights or DEFAULT_WEIGHTS
    caps = caps or DEFAULT_CAPS
    records: List[Dict[str, Any]] = []
    for path in iter_task_files(root, statuses):
        try:
            fm = parse_task_frontmatter(path)
        except Exception:
            continue
        if not fm.get("task_id"):
            continue
        marker = find_worktree_marker(root, fm["task_id"], worktree_root)
        rec = compute_drift_record(fm, marker, now, weights, caps)
        try:
            rec["task_file"] = str(path.relative_to(root))
        except ValueError:
            rec["task_file"] = str(path)
        records.append(rec)
    records.sort(key=lambda r: (-r["drift_score"], r["task_id"] or ""))
    by_territory = _aggregate(records, lambda r: r["territory"], "territory")
    by_owner = _aggregate(records, lambda r: r["owner"], "owner")
    summary = {
        "task_count": len(records),
        "high_count": sum(1 for r in records if r["band"] == "high"),
        "medium_count": sum(1 for r in records if r["band"] == "medium"),
        "low_count": sum(1 for r in records if r["band"] == "low"),
    }
    return {
        "drift_score_version": DRIFT_SCORE_VERSION,
        "subjects": records,
        "by_territory": by_territory,
        "by_owner": by_owner,
        "summary": summary,
        "params": {"weights": weights, "caps": caps, "statuses": list(statuses)},
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print_report(root: Path, result: Dict[str, Any]) -> None:
    print("\n=== g-skl-drift (T195 / D15) ===")
    print(f"  root: {root}")
    p = result["params"]
    print(
        f"  weights: claim={p['weights']['claim']} worktree={p['weights']['worktree']} "
        f"uncommitted={p['weights']['uncommitted']}"
    )
    print(
        f"  caps: claim={p['caps']['claim']}min worktree={p['caps']['worktree']}min "
        f"uncommitted={p['caps']['uncommitted']}files"
    )
    print(f"  statuses scanned: {', '.join(p['statuses'])}")
    print()
    print(f"  {'TASK':<8}{'OWNER':<22}{'TERRITORY':<28}{'CLAIM':>7}{'WT':>7}{'UNCM':>7}{'DRIFT':>8}  BAND")
    for r in result["subjects"]:
        print(
            f"  {str(r['task_id'])[:8]:<8}{str(r['owner'])[:21]:<22}{str(r['territory'])[:27]:<28}"
            f"{r['claim_staleness']:>7.1f}{r['worktree_staleness']:>7.1f}{r['uncommitted_footprint']:>7.1f}"
            f"{r['drift_score']:>8.1f}  {r['band']}"
        )
    if not result["subjects"]:
        print("  (no matching tasks)")
    print("\n  -- by territory --")
    for t in result["by_territory"]:
        print(
            f"  {t['territory']:<28} tasks={t['task_count']:<4} avg={t['avg_drift_score']:>6.1f} "
            f"max={t['max_drift_score']:>6.1f} band={t['band']}"
        )
    print("\n  -- by owner (dev) --")
    for o in result["by_owner"]:
        print(
            f"  {o['owner']:<22} tasks={o['task_count']:<4} avg={o['avg_drift_score']:>6.1f} "
            f"max={o['max_drift_score']:>6.1f} band={o['band']}"
        )
    s = result["summary"]
    print(f"\n  SUMMARY: {s['task_count']} task(s) -- high={s['high_count']} "
          f"medium={s['medium_count']} low={s['low_count']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic per-territory / per-dev drift score (T195 / D15)."
    )
    parser.add_argument("--root", default=None, help="Project root (default: auto-detect via .gald3r/).")
    parser.add_argument("--worktree-root", default=None, help="Override worktree root search dir (g-rl-02).")
    parser.add_argument(
        "--status", action="append", default=None,
        help="Task status folder to scan (repeatable; default: in-progress). Use 'all' for every status.",
    )
    parser.add_argument("--claim-stale-cap-min", type=float, default=DEFAULT_CAPS["claim"])
    parser.add_argument("--worktree-stale-cap-min", type=float, default=DEFAULT_CAPS["worktree"])
    parser.add_argument("--uncommitted-cap-files", type=float, default=DEFAULT_CAPS["uncommitted"])
    parser.add_argument("--json", action="store_true", help="Emit the g-skl-json-output-compatible envelope.")
    parser.add_argument("--compact", action="store_true", help="Minified JSON (with --json).")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)

    root = Path(args.root).resolve() if args.root else _find_root()
    if not (root / ".gald3r").is_dir():
        print(f"ERROR: no .gald3r/ found at or above {root}", file=sys.stderr)
        return 1

    statuses = args.status or ["in-progress"]
    caps = {
        "claim": args.claim_stale_cap_min,
        "worktree": args.worktree_stale_cap_min,
        "uncommitted": args.uncommitted_cap_files,
    }
    now = datetime.now(timezone.utc)
    result = run(root, worktree_root=args.worktree_root, statuses=statuses, now=now, caps=caps)

    if args.json:
        envelope: "OrderedDict[str, Any]" = OrderedDict(
            [
                ("gald3r_version", _read_gald3r_version(root)),
                ("generated_at", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
                ("command", "g-skl-drift"),
                ("schema", "drift"),
                ("data", result),
            ]
        )
        if args.compact:
            text = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False)
        else:
            text = json.dumps(envelope, indent=2, ensure_ascii=False)
        print(text)
    else:
        _print_report(root, result)

    return 2 if result["summary"]["high_count"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
