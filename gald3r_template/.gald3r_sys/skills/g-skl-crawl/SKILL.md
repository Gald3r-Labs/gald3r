---
name: g-skl-crawl
description: Native crawl4ai web crawler — FETCH, BATCH, and SETUP operations. Produces clean LLM-optimized Markdown from any URL. No Docker, no MCP required. Shared crawl primitive used by g-skl-ingest-docs, g-skl-ingest-url, and g-skl-harvest.
---
# g-crawl

**Scripts**: `.cursor/skills/g-skl-crawl/scripts/`

**Activate for**: "crawl this URL", "fetch page", "get docs from URL", "bulk fetch", "install crawl4ai", "set up crawler", any request to retrieve web content as Markdown.

---

## Purpose

This skill wraps [crawl4ai](https://github.com/unclecode/crawl4ai) as a plain Python subprocess — no Docker, no MCP server. It is the **shared crawl primitive** for vault ingestion tasks. It only fetches and converts — it does not write to the vault. Vault write logic lives in the calling skill.

---

## Setup Check

Before any FETCH or BATCH, confirm the environment is ready:

```bash
python -m crawl4ai --version  2>/dev/null || echo "NOT INSTALLED"
```

If not installed, run **SETUP** first.

---

## Operation: SETUP

Install crawl4ai and its Playwright browser dependency.

```bash
pip install crawl4ai
python -m playwright install --with-deps chromium
```

Verify:
```bash
python -m crawl4ai --version
```

If `pip` is unavailable, suggest `uv pip install crawl4ai` (per C-004).

---

## Operation: FETCH

Fetch a single URL and return clean Markdown.

**Invoke the script directly:**

```bash
python .cursor/skills/g-skl-crawl/scripts/crawl_url.py \
  --url "https://example.com/docs" \
  [--output path/to/output.md] \
  [--no-js]          # disable JS rendering (faster, works for static pages)
  [--timeout 30]     # seconds, default 30
```

**What you get:**
- Clean Markdown with boilerplate stripped (nav, ads, footers)
- `<output>.md` if `--output` is given; otherwise printed to stdout
- Non-zero exit code on failure with a descriptive error message

**When to use `--no-js`:** Static documentation sites (GitHub README, plain HTML docs) don't need JS rendering. SPAs (React, Vue, Angular docs) do.

---

## Operation: BATCH

Crawl a list of URLs and write one `.md` file per URL.

```bash
python .cursor/skills/g-skl-crawl/scripts/crawl_batch.py \
  --urls-file path/to/urls.txt \
  --output-dir path/to/output/ \
  [--no-js]
  [--resume]   # skip URLs already in crawl_batch_state.json
```

**urls.txt format** — one URL per line, blank lines and `#` comments ignored:
```
https://docs.example.com/api
https://docs.example.com/guide
# https://skipped.com
```

**Output:**
- One `{slugified-url}.md` per URL in `--output-dir`
- `crawl_batch_state.json` tracking `{url: status}` — use `--resume` to skip completed URLs

---

## Configuration Defaults

| Setting | Default | Override |
|---|---|---|
| JS rendering | Enabled | `--no-js` flag |
| Timeout | 30 seconds | `--timeout N` |
| Word count threshold | 10 (filters boilerplate) | hardcoded in script |
| External links | Excluded | hardcoded in script |

---

## Error Handling

| Error | Script behavior |
|---|---|
| Network error / DNS failure | Exit 1, stderr: "FETCH_ERROR: {url} — {message}" |
| Non-200 status | Exit 1, stderr: "HTTP_{code}: {url}" |
| JS timeout | Exit 1, stderr: "JS_TIMEOUT: {url} — try --no-js" |
| crawl4ai not installed | Exit 2, stderr: "SETUP_REQUIRED: run g-crawl SETUP" |

---

## Not In Scope

- This skill does NOT write to the vault
- This skill does NOT do authentication flows beyond static headers
- Use `g-skl-ingest-docs` for docs with revisit logic
- Use `g-skl-ingest-url` for one-time URL capture
- Use `g-skl-harvest` for idea extraction from repos/articles
