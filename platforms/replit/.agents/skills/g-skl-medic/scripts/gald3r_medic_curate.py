#!/usr/bin/env python3
"""Python port of gald3r_medic_curate.ps1 (T1585).

g-medic curation: dry-run fragmentation report, optional apply from prior
proposal JSON.

Default (dry-run): analyze .gald3r/features and .gald3r/subsystems, run the
hierarchy sync helpers (-WarnOnly), optionally write markdown + machine-
readable proposal under .gald3r/reports/. Never deletes feature/subsystem
files.

Apply: requires -ProposalJson pointing to JSON produced by a prior dry-run.
Backs up each source file, executes git mv moves, replaces path strings in
FEATURES.md, SUBSYSTEMS.md, and task markdown under .gald3r/tasks/** when
those files reference moved paths, then refreshes architecture diagrams.
Refuses apply if the git working tree has unexpected dirty paths.

Cross-skill helpers (gald3r_feature_hierarchy_sync, gald3r_subsystem_
hierarchy_sync, gald3r_subsystem_diagrams_generate) are resolved at runtime:
a .py sibling is preferred when present; otherwise the .ps1 is invoked via
pwsh (or Windows PowerShell as a fallback).
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _bootstrap_engine() -> bool:
    """Make `gald3r.utils` importable (installed package or bundled engine src)."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
if _HAS_ENGINE:
    from gald3r.utils import process as _process
else:
    _process = None  # graceful stdlib fallback


def run_cmd(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr) without raising."""
    if _process is not None:
        try:
            r = _process.run_cmd(args, cwd=cwd, check=False)
            return r.returncode, r.stdout, r.stderr
        except (OSError, ValueError):
            return 127, "", f"failed to run: {args[0]}"
    try:
        proc = subprocess.run(
            args, cwd=str(cwd) if cwd else None, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (FileNotFoundError, OSError):
        return 127, "", f"failed to run: {args[0]}"


def run_git(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    return run_cmd(["git", *args], cwd=cwd)


def die(message: str) -> None:
    """Write-Error + $ErrorActionPreference=Stop equivalent: print + exit 1."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _find_powershell() -> Optional[str]:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def run_helper_script(script_dir: Path, basename: str,
                      args: List[str]) -> Tuple[int, str, str]:
    """Cross-skill helper resolver: prefer a .py sibling when it exists at
    runtime, else invoke the .ps1 via pwsh/powershell.

    Returns (returncode, stdout, stderr); (127, "", reason) when neither
    implementation is available.
    """
    py = script_dir / f"{basename}.py"
    if py.is_file():
        return run_cmd([sys.executable, str(py), *args])
    ps1 = script_dir / f"{basename}.ps1"
    if ps1.is_file():
        shell = _find_powershell()
        if shell is None:
            return 127, "", "no pwsh/powershell available to run " + str(ps1)
        return run_cmd([shell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(ps1), *args])
    return 127, "", f"helper not found: {script_dir / basename}(.py|.ps1)"


def get_git_status_short(root: Path) -> List[str]:
    rc, out, _ = run_git(["status", "--porcelain=v1", "-uall"], cwd=root)
    if rc != 0:
        return []
    return [ln for ln in out.splitlines() if ln]


def normalize_repo_path(p: Optional[str]) -> str:
    if not p or not str(p).strip():
        return ""
    return str(p).strip().replace("\\", "/")


def update_text_file_paths(file_path: Path,
                           move_pairs: List[Dict[str, str]]) -> bool:
    if not file_path.is_file():
        return False
    try:
        text = file_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    orig = text
    for pair in move_pairs:
        frm = pair.get("from")
        to = pair.get("to")
        if frm and to and frm in text:
            text = text.replace(frm, to)
    if text == orig:
        return False
    file_path.write_text(text, encoding="utf-8")  # UTF-8 without BOM
    return True


def new_curation_suggestion(kind: str, frm: str, to: str, risk: str,
                            confidence: str, rationale: str,
                            action: str = "move") -> Dict[str, str]:
    return {
        "kind": kind, "action": action, "from": frm, "to": to,
        "risk": risk, "confidence": confidence, "rationale": rationale,
    }


def get_feature_area(file_name: str) -> str:
    n = file_name.lower()
    if re.search(r"agent|gateway|trace|eval|inference|loop|sdk", n):
        return "gald3r-agent"
    if re.search(r"backend|api|mcp|oracle|docker|server|websocket|auth", n):
        return "gald3r-backend"
    if re.search(r"vault|knowledge|recon|harvest|ingest|crawl|memory", n):
        return "knowledge-vault"
    if re.search(r"workspace|wpac|link|member|template|parity", n):
        return "workspace-control"
    if re.search(r"skill|command|platform|cursor|claude|codex|opencode|gemini|copilot", n):
        return "platform-surfaces"
    if re.search(r"medic|health|status|task|bug|feature|prd|release|plan|constraint|subsystem", n):
        return "gald3r-control-plane"
    if re.search(r"desktop|tauri|electron|frontend|react|web|ui|theme|voice|3d|level", n):
        return "app-surfaces"
    if re.search(r"personality|fandom|fan|silicon|trek|firefly|bsg|hackers", n):
        return "personality-packs"
    return "needs-human-review"


def get_subsystem_domain(file_name: str) -> str:
    n = file_name.lower()
    if re.search(r"^adopted_example_web_", n):
        return "adopted/example_web"
    if re.search(r"^adopted_gald3r_discord_", n):
        return "adopted/gald3r_discord"
    if re.search(r"^gald3r-agent-", n):
        return "gald3r-agent"
    if re.search(r"vault|knowledge|recon|harvest|ingest|crawl|memory", n):
        return "knowledge-vault"
    if re.search(r"backend|api|oracle|websocket|auth|streaming|status", n):
        return "backend"
    if re.search(r"frontend|web-ui|tauri|electron|theme|voice|3d|level|communications", n):
        return "apps"
    if re.search(r"ai-agent|ai-skill|command|behavioral|platform|parity|skill", n):
        return "platform-surfaces"
    if re.search(r"task|bug|feature|project|idea|release|planning|constraint|medic|health|subsystem", n):
        return "gald3r-control-plane"
    if re.search(r"workspace|wpac|link|member", n):
        return "workspace-control"
    return "core"


def do_apply(project_root: Path, proposal_json: str, reports: Path,
             stamp: str) -> int:
    if not proposal_json.strip() or not Path(proposal_json).is_file():
        die("Apply requires -ProposalJson path to a dry-run proposal JSON "
            "(from .gald3r/reports/medic_curate_proposal_*.json).")
    dirty = get_git_status_short(project_root)
    unexpected = [
        ln for ln in dirty
        if re.search(r"^\?\?|^.. \.gald3r/", ln)
        and not re.search(r"reports[/\\]medic_curate", ln)
        and not re.search(r"reports[/\\]medic_curate_backup", ln)
    ]
    if unexpected:
        die("Refusing apply: working tree has unrelated changes:\n"
            + "\n".join(unexpected))
    try:
        prop = json.loads(Path(proposal_json).read_text(encoding="utf-8-sig",
                                                        errors="replace"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        die(f"Could not parse proposal JSON: {exc}")
        return 1
    moves_arr = prop.get("moves")
    if moves_arr is None:
        die("Proposal has no moves array - run dry-run first.")
    moves_arr = list(moves_arr)
    if not moves_arr:
        die("Proposal moves is empty. Add approved git mv entries to the JSON, "
            "then re-run -Apply.")

    norm_moves: List[Dict[str, str]] = []
    tos: Dict[str, bool] = {}
    froms: Dict[str, bool] = {}
    for m in moves_arr:
        f = normalize_repo_path(str(m.get("from", "")))
        t = normalize_repo_path(str(m.get("to", "")))
        if not f or not t:
            die(f"Move entry missing from/to: {json.dumps(m)}")
        if f == t:
            die(f"Move from and to are identical: {f}")
        if not re.match(r"(?i)^\.gald3r/(features|subsystems)/", f):
            die("Refusing apply: from path must be under .gald3r/features or "
                f".gald3r/subsystems: {f}")
        if not re.match(r"(?i)^\.gald3r/(features|subsystems)/", t):
            die("Refusing apply: to path must be under .gald3r/features or "
                f".gald3r/subsystems: {t}")
        if t in tos:
            die(f"Refusing apply: duplicate move target: {t}")
        if f in froms:
            die(f"Refusing apply: duplicate move source: {f}")
        tos[t] = True
        froms[f] = True
        norm_moves.append({"from": f, "to": t})

    backup_root = reports / f"medic_curate_backup_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    for mv in norm_moves:
        from_fs = project_root / Path(*mv["from"].split("/"))
        to_fs = project_root / Path(*mv["to"].split("/"))
        if not from_fs.exists():
            print(f"WARNING: Skip missing: {from_fs}", file=sys.stderr)
            continue
        rel_backup = mv["from"].lstrip(".").lstrip("/")
        dest_backup = backup_root / Path(*rel_backup.split("/"))
        dest_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(from_fs), str(dest_backup))
        to_fs.parent.mkdir(parents=True, exist_ok=True)
        rc, out, err = run_git(["-C", str(project_root), "mv", "--",
                                mv["from"], mv["to"]])
        if out.strip():
            print(out.rstrip("\n"))
        if err.strip():
            print(err.rstrip("\n"))

    gald3r = project_root / ".gald3r"
    patch_files: List[Path] = [gald3r / "FEATURES.md", gald3r / "SUBSYSTEMS.md"]
    # T1025: tasks now live in status subfolders — recurse to find all
    tasks_root = gald3r / "tasks"
    if tasks_root.is_dir():
        patch_files.extend(sorted(tasks_root.rglob("*.md")))
    updated: List[str] = []
    for pf in patch_files:
        if update_text_file_paths(pf, norm_moves):
            updated.append(str(pf))

    manifest = reports / f"medic_curate_manifest_{stamp}.json"
    manifest.write_text(json.dumps({
        "applied": stamp,
        "source_proposal": proposal_json,
        "moves": norm_moves,
        "backup_directory": str(backup_root),
        "patched_files": updated,
    }, indent=2) + "\n", encoding="utf-8")

    rc, out, err = run_helper_script(
        project_root / "scripts", "gald3r_subsystem_diagrams_generate",
        ["-ProjectRoot", str(project_root)])
    if rc == 127:
        print(f"WARNING: diagram refresh skipped: {err}", file=sys.stderr)
    elif out.strip():
        print(out.rstrip("\n"))
    print(f"Apply complete. Manifest: {manifest} Backup: {backup_root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="g-medic curation: dry-run fragmentation report, optional "
                    "apply from prior proposal JSON.")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()),
                        help="Root of the gald3r project (default: cwd).")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Apply approved moves from -ProposalJson.")
    parser.add_argument("-ProposalJson", "--proposal-json", dest="proposal_json",
                        default="",
                        help="Path to medic_curate_proposal.json from a "
                             "previous dry-run.")
    parser.add_argument("-ForceSameRun", "--force-same-run",
                        dest="force_same_run", action="store_true",
                        help="Reserved for future use — apply still requires "
                             "ProposalJson today.")
    parser.add_argument("-NoReportFiles", "--no-report-files",
                        dest="no_report_files", action="store_true",
                        help="Dry-run only: do not write report/proposal files.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()

    reports = project_root / ".gald3r" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    proposal_path = reports / f"medic_curate_proposal_{stamp}.json"
    report_md = reports / f"medic_curate_{stamp}.md"

    if args.apply:
        return do_apply(project_root, args.proposal_json, reports, stamp)

    # --- Dry-run ---
    scripts_dir = project_root / "scripts"
    sync_args = ["-ProjectRoot", str(project_root), "-WarnOnly", "-Json"]
    _, feat_raw, _ = run_helper_script(scripts_dir,
                                       "gald3r_feature_hierarchy_sync", sync_args)
    _, sub_raw, _ = run_helper_script(scripts_dir,
                                      "gald3r_subsystem_hierarchy_sync", sync_args)
    feat_lines = [ln for ln in feat_raw.splitlines() if ln.strip()]
    sub_lines = [ln for ln in sub_raw.splitlines() if ln.strip()]
    feat_out = feat_lines[-1] if feat_lines else ""
    sub_out = sub_lines[-1] if sub_lines else ""

    feat_root = project_root / ".gald3r" / "features"
    sub_root = project_root / ".gald3r" / "subsystems"
    feature_file_items = [
        f for f in (sorted(feat_root.rglob("*.md")) if feat_root.is_dir() else [])
        if f.is_file() and re.search(r"(?i)feat[-_]?\d+", f.name)
    ]
    subsystem_file_items = [
        f for f in (sorted(sub_root.rglob("*.md")) if sub_root.is_dir() else [])
        if f.is_file()
        and not re.match(r"^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)", f.name)
    ]
    feat_files = len(feature_file_items)
    sub_files = len(subsystem_file_items)
    nested_feat = len([
        f for f in (sorted(feat_root.rglob("*.md")) if feat_root.is_dir() else [])
        if f.is_file() and f.parent != feat_root
    ])

    areas: Dict[str, int] = {}
    for ff in feature_file_items:
        rel = str(ff.relative_to(feat_root))
        seg = re.split(r"[\\/]", rel)[0]
        key = "_flat_root" if re.match(r"(?i)^feat[-_]?\d+", seg) else seg
        areas[key] = areas.get(key, 0) + 1

    suggested_moves: List[Dict[str, str]] = []
    index_candidates: List[Dict[str, str]] = []

    for ff in sorted(feature_file_items, key=lambda p: str(p)):
        if ff.parent != feat_root:
            continue
        rel = ".gald3r/features/" + ff.name
        area = get_feature_area(ff.name)
        risk = "medium" if area == "needs-human-review" else "low"
        confidence = "low" if area == "needs-human-review" else "medium"
        suggested_moves.append(new_curation_suggestion(
            kind="feature", frm=rel,
            to=f".gald3r/features/{area}/{ff.name}",
            risk=risk, confidence=confidence,
            rationale=(f"Flat root feature file; filename tokens map to the "
                       f"'{area}' feature area. Review before copying into "
                       "apply moves.")))

    for sf in sorted(subsystem_file_items, key=lambda p: str(p)):
        if sf.parent != sub_root:
            continue
        rel = ".gald3r/subsystems/" + sf.name
        domain = get_subsystem_domain(sf.name)
        risk = "medium" if domain == "core" else "low"
        confidence = "low" if domain == "core" else "medium"
        suggested_moves.append(new_curation_suggestion(
            kind="subsystem", frm=rel,
            to=f".gald3r/subsystems/{domain}/{sf.name}",
            risk=risk, confidence=confidence,
            rationale=(f"Flat subsystem spec; filename tokens map to the "
                       f"'{domain}' domain. Moving requires index/path patch "
                       "review.")))

    # FEATURES.md: duplicate feat-NNN id lines on table rows
    feat_dupes: List[str] = []
    features_md = project_root / ".gald3r" / "FEATURES.md"
    if features_md.is_file():
        fm = features_md.read_text(encoding="utf-8-sig", errors="replace")
        id_hits: Dict[str, int] = {}
        for line in re.split(r"\r?\n", fm):
            if not line.startswith("|"):
                continue
            for m in re.finditer(r"(?i)feat-(\d+)", line):
                fid = m.group(1)
                id_hits[fid] = id_hits.get(fid, 0) + 1
        for k, count in id_hits.items():
            if count > 1:
                feat_dupes.append(
                    f"feat-{k} appears {count} times in FEATURES.md table rows")

    sub_json_obj: Optional[Any] = None
    try:
        sub_json_obj = json.loads(sub_out) if sub_out.strip() else None
    except (json.JSONDecodeError, ValueError):
        sub_json_obj = None
    disk_not_indexed: List[str] = []
    if isinstance(sub_json_obj, dict) and sub_json_obj.get("disk_not_indexed"):
        disk_not_indexed = [str(p) for p in sub_json_obj["disk_not_indexed"]]
    for p in disk_not_indexed:
        is_demo = bool(re.search(r"nested-path-demo", p))
        confidence = "low" if is_demo else "high"
        risk = "low"
        rationale = (
            "Fixture/demo path detected. Keep unindexed unless you want fixture "
            "specs surfaced in SUBSYSTEMS.md." if is_demo else
            "Spec exists on disk but is absent from SUBSYSTEMS.md index; likely "
            "should be registered before broader tree moves.")
        index_candidates.append(new_curation_suggestion(
            kind="subsystem-index", action="index", frm=f".gald3r/{p}",
            to=".gald3r/SUBSYSTEMS.md", risk=risk, confidence=confidence,
            rationale=rationale))

    sb: List[str] = []
    sb.append(f"# medic_curate dry-run {stamp} UTC")
    sb.append("")
    sb.append("## Executive summary")
    sb.append("")
    sb.append(f"This is a **recommendation report**, not an apply plan. It found "
              f"{feat_files} feature files, {sub_files} subsystem specs, and "
              f"{len(disk_not_indexed)} subsystem specs that exist on disk but "
              "are not indexed.")
    sb.append("")
    sb.append("**Recommended next step:** review the `suggested_moves` and "
              "`index_candidates` sections in the JSON, copy only approved "
              "entries into the top-level `moves` array, then run `-Apply "
              "-ProposalJson`. The top-level `moves` array remains empty by "
              "design so dry-run suggestions cannot migrate files accidentally.")
    sb.append("")
    sb.append("### Suggested first batch")
    sb.append("")
    if index_candidates:
        sb.append("1. Register real `disk_not_indexed` subsystem specs in "
                  "`SUBSYSTEMS.md`; keep fixtures/demo files unindexed unless "
                  "they are meant to become real subsystems.")
    else:
        sb.append("1. No unindexed subsystem specs detected.")
    if areas.get("_flat_root", 0) > 0:
        sb.append(f"2. Move flat root feature files into reviewed area folders. "
                  f"Candidate count: {areas['_flat_root']}.")
    else:
        sb.append("2. Feature files already appear to live under area folders; "
                  "focus on index cleanup first.")
    sb.append("3. Move flat subsystem specs into domain folders only after "
              "reviewing `SUBSYSTEMS.md` link updates in the resulting diff.")
    sb.append("")
    sb.append("## Summary")
    sb.append("| Metric | Value |")
    sb.append("|--------|-------|")
    sb.append(f"| Feature markdown files (featNNN / feat-NNN) | {feat_files} |")
    sb.append(f"| Subsystem spec files (recursive) | {sub_files} |")
    sb.append(f"| Nested-under-area feature paths (heuristic) | {nested_feat} |")
    sb.append("")
    sb.append("## Fragmentation heuristics")
    if feat_dupes:
        sb.append("### Possible duplicate feature IDs in FEATURES.md")
        for d in feat_dupes[:20]:
            sb.append(f"- {d}")
        if len(feat_dupes) > 20:
            sb.append(f"- _(truncated - see proposal JSON feature_dupes for all "
                      f"{len(feat_dupes)} entries)_")
        sb.append("")
    else:
        sb.append("- No duplicate `feat-NNN` token counts detected in "
                  "FEATURES.md table rows.")
        sb.append("")
    if disk_not_indexed:
        sb.append(f"### Subsystem specs on disk not matched in SUBSYSTEMS.md "
                  f"index ({len(disk_not_indexed)})")
        for p in disk_not_indexed[:25]:
            sb.append(f"- `{p}`")
        if len(disk_not_indexed) > 25:
            sb.append("- _(truncated — see proposal JSON "
                      "`subsystem_sync.disk_not_indexed`)_")
        sb.append("")

    sb.append("## Feature area counts (folder segment under features/)")
    for k in sorted(areas.keys()):
        sb.append(f"- **{k}**: {areas[k]} file(s)")
    sb.append("")
    sb.append("## Recommended candidate actions")
    sb.append("")
    if index_candidates:
        sb.append("### Index registration candidates")
        sb.append("| Action | Source | Target | Confidence | Rationale |")
        sb.append("|--------|--------|--------|------------|-----------|")
        for c in index_candidates[:20]:
            sb.append(f"| {c['action']} | `{c['from']}` | `{c['to']}` | "
                      f"{c['confidence']} | {c['rationale']} |")
        if len(index_candidates) > 20:
            sb.append("| note | _(truncated)_ | proposal JSON | - | See "
                      "`index_candidates` for all candidates. |")
        sb.append("")
    if suggested_moves:
        sb.append("### Candidate file moves")
        sb.append("| Kind | From | To | Risk | Confidence | Rationale |")
        sb.append("|------|------|----|------|------------|-----------|")
        sorted_moves = sorted(suggested_moves,
                              key=lambda c: (c["kind"], c["risk"], c["from"]))
        for c in sorted_moves[:40]:
            sb.append(f"| {c['kind']} | `{c['from']}` | `{c['to']}` | "
                      f"{c['risk']} | {c['confidence']} | {c['rationale']} |")
        if len(suggested_moves) > 40:
            sb.append("| note | _(truncated)_ | proposal JSON | - | - | See "
                      "`suggested_moves` for all candidates. |")
        sb.append("")
    else:
        sb.append("- No candidate moves generated by the current heuristics.")
        sb.append("")
    sb.append("## Hierarchy sync (machine JSON)")
    sb.append("```json")
    sb.append(feat_out)
    sb.append(sub_out)
    sb.append("```")
    sb.append("")
    sb.append("## Proposed moves")
    sb.append("_Conservative default: no automatic apply moves in dry-run._ "
              "Review `suggested_moves`, copy approved `{ from, to }` entries "
              "into the JSON top-level `moves` array, then run `-Apply "
              "-ProposalJson`. Apply copies each source into "
              "`reports/medic_curate_backup_<stamp>/`, runs `git mv`, then "
              "replaces path strings in FEATURES.md, SUBSYSTEMS.md, and "
              "`.gald3r/tasks/**/*.md` (status subfolders — T1025) when they "
              "reference old paths.")
    sb.append("")
    sb.append("## Risk")
    sb.append("- **Low** for read-only dry-run (use `-NoReportFiles` to avoid "
              "writing report/proposal files).")
    sb.append("- **Medium** when applying moves: review git diff; path replace "
              "is literal substring — avoid ambiguous partial paths.")
    sb.append("")
    sb.append("## Workspace-Control")
    sb.append("This script only targets the controller `.gald3r/` tree passed "
              "as `-ProjectRoot`. Do not point at member repos with marker-only "
              "`.gald3r/`.")

    def _parse_json_or_none(raw: str) -> Optional[Any]:
        try:
            return json.loads(raw) if raw.strip() else None
        except (json.JSONDecodeError, ValueError):
            return None

    proposal = {
        "schemaVersion": 1,
        "generated_utc": stamp,
        "moves": [],
        "suggested_moves": suggested_moves,
        "index_candidates": index_candidates,
        "notes": ("moves is intentionally empty. Review suggested_moves and "
                  "copy approved { from, to } entries into moves before -Apply. "
                  "index_candidates are SUBSYSTEMS.md registration suggestions, "
                  "not git mv entries."),
        "feature_sync": _parse_json_or_none(feat_out),
        "subsystem_sync": _parse_json_or_none(sub_out),
        "feature_dupes": feat_dupes,
        "disk_not_indexed": disk_not_indexed,
    }

    report_text = "\n".join(sb) + "\n"
    if not args.no_report_files:
        report_md.write_text(report_text, encoding="utf-8")
        proposal_path.write_text(json.dumps(proposal, indent=2) + "\n",
                                 encoding="utf-8")
        shutil.copyfile(str(proposal_path),
                        str(reports / "medic_curate_latest.json"))
        print(f"Dry-run report: {report_md}")
        print(f"Proposal JSON: {proposal_path}")
        print("(also copied to reports/medic_curate_latest.json)")
    else:
        print(report_text)
        print("--- proposal (stdout, not written) ---")
        print(json.dumps(proposal, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
