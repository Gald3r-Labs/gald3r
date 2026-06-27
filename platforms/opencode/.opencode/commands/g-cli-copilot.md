---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-cli-copilot — GitHub Copilot CLI

Activate `g-skl-cli-copilot` for GitHub Copilot CLI operations.

Use when:
- Setting up gald3r workspace instructions for Copilot users
- Generating or regenerating `.github/copilot-instructions.md`
- Invoking `gh copilot suggest` or `gh copilot explain`
- Configuring Copilot in a gald3r project (Phase 1 compatible target)
- Understanding Copilot Phase 1 vs Phase 2 capabilities

## Actions

- **Generate instructions**: run `python .gald3r_sys/skills/g-skl-platform-copilot/scripts/generate_copilot_instructions.py`
- **Suggest command**: `gh copilot suggest --target {shell|git|gh} "{description}"`
- **Explain command**: `gh copilot explain "{command}"`
- **Status**: confirm `gh auth status` + Copilot subscription active

Read and follow `g-skl-cli-copilot/SKILL.md` for full reference.
