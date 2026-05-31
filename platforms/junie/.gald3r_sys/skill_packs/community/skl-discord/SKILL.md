---
name: skl-discord
description: Discord server management for project communities ΓÇö setup, bots, moderation, growth playbook, analytics, GitHub/CI integrations.
skill_group: "community"
skill_category: "Community & Communication"
---
# Discord Server Management

**Activate for**: "Discord server", "Discord bot", "Discord setup", "community management", "AutoMod", "Discord webhook"

---

## SETUP ΓÇö New Server Scaffold

### Channel categories
```
INFORMATION: #welcome, #announcements, #roadmap
COMMUNITY: #general, #introductions, #showcase, #off-topic
DEVELOPMENT: #dev-chat, #help (Forum), #bugs, #pull-requests
VOICE: #voice-general, #pair-programming
ADMIN (hidden): #mod-log, #admin-chat
```

### Role hierarchy
Owner ΓåÆ Admin ΓåÆ Moderator ΓåÆ Contributor ΓåÆ Member ΓåÆ Unverified ΓåÆ Bot

### Onboarding
1. Enable Community features
2. Set Verification Level to Medium
3. Create Rules Screening
4. Configure Onboarding questions for auto-role assignment

---

## BOT ΓÇö Bot Integration

| Bot | Best for | Free? |
|-----|----------|-------|
| Carl-bot | Auto-roles, embeds | Yes |
| MEE6 | Welcome, levels | Limited |
| Combot | Analytics, spam | Yes |
| Custom (Discord.py) | Full control | N/A |

### Discord.py quickstart
```python
import discord
from discord import app_commands

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(client.latency*1000)}ms")

client.run("BOT_TOKEN")  # Use env var
```

---

## USER-MGMT ΓÇö Member Management

- **Reaction roles**: Carl-bot or custom bot, emoji-based self-assignment
- **Moderation**: Timeout (up to 28 days), Kick (can rejoin), Ban (permanent)
- **Verification levels**: None ΓåÆ Low (email) ΓåÆ Medium (5min) ΓåÆ High (10min) ΓåÆ Highest (phone)

---

## MODERATION ΓÇö AutoMod & Spam

### AutoMod rules (Server Settings ΓåÆ AutoMod)
- Block spam links, slurs, mention spam (5+), repeated messages
- Set escalation: Warning ΓåÆ 1h timeout ΓåÆ 24h timeout ΓåÆ Kick ΓåÆ Ban

### Mod log
Configure bot to log joins/leaves, deletes, role changes, bans to `#mod-log`.

---

## GROWTH ΓÇö Community Playbook

### Discord badge for README
```markdown
[![Discord](https://img.shields.io/discord/SERVER_ID?color=5865F2&logo=discord&logoColor=white)](https://discord.gg/INVITE)
```

### Cross-posting: Twitter per release, Reddit monthly showcases, LinkedIn quarterly milestones
### Campaigns: weekly showcases, monthly AMAs, contributor spotlights

---

## ANALYTICS ΓÇö Health Metrics

| Metric | Healthy | Source |
|--------|---------|--------|
| Daily active | 5ΓÇô15% of total | Server Insights |
| Join/leave ratio | >2:1 | Server Insights |
| Engagement rate | 20ΓÇô40% | Statbot |

---

## INTEGRATIONS ΓÇö GitHub & CI Webhooks

### GitHub ΓåÆ Discord
Channel Settings ΓåÆ Integrations ΓåÆ Webhooks ΓåÆ copy URL ΓåÆ GitHub Settings ΓåÆ Webhooks ΓåÆ paste with `/github` suffix.

### CI/CD notification
```yaml
- name: Discord notify
  run: |
    curl -X POST "${{ secrets.DISCORD_WEBHOOK }}" \
      -H "Content-Type: application/json" \
      -d '{"embeds":[{"title":"Build ${{ job.status }}","color":3066993}]}'
```
