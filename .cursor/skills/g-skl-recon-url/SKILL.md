---
name: g-skl-recon-url
description: One-time URL ingestion into vault research/articles/. No revisit scheduling. Dedup by source URL in _index.yaml. Depends on g-skl-crawl (crawl4ai).
---
# g-recon-url

**Scripts**: `.cursor/skills/g-skl-ingest-url/scripts/`

**Activate for**: "save this page to vault", "ingest this article", "capture this URL", "add to research", any URL to capture once.

---

## Purpose

One-shot capture of a URL into `research/articles/`. Unlike `g-skl-ingest-docs`, there is no refresh schedule — the content is captured once as a snapshot. Suitable for blog posts, papers, news articles, forum threads, and any page you don't expect to revisit.

Depends on **g-skl-crawl**. Run `@g-crawl SETUP` first if crawl4ai is not installed.

---

## Operation: INGEST_URL

Ingest a single URL.

```bash
python .cursor/skills/g-skl-ingest-url/scripts/ingest_url.py \
  --url "https://example.com/article" \
  --vault-path /path/to/vault \
  [--title "Optional Title Override"] \
  [--topics "topic1,topic2"]
  [--no-js]
  [--force]   # re-ingest even if URL already in _index.yaml
```

**What happens:**
1. Check `_index.yaml` — already captured? Skip unless `--force`.
2. Crawl URL via `g-skl-crawl` FETCH
3. Write vault note to `research/articles/{YYYY-MM-DD}_{slugified-url}.md`
4. Append entry to `research/articles/_index.yaml`
5. Append to `vault/log.md`

---

## Operation: INGEST_URL_BATCH

Ingest a list of URLs from a text file.

```bash
python .cursor/skills/g-skl-ingest-url/scripts/ingest_url.py \
  --urls-file path/to/urls.txt \
  --vault-path /path/to/vault \
  [--no-js] [--resume]
```

**urls.txt format** — one URL per line, blank lines and `#` comments ignored.

---

## Deduplication

Before fetching, the script checks `research/articles/_index.yaml` for a matching `url:` field. If found and `--force` is not set, the fetch is skipped with:
```
DUPLICATE: https://... (captured 2026-03-12) — skip (use --force to re-capture)
```

---

## Vault Note Schema

```yaml
---
date: 2026-04-06
type: article
ingestion_type: one_shot
source: https://example.com/article
title: "Article Title"
tags: [article]
refresh_policy: manual
source_volatility: snapshot
analysis_depth: full_text
---
{clean Markdown content from crawl4ai}
```

> **Obsidian Compatibility**: All notes written by this skill must conform to **VAULT_OBSIDIAN_STANDARD.md** (§2 type registry, §3 tag taxonomy). Required fields: `type: article`, `tags: [article, ...]`, `title:`, `date:`. Encoding: UTF-8 without BOM.

