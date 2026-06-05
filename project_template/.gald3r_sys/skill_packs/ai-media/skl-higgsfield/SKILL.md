---
name: skl-higgsfield
description: Higgsfield AI image-to-video (DoP cinematic motion) via the Higgsfield public API. Async submit → poll → download → vault note. No Docker, no MCP. Pure httpx. Stores in research/videos/.
skill_group: "ai-media"
skill_category: "AI Image & Video Generation"
---
# Higgsfield MCP

One connector, 30+ models. Subscription-billed in credits — no per-provider API keys.

## When to use this skill

Only use this skill if the user **already pays for a Higgsfield subscription**. The whole value is access to 30+ models behind one auth, billed against credits they're already paying for. Don't push a non-subscriber to subscribe for one project.

## Installation

Requires a Higgsfield subscription (credits are consumed per generation — see cost table below).

**Agent-guided setup (runs automatically on first use):**

1. **Already configured?**
   Check `.cursor/mcp.json` (Cursor) or run `/mcp` (Claude Code) for a `higgsfield` entry.
   If present and `select_workspace` is reachable → skip, proceed.

2. **MCP entry missing — wire it:**
   - **Cursor**: add to `.cursor/mcp.json`:
     ```json
     { "higgsfield": { "type": "http", "url": "https://mcp.higgsfield.ai/mcp" } }
     ```
     Then open Cursor Settings → MCP and complete OAuth with your Higgsfield account.
   - **Claude Code**: run in terminal, then complete OAuth in the browser that opens:
     ```
     claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp
     ```
     Then run `/mcp` in your session.

3. **After connecting — mandatory**: call `select_workspace` once per session. Generation calls fail silently without it.

> **Cost gate**: Before any `generate_image` or `generate_video` call, quote the estimated credit cost and current balance. Wait for explicit "go". See [ALWAYS quote credit cost](#always-quote-credit-cost-before-generating) below.

**Heads-up:** MCP tools may not appear after a fresh install — restart Claude Code / Cursor if the server shows connected but no tools are visible.

## Three spokes

The skill does three things — keep it scoped to these:

1. **Explore models** — what's available, what role each model accepts
2. **Generate image** — single or batched
3. **Generate video** — including image→video chains

## ALWAYS quote credit cost before generating

**Non-negotiable.** Before any `generate_image` or `generate_video` call, quote:

- Model + settings
- **Estimated credit cost** (use the table below)
- Current `balance`
- Balance after the call

Wait for explicit "go" before firing. Credits ≠ free, and silent burn is the #1 way to ruin trust. Auto mode does not override this.

## Cost table (measured, not from docs)

`models_explore` does NOT return credit costs — they're not in the API. Use this baked table:

| Model | Settings | Credits |
|---|---|---|
| `gpt_image_2` | 2K medium | ~3 |
| `nano_banana_2` | 2K | ~11 |
| `seedance_1_5` | 480p, 4s | ~2.4 |
| `seedance_1_5` | 480p, 12s | ~7.2 |
| Video at higher tiers | — | TBD (measure first run) |

**Numbers will drift.** Verify in the Higgsfield dashboard if a run feels off. Update this table when you measure new ones.

## Plan-tier silently gates models

Higher-end models (e.g. `seedance_2_0`) are blocked on Starter and return a generic "Something went wrong" — no helpful error. If a model errors mysteriously, suspect plan gating before debugging the prompt. Suggest checking `balance` to infer the user's tier.

## Workflow mechanics

**Upload is 3 steps**, not one. Wrap as a single helper if calling repeatedly:

1. `media_upload` → returns a presigned PUT URL + `media_id`
2. `curl -X PUT` the file bytes to that URL
3. `media_confirm({ media_id })` → marks it ready

**Generation is async:**

1. Call `generate_image` or `generate_video` → returns `job_id`
2. Poll `job_status({ job_id, sync: true })` — usually resolves in 1–2 polls (~10–20s for images, longer for video)

**Result fields:** always pull `rawUrl` (PNG / source). `minUrl` is just the webp preview.

**One ref, many gens** — an uploaded `media_id` survives the session. Reuse it across calls instead of re-uploading.

**Parallel jobs work fine** — fire multiple `generate_image` calls and poll independently.

## Reference passing

Schema is `medias: [{ value, role }]` (not `reference_images`). `value` accepts three forms:

- **`media_id`** — from `media_upload` / `media_confirm`
- **`job_id`** — output of a prior generation, used as input to the next. **Killer feature for image→video chains** — generate a still, feed its `job_id` straight into `generate_video` without re-uploading.
- **`https://` URL** — any public image URL

## Role taxonomy varies per model

Always run `models_explore action=get` for a model before crafting the call. Roles are not consistent:

| Model | Accepted roles |
|---|---|
| Seedance 1.5 | `start_image`, `end_image` |
| Seedance 2.0 | full set (`image`, `start_image`, `end_image`, `video`, `audio`) |
| Kling 3.0 | `start_image` only |
| Nano Banana Pro / GPT Image 2 | `image` |

Pass the wrong role and the call rejects.

## Seedance 1.5 duration trap

If you omit `duration`, Seedance 1.5 silently defaults to **12 seconds** — 3× the cost of a 4s clip. **Always pass `duration` explicitly.**

## Pricing footnotes

- **Plus plan:** $39/month, 1000 credits — sweet spot for ad workloads
- **Top-up packs** ($5 / 100 credits) **expire in 90 days** — don't stockpile
- Verify exact per-call credit cost in the Higgsfield dashboard before committing to a workflow swap

## Animation Theme Pack Generation

Cloud-based animation content pipeline for example_desktop theme packs using Higgsfield models. Zero local GPU required — uses Seedance 2.0, Kling 2.0, and other cloud models.

### Creative Pipeline (4 stages)

```
concept prompt
    ↓
style frames (image models)    ← Nano Banana Pro, GPT Image 2, Flux
    ↓
animation clips (video models) ← Seedance 2.0, Kling 2.0, Hailuo 02
    ↓
brand system + theme pack
```

**Stage 1 — Concept & Style Frames:**
- Use `generate_image` with `nano_banana_2` or `gpt_image_2` to create 4–6 style reference frames per theme
- Prompts should establish: color palette, character mood, environment
- Save style frame `job_id` values — they become the visual anchors for all video calls

**Stage 2 — Animation Clips:**
- Feed style frame `job_id` directly into `generate_video` as `medias: [{value: job_id, role: "image"}]`
- **Seedance 2.0**: full multi-role support, best quality. Always pass `duration: 4` (prevents 12s default)
- **Kling 2.0**: `start_image` role only, excellent character consistency across theme clips
- **Hailuo 02**: fastest, good for background/ambient loops

**Stage 3 — Context Retention:**
- Track hex color codes and style descriptors from Stage 1 across all Stage 2 calls
- Use consistent seed values across a theme pack for visual coherence
- Store all `job_id` and `rawUrl` values in a per-theme manifest

**Output Convention:**
```
<workspace>\example_desktop\src-tauri\maestro2\themes\{theme_name}\
    style_frames/        ← PNG stills (rawUrl downloads)
    animation_clips/     ← video files
    theme_manifest.json  ← job IDs, model settings, hex palette, prompts used
```

### 3 Example Theme Styles

**Norse/Viking:**
- Style frame prompt: `"A Norse warrior hall at dusk, mead tables, torchlight, ash wood beams, muted gold and charcoal color palette, cinematic, dramatic shadows"`
- Animation prompt: `"Norse warrior drinking from a horn, firelight flickering, slow ambient motion, 4 seconds"`
- Model: Seedance 2.0 (character consistency), duration 4s
- Palette: `#8B7355` (ash), `#2C2C2C` (charcoal), `#B8860B` (muted gold)

**Cyberpunk:**
- Style frame prompt: `"Tokyo backstreet, holographic ad panels, rain on asphalt, neon cyan and magenta, corporate logos in kanji, depth fog"`
- Animation prompt: `"Rain falling on a neon-lit alley, holograms flickering, ambient city loop, 4 seconds"`
- Model: Kling 2.0 (sharp neon details), start_image from style frame
- Palette: `#00FFFF` (cyan), `#FF00FF` (magenta), `#1A1A2E` (dark navy)

**Minimal/Silicon Valley:**
- Style frame prompt: `"Clean open-plan tech office, morning light through floor-to-ceiling windows, white desks, succulents, minimal nordic design"`
- Animation prompt: `"Sunlight slowly shifting through a clean tech office, gentle ambient motion, 4 seconds"`
- Model: Hailuo 02 (smooth ambient loops), or Seedance 2.0 if character needed
- Palette: `#F5F5F5` (off-white), `#4A90D9` (tech blue), `#2D2D2D` (charcoal)

### Cost Guard for Theme Packs

Before starting a full theme pack:
- 6 style frames × 3 credits (Nano Banana Pro) = ~18 credits
- 6 animation clips × Seedance 2.0 @ 4s = ~14.4 credits per theme
- **Full theme pack estimate: ~33 credits (~$1.65 on Plus plan)**
- Always quote total before generating; check balance covers full pack

### API Key Setup

If Higgsfield MCP not configured, follow the Installation section above. Key note: `select_workspace` must be called once per session before any generation calls succeed.

---

## Failure rules

- **Don't silently fall back from ref-to-video to text-to-video** — losing the visual anchor defeats the workflow. Surface the failure.
- **Don't retry the same input on the same model when a content-policy check trips** — propose changing the input or model.
- **If the MCP errors out**, check `/mcp` to confirm the connection is still live. Subscription lapses break auth.

## Models exposed

30+ behind one URL. Highlights:

| Category | Models |
|---|---|
| Image | Nano Banana Pro, GPT Image 2, Flux, Seedream |
| Video | Seedance 2.0, Sora 2, Veo, Kling, Hailuo |
| Higgsfield exclusives | Soul (character consistency), Cinema Studio |

**Limits:** images up to 4K, video up to 15 sec.
