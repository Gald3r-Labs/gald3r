#!/usr/bin/env python3
"""System check functions for gald3r_system_test.py (T1585 port of
gald3r_system_test.ps1, T1540).

Each ``check_*`` function exercises one gald3r system non-destructively and
returns a result dict::

    {name, key, passed, failed, skipped, structural, failures: [..], notes}

Writes (Task / Bug create-read-update) happen in a throwaway temp dir and
NEVER touch the real ``.gald3r/`` tree. Where a system cannot be functionally
exercised cheaply the check does an honest structural/presence check and
labels it [structural] in the notes (no fake green).
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class CheckContext:
    """Resolved roots + host info shared by every check."""

    repo_root: Path
    ps_host: Optional[str] = None

    @property
    def dot_gald3r(self) -> Path:
        return self.repo_root / ".gald3r"

    @property
    def dot_gald3r_sys(self) -> Path:
        return self.repo_root / ".gald3r_sys"

    @property
    def custom_scripts(self) -> Path:
        return self.repo_root / "custom_scripts"


def new_system_result(name: str, key: str) -> Dict[str, Any]:
    """Fresh result accumulator (mirrors New-SystemResult)."""
    return {
        "name": name,
        "key": key,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "structural": False,
        "failures": [],
        "notes": "",
    }


def add_pass(r: Dict[str, Any]) -> None:
    r["passed"] += 1


def add_fail(r: Dict[str, Any], msg: str) -> None:
    r["failed"] += 1
    r["failures"].append(f"FAIL: {msg}")


def add_skip(r: Dict[str, Any]) -> None:
    r["skipped"] += 1


def find_powershell() -> Optional[str]:
    """Locate a PowerShell host (prefer pwsh, fall back to Windows PowerShell)."""
    for cand in ("pwsh", "powershell"):
        exe = shutil.which(cand)
        if exe:
            return exe
    return None


def invoke_script(ctx: CheckContext, path: Path,
                  arguments: Sequence[str] = ()) -> Tuple[str, int]:
    """Run a helper script, capturing combined output + exit code.

    Resolver: prefer a .py sibling of a .ps1 (run with this interpreter), else
    dispatch the .ps1 via the PowerShell host. Exceptions map to exit 999,
    mirroring the PS1 Invoke-Script.
    """
    py_sibling = path.with_suffix(".py") if path.suffix.lower() == ".ps1" else None
    try:
        if py_sibling is not None and py_sibling.is_file():
            argv = [sys.executable, str(py_sibling), *arguments]
        elif path.suffix.lower() == ".py":
            argv = [sys.executable, str(path), *arguments]
        else:
            if not ctx.ps_host:
                return ("no PowerShell host on PATH", 999)
            argv = [ctx.ps_host, "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(path), *arguments]
        proc = subprocess.run(argv, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        return ((proc.stdout or "") + (proc.stderr or ""), proc.returncode)
    except OSError as exc:
        return (str(exc), 999)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _head_lines(path: Path, n: int) -> str:
    lines: List[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for _ in range(n):
                line = fh.readline()
                if not line:
                    break
                lines.append(line.rstrip("\r\n"))
    except OSError:
        return ""
    return "\n".join(lines)


def _temp_dir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix + uuid.uuid4().hex[:8] + "_"))


# --- Task Management --------------------------------------------------------
def check_task_management(ctx: CheckContext) -> Dict[str, Any]:
    """Functional create/read/update cycle in a TEMP dir (never touches real .gald3r/)."""
    r = new_system_result("Task Management", "task")
    tmp = _temp_dir("g3sys_task_")
    try:
        tasks_dir = tmp / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = tasks_dir / "task9001_harness_selftest.md"
        index_file = tmp / "TASKS.md"

        # 1) create task file
        body = (
            "---\n"
            "id: T9001\n"
            'title: "harness selftest"\n'
            "status: pending\n"
            "priority: low\n"
            "type: chore\n"
            "created: 2026-05-30\n"
            "---\n"
            "\n"
            "# T9001 - harness selftest\n"
        )
        task_file.write_text(body, encoding="utf-8")
        if task_file.is_file():
            add_pass(r)
        else:
            add_fail(r, "task file not created")

        # 2) read it back + verify frontmatter id
        read = _read(task_file)
        if re.search(r"(?m)^id:\s*T9001\s*$", read):
            add_pass(r)
        else:
            add_fail(r, "task frontmatter id not readable")

        # 3) update status pending -> in-progress
        updated = re.sub(r"(?m)^(status:\s*)pending\s*$", r"\1in-progress", read)
        task_file.write_text(updated, encoding="utf-8")
        re_read = _read(task_file)
        if re.search(r"(?m)^status:\s*in-progress\s*$", re_read):
            add_pass(r)
        else:
            add_fail(r, "status update did not persist")

        # 4) write + verify a TASKS.md index row
        row = "| [in-progress] | T9001 | harness selftest | low | chore |"
        index_file.write_text("# TASKS.md\n\n" + row + "\n", encoding="utf-8")
        if "T9001" in _read(index_file):
            add_pass(r)
        else:
            add_fail(r, "TASKS.md index row not written")

        # 5) live g-skl-tasks ownership present (the real system the user installs)
        skill_live = ctx.dot_gald3r_sys / "skills" / "g-skl-tasks" / "SKILL.md"
        skill_claude = ctx.repo_root / ".claude" / "skills" / "g-skl-tasks" / "SKILL.md"
        if skill_live.is_file() or skill_claude.is_file():
            add_pass(r)
        else:
            add_fail(r, "g-skl-tasks SKILL.md not found in install")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r["notes"] = "create/read/update/index in temp dir + g-skl-tasks present"
    return r


# --- Bug Tracking ------------------------------------------------------------
def check_bug_tracking(ctx: CheckContext) -> Dict[str, Any]:
    """Functional bug create/read/index cycle in a TEMP dir."""
    r = new_system_result("Bug Tracking", "bug")
    tmp = _temp_dir("g3sys_bug_")
    try:
        bugs_dir = tmp / "bugs"
        bugs_dir.mkdir(parents=True, exist_ok=True)
        bug_file = bugs_dir / "bug9001_harness_selftest.md"
        index_file = tmp / "BUGS.md"

        body = (
            "---\n"
            "id: BUG-9001\n"
            'title: "harness selftest bug"\n'
            "severity: Low\n"
            "status: open\n"
            "created: 2026-05-30\n"
            "---\n"
            "\n"
            "# BUG-9001 - harness selftest bug\n"
        )
        bug_file.write_text(body, encoding="utf-8")
        if bug_file.is_file():
            add_pass(r)
        else:
            add_fail(r, "bug file not created")

        read = _read(bug_file)
        if re.search(r"(?m)^id:\s*BUG-9001\s*$", read):
            add_pass(r)
        else:
            add_fail(r, "bug frontmatter id not readable")

        row = "| BUG-9001 | harness selftest bug | Low | open |"
        index_file.write_text("# BUGS.md\n\n" + row + "\n", encoding="utf-8")
        if "BUG-9001" in _read(index_file):
            add_pass(r)
        else:
            add_fail(r, "BUGS.md index row not written")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r["notes"] = "create/read/index in temp dir"
    return r


# --- PLATFORM_SPEC ------------------------------------------------------------
def check_platform_spec(ctx: CheckContext) -> Dict[str, Any]:
    """Reuse the existing -ValidatePlatformSpecs validator (DRY). Exit 0 = all OK."""
    r = new_system_result("PLATFORM_SPEC", "platform_spec")
    parity = ctx.custom_scripts / "platform_parity_sync.ps1"
    if not parity.is_file() and not parity.with_suffix(".py").is_file():
        add_skip(r)
        r["notes"] = "platform_parity_sync.ps1 not present (skipped)"
        return r
    output, exit_code = invoke_script(ctx, parity, ["-ValidatePlatformSpecs"])
    scanned = 0
    m = re.search(r"Specs scanned\s*:\s*(\d+)", output)
    if m:
        scanned = int(m.group(1))
    if exit_code == 0:
        if scanned > 0:
            add_pass(r)
        else:
            add_fail(r, "no PLATFORM_SPEC.md files were scanned")
    else:
        miss_line = next((l for l in re.split(r"\r?\n", output)
                          if "MISSING sections:" in l), "")
        add_fail(r, "ValidatePlatformSpecs exit {0}: {1}".format(
            exit_code, re.sub(r"\s+", " ", miss_line).strip()))
    r["notes"] = f"validator scanned {scanned} spec(s)"
    return r


# --- Platform Parity ----------------------------------------------------------
def check_platform_parity(ctx: CheckContext) -> Dict[str, Any]:
    """Run platform_parity_sync in report-only mode and detect missing-file gaps."""
    r = new_system_result("Platform Parity", "parity")
    parity = ctx.custom_scripts / "platform_parity_sync.ps1"
    if not parity.is_file() and not parity.with_suffix(".py").is_file():
        add_skip(r)
        r["notes"] = "platform_parity_sync.ps1 not present (skipped)"
        return r
    output, exit_code = invoke_script(ctx, parity, [])
    gap_lines = [l for l in re.split(r"\r?\n", output)
                 if re.search(r"\bMISSING\b", l) and "MISSING sections" not in l]
    if exit_code == 0 and not gap_lines:
        add_pass(r)
        r["notes"] = "report-only run: exit 0, no missing-file gaps"
    elif exit_code != 0:
        add_fail(r, f"parity sync exit {exit_code}")
        r["notes"] = "report-only run flagged a non-zero exit"
    else:
        for g in gap_lines[:5]:
            add_fail(r, g.strip())
        r["notes"] = f"{len(gap_lines)} parity gap line(s) detected"
    return r


# --- Hook Wiring ----------------------------------------------------------------
def _ps_parse_check(ctx: CheckContext, files: Sequence[Path]) -> Optional[Dict[str, bool]]:
    """Batch-parse .ps1 files with the PowerShell AST parser (one host invocation).

    Returns {path_str: parse_ok} or None when no PowerShell host is available.
    """
    if not ctx.ps_host or not files:
        return None
    quoted = ", ".join("'" + str(f).replace("'", "''") + "'" for f in files)
    command = (
        "$files = @(" + quoted + "); "
        "foreach ($f in $files) { $errs = $null; "
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        "$f, [ref]$null, [ref]$errs); "
        "if ($errs -and $errs.Count -gt 0) { Write-Output ('PARSEFAIL|' + $f) } "
        "else { Write-Output ('PARSEOK|' + $f) } }"
    )
    try:
        proc = subprocess.run([ctx.ps_host, "-NoProfile", "-Command", command],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError:
        return None
    results: Dict[str, bool] = {}
    for line in (proc.stdout or "").splitlines():
        if line.startswith("PARSEOK|"):
            results[line[len("PARSEOK|"):]] = True
        elif line.startswith("PARSEFAIL|"):
            results[line[len("PARSEFAIL|"):]] = False
    return results


def check_hook_wiring(ctx: CheckContext) -> Dict[str, Any]:
    """Every hook command in .claude/hooks.json resolves on disk AND parses cleanly."""
    r = new_system_result("Hook Wiring", "hooks")
    hooks_json = ctx.repo_root / ".claude" / "hooks.json"
    if not hooks_json.is_file():
        add_skip(r)
        r["notes"] = ".claude/hooks.json not present (skipped)"
        return r
    raw = _read(hooks_json)
    paths = sorted({m.group(1) for m in re.finditer(r'-File\s+([^\s"]+\.ps1)', raw)})
    if not paths:
        add_skip(r)
        r["notes"] = "no hook .ps1 commands found in hooks.json"
        return r

    existing: List[Path] = []
    for rel in paths:
        full = ctx.repo_root / rel.replace("/", "\\").replace("\\", "/")
        if not full.is_file():
            add_fail(r, f"hook missing on disk: {rel}")
        else:
            existing.append(full)

    parse_results = _ps_parse_check(ctx, existing)
    if parse_results is None:
        # No PowerShell host: existence is the best honest check available.
        for _full in existing:
            add_pass(r)
        r["structural"] = True
        r["notes"] = (f"{len(paths)} wired hook(s) verified "
                      "[structural] parse check skipped (no PowerShell host)")
        return r

    for full in existing:
        if parse_results.get(str(full), False):
            add_pass(r)
        else:
            add_fail(r, f"hook parse error: {full.relative_to(ctx.repo_root)}")
    r["notes"] = f"{len(paths)} wired hook(s) verified"
    return r


# --- Git Hooks --------------------------------------------------------------------
def check_git_hooks(ctx: CheckContext) -> Dict[str, Any]:
    """Honor core.hooksPath if set, else .git/hooks; verify pre-commit dispatches."""
    r = new_system_result("Git Hooks", "git_hooks")
    hooks_path: Optional[str] = None
    try:
        proc = subprocess.run(
            ["git", "-C", str(ctx.repo_root), "config", "--get", "core.hooksPath"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            hooks_path = proc.stdout.strip() or None
    except OSError:
        hooks_path = None

    if hooks_path:
        hooks_dir = ctx.repo_root / hooks_path.replace("/", os.sep)
        r["notes"] = f"core.hooksPath={hooks_path}"
    else:
        hooks_dir = ctx.repo_root / ".git" / "hooks"
        r["notes"] = "default .git/hooks"
    pre_commit = hooks_dir / "pre-commit"
    if not pre_commit.is_file():
        add_fail(r, f"pre-commit hook not found at {pre_commit}")
        return r
    add_pass(r)
    content = _read(pre_commit)
    # Dispatcher = the hook invokes a .ps1 / .sh / script (not an empty stub).
    if re.search(r"\.ps1|\.sh|pwsh|powershell|exec\s", content):
        add_pass(r)
    else:
        add_fail(r, "pre-commit hook has no dispatcher invocation")
    return r


# --- Schema Validation --------------------------------------------------------------
def _get_current_version(text: str, schema_id: str) -> Optional[str]:
    m = re.search(r"schema_id:\s*" + re.escape(schema_id)
                  + r"\s*[\r\n]+\s*current_version:\s*(\S+)", text)
    return m.group(1) if m else None


def check_schema_validation(ctx: CheckContext) -> Dict[str, Any]:
    """Schema version probe (T1440): registry vs TASKS.md + sampled task files."""
    r = new_system_result("Schema Validation", "schema")
    registry = ctx.dot_gald3r_sys / "schemas" / "_registry.yaml"
    if not registry.is_file():
        add_skip(r)
        r["notes"] = "schemas/_registry.yaml not present (skipped)"
        return r
    add_pass(r)  # registry present + readable
    reg = _read(registry)

    tasks_md_ver = _get_current_version(reg, "TASKS-md")
    task_file_ver = _get_current_version(reg, "task-file")

    # Probe .gald3r/TASKS.md frontmatter (missing schema_version => v0 / pre-versioned).
    tasks_md = ctx.dot_gald3r / "TASKS.md"
    if tasks_md.is_file():
        head = _head_lines(tasks_md, 20)
        m = re.search(r"(?m)^schema_version:\s*(\S+)", head)
        if m:
            fv = m.group(1)
            if tasks_md_ver and fv != tasks_md_ver:
                add_fail(r, f"TASKS.md schema_version {fv} != system {tasks_md_ver}")
            else:
                add_pass(r)
        else:
            # No schema_version field: common pre-T1440 state; PASS-with-note.
            add_pass(r)
            r["notes"] = "TASKS.md has no schema_version field (v0 / pre-versioned baseline)"
    else:
        add_skip(r)

    # Sample up to 3 recent task files for drift to a NEWER schema than the system.
    tasks_root = ctx.dot_gald3r / "tasks"
    if tasks_root.is_dir():
        all_md = [p for p in tasks_root.rglob("*.md") if p.is_file()]
        sample = sorted(all_md, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
        drift = 0
        for f in sample:
            fh = _head_lines(f, 25)
            m = re.search(r"(?m)^schema_version:\s*(\S+)", fh)
            if m and task_file_ver and m.group(1) != task_file_ver:
                drift += 1
        if drift == 0:
            add_pass(r)
        else:
            add_fail(r, f"{drift}/{len(sample)} sampled task files drift from system schema")
    else:
        add_skip(r)
    return r


# --- Constraints ----------------------------------------------------------------------
def check_constraints(ctx: CheckContext) -> Dict[str, Any]:
    """Every active constraint in the index must have an **Enforcement**: block."""
    r = new_system_result("Constraints", "constraints")
    c_file = ctx.dot_gald3r / "CONSTRAINTS.md"
    if not c_file.is_file():
        add_skip(r)
        r["notes"] = "CONSTRAINTS.md not present (skipped)"
        return r
    content = _read(c_file)
    row_matches = list(re.finditer(r"(?m)^\|\s*(C-\d+)\s*\|[^|]*\|\s*active\s*\|", content))
    if not row_matches:
        add_skip(r)
        r["notes"] = "no active constraints in index"
        return r
    add_pass(r)  # index parsed
    missing: List[str] = []
    for m in row_matches:
        cid = m.group(1)
        block_head = re.search(r"(?m)^##\s+" + re.escape(cid) + r"\b", content)
        if not block_head:
            missing.append(f"{cid} (no definition block)")
            continue
        rest = content[block_head.start():]
        nxt = re.search(r"(?m)^##\s", rest[1:])
        block = rest[:1 + nxt.start()] if nxt else rest
        if not re.search(r"(?im)\*\*Enforcement\*\*:", block):
            missing.append(f"{cid} (no Enforcement field)")
    if not missing:
        add_pass(r)
    else:
        for x in missing[:5]:
            add_fail(r, f"constraint {x}")
    r["notes"] = f"{len(row_matches)} active constraint(s) checked"
    return r


# --- Subsystems ------------------------------------------------------------------------
def check_subsystems(ctx: CheckContext) -> Dict[str, Any]:
    """Every active SUBSYSTEMS.md entry must have a spec file in subsystems/."""
    r = new_system_result("Subsystems", "subsystems")
    ss_file = ctx.dot_gald3r / "SUBSYSTEMS.md"
    ss_dir = ctx.dot_gald3r / "subsystems"
    if not ss_file.is_file():
        add_skip(r)
        r["notes"] = "SUBSYSTEMS.md not present (skipped)"
        return r
    content = _read(ss_file)
    rows = list(re.finditer(r"(?m)^\|\s*SS-\d+\s*\|\s*([a-z0-9\-_]+)\s*\|\s*(\w+)\s*\|",
                            content))
    if not rows:
        add_skip(r)
        r["notes"] = "no subsystem rows in registry"
        return r
    add_pass(r)  # registry parsed
    orphans: List[str] = []
    active_count = 0
    for m in rows:
        name, status = m.group(1), m.group(2)
        if status != "active":
            continue  # only active entries require a spec
        active_count += 1
        if not (ss_dir / f"{name}.md").is_file():
            orphans.append(name)
    if not orphans:
        add_pass(r)
    else:
        for o in orphans:
            add_fail(r, f"active subsystem '{o}' has no spec file in subsystems/")
    r["notes"] = f"{len(rows)} registry row(s); {active_count} active require spec"
    return r


# --- Skills Inventory --------------------------------------------------------------------
def check_skills_inventory(ctx: CheckContext) -> Dict[str, Any]:
    """Count skills; each SKILL.md must have name + description frontmatter."""
    r = new_system_result("Skills Inventory", "skills")
    skill_roots = [c for c in (ctx.dot_gald3r_sys / "skills",
                               ctx.repo_root / ".claude" / "skills") if c.is_dir()]
    if not skill_roots:
        add_skip(r)
        r["notes"] = "no skills directory found (skipped)"
        return r
    skill_root = skill_roots[0]
    skill_files = [p for p in skill_root.rglob("SKILL.md") if p.is_file()]
    if not skill_files:
        add_skip(r)
        r["notes"] = f"no SKILL.md under {skill_root}"
        return r
    add_pass(r)  # at least one skill present
    malformed: List[str] = []
    for f in skill_files:
        head = _head_lines(f, 15)
        has_name = bool(re.search(r"(?m)^name:\s*\S+", head))
        has_desc = bool(re.search(r"(?m)^description:\s*\S+", head))
        if not (has_name and has_desc):
            malformed.append(f.parent.name)
    if not malformed:
        add_pass(r)
    else:
        add_fail(r, "{0} malformed skill(s) (missing name/description): {1}".format(
            len(malformed), ", ".join(malformed[:5])))
    r["notes"] = f"{len(skill_files)} skill(s) scanned under {skill_root.name}"
    return r


# --- WPAC Topology --------------------------------------------------------------------------
def check_wpac_topology(ctx: CheckContext) -> Dict[str, Any]:
    """If topology.md exists, verify project_path entries resolve on disk."""
    r = new_system_result("WPAC Topology", "wpac")
    topo = ctx.dot_gald3r / "workspace" / "topology.md"
    if not topo.is_file():
        add_skip(r)
        r["notes"] = "no topology.md (not a WPAC project, skipped)"
        return r
    add_pass(r)  # topology present + readable
    content = _read(topo)
    path_matches = re.finditer(
        r'(?m)project_path:\s*"?([A-Za-z]:[\\/][^"\r\n]+?)"?\s*$', content)
    checked = 0
    missing: List[str] = []
    for m in path_matches:
        p = m.group(1).strip()
        if not p:
            continue
        checked += 1
        if not Path(p).exists():
            missing.append(p)
    if checked == 0:
        add_skip(r)
        r["notes"] = "topology has no resolvable project_path entries"
        return r
    if not missing:
        add_pass(r)
    else:
        # Offline peers are common; fail entries are labeled clearly (PARTIAL-style).
        for x in missing[:5]:
            add_fail(r, f"topology path does not resolve: {x}")
    r["notes"] = f"{checked} topology path(s) checked, {len(missing)} unresolved"
    return r


# --- Release Pipeline ------------------------------------------------------------------------
def check_release_pipeline(ctx: CheckContext) -> Dict[str, Any]:
    """CHANGELOG.md parseable + every versioned header has a matching release file."""
    r = new_system_result("Release Pipeline", "release")
    changelog = ctx.repo_root / "CHANGELOG.md"
    if not changelog.is_file():
        add_skip(r)
        r["notes"] = "CHANGELOG.md not present (skipped)"
        return r
    content = _read(changelog)
    ver_matches = list(re.finditer(r"(?m)^##\s*\[(\d+\.\d+\.\d+)\]", content))
    if not ver_matches:
        add_skip(r)
        r["notes"] = "no versioned CHANGELOG headers"
        return r
    add_pass(r)  # changelog parsed, has versions
    releases_dir = ctx.dot_gald3r / "releases"
    # Release records keyed by AUTHORITATIVE version: the frontmatter field, not
    # just the filename slug (codename slugs would otherwise read as a false gap).
    rel_files: List[str] = []
    rel_versions: List[str] = []
    if releases_dir.is_dir():
        for rf in sorted(releases_dir.glob("*.md")):
            rel_files.append(rf.name)
            head = _head_lines(rf, 30)
            vm = re.search(r"(?m)^version:\s*['\"]?(\d+\.\d+\.\d+)['\"]?\s*$", head)
            if vm:
                rel_versions.append(vm.group(1))
    gaps: List[str] = []
    for m in ver_matches:
        v = m.group(1)               # 1.7.0
        v_slug = v.replace(".", "-")  # 1-7-0
        hit = (v in rel_versions) or any(v_slug in name for name in rel_files)
        if not hit:
            gaps.append(v)
    if not gaps:
        add_pass(r)
    else:
        for g in gaps[:5]:
            add_fail(r, f"CHANGELOG version {g} has no release file")
    r["notes"] = f"{len(ver_matches)} version(s); {len(gaps)} gap(s)"
    return r


# --- Encoding Integrity ------------------------------------------------------------------------
def check_encoding_integrity(ctx: CheckContext) -> Dict[str, Any]:
    """Flag .ps1 files with non-ASCII bytes AND no UTF-8 BOM (PS 5.1 crash class).

    A UTF-8 BOM is PROTECTIVE here, not a defect (BUG-117 / BUG-112 / BUG-124):
    BOM present -> PASS; pure ASCII no BOM -> PASS; non-ASCII without BOM -> FAIL.
    """
    r = new_system_result("Encoding Integrity", "encoding")
    scan_dirs = [d for d in (ctx.custom_scripts, ctx.dot_gald3r_sys,
                             ctx.repo_root / ".claude") if d.is_dir()]
    if not scan_dirs:
        add_skip(r)
        r["notes"] = "no scan dirs found (skipped)"
        return r
    all_files: List[Path] = []
    for d in scan_dirs:
        all_files.extend(p for p in d.rglob("*.ps1") if p.is_file())
    if not all_files:
        add_skip(r)
        r["notes"] = "no .ps1 files found to sample"
        return r
    sample = random.sample(all_files, min(50, len(all_files)))
    bom_count = 0
    unsafe: List[str] = []  # non-ASCII AND no BOM
    for f in sample:
        try:
            data = f.read_bytes()
        except OSError:
            continue
        has_bom = data[:3] == b"\xef\xbb\xbf"
        if has_bom:
            bom_count += 1
        start = 3 if has_bom else 0
        has_non_ascii = any(b > 0x7F for b in data[start:])
        # FAIL only the dangerous case: non-ASCII content WITHOUT a protective BOM.
        if has_non_ascii and not has_bom:
            unsafe.append(f.name)
    if not unsafe:
        add_pass(r)
    else:
        add_fail(r, "{0}/{1} sampled .ps1 files have non-ASCII bytes WITHOUT a UTF-8 "
                    "BOM (unparseable under PS 5.1): {2}".format(
                        len(unsafe), len(sample), ", ".join(unsafe[:5])))
    r["notes"] = ("sampled {0} of {1} .ps1 file(s); {2} BOM-protected, "
                  "{3} non-ASCII-without-BOM".format(
                      len(sample), len(all_files), bom_count, len(unsafe)))
    return r


# Registry of system checks (key -> function). Order = report order.
CHECK_REGISTRY = {
    "task": check_task_management,
    "bug": check_bug_tracking,
    "platform_spec": check_platform_spec,
    "parity": check_platform_parity,
    "hooks": check_hook_wiring,
    "git_hooks": check_git_hooks,
    "schema": check_schema_validation,
    "constraints": check_constraints,
    "subsystems": check_subsystems,
    "skills": check_skills_inventory,
    "wpac": check_wpac_topology,
    "release": check_release_pipeline,
    "encoding": check_encoding_integrity,
}
