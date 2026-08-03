---
name: g-skl-yt-video-analysis
description: MCP or full-pipeline video analysis — vault notes must match Obsidian standard. For local yt-dlp transcripts only, use g-skl-ingest-youtube.
token_budget: medium
subsystem_memberships: [VAULT_AND_RESEARCH]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# g-skl-yt-video-analysis

**Activate for**: `video_analyze`, MCP video pipeline, YouTube notes with vision/frames + transcript (not plain yt-dlp).

---

## Relationship to g-skl-ingest-youtube

| Path | Skill | When |
|------|-------|------|
| Transcript-only, no MCP | **g-skl-ingest-youtube** | Default local capture |
| MCP / vision / batch | **g-skl-yt-video-analysis** (this doc) | Tool output contract |

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
