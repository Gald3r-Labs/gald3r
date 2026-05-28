#!/usr/bin/env python3
"""
ingest_url.py — gald3r one-time URL ingester.
Captures a URL (or list of URLs) into research/articles/ with dedup.

Usage:
    python ingest_url.py --url URL --vault-path PATH [--title TITLE] [--tags t1,t2] [--no-js] [--force]
    python ingest_url.py --urls-file FILE --vault-path PATH [--no-js] [--resume]
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("SETUP_REQUIRED: PyYAML not installed — run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

INDEX_FILE = "_index.yaml"


def find_crawl_script():
    current = Path(__file__).resolve()
    for _ in range(8):
        candidate = current / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py"
        if candidate.exists():
            return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return str(Path(__file__).parent.parent.parent.parent / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py")


def slugify_url(url: str, max_len: int = 80) -> str:
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w\-]", "_", slug)
    return slug[:max_len]


def slugify_title(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_len]


def extract_metadata(markdown: str) -> tuple[str, str, str]:
    """Extract (title, author, published_date) from crawl4ai markdown output.

    Extraction priority:
    - title:     first ATX heading (# …) → first setext underline → empty string
    - author:    "By …" / "Author: …" / "Written by …" patterns → empty string
    - published: ISO date (YYYY-MM-DD) near "date", "published", "posted" keywords
                 → other common date patterns → empty string

    Returns empty strings for any field that cannot be extracted.
    """
    title = ""
    author = ""
    published = ""

    lines = markdown.splitlines()

    # ── Title: first ATX heading ────────────────────────────────────────────
    for line in lines:
        m = re.match(r"^#{1,6}\s+(.+)", line)
        if m:
            title = m.group(1).strip().strip("#").strip()
            break

    # Fallback: setext-style heading (line followed by ===)
    if not title:
        for i, line in enumerate(lines):
            if i + 1 < len(lines) and re.match(r"^=+\s*$", lines[i + 1]) and line.strip():
                title = line.strip()
                break

    # ── Author: byline heuristics ────────────────────────────────────────────
    author_patterns = [
        r"(?i)^by\s+([A-Z][a-zA-Z .'-]{2,40})(?:\s*[|,]|$)",
        r"(?i)\bauthor[:\s]+([A-Z][a-zA-Z .'-]{2,40})(?:\s*[|,]|$)",
        r"(?i)written\s+by\s+([A-Z][a-zA-Z .'-]{2,40})(?:\s*[|,]|$)",
        r"(?i)posted\s+by\s+([A-Z][a-zA-Z .'-]{2,40})(?:\s*[|,]|$)",
        r"(?i)published\s+by\s+([A-Z][a-zA-Z .'-]{2,40})(?:\s*[|,]|$)",
    ]
    for line in lines[:60]:  # only scan the first 60 lines for byline
        for pat in author_patterns:
            m = re.search(pat, line)
            if m:
                candidate = m.group(1).strip().rstrip(".,")
                # Reject obvious false positives (very short or looks like a date)
                if len(candidate) >= 3 and not re.search(r"\d{4}", candidate):
                    author = candidate
                    break
        if author:
            break

    # ── Published date ────────────────────────────────────────────────────────
    # Look for ISO dates near date-related keywords first
    iso_near_keyword = re.compile(
        r"(?i)(?:published|posted|date|updated|written)[^\n]{0,30}?(\d{4}-\d{2}-\d{2})"
    )
    m = iso_near_keyword.search(markdown[:4000])
    if m:
        published = m.group(1)

    if not published:
        # Any ISO date in the first 4000 chars
        m = re.search(r"(\d{4}-\d{2}-\d{2})", markdown[:4000])
        if m:
            published = m.group(1)

    if not published:
        # Long-form dates: "January 15, 2026" / "Jan 15 2026" / "15 January 2026"
        long_date = re.compile(
            r"(?i)(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"\s+\d{1,2}[,\s]+\d{4}"
        )
        m = long_date.search(markdown[:4000])
        if m:
            # Normalise to YYYY-MM-DD best-effort; leave as-is if parsing fails
            try:
                from datetime import datetime as _dt
                raw = m.group(0).strip().replace(",", "")
                for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
                    try:
                        published = _dt.strptime(raw, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
            except Exception:
                published = m.group(0).strip()

    return title, author, published


def load_index(articles_dir: Path) -> list:
    index_path = articles_dir / INDEX_FILE
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def save_index(articles_dir: Path, index: list):
    index_path = articles_dir / INDEX_FILE
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index, f, default_flow_style=False, allow_unicode=True)


def is_duplicate(index: list, url: str) -> dict | None:
    for entry in index:
        if entry.get("url") == url:
            return entry
    return None


def crawl(url: str, output_path: str, no_js: bool):
    crawl_script = find_crawl_script()
    cmd = [sys.executable, crawl_script, "--url", url, "--output", output_path]
    if no_js:
        cmd.append("--no-js")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())


def write_note(out_path: Path, url: str, title: str, author: str,
               published: str, tags: list[str], markdown: str):
    today = datetime.today().strftime("%Y-%m-%d")
    merged: list[str] = ["article"]
    for t in tags:
        nt = str(t).strip().lower().replace(" ", "-").replace("_", "-")
        if nt and nt not in merged:
            merged.append(nt)
        if len(merged) >= 10:
            break
    tags_yaml = yaml.dump(merged, default_flow_style=True).strip()
    topics_yaml = yaml.dump(merged, default_flow_style=True).strip()
    header = f"""---
date: {today}
type: article
ingestion_type: one_shot
source: {url}
title: "{title}"
author: "{author}"
published: "{published}"
tags: {tags_yaml}
topics: {topics_yaml}
refresh_policy: manual
source_volatility: snapshot
source_notes: "Captured {today}. Original page may have changed."
analysis_depth: full_text
---

"""
    out_path.write_text(header + markdown, encoding="utf-8")


def append_log(vault_path: str, out_path: str):
    log_path = Path(vault_path) / "log.md"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rel = os.path.relpath(out_path, vault_path)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## {timestamp} | ingest | {rel}\n")


def ingest_one(url: str, vault_path: str, title_override: str | None,
               tags: list[str], no_js: bool, force: bool) -> bool:
    articles_dir = Path(vault_path) / "research" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    index = load_index(articles_dir)

    existing = is_duplicate(index, url)
    if existing and not force:
        print(f"DUPLICATE: {url} (captured {existing.get('date', '?')}) — skip (use --force to re-capture)")
        return True  # not an error

    today = datetime.today().strftime("%Y-%m-%d")
    slug = slugify_url(url)
    out_path = articles_dir / f"{today}_{slug}.md"

    print(f"Fetching: {url}", file=sys.stderr)
    try:
        crawl(url, str(out_path), no_js)
    except RuntimeError as exc:
        print(f"FETCH_ERROR: {exc}", file=sys.stderr)
        return False

    raw_markdown = out_path.read_text(encoding="utf-8")

    # Extract metadata from crawled content; fall back to manual override or URL
    extracted_title, extracted_author, extracted_published = extract_metadata(raw_markdown)
    title = title_override or extracted_title or url
    author = extracted_author
    published = extracted_published

    if extracted_title and not title_override:
        print(f"  Title: {title}", file=sys.stderr)
    if author:
        print(f"  Author: {author}", file=sys.stderr)
    if published:
        print(f"  Published: {published}", file=sys.stderr)

    write_note(out_path, url, title, author, published, tags, raw_markdown)

    entry = {
        "url": url,
        "title": title,
        "author": author,
        "published": published,
        "date": today,
        "vault_path": str(out_path.relative_to(vault_path)),
        "tags": tags,
    }
    # Replace existing entry or append
    if existing:
        for i, e in enumerate(index):
            if e.get("url") == url:
                index[i] = entry
                break
    else:
        index.append(entry)
    save_index(articles_dir, index)
    append_log(vault_path, str(out_path))
    print(f"Saved: {out_path}")
    return True


def load_urls(urls_file: str) -> list[str]:
    urls = []
    with open(urls_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(description="One-time URL ingestion into vault")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single URL to ingest")
    group.add_argument("--urls-file", help="Text file with one URL per line")
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--title", default=None, help="Optional title override (single URL mode)")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--no-js", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-ingest even if already captured")
    parser.add_argument("--resume", action="store_true", help="Skip URLs already captured (batch mode default)")
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    if args.url:
        ok = ingest_one(args.url, args.vault_path, args.title, tags, args.no_js, args.force)
        sys.exit(0 if ok else 1)
    else:
        urls = load_urls(args.urls_file)
        ok_count, fail_count = 0, 0
        for url in urls:
            success = ingest_one(url, args.vault_path, None, tags, args.no_js, args.force)
            if success:
                ok_count += 1
            else:
                fail_count += 1
        print(f"\nDone: {ok_count} OK / {fail_count} failed")
        if fail_count:
            sys.exit(1)


if __name__ == "__main__":
    main()
