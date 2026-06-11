#!/usr/bin/env python3
"""Python port of graph_impact.ps1 (T1585).

Cross-file impact analysis for gald3r projects (T1158). Returns a list of
files that import, call, or reference the target file/symbol.

Wraps the gald3r_muninn `graph_impact` MCP tool (replaces the deprecated
gitnexus-based gitnexus_impact script).

Backend resolution order:
1. muninn (preferred) — invoke the muninn plugin core in-process
   (docker/gald3r/tools/plugins/muninn/plugin.py). Uses the persistent
   SQLite graph store at ~/.gald3r/muninn.db (override with MUNINN_DB_PATH).
2. MCP HTTP (optional) — pass -Backend mcp to force a JSON-RPC call against
   the running example_app MCP server (default http://localhost:8090/mcp,
   override with -McpUrl).
3. ripgrep fallback — when neither muninn path is reachable (no index,
   plugin import failed, network error), fall back to the legacy
   ripgrep-based import-pattern scan.
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
import urllib.error
import urllib.request
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
           "darkyellow": "33", "darkgray": "90"}


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


def invoke_muninn_impact(project_root: Path, rel_file: str, depth: int) -> Optional[Dict[str, Any]]:
    """BACKEND: muninn — load the plugin core in-process and call graph_impact."""
    plugin_path = project_root / "docker" / "gald3r" / "tools" / "plugins" / "muninn" / "plugin.py"
    if not plugin_path.exists():
        return None

    try:
        import asyncio
        import importlib.util

        spec = importlib.util.spec_from_file_location("muninn_plugin_core", plugin_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        parsed = asyncio.run(mod.graph_impact(file_path=rel_file.replace("\\", "/")))
    except Exception:  # plugin import/exec failure -> unavailable, fall back
        return None

    if not isinstance(parsed, dict):
        return None
    # Error envelope from the plugin -> treat as unavailable, fall back.
    if parsed.get("error"):
        return None

    # Successful, but no index? Surface so the caller knows to fall back.
    warning = parsed.get("warning")

    files: List[str] = []
    for f in parsed.get("files") or []:
        if isinstance(f, dict) and f.get("path"):
            files.append(f["path"])
        else:
            files.append(str(f))

    return {
        "backend": "muninn",
        "files": files,
        "count": parsed.get("count") or len(files),
        "depth": depth,
        "warning": warning,
    }


def invoke_mcp_impact(mcp_url: str, rel_file: str, depth: int) -> Optional[Dict[str, Any]]:
    """BACKEND: MCP HTTP (example_app server) — JSON-RPC tools/call."""
    try:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "graph_impact",
                       "arguments": {"file_path": rel_file}},
        }).encode("utf-8")
        req = urllib.request.Request(
            mcp_url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
        if not content:
            return None
        body = json.loads(content)
        if body.get("error"):
            return None

        # FastMCP tools/call wraps tool output in result.content[].text
        text_payload: Optional[str] = None
        result = body.get("result") or {}
        for c in result.get("content") or []:
            if isinstance(c, dict) and c.get("text"):
                text_payload = c["text"]
                break
        if not text_payload:
            return None

        parsed = json.loads(text_payload)
        if not isinstance(parsed, dict) or parsed.get("error"):
            return None

        files: List[str] = []
        for f in parsed.get("files") or []:
            if isinstance(f, dict) and f.get("path"):
                files.append(f["path"])
            else:
                files.append(str(f))
        return {
            "backend": "muninn-mcp",
            "files": files,
            "count": parsed.get("count") or len(files),
            "depth": depth,
            "warning": parsed.get("warning"),
        }
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _rg_files(rg: str, args: List[str]) -> List[str]:
    """Run ripgrep -l and return matching file paths (empty on any failure)."""
    try:
        proc = subprocess.run([rg, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]


def invoke_ripgrep_impact(project_root: Path, abs_file: str, rel_file: str,
                          depth: int) -> Dict[str, Any]:
    """BACKEND: ripgrep fallback — import-pattern scan, limited precision."""
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
        patterns = [
            f"import {base_name}",
            f"from {base_name} import",
            f"from .* import.*{base_name}",
        ]
        rel_dir = os.path.dirname(rel_file)
        module_path = rel_dir.replace("\\", ".").replace("/", ".").lstrip(".")
        if module_path:
            patterns.append(f"from {module_path} import")
            patterns.append(f"from {module_path}\\.{base_name}")
        if rg:
            for pattern in patterns:
                add_matches(_rg_files(rg, ["-l", "--type", "py", pattern, root_str]))
    elif ext in (".ts", ".tsx", ".js", ".mjs", ".mts"):
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
        if rg:
            add_matches(_rg_files(rg, ["-l", base_name, root_str]))

    file_list = [
        f for f in sorted(affected)
        if not re.search(r"\.(lock|log|md|yaml|yml|json)$", f, re.IGNORECASE)
        and not re.search(r"node_modules", f, re.IGNORECASE)
        and not re.search(r"\.gald3r", f, re.IGNORECASE)
    ]

    return {
        "backend": "ripgrep-fallback",
        "files": file_list,
        "count": len(file_list),
        "depth": depth,
        "note": "muninn graph unavailable / not indexed - using ripgrep import scan "
                "(limited precision)",
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Cross-file impact analysis via gald3r_muninn "
                    "(Python port of graph_impact.ps1, T1158).",
        allow_abbrev=False)
    parser.add_argument("-File", "--file", dest="file", required=True,
                        help="Relative or absolute path to the target file to analyze.")
    parser.add_argument("-Depth", "--depth", dest="depth", type=int, default=2,
                        help="Search depth for transitive dependents (default: 2).")
    parser.add_argument("-Backend", "--backend", dest="backend", default="auto",
                        choices=["muninn", "mcp", "ripgrep", "auto"],
                        help="Force backend (default: auto).")
    parser.add_argument("-McpUrl", "--mcp-url", dest="mcp_url",
                        default="http://localhost:8090/mcp",
                        help="MCP server URL when -Backend mcp is used.")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Output results as JSON instead of formatted text.")
    args = parser.parse_args(argv)

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

    result: Optional[Dict[str, Any]] = None
    if args.backend == "muninn":
        result = invoke_muninn_impact(project_root, rel_file, args.depth)
    elif args.backend == "mcp":
        result = invoke_mcp_impact(args.mcp_url, rel_file, args.depth)
    elif args.backend == "ripgrep":
        result = invoke_ripgrep_impact(project_root, abs_file, rel_file, args.depth)
    else:  # auto
        result = invoke_muninn_impact(project_root, rel_file, args.depth)
        if not result:
            result = invoke_ripgrep_impact(project_root, abs_file, rel_file, args.depth)

    # Last-ditch: never let an empty path-through escape; fall back to ripgrep.
    if not result:
        result = invoke_ripgrep_impact(project_root, abs_file, rel_file, args.depth)

    final_result: Dict[str, Any] = {
        "success": True,
        "backend": result["backend"],
        "file": rel_file,
        "affected_files": result["files"],
        "count": result["count"],
        "depth": result["depth"],
    }
    if result.get("warning"):
        final_result["warning"] = result["warning"]
    if result.get("note"):
        final_result["note"] = result["note"]

    if args.json:
        print(json.dumps(final_result, indent=2))
    else:
        say("")
        say(f"Impact Analysis: {rel_file}", "cyan")
        say(f"Backend: {final_result['backend']}", "gray")

        files = final_result["affected_files"]
        if files:
            say(f"Affected files ({len(files)}):", "yellow")
            for f in files:
                say(f"  - {f}")
        else:
            say("No files found that import/reference this target.", "green")
        if final_result.get("warning"):
            say("")
            say(f"Warning: {final_result['warning']}", "darkyellow")
        if final_result.get("note"):
            say("")
            say(f"Note: {final_result['note']}", "darkgray")
        say("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
