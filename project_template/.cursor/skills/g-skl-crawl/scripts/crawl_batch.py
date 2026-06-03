#!/usr/bin/env python3
"""
crawl_batch.py — gald3r crawl4ai batch URL fetcher
Reads a text file of URLs and writes one .md file per URL.

Usage:
    python crawl_batch.py --urls-file FILE --output-dir DIR [--no-js] [--resume]
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path


def check_crawl4ai():
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        print(
            "SETUP_REQUIRED: crawl4ai not installed — run: pip install crawl4ai "
            "&& python -m playwright install --with-deps chromium",
            file=sys.stderr,
        )
        sys.exit(2)


def slugify(url: str) -> str:
    """Convert URL to a safe filename stem (max 120 chars)."""
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w\-]", "_", slug)
    return slug[:120]


def load_urls(urls_file: str) -> list[str]:
    """Read URLs from file — one per line, skip blank lines and # comments."""
    urls = []
    with open(urls_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def load_state(state_file: str) -> dict:
    if os.path.exists(state_file):
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state_file: str, state: dict):
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


async def crawl_one(crawler, url: str, use_js: bool, timeout: int) -> str | None:
    from crawl4ai import CrawlerRunConfig

    run_cfg = CrawlerRunConfig(
        word_count_threshold=10,
        exclude_external_links=True,
        js_code=None if use_js else "",
        page_timeout=timeout * 1000,
    )
    try:
        result = await crawler.arun(url=url, config=run_cfg)
        if not result.success:
            return None
        return result.markdown or result.cleaned_html or ""
    except Exception:
        return None


async def batch(urls_file: str, output_dir: str, use_js: bool, resume: bool, timeout: int = 30):
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    urls = load_urls(urls_file)
    if not urls:
        print("No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    state_file = os.path.join(output_dir, "crawl_batch_state.json")
    state = load_state(state_file) if resume else {}

    browser_cfg = BrowserConfig(headless=True)
    ok, fail, skip = 0, 0, 0

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for url in urls:
            if resume and state.get(url) == "ok":
                skip += 1
                print(f"SKIP  {url}", file=sys.stderr)
                continue

            state[url] = "in_progress"
            save_state(state_file, state)

            markdown = await crawl_one(crawler, url, use_js, timeout)

            if markdown is None:
                state[url] = "failed"
                fail += 1
                print(f"FAIL  {url}", file=sys.stderr)
            else:
                out_path = Path(output_dir) / f"{slugify(url)}.md"
                out_path.write_text(markdown, encoding="utf-8")
                state[url] = "ok"
                ok += 1
                print(f"OK    {url} → {out_path.name}", file=sys.stderr)

            save_state(state_file, state)

    print(f"\nDone: {ok} OK / {fail} failed / {skip} skipped", file=sys.stderr)
    if fail:
        sys.exit(1)


def main():
    check_crawl4ai()

    parser = argparse.ArgumentParser(description="Batch-crawl a list of URLs to Markdown files")
    parser.add_argument("--urls-file", required=True, help="Text file with one URL per line")
    parser.add_argument("--output-dir", required=True, help="Directory to write .md files into")
    parser.add_argument("--no-js", action="store_true", help="Disable JS rendering")
    parser.add_argument("--resume", action="store_true", help="Skip URLs already marked 'ok' in state file")
    parser.add_argument("--timeout", type=int, default=30, help="Per-URL timeout in seconds (default: 30)")
    args = parser.parse_args()

    asyncio.run(batch(
        urls_file=args.urls_file,
        output_dir=args.output_dir,
        use_js=not args.no_js,
        resume=args.resume,
        timeout=args.timeout,
    ))


if __name__ == "__main__":
    main()
