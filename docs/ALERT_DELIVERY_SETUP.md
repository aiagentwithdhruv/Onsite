# Alert delivery setup (Telegram, Discord, WhatsApp, Email)

Smart alerts are sent to users on **Telegram**, **Discord**, **WhatsApp**, and **Email** based on their preferences.

## 1. Run migrations 009 and 010

In Supabase SQL Editor, run in order:
- `database/009_alert_delivery_channels.sql`
- `database/010_discord_channel.sql`

## 2. Environment variables

Add to `.env`:

```env
# Telegram (priority) — create bot via @BotFather, then:
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# WhatsApp (Gupshup or Business API)
GUPSHUP_API_KEY=...
GUPSHUP_APP_NAME=...
GUPSHUP_SOURCE_NUMBER=...

# Optional: WhatsApp Cloud API (alternative to Gupshup)
# WHATSAPP_CLOUD_API_TOKEN=...
# WHATSAPP_PHONE_NUMBER_ID=...

# Email (Resend)
RESEND_API_KEY=...
FROM_EMAIL=alerts@onsite.team
```

## 3. Telegram webhook (for "Link Telegram")

So that "Link account" on the Alerts page works, Telegram must call your backend when a user sends `/start`:

1. Expose your backend (e.g. `https://your-api.com`) with HTTPS.
2. Set the webhook (once):

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-api.com/api/alerts/telegram-webhook"
```

3. Users: open Alerts → Alert delivery → **Link account** → open the `t.me/YourBot?start=...` link and tap **Start**. Their Telegram is then linked for alert delivery.

## 4. Discord (webhook)

No env vars needed. Each user:

1. In Discord: Server → Channel Settings → Integrations → Webhooks → New Webhook. Copy the webhook URL.
2. In app: Alerts → Alert delivery → Discord: paste URL and click Save. Toggle "Discord" on.

Alerts are posted to that channel (max 2000 chars per message).

## 5. User preferences

- **Alerts page** → "Alert delivery": toggle Telegram / Discord / WhatsApp / Email; link Telegram; paste Discord webhook.
- **WhatsApp** uses `users.phone` (with country code, e.g. 919876543210).
- **Email** uses `users.email`.

Delivery order: **Telegram** → **Discord** → **WhatsApp** → **Email**. All enabled channels receive each alert after a CSV upload.
