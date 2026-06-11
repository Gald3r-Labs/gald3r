#!/usr/bin/env python3
"""Python port of gald3r_post_write_lint.ps1 (T1587).

Post-write lint validation for the gald3r g-go-code workflow (T919). Runs a
language-appropriate syntax check after each file write in the g-go-code
implementation loop — catching malformed syntax at write time, not at
test/CI time. Pattern from Hermes v0.13.0 PR #20191.

Supported: .py, .json, .yaml/.yml, .toml, .ts/.tsx/.js/.jsx/.mts/.mjs (when a
tsconfig.json exists), .ps1/.psm1/.psd1 (via pwsh/powershell parser).
Unsupported extensions pass silently.

Exit codes (same as the PS1): 0 = OK or skipped, 1 = file not found,
2 = syntax error.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def _bootstrap_engine_path() -> None:
    here = Path(__file__).resolve().parent
    candidates: List[Path] = [here.parent / "engine" / "src"]
    for anc in [here, *here.parents]:
        candidates.append(anc / ".gald3r_sys" / "engine" / "src")
        candidates.append(
            anc / "gald3r_core" / "project_template" / ".gald3r_sys" / "engine" / "src"
        )
    for cand in candidates:
        if (cand / "gald3r" / "utils" / "console.py").is_file():
            sys.path.insert(0, str(cand))
            return


try:
    from gald3r.utils import console as _console
except ImportError:
    _bootstrap_engine_path()
    try:
        from gald3r.utils import console as _console
    except ImportError:
        _console = None

_GREEN, _RED, _YELLOW, _RESET = "\x1b[92m", "\x1b[91m", "\x1b[93m", "\x1b[0m"


def _color_enabled() -> bool:
    if _console is not None:
        return _console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="gald3r_post_write_lint.py", allow_abbrev=False,
        description="Post-write syntax lint for the g-go-code loop (T919).",
    )
    p.add_argument("-FilePath", "--file-path", dest="file_path", required=True,
                   help="Path to the file that was just written or modified.")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                   default=os.getcwd(),
                   help="Root of the project (default: current directory).")
    p.add_argument("-Json", "--json", dest="json", action="store_true",
                   help="Emit a compact JSON result object.")
    return p.parse_args(argv)


def write_result(as_json: bool, file_path: str, ok: bool, message: str,
                 detail: str = "") -> None:
    if as_json:
        obj = {"ok": ok, "message": message, "detail": detail, "file": file_path}
        print(json.dumps(obj, separators=(",", ":")))
        return
    prefix = "[LINT OK]" if ok else "[LINT FAIL]"
    color = _GREEN if ok else _RED
    if _color_enabled():
        print(f"{color}{prefix} {message}{_RESET}")
        if detail and not ok:
            print(f"{_YELLOW}  {detail}{_RESET}")
    else:
        print(f"{prefix} {message}")
        if detail and not ok:
            print(f"  {detail}")


def _run(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    """Run a command, return (returncode, combined output as one '; ' detail)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        return 127, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, "; ".join(ln for ln in out.splitlines() if ln.strip())


def _lint_powershell(abs_path: str) -> Tuple[bool, str]:
    """Parse a .ps1/.psm1/.psd1 with the PowerShell language parser.

    Uses Parser::ParseFile (not PSParser::Tokenize) so structural syntax
    errors (e.g. unbalanced braces) actually surface (BUG-101 Gap 2).
    """
    exe = shutil.which("pwsh") or shutil.which("powershell")
    if not exe:
        return True, "__SKIP__"  # no PowerShell host available — skip silently
    ps_path = abs_path.replace("'", "''")
    script = (
        "$pe=$null;"
        f"$null=[System.Management.Automation.Language.Parser]::ParseFile('{ps_path}',[ref]$null,[ref]$pe);"
        "if($pe -and $pe.Count -gt 0){"
        "$pe | ForEach-Object { \"L$($_.Extent.StartLineNumber): $($_.Message)\" };"
        "exit 2 } else { exit 0 }"
    )
    code, out = _run([exe, "-NoProfile", "-NonInteractive", "-Command", script])
    if code == 0:
        return True, ""
    return False, out


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    file_path = args.file_path

    # Resolve absolute path
    if os.path.isabs(file_path):
        abs_path = file_path
    else:
        abs_path = os.path.normpath(os.path.join(args.project_root, file_path))

    if not os.path.exists(abs_path):
        write_result(args.json, file_path, False, "File not found", abs_path)
        return 1

    ext = os.path.splitext(abs_path)[1].lower()
    ok = True
    detail = ""

    if ext == ".py":
        import py_compile
        try:
            py_compile.compile(abs_path, doraise=True)
        except py_compile.PyCompileError as exc:
            ok = False
            detail = "; ".join(str(exc).splitlines())
        except (SyntaxError, ValueError, OSError) as exc:
            ok = False
            detail = str(exc)
    elif ext == ".json":
        try:
            with open(abs_path, "r", encoding="utf-8-sig") as fh:
                json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            ok = False
            detail = str(exc)
    elif ext in (".yaml", ".yml"):
        try:
            import yaml  # optional dependency
        except ImportError:
            # PyYAML not installed — skip rather than fail the write
            write_result(args.json, file_path, True,
                         "YAML lint skipped (PyYAML not installed)", "")
            return 0
        try:
            with open(abs_path, "r", encoding="utf-8-sig") as fh:
                yaml.safe_load(fh.read())
        except yaml.YAMLError as exc:
            ok = False
            detail = "; ".join(str(exc).splitlines())
        except (UnicodeDecodeError, OSError) as exc:
            ok = False
            detail = str(exc)
    elif ext == ".toml":
        try:
            import tomllib
        except ImportError:
            write_result(args.json, file_path, True,
                         "TOML lint skipped (tomllib unavailable; Python < 3.11)", "")
            return 0
        try:
            with open(abs_path, "rb") as fh:
                tomllib.load(fh)
        except (tomllib.TOMLDecodeError, OSError) as exc:
            ok = False
            detail = str(exc)
    elif ext in (".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs"):
        # Only run tsc when a tsconfig is present in the project
        tsconfig = os.path.join(args.project_root, "tsconfig.json")
        if not os.path.exists(tsconfig):
            write_result(args.json, file_path, True,
                         "TypeScript/JS lint skipped (no tsconfig.json)", "")
            return 0
        npx = shutil.which("npx")
        if not npx:
            write_result(args.json, file_path, True,
                         "TypeScript/JS lint skipped (npx not on PATH)", "")
            return 0
        code, out = _run([npx, "tsc", "--noEmit", "--allowJs"],
                         cwd=args.project_root)
        if code != 0:
            ok = False
            # Only surface errors from the target file to keep noise low
            base = re.escape(os.path.basename(abs_path))
            lines = out.split("; ")
            filtered = [ln for ln in lines if re.search(base, ln)]
            detail = "; ".join(filtered) if filtered else "; ".join(lines[:5])
    elif ext in (".ps1", ".psm1", ".psd1"):
        ok, detail = _lint_powershell(abs_path)
        if ok and detail == "__SKIP__":
            write_result(args.json, file_path, True,
                         "PowerShell lint skipped (no pwsh/powershell on PATH)", "")
            return 0
    else:
        # Unsupported extension — pass silently
        write_result(args.json, file_path, True,
                     f"Lint skipped (unsupported extension: {ext})", "")
        return 0

    if ok:
        write_result(args.json, file_path, True, f"Syntax OK ({ext})")
        return 0
    write_result(args.json, file_path, False, f"Syntax error ({ext})", detail)
    return 2


if __name__ == "__main__":
    sys.exit(main())
