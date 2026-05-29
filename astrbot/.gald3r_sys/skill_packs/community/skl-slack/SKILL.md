---
name: skl-slack
description: Slack workspace management ΓÇö channels, apps, webhooks, workflow builder, bot development with Bolt SDK, Block Kit UI, MCP context gaps, community management.
skill_group: "community"
skill_category: "Community & Communication"
---

# Slack Workspace Management

Slack is the dominant team communication platform. This skill covers workspace administration, app/bot development, and community management.

## Prerequisites

- Slack workspace admin access
- For app development: https://api.slack.com/apps ΓåÆ Create New App
- Bolt SDK: `npm install @slack/bolt` or `pip install slack-bolt`

## Operation: WORKSPACE

Workspace configuration and administration.

**Key admin settings (via workspace admin panel):**
- **Sidebar**: Customize default channels, section ordering
- **Permissions**: Who can create channels, DM externals, install apps
- **Retention**: Message retention policy per channel/DM
- **Analytics**: workspace.admin.analytics API for usage stats

```bash
# Slack CLI (for app management)
npm install -g @slack/cli
slack login
slack workspace list
```

## Operation: CHANNELS

Channel strategy for projects and communities.

**Recommended channel structure for a dev project:**
| Channel | Purpose |
|---------|---------|
| `#general` | Team announcements |
| `#dev` | Engineering discussion |
| `#deploys` | CI/CD notifications |
| `#alerts` | Monitoring/error alerts |
| `#releases` | Release announcements |
| `#feedback` | User/customer feedback |
| `#random` | Off-topic |

```bash
# Slack API: create channel
curl -X POST https://slack.com/api/conversations.create \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "dev-updates", "is_private": false}'

# Archive channel
curl -X POST https://slack.com/api/conversations.archive \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -d '{"channel": "C1234567890"}'
```

## Operation: APP

Create Slack apps (bots and integrations).

**App manifest (api.slack.com ΓåÆ App Manifest):**
```yaml
display_information:
  name: gald3r-bot
  description: gald3r task notifications
features:
  bot_user:
    display_name: gald3r
    always_online: true
oauth_config:
  scopes:
    bot:
      - channels:read
      - chat:write
      - commands
      - incoming-webhook
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.channels
  slash_commands:
    - command: /status
      description: Show gald3r project status
  org_deploy_enabled: false
  socket_mode_enabled: true
```

## Operation: WEBHOOKS

Incoming webhooks for one-way notifications (CI/CD, alerts, deploys).

```python
# Python: send message via webhook
import httpx, os

def notify_slack(message: str, channel_webhook: str = None):
    url = channel_webhook or os.environ["SLACK_WEBHOOK_URL"]
    httpx.post(url, json={"text": message})

# With Block Kit formatting
httpx.post(url, json={
    "blocks": [
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f"*Deploy Complete* :rocket:\n`{branch}` ΓåÆ production\n{url}"}},
        {"type": "divider"},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"Triggered by {actor} at {timestamp}"}
        ]}
    ]
})
```

```bash
# GitHub Actions: send Slack notification
- name: Notify Slack
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"Deploy to production complete :white_check_mark:"}' \
      $SLACK_WEBHOOK_URL
```

## Operation: WORKFLOW-BUILDER

No-code automation within Slack.

**Useful workflows:**
- **Standup collector**: Scheduled message asking team for updates ΓåÆ compiles thread
- **Incident response**: `/incident` command ΓåÆ creates channel, pages on-call, posts runbook
- **Onboarding**: New member joins ΓåÆ DMs welcome message with links
- **Approval flow**: Request ΓåÆ manager DM ΓåÆ approve/deny ΓåÆ channel notification

Setup: Workspace ΓåÆ Automations ΓåÆ Workflow Builder ΓåÆ Create Workflow

## Operation: BOT

Build interactive Slack bots with Bolt SDK.

```python
# pip install slack-bolt
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.command("/status")
def handle_status(ack, respond, command):
    ack()
    respond(f"Project status: All systems operational")

@app.event("app_mention")
def handle_mention(event, say):
    say(f"Hey <@{event['user']}>, I'm here!")

@app.action("approve_button")
def handle_approval(ack, body, client):
    ack()
    client.chat_postMessage(
        channel=body["channel"]["id"],
        text="Request approved!"
    )

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

## Operation: MCP-CONTEXT

Slack content surfacing via gald3r MCP context injection.

**Current gaps (no native Slack MCP in gald3r v1.2):**
- Slack messages not indexed in vault
- Thread summaries not auto-captured to session context

**Workarounds:**
1. Use Slack's "Save to gald3r" workflow (Workflow Builder + webhook ΓåÆ vault note)
2. Export channel history via Slack API ΓåÆ `vault_sync` MCP tool
3. Use Slack's Zapier/Make integration ΓåÆ POST to gald3r webhook endpoint

```bash
# Export channel history (admin only)
curl "https://slack.com/api/conversations.history?channel=$CHANNEL_ID&limit=100" \
  -H "Authorization: Bearer $SLACK_TOKEN" > channel_export.json
```

## Operation: COMMUNITY

Managing open-source or public Slack communities.

- **Slack Connect**: Invite external users to shared channels without workspace membership
- **User groups**: `@design-team`, `@on-call` ΓÇö notify subsets without @channel
- **Channel sections**: Group related channels in sidebar for discoverability
- **Shared channels**: Bridge two Slack workspaces (useful for partner orgs)
- **Community guidelines**: Pin in `#general`, reference in onboarding workflow
- **Moderation**: Workspace settings ΓåÆ Members ΓåÆ Restrict messaging; DM guard for spam
