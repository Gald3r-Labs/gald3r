#!/usr/bin/env python3
"""
Persist Claude Code chat history to .gald3r/logs/ — the Claude-side mirror of
g-hk-cursor-chat-logger.py (BUG-091).

Claude Code's Stop hook provides the session transcript path directly, so this
logger needs no database scraping (unlike the Cursor engine, which reads
Cursor's state.vscdb). It reads the transcript JSONL and writes a
human-readable transcript in the SAME format the Cursor logger produces:

    timestamp / platform / conversation_id / status / loop_count / turns
    ---
    [Turn N] User / [Turn N] Assistant blocks

Claude transcript schema differences handled here:
- The role is at record["message"]["role"]; the top-level "type" field is the
  discriminator ("user" | "assistant" | "system" | "attachment" | ...).
- A user message's content may be a plain string OR a list of content blocks.
- Tool results are recorded as type=="user" records whose content is a list
  containing a "tool_result" block — these are NOT human turns and are skipped.
- Sidechain (subagent) records carry isSidechain==true and are skipped, mirroring
  the Cursor logger's exclusion of agent-transcripts/subagents.
- Only "text" content blocks are emitted (tool_use / thinking are skipped),
  matching the Cursor logger which extracts type=="text" only.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


def extract_text_blocks(content: object) -> str:
    """Return the human-readable text from a message's content.

    Handles both the string form (Claude user prompts) and the list-of-blocks
    form (Claude assistant messages and rich user messages).
    """
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: List[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"].strip())
    return "\n\n".join(part for part in parts if part)


def is_tool_result(content: object) -> bool:
    """True when a user-role record is actually a tool result, not a human turn."""
    if isinstance(content, list):
        return any(
            isinstance(block, dict) and block.get("type") == "tool_result"
            for block in content
        )
    return False


def extract_turns_from_transcript(transcript_path: Path) -> List[Dict[str, str]]:
    """Pair human prompts with the assistant text that follows, like Cursor's logger.

    A new human user message starts a turn; all assistant text up to the next
    human user message is concatenated into that turn's assistant side.
    """
    turns: List[Dict[str, str]] = []
    pending_user: Optional[str] = None
    assistant_buf: List[str] = []

    def flush() -> None:
        nonlocal pending_user, assistant_buf
        if pending_user is not None or assistant_buf:
            turns.append(
                {
                    "user": pending_user or "",
                    "assistant": "\n\n".join(a for a in assistant_buf if a),
                }
            )
        pending_user = None
        assistant_buf = []

    for raw_line in transcript_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        if record.get("isSidechain"):
            continue

        rtype = record.get("type")
        if rtype not in ("user", "assistant"):
            continue

        message = record.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")

        if rtype == "user":
            if is_tool_result(content):
                continue
            text = extract_text_blocks(content)
            if not text:
                continue
            flush()
            pending_user = text
        elif rtype == "assistant":
            text = extract_text_blocks(content)
            if text:
                assistant_buf.append(text)

    flush()
    return turns


def sanitize_for_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)
    return cleaned[:32] or "unknown"


def write_chat_log(
    project_path: Path,
    conversation_id: str,
    loop_count: int,
    status: str,
    platform: str,
    turns: List[Dict[str, str]],
) -> Path:
    """Write the transcript using the exact format of g-hk-cursor-chat-logger.py."""
    logs_dir = project_path / ".gald3r" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    short_id = sanitize_for_filename(conversation_id)
    platform_slug = sanitize_for_filename(platform)
    file_path = logs_dir / f"{date_part}_{short_id}_{platform_slug}_chat.log"

    lines = [
        f"timestamp: {now.isoformat()}",
        f"platform: {platform}",
        f"conversation_id: {conversation_id}",
        f"status: {status}",
        f"loop_count: {loop_count}",
        f"turns: {len(turns)}",
        "---",
        "",
    ]

    for idx, turn in enumerate(turns, start=1):
        user_text = (turn.get("user") or "").strip()
        assistant_text = (turn.get("assistant") or "").strip()
        lines.append(f"[Turn {idx}] User")
        lines.append(user_text or "[empty]")
        lines.append("")
        lines.append(f"[Turn {idx}] Assistant")
        lines.append(assistant_text or "[empty]")
        lines.append("")
        lines.append("---")
        lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a Claude Code chat transcript to .gald3r/logs"
    )
    parser.add_argument("--transcript-path", required=True)
    parser.add_argument("--project-path", default=os.getcwd())
    parser.add_argument("--conversation-id", default=None)
    parser.add_argument("--status", default="completed")
    parser.add_argument("--platform", default="claude")
    parser.add_argument("--loop-count", type=int, default=0)
    args = parser.parse_args()

    transcript_path = Path(args.transcript_path)
    if not transcript_path.exists():
        return 1

    conversation_id = args.conversation_id or transcript_path.stem
    turns = extract_turns_from_transcript(transcript_path)
    if not turns:
        return 3

    write_chat_log(
        project_path=Path(args.project_path),
        conversation_id=conversation_id,
        loop_count=args.loop_count,
        status=args.status,
        platform=args.platform,
        turns=turns,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
