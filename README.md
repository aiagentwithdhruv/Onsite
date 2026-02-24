# Onsite — AI-Powered Sales Intelligence & Automation

**Internal tools for Onsite Teams** — Construction Management Software

> ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED | [onsiteteams.com](https://www.onsiteteams.com)

---

## What This Does

Upload your CRM/pipeline CSV and the system:
- **Scores leads** Hot/Warm/Cold with AI-powered reasoning
- **Detects anomalies** — stale deals, missing follow-ups, pipeline risks
- **Sends smart alerts** to your team via Telegram, WhatsApp, and Email
- **Generates daily briefs** — personalized morning briefings per rep
- **Profiles agents** — performance analysis across 33 deal owners

Built for reps, team leads, and founders to act on leads faster.

---

## Project Structure

```
Onsite/
  sales-intelligence/            # AI Sales Intelligence System
    backend/                     # FastAPI + LangGraph agents (port 8000)
    frontend-next/               # Next.js 16 dashboard (port 3000)

  quotations/                    # Quotation generator + templates
    QuotationGenerator.gs        # Google Apps Script backend
    quotation-generator.html     # Web UI
    *.pdf / *.csv                # Generated quotations

  database/                      # Supabase SQL migrations (11 files)
  docs/
    design/                      # System specs (01-05)
    guides/                      # Progress, troubleshooting, quick-start
  scripts/                       # Utility scripts
  knowledge/                     # Market research, competitors, glossary
  runbooks/                      # Deployment guides
```

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
cd sales-intelligence/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill Supabase + AI keys
uvicorn app.main:app --port 8000 --reload
```

### Frontend

```bash
cd sales-intelligence/frontend-next
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_SUPABASE_URL, API_URL
npm run dev
```

- Backend: **http://localhost:8000** | Health: `/health`
- Frontend: **http://localhost:3000**

### Database Setup

Run migrations in Supabase SQL Editor from `database/` folder, or:

```bash
python3 scripts/setup_database.py
```

---

## Dashboard Pages

| Page | What It Shows |
|------|---------------|
| **Home** | Pipeline value, hot leads, priority call list, daily brief |
| **Intelligence** | CSV upload, KPIs, 8 analysis tabs, filters |
| **Leads** | Hot prospects + stale leads from pipeline analysis |
| **Agent Profiles** | 33 deal owners with performance, strengths, concerns |
| **Analytics** | Pipeline funnel, rep performance, source analysis, trends |
| **Alerts** | Smart alerts with severity, multi-channel delivery |
| **Briefs** | AI-generated daily briefings per user |
| **Settings** | LLM config, notification preferences |

---

## Alert Channels

| Channel | Status | Config |
|---------|--------|--------|
| Telegram | Working | Bot token + chat ID per user |
| WhatsApp | Ready | Meta Cloud API (direct, no BSP) |
| Email | Ready | Resend API |
| Discord | Ready | Webhook URL per user |

---

## Quotation Generator

Automated quotation/proforma invoice generator for the sales team.

- Auto-generate professional PDF quotations (INR & USD)
- Multiple plans: Business, Business+, Enterprise, White Label
- Add-ons: GPS, Tally, Zoho integrations
- Email to client + save to Google Drive

Files in `quotations/` folder.

---

## Team

| Name | Role |
|------|------|
| Dhruv Tomar | Founder / Admin |
| Sales Team (21 users) | Reps, Team Leads, Managers |

---

**Proprietary** — ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED. All rights reserved.

*Powered by [Onsite](https://www.onsiteteams.com) — Construction Management Software*
