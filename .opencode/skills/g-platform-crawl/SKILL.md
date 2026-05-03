---
name: g-platform-crawl
description: Crawl platform documentation and web docs with crawl4ai; write .platforms/ and vault markdown with frontmatter. For platform docs, knowledge refresh, web ingest.
---
# g-platform-crawl

**Activate for**: "crawl platform docs", "ingest documentation site", "fetch latest AI platform docs", "update platform knowledge", bulk doc crawling, crawl4ai batch jobs.

---

## Purpose

Crawl AI platform documentation sites (Anthropic, OpenAI, Google Gemini, OpenCode, Cursor) and write Obsidian-compatible vault notes to `research/platforms/{platform-name}/`. This skill uses **crawl4ai only** via `g-skl-crawl` for both one-off refreshes and bulk documentation crawls.

If a workflow needs web extraction, route it through `g-skl-crawl`, `g-skl-recon-docs`, `g-skl-recon-url`, or the crawl4ai-backed MCP URL/platform-doc tools.

---

## Vault Note Schema

All platform doc notes written by this skill use:

```yaml
---
date: {YYYY-MM-DD}
type: platform_doc
ingestion_type: crawl4ai
source: {source-url}
title: "{page-title}"
tags: [platform-doc, {platform-name}]
refresh_policy: weekly
refresh_after: {YYYY-MM-DD}
expires_after: {YYYY-MM-DD}
source_volatility: high
project_id: null
---

# {title}

> **Source**: [{source-url}]({source-url})
> Ingested: {YYYY-MM-DD} via crawl4ai

{page content in clean Markdown}
```

**Tag derivation rules:**
```python
tags = ["platform-doc", platform_name]  # minimum required
# Additional topic tags from URL path:
# /docs/agents  -> "agents"
# /docs/tool-use -> "tool-use"
# /api/models    -> "api", "models"
# /docs/mcp      -> "mcp"
```

**Encoding**: Always write `encoding="utf-8"` (no BOM). Never use `utf-8-sig` for new notes.

---

## Crawl Flow

Use `g-skl-crawl` as the shared primitive:

```bash
python .cursor/skills/g-skl-crawl/scripts/crawl_url.py \
  --url "https://docs.example.com" \
  --output research/platforms/example.md
```

For bulk crawls, feed URLs through the `g-skl-crawl` batch script or a platform-doc wrapper that calls the same crawl4ai primitive. Keep crawl state in the platform docs index so stale-doc refreshes can resume safely.

---

## After Bulk Crawl: MOC Generation

After any bulk platform crawl (10+ files), regenerate the directory MOC:

```bash
python scripts/gen_vault_moc.py \
  --vault-path {vault_path} \
  --path {vault_path}/research/platforms/{platform-name}
```

This creates/updates `_INDEX.md` with `[[wikilinks]]` to all notes, forming the hub-and-spoke structure in Obsidian's graph view.

---

## Platform Directory Map

| Platform | Vault path | crawl4ai source |
|----------|------------|-----------------|
| Anthropic/Claude | `research/platforms/claude-code/` | docs.anthropic.com |
| OpenAI | `research/platforms/openai/` | platform.openai.com |
| Google Gemini | `research/platforms/gemini/` | ai.google.dev |
| Cursor | `research/platforms/cursor/` | docs.cursor.com |
| OpenCode | `research/platforms/opencode/` | opencode.ai/docs |

---

## Obsidian Compatibility

All notes written by this skill must conform to **VAULT_OBSIDIAN_STANDARD.md** (§2 type registry, §3 tag taxonomy).

Required fields: `type: platform_doc`, `tags: [platform-doc, {platform-name}, ...]`, `title:`, `date:`.  
Encoding: UTF-8 without BOM.  
Body: starts with H1 heading, then source attribution block.  
See also: `scripts/gen_vault_moc.py`, `scripts/normalize_vault_tags.py`.
