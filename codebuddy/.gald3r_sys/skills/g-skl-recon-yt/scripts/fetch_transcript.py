#!/usr/bin/env python3
"""
fetch_transcript.py — gald3r YouTube transcript fetcher
Uses yt-dlp to download captions and metadata, then writes a vault note.

Usage:
    python fetch_transcript.py --url URL --vault-path PATH [--no-summary]
    python fetch_transcript.py --check-setup
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Setup check
# ---------------------------------------------------------------------------

def check_ytdlp():
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def cmd_check_setup():
    ver = check_ytdlp()
    if ver:
        print(f"yt-dlp {ver} — OK")
        sys.exit(0)
    else:
        print("SETUP_REQUIRED: yt-dlp not found — run: pip install yt-dlp", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_len]


def fetch_metadata(url: str) -> dict:
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"METADATA_ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def fetch_vtt(url: str, tmpdir: str) -> str | None:
    """Download VTT captions; return path or None if unavailable."""
    result = subprocess.run(
        [
            "yt-dlp",
            "--write-auto-sub", "--write-subs",
            "--skip-download",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "--output", os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "--no-playlist",
            url,
        ],
        capture_output=True, text=True, timeout=120
    )
    vtt_files = list(Path(tmpdir).glob("*.vtt"))
    if vtt_files:
        return str(vtt_files[0])
    return None


def parse_vtt(vtt_path: str) -> str:
    """Parse VTT file → clean deduplicated transcript text."""
    with open(vtt_path, encoding="utf-8") as f:
        content = f.read()

    lines = []
    prev_line = ""
    in_cue = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        # Skip header, timestamp lines, NOTE lines, empty
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            in_cue = False
            continue
        if re.match(r"^\d{2}:\d{2}", line) or "-->" in line:
            in_cue = True
            continue
        if re.match(r"^\d+$", line):
            continue

        # Strip VTT tags like <00:01:23.456><c>text</c>
        line = re.sub(r"<[^>]+>", "", line).strip()

        if in_cue and line and line != prev_line:
            lines.append(line)
            prev_line = line

    return " ".join(lines)


def generate_summary(transcript: str) -> tuple[str, list[str]]:
    """
    Simple heuristic summary — first 3 sentences + extract key phrases.
    A real implementation would call an LLM API here.
    """
    sentences = re.split(r"(?<=[.!?])\s+", transcript.strip())
    summary = " ".join(sentences[:3]) if sentences else transcript[:300]
    # Key points: sentences 4-9 as bullet hints
    key_points = [s.strip() for s in sentences[3:9] if len(s.strip()) > 20]
    return summary, key_points


def build_video_tags(metadata: dict) -> list[str]:
    """Derive tags from yt-dlp metadata for Obsidian indexing."""
    tags: list[str] = ["video"]
    channel = metadata.get("uploader", metadata.get("channel", ""))
    if channel:
        slug = re.sub(r"[^\w\s-]", "", channel.lower())
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")[:40]
        if slug and slug not in tags:
            tags.append(slug)
    for cat in (metadata.get("categories") or [])[:4]:
        slug = re.sub(r"[^\w\s-]", "", str(cat).lower())
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")[:40]
        if slug and slug not in tags:
            tags.append(slug)
    for t in (metadata.get("tags") or [])[:6]:
        slug = re.sub(r"[^\w\s-]", "", str(t).lower())
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")[:40]
        if slug and slug not in tags:
            tags.append(slug)
        if len(tags) >= 10:
            break
    return tags


def write_vault_note(
    vault_path: str,
    metadata: dict,
    transcript: str,
    summary: str,
    key_points: list[str],
) -> str:
    title = metadata.get("title", "Unknown Title")
    channel = metadata.get("uploader", metadata.get("channel", ""))
    upload_ts = metadata.get("upload_date", "")  # YYYYMMDD
    try:
        upload_date = f"{upload_ts[:4]}-{upload_ts[4:6]}-{upload_ts[6:8]}"
    except Exception:
        upload_date = ""
    duration_sec = metadata.get("duration", 0) or 0
    duration_min = round(duration_sec / 60, 1)
    source_url = metadata.get("webpage_url", metadata.get("original_url", ""))

    today = datetime.today().strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{today}_{slug}.md"

    out_dir = Path(vault_path) / "research" / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    kp_md = "\n".join(f"- {p}" for p in key_points) if key_points else "- (see transcript)"

    tags = build_video_tags(metadata)
    try:
        import yaml as _yaml
        tags_yaml = _yaml.dump(tags, default_flow_style=True).strip()
        topics_yaml = _yaml.dump(tags, default_flow_style=True).strip()
    except ImportError:
        import json
        tags_yaml = json.dumps(tags)
        topics_yaml = json.dumps(tags)

    note = f"""---
date: {today}
type: video
ingestion_type: one_shot
source: {source_url}
title: "{title}"
channel: "{channel}"
published: "{upload_date}"
duration_minutes: {duration_min}
tags: {tags_yaml}
topics: {topics_yaml}
refresh_policy: manual
source_volatility: snapshot
analysis_depth: transcript_only
source_notes: "Transcript captured {today}. No visual analysis."
---

## Summary
{summary}

## Key Points
{kp_md}

## Full Transcript
{transcript}
"""

    out_path.write_text(note, encoding="utf-8")
    return str(out_path)


def append_log(vault_path: str, out_path: str):
    log_path = Path(vault_path) / "log.md"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rel = os.path.relpath(out_path, vault_path)
    entry = f"\n## {timestamp} | ingest | {rel}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if "--check-setup" in sys.argv:
        cmd_check_setup()

    parser = argparse.ArgumentParser(description="Ingest a YouTube video transcript into the vault")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--vault-path", required=True, help="Path to vault root")
    parser.add_argument("--no-summary", action="store_true", help="Skip AI summary generation")
    args = parser.parse_args()

    if not check_ytdlp():
        print("SETUP_REQUIRED: yt-dlp not found — run: pip install yt-dlp", file=sys.stderr)
        sys.exit(2)

    print(f"Fetching metadata: {args.url}", file=sys.stderr)
    metadata = fetch_metadata(args.url)

    with tempfile.TemporaryDirectory() as tmpdir:
        print("Downloading captions...", file=sys.stderr)
        vtt_path = fetch_vtt(args.url, tmpdir)

        if vtt_path:
            print(f"Parsing captions: {os.path.basename(vtt_path)}", file=sys.stderr)
            transcript = parse_vtt(vtt_path)
        else:
            print("WARNING: No captions available — creating metadata-only note", file=sys.stderr)
            transcript = "(No captions available for this video.)"

    summary, key_points = ("", [])
    if not args.no_summary and len(transcript) > 50:
        summary, key_points = generate_summary(transcript)

    out_path = write_vault_note(
        vault_path=args.vault_path,
        metadata=metadata,
        transcript=transcript,
        summary=summary,
        key_points=key_points,
    )

    append_log(args.vault_path, out_path)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
