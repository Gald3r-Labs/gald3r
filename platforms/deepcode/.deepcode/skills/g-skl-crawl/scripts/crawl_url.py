#!/usr/bin/env python3
"""
crawl_url.py — gald3r crawl4ai single-URL fetcher
Produces clean LLM-optimized Markdown from a URL.
No Docker, no MCP required.

Usage:
    python crawl_url.py --url URL [--output FILE] [--no-js] [--timeout N]
"""

import argparse
import asyncio
import sys
import re


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
    """Convert URL to a safe filename stem."""
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w\-]", "_", slug)
    return slug[:120]


async def fetch(url: str, use_js: bool, timeout: int, output_path: str | None):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(
        word_count_threshold=10,
        exclude_external_links=True,
        js_code=None if use_js else "",
        page_timeout=timeout * 1000,
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
    except Exception as exc:
        print(f"FETCH_ERROR: {url} — {exc}", file=sys.stderr)
        sys.exit(1)

    if not result.success:
        status = getattr(result, "status_code", "?")
        print(f"HTTP_{status}: {url}", file=sys.stderr)
        sys.exit(1)

    markdown = result.markdown or result.cleaned_html or ""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Saved: {output_path}", file=sys.stderr)
    else:
        print(markdown)


def main():
    check_crawl4ai()

    parser = argparse.ArgumentParser(description="Fetch a URL as clean Markdown")
    parser.add_argument("--url", required=True, help="URL to crawl")
    parser.add_argument("--output", default=None, help="Output .md file path")
    parser.add_argument("--no-js", action="store_true", help="Disable JS rendering (faster for static sites)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")
    args = parser.parse_args()

    asyncio.run(fetch(
        url=args.url,
        use_js=not args.no_js,
        timeout=args.timeout,
        output_path=args.output,
    ))


if __name__ == "__main__":
    main()
