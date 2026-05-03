---
name: g-yt-video-analysis
description: MCP or full-pipeline video analysis — vault notes must match Obsidian standard. For local yt-dlp transcripts only, use g-skl-ingest-youtube.
---
# g-yt-video-analysis

**Activate for**: `video_analyze`, MCP video pipeline, YouTube notes with vision/frames + transcript (not plain yt-dlp).

---

## Relationship to g-skl-ingest-youtube

| Path | Skill | When |
|------|-------|------|
| Transcript-only, no MCP | **g-skl-ingest-youtube** | Default local capture |
| MCP / vision / batch | **g-yt-video-analysis** (this doc) | Tool output contract |

---

## Vault note template (required)

```yaml
---
date: YYYY-MM-DD
type: video
ingestion_type: video-analyzer
source: https://www.youtube.com/watch?v=VIDEO_ID
title: "Video Title"
tags: [video]
---

# {title}

> **Channel**: … | **URL**: [watch](https://…)

## Summary

{2–3 sentences from analysis}

## Key Points

- …
- …

## Transcript

{full transcript or link to collapsed block}
```

**Encoding:** UTF-8 without BOM (`encoding="utf-8"` in Python).

---

## See also

- **VAULT_OBSIDIAN_STANDARD.md** — §2 type registry (`video`), §3 tags, §5 body layout
- **g-skl-ingest-youtube** — canonical local script paths and `ingestion_type: one_shot` variant
- **scripts/gen_vault_moc.py** — refresh `research/videos/_INDEX.md` after adding notes
