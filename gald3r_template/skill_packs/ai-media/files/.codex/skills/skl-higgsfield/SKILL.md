---
name: skl-higgsfield
description: Higgsfield AI image-to-video (DoP cinematic motion) via the Higgsfield public API. Async submit → poll → download → vault note. No Docker, no MCP. Pure httpx. Stores in research/videos/.
---

# Higgsfield AI — Image-to-Video (DoP)

Higgsfield's DoP (Director of Photography) model generates cinematic motion videos from still images. Input is always an image (URL or local path). Output is a 5-second MP4.

## Prerequisites

Two environment variables required:

| Env Var | Description |
|---------|-------------|
| `HIGGSFIELD_KEY_ID` | API Key ID from https://platform.higgsfield.ai |
| `HIGGSFIELD_KEY_SECRET` | API Key Secret |

Combined form also accepted: `HIGGSFIELD_KEY="{key_id}:{key_secret}"`

Install httpx: `uv add httpx` or `pip install httpx`

## Pricing

| Model | Cost per generation |
|-------|---------------------|
| `higgsfield-ai/dop/preview` | $0.563 |
| `higgsfield-ai/dop/turbo` | $0.406 |
| `higgsfield-ai/dop/lite` | $0.125 |

Cost is charged per GENERATE call, regardless of outcome.

## Operation: GENERATE

Submit an image-to-video generation request.

**Required:** `image_url` OR `image_path` (fails fast if neither provided)

**Optional:** `prompt`, `motion_type`, `model` (default: `higgsfield-ai/dop/preview`), `seed`

**Returns:** `request_id` (string), `estimated_cost_usd` (float)

```python
import httpx, os, base64, json
from pathlib import Path

key_id = os.environ.get("HIGGSFIELD_KEY_ID", "")
key_secret = os.environ.get("HIGGSFIELD_KEY_SECRET", "")
if not key_id:
    combined = os.environ.get("HIGGSFIELD_KEY", "")
    key_id, key_secret = combined.split(":", 1)

token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

payload = {
    "image_url": "https://example.com/photo.jpg",
    "model": "higgsfield-ai/dop/preview",
    "prompt": "Camera slowly pulls back revealing the full scene"
}
r = httpx.post("https://api.higgsfield.ai/v1/generate", json=payload, headers=headers)
r.raise_for_status()
request_id = r.json()["request_id"]
```

## Operation: STATUS

Poll generation status by `request_id`.

**States:** `queued` | `in_progress` | `completed` | `failed` | `nsfw`

Both `failed` and `nsfw` are **terminal** — do not retry.

```python
r = httpx.get(f"https://api.higgsfield.ai/v1/status/{request_id}", headers=headers)
state = r.json()["status"]
```

Use exponential backoff: `2s, 4s, 8s, 16s, 32s, 32s…` with 300s wall-clock cap.

## Operation: DOWNLOAD

Fetch the MP4 from a `completed` job and save locally.

```python
from datetime import datetime
from pathlib import Path

r = httpx.get(f"https://api.higgsfield.ai/v1/result/{request_id}", headers=headers)
video_url = r.json()["output"]["video_url"]

slug = prompt[:40].lower().replace(" ", "_").replace("/", "") if prompt else request_id[:16]
filename = f"higgsfield_{datetime.now().strftime('%Y%m%d')}_{slug}.mp4"
out_path = Path("research/videos") / filename
out_path.parent.mkdir(parents=True, exist_ok=True)
with httpx.stream("GET", video_url) as stream:
    with open(out_path, "wb") as f:
        for chunk in stream.iter_bytes(): f.write(chunk)
```

## Operation: NOTE

Write an Obsidian-compatible vault note at `research/videos/{slug}.md`.

**Required frontmatter:**
```yaml
---
date: YYYY-MM-DD
type: video
source: higgsfield
model: higgsfield-ai/dop/preview
ingestion_type: ai-generated
title: "Higgsfield: {prompt[:60]}"
topics: [ai-video, higgsfield, generated]
tags: [video, higgsfield, generated, ai-video, dop, image-to-video]
analysis_depth: generation_only
prompt: "{full prompt}"
source_image: "{image_url or image_path}"
output_file: research/videos/{filename}
cost_usd: 0.563
created_date: YYYY-MM-DD
---
```

**NSFW handling:** If STATUS returns `nsfw`, write `research/videos/{slug}.nsfw.md` with the raw response JSON. Do NOT retry. Log to `vault/log.md` if it exists.

## Operation: FULL

Convenience operation: GENERATE → STATUS poll loop → DOWNLOAD → NOTE.

```
agent: run FULL with image_url="..." [prompt="..."] [model=higgsfield-ai/dop/lite]
```

Abort with nsfw.md written if NSFW state is returned. Print progress dots every 4s.

## Not In Scope

- Seedance / ByteDance models → use `skl-seedance`
- Kling video / Wan video → separate skills
- Text-to-video (Higgsfield requires an input image)

## Error Handling

| Error | Resolution |
|-------|-----------|
| 401 | Check `HIGGSFIELD_KEY_ID` / `HIGGSFIELD_KEY_SECRET` values |
| `nsfw` state | Content flagged — write `.nsfw.md` and stop |
| `failed` state | Check `r.json()["error_message"]`; usually image quality issue |
| Timeout >300s | Generation hung; check platform status at https://platform.higgsfield.ai |
