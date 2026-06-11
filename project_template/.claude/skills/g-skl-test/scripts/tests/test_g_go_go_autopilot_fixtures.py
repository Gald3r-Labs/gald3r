#!/usr/bin/env python3
"""Python port of test_g_go_go_autopilot_fixtures.ps1 (T1585).

Verification fixtures for the ``g-go-go`` maximal autopilot command (T533
contract), adapted for the gald3r_templates repo (T1532).

``g-go-go`` is an LLM-executed prompt; these fixtures verify that the
behavior-contract surfaces are intact across the IDE command surfaces PRESENT
IN THIS REPO (discovered dynamically: any top-level ``.<ide>/commands/
g-go-go.md``) and that the safety primitives the autopilot depends on are
present. Missing surfaces fail closed.

Fixtures F1-F13 mirror the PS1 one-for-one. Exit 0 = all pass, 1 = failures.
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
from typing import Dict, List, Optional, Sequence, Tuple


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


def test_across_gogo(repo_root: Path, ide_roots: List[str],
                     patterns: List[str], description: str) -> Tuple[bool, List[str]]:
    """Require all regexes present in every discovered g-go-go.md."""
    if len(ide_roots) < 1:
        return False, ["no g-go-go.md command surface found"]
    all_pass = True
    missing: List[str] = []
    for ide in ide_roots:
        content = _read(repo_root / ide / "commands" / "g-go-go.md")
        for pat in patterns:
            if not re.search(pat, content):
                all_pass = False
                missing.append(f"{ide}: {description}")
                break
    return all_pass, sorted(set(missing))


def run_fixtures(repo_root: Path) -> List[Dict[str, object]]:
    """Run F1-F13 and return the result rows."""
    ide_roots = get_ide_command_roots(repo_root, "g-go-go.md")
    manifest_path = repo_root / MANIFEST_REL
    results: List[Dict[str, object]] = []

    def add(fid: str, name: str, passed: bool, evidence: str) -> None:
        results.append({"id": fid, "name": name, "pass": passed, "evidence": evidence})

    def across(fid: str, name: str, patterns: List[str], description: str,
               pass_msg: str) -> None:
        ok, missing = test_across_gogo(repo_root, ide_roots, patterns, description)
        ev = [pass_msg] if ok else missing
        add(fid, name, ok, "; ".join(ev))

    # F1. Command surface present.
    f1_pass = len(ide_roots) >= 1
    f1_ev = (f"g-go-go.md discovered in: {', '.join(ide_roots)}" if f1_pass
             else "no IDE command surface with g-go-go.md found")
    add("F1", "Command surface present (discovered IDE roots)", f1_pass, f1_ev)

    # F2. Default = workspace + swarm rolling loop.
    across("F2", "Default = workspace + swarm + rolling loop with budget",
           [r"(?i)--swarm", r"(?i)--workspace", r"(?i)loop|rolling|budget"],
           "missing default workspace+swarm rolling-loop surface",
           "All discovered g-go-go.md files surface swarm+workspace rolling loop with budget")

    # F3. File-first fallback documented.
    across("F3", "File-first fallback documented",
           [r"(?i)file-first|file first|fallback", r"(?i)backend"],
           "missing file-first / backend-optional fallback language",
           "All discovered g-go-go.md files document file-first / backend-optional fallback")

    # F4. Hard stops surface present.
    across("F4", "Hard stops surface present",
           [r"(?i)hard stop|stop condition|stop reason|Run budget exhausted|No runnable work"],
           "missing hard-stop / stop-condition surface",
           "All discovered g-go-go.md files document hard-stop conditions")

    # F5. Member-scoped routing gates documented.
    across("F5", "Member-scoped routing gates documented",
           [r"(?i)workspace_repos", r"(?i)workspace_touch_policy|touch_policy|per-repo|per-root"],
           "missing workspace_repos / workspace_touch_policy routing",
           "All discovered g-go-go.md files reference workspace_repos + touch-policy / "
           "per-repo gates")

    # F6. Marker-only protection language.
    across("F6", "Marker-only `.gald3r/` invariant referenced",
           [r"(?i)marker-only"],
           "missing marker-only invariant language",
           "All discovered g-go-go.md files reference the marker-only `.gald3r/` invariant")

    # F7. Rolling-loop iteration / budget mechanics.
    across("F7", "Rolling-loop iteration/budget mechanics documented",
           [r"(?i)budget", r"(?i)loop|iteration|iter"],
           "missing iteration/budget loop mechanics",
           "All discovered g-go-go.md files document iter/budget loop mechanics")

    # F8. Verification independence -- reviewers spawned without Phase 1 context.
    across("F8", "Verification independence preserved across loop",
           [r"(?i)fresh reviewer|no Phase 1 context|independent review|never self-verify|"
            r"adversarial"],
           "missing verification-independence language",
           "All discovered g-go-go.md files preserve adversarial review independence")

    # F9. Heartbeat output surface.
    across("F9", "Heartbeat output surface present",
           [r"(?i)heartbeat"],
           "missing heartbeat surface",
           "All discovered g-go-go.md files include a heartbeat surface")

    # F10. Final summary surface.
    across("F10", "Final summary surface present",
           [r"(?i)final summary|session summary"],
           "missing final-summary surface",
           "All discovered g-go-go.md files include a final/session summary surface")

    # F11. Bare /g-go preserved -- autopilot is explicit, not an alias.
    across("F11", "Bare /g-go preserved (autopilot is explicit opt-in)",
           [r"(?i)bare\s*`?/?g-go`?", r"(?i)unchanged|explicit|not an alias|separate"],
           "missing bare /g-go preservation language",
           "All discovered g-go-go.md files preserve bare /g-go as a separate explicit command")

    # F12. Manifest resolves -- workspace manifest parseable for autopilot member work.
    f12_pass = False
    f12_ev = []
    if not manifest_path.is_file():
        f12_ev.append(f"manifest missing at {manifest_path}")
    else:
        manifest_text = _read(manifest_path)
        matches = list(_MANIFEST_ENTRY_RX.finditer(manifest_text))
        if len(matches) >= 2:
            f12_pass = True
            f12_ev.append(f"Manifest parseable; {len(matches)} repository entries "
                          "with id+local_path")
        else:
            f12_ev.append(f"manifest has too few parseable entries ({len(matches)})")
    add("F12", "Workspace manifest parseable for autopilot", f12_pass, "; ".join(f12_ev))

    # F13. Guard helper present (relocated home under .gald3r_sys/).
    guard = (repo_root / ".gald3r_sys" / "skills" / "g-skl-workspace" / "scripts"
             / "check_member_repo_gald3r_guard.ps1")
    f13_pass = guard.is_file()
    f13_ev = ("guard helper present at .gald3r_sys/skills/g-skl-workspace/scripts/"
              if f13_pass else "guard helper missing")
    add("F13", "Marker-only guard helper present", f13_pass, f13_ev)

    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the fixture suite and emit the human or JSON summary."""
    p = argparse.ArgumentParser(
        description="g-go-go autopilot policy/contract fixtures (T533/T1532)."
    )
    p.add_argument("-Json", "--json", dest="json", action="store_true")
    args = p.parse_args(argv)

    repo_root = REPO_ROOT
    os.chdir(repo_root)
    ide_roots = get_ide_command_roots(repo_root, "g-go-go.md")
    results = run_fixtures(repo_root)

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed

    if args.json:
        print(json.dumps({
            "suite": "T533 g-go-go autopilot fixtures (T1532 adapted)",
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
        cprint("  g-go-go autopilot fixture suite (T1532)   ", "cyan")
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
