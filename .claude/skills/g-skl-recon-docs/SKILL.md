---
name: g-skl-recon-docs
description: Documentation URL ingestion with periodic revisit. Crawls URLs into research/platforms/, tracks staleness per _index.yaml, surfaces stale count at session start. Depends on g-skl-crawl (crawl4ai).
---
# g-recon-docs

**Scripts**: `.cursor/skills/g-skl-ingest-docs/scripts/`

**Activate for**: "ingest these docs", "add documentation URL", "refresh stale docs", "update platform docs", "crawl documentation site".

---

## Purpose

Periodically crawl documentation URLs and store them in `research/platforms/`. Unlike one-time URL ingestion, these entries track a `refresh_policy` (e.g. every 30 days) and surface a **stale count** at session start when any doc's `last_fetched` is past its deadline.

Depends on **g-skl-crawl** (crawl4ai). Run `@g-crawl SETUP` first.

---

## Clean Room Boundary

This capture skill may store source material in the vault for research, provenance, and later review. When captured content is used for `--deep`, `g-skl-res-deep`, or any adoption workflow, downstream outputs must be clean-room reverse specs: behavior-level summaries, interfaces, workflows, data shapes, constraints, and architectural patterns only. Do not copy source code, comments, docs prose, prompts, tests, or unique strings into generated gald3r artifacts except tiny attributed excerpts that are license-compatible and necessary for review. Record source URL/path, license when discoverable, capture date, and extraction limits so reviewers can separate source evidence from original gald3r specifications.

---

## Operation: INGEST_DOC

Add or update a documentation URL.

```bash
python .cursor/skills/g-skl-ingest-docs/scripts/ingest_doc.py \
  --url "https://docs.example.com" \
  --vault-path /path/to/vault \
  --name "ExampleDocs" \
  [--platform cursor]    # Obsidian platform tag; default: inferred from URL
  [--refresh-days 30]   # default: 30
  [--no-js]             # disable JS rendering for static sites
  [--force]             # re-fetch even if not yet stale
```

**What happens:**
1. Check `_index.yaml` — is the URL already registered and fresh? Skip unless `--force`.
2. Run `g-skl-crawl` FETCH to get clean Markdown
3. Write vault note to `research/platforms/{slugified-name}.md`
4. Update / create `research/platforms/_index.yaml` entry: `{url, name, last_fetched, refresh_days, status}`
5. Append to `vault/log.md`
6. After **REFRESH_STALE** completes any successful fetches, `refresh_stale_docs.py` runs `scripts/gen_vault_moc.py --auto` when available (MOC / graph hubs).

---

## Operation: REFRESH_STALE

Scan `_index.yaml` and re-fetch all docs past their `refresh_days` deadline.

```bash
python .cursor/skills/g-skl-ingest-docs/scripts/refresh_stale_docs.py \
  --vault-path /path/to/vault \
  [--dry-run]   # list stale URLs without fetching
  [--no-js]
```

**Output:**
- Re-fetches each stale doc using `crawl_url.py`
- Updates `_index.yaml` with new `last_fetched` timestamp
- Prints: `Refreshed N / M stale docs`

---

## `_index.yaml` Schema (per entry)

```yaml
- url: "https://docs.example.com"
  name: "ExampleDocs"
  slug: "exampledocs"
  last_fetched: "2026-04-06"
  refresh_days: 30
  next_refresh: "2026-05-06"
  status: fresh          # fresh | stale | error
  vault_path: "research/platforms/exampledocs.md"
```

---

## Session Hook Integration

During session start (`g-rl-25`), surface stale count:

```
📚 Vault Docs: 12 registered | 3 stale (run @g-ingest-docs REFRESH_STALE)
```

The session start hook calls:
```bash
python .cursor/skills/g-skl-ingest-docs/scripts/refresh_stale_docs.py \
  --vault-path {vault_path} --dry-run --count-only
```

---

## Vault Note Schema

```yaml
---
date: 2026-04-06
type: platform_doc
ingestion_type: periodic
source: https://docs.example.com
title: "ExampleDocs"
tags: [platform-doc, cursor, agents]
refresh_policy: every_30_days
last_fetched: 2026-04-06
source_volatility: living_document
analysis_depth: full_text
---
{clean Markdown content from crawl4ai}
```

---

## Obsidian compatibility (see also)

All notes written by this skill must conform to **`.gald3r/vault/VAULT_OBSIDIAN_STANDARD.md`** (or the copy at `{vault_location}`): §1 frontmatter, §3 tags (`platform-doc` + platform slug + path-derived topics), UTF-8 **no BOM**.

Bulk / scheduled workflows: use **`g-platform-crawl`** for crawl4ai-backed batch documentation crawls; after large crawls run `scripts/gen_vault_moc.py` as documented there.

