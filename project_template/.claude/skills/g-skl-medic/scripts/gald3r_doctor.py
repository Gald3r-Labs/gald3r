#!/usr/bin/env python3
"""Python port of gald3r_doctor.ps1 (T1585).

Environment health check for gald3r projects. Validates: identity/config,
task state, MCP/Docker, vault, platform parity. Safe to run multiple times
(read-only by default; -Fix scope is narrow).

Fix scope (NARROW by design - the OpenClaw 5.5 lesson):
  - Creates missing .gald3r/ subdirectories
  - Writes a minimal .gald3r/.identity stub when the file is missing
  - Does NOT touch routing, credentials, connection types, or TASKS.md

Exit codes: 0 = no FAIL results; 1 = at least one FAIL; 2 = no .gald3r/ found.

Usage:
  python gald3r_doctor.py                     # full health report
  python gald3r_doctor.py -Fix                # apply safe auto-fixes
  python gald3r_doctor.py -Category identity  # run one category only
  python gald3r_doctor.py -Quiet              # pass/fail counts only
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def run_cmd(args: List[str]) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr) without raising.

    Returns rc=127 when the executable is missing entirely.
    """
    exe = shutil.which(args[0])
    if exe is None:
        return 127, "", f"{args[0]} not found in PATH"
    if _process is not None:
        try:
            r = _process.run_cmd([exe, *args[1:]], check=False)
            return r.returncode, r.stdout, r.stderr
        except (OSError, ValueError):
            return 127, "", f"failed to run: {args[0]}"
    try:
        proc = subprocess.run(
            [exe, *args[1:]], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (FileNotFoundError, OSError):
        return 127, "", f"failed to run: {args[0]}"


class Doctor:
    def __init__(self, project_root: Path, fix: bool) -> None:
        self.project_root = project_root
        self.gald3r_dir = project_root / ".gald3r"
        self.fix = fix
        self.results: List[Dict[str, str]] = []

    def add_result(self, status: str, check: str, detail: str,
                   fix_hint: str = "") -> None:
        self.results.append({"Status": status, "Check": check,
                             "Detail": detail, "FixHint": fix_hint})

    def passed(self, check: str, detail: str) -> None:
        self.add_result("PASS", check, detail)

    def warn(self, check: str, detail: str, fix_hint: str = "") -> None:
        self.add_result("WARN", check, detail, fix_hint)

    def fail(self, check: str, detail: str, fix_hint: str = "") -> None:
        self.add_result("FAIL", check, detail, fix_hint)

    # ------------------------------------------------------------------
    # Category 1: Identity & Config
    # ------------------------------------------------------------------
    def test_identity(self) -> None:
        identity_path = self.gald3r_dir / ".identity"

        if not identity_path.exists():
            if self.fix:
                new_id = str(uuid.uuid4())
                stub = (f"project_id=stub-{new_id}\n"
                        "gald3r_version=unknown\n"
                        "vault_location={LOCAL}\n")
                identity_path.write_text(stub, encoding="utf-8")
                self.passed("identity/.identity exists",
                            "Created stub .identity via -Fix")
            else:
                self.fail("identity/.identity exists",
                          ".gald3r/.identity not found",
                          "Run @g-doctor -Fix to create a stub, then fill in "
                          "project_id and vault_location")
            return

        raw = identity_path.read_text(encoding="utf-8-sig", errors="replace")
        required_fields = ["project_id", "gald3r_version", "vault_location"]
        missing = [f for f in required_fields
                   if not re.search(rf"(?m)^{f}=.+", raw)]
        if missing:
            self.fail("identity/.identity fields",
                      "Missing required fields: " + ", ".join(missing),
                      "Edit .gald3r/.identity and add the missing fields")
        else:
            self.passed("identity/.identity fields",
                        "project_id, gald3r_version, vault_location all present")

        # Core file presence
        required = ["TASKS.md", "PLAN.md", "PROJECT.md", "CONSTRAINTS.md",
                    "BUGS.md", "SUBSYSTEMS.md"]
        missing_files = [f for f in required
                         if not (self.gald3r_dir / f).exists()]
        if missing_files:
            self.warn("identity/.gald3r structure",
                      "Missing core files: " + ", ".join(missing_files),
                      "Run @g-setup to initialize missing files")
        else:
            self.passed("identity/.gald3r structure",
                        "All core .gald3r/ files present")

        # Subdirectories
        for sub in ("tasks", "bugs", "subsystems"):
            sub_path = self.gald3r_dir / sub
            if not sub_path.exists():
                if self.fix:
                    sub_path.mkdir(parents=True, exist_ok=True)
                    self.passed(f"identity/{sub}/",
                                f"Created missing {sub}/ via -Fix")
                else:
                    self.warn(f"identity/{sub}/",
                              f".gald3r/{sub}/ directory missing",
                              f"Run @g-doctor -Fix or mkdir .gald3r/{sub}")
            else:
                self.passed(f"identity/{sub}/", f".gald3r/{sub}/ exists")

    # ------------------------------------------------------------------
    # Category 2: Task State
    # ------------------------------------------------------------------
    def test_tasks(self) -> None:
        tasks_md = self.gald3r_dir / "TASKS.md"
        tasks_dir = self.gald3r_dir / "tasks"

        if not tasks_md.is_file():
            self.warn("tasks/TASKS.md",
                      "TASKS.md not found - skipping task sync check",
                      "Run @g-setup")
            return

        tasks_content = tasks_md.read_text(encoding="utf-8-sig",
                                           errors="replace")
        md_ids = set()
        # Table row format
        for m in re.finditer(r"\|\s*\[[^\]]+\]\s*\|\s*\[(\d+)\]", tasks_content):
            md_ids.add(str(int(m.group(1))))
        # Bullet row format
        for m in re.finditer(r"-\s*\[[^\]]+\]\s*\*{0,2}[Tt](?:ask)?\s*(\d+)",
                             tasks_content):
            md_ids.add(str(int(m.group(1))))

        if not tasks_dir.is_dir():
            self.warn("tasks/sync",
                      "tasks/ directory missing - cannot verify sync",
                      "Run @g-doctor -Fix")
            return

        file_ids = set()
        for f in tasks_dir.glob("task*.md"):
            m = re.search(r"task(\d+)", f.name)
            if m:
                file_ids.add(str(int(m.group(1))))

        phantoms = sorted([i for i in md_ids if i not in file_ids], key=int)
        orphans = sorted([i for i in file_ids if i not in md_ids], key=int)

        if phantoms:
            self.warn("tasks/phantom",
                      f"{len(phantoms)} phantom task(s) in TASKS.md with no "
                      "task file: " + ", ".join(phantoms),
                      "Create missing task files or remove stale TASKS.md rows")
        else:
            self.passed("tasks/phantom", "No phantom tasks detected")

        if orphans:
            self.warn("tasks/orphan",
                      f"{len(orphans)} orphan task file(s) not in TASKS.md: "
                      + ", ".join(orphans),
                      "Add missing rows to TASKS.md or archive stale files via "
                      "@g-task-archive")
        else:
            self.passed("tasks/orphan", "No orphan task files detected")

        self.passed("tasks/TASKS.md",
                    f"TASKS.md present ({len(md_ids)} task IDs parsed)")

    # ------------------------------------------------------------------
    # Category 3: MCP / Docker
    # ------------------------------------------------------------------
    def test_mcp(self) -> None:
        # Docker engine
        docker_ok = False
        rc, _, _ = run_cmd(["docker", "info"])
        if rc == 127:
            self.warn("mcp/docker-engine",
                      "docker CLI not found or not in PATH",
                      "Install Docker Desktop: https://docs.docker.com/desktop/")
        elif rc == 0:
            docker_ok = True
            self.passed("mcp/docker-engine", "Docker engine is running")
        else:
            self.fail("mcp/docker-engine",
                      "Docker info returned non-zero exit code",
                      "Start Docker Desktop or the Docker daemon")

        # gald3r container
        if docker_ok:
            rc, out, _ = run_cmd(["docker", "ps", "--filter", "name=gald3r",
                                  "--format", "{{.Names}}"])
            if rc == 0:
                names = [n for n in out.splitlines() if n.strip()]
                if any("gald3r" in n for n in names):
                    self.passed("mcp/container",
                                "gald3r container running: " + ", ".join(names))
                else:
                    self.warn("mcp/container",
                              "No running gald3r container found",
                              "Run: cd docker && docker compose up -d")
            else:
                self.warn("mcp/container", "Could not query Docker containers",
                          "Verify Docker is accessible")

        # HTTP health check
        mcp_url = "http://localhost:8092/health"
        try:
            with urllib.request.urlopen(mcp_url, timeout=5) as response:
                status = getattr(response, "status", response.getcode())
                if status == 200:
                    self.passed("mcp/health-endpoint",
                                f"MCP server responded OK at {mcp_url}")
                else:
                    self.warn("mcp/health-endpoint",
                              f"MCP server returned HTTP {status}",
                              "Check: docker logs gald3r_docker")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            self.warn("mcp/health-endpoint",
                      f"MCP server not reachable at {mcp_url} ({exc})",
                      "Run: cd docker && docker compose up -d")

        # Tool availability
        for tool in ("node", "python", "uv"):
            rc, out, _ = run_cmd([tool, "--version"])
            if rc == 127:
                self.warn(f"mcp/tool-{tool}", f"{tool} not found in PATH",
                          f"Install {tool}: see project README")
            elif rc == 0:
                first = out.splitlines()[0] if out.splitlines() else ""
                self.passed(f"mcp/tool-{tool}",
                            f"{tool} available: {first}")
            else:
                self.warn(f"mcp/tool-{tool}",
                          f"{tool} returned non-zero on --version",
                          f"Install or repair {tool}")

    # ------------------------------------------------------------------
    # Category 4: Vault
    # ------------------------------------------------------------------
    def test_vault(self) -> None:
        identity_path = self.gald3r_dir / ".identity"
        if not identity_path.is_file():
            self.warn("vault/location",
                      ".identity missing - cannot determine vault path",
                      "Run identity checks first")
            return

        raw = identity_path.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"(?m)^vault_location=(.+)", raw)
        if not m:
            self.warn("vault/location", "vault_location not set in .identity",
                      "Add vault_location= to .gald3r/.identity")
            return
        vault_location = m.group(1).strip()

        if vault_location == "{LOCAL}":
            self.passed("vault/location",
                        "vault_location={LOCAL} (local vault mode - no remote "
                        "connectivity check)")
            local_vault = self.project_root / "vault"
            if local_vault.exists():
                if (local_vault / "_index.yaml").exists():
                    self.passed("vault/index", "vault/_index.yaml present")
                else:
                    self.warn("vault/index", "vault/_index.yaml missing",
                              "Run @g-vault-lint to regenerate the index")
            else:
                self.warn("vault/local-dir",
                          f"vault/ directory not found at: {local_vault}",
                          "Create the vault/ folder or set vault_location to a "
                          "valid path")
            return

        # Non-local vault
        if Path(vault_location).exists():
            self.passed("vault/directory",
                        f"Vault directory accessible: {vault_location}")
            if (Path(vault_location) / "_index.yaml").exists():
                self.passed("vault/index", "_index.yaml present in vault")
            else:
                self.warn("vault/index",
                          f"_index.yaml missing from vault at: {vault_location}",
                          "Run @g-vault-lint to regenerate")
        else:
            self.fail("vault/directory",
                      f"Vault directory not found: {vault_location}",
                      "Update vault_location in .gald3r/.identity or create "
                      "the directory")

        # AC7: Remote connectivity check
        if re.match(r"^https?://", vault_location):
            try:
                with urllib.request.urlopen(vault_location, timeout=8) as r:
                    status = getattr(r, "status", r.getcode())
                    self.passed("vault/remote-api",
                                f"Remote vault API reachable (HTTP {status})")
            except (urllib.error.URLError, OSError, ValueError) as exc:
                self.fail("vault/remote-api",
                          f"Remote vault API unreachable: {exc}",
                          "Check network connectivity and vault_location URL")

    # ------------------------------------------------------------------
    # Category 5: Platform IDE Parity
    # ------------------------------------------------------------------
    def test_platform(self) -> None:
        platforms = [
            (".cursor", ".cursor/"),
            (".claude", ".claude/"),
            (".agent", ".agent/"),
            (".codex", ".codex/"),
            (".opencode", ".opencode/"),
        ]

        for key, label in platforms:
            path = self.project_root / key
            if path.exists():
                self.passed(f"platform/{key}", f"{label} directory present")
            else:
                self.warn(f"platform/{key}", f"{label} not found",
                          "Run @g-setup or platform_parity_sync.ps1 -Sync to "
                          "restore")

        # Primary surfaces: commands/ and skills/
        for primary in (".cursor", ".claude"):
            cmd_path = self.project_root / primary / "commands"
            skill_path = self.project_root / primary / "skills"
            if cmd_path.is_dir():
                cmd_count = len(list(cmd_path.glob("*.md")))
                self.passed(f"platform/{primary}/commands",
                            f"{primary}/commands/ present ({cmd_count} files)")
            else:
                self.warn(f"platform/{primary}/commands",
                          f"{primary}/commands/ missing", "Run @g-setup")
            if skill_path.exists():
                self.passed(f"platform/{primary}/skills",
                            f"{primary}/skills/ present")
            else:
                self.warn(f"platform/{primary}/skills",
                          f"{primary}/skills/ missing", "Run @g-setup")

        # Copilot (Phase 1)
        if (self.project_root / ".copilot").exists():
            self.passed("platform/.copilot",
                        ".copilot/ directory present (Phase 1 compatible)")
        else:
            self.warn("platform/.copilot",
                      ".copilot/ not found - GitHub Copilot support not "
                      "installed",
                      "Run platform_parity_sync.ps1 -Sync")


def find_project_root(start: Optional[str]) -> Optional[Path]:
    if start:
        p = Path(start)
        return p if (p / ".gald3r").exists() else None
    d = Path.cwd()
    while True:
        if (d / ".gald3r").exists():
            return d
        if d.parent == d:
            return None
        d = d.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Environment health check for gald3r projects "
                    "(identity/config, task state, MCP/Docker, vault, "
                    "platform parity).")
    parser.add_argument("-Fix", "--fix", dest="fix", action="store_true",
                        help="Apply safe auto-fixes (narrow scope).")
    parser.add_argument("-Category", "--category", dest="category",
                        default="all",
                        choices=["identity", "tasks", "mcp", "vault",
                                 "platform", "all"],
                        help="Run one category only (default: all).")
    parser.add_argument("-Quiet", "--quiet", dest="quiet", action="store_true",
                        help="Pass/fail counts only.")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default="", help="Project root (default: walk up from cwd).")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    project_root = find_project_root(args.project_root or None)
    if project_root is None:
        print("FATAL: Cannot locate .gald3r/ folder. Run from inside a gald3r "
              "project.")
        return 2

    doctor = Doctor(project_root, fix=args.fix)

    if args.category == "all":
        categories = ["identity", "tasks", "mcp", "vault", "platform"]
    else:
        categories = [args.category]

    for cat in categories:
        if cat == "identity":
            doctor.test_identity()
        elif cat == "tasks":
            doctor.test_tasks()
        elif cat == "mcp":
            doctor.test_mcp()
        elif cat == "vault":
            doctor.test_vault()
        elif cat == "platform":
            doctor.test_platform()

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    pass_count = sum(1 for r in doctor.results if r["Status"] == "PASS")
    warn_count = sum(1 for r in doctor.results if r["Status"] == "WARN")
    fail_count = sum(1 for r in doctor.results if r["Status"] == "FAIL")

    if not args.quiet:
        print()
        print("gald3r doctor -- Environment Health Report")
        print("=" * 50)
        print()
        for r in doctor.results:
            print(f"[{r['Status']}]  {r['Check']}")
            print(f"        {r['Detail']}")
            if r["Status"] in ("WARN", "FAIL") and r["FixHint"]:
                print(f"        Fix: {r['FixHint']}")
        print()
        print("=" * 50)
        print(f"Summary: [PASS] {pass_count}  [WARN] {warn_count}  "
              f"[FAIL] {fail_count}")
        if args.fix:
            print()
            print("NOTE: -Fix applied. Routing, credentials, and connection "
                  "settings were NOT changed.")
        print()
    else:
        print(f"Summary: [PASS] {pass_count}  [WARN] {warn_count}  "
              f"[FAIL] {fail_count}")

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
