#!/usr/bin/env python3
"""
Persist local chat history to .gald3r/logs without MCP dependencies.

This script is intentionally slim:
- prefers an explicit transcript file when the host platform provides one
- falls back to Cursor project transcripts for this workspace
- falls back again to Cursor's local state.vscdb
- writes a human-readable transcript to .gald3r/logs/
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


def find_state_vscdb() -> Optional[Path]:
    candidates: List[Path] = []

    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            candidates.append(Path(appdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb")
        if localappdata:
            candidates.append(Path(localappdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb")
    elif sys.platform == "darwin":
        candidates.append(
            Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "state.vscdb"
        )
    else:
        candidates.append(Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "state.vscdb")

    for path in candidates:
        if path.exists():
            return path
    return None


def copy_db(db_path: Path) -> Path:
    fd, tmp_name = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tmp_path = Path(tmp_name)
    shutil.copy2(db_path, tmp_path)
    return tmp_path


def decode_value(raw_value: object) -> str:
    if isinstance(raw_value, (bytes, bytearray)):
        return raw_value.decode("utf-8", errors="replace")
    return str(raw_value)


def slugify_project_path(project_path: Path) -> str:
    raw = str(project_path.resolve()).replace(":", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", raw).strip("-").lower()
    return slug


def find_project_transcript_root(project_path: Path) -> Optional[Path]:
    slug = slugify_project_path(project_path)
    transcript_root = Path.home() / ".cursor" / "projects" / slug / "agent-transcripts"
    if transcript_root.exists():
        return transcript_root
    return None


def find_transcript_file(project_path: Path, conversation_id: Optional[str]) -> Optional[Path]:
    transcript_root = find_project_transcript_root(project_path)
    if not transcript_root:
        return None

    if conversation_id and conversation_id.lower() not in {"unknown", "none", ""}:
        direct_path = transcript_root / conversation_id / f"{conversation_id}.jsonl"
        if direct_path.exists():
            return direct_path

    candidates = [
        path
        for path in transcript_root.glob("*/*.jsonl")
        if "subagents" not in {part.lower() for part in path.parts}
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def extract_text_blocks(content: object) -> str:
    if not isinstance(content, list):
        return ""

    parts: List[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"].strip())
    return "\n\n".join(part for part in parts if part)


def extract_turns_from_transcript(transcript_path: Path) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    pending_user = ""

    for raw_line in transcript_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        role = record.get("role")
        message = record.get("message", {})
        text = extract_text_blocks(message.get("content"))
        if not text:
            continue

        if role == "user":
            pending_user = text
        elif role == "assistant":
            turns.append({"user": pending_user, "assistant": text})
            pending_user = ""

    if pending_user:
        turns.append({"user": pending_user, "assistant": ""})

    return turns


def find_latest_conversation_id(db_path: Path) -> Optional[str]:
    tmp_path = copy_db(db_path)
    try:
        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
        rows = cur.fetchall()
    finally:
        try:
            conn.close()
        except Exception:
            pass
        tmp_path.unlink(missing_ok=True)

    best_id = None
    best_count = -1

    for row in rows:
        key = row["key"]
        raw_value = decode_value(row["value"])
        conv_id = key.split(":", 1)[1] if ":" in key else None
        if not conv_id:
            continue
        try:
            data = json.loads(raw_value)
        except Exception:
            continue
        headers = data.get("fullConversationHeadersOnly", [])
        bubble_count = len(headers)
        if bubble_count > best_count:
            best_count = bubble_count
            best_id = conv_id

    return best_id


def extract_turns_from_vscdb(db_path: Path, conversation_id: str) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    tmp_path = copy_db(db_path)

    try:
        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        composer_key = f"composerData:{conversation_id}"
        cur.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (composer_key,))
        row = cur.fetchone()

        if not row:
            cur.execute(
                "SELECT key, value FROM cursorDiskKV WHERE key LIKE ?",
                (f"composerData:%{conversation_id}%",),
            )
            matches = cur.fetchall()
            row = matches[0] if matches else None

        if not row:
            return turns

        composer_data = json.loads(decode_value(row["value"]))
        headers = composer_data.get("fullConversationHeadersOnly", [])

        if not headers:
            for key in ["bubbles", "conversation"]:
                candidate = composer_data.get(key, [])
                if isinstance(candidate, dict):
                    candidate = candidate.get("bubbles", [])
                if isinstance(candidate, list) and candidate:
                    headers = [
                        {
                            "bubbleId": bubble.get("bubbleId"),
                            "type": 1 if bubble.get("role") in ("user", "human") else 2,
                        }
                        for bubble in candidate
                        if isinstance(bubble, dict) and bubble.get("bubbleId")
                    ]
                    break

        user_msg: Optional[str] = None

        for header in headers:
            bubble_id = header.get("bubbleId")
            bubble_type = header.get("type", 0)
            if not bubble_id:
                continue

            bubble_key = f"bubbleId:{conversation_id}:{bubble_id}"
            cur.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (bubble_key,))
            bubble_row = cur.fetchone()

            if not bubble_row:
                cur.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (f"bubbleId:{bubble_id}",))
                bubble_row = cur.fetchone()

            if not bubble_row:
                continue

            bubble = json.loads(decode_value(bubble_row["value"]))
            if isinstance(bubble, dict):
                text = bubble.get("text") or bubble.get("rawText") or bubble.get("content", "")
            else:
                text = str(bubble)

            if not isinstance(text, str):
                text = json.dumps(text)

            text = text.strip()
            if not text:
                continue

            if bubble_type == 1:
                user_msg = text
            elif bubble_type == 2:
                turns.append({"user": user_msg or "", "assistant": text})
                user_msg = None

        if user_msg:
            turns.append({"user": user_msg, "assistant": ""})
    finally:
        try:
            conn.close()
        except Exception:
            pass
        tmp_path.unlink(missing_ok=True)

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
    parser = argparse.ArgumentParser(description="Write a local chat transcript to .gald3r/logs")
    parser.add_argument("--conversation-id", default=None)
    parser.add_argument("--project-path", default=os.getcwd())
    parser.add_argument("--loop-count", type=int, default=0)
    parser.add_argument("--status", default="completed")
    parser.add_argument("--platform", default="cursor")
    parser.add_argument("--transcript-path", default=None)
    parser.add_argument("--vscdb", default=None)
    args = parser.parse_args()

    project_path = Path(args.project_path)

    conversation_id = args.conversation_id
    turns: List[Dict[str, str]] = []

    transcript_path = Path(args.transcript_path) if args.transcript_path else None
    if transcript_path and transcript_path.exists():
        turns = extract_turns_from_transcript(transcript_path)
        if not conversation_id:
            conversation_id = transcript_path.stem

    if not turns:
        transcript_path = find_transcript_file(project_path, conversation_id)
    else:
        transcript_path = None

    if transcript_path:
        turns = extract_turns_from_transcript(transcript_path)
        if not conversation_id:
            conversation_id = transcript_path.stem

    if not turns:
        db_path = Path(args.vscdb) if args.vscdb else find_state_vscdb()
        if not db_path or not db_path.exists():
            return 1
        if not conversation_id or conversation_id.lower() in {"unknown", "none", ""}:
            conversation_id = find_latest_conversation_id(db_path)
        if not conversation_id:
            return 2
        turns = extract_turns_from_vscdb(db_path, conversation_id)

    if not turns:
        return 3

    write_chat_log(
        project_path=project_path,
        conversation_id=conversation_id,
        loop_count=args.loop_count,
        status=args.status,
        platform=args.platform,
        turns=turns,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
