# AstrBot — gald3r Template

**gald3r** for **AstrBot** (open-source cross-platform AI agent chatbot platform)

---

## What is AstrBot?

[AstrBot](https://astrbot.app/) is an open-source all-in-one Agentic AI infrastructure that deploys AI agents into 18+ instant messaging platforms: QQ, Telegram, Slack, Discord, WeChat, DingTalk, LINE, and more.

**30,000+ GitHub stars** | Deploy via Docker, BT-Panel, 1Panel, or Windows installer.

---

## gald3r Compatibility

**Tier 3 — Adapted Compatibility**

AstrBot supports **Anthropic Skills** (from v4.13.0) — the same `SKILL.md` format gald3r uses. Skills are uploaded via the WebUI admin panel or bundled into a Python plugin. AstrBot is not a coding IDE — it's a chatbot deployment platform that can carry gald3r skills into your team's IM workflows.

---

## Quick Start

### Option A — Upload Individual Skills via WebUI

```bash
# 1. Package a gald3r skill
zip -r g-skl-status.zip g-skl-status/

# 2. Open AstrBot WebUI admin panel
# 3. Navigate: Plugins > Skills > Import Skill
# 4. Upload the .zip file
```

### Option B — Bundle as Plugin (Recommended)

```bash
# Copy the gald3r AstrBot plugin to your AstrBot plugins directory
cp -r gald3r/astrbot/gald3r_plugin/ /path/to/astrbot/plugins/

# Or upload via WebUI > Plugins > Install Plugin
```

---

## What's Inside

```
astrbot/
+-- gald3r_plugin/              <- installable AstrBot plugin
|   +-- metadata.yaml
|   +-- main.py
|   +-- skills/
|       +-- g-skl-status/
|       |   +-- SKILL.md
|       +-- g-skl-tasks/
|       |   +-- SKILL.md
|       +-- [... all gald3r skills ...]
+-- skills/                     <- individual skills for manual upload
    +-- g-skl-status.zip
    +-- g-skl-tasks.zip
    +-- [...]
```

---

## Supported Platforms

AstrBot connects gald3r skills to:

| Platform | Type |
|---|---|
| Telegram | IM |
| Discord | IM |
| Slack | IM |
| QQ / QQ Channel | IM |
| WeChat (企微) | IM |
| Lark (Feishu) | IM |
| DingTalk | IM |
| LINE | IM |
| +10 more | IM |

---

## Requirements

- AstrBot v4.13.0 or later
- Sandbox mode enabled for skill scripts (Config > Computer Use)

---

## Learn More

- [AstrBot Documentation](https://docs.astrbot.app/)
- [AstrBot Skills Guide](https://docs.astrbot.app/en/use/skills.html)
- [AstrBot Plugin Development](https://docs.astrbot.app/en/dev/star/plugin-new.html)
- [gald3r Framework](https://github.com/wrm3/gald3r)
