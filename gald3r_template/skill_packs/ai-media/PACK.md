# Pack: ai-media

AI video generation skills — Seedance 2.0 text/image-to-video and Higgsfield DoP cinematic image-to-video.

## What This Installs

- `skl-seedance` — Seedance 2.0 text-to-video and image-to-video via fal.ai, VolcEngine, or Replicate. GENERATE/STATUS/DOWNLOAD/NOTE/FULL operations.
- `skl-higgsfield` — Higgsfield DoP cinematic image-to-video. GENERATE/STATUS/DOWNLOAD/NOTE/FULL with NSFW handling. Requires input image.

## Prerequisites

**skl-seedance:** Set `FAL_KEY` (default) or `SEEDANCE_API_KEY` / `REPLICATE_API_TOKEN` + `SEEDANCE_PROVIDER`
**skl-higgsfield:** Set `HIGGSFIELD_KEY_ID` + `HIGGSFIELD_KEY_SECRET`

Both require `httpx`: `uv add httpx` or `pip install httpx`

## Install

```powershell
.\skill_packs\ai-media\install.ps1
.\skill_packs\ai-media\install.ps1 -ProjectRoot "C:\my-project"
```

## Uninstall

Delete these skill directories from your project's `.cursor/skills/`, `.claude/skills/`, etc.:
- `skl-seedance/`, `skl-higgsfield/`

## FILES

- `.cursor/skills/skl-seedance/SKILL.md`
- `.cursor/skills/skl-higgsfield/SKILL.md`
- `.claude/skills/skl-seedance/SKILL.md`
- `.claude/skills/skl-higgsfield/SKILL.md`
- `.agent/skills/skl-seedance/SKILL.md`
- `.agent/skills/skl-higgsfield/SKILL.md`
- `.codex/skills/skl-seedance/SKILL.md`
- `.codex/skills/skl-higgsfield/SKILL.md`
- `.opencode/skills/skl-seedance/SKILL.md`
- `.opencode/skills/skl-higgsfield/SKILL.md`
