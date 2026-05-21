# WhatsApp — Meta Cloud API Direct (no Gallabox)

> **Built:** 2026-05-21 (this session, Angelina executed end-to-end)
> **Why direct, not Gallabox:** Gallabox is a BSP wrapping Meta's API + charging platform fees on top. For an inbound AI bot (customers message us first), Meta's user-initiated tier is FREE up to 1,000 conversations/month, then ~Rs.0.30 each. We don't need Gallabox's agent dashboard.
> **Status:** Code is live. Pending Meta test creds to fire first send.

---

## Files shipped

| File | Purpose |
|---|---|
| `onsite-hub/src/lib/whatsapp/meta_client.ts` | Send text / templates / media; download incoming media; mark-read. Talks to `graph.facebook.com/v21.0`. |
| `onsite-hub/src/lib/whatsapp/signature.ts` | Verifies `X-Hub-Signature-256` HMAC on incoming webhook posts. Refuses unverified payloads. |
| `onsite-hub/src/app/api/task-bot/whatsapp/webhook/route.ts` | GET (verification handshake) + POST (incoming messages). Auto-echoes for now; will plug into the bot pipeline in the next iteration. |
| `onsite-hub/src/app/api/task-bot/whatsapp/test-send/route.ts` | Internal-only test endpoint, gated by `INTERNAL_PUSH_SECRET`. Use for the first send. |
| `Onsite/task-ai/database/010_wa_user_link.sql` | `wa_user_link` + `wa_link_otp` tables for phone↔user mapping + 6-digit OTP linking. Not used by initial test send — required when we add real bot brain. |

TS check: clean. All 3 remaining errors are pre-existing (chat/route.ts + chat/page.tsx, documented).

---

## The 30-minute path to first test send

You can test TODAY without Sumit kicking off business verification. Meta gives every dev app a free test phone number + 5 verified-recipient slots.

### Step 1 — Create a dev app at Meta (10 min)

1. Open https://developers.facebook.com → **My Apps** → **Create App**
2. Type: **Business** (NOT "Consumer")
3. App name: `Onsite Task AI` (whatever you want)
4. Contact email: yours
5. Business Account: pick the existing Onsite Meta Business Account if dropdown shows one, else "Create new" (you can switch later)

### Step 2 — Add WhatsApp product (5 min)

1. App dashboard → **Add products to your app** → find **WhatsApp** → **Set up**
2. You'll land on **WhatsApp > API Setup**
3. From this screen, copy three values into a note:
   - **Temporary access token** (24-hr; we'll swap for a permanent one later)
   - **Phone number ID** (looks like `123456789012345` — this is the graph ID, NOT the phone digits)
   - **App ID** (top of left sidebar)

### Step 3 — Add your own phone as a verified test recipient (2 min)

In the same **API Setup** screen:

1. **To** dropdown → **Manage phone number list** → **Add phone number**
2. Enter `+91 8770101822` (or whichever number should receive)
3. Meta sends an SMS verification — type the code
4. Phone is now whitelisted for receiving test messages

### Step 4 — Grab the App Secret (1 min)

In your app dashboard:

1. Left sidebar → **App settings** → **Basic**
2. **App Secret** → **Show** → copy

This is the secret we HMAC the incoming webhooks against. Required.

### Step 5 — Paste into onsite-hub/.env.local (1 min)

Add these to `Onsite/onsite-hub/.env.local`:

```
META_WHATSAPP_ACCESS_TOKEN=<temp token from API Setup>
META_WHATSAPP_PHONE_NUMBER_ID=<phone number ID, the graph ID>
META_WHATSAPP_APP_SECRET=<App Secret from App Settings → Basic>
META_WHATSAPP_WEBHOOK_VERIFY_TOKEN=<make one up, any random string e.g. "onsite-wa-verify-2026">
META_GRAPH_VERSION=v21.0
```

Restart dev server.

### Step 6 — Fire the first test send (1 min)

```bash
# Read your INTERNAL_PUSH_SECRET (set during PWA sprint) from .env.local
INTERNAL_PUSH_SECRET=$(grep ^INTERNAL_PUSH_SECRET "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub/.env.local" | cut -d= -f2)

curl -X POST 'http://localhost:3001/api/task-bot/whatsapp/test-send' \
  -H "X-Internal-Auth: $INTERNAL_PUSH_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "918770101822",
    "template": "hello_world",
    "language": "en_US"
  }'
```

`hello_world` is Meta's default approved template — works on every fresh dev app. Expect `200` + `message_id` + a WhatsApp on your phone within ~5 seconds.

After the recipient (you) replies to that message, the 24-hour service window opens. Then this works:

```bash
curl -X POST 'http://localhost:3001/api/task-bot/whatsapp/test-send' \
  -H "X-Internal-Auth: $INTERNAL_PUSH_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"to": "918770101822", "text": "Freeform send from Onsite Task AI"}'
```

### Step 7 — Wire the webhook (5 min)

For the bot to receive incoming messages from real customers, Meta needs a public URL to POST to. Locally:

```bash
cloudflared tunnel --url http://localhost:3001
# Note the public URL it prints, e.g. https://something.trycloudflare.com
```

In Meta dashboard:

1. **WhatsApp > Configuration > Webhook** → **Edit**
2. **Callback URL:** `https://<tunnel-url>/api/task-bot/whatsapp/webhook`
3. **Verify Token:** the same string you set in `META_WHATSAPP_WEBHOOK_VERIFY_TOKEN`
4. Click **Verify and Save** → Meta does a GET; our route echoes the challenge back; subscribes
5. **Webhook fields** → toggle on **messages**

Now message your test number from your personal WhatsApp. Server log shows the incoming; you get an echo reply.

---

## The production path (Sumit's side — 1-3 days, can run in parallel)

Test mode caps at 5 verified recipients. Real customer rollout needs:

1. **Meta Business Verification.** Sumit logs into `business.facebook.com` → **Business Info** → **Start verification**. Upload Onsite's CIN docs (`U72900DL2021PTC379359`) + GST cert (`09AAVCA0250E1ZR`). 1-3 business days for Meta to approve.
2. **Real phone number** registered to the WhatsApp Business Account. Use a number that's NOT on any other WhatsApp app or WhatsApp Business app — Meta locks it to the API. Sumit can dedicate a number for this.
3. **Permanent System User access token.** Once verified, create a System User in Business Manager with `whatsapp_business_messaging` + `whatsapp_business_management` scopes. Generate the token. **It doesn't expire.** Swap into `META_WHATSAPP_ACCESS_TOKEN`.
4. **Display name approval.** WhatsApp Manager → set display name (e.g. "Onsite AI"). Approval takes ~30 min.
5. **Templates.** For any messages you'll send WHERE the customer hasn't messaged us in 24 hours (notifications, reminders, broadcasts), create + submit templates in WhatsApp Manager > Message Templates. Approval is ~30 min — 24 hr per template.

When all of the above is done, swap the env vars to the production values and we're live.

---

## Cost model (vs Gallabox)

For an inbound AI bot at Onsite's expected scale (1,000-3,000 customer messages/month):

| Provider | Platform fee | Per-conversation | Monthly est. |
|---|---|---|---|
| **Meta Cloud API direct** | Rs.0 | Rs.0 for first 1,000 user-initiated/mo, Rs.0.30 after | **Rs.0-600/mo** |
| Gallabox Starter | Rs.1,499/mo for 1 user | Markup on Meta rates | Rs.1,500-3,000/mo |
| Gallabox Growth (3 users) | Rs.3,499/mo | Markup | Rs.3,500-5,000/mo |

For the 16-user sales team currently on Gallabox: we keep that for outbound CRM messaging if needed (separate from bot), or migrate that too once the bot pipe is proven.

---

## What's not yet wired (next iteration)

The webhook currently echoes back a hardcoded reply. Next chunk plugs WhatsApp incoming → the existing bot pipeline:

1. **Phone → user resolution.** `wa_user_link` table queried on each incoming. If unknown phone → bot replies "Send the 6-digit code from your Onsite app to link."
2. **Bot brain.** Translate `messages: [{role: 'user', content: text.body}]`, call existing `/api/task-bot` route logic with the resolved user's JWT, get reply.
3. **Voice notes.** Download via `downloadMedia()`, send to Gemini for transcription, run through bot, generate TTS reply, upload + send as audio.
4. **Tool cards on WhatsApp.** RAG citations, ticket creation confirmations, etc. — render as compact text (no rich UI in WhatsApp).

I'll wire those when you give the go after the first ping-pong test succeeds.

---

## Quick env-var checklist

```
META_WHATSAPP_ACCESS_TOKEN=                # 24-hr temp from dev dashboard, or permanent System User token
META_WHATSAPP_PHONE_NUMBER_ID=             # the graph ID, NOT the phone digits
META_WHATSAPP_APP_SECRET=                  # from App Settings → Basic
META_WHATSAPP_WEBHOOK_VERIFY_TOKEN=        # any random string you choose, used during webhook setup
META_GRAPH_VERSION=v21.0                   # optional
INTERNAL_PUSH_SECRET=                      # already set during PWA sprint — same secret gates the test-send endpoint
```

---

## When you get blocked

| Symptom | Cause | Fix |
|---|---|---|
| `401` on send | Token expired (24-hr temp) or wrong | Regenerate temp token in dev dashboard, or upgrade to System User permanent token |
| `400 (#131009) Recipient phone number not in allowed list` | Test mode; recipient not added | Add recipient in API Setup → Manage phone number list |
| `400 outside 24-hour window` | Sending freeform to a number that hasn't messaged us in 24h | Use template (`hello_world` works in test) OR have recipient message first |
| `400 Phone number not found` | `META_WHATSAPP_PHONE_NUMBER_ID` is wrong (using digits, not graph ID) | Copy the long numeric ID, not the phone digits, from API Setup |
| Webhook never fires | Verify token mismatch, or webhook not subscribed to `messages` field | Re-verify in WhatsApp > Configuration; toggle on `messages` subscription |
| HMAC `403` on webhook POST | `META_WHATSAPP_APP_SECRET` wrong | Recopy from App Settings → Basic (NOT App Secret from other contexts) |

---

## Ready when you are

Drop the 4 creds into `.env.local`, restart dev, then say "fire the test." I'll run the curl, show you the response, and we proceed from there.
