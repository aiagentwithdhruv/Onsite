# Sales Intelligence System

**AI-powered sales pipeline intelligence for Onsite Teams** — CSV-driven pipeline analysis, smart alerts, daily digests, and configurable LLM providers. Built for reps, team leads, and founders to act on leads faster.

---

## What This System Does (In One Sentence)

Upload a CRM/pipeline CSV → the system scores leads, detects anomalies, suggests next actions, and sends **smart alerts** and **daily digests** (Telegram/email) so reps and managers never miss follow-ups, overdue deals, or notes that need action.

---

## For Founders & Stakeholders: The Big Picture

| Goal | How the system helps |
|------|----------------------|
| **Pipeline visibility** | Dashboard shows deal owners, stale deals, demos pending, and AI-suggested next actions. |
| **No missed follow-ups** | Alerts for **overdue**, **due today**, and **due tomorrow** (from CRM "Followup Date"). |
| **Notes that need action** | AI detects action keywords in notes/remarks and alerts with lead name, phone, and snippet. |
| **Consistent touchpoints** | Morning / afternoon / evening digests (3× daily) keep the team aligned. |
| **Cost control** | Admins choose **primary**, **fast**, and **fallback** AI models (OpenAI, Anthropic, OpenRouter, Moonshot) and store API keys in the app — no .env needed for keys. |
| **One place for alerts** | Users link Telegram (Chat ID) or use email; "Send test alert" validates delivery. |

---

## End-to-End Flow (How Data Moves)

```
┌─────────────────┐     upload      ┌──────────────────┐     sync / cron     ┌─────────────────┐
│  CRM / Export   │ ───────────────► │  Sales Intel     │ ◄───────────────── │  Supabase DB    │
│  (CSV)          │                  │  Backend         │                    │  (leads, config)│
└─────────────────┘                  └────────┬─────────┘                    └────────┬────────┘
                                             │                                        │
                                             │  LLM (scoring, research, alerts)       │
                                             │  Keys & model choice from app_config   │
                                             ▼                                        │
                                    ┌──────────────────┐                             │
                                    │  Smart Alerts     │ ──► batch per user          │
                                    │  + Digests        │ ──► Telegram / Email        │
                                    └──────────────────┘                             │
                                             │                                        │
                                             ▼                                        ▼
                                    ┌──────────────────┐     GET/PATCH               │
                                    │  Next.js App      │ ◄───────────────────────────┘
                                    │  (Dashboard,      │     (users, preferences,
                                    │   Alerts,         │      admin LLM/Telegram)
                                    │   Settings)       │
                                    └──────────────────┘
```

1. **Upload** — Admin/manager uploads a pipeline CSV (e.g. from Zoho/CRM). Columns include Deal Owner, Stage, Value, Followup Date, Notes/Remarks, etc.
2. **Backend** — FastAPI parses CSV, normalizes columns (flexible names), stores/caches in Supabase. Scheduler runs morning (8 AM), afternoon (2 PM), evening (6 PM) IST for digests.
3. **AI** — LLM (model chosen in Settings) scores leads, ranks by priority, detects anomalies, and powers "notes need action" and research. Primary / fast / fallback models are configurable.
4. **Alerts** — Smart alerts: overdue, due today, due tomorrow, notes needing action, high-value, etc. Batched per user and sent via Telegram and/or email. Test alert available from Alerts page.
5. **Frontend** — Next.js dashboard for pipeline summary, team attention, deal owners; Alerts page for notification preferences and test alert; Settings for Telegram bot token (manager+) and LLM API keys + model selection (admin only).

---

## Main Features (What We Built)

- **Intelligence pipeline**
  - CSV upload with flexible column mapping (Deal Owner, Followup Date, Notes/Remarks, etc.).
  - Cached pipeline and dashboard summary (deal owners, stale count, demos pending, next best action).
- **Smart alerts**
  - Types: overdue follow-up, due today, due tomorrow, notes need action (with lead name, phone, snippet), high-value, anomaly, etc.
  - Batched per user on upload; delivered via Telegram and/or email.
  - User preferences: enable/disable types, set Telegram Chat ID, "Send test alert."
- **Digests**
  - Morning, afternoon, evening (3× daily, IST). Structured message templates.
- **LLM & model selection**
  - API keys: Anthropic, OpenAI, OpenRouter, Moonshot — set in **Settings → LLM Providers** (stored in DB, not .env).
  - Model dropdowns: **Primary**, **Fast**, **Fallback** (from a fixed list of top models). Used for complex tasks, cheap tasks (e.g. scoring), and fallback on failure.
- **Telegram**
  - Bot token in Settings (manager+); stored in `app_config`. Users add Chat ID on Alerts page. Test alert to verify delivery.
- **Admin**
  - User management, sync status, AI usage, Telegram config, LLM config (keys + model selection). Roles: rep, team_lead, manager, founder, admin.

---

## Repository Structure

```
sales-intelligence-system/
├── README.md                 # This file — overview and flow
├── GAMMA-SLIDES-CONTENT.md   # Slide-by-slide content for Gamma PPT
├── DEPLOY.md                 # Deployment steps
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/routes/       # auth, leads, research, briefs, alerts, admin, intelligence, agents, cron
│   │   ├── core/             # config, auth, llm, llm_config, llm_models, supabase_client
│   │   ├── services/         # alert_delivery, digests, scheduler, telegram
│   │   └── agents/           # smart_alerts, scoring, etc.
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend-next/            # Next.js dashboard
│   ├── src/app/(dashboard)/  # dashboard, alerts, settings, etc.
│   └── package.json
└── database/                 # Supabase migrations
    ├── 001_initial_schema.sql
    ├── 007_smart_alerts.sql
    ├── 009_alert_delivery_channels.sql
    ├── 011_app_config.sql    # LLM keys, Telegram token, model selection
    └── ...
```

---

## Setup (Developers)

### Prerequisites

- Python 3.12+, Node 20+
- Supabase project (run migrations in `database/` in order)
- At least one LLM API key (e.g. Anthropic or OpenAI) — can be set in .env or later in Admin → Settings

### Backend

```bash
cd backend
cp .env.example .env   # Fill SUPABASE_*, SECRET_KEY, CORS_ORIGINS, optional API keys
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health`

### Frontend

```bash
cd frontend-next
cp .env.example .env.local   # NEXT_PUBLIC_SUPABASE_*, NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open `http://localhost:3000`. Log in with a user that exists in Supabase (e.g. seeded in `002_seed_data.sql`).

### Database

Run SQL files in `database/` in numeric order (001, 002, … 011) in your Supabase SQL editor. This creates tables for users, leads, alert preferences, `app_config`, etc.

---

## Environment Variables (Summary)

| Variable | Used for |
|----------|----------|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Backend DB and auth |
| `SECRET_KEY` | JWT signing |
| `CORS_ORIGINS` | Allowed frontend origins (e.g. `http://localhost:3000`) |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `MOONSHOT_API_KEY` | Optional here — can be set in Admin → Settings and stored in `app_config` |
| `RESEND_API_KEY`, `FROM_EMAIL` | Email digests/alerts |
| `ZOHO_*` | Optional Zoho CRM sync |
| `GUPSHUP_*` | Optional WhatsApp |

---

## Deployment (High Level)

- **Backend:** Run as a single process (e.g. `uvicorn app.main:app --host 0.0.0.0 --port 8000`). Can be deployed on **Railway**, **Render**, **Fly.io**, or any host that runs Docker/Python. Use the same `Dockerfile` in `backend/`.
- **Frontend:** Build with `npm run build`, then `npm run start`, or deploy to **Vercel** (set `NEXT_PUBLIC_API_URL` to your backend URL).
- **Cron:** Point your scheduler (e.g. cron.org, Render cron, or Vercel cron) to:
  - `GET /api/cron/digest-morning`
  - `GET /api/cron/digest-afternoon`
  - `GET /api/cron/digest-evening`
  (with auth/cron secret if you add one.)
- **Supabase:** Already hosted; ensure migrations are applied and RLS/policies allow the service role for backend.

---

## How to Explain This to Anyone (Elevator Pitch)

"We have an internal **Sales Intelligence** app. You upload a pipeline CSV from our CRM. The app uses AI to score leads, flag overdue follow-ups and notes that need action, and send **smart alerts** and **daily digests** to the team over Telegram or email. Admins configure which AI models to use and store API keys in the app, so we're not dependent on a single provider. Everything is designed so reps and managers can act on the right leads at the right time."

---

## Support & Ownership

- **Repo:** Onsite (sales-intelligence-system). Private — ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED.
- **Docs:** This README + `GAMMA-SLIDES-CONTENT.md` for slide deck context.
- For technical issues or feature requests, use your internal process (e.g. GitHub issues or team channel).
