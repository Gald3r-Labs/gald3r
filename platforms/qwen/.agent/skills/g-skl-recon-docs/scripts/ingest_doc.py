#!/usr/bin/env python3
"""
ingest_doc.py — gald3r documentation URL ingester with revisit tracking.
Fetches a URL via crawl4ai and stores it in research/platforms/.

Usage:
    python ingest_doc.py --url URL --vault-path PATH --name NAME
                         [--refresh-days N] [--no-js] [--force]
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None  # handled at runtime


INDEX_FILE = "_index.yaml"
CRAWL_SCRIPT = Path(__file__).parent.parent.parent.parent / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py"


def find_crawl_script():
    """Walk up looking for the crawl_url.py script relative to .gald3r/."""
    current = Path(__file__).resolve()
    for _ in range(8):
        candidate = current / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py"
        if candidate.exists():
            return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: same tree as this file
    return str(Path(__file__).parent.parent.parent.parent / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py")


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_len]


def load_index(platforms_dir: Path) -> list:
    if yaml is None:
        raise RuntimeError("PyYAML not installed — run: pip install pyyaml")
    index_path = platforms_dir / INDEX_FILE
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def save_index(platforms_dir: Path, index: list):
    if yaml is None:
        raise RuntimeError("PyYAML not installed — run: pip install pyyaml")
    index_path = platforms_dir / INDEX_FILE
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index, f, default_flow_style=False, allow_unicode=True)


def find_entry(index: list, url: str) -> tuple[int, dict | None]:
    for i, entry in enumerate(index):
        if entry.get("url") == url:
            return i, entry
    return -1, None


def is_stale(entry: dict) -> bool:
    next_refresh = entry.get("next_refresh", "")
    if not next_refresh:
        return True
    try:
        return datetime.today().date() >= datetime.strptime(next_refresh, "%Y-%m-%d").date()
    except ValueError:
        return True


def infer_platform_from_url(url: str) -> str:
    """Map documentation URL to Obsidian platform tag (T044 §3.2)."""
    u = url.lower()
    if "anthropic.com" in u or "docs.claude" in u:
        return "claude-code"
    if "cursor.com" in u or "cursor.sh" in u:
        return "cursor"
    if "openai.com" in u or "platform.openai" in u:
        return "openai"
    if "google.dev" in u or "ai.google" in u or "gemini" in u:
        return "gemini"
    if "opencode.ai" in u or "opencode" in urlparse(url).netloc.lower():
        return "opencode"
    host = urlparse(url).netloc.lower().split(":")[0]
    if not host:
        return "docs"
    parts = host.replace("www.", "").split(".")
    stem = parts[0] if len(parts) < 2 else parts[-2]
    return re.sub(r"[^\w-]", "", stem.replace("_", "-"))[:40] or "docs"


_SEGMENT_ALIASES = {
    "agent": "agents",
    "agents": "agents",
    "mcp": "mcp",
    "api": "api",
    "models": "models",
    "docs": "docs",
    "documentation": "docs",
    "guide": "guide",
    "hooks": "hooks",
    "tools": "tools",
    "cli": "cli",
    "sdk": "sdk",
}


def extract_topic_tags(url: str, max_extra: int = 8) -> list[str]:
    """Derive lowercase hyphen tags from URL path segments (T045)."""
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return []
    skip = {"en", "us", "latest", "stable", "v1", "v2", "v3", "docs", "documentation"}
    out: list[str] = []
    for seg in path.split("/"):
        seg = re.sub(r"[^\w\-]", "", seg.replace("_", "-"))
        if not seg or seg in skip or seg.isdigit():
            continue
        tag = _SEGMENT_ALIASES.get(seg, seg)
        if tag not in out:
            out.append(tag)
        if len(out) >= max_extra:
            break
    return out


def crawl(url: str, output_path: str, no_js: bool):
    crawl_script = find_crawl_script()
    cmd = [sys.executable, crawl_script, "--url", url, "--output", output_path]
    if no_js:
        cmd.append("--no-js")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())


def build_platform_doc_tags(url: str, platform: str | None) -> list[str]:
    plat = (platform or infer_platform_from_url(url)).strip().lower().replace(" ", "-")
    topics = extract_topic_tags(url)
    tags = ["platform-doc", plat]
    for t in topics:
        t = t.lower().replace("_", "-")
        if t and t not in tags:
            tags.append(t)
        if len(tags) >= 10:
            break
    return tags


def write_note(
    out_path: Path,
    url: str,
    name: str,
    refresh_days: int,
    markdown: str,
    platform: str | None = None,
):
    today = datetime.today().strftime("%Y-%m-%d")
    next_refresh = (datetime.today() + timedelta(days=refresh_days)).strftime("%Y-%m-%d")
    tags = build_platform_doc_tags(url, platform)
    if yaml is not None:
        tags_yaml = yaml.dump(tags, default_flow_style=True).strip()
        topics_yaml = yaml.dump(tags, default_flow_style=True).strip()
    else:
        import json

        tags_yaml = json.dumps(tags)
        topics_yaml = json.dumps(tags)
    header = f"""---
date: {today}
type: platform_doc
ingestion_type: periodic
source: {url}
title: "{name}"
tags: {tags_yaml}
topics: {topics_yaml}
refresh_policy: every_{refresh_days}_days
last_fetched: {today}
next_refresh: {next_refresh}
source_volatility: living_document
analysis_depth: full_text
---

"""
    out_path.write_text(header + markdown, encoding="utf-8")


def append_log(vault_path: str, out_path: str, action: str = "ingest"):
    log_path = Path(vault_path) / "log.md"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rel = os.path.relpath(out_path, vault_path)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## {timestamp} | {action} | {rel}\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest a documentation URL into the vault")
    parser.add_argument("--url", required=True)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--name", required=True, help="Human-readable name for this doc set")
    parser.add_argument(
        "--platform",
        default=None,
        help="Obsidian platform tag (e.g. cursor, claude-code). Default: inferred from URL.",
    )
    parser.add_argument("--refresh-days", type=int, default=30)
    parser.add_argument("--no-js", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if not stale")
    args = parser.parse_args()

    platforms_dir = Path(args.vault_path) / "research" / "platforms"
    platforms_dir.mkdir(parents=True, exist_ok=True)

    index = load_index(platforms_dir)
    idx, entry = find_entry(index, args.url)
    today = datetime.today().strftime("%Y-%m-%d")
    next_refresh = (datetime.today() + timedelta(days=args.refresh_days)).strftime("%Y-%m-%d")
    slug = slugify(args.name)
    out_path = platforms_dir / f"{slug}.md"

    if entry and not is_stale(entry) and not args.force:
        print(f"FRESH: {args.url} (next refresh: {entry.get('next_refresh')}) — skip (use --force to override)")
        return

    print(f"Fetching: {args.url}", file=sys.stderr)
    try:
        crawl(args.url, str(out_path), args.no_js)
    except RuntimeError as exc:
        print(f"FETCH_ERROR: {exc}", file=sys.stderr)
        # Update status in index to 'error'
        new_entry = {
            "url": args.url, "name": args.name, "slug": slug,
            "last_fetched": today, "refresh_days": args.refresh_days,
            "next_refresh": next_refresh, "status": "error",
            "vault_path": str(out_path.relative_to(args.vault_path)),
        }
        if idx >= 0:
            index[idx] = new_entry
        else:
            index.append(new_entry)
        save_index(platforms_dir, index)
        sys.exit(1)

    # Read the fetched content and re-write with frontmatter
    raw_markdown = out_path.read_text(encoding="utf-8")
    write_note(
        out_path,
        args.url,
        args.name,
        args.refresh_days,
        raw_markdown,
        platform=args.platform,
    )

    new_entry = {
        "url": args.url, "name": args.name, "slug": slug,
        "last_fetched": today, "refresh_days": args.refresh_days,
        "next_refresh": next_refresh, "status": "fresh",
        "vault_path": str(out_path.relative_to(args.vault_path)),
    }
    if idx >= 0:
        index[idx] = new_entry
    else:
        index.append(new_entry)
    save_index(platforms_dir, index)
    append_log(args.vault_path, str(out_path))
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
