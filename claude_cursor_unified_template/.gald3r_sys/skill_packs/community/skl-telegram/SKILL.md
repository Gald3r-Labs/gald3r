---
name: skl-telegram
description: Telegram channel & community management ΓÇö bots, channels, groups, moderation, notifications, growth, Mini Apps. GitHub/CI webhook integration.
skill_group: "community"
skill_category: "Community & Communication"
---
# Telegram Community Management

**Activate for**: "Telegram bot", "Telegram channel", "Telegram group", "BotFather", "Telegram webhook"

---

## BOT ΓÇö Bot Creation

### BotFather workflow
1. Open @BotFather ΓåÆ `/newbot` ΓåÆ choose name + username (must end in "bot")
2. Save token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Webhook vs polling
| Mode | Pros | Cons |
|------|------|------|
| Webhook | Real-time, scalable | Needs HTTPS endpoint |
| Polling | No server needed | Latency, wastes resources |

### python-telegram-bot quickstart
```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online!")

app = Application.builder().token("BOT_TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
```

### Rate limits: 1 msg/sec per chat, 30 msg/sec global

---

## CHANNEL ΓÇö Channel Management

- **Public**: searchable, `t.me/username` ΓÇö for announcements
- **Private**: invite-link only ΓÇö for beta testers
- Link a **discussion group** for comments on channel posts

### Post scheduling
```python
from telegram.ext import Application
from datetime import datetime, timedelta, timezone
import asyncio

async def schedule_post(bot_token, chat_id, text, when: datetime):
    """Schedule a message using APScheduler or asyncio."""
    app = Application.builder().token(bot_token).build()
    delay = (when - datetime.now(timezone.utc)).total_seconds()
    await asyncio.sleep(max(0, delay))
    await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

# Using APScheduler (recommended for production)
# pip install APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(
    lambda: bot.send_message(chat_id="@mychannel", text="≡ƒôó Weekly update!"),
    trigger="cron", day_of_week="mon", hour=9
)
scheduler.start()
```

### Pin and unpin messages
```bash
# Pin a message (use message_id from the post)
curl "https://api.telegram.org/bot$TOKEN/pinChatMessage" \
  -d chat_id="@mychannel" -d message_id=123 -d disable_notification=true

# Unpin
curl "https://api.telegram.org/bot$TOKEN/unpinChatMessage" \
  -d chat_id="@mychannel" -d message_id=123

# Unpin all
curl "https://api.telegram.org/bot$TOKEN/unpinAllChatMessages" \
  -d chat_id="@mychannel"
```

### Channel statistics
```bash
# Get member count
curl "https://api.telegram.org/bot$TOKEN/getChatMemberCount?chat_id=@mychannel"

# Get post view count (available per message, not aggregate)
curl "https://api.telegram.org/bot$TOKEN/getChat?chat_id=@mychannel"
# Returns: title, description, invite_link, pinned_message, linked_chat_id

# Full analytics: use @ControllerBot or @TGStat_bot in the channel
# Third-party: https://tgstat.ru or https://telemetr.io (public channels)
```

| Metric | API | Third-party tool |
|--------|-----|-----------------|
| Member count | getChatMemberCount | TGStat/Telemetr |
| Post views | message.views field | TGStat/Telemetr |
| Forwards | message.forwards field | TGStat |
| Subscriber growth | ΓÇö | TGStat/Telemetr |

---

## GROUP ΓÇö Supergroup Administration

### Anti-spam bots
| Bot | Features |
|-----|----------|
| @ComBot | Analytics, captcha, CAS |
| @RoseSupportBot | Filters, notes, warnings |
| @ShieldyBot | Join captcha verification |

### Slow mode: 10s to 1hr between messages per user

---

## MODERATION ΓÇö Ban/Kick/Restrict

```bash
# Ban user
curl "https://api.telegram.org/bot$TOKEN/banChatMember?chat_id=$CHAT&user_id=$USER"
# Restrict (read-only for 1 hour)
curl "https://api.telegram.org/bot$TOKEN/restrictChatMember?chat_id=$CHAT&user_id=$USER&permissions={\"can_send_messages\":false}&until_date=$(($(date +%s)+3600))"
```

### CAS (Combot Anti-Spam): Add @comaborgupdates, `/cas on`

---

## NOTIFICATIONS ΓÇö GitHub & CI Integration

### GitHub Actions ΓåÆ Telegram
```yaml
- name: Telegram notify
  run: |
    curl -s -X POST "https://api.telegram.org/bot${{ secrets.TG_TOKEN }}/sendMessage" \
      -d chat_id="${{ secrets.TG_CHAT }}" -d parse_mode="HTML" \
      -d text="$([[ '${{ job.status }}' == 'success' ]] && echo 'Γ£à' || echo 'Γ¥î') <b>Build ${{ job.status }}</b>"
```

### gald3r task completion alert via bot
```python
import httpx, os

async def gald3r_task_alert(task_id: int, title: str, status: str):
    """Send gald3r task completion notification to a Telegram channel."""
    icon = "Γ£à" if status == "completed" else "≡ƒöì" if status == "awaiting-verification" else "Γ¥î"
    text = f"{icon} <b>gald3r Task #{task_id}</b>\n<code>{title}</code>\nStatus: <b>{status}</b>"
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
            json={"chat_id": os.environ["TG_CHAT_ID"], "text": text, "parse_mode": "HTML"}
        )

# Wire into gald3r hook: .claude/hooks/g-hk-agent-complete.ps1
# Add: Invoke-RestMethod -Uri "https://yourserver/gald3r-notify" -Method POST -Body ...
```

### sendMessage API
```bash
curl "https://api.telegram.org/bot$TOKEN/sendMessage" -d chat_id="$CHAT" -d text="Hello!" -d parse_mode="MarkdownV2"
```

---

## GROWTH ΓÇö Community Growth

### Invite links with limits
```bash
curl "https://api.telegram.org/bot$TOKEN/createChatInviteLink" \
  -d chat_id="$CHAT" -d member_limit=100 -d name="Twitter campaign"
```

### Telegram Directory listing
Submit your public channel to **[t.me/catalog](https://t.me/catalog)** (Telegram's official directory) and third-party aggregators:
- **TGStat.ru** ΓÇö `https://tgstat.ru/en/channel/add` ΓÇö submit username, verify ownership via pinned post or bot
- **Telemetr.io** ΓÇö `https://telemetr.io/en/channels` ΓÇö automatic index for public channels >100 subscribers
- **Combot Ratings** ΓÇö auto-indexed via @ComBot when added to your channel

### README badge
```markdown
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white)](https://t.me/gald3r_community)
```

---

## MINI-APPS ΓÇö When to Use

| Feature | Bot Commands | Mini Apps |
|---------|-------------|-----------|
| Simple actions | /status | Overkill |
| Rich UI | Awkward | Dashboard, forms |
| Payments | Basic | Full checkout |

### Web App launch_url pattern
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Button that launches a Mini App (Web App)
keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        text="Open Dashboard",
        web_app=WebAppInfo(url="https://yourapp.com/tg-miniapp")
    )
]])

await update.message.reply_text("Open the gald3r dashboard:", reply_markup=keyboard)

# Your web app receives initData via window.Telegram.WebApp.initData
# Validate server-side using HMAC-SHA256 with bot token
```

```javascript
// Client-side Mini App initialization
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();  // Full screen

const user = tg.initDataUnsafe.user;
console.log(user.id, user.username);

// Send data back to bot
tg.sendData(JSON.stringify({ action: "task_complete", task_id: 42 }));
tg.close();
```

### Payment integration basics
```python
# 1. Get Stripe test token from @BotFather ΓåÆ /mybots ΓåÆ Payments ΓåÆ Connect Stripe (test)
# 2. Send invoice
await context.bot.send_invoice(
    chat_id=update.effective_chat.id,
    title="gald3r Pro Subscription",
    description="Monthly access to gald3r Pro features",
    payload="pro-monthly-{user_id}",
    provider_token=os.environ["PAYMENT_TOKEN"],  # from BotFather
    currency="USD",
    prices=[{"label": "Monthly", "amount": 999}]  # amount in cents
)

# 3. Handle pre-checkout query (always answer within 10s)
async def precheckout(update, context):
    await update.pre_checkout_query.answer(ok=True)

# 4. Handle successful payment
async def successful_payment(update, context):
    payment = update.message.successful_payment
    # Activate subscription for user
```

---

## Notes

- Bot API base: `https://api.telegram.org/bot{token}/`
- Chat IDs: groups are negative, users are positive
- Parse modes: `HTML`, `MarkdownV2` (recommended)
- No per-user analytics ΓÇö subscriber count + post views only
