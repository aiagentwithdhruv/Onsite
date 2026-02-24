# Sales Intelligence System

AI-powered sales pipeline intelligence for Onsite Teams — CSV-driven pipeline analysis, smart alerts, and daily digests so reps and managers never miss follow-ups, overdue deals, or notes that need attention.

---

## What It Does

Upload a CRM/pipeline CSV and the system:
- **Scores leads** Hot/Warm/Cold with AI-powered reasoning
- **Detects anomalies** — stale deals, missing follow-ups, pipeline risks
- **Sends smart alerts** to your team via Telegram, WhatsApp, and Email
- **Generates daily briefs** — personalized morning briefings per rep
- **Profiles agents** — performance analysis across 33 deal owners

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Frontend** | Next.js 16, React 19, Tailwind 4, Recharts |
| **Backend** | FastAPI (Python), LangGraph agents |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **AI** | Claude (primary), GPT-4o (fallback), Haiku (scoring) |
| **CRM** | Zoho CRM REST API v8 |
| **Alerts** | Telegram, WhatsApp (Meta Cloud API), Email (Resend), Discord |

---

## Run Locally

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill Supabase + AI keys
uvicorn app.main:app --port 8000 --reload
```

### Frontend

```bash
cd frontend-next
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_SUPABASE_URL, API_URL
npm run dev
```

- Backend: **http://localhost:8000** | Health: `/health`
- Frontend: **http://localhost:3000**

### Database

Run migrations from `../database/` in Supabase SQL Editor, or:

```bash
python3 ../scripts/setup_database.py
```

---

## Dashboard Pages

| Page | What It Shows |
|------|---------------|
| **Home** | Pipeline value, hot leads, priority call list, daily brief |
| **Intelligence** | CSV upload, KPIs, 8 analysis tabs, filters |
| **Leads** | Hot prospects + stale leads from pipeline analysis |
| **Agent Profiles** | 33 deal owners — performance, strengths, concerns, trends |
| **Analytics** | Pipeline funnel, rep performance, source analysis, conversion trends |
| **Alerts** | Smart alerts with severity, multi-channel delivery |
| **Briefs** | AI-generated daily briefings per user |
| **Settings** | LLM config, notification preferences |

---

## Architecture

**Core principle:** Store OUTCOMES, not raw data.

CSV upload computes aggregated analytics (charts, KPIs, alerts, agent profiles) and stores only those in Supabase. Individual leads stay in Zoho CRM — not duplicated in the database.

Key data: Single `dashboard_summary` row with all pre-computed analytics — KPIs, charts, aging data, per-owner breakdowns.

---

## Alert Channels

| Channel | Status | Config |
|---------|--------|--------|
| Telegram | Working | Bot token + chat ID per user |
| WhatsApp | Ready | Meta Cloud API (direct, no BSP) |
| Email | Ready | Resend API |
| Discord | Ready | Webhook URL per user |

---

## AI Agents

| Agent | Schedule | What It Does |
|-------|----------|--------------|
| Daily Pipeline | 7:30 AM | Scores leads, generates call list, sends morning brief |
| Research | On-demand | Company research + CRM notes + close strategy |
| Assignment | On-demand | Auto-assigns new leads to best-fit rep |
| Weekly Report | Mon 8 AM | Pipeline summary, wins/losses, team performance |

---

## Env Variables

```
SUPABASE_URL=               # Supabase project URL
SUPABASE_KEY=               # Supabase anon key
SUPABASE_SERVICE_KEY=       # Supabase service role key
ANTHROPIC_API_KEY=          # Claude API
OPENAI_API_KEY=             # GPT-4o fallback
RESEND_API_KEY=             # Email delivery
WHATSAPP_CLOUD_TOKEN=       # Meta Cloud API token
WHATSAPP_PHONE_NUMBER_ID=   # Meta phone number ID
ZOHO_CLIENT_ID=             # Zoho CRM (optional)
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
```
