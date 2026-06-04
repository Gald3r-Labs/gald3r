# Hermes Agent — gald3r Integration

## Setup Note

**All Hermes configuration is user-global** — there is no per-project `.hermes/` directory.

To integrate gald3r skills with Hermes, install them to your global Hermes skills directory:

```bash
# Copy gald3r skills to your global Hermes install
cp -r .gald3r_sys/skills/g-skl-*/ ~/.hermes/skills/
```

## Project Guidance

Hermes reads `AGENTS.md` at the project root for project-specific context, conventions, and
architecture notes. See `AGENTS.md` in this template for a pre-configured starting point.

## Global Config Location

```
~/.hermes/
├── config.yaml      # Primary settings (model, provider, API keys path)
├── SOUL.md          # Agent identity (slot #1 in system prompt)
├── skills/          # All gald3r skills go here
│   └── gald3r/
│       └── SKILL.md
└── memories/
    └── MEMORY.md    # Cross-session persistent memory
```

## Docs

- https://hermes-agent.nousresearch.com/docs/
- https://github.com/NousResearch/hermes-agent
