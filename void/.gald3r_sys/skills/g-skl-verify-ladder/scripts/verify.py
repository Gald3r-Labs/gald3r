#!/usr/bin/env python3
"""Verification ladder for gald3r task completion.

Usage:
    python verify.py <task_id> [--level minimal|standard|thorough|manual]
    python verify.py <task_id> --check-only   # Dry run, no status changes

Reads the task file, determines verification level, runs checks in order,
writes a verification report, and returns structured JSON result.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _find_project_root() -> Path:
    d = Path(__file__).resolve()
    for p in [d, *d.parents]:
        if (p / ".gald3r").is_dir():
            return p
    return Path.cwd()


ROOT = _find_project_root()
GALD3R_DIR = ROOT / ".gald3r"
TASKS_DIR = GALD3R_DIR / "tasks"
LOGS_DIR = GALD3R_DIR / "logs"

LEVEL_ORDER = ["minimal", "standard", "thorough", "manual"]
BLAST_TO_LEVEL = {
    "low": "minimal",
    "medium": "standard",
    "high": "thorough",
}


def parse_task_frontmatter(task_id: int) -> dict:
    patterns = [f"task_{task_id}.md", f"task{task_id}_*.md", f"task_{task_id}_*.md"]
    task_file = None
    for p in TASKS_DIR.glob("*.md"):
        if f"task_{task_id}" in p.stem or f"task{task_id}" in p.stem:
            task_file = p
            break

    if not task_file or not task_file.exists():
        return {"error": f"Task file for {task_id} not found"}

    text = task_file.read_text(encoding="utf-8")
    fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return {"error": "No YAML frontmatter found"}

    fm = {}
    for line in fm_match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
            fm[key] = val

    ac_section = re.search(r"## Acceptance Criteria\s*\n((?:- \[.\].*\n?)+)", text)
    criteria = []
    if ac_section:
        for line in ac_section.group(1).splitlines():
            m = re.match(r"- \[(.)\] (.+)", line)
            if m:
                criteria.append({"checked": m.group(1) != " ", "text": m.group(2).strip()})

    fm["_acceptance_criteria"] = criteria
    fm["_file_path"] = str(task_file)
    fm["_full_text"] = text
    return fm


def determine_level(task: dict, override: str = None) -> str:
    if override:
        return override
    if task.get("verification_level"):
        return task["verification_level"]
    if task.get("requires_verification") is True:
        return "manual"
    blast = task.get("blast_radius", "medium")
    return BLAST_TO_LEVEL.get(blast, "standard")


def run_command(cmd: str, timeout: int = 300) -> dict:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(ROOT)
        )
        return {
            "command": cmd,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "passed": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "exit_code": -1, "stdout": "", "stderr": "Timeout", "passed": False}
    except Exception as e:
        return {"command": cmd, "exit_code": -1, "stdout": "", "stderr": str(e), "passed": False}


def level_1_lint(task: dict) -> dict:
    results = []
    commands = task.get("verification_commands", [])
    if not commands:
        return {"level": 1, "name": "Syntax & Lint", "passed": True, "results": [], "skipped": True}

    lint_cmds = [c for c in commands if any(k in c.lower() for k in ["lint", "compile", "check", "mypy", "ruff"])]
    if not lint_cmds:
        lint_cmds = commands[:1]

    for cmd in lint_cmds:
        results.append(run_command(cmd))

    passed = all(r["passed"] for r in results)
    return {"level": 1, "name": "Syntax & Lint", "passed": passed, "results": results}


def level_2_tests(task: dict) -> dict:
    commands = task.get("verification_commands", [])
    if not commands:
        return {"level": 2, "name": "Tests", "passed": True, "results": [], "skipped": True}

    test_cmds = [c for c in commands if any(k in c.lower() for k in ["test", "pytest", "jest", "mocha"])]
    if not test_cmds:
        test_cmds = commands

    results = [run_command(cmd) for cmd in test_cmds]
    passed = all(r["passed"] for r in results)
    return {"level": 2, "name": "Tests", "passed": passed, "results": results}


def level_3_acceptance(task: dict) -> dict:
    criteria = task.get("_acceptance_criteria", [])
    if not criteria:
        return {"level": 3, "name": "Acceptance Criteria", "passed": True, "results": [], "skipped": True}

    unchecked = [c for c in criteria if not c["checked"]]
    return {
        "level": 3,
        "name": "Acceptance Criteria",
        "passed": len(unchecked) == 0,
        "total": len(criteria),
        "checked": len(criteria) - len(unchecked),
        "unchecked": [c["text"] for c in unchecked],
    }


def level_4_artifacts(task: dict) -> dict:
    artifacts = task.get("verification_artifacts", [])
    if not artifacts:
        return {"level": 4, "name": "Artifact Verification", "passed": True, "results": [], "skipped": True}

    results = []
    for art in artifacts:
        if isinstance(art, str):
            path = art
            check = "exists"
        else:
            path = art.get("path", "")
            check = art.get("check", "exists")

        task_id = task.get("id", "")
        path = path.replace("{id}", str(task_id))
        full_path = ROOT / path

        if check == "exists":
            exists = full_path.exists()
            size = full_path.stat().st_size if exists else 0
            results.append({"path": path, "exists": exists, "size": size, "passed": exists and size > 0})
        else:
            results.append({"path": path, "check": check, "passed": True})

    passed = all(r["passed"] for r in results)
    return {"level": 4, "name": "Artifact Verification", "passed": passed, "results": results}


def level_5_hallucination(task: dict) -> dict:
    diff_result = run_command("git diff --stat HEAD~1..HEAD")
    if diff_result["exit_code"] != 0:
        return {"level": 5, "name": "Hallucination Guard", "passed": True, "skipped": True,
                "reason": "git diff failed (no commits or not a git repo)"}

    files_changed = len([l for l in diff_result["stdout"].splitlines() if "|" in l])
    has_changes = files_changed > 0

    return {
        "level": 5,
        "name": "Hallucination Guard",
        "passed": has_changes,
        "files_changed": files_changed,
        "reason": "No file changes detected" if not has_changes else f"{files_changed} files changed",
    }


def write_report(task_id: int, level: str, results: list, overall: bool, attempts: int):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    report_path = LOGS_DIR / f"task{task_id}_verification.md"

    lines = [
        "---",
        f"task_id: {task_id}",
        f"verification_level: {level}",
        f"started: {now.isoformat()}",
        f"completed: {now.isoformat()}",
        f"result: {'passed' if overall else 'failed'}",
        f"attempts: {attempts}",
        "---",
        "",
        f"# Verification Report: Task {task_id}",
        "",
    ]

    for r in results:
        status = "PASS" if r["passed"] else ("SKIP" if r.get("skipped") else "FAIL")
        lines.append(f"## Level {r['level']}: {r['name']} {status}")

        if r.get("skipped"):
            lines.append(f"- Skipped: {r.get('reason', 'No checks configured')}")
        elif r.get("results"):
            for cmd_r in r["results"]:
                lines.append(f"- Ran: `{cmd_r.get('command', 'N/A')}`")
                lines.append(f"- Exit code: {cmd_r.get('exit_code', 'N/A')}")
                if cmd_r.get("stderr"):
                    lines.append(f"- Error: {cmd_r['stderr'][:500]}")
        elif r.get("unchecked"):
            for item in r["unchecked"]:
                lines.append(f"- [ ] {item}")
        elif r.get("files_changed") is not None:
            lines.append(f"- Files changed: {r['files_changed']}")
            lines.append(f"- Reason: {r.get('reason', '')}")

        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_verification(task_id: int, level_override: str = None, check_only: bool = False):
    task = parse_task_frontmatter(task_id)
    if "error" in task:
        return {"task_id": task_id, "error": task["error"], "passed": False}

    level = determine_level(task, level_override)
    max_level_idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 1
    max_attempts = int(task.get("max_fix_attempts", 3))

    level_funcs = [level_1_lint, level_2_tests, level_3_acceptance, level_4_artifacts, level_5_hallucination]
    level_names = ["minimal", "standard", "standard", "thorough", "thorough"]

    results = []
    overall_passed = True

    for i, (func, req_level) in enumerate(zip(level_funcs, level_names)):
        req_idx = LEVEL_ORDER.index(req_level)
        if req_idx > max_level_idx:
            break

        result = func(task)
        results.append(result)

        if not result["passed"] and not result.get("skipped"):
            overall_passed = False
            break

    report_path = None
    if not check_only:
        report_path = write_report(task_id, level, results, overall_passed, 1)

    return {
        "task_id": task_id,
        "verification_level": level,
        "passed": overall_passed,
        "levels_checked": len(results),
        "results": results,
        "report": report_path,
    }


def main():
    parser = argparse.ArgumentParser(description="gald3r verification ladder")
    parser.add_argument("task_id", type=int, help="Task ID to verify")
    parser.add_argument("--level", choices=LEVEL_ORDER, help="Override verification level")
    parser.add_argument("--check-only", action="store_true", help="Dry run, no report written")

    args = parser.parse_args()
    result = run_verification(args.task_id, args.level, args.check_only)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
