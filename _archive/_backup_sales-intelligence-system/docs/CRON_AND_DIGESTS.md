# Cron jobs: afternoon digest, evening summary, intelligence briefs

## Endpoints (POST)

- **`/api/cron/afternoon-digest`** — Sends "rest of day" digest to all users with notification channels enabled. Schedule at **2–3 PM**.
- **`/api/cron/evening-summary`** — Sends "tomorrow's focus" summary. Schedule at **6 PM**.
- **`/api/cron/generate-intelligence-briefs`** — Generates today's briefs from Intelligence summary + agent profiles (no Zoho). Schedule at **7 AM** or call after CSV upload (already triggered on upload).

## Security

Optional: set `SECRET_KEY` in `.env` (or keep default `change-this`). If set to a non-default value, requests must include header:

```
X-Cron-Secret: <your SECRET_KEY value>
```

Otherwise the endpoint returns 403. In development with default `secret_key`, the header is not required.

## How to schedule (n8n or system cron)

### n8n

1. Create a workflow with a **Schedule** trigger (e.g. 0 14 * * * for 2 PM, 0 18 * * * for 6 PM, 0 7 * * * for 7 AM).
2. Add an **HTTP Request** node:
   - Method: POST
   - URL: `https://your-backend.com/api/cron/afternoon-digest` (or evening-summary / generate-intelligence-briefs)
   - Headers: `X-Cron-Secret`: your secret (if required)

### System cron

```bash
# 2 PM: afternoon digest
0 14 * * * curl -s -X POST -H "X-Cron-Secret: YOUR_SECRET" https://your-backend.com/api/cron/afternoon-digest

# 6 PM: evening summary
0 18 * * * curl -s -X POST -H "X-Cron-Secret: YOUR_SECRET" https://your-backend.com/api/cron/evening-summary

# 7 AM: intelligence briefs (so reps see today's brief)
0 7 * * * curl -s -X POST -H "X-Cron-Secret: YOUR_SECRET" https://your-backend.com/api/cron/generate-intelligence-briefs
```

## Data source

- Digests and intelligence briefs use **dashboard_summary** (with `summary_by_owner`) and **agent_profiles** from Supabase. Ensure a CSV has been uploaded in Intelligence so summary and profiles exist.
- Users receive digests only if they have at least one of Telegram, Discord, WhatsApp, or Email enabled in Alerts → Alert delivery, and (for Telegram/Discord) are linked.
