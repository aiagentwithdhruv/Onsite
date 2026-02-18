# Sales Intelligence System — Progress Summary

**Project:** Onsite Sales Intelligence  
**Location:** `Onsite/sales-intelligence-system`  
**Last updated:** Feb 18, 2025

---

## What’s built

### Backend (FastAPI)

| Area | Status | Notes |
|------|--------|------|
| **API** | Done | Auth, Leads, Research, Briefs, Alerts, Analytics, Admin |
| **Auth** | Done | Login/logout, `/me`, Supabase JWT validation |
| **Leads** | Done | List (paginated), detail, action, timeline |
| **Research** | Done | Trigger research by lead, status, results |
| **Briefs** | Done | Today’s brief, history, rep-specific |
| **Alerts** | Done | List, unread count |
| **Analytics** | Done | Rep performance, pipeline funnel, source analysis, conversion trends |
| **Admin** | Done | Users CRUD, sync status, trigger sync, AI usage |
| **Scheduler** | Done | Daily pipeline (7:30 AM), delta sync (every 2h), full sync (2 AM), weekly report (Mon 8 AM) |
| **Agents** | Done | `daily_pipeline`, `weekly_report`, `research_agent`, `assignment_agent` |
| **Services** | Done | `zoho_sync`, `email`, `whatsapp`, `scheduler` |
| **Config** | Done | Supabase, AI (Anthropic/OpenAI), Zoho, WhatsApp, Resend, LangSmith |

### Frontend (Next.js 16)

| Area | Status | Notes |
|------|--------|------|
| **App** | Done | Next.js 16, Tailwind 4, dark sidebar (zinc-900) + amber accent |
| **Auth** | Done | Supabase Auth + AuthContext, login page |
| **Pages** | Done | Dashboard home, Leads, Lead detail, Briefs, Analytics, Alerts, Admin, Settings |
| **API** | Done | `lib/api.ts` + Next.js rewrites `/api/*` → backend |
| **UI** | Done | Header, Sidebar, ScoreBadge, responsive layout |

### Database (Supabase)

| Area | Status | Notes |
|------|--------|------|
| **Schema** | Done | `database/001_initial_schema.sql` (users, leads, lead_scores, notes, activities, briefs, alerts, etc.) |
| **Setup** | Done | `setup_database.py` for schema + seed + test user |

---

## Run locally

### 1. Backend

```bash
cd Onsite/sales-intelligence-system/backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill Supabase + optional AI/Zoho/WhatsApp/Resend
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
```

Or from project root:

```bash
./Onsite/sales-intelligence-system/start-backend.sh
```

Backend: **http://localhost:8000**  
Health: **http://localhost:8000/health**

### 2. Frontend (Next.js)

```bash
cd Onsite/sales-intelligence-system/frontend-next
cp .env.example .env.local
# Set in .env.local: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, API_URL=http://localhost:8000
npm install
npm run dev
```

Frontend: **http://localhost:3000**

### 3. One-time DB setup

- In Supabase: run `database/001_initial_schema.sql` in SQL Editor (if not using RPC).
- Or run `python3 setup_database.py` from `Onsite/sales-intelligence-system` (uses `backend/.env` for Supabase URL + service key).

---

## Env checklist

| File | Required |
|------|----------|
| `backend/.env` | `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`; optional: AI, Zoho, WhatsApp, Resend |
| `frontend-next/.env.local` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `API_URL=http://localhost:8000` |

---

## Optional / not required for basic test

- **Zoho:** Sync and CRM features (needs client id/secret/refresh token).
- **AI keys:** Research and scoring (Anthropic/OpenAI).
- **WhatsApp/Resend:** Alerts delivery.

You can run and test UI + auth + leads list with only **Supabase** configured.

---

## Local run verification (Feb 18, 2025)

- **Backend:** Started with `uvicorn` on http://127.0.0.1:8000 — health check OK, scheduler started.
- **Frontend:** Next.js 16 (Turbopack) on http://localhost:3000 — `npm run dev` ready, `.env.local` created from example.
- **Note:** Replace placeholder Supabase values in `frontend-next/.env.local` to test login and API calls.
