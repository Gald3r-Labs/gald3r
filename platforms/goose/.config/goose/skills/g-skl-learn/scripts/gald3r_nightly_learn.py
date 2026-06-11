#!/usr/bin/env python3
"""Python port of gald3r_nightly_learn.ps1 (T1585).

Nightly session summary extraction into learned-facts.md (T928).

Reads recent session summaries from the vault (or local fallback), identifies
facts not yet captured in learned-facts.md, and outputs an extraction prompt
for the next agent session. Closes the gald3r learning loop:
session ends -> memory_capture_session -> nightly extraction -> learned-facts.md
"""
# @subsystems: MEMORY_AND_KNOWLEDGE
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
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


_COLORS = {"white": "37", "red": "31", "yellow": "33", "cyan": "36",
           "gray": "37", "green": "32"}


def _parse_iso(value: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp, tolerating the PS1 round-trip ('o') format
    with 7 fractional digits. Returns a naive local datetime."""
    v = value.strip()
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        # Trim >6 fractional digits (PS 'o' format writes 7).
        m = re.match(r"^(.+?\.\d{6})\d+(.*)$", v)
        if not m:
            return None
        try:
            dt = datetime.fromisoformat(m.group(1) + m.group(2))
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


def _write_utf8(path: Path, content: str) -> None:
    """Write UTF-8 without BOM (matches the PS1 UTF8Encoding(false))."""
    path.write_text(content, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Nightly session summary extraction into learned-facts.md "
                    "(Python port of gald3r_nightly_learn.ps1, T928).",
        allow_abbrev=False)
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()),
                        help="Root directory of the gald3r-managed project.")
    parser.add_argument("-LookbackDays", "--lookback-days", dest="lookback_days",
                        type=int, default=3,
                        help="How many days of sessions to include (default: 3).")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Agent has performed extraction; write the results "
                             "(requires -ExtractedFacts).")
    parser.add_argument("-ExtractedFacts", "--extracted-facts", dest="extracted_facts",
                        default="", help="Newline-separated bullet points (with -Apply).")
    parser.add_argument("-DryRun", "--dry-run", dest="dry_run", action="store_true",
                        help="Show what would be done without writing anything.")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Output structured JSON.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)

    def log(msg: str, color: str = "white") -> None:
        if not args.json:
            if _color_enabled() and color in _COLORS:
                print(f"\x1b[{_COLORS[color]}m{msg}\x1b[0m")
            else:
                print(msg)

    def out_json(data: Dict[str, Any]) -> None:
        print(json.dumps(data, separators=(",", ":")))

    # -- Load .identity ------------------------------------------------------
    identity_path = project_root / ".gald3r" / ".identity"
    project_name = "unknown"
    vault_location = ""

    if identity_path.exists():
        for line in identity_path.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^project_name=(.+)$", line)
            if m:
                project_name = m.group(1).strip()
            m = re.match(r"^vault_location=(.+)$", line)
            if m:
                vault_location = m.group(1).strip()

    # -- Locate learned-facts.md ----------------------------------------------
    learned_facts_path = project_root / ".gald3r" / "learned-facts.md"
    existing_facts = ""
    if learned_facts_path.exists():
        existing_facts = learned_facts_path.read_text(encoding="utf-8-sig")

    # -- APPLY MODE: write extracted facts ------------------------------------
    if args.apply:
        if not args.extracted_facts:
            log("ERROR: -Apply requires -ExtractedFacts", "red")
            return 1

        lines = [ln for ln in args.extracted_facts.split("\n")
                 if re.match(r"^\s*-\s+", ln)]
        if not lines:
            log("No fact lines found in -ExtractedFacts", "yellow")
            return 0

        new_facts: List[str] = []
        for line in lines:
            fact = line.strip()
            # Simple string dedup: skip if any existing line contains this
            # fact's keywords.
            stripped = re.sub(r"^\s*-\s+\[[\w-]+\]\s*", "", fact)
            keywords = [w for w in re.split(r"\s+", stripped) if len(w) > 4][:3]
            is_dup = False
            for kw in keywords:
                if re.search(re.escape(kw), existing_facts, re.IGNORECASE):
                    is_dup = True
                    break
            if not is_dup:
                new_facts.append(fact)

        if not new_facts:
            log("All extracted facts already present in learned-facts.md — "
                "nothing to add.", "cyan")
            if args.json:
                out_json({"ok": True, "added": 0, "skipped": len(lines)})
            return 0

        if args.dry_run:
            log(f"DRY-RUN: would append {len(new_facts)} fact(s):", "cyan")
            for f in new_facts:
                log(f"  {f}", "gray")
            if args.json:
                out_json({"ok": True, "dryRun": True, "wouldAdd": new_facts})
            return 0

        # Ensure the file has an Architecture section
        if not learned_facts_path.exists():
            scaffold = ("# learned-facts.md\n\n"
                        "## Architecture & Conventions\n\n"
                        "## Recurring Preferences\n\n"
                        "## Watch-Outs & Gotchas\n\n"
                        "## Superseded Facts")
            learned_facts_path.parent.mkdir(parents=True, exist_ok=True)
            _write_utf8(learned_facts_path, scaffold)
            existing_facts = learned_facts_path.read_text(encoding="utf-8-sig")

        append_block = "\n" + "\n".join(new_facts) + "\n"

        if re.search(r"## Architecture & Conventions", existing_facts, re.IGNORECASE):
            # Insert after the Architecture header
            existing_facts = re.sub(
                r"(## Architecture & Conventions\n)",
                lambda m: m.group(1) + append_block,
                existing_facts, flags=re.IGNORECASE)
        else:
            existing_facts += append_block

        _write_utf8(learned_facts_path, existing_facts)
        log(f"Appended {len(new_facts)} new fact(s) to learned-facts.md", "green")
        if args.json:
            out_json({"ok": True, "added": len(new_facts), "facts": new_facts})
        return 0

    # -- GATHER MODE: collect recent session summaries -------------------------
    now = datetime.now()
    cutoff_ts = now.timestamp() - args.lookback_days * 86400
    session_files: List[Path] = []

    # 1. Vault sessions path
    if vault_location and vault_location != "{LOCAL}" and Path(vault_location).exists():
        vault_sessions = Path(vault_location) / "projects" / project_name / "sessions"
        if vault_sessions.exists():
            session_files += [f for f in vault_sessions.glob("*.md")
                              if f.is_file() and f.stat().st_mtime >= cutoff_ts]

    # 2. Local fallback: .gald3r/logs/ or .gald3r/reports/
    local_logs = project_root / ".gald3r" / "logs"
    if local_logs.exists():
        session_files += [f for f in local_logs.glob("*session*")
                          if f.is_file() and f.stat().st_mtime >= cutoff_ts]

    # 3. Check last-extracted timestamp
    last_extracted_path = project_root / ".gald3r" / "logs" / "nightly_learn_last_run.txt"
    last_extracted: Optional[datetime] = None
    if last_extracted_path.exists():
        last_extracted = _parse_iso(
            last_extracted_path.read_text(encoding="utf-8-sig").strip())
        if last_extracted is not None:
            # Only include sessions newer than last extraction
            last_ts = last_extracted.timestamp()
            session_files = [f for f in session_files
                             if f.stat().st_mtime > last_ts]

    if not session_files:
        since_date = last_extracted if last_extracted is not None else \
            datetime.fromtimestamp(cutoff_ts)
        log(f"No new session files found since {since_date} - nothing to extract.",
            "cyan")
        if args.json:
            out_json({"ok": True, "sessionsFound": 0, "action": "none"})
        return 0

    log(f"Found {len(session_files)} session file(s) to process:", "cyan")
    for f in session_files:
        log(f"  {f.name}", "gray")

    # -- Build extraction prompt -----------------------------------------------
    summaries: List[str] = []
    for f in session_files:
        try:
            body = f.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            body = ""
        if body:
            summaries.append(f"### {f.name}\n{body[:2000]}")

    if len(existing_facts) > 3000:
        existing_facts_snippet = existing_facts[:3000] + "\n...(truncated)"
    else:
        existing_facts_snippet = existing_facts

    joined_summaries = "\n\n---\n\n".join(summaries)
    prompt = f"""You are reviewing recent agent session summaries for the gald3r project ("{project_name}").
Your job is to extract durable architectural facts, patterns, and gotchas that should be
preserved in learned-facts.md for the next agent session.

## Existing facts (do NOT repeat these):

{existing_facts_snippet}

## Recent session summaries:

{joined_summaries}

## Instructions:

List any NEW architectural decisions, patterns, conventions, gotchas, or preferences
that are NOT already captured above. Format each as a single bullet:

  - [YYYY-MM-DD] {{fact}} (context: {{brief context}})

Focus on:
- Architecture decisions and rationale
- File locations and naming patterns
- Gotchas and workarounds discovered
- User/project preferences observed

Emit ONLY the bullet list. If nothing new, emit: (none)"""

    # Write extraction prompt to a temp file for the agent to use
    prompt_path = project_root / ".gald3r" / "logs" / "nightly_learn_pending.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    _write_utf8(prompt_path, prompt)

    # Update last-run timestamp
    _write_utf8(last_extracted_path, datetime.now().astimezone().isoformat())

    log("")
    log(f"Extraction prompt written to: {prompt_path}", "green")
    log("")
    log("To complete the learning loop, run in your next agent session:", "yellow")
    log("  @g-learn extract", "yellow")
    log("")
    log("Or run the agent directly with the prompt content.", "gray")

    if args.json:
        out_json({
            "ok": True,
            "sessionsFound": len(session_files),
            "promptPath": str(prompt_path),
            "action": "prompt-ready",
            "nextStep": "@g-learn extract",
        })
    return 0


if __name__ == "__main__":
    sys.exit(main())
