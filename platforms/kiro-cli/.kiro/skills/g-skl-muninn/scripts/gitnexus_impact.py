#!/usr/bin/env python3
"""Python port of gitnexus_impact.ps1 (T1585).

[DEPRECATED — T1158] Use g-skl-muninn/scripts/graph_impact.py instead.
Cross-file impact analysis for gald3r projects (T921). Returns a list of
files that import, call, or reference the target file/symbol.

This script wrapped GitNexus, which has been replaced by the gald3r_muninn
clean-room rewrite (parent epic T1147, plugin T1157). The wrapper is kept
temporarily so that any out-of-tree callers do not break mid-migration. It
forwards to graph_impact.py when that script is available and only falls
through to the original GitNexus / ripgrep path when graph_impact.py is
missing.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _bootstrap_engine() -> bool:
    """Make gald3r.utils importable; fall back to stdlib when unavailable."""
    try:
        import gald3r.utils  # noqa: F401

        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for d in here.parents:
        engine_src = d / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401

                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()


def _color_enabled() -> bool:
    if _HAS_ENGINE:
        from gald3r.utils import console

        return console.color_enabled()
    return bool(getattr(sys.stdout, "isatty", lambda: False)()) and not os.environ.get("NO_COLOR")


_COLORS = {"cyan": "36", "gray": "37", "yellow": "33", "green": "32",
           "darkgray": "90"}


def say(msg: str, color: Optional[str] = None) -> None:
    """Write-Host equivalent — same text, ANSI color when supported."""
    if color and _color_enabled():
        print(f"\x1b[{_COLORS[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def find_project_root() -> Path:
    """Resolve project root (walk up from cwd to find .gald3r/)."""
    if _HAS_ENGINE:
        from gald3r.utils import paths

        try:
            return paths.gald3r_root()
        except FileNotFoundError:
            return Path.cwd()
    d = Path.cwd()
    while d != d.parent:
        if (d / ".gald3r").exists():
            return d
        d = d.parent
    return Path.cwd()


def invoke_gitnexus_impact(project_root: Path, rel_file: str, depth: int) -> Optional[Dict[str, Any]]:
    """BACKEND: GitNexus — requires `gitnexus` to be installed and indexed."""
    gn = shutil.which("gitnexus")
    if not gn:
        return None

    # Check if indexed
    try:
        status_proc = subprocess.run([gn, "status"], capture_output=True, text=True,
                                     encoding="utf-8", errors="replace")
    except OSError:
        return None
    status_out = (status_proc.stdout or "") + (status_proc.stderr or "")
    if "not indexed" in status_out:
        return None

    try:
        # Use a timeout to avoid hanging if gitnexus crashes (known Windows
        # tree-sitter access-violation issue; see T921 evaluation finding).
        proc = subprocess.run(
            [gn, "impact", rel_file, "--depth", str(depth), "--format", "json"],
            cwd=str(project_root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return None  # Timed out / failed to launch — fall back

    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if proc.returncode == 0 and output:
        return {"backend": "gitnexus", "raw": output}
    return None


def _rg_files(rg: str, args: List[str]) -> List[str]:
    """Run ripgrep -l and return matching file paths (empty on any failure)."""
    try:
        proc = subprocess.run([rg, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]


def invoke_python_impact(project_root: Path, abs_file: str, rel_file: str,
                         depth: int) -> Dict[str, Any]:
    """BACKEND: Python AST + ripgrep fallback — import-pattern scan."""
    ext = Path(abs_file).suffix.lower()
    base_name = Path(abs_file).stem

    affected: set = set()
    rg = shutil.which("rg")
    root_str = str(project_root)

    def add_matches(matches: List[str]) -> None:
        for m in matches:
            if m != abs_file:
                affected.add(m.replace(root_str, "").lstrip("\\/"))

    if ext in (".py", ".pyi"):
        # Python: search for import/from patterns
        patterns = [
            f"import {base_name}",
            f"from {base_name} import",
            f"from .* import.*{base_name}",
        ]
        # Get module path relative to src/project root
        rel_dir = os.path.dirname(rel_file)
        module_path = rel_dir.replace("\\", ".").replace("/", ".").lstrip(".")
        if module_path:
            patterns.append(f"from {module_path} import")
            patterns.append(f"from {module_path}\\.{base_name}")
        if rg:
            for pattern in patterns:
                add_matches(_rg_files(rg, ["-l", "--type", "py", pattern, root_str]))
    elif ext in (".ts", ".tsx", ".js", ".mjs", ".mts"):
        # TypeScript/JavaScript: search for import patterns
        patterns = [
            f"from ['\"].*{base_name}['\"]",
            f"import.*['\"].*{base_name}['\"]",
            f"require\\(['\"].*{base_name}['\"]",
        ]
        if rg:
            for pattern in patterns:
                add_matches(_rg_files(
                    rg, ["-l", "-e", pattern, "--type", "ts", "--type", "js", root_str]))
    else:
        # Generic: filename-based reference search
        if rg:
            add_matches(_rg_files(rg, ["-l", base_name, root_str]))

    file_list = [
        f for f in sorted(affected)
        if not re.search(r"\.(lock|log|md|yaml|yml|json)$", f, re.IGNORECASE)
        and not re.search(r"node_modules", f, re.IGNORECASE)
        and not re.search(r"\.gald3r", f, re.IGNORECASE)
    ]

    return {
        "backend": "python-ripgrep",
        "files": file_list,
        "depth": depth,
        "note": "GitNexus unavailable/crashed - using ripgrep import scan "
                "(limited precision)",
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="[DEPRECATED — T1158] Use graph_impact.py instead. "
                    "GitNexus-based impact analysis (Python port of "
                    "gitnexus_impact.ps1, T921).",
        allow_abbrev=False)
    parser.add_argument("-File", "--file", dest="file", required=True,
                        help="Relative or absolute path to the target file or symbol.")
    parser.add_argument("-Depth", "--depth", dest="depth", type=int, default=2,
                        help="Search depth for transitive dependents (default: 2).")
    parser.add_argument("-Backend", "--backend", dest="backend", default="auto",
                        choices=["gitnexus", "python", "auto"],
                        help="Force backend (default: auto).")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Output results as JSON instead of formatted text.")
    args = parser.parse_args(argv)

    # DEPRECATION NOTICE — T1158. Forward to graph_impact.py when available so
    # existing callers keep working during the migration window.
    replacement = Path(__file__).resolve().parent / "graph_impact.py"
    if replacement.exists():
        print("WARNING: [DEPRECATED] .claude/skills/g-skl-muninn/scripts/gitnexus_impact.py "
              "is deprecated (T1158). Forwarding to "
              ".claude/skills/g-skl-muninn/scripts/graph_impact.py.", file=sys.stderr)
        # Forward original parameters verbatim. Note: -Backend gitnexus is no
        # longer meaningful; the new script accepts 'muninn' | 'mcp' | 'ripgrep'
        # | 'auto'. Map the closest equivalent and let the new script decide.
        new_backend = {"gitnexus": "auto", "python": "ripgrep"}.get(args.backend, "auto")
        fwd_args = [sys.executable, str(replacement), "-File", args.file,
                    "-Depth", str(args.depth), "-Backend", new_backend]
        if args.json:
            fwd_args.append("-Json")
        proc = subprocess.run(fwd_args)
        return proc.returncode

    project_root = find_project_root()
    abs_file = args.file if os.path.isabs(args.file) else str(project_root / args.file)
    if abs_file.startswith(str(project_root)):
        rel_file = abs_file[len(str(project_root)):].lstrip("\\/")
    else:
        rel_file = args.file

    if not Path(abs_file).exists():
        result = {"success": False, "error": f"File not found: {abs_file}",
                  "file": rel_file}
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["error"], file=sys.stderr)
        return 1

    gn_result: Optional[Dict[str, Any]] = None
    if args.backend in ("gitnexus", "auto"):
        gn_result = invoke_gitnexus_impact(project_root, rel_file, args.depth)

    if gn_result:
        final_result: Dict[str, Any] = {
            "success": True,
            "backend": "gitnexus",
            "file": rel_file,
            "impact_raw": gn_result["raw"],
        }
    else:
        py_result = invoke_python_impact(project_root, abs_file, rel_file, args.depth)
        final_result = {
            "success": True,
            "backend": py_result["backend"],
            "file": rel_file,
            "affected_files": py_result["files"],
            "count": len(py_result["files"]),
            "depth": args.depth,
            "note": py_result["note"],
        }

    if args.json:
        print(json.dumps(final_result, indent=2))
    else:
        say("")
        say(f"Impact Analysis: {rel_file}", "cyan")
        say(f"Backend: {final_result['backend']}", "gray")

        if final_result["backend"] == "gitnexus":
            say(final_result["impact_raw"])
        else:
            files = final_result["affected_files"]
            if files:
                say(f"Affected files ({len(files)}):", "yellow")
                for f in files:
                    say(f"  - {f}")
            else:
                say("No files found that import/reference this target.", "green")
            if final_result.get("note"):
                say("")
                say(f"Note: {final_result['note']}", "darkgray")
        say("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
