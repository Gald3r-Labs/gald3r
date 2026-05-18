---
name: skl-discord
description: Discord server management for project communities — setup, bots, moderation, growth playbook, analytics, GitHub/CI integrations.
---
# Discord Server Management

**Activate for**: "Discord server", "Discord bot", "Discord setup", "community management", "AutoMod", "Discord webhook"

---

## SETUP — New Server Scaffold

### Channel categories
```
INFORMATION: #welcome, #announcements, #roadmap
COMMUNITY: #general, #introductions, #showcase, #off-topic
DEVELOPMENT: #dev-chat, #help (Forum), #bugs, #pull-requests
VOICE: #voice-general, #pair-programming
ADMIN (hidden): #mod-log, #admin-chat
```

### Role hierarchy
Owner → Admin → Moderator → Contributor → Member → Unverified → Bot

### Onboarding
1. Enable Community features
2. Set Verification Level to Medium
3. Create Rules Screening
4. Configure Onboarding questions for auto-role assignment

---

## BOT — Bot Integration

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

## USER-MGMT — Member Management

- **Reaction roles**: Carl-bot or custom bot, emoji-based self-assignment
- **Moderation**: Timeout (up to 28 days), Kick (can rejoin), Ban (permanent)
- **Verification levels**: None → Low (email) → Medium (5min) → High (10min) → Highest (phone)

---

## MODERATION — AutoMod & Spam

### AutoMod rules (Server Settings → AutoMod)
- Block spam links, slurs, mention spam (5+), repeated messages
- Set escalation: Warning → 1h timeout → 24h timeout → Kick → Ban

### Mod log
Configure bot to log joins/leaves, deletes, role changes, bans to `#mod-log`.

---

## GROWTH — Community Playbook

### Discord badge for README
```markdown
[![Discord](https://img.shields.io/discord/SERVER_ID?color=5865F2&logo=discord&logoColor=white)](https://discord.gg/INVITE)
```

### Cross-posting: Twitter per release, Reddit monthly showcases, LinkedIn quarterly milestones
### Campaigns: weekly showcases, monthly AMAs, contributor spotlights

---

## ANALYTICS — Health Metrics

| Metric | Healthy | Source |
|--------|---------|--------|
| Daily active | 5–15% of total | Server Insights |
| Join/leave ratio | >2:1 | Server Insights |
| Engagement rate | 20–40% | Statbot |

---

## INTEGRATIONS — GitHub & CI Webhooks

### GitHub → Discord
Channel Settings → Integrations → Webhooks → copy URL → GitHub Settings → Webhooks → paste with `/github` suffix.

### CI/CD notification
```yaml
- name: Discord notify
  run: |
    curl -X POST "${{ secrets.DISCORD_WEBHOOK }}" \
      -H "Content-Type: application/json" \
      -d '{"embeds":[{"title":"Build ${{ job.status }}","color":3066993}]}'
```
