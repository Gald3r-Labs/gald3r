# TRAE (ByteDance) + gald3r

**Tier 1 — Fully Supported**

[TRAE](https://www.trae.ai) is ByteDance's AI-native IDE with SOLO autonomous agent mode. It uses the **Agent Skills open standard** — the exact same `SKILL.md` format as gald3r. Zero translation needed.

## Why Tier 1?

- **Native SKILL.md**: TRAE uses the Agent Skills open standard — gald3r skills install directly
- **Free models**: Doubao-Seed-2.0-Code (87.8 LiveCodeBench v6) included free
- **ByteDance backing**: Large user base, especially strong in China developer market
- **SOLO Mode**: Autonomous task execution with spec-driven workflows
- **MCP**: Supported

## Quick Start (New Project)

1. Download **TRAE** from [trae.ai](https://www.trae.ai) (macOS or Windows)
2. Copy the `trae/` folder contents to your project root
3. Open your project in TRAE — skills are auto-discovered from `.trae/skills/`

## What's Inside

```
trae/
  .trae/
    skills/
      gald3r/
        SKILL.md          # gald3r project skill (Agent Skills format)
    rules/
      gald3r.md           # gald3r project rules
  README.md               # This file
```

## Skills Format

TRAE uses the same `SKILL.md` format as gald3r:

```markdown
---
name: skill-name
description: "When and how to use this skill"
---

# Skill Instructions
```

You can also upload skills via TRAE Settings > Rules & Skills, or install from the TRAE marketplace.

## Documentation

- **Primary**: [trae.ai](https://www.trae.ai)
- **Agent (open source)**: [github.com/bytedance/trae-agent](https://github.com/bytedance/trae-agent)
- **Skills standard**: [agentskills.io](https://agentskills.io)
