---
name: g-skl-comfyui
description: ComfyUI V5 agent integration for local GPU image/video generation. Install, launch, manage workflows, and run AnimateDiff/SDXL pipelines via the ComfyUI REST API. Local GPU path — zero cloud costs. Use for example_desktop theme pack animation or any offline image/video generation.
token_budget: medium
subsystem_memberships: [UI_AND_OUTPUT]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
