# Alert delivery setup (Telegram, Discord, WhatsApp, Email)

Smart alerts are sent to users on **Telegram**, **Discord**, **WhatsApp**, and **Email** based on their preferences.

---

## When are alerts sent?

Alerts are sent automatically when:

1. **CSV upload (Intelligence)** — After you upload a CSV, the backend generates smart alerts and delivers them to each user’s enabled channels (Telegram, Discord, WhatsApp, Email). So: upload a CSV → alerts are created → they are sent to Telegram (and others) if you have Chat ID + Telegram turned on.
2. **Afternoon / evening digests** — If you’ve set up cron (see `CRON_AND_DIGESTS.md`), digest messages are also sent to the same channels.

You need both: **Bot Token** (backend) and **Chat ID** (per user in the app). The backend uses the token to call Telegram’s API and send to your chat ID.

---

## 1. Run migrations 009 and 010

In Supabase SQL Editor, run in order:
- `database/009_alert_delivery_channels.sql`
- `database/010_discord_channel.sql`

---

## 2. Telegram: Bot Token + Chat ID

### Step A — Create a bot and get the token (one-time, backend)

1. In Telegram, open **@BotFather**.
2. Send `/newbot`, follow the prompts, and name your bot (e.g. “Onsite Alerts”).
3. BotFather will give you a **token** like `123456789:ABCdefGHI...`.
4. In your **backend** project, add to `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
```

5. Restart the backend so it loads the new env.

### Step B — Add your Chat ID (per user, in the app)

1. In Telegram, open **@userinfobot** and send any message.
2. It will reply with your **Id** (e.g. `123456789`). That is your **Chat ID**.
3. In the app: **Alerts** → **Alert delivery** → paste that number into **Chat ID** → click **Save**.
4. Turn the **Telegram** checkbox **on**.

After that, when alerts are generated (e.g. after an Intelligence CSV upload), the backend will send them to your Telegram using the Bot Token + your Chat ID. No webhook or “link account” flow is required.

---

## 3. Other environment variables

Add to backend `.env` as needed:

```env
# Telegram (see Step A above)
TELEGRAM_BOT_TOKEN=...

# WhatsApp (Gupshup or Business API)
GUPSHUP_API_KEY=...
GUPSHUP_APP_NAME=...
GUPSHUP_SOURCE_NUMBER=...

# Email (Resend)
RESEND_API_KEY=...
FROM_EMAIL=alerts@onsite.team
```

---

## 4. Discord (webhook)

No env vars needed. Each user:

1. In Discord: Server → Channel Settings → Integrations → Webhooks → New Webhook. Copy the webhook URL.
2. In app: Alerts → Alert delivery → Discord: paste URL and click Save. Toggle "Discord" on.

Alerts are posted to that channel (max 2000 chars per message).

## 5. User preferences

- **Alerts page** → “Alert delivery”: toggle Telegram / Discord / WhatsApp / Email; for Telegram paste **Chat ID** and Save; for Discord paste **Webhook URL** and Save.
- **WhatsApp** uses `users.phone` (with country code, e.g. 919876543210).
- **Email** uses `users.email`.

Delivery order: **Telegram** → **Discord** → **WhatsApp** → **Email**. All enabled channels receive each alert when they are generated (e.g. after a CSV upload in Intelligence).
