# g-recon-yt

Capture a YouTube video transcript into the vault knowledge store.

Activates **g-skl-recon-yt** → CAPTURE operation.

> **Replaces**: `@g-ingest-youtube` (deprecated alias — prints warning, then calls this)

## Usage

```
@g-recon-yt https://www.youtube.com/watch?v=VIDEO_ID
@g-recon-yt https://www.youtube.com/watch?v=VIDEO_ID --deep   # capture + deep analysis
```

## What it does

1. Fetches video metadata (title, channel, duration, upload date) via yt-dlp
2. Downloads transcript/captions (manual → auto-generated → translated, in priority order)
3. Parses VTT captions to clean text (no timestamps, deduplicated rolling lines)
4. Generates summary and key points from transcript
5. Writes vault note to `research/videos/` with `analysis_depth: transcript_only`
6. Updates `vault/log.md` and `vault/_index.yaml`

## --deep flag

After capturing, runs deep analysis of the transcript and writes a recon report to
`vault/research/recon/{slug}/`. Equivalent to running `@g-res-deep` on the video note.

## Clean Room Boundary

These commands support clean-room research and reverse-spec work. Capture/recon may observe and summarize source behavior, interfaces, workflows, data shapes, and architectural patterns; generated gald3r artifacts must use original wording and local architecture terms, not copied source code, docs prose, prompts, tests, or unique strings. Keep source URL, license, and capture provenance in recon notes; treat source file paths as traceability, not implementation instructions. Adoption requires human approval through `@g-res-review` / `@g-res-apply`.

## Notes

- No video download — transcript only
- No Docker, no MCP required (uses yt-dlp locally)
- Notes include `analysis_depth: transcript_only` — a future task can upgrade to full vision analysis
- If no captions are available, creates a metadata-only note with a warning

## Check setup

```
@g-recon-yt --check-setup
```

## Prerequisites

```bash
pip install yt-dlp
```
