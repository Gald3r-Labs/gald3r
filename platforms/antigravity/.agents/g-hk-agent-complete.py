#!/usr/bin/env python3
"""Python port of g-hk-agent-complete.ps1 (T1584).

Agent/stop lifecycle hook (fires on the "stop" event). Reads the stop-event
payload from stdin ({"status": ..., "loop_count": N, "conversation_id": ...,
"transcript_path": ...}), writes diagnostic entries to
.gald3r/logs/hook_diag.log, discovers a transcript via the T1232 fallback
(most recent non-subagent .jsonl under ~/.cursor/projects/<slug>/
agent-transcripts) when the payload omits it, launches the sibling chat
logger script with a 30-second timeout, writes a pending-reflection hint
(.gald3r/logs/pending_reflection.json) for the next session-start hook, and
optionally stages a skill-capture stub (T1174) when AGENT_CONFIG.md has
skill_capture_hook: true. Emits "{}" and always exits 0.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _diag(project_root, msg):
    """Append a timestamped line to .gald3r/logs/hook_diag.log (fail-soft)."""
    try:
        logs_dir = project_root / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "hook_diag.log", "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (_now(), msg))
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="gald3r agent-complete hook (Python port of "
                    "g-hk-agent-complete.ps1)")
    parser.parse_known_args()

    project_root = Path.cwd()
    event_data = _hook_common.read_stdin_json()

    # ── Diagnostic log (fires unconditionally — proves hook ran) ─────────────
    _diag(project_root,
          "agent-complete hook fired, cwd=%s" % project_root)

    status = event_data.get("status") or "unknown"
    # Official Cursor schema uses snake_case: loop_count, conversation_id,
    # transcript_path
    loop_count = event_data.get("loop_count")
    if loop_count is None:
        loop_count = 0
    conversation_id = event_data.get("conversation_id") or "unknown"
    transcript_path = event_data.get("transcript_path") or None
    # Fallback: Cursor also exposes transcript path as env var
    if not transcript_path and os.environ.get("CURSOR_TRANSCRIPT_PATH"):
        transcript_path = os.environ["CURSOR_TRANSCRIPT_PATH"]

    # ── T1232: Fallback transcript discovery via agent-transcripts/ ─────────
    # Cursor stopped sending conversation_id/transcript_path in the stop event
    # payload around April 2026. When those are missing, scan the
    # agent-transcripts folder directly and use the most recently modified
    # non-subagent JSONL file.
    if not transcript_path or not Path(str(transcript_path)).exists():
        try:
            raw_slug = str(project_root).replace(":", "")
            raw_slug = re.sub(r"[^A-Za-z0-9]", "-", raw_slug).lower().strip("-")
            user_profile = os.environ.get("USERPROFILE") or str(Path.home())
            transcript_root = (Path(user_profile) / ".cursor" / "projects"
                               / raw_slug / "agent-transcripts")
            if transcript_root.is_dir():
                jsonls = [
                    p for p in transcript_root.rglob("*.jsonl")
                    if not re.search(r"[\\/]subagents[\\/]", str(p))
                    and not re.search(r"subagent", p.name)
                ]
                jsonls.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                if jsonls:
                    latest = jsonls[0]
                    transcript_path = str(latest)
                    if conversation_id == "unknown":
                        conversation_id = latest.stem
                    _diag(project_root,
                          "T1232 fallback transcript: %s" % latest.name)
            # else: fall through — keep transcript_path null
        except Exception as exc:  # parity: any discovery error is logged
            _diag(project_root,
                  "T1232 transcript discovery error: %s" % exc)

    # Log resolved values to diagnostic (second entry with context)
    _diag(project_root,
          "event: status=%s loops=%s convId=%s"
          % (status, loop_count, conversation_id))

    # ── Chat transcript logger (synchronous, 30s timeout) ───────────────────
    try:
        # BUG-133 fix: probe for whichever chat logger actually ships in
        # this hook directory. g-hk-cursor-chat-logger.py does not ship in
        # every deployment (the .claude install ships g-hk-claude-chat-
        # logger.py); the previous hardcoded name was a silent no-op there.
        logger_script = None
        for _logger_name in ("g-hk-cursor-chat-logger.py",
                             "g-hk-claude-chat-logger.py"):
            _candidate = SCRIPT_DIR / _logger_name
            if _candidate.is_file():
                logger_script = _candidate
                break
        if logger_script is None:
            _diag(project_root,
                  "logger skipped: no chat logger ships in this deployment")
        if logger_script is not None:
            # The PS1 probes for py/python/python3; here the running
            # interpreter is the natural equivalent.
            logger_args = [
                sys.executable, str(logger_script),
                "--project-path", str(project_root),
                "--loop-count", str(loop_count),
                "--status", "completed" if status == "completed" else str(status),
                "--platform", "cursor",
            ]
            if conversation_id and conversation_id != "unknown":
                logger_args += ["--conversation-id", str(conversation_id)]
            if transcript_path:
                logger_args += ["--transcript-path", str(transcript_path)]

            try:
                res = subprocess.run(logger_args, capture_output=True,
                                     text=True, timeout=30)
                if res.returncode != 0:
                    out = (res.stdout or "") + (res.stderr or "")
                    _diag(project_root,
                          "logger FAILED exit=%d : %s"
                          % (res.returncode, out.strip()))
                else:
                    _diag(project_root, "logger OK: chat log written")
            except subprocess.TimeoutExpired:
                _diag(project_root, "logger launch error: timeout after 30s")
    except Exception as exc:
        _diag(project_root, "logger launch error: %s" % exc)

    # ── Reflection hint for next session-start ──────────────────────────────
    # Always write a reflection hint so the next session-start hook can prompt
    # a brief review of what was accomplished. Includes written_at so the
    # session-start hook can ignore stale files (e.g. > 48 hours old).
    try:
        logs_dir = project_root / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        # Parity with [int]$loopCount: a non-castable value aborts the block
        # (outer except), so the reflection file is not written.
        loop_count_int = int(float(loop_count))
        reflection_data = {
            "conversation_id": conversation_id,
            "loop_count": loop_count_int,
            "status": status,
            "written_at": _now(),
        }
        (logs_dir / "pending_reflection.json").write_text(
            json.dumps(reflection_data, separators=(",", ":")),
            encoding="utf-8",
        )
    except Exception:
        pass

    # ── T1174: Skill-Capture Stub (opt-in) ───────────────────────────────────
    # When AGENT_CONFIG.md has `skill_capture_hook: true`, stage a stub file in
    # .gald3r/reports/skill_candidates/ inviting the next agent session to
    # capture any reusable patterns discovered during this task as a SKILL.md
    # candidate. The hook is fire-and-stage only. Default: disabled.
    try:
        agent_config_path = project_root / ".gald3r" / "config" / "AGENT_CONFIG.md"
        skill_capture_enabled = False
        if agent_config_path.is_file():
            try:
                config_content = agent_config_path.read_text(
                    encoding="utf-8", errors="replace")
            except OSError:
                config_content = ""
            if config_content and re.search(
                    r"(?m)^\s*skill_capture_hook\s*:\s*true\b", config_content):
                skill_capture_enabled = True

        if skill_capture_enabled and status == "completed":
            candidates_dir = project_root / ".gald3r" / "reports" / "skill_candidates"
            candidates_dir.mkdir(parents=True, exist_ok=True)

            now = datetime.now()
            stamp_date = now.strftime("%Y%m%d")
            stamp_time = now.strftime("%H%M%S")
            # Short, filesystem-safe conv id slice (or fallback to time stamp)
            if conversation_id and conversation_id != "unknown":
                clean = re.sub(r"[^A-Za-z0-9]", "", str(conversation_id))
                conv_short = clean[: min(8, len(clean))]
            else:
                conv_short = stamp_time
            if not conv_short:
                conv_short = stamp_time
            stub_name = "%s_%s_session%s.md" % (stamp_date, stamp_time, conv_short)
            stub_path = candidates_dir / stub_name

            if not stub_path.exists():
                stub_body = (
                    "---\n"
                    "status: pending\n"
                    "captured_at: %s\n"
                    "session_id: %s\n"
                    "loop_count: %s\n"
                    "session_status: %s\n"
                    "task_id: \"\"        # fill in if this session worked on "
                    "a specific task (e.g., 1174)\n"
                    "---\n"
                    "\n"
                    "# SKILL Candidate Stub (pending agent input)\n"
                    "\n"
                    "Did this session reveal a reusable pattern? If yes, "
                    "describe it in 3-5 lines\n"
                    "matching the SKILL.md structure below. If no, set "
                    "`status: discarded` in the\n"
                    "frontmatter above and leave the body empty.\n"
                    "\n"
                    "## name\n"
                    "<short kebab-case skill name, e.g., parallel-status-sweep>\n"
                    "\n"
                    "## when_to_use\n"
                    "<one sentence — the trigger condition or user phrasing "
                    "that activates it>\n"
                    "\n"
                    "## how_it_works\n"
                    "<3-5 lines describing the procedure / steps / tool "
                    "sequence>\n"
                    "\n"
                    "## example\n"
                    "<minimal concrete example, code block, or invocation>\n"
                    "\n"
                    "---\n"
                    "\n"
                    "**Filled by**: agent / human\n"
                    "**Next step**: `@g-idea-farm` scans this folder and "
                    "promotes filled stubs to `IDEA_BOARD.md`.\n"
                    % (_now(), conversation_id, loop_count, status)
                )
                stub_path.write_text(stub_body, encoding="utf-8")
                _diag(project_root,
                      "skill_capture stub written: %s" % stub_path)
    except Exception as exc:
        _diag(project_root, "skill_capture error: %s" % exc)

    print("{}")
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        try:
            print("{}")
        except Exception:
            pass
        sys.exit(0)
