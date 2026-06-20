#!/usr/bin/env python3
"""Python port of generate_copilot_instructions.ps1 (T1585).

Generates .github/copilot-instructions.md from gald3r always-apply rules.
Idempotent — safe to rerun; output is deterministic given the same input
files. Also generates .github/agents/ (from .claude/agents/),
.github/hooks/gald3r-hooks.json, and .github/prompts/ (from
.cursor/commands/, renamed *.md -> *.prompt.md).
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional


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

_HOOKS_CONTENT = """{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-session-start.sh",
        "powershell": ".claude/hooks/g-hk-session-start.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ],
    "agentStop": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-agent-complete.sh",
        "powershell": ".claude/hooks/g-hk-agent-complete.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ],
    "preToolUse": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-validate-shell.sh",
        "powershell": ".claude/hooks/g-hk-validate-shell.ps1",
        "cwd": ".",
        "timeoutSec": 15
      }
    ],
    "sessionEnd": [
      {
        "type": "command",
        "bash": ".claude/hooks/g-hk-agent-complete.sh",
        "powershell": ".claude/hooks/g-hk-agent-complete.ps1",
        "cwd": ".",
        "timeoutSec": 30
      }
    ]
  }
}"""


def _write_utf8(path: Path, content: str) -> None:
    """Write UTF-8 without BOM (matches the PS1 UTF8Encoding(false))."""
    path.write_text(content, encoding="utf-8")


def _report_io_error(exc: OSError) -> None:
    """Per-destination failures are non-fatal — the PS1 prints the error and
    continues (e.g. the literal '<template_full>' placeholder is an invalid
    Windows dirname when no ecosystem template folder exists)."""
    print(f"ERROR: {exc}", file=sys.stderr)


def find_project_root(explicit: str) -> Path:
    """Locate project root (walk up from script location looking for AGENTS.md)."""
    if explicit:
        return Path(explicit)
    d: Optional[Path] = Path(__file__).resolve().parent
    while d is not None and not (d / "AGENTS.md").exists():
        parent = d.parent
        d = None if parent == d else parent
    return d if d is not None else Path(__file__).resolve().parent


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Generate .github/copilot-instructions.md (and agents/hooks/"
                    "prompts) from gald3r always-apply rules (Python port of "
                    "generate_copilot_instructions.ps1).",
        allow_abbrev=False)
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default="", help="Project root (default: walk up from the "
                                         "script looking for AGENTS.md).")
    parser.add_argument("-DryRun", "--dry-run", dest="dry_run", action="store_true",
                        help="Show what would be written without writing.")
    parser.add_argument("-Verbose", "--verbose", dest="verbose", action="store_true",
                        help="Verbose progress output.")
    args = parser.parse_args(argv)

    def verbose(msg: str) -> None:
        if args.verbose:
            print(f"VERBOSE: {msg}", file=sys.stderr)

    project_root = find_project_root(args.project_root)
    verbose(f"Project root: {project_root}")
    ecosystem_root = project_root.parent
    template_full_root = ecosystem_root / "<template_full>"

    # Source: all g-rl-*.mdc files in .cursor/rules/, sorted numerically
    rules_dir = project_root / ".cursor" / "rules"
    rule_files = sorted(rules_dir.glob("g-rl-*.mdc")) if rules_dir.is_dir() else []

    if not rule_files:
        print(f"WARNING: No g-rl-*.mdc files found in {rules_dir}", file=sys.stderr)
        return 1

    verbose(f"Found {len(rule_files)} rule files")

    # Header banner
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    banner = f"""<!--
  .github/copilot-instructions.md — AUTO-GENERATED, DO NOT EDIT MANUALLY

  Generated from: .cursor/rules/g-rl-*.mdc
  Generator:      .claude/skills/g-skl-platform-copilot/scripts/generate_copilot_instructions.py
  Generated at:   {timestamp}

  This file carries gald3r always-apply rules into GitHub Copilot sessions.
  Regenerate after modifying rules: python scripts/generate_copilot_instructions.py

  gald3r — AI Development System for Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot
  Supported IDEs: Cursor (.cursor/), Claude Code (.claude/), Gemini (.agent/),
                  Codex (.codex/), OpenCode (.opencode/), GitHub Copilot (.copilot/)
-->

# gald3r System Instructions for GitHub Copilot

The following rules apply to every Copilot session in this repository.
They are automatically concatenated from gald3r's always-apply rule files.

---

"""

    # Build content blocks — strip Cursor-specific frontmatter from each file
    blocks: List[str] = []
    for file in rule_files:
        verbose(f"Processing: {file.name}")
        raw = file.read_text(encoding="utf-8-sig")

        # Strip YAML frontmatter block (--- ... ---)
        content = re.sub(r"(?s)^---\r?\n.*?\r?\n---\r?\n", "", raw, count=1)

        # Remove alwaysApply: lines (Cursor-specific config)
        content = re.sub(r"(?m)^alwaysApply:.*$\r?\n", "", content)

        # Remove empty leading/trailing lines from each block
        content = content.strip()

        if content:
            blocks.append(f"<!-- Rule: {file.name} -->\n{content}\n")

    # Assemble output
    output = banner + "\n---\n\n".join(blocks) + "\n"

    # Destination paths
    destinations = [
        project_root / ".github" / "copilot-instructions.md",
        template_full_root / ".github" / "copilot-instructions.md",
    ]

    for dest in destinations:
        dest_dir = dest.parent
        if not dest_dir.exists():
            if args.dry_run:
                print(f"[DRY-RUN] Would create: {dest_dir}")
            else:
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _report_io_error(exc)

        if args.dry_run:
            print(f"[DRY-RUN] Would write {len(output)} chars to: {dest}")
        else:
            try:
                _write_utf8(dest, output)
                print(f"Written: {dest} ({len(output)} chars)")
            except OSError as exc:
                _report_io_error(exc)

    if not args.dry_run:
        print("")
        print("copilot-instructions.md generated successfully.")
        print(f"Rule files processed: {len(rule_files)}")
        print(f"Rule files: {', '.join(f.name for f in rule_files)}")

    # -----------------------------------------------------------------------
    # Step 2: Generate .github/agents/ from .claude/agents/g-agnt-*.md
    # -----------------------------------------------------------------------
    print("")
    print("--- Generating .github/agents/ ---")

    agent_src = project_root / ".claude" / "agents"
    agent_targets = [
        project_root / ".github" / "agents",
        template_full_root / ".github" / "agents",
    ]

    for agent_dst in agent_targets:
        if not agent_dst.exists():
            if args.dry_run:
                print(f"[DRY-RUN] Would create: {agent_dst}")
            else:
                try:
                    agent_dst.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _report_io_error(exc)
        agent_files = (sorted(f for f in agent_src.glob("g-agnt-*.md") if f.is_file())
                       if agent_src.is_dir() else [])
        for f in agent_files:
            if args.dry_run:
                print(f"[DRY-RUN] Would copy {f.name} -> {agent_dst}")
            else:
                try:
                    shutil.copy2(str(f), str(agent_dst / f.name))
                except OSError as exc:
                    _report_io_error(exc)
        if not args.dry_run:
            print(f"Agents: {len(agent_files)} files -> {agent_dst}")

    # -----------------------------------------------------------------------
    # Step 3: Generate .github/hooks/gald3r-hooks.json
    # -----------------------------------------------------------------------
    print("")
    print("--- Generating .github/hooks/ ---")

    hooks_targets = [
        project_root / ".github" / "hooks" / "gald3r-hooks.json",
        template_full_root / ".github" / "hooks" / "gald3r-hooks.json",
    ]

    for h_dst in hooks_targets:
        h_dir = h_dst.parent
        if not h_dir.exists():
            if args.dry_run:
                print(f"[DRY-RUN] Would create: {h_dir}")
            else:
                try:
                    h_dir.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _report_io_error(exc)
        if args.dry_run:
            print(f"[DRY-RUN] Would write gald3r-hooks.json -> {h_dst}")
        else:
            try:
                _write_utf8(h_dst, _HOOKS_CONTENT)
                print(f"Hooks written: {h_dst}")
            except OSError as exc:
                _report_io_error(exc)

    # -----------------------------------------------------------------------
    # Step 4: Generate .github/prompts/ from .cursor/commands/ (*.md -> *.prompt.md)
    # -----------------------------------------------------------------------
    print("")
    print("--- Generating .github/prompts/ ---")

    prompt_target_pairs = [
        (project_root / ".cursor" / "commands", project_root / ".github" / "prompts"),
        (template_full_root / ".cursor" / "commands",
         template_full_root / ".github" / "prompts"),
    ]

    for src, dst in prompt_target_pairs:
        if not dst.exists():
            if args.dry_run:
                print(f"[DRY-RUN] Would create: {dst}")
            else:
                try:
                    dst.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _report_io_error(exc)
        cmd_files = (sorted(f for f in src.glob("*.md") if f.is_file())
                     if src.is_dir() else [])
        for f in cmd_files:
            prompt_name = f"{f.stem}.prompt.md"
            if args.dry_run:
                print(f"[DRY-RUN] Would copy {f.name} -> {prompt_name}")
            else:
                try:
                    shutil.copy2(str(f), str(dst / prompt_name))
                except OSError as exc:
                    _report_io_error(exc)
        if not args.dry_run:
            print(f"Prompts: {len(cmd_files)} files -> {dst}")

    print("")
    print("All Copilot .github/ targets generated.")
    print("  copilot-instructions.md : rules source")
    print("  .github/agents/         : agent definitions (from .claude/agents/)")
    print("  .github/hooks/          : lifecycle hooks (gald3r-hooks.json)")
    print("  .github/prompts/        : prompt templates (from .cursor/commands/)")
    print("  Skills                  : auto-discovered from .claude/skills/ (no copy needed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
