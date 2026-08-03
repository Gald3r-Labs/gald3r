#!/usr/bin/env python3
"""Python port of codeowners_gen.ps1 (T1585).

Generate .github/CODEOWNERS from gald3r subsystem specs (T1299).

Reads every .gald3r/subsystems/**/*.md spec, parses the YAML frontmatter
``owners:`` and ``locations.code:`` inline lists, and emits one CODEOWNERS
line per code path for each subsystem that declares non-empty owners.

Idempotent and safe to re-run. The generated (auto) block is rewritten each
run; anything the user adds below the ``# CUSTOM ENTRIES BELOW`` marker is
preserved verbatim. No-op (exit 0, message) when no subsystem declares owners.
"""
# @subsystems: PLATFORM_INTEGRATION
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
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable via the installed package.

    T274 (P5-E blocker): the pre-retirement ".gald3r_sys/engine/src" fallback
    walk is removed -- ".gald3r_sys/" is actively purged from every project
    by the deploy pipeline (T335) and never exists in a fresh install, so
    that branch was permanently dead code, not a real fallback.
    """
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        return False


_HAS_UTILS = _bootstrap_engine_utils()

CUSTOM_MARKER = "# CUSTOM ENTRIES BELOW"


def _is_gitignored(path: Path) -> "bool | None":
    """T516: cheap, authoritative gitignore check (same guard shape as T512's
    `find_gald3r_root` fix, commit 3682aa64) -- delegates to `git
    check-ignore -v` rather than reimplementing `.gitignore` pattern
    matching. `None` (check could not run at all) is treated as fail-open
    by the caller."""
    try:
        result = subprocess.run(  # noqa: S603 -- fixed argv, no shell
            ["git", "check-ignore", "-v", str(path)],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def find_project_root(
    start: Optional[str] = None, *, ambiguous_candidates: "List[Path] | None" = None
) -> str:
    """Walk up (max 12 levels) from start/script dir to the .gald3r marker; else cwd.

    T516 (T512 inventory row 20): a candidate whose `.gald3r/` is gitignored
    is refused (never adopted -- the walk continues upward for the real,
    tracked root), same guard shape as `find_gald3r_root`'s T512 fix. A
    second, non-gitignored candidate further up than the nearest one is
    appended to `ambiguous_candidates` (when supplied) but the NEAREST
    candidate still wins -- no behavior change for the ordinary
    single-`.gald3r/` case.
    """
    d = Path(start).resolve() if start else Path(__file__).resolve().parent
    resolved: Optional[Path] = None
    for _ in range(12):
        marker = d / ".gald3r"
        if marker.exists():
            if _is_gitignored(marker):
                pass  # T516: refuse -- never silently adopt a decoy.
            elif resolved is None:
                resolved = d
            elif ambiguous_candidates is not None:
                ambiguous_candidates.append(d)
        if d.parent == d:
            break
        d = d.parent
    if resolved is not None:
        return str(resolved)
    return str(Path.cwd())


def _split_inline_list(raw: str) -> List[str]:
    """Split an inline YAML list body ``a, "b", 'c'`` into clean items."""
    items = []
    for part in raw.split(","):
        item = part.strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def read_spec_owners(path: Path) -> Optional[Dict[str, object]]:
    """Minimal frontmatter reader: owners[] and locations.code paths[] for a spec."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not lines:
        return None
    # frontmatter is between the first two '---' fences
    fence: List[int] = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fence.append(i)
            if len(fence) == 2:
                break
    if len(fence) < 2:
        return None
    fm = lines[fence[0] + 1:fence[1]]

    owners: List[str] = []
    code_paths: List[str] = []
    in_locations = False
    for l in fm:
        # owners: [a, "@b/c"]   (inline list form)
        m = re.match(r"^\s*owners\s*:\s*\[(.*)\]\s*$", l)
        if m:
            owners = _split_inline_list(m.group(1))
            continue
        if re.match(r"^\s*locations\s*:\s*$", l):
            in_locations = True
            continue
        if in_locations:
            # leave locations block when a non-indented key appears
            if re.match(r"^\S", l):
                in_locations = False
            else:
                m = re.match(r"^\s+code\s*:\s*\[(.*)\]\s*$", l)
                if m:
                    code_paths = _split_inline_list(m.group(1))
    if not owners:
        return None
    return {"Owners": owners, "CodePaths": code_paths, "Spec": path.name}


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Generate .github/CODEOWNERS from gald3r subsystem specs (T1299)."
    )
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=None)
    p.add_argument("-DryRun", "--dry-run", dest="dry_run", action="store_true",
                   help="Print the would-be CODEOWNERS to stdout without writing the file.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: parse specs -> compose auto block -> preserve custom block -> write."""
    args = build_parser().parse_args(argv)
    root = Path(find_project_root(args.project_root))
    subsys_dir = root / ".gald3r" / "subsystems"
    if not subsys_dir.is_dir():
        print(f"No .gald3r/subsystems/ directory found at {root}. Nothing to do.")
        return 0

    specs = [f for f in sorted(subsys_dir.rglob("*.md"))
             if f.is_file() and not f.name.startswith("SUBSYSTEM")]

    entries: List[Dict[str, str]] = []
    for s in specs:
        info = read_spec_owners(s)
        if not info:
            continue
        owners = info["Owners"]
        assert isinstance(owners, list)
        owner_str = " ".join(o if o.startswith("@") else f"@{o}" for o in owners)
        code_paths = info["CodePaths"]
        assert isinstance(code_paths, list)
        for p in code_paths:
            # normalize to a leading-slash repo path pattern
            pat = ("/" + re.sub(r"^[./]+", "", p)).replace("\\", "/")
            entries.append({"Pattern": pat, "Owners": owner_str, "Spec": str(info["Spec"])})

    if not entries:
        print("No subsystem declares a non-empty owners: list. "
              "CODEOWNERS not generated (no-op).")
        return 0

    nl = "\n"
    auto: List[str] = []
    auto.append("# Auto-generated by g-codeowners-gen -- do not hand-edit above the marker.")
    auto.append("# Source: .gald3r/subsystems/*.md frontmatter (owners: + locations.code:).")
    auto.append("# Regenerate: @g-codeowners-gen  (helper: codeowners_gen.py)")
    auto.append("")
    for e in sorted(entries, key=lambda x: x["Pattern"]):
        auto.append(f"{e['Pattern']} {e['Owners']}")
    auto.append("")
    auto.append(CUSTOM_MARKER)
    auto_block = nl.join(auto)

    codeowners_path = root / ".github" / "CODEOWNERS"

    # Preserve any existing custom entries below the marker.
    custom_block = ""
    if codeowners_path.is_file():
        existing = codeowners_path.read_text(encoding="utf-8", errors="replace")
        idx = existing.find(CUSTOM_MARKER)
        if idx >= 0:
            custom_block = existing[idx + len(CUSTOM_MARKER):].lstrip("\r\n")

    final = auto_block
    if custom_block:
        final += nl + custom_block.rstrip() + nl
    else:
        final += nl

    spec_count = len({e["Spec"] for e in entries})
    if args.dry_run:
        print(f"--- DRY RUN: .github/CODEOWNERS ({len(entries)} entries from "
              f"{spec_count} subsystem(s)) ---")
        print(final)
        return 0

    codeowners_path.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 without BOM (avoid the BUG-016/041 mojibake class)
    codeowners_path.write_text(final, encoding="utf-8")
    print(f"Wrote {codeowners_path} ({len(entries)} ownership line(s)); "
          "custom entries preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
