#!/usr/bin/env python3
"""Python port of test_g_go_workspace_mode_fixtures.ps1 (T1585).

Verification fixtures for ``g-go --workspace`` and ``g-go --swarm --workspace``
(T532 contract), adapted for the gald3r_templates repo (T1532).

Documentation-and-policy fixtures: because ``g-go`` is an LLM-executed prompt,
these verify that the policy CONTRACT surfaces are intact across the IDE
command surfaces PRESENT IN THIS REPO (discovered dynamically: any top-level
``.<ide>/commands/g-go.md``) and that the workspace manifest + helper scripts
honor the cases the spec calls out. Missing surfaces fail closed.

Fixtures F1-F9 mirror the PS1 one-for-one. Exit 0 = all pass, 1 = failures.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable: installed package, else walk up to .gald3r_sys/engine/src."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".gald3r_sys" / "engine" / "src"
        if (cand / "gald3r" / "utils" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_UTILS = _bootstrap_engine_utils()


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "gray": "90"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REL = Path(".gald3r") / "workspace" / "workspace_manifest.yaml"
_MANIFEST_ENTRY_RX = re.compile(
    r"(?ms)^- id:\s+(?P<id>[a-z][a-z0-9_]*).*?^  local_path:\s+(?P<path>.+?)$"
)


def get_ide_command_roots(repo_root: Path, command_file: str) -> List[str]:
    """Discover top-level dot-dirs carrying commands/<command_file> (D015 parity)."""
    found = []
    try:
        children = sorted(repo_root.iterdir())
    except OSError:
        return []
    for d in children:
        if not d.is_dir() or not d.name.startswith("."):
            continue
        if (d / "commands" / command_file).is_file():
            found.append(d.name)
    return sorted(set(found))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def run_fixtures(repo_root: Path) -> List[Dict[str, object]]:
    """Run F1-F9 and return the result rows."""
    ide_roots = get_ide_command_roots(repo_root, "g-go.md")
    manifest_path = repo_root / MANIFEST_REL
    results: List[Dict[str, object]] = []

    def add(fid: str, name: str, passed: bool, evidence: str) -> None:
        results.append({"id": fid, "name": name, "pass": passed, "evidence": evidence})

    # F1. g-go command surface present on at least one discovered IDE root.
    f1_pass = len(ide_roots) >= 1
    f1_ev = (f"g-go.md discovered in: {', '.join(ide_roots)}" if f1_pass
             else "no IDE command surface with g-go.md found")
    add("F1", "g-go command surface present (discovered IDE roots)", f1_pass, f1_ev)

    # F2. Workspace flag documented in each discovered g-go.md.
    f2_pass = len(ide_roots) >= 1
    f2_ev: List[str] = []
    for ide in ide_roots:
        content = _read(repo_root / ide / "commands" / "g-go.md")
        if "--workspace" not in content:
            f2_pass = False
            f2_ev.append(f"{ide}: missing --workspace")
    if f2_pass:
        f2_ev = [f"--workspace flag documented in all {len(ide_roots)} discovered g-go.md files"]
    add("F2", "Workspace flag documented in g-go.md", f2_pass, "; ".join(f2_ev))

    # F3. Workspace mode rules surface present (workspace + per-repo / marker-only).
    f3_pass = len(ide_roots) >= 1
    f3_ev = []
    for ide in ide_roots:
        content = _read(repo_root / ide / "commands" / "g-go.md")
        has_ws = bool(re.search(r"(?i)Workspace Mode|--workspace", content))
        has_marker = bool(re.search(r"(?i)per-repo|per-root|marker-only|workspace_repos",
                                    content))
        if not (has_ws and has_marker):
            miss = []
            if not has_ws:
                miss.append("workspace-mode")
            if not has_marker:
                miss.append("per-repo/marker-only")
            f3_pass = False
            f3_ev.append(f"{ide}: missing {','.join(miss)}")
    if f3_pass:
        f3_ev = ["Workspace-mode + per-repo/marker-only surfaces present on all "
                 "discovered g-go.md files"]
    add("F3", "Workspace queue / per-repo / marker-only surface present",
        f3_pass, "; ".join(f3_ev))

    # F4. Member-scoped task: manifest resolves >= 1 non-owner member w/ existing path.
    f4_pass = False
    f4_ev = []
    if not manifest_path.is_file():
        f4_ev.append(f"manifest missing at {manifest_path}")
    else:
        manifest_text = _read(manifest_path)
        matches = list(_MANIFEST_ENTRY_RX.finditer(manifest_text))
        resolved = []
        for m in matches:
            mid = m.group("id")
            p = m.group("path").strip()
            if mid not in ("gald3r_dev",) and Path(p).exists():
                resolved.append(f"{mid} => {p}")
        if resolved:
            f4_pass = True
            f4_ev.append(f"Resolved {len(resolved)} non-owner member(s) with existing local_path")
        else:
            f4_ev.append(f"manifest parsed ({len(matches)} entries) but no non-owner "
                         "member local_path exists on disk")
    add("F4", "Manifest resolves at least one member-scoped target",
        f4_pass, "; ".join(f4_ev))

    # F5. Marker-only guard + bootstrap helpers present (relocated home under .gald3r_sys/).
    helper_dir = repo_root / ".gald3r_sys" / "skills" / "g-skl-workspace" / "scripts"
    guard = helper_dir / "check_member_repo_gald3r_guard.ps1"
    bootstrap = helper_dir / "bootstrap_member_gald3r_marker.ps1"
    f5_pass = guard.is_file() and bootstrap.is_file()
    f5_ev = ("guard + bootstrap helpers present under "
             ".gald3r_sys/skills/g-skl-workspace/scripts/" if f5_pass
             else f"missing (guard={guard.is_file()}, bootstrap={bootstrap.is_file()})")
    add("F5", "Marker-only guard + bootstrap helpers present", f5_pass, f5_ev)

    # F6. Per-root dirty member gate documented in g-rl-33 across IDE rule mirrors.
    f6_pass = True
    f6_ev = []
    f6_checked = 0
    for ide in ide_roots:
        rules_dir = repo_root / ide / "rules"
        if not rules_dir.is_dir():
            continue  # not all IDE roots carry a rule mirror
        rules = sorted(rules_dir.glob("g-rl-33-*"))
        if not rules:
            f6_pass = False
            f6_ev.append(f"{ide}: g-rl-33 missing")
            continue
        f6_checked += 1
        content = _read(rules[0])
        if not re.search(r"(?i)per-root|every git root in the computed touch set|"
                         r"Pre-Reconciliation Clean Gate", content):
            f6_pass = False
            f6_ev.append(f"{ide} rl-33: missing per-root touch-set language")
    if f6_checked == 0 and f6_pass:
        f6_ev.append("no IDE rule mirror present to check (skipped)")
    elif f6_pass:
        f6_ev = [f"g-rl-33 per-root touch-set gate present in {f6_checked} IDE rule mirror(s)"]
    add("F6", "Per-root dirty member gate documented in g-rl-33", f6_pass, "; ".join(f6_ev))

    # F7. Marker-only invariant rule (g-rl-36) installed in discovered IDE rule trees.
    f7_pass = True
    f7_ev = []
    f7_checked = 0
    for ide in ide_roots:
        rules_dir = repo_root / ide / "rules"
        if not rules_dir.is_dir():
            continue
        if not sorted(rules_dir.glob("g-rl-36-*")):
            f7_pass = False
            f7_ev.append(f"{ide}: g-rl-36 missing")
            continue
        f7_checked += 1
    if f7_checked == 0 and f7_pass:
        f7_ev.append("no IDE rule mirror present to check (skipped)")
    elif f7_pass:
        f7_ev = [f"g-rl-36 marker-only guard rule present in {f7_checked} IDE rule mirror(s)"]
    add("F7", "Marker-only invariant rule (g-rl-36) installed", f7_pass, "; ".join(f7_ev))

    # F8. Manifest declares controlled members (skip / deferred-path reason source).
    f8_pass = False
    f8_ev = []
    if not manifest_path.is_file():
        f8_ev.append("manifest missing")
    else:
        manifest_text = _read(manifest_path)
        if (re.search(r"(?im)^\s*controlled_members:", manifest_text)
                or re.search(r"(?im)workspace_role:\s*controlled_member", manifest_text)):
            f8_pass = True
            f8_ev.append("manifest declares controlled_members / controlled_member roles")
        else:
            f8_ev.append("manifest has no controlled_members block or controlled_member roles")
    add("F8", "Controlled members declared in manifest (deferred-path source)",
        f8_pass, "; ".join(f8_ev))

    # F9. Swarm workspace coordination surface present on each discovered g-go.md.
    f9_pass = len(ide_roots) >= 1
    f9_ev = []
    for ide in ide_roots:
        content = _read(repo_root / ide / "commands" / "g-go.md")
        if not re.search(r"(?i)--swarm", content):
            f9_pass = False
            f9_ev.append(f"{ide}: missing --swarm coordination surface")
    if f9_pass:
        f9_ev = ["--swarm coordination surface present on all discovered g-go.md files"]
    add("F9", "Swarm workspace coordination surface present", f9_pass, "; ".join(f9_ev))

    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the fixture suite and emit the human or JSON summary."""
    p = argparse.ArgumentParser(
        description="g-go --workspace policy/contract fixtures (T532/T1532)."
    )
    p.add_argument("-Json", "--json", dest="json", action="store_true")
    args = p.parse_args(argv)

    repo_root = REPO_ROOT
    os.chdir(repo_root)
    ide_roots = get_ide_command_roots(repo_root, "g-go.md")
    results = run_fixtures(repo_root)

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed

    if args.json:
        print(json.dumps({
            "suite": "T532 g-go --workspace fixtures (T1532 adapted)",
            "repo_root": str(repo_root),
            "ide_roots": ide_roots,
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        }, indent=2))
    else:
        print("")
        cprint("============================================", "cyan")
        cprint("  g-go --workspace fixture suite (T1532)    ", "cyan")
        cprint("============================================", "cyan")
        cprint(f"  IDE roots discovered: {', '.join(ide_roots)}", "gray")
        for r in results:
            icon = "PASS" if r["pass"] else "FAIL"
            color = "green" if r["pass"] else "red"
            cprint(f"  [{icon}] {r['id']}: {r['name']}", color)
            cprint(f"        {r['evidence']}", "gray")
        print("")
        cprint(f"Summary: {passed}/{total} passed, {failed} failed",
               "green" if failed == 0 else "yellow")
        print("")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
