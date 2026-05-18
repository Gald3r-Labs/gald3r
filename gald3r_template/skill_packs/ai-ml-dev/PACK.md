# Pack: ai-ml-dev

AI/ML development, cloud GPU training, and Manim mathematical animation.

## What This Installs

- `ai-ml-development` — Model selection, training loops, evaluation, fine-tuning, RLHF, RAG, MLOps
- `cloud-gpu-training` — RunPod/Lambda/Vast.ai; SCP workflow, batch sizing, cost estimates, checkpointing
- `manim-animation` — 3Blue1Brown-style math animations; scenes, LaTeX, graphs, algorithm demos in Python

## Prerequisites

- For `cloud-gpu-training`: Hugging Face account + API token (optional, for HF Jobs)
- For `manim-animation`: `pip install manim` + ffmpeg

## Install

```powershell
.\skill_packs\ai-ml-dev\install.ps1
.\skill_packs\ai-ml-dev\install.ps1 -ProjectRoot "C:\my-project"
```

## Uninstall

Delete these skill directories from your project's `.cursor/skills/`, `.agent/skills/`, etc.:
- `ai-ml-development/`, `cloud-gpu-training/`, `manim-animation/`

## FILES

- `.cursor/skills/ai-ml-development/SKILL.md`
- `.cursor/skills/cloud-gpu-training/SKILL.md`
- `.cursor/skills/manim-animation/SKILL.md`
- `.agent/skills/ai-ml-development/SKILL.md`
- `.agent/skills/cloud-gpu-training/SKILL.md`
- `.agent/skills/manim-animation/SKILL.md`
- `.claude/skills/ai-ml-development/SKILL.md`
- `.claude/skills/cloud-gpu-training/SKILL.md`
- `.claude/skills/manim-animation/SKILL.md`
- `.codex/skills/ai-ml-development/SKILL.md`
- `.codex/skills/cloud-gpu-training/SKILL.md`
- `.codex/skills/manim-animation/SKILL.md`
- `.opencode/skills/ai-ml-development/SKILL.md`
- `.opencode/skills/cloud-gpu-training/SKILL.md`
- `.opencode/skills/manim-animation/SKILL.md`
