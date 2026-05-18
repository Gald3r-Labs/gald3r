# Pack: community

Community management and growth — Discord, Telegram, and Slack.

## What This Installs

- `skl-discord` — Discord server setup, bots, moderation, growth playbook, analytics, GitHub/CI webhooks
- `skl-telegram` — Telegram bots, channels, groups, moderation, notifications, growth, Mini Apps
- `skl-slack` — Slack workspace management, app/bot development (Bolt SDK), Block Kit UI, Workflow Builder, webhooks

## Prerequisites

None required (documentation skills — no executables needed).

Optional for bot development:
- Discord: `npm install discord.js` or `pip install discord.py`
- Slack: `pip install slack-bolt` or `npm install @slack/bolt`
- Telegram: `pip install python-telegram-bot` or `npm install node-telegram-bot-api`

## Install

```powershell
.\skill_packs\community\install.ps1
.\skill_packs\community\install.ps1 -ProjectRoot "C:\my-project"
.\skill_packs\community\install.ps1 -List
```

## Uninstall

Delete these skill directories from your project's `.cursor/skills/`, `.claude/skills/`, etc.:
- `skl-discord/`, `skl-telegram/`, `skl-slack/`

## FILES

3 skills × 5 IDE targets = 15 files.

- `.cursor/skills/skl-discord/SKILL.md`
- `.cursor/skills/skl-telegram/SKILL.md`
- `.cursor/skills/skl-slack/SKILL.md`
- (+ 4 more IDE targets: .claude, .agent, .codex, .opencode)
