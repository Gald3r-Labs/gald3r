#!/usr/bin/env python3
"""Python port of gald3r_medic_heal.ps1 (T1585).

gald3r Medic Heal - structural backfill for repos that predate a framework
feature (T1436). g-medic L1 triage detects structural gaps; this script
remediates them. Dry-run by default; pass -Apply to write. Every applied
operation is logged to .gald3r/logs/medic_heal_YYYYMMDD.log.

Phase 1 heals:
  c023        - create missing .gald3r/releases/ files from CHANGELOG
                (delegates to g-skl-release/scripts/backfill_release_files —
                a .py sibling is preferred at runtime, else the .ps1 via pwsh)
  version     - create root VERSION file from the latest CHANGELOG ## [X.Y.Z]
  constraints - report inheritable framework constraints missing from local
                CONSTRAINTS.md; with -Apply, append clearly-marked stubs
  all         - run every Phase 1 heal in order (version, c023, constraints)

Task: T1436  Constraint: C-023  Skill: g-skl-medic
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
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


def _find_powershell() -> Optional[str]:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def run_helper_script(script_dir: Path, basename: str,
                      args: List[str]) -> Tuple[int, str, str]:
    """Cross-skill helper resolver: prefer a .py sibling when it exists at
    runtime, else invoke the .ps1 via pwsh/powershell."""
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


class Healer:
    def __init__(self, project_root: Path, apply: bool, as_json: bool) -> None:
        self.project_root = project_root
        self.apply = apply
        self.as_json = as_json
        self.mode = "apply" if apply else "dry-run"
        self.results: List[Dict[str, Any]] = []
        self.script_dir = Path(__file__).resolve().parent
        self.log_dir = project_root / ".gald3r" / "logs"
        self.log_file = self.log_dir / (
            "medic_heal_" + date.today().strftime("%Y%m%d") + ".log")

    def write_heal_log(self, heal: str, action: str, detail: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts} | heal={heal} | mode={self.mode} | {action} | {detail}"
        if self.apply:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            with self.log_file.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        elif not self.as_json:
            print(f"[DRY-RUN LOG] {line}")

    def add_result(self, heal: str, status: str, message: str,
                   files: Optional[List[str]] = None) -> None:
        self.results.append({"heal": heal, "status": status,
                             "message": message, "files": files or []})
        if not self.as_json:
            print(f"  [{status}] {heal}: {message}")

    # --- heal: c023 (release file backfill) — delegate to release script ---
    def heal_c023(self) -> None:
        backfill_dir = (self.script_dir / ".." / ".." / "g-skl-release"
                        / "scripts").resolve()
        if not ((backfill_dir / "backfill_release_files.py").is_file()
                or (backfill_dir / "backfill_release_files.ps1").is_file()):
            self.write_heal_log(
                "c023", "skip",
                f"backfill_release_files not found under {backfill_dir}")
            self.add_result("c023", "skipped",
                            "backfill_release_files not available (slim tier?)")
            return
        bf_args = ["-ProjectRoot", str(self.project_root), "-Json"]
        if self.apply:
            bf_args.append("-Apply")
        rc, out, err = run_helper_script(backfill_dir,
                                         "backfill_release_files", bf_args)
        if rc == 127:
            self.write_heal_log("c023", "error", err)
            self.add_result("c023", "error", err)
            return
        parsed: Optional[Any] = None
        try:
            parsed = json.loads(out) if out.strip() else None
        except (json.JSONDecodeError, ValueError):
            parsed = None
        created: List[str] = []
        if isinstance(parsed, dict) and parsed.get("created") is not None:
            created = [str(c) for c in parsed["created"]]
        created_count = len(created)
        msg = (f"{created_count} release file(s) backfilled" if self.apply
               else f"{created_count} release file(s) would be backfilled")
        self.write_heal_log("c023", "applied" if self.apply else "planned", msg)
        self.add_result("c023", "ok", msg, created)

    # --- heal: version (VERSION file from latest CHANGELOG header) ---
    def heal_version(self) -> None:
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            self.write_heal_log("version", "skip", "VERSION already present")
            self.add_result("version", "ok", "VERSION already present (no action)")
            return
        changelog = self.project_root / "CHANGELOG.md"
        if not changelog.is_file():
            self.write_heal_log("version", "skip",
                                "no CHANGELOG.md to derive version from")
            self.add_result("version", "skipped", "no CHANGELOG.md found")
            return
        ver: Optional[str] = None
        for line in changelog.read_text(encoding="utf-8-sig",
                                        errors="replace").splitlines():
            m = re.match(r"^\#\#\s*\[(\d+\.\d+\.\d+)\]", line)
            if m:
                ver = m.group(1)
                break
        if not ver:
            self.write_heal_log("version", "skip",
                                "no versioned header in CHANGELOG")
            self.add_result("version", "skipped",
                            "no ## [X.Y.Z] header in CHANGELOG")
            return
        if self.apply:
            version_file.write_text(ver, encoding="utf-8")  # no trailing newline
            self.write_heal_log("version", "applied", f"wrote VERSION={ver}")
            self.add_result("version", "ok", f"created VERSION ({ver})",
                            ["VERSION"])
        else:
            self.write_heal_log("version", "planned", f"would write VERSION={ver}")
            self.add_result("version", "ok", f"would create VERSION ({ver})",
                            ["VERSION"])

    # --- heal: constraints (inheritable framework constraints missing locally) ---
    def heal_constraints(self) -> None:
        local_con = self.project_root / ".gald3r" / "CONSTRAINTS.md"
        fwk_con = (self.script_dir / ".." / ".." / ".." / "constraints"
                   / "framework_inheritable_constraints.md")
        if not fwk_con.is_file():
            self.write_heal_log("constraints", "skip",
                                "framework_inheritable_constraints.md not found")
            self.add_result("constraints", "skipped",
                            "framework inheritable source not available "
                            "(slim tier?)")
            return
        fwk_con = fwk_con.resolve()
        fwk_text = fwk_con.read_text(encoding="utf-8-sig", errors="replace")
        fwk_ids = sorted(set(re.findall(r"\b(C-\d{3})\b", fwk_text)))
        local_ids: List[str] = []
        if local_con.is_file():
            local_text = local_con.read_text(encoding="utf-8-sig",
                                             errors="replace")
            local_ids = sorted(set(re.findall(r"\b(C-\d{3})\b", local_text)))
        missing = [c for c in fwk_ids if c not in local_ids]
        if not missing:
            self.write_heal_log("constraints", "ok",
                                "no missing inheritable constraints")
            self.add_result("constraints", "ok",
                            "all inheritable framework constraints present "
                            "locally")
            return
        missing_list = ", ".join(missing)
        if self.apply:
            # Phase 1 is cautious: append clearly-marked pointer stubs only.
            if not local_con.is_file():
                self.write_heal_log(
                    "constraints", "skip",
                    "local CONSTRAINTS.md absent; refusing to create it "
                    "(needs g-setup)")
                self.add_result(
                    "constraints", "needs_attention",
                    "local CONSTRAINTS.md missing; run @g-setup first. "
                    f"Missing: {missing_list}")
                return
            stub = ("\n<!-- T1436 heal-constraints ("
                    + date.today().strftime("%Y-%m-%d")
                    + "): the following inheritable framework constraints are "
                      "not yet present locally. Review "
                      "framework_inheritable_constraints.md and adopt via "
                      f"@g-constraint-add: {missing_list} -->\n")
            with local_con.open("a", encoding="utf-8") as fh:
                fh.write(stub)
            self.write_heal_log("constraints", "applied",
                                f"appended pointer stub for: {missing_list}")
            self.add_result(
                "constraints", "deferred_verify",
                f"appended adoption pointer for {len(missing)} constraint(s): "
                f"{missing_list}", [".gald3r/CONSTRAINTS.md"])
        else:
            self.write_heal_log("constraints", "planned",
                                f"would flag missing: {missing_list}")
            self.add_result(
                "constraints", "ok",
                f"{len(missing)} inheritable constraint(s) missing locally: "
                f"{missing_list}", [])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="gald3r Medic Heal - structural backfill for repos that "
                    "predate a framework feature (T1436).")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()),
                        help="Root directory of the target project (default: cwd).")
    parser.add_argument("-Heal", "--heal", dest="heal", required=True,
                        choices=["c023", "version", "constraints", "all"],
                        help="Which heal to run.")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Actually write files (default is dry-run).")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit a JSON result object instead of text.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"ERROR: ProjectRoot not found: {args.project_root}",
              file=sys.stderr)
        return 1
    healer = Healer(project_root.resolve(), apply=args.apply, as_json=args.json)

    if not args.json:
        print(f"g-medic heal ({healer.mode}) -- ProjectRoot: "
              f"{healer.project_root}\n")

    if args.heal == "c023":
        healer.heal_c023()
    elif args.heal == "version":
        healer.heal_version()
    elif args.heal == "constraints":
        healer.heal_constraints()
    else:  # all — dependency order: version -> c023 -> constraints
        healer.heal_version()
        healer.heal_c023()
        healer.heal_constraints()

    if args.json:
        print(json.dumps({
            "mode": healer.mode,
            "heal": args.heal,
            "root": str(healer.project_root),
            "results": healer.results,
        }, indent=2))
    else:
        print(f"\nDone. {len(healer.results)} heal operation(s). "
              f"Log: {healer.log_file} (written only with -Apply).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
