---
name: higgsfield
description: One MCP, 30+ image and video models. Use this skill when the user wants to generate images or videos via Higgsfield (Seedance 2.0, Sora 2, Veo, Kling, Nano Banana Pro, GPT Image 2, Flux, Hailuo, Soul, Cinema Studio, etc.) without juggling per-provider API keys. Triggers on "higgsfield", "higgsfield mcp", "use higgsfield", or any image/video generation request when the user already has a Higgsfield subscription.
---

# Higgsfield MCP

One connector, 30+ models. Subscription-billed in credits — no per-provider API keys.

## When to use this skill

Only use this skill if the user **already pays for a Higgsfield subscription**. The whole value is access to 30+ models behind one auth, billed against credits they're already paying for. Don't push a non-subscriber to subscribe for one project.

## Three spokes

The skill does three things — keep it scoped to these:

1. **Explore models** — what's available, what role each model accepts
2. **Generate image** — single or batched
3. **Generate video** — including image→video chains

## Install

**Two ways to connect.** Both end at the same place: an authenticated MCP your session can call.

**Terminal (Claude Code):**

```
claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp
```

Then run `/mcp` in your session and complete OAuth with the Higgsfield account that owns the subscription.

**Claude Desktop app:**

Settings → Connectors → Add custom connector → paste `https://mcp.higgsfield.ai/mcp` → sign in.

**After auth — mandatory step:**

```
select_workspace
```

Generation calls fail silently until a workspace is selected. Always run this once at the start of a session.

**Heads-up:** MCP tools may not appear in the running session after a fresh install — restart Claude Code / Desktop if `/mcp` shows higgsfield connected but no tools are visible.

No API keys to manage. No `.env`. The MCP handles auth.

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
