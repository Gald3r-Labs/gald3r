---
name: skl-seedance
description: Seedance 2.0 AI video generation — text-to-video and image-to-video via VolcEngine, fal.ai, or Replicate. Async submit → poll → download → vault note. No Docker, no MCP. Stores in research/videos/.
---

# Seedance 2.0 AI Video Generation

Seedance 2.0 (by ByteDance) is a state-of-the-art video generation model available via multiple API providers. This skill covers the full generation workflow: submit request → poll for completion → download result → write vault note.

## Prerequisites

Set one of the following environment variables based on your chosen provider:

| Provider | Env Var | How to Get |
|----------|---------|-----------|
| fal.ai (default) | `FAL_KEY` | https://fal.ai/dashboard/keys |
| VolcEngine | `SEEDANCE_API_KEY` | https://www.volcengine.com/product/visual-generation |
| Replicate | `REPLICATE_API_TOKEN` | https://replicate.com/account/api-tokens |

Set provider: `SEEDANCE_PROVIDER=fal` (default) | `volcengine` | `replicate`

## Operation: GENERATE

Submit a text-to-video or image-to-video request.

**Required params:**
- `prompt` — text description of the video
- `model` — model ID (default: `fal-ai/seedance-1-lite` for fal, adjust for other providers)
- `duration` — video length in seconds (e.g., `5`)
- `aspect_ratio` — `16:9` | `9:16` | `1:1`

**Optional params:**
- `image_url` — seed image URL for image-to-video mode
- `image_path` — local image path (fal provider uploads automatically)
- `seed` — integer for reproducibility

**Returns:** `task_id` (string), `estimated_cost_usd` (float)

```python
# httpx example (fal.ai provider)
import httpx, os

headers = {"Authorization": f"Key {os.environ['FAL_KEY']}", "Content-Type": "application/json"}
payload = {
    "prompt": "A serene mountain lake at sunrise, timelapse",
    "duration": 5,
    "aspect_ratio": "16:9"
}
r = httpx.post("https://queue.fal.run/fal-ai/seedance-1-lite", json=payload, headers=headers)
task_id = r.json()["request_id"]
```

## Operation: STATUS

Poll generation status by `task_id`.

**States:** `IN_QUEUE` | `IN_PROGRESS` | `COMPLETED` | `FAILED`

```python
r = httpx.get(f"https://queue.fal.run/fal-ai/seedance-1-lite/requests/{task_id}/status",
              headers=headers)
state = r.json()["status"]
```

Use exponential backoff: 2s, 4s, 8s, 16s, 32s, 32s… with a 300s wall-clock cap.

## Operation: DOWNLOAD

Fetch the video from a COMPLETED job and save locally.

```python
r = httpx.get(f"https://queue.fal.run/fal-ai/seedance-1-lite/requests/{task_id}",
              headers=headers)
video_url = r.json()["video"]["url"]

from datetime import datetime
from pathlib import Path
slug = prompt[:40].lower().replace(" ", "_").replace("/", "")
filename = f"seedance_{datetime.now().strftime('%Y%m%d')}_{slug}.mp4"
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
source: seedance
model: seedance-2.0
ingestion_type: ai-generated
title: "Prompt: {prompt[:60]}"
topics: [ai-video, seedance, generated]
tags: [video, seedance, generated, ai-video]
analysis_depth: generation_only
prompt: "{full prompt}"
duration: 5
aspect_ratio: "16:9"
output_file: research/videos/{filename}
provider: fal
created_date: YYYY-MM-DD
---
```

## Operation: FULL

Convenience operation chaining GENERATE → STATUS (poll loop) → DOWNLOAD → NOTE.

```
agent: run FULL with prompt="..." [duration=5] [aspect_ratio=16:9] [image_url=...]
```

Prints progress: `⏳ Submitted task_id=xyz`, `🔄 Polling… (12s)`, `✅ Downloaded: research/videos/...`

## Not In Scope

- Kling video models (use a separate skl-kling skill)
- Wan video, Mochi, CogVideoX (separate providers)
- Image generation (not video)

## Error Handling

| Error | Resolution |
|-------|-----------|
| 401 Unauthorized | Check `FAL_KEY` / `SEEDANCE_API_KEY` is set |
| FAILED status | Check `r.json()["error"]`; usually invalid prompt or image format |
| Timeout >300s | Increase poll budget or retry with shorter duration |
| 429 Rate limit | Wait 60s and retry; fal.ai has per-minute limits |
