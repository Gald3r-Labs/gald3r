# g-recon-url

One-time URL capture into vault `research/articles/`.

Activates **g-skl-recon-url** → CAPTURE or CAPTURE_BATCH operation.

> **Replaces**: `@g-ingest-url` (deprecated alias — prints warning, then calls this)

## Usage

```
@g-recon-url https://example.com/article
@g-recon-url https://example.com/article --title "Custom Title" --topics "ai,benchmarks"
@g-recon-url --urls-file my_urls.txt
@g-recon-url https://example.com/article --deep   # capture + deep analysis report
```

## What it does

1. Checks if URL is already captured (dedup via `_index.yaml`) — skips duplicates unless `--force`
2. Crawls URL via `g-skl-crawl` (crawl4ai) → clean Markdown
3. Writes vault note to `research/articles/{date}_{slug}.md`
4. Registers URL in `research/articles/_index.yaml`
5. Updates `vault/log.md`

## --deep flag

After capturing, runs deep analysis and writes a recon report to `vault/research/recon/{slug}/`.
Equivalent to running `@g-res-deep` on the captured content.

## Notes

- No revisit schedule — these are one-shot snapshots
- Use `@g-recon-docs` for documentation that should be refreshed periodically
- Use `--force` to re-capture an already-indexed URL
- Requires `g-skl-crawl` (crawl4ai) — run `@g-crawl SETUP` first

## Prerequisites

```bash
pip install crawl4ai pyyaml
python -m playwright install --with-deps chromium
```
