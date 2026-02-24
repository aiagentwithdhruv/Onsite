# Sales Intelligence System — Deployment

Quick reference for deploying the backend and frontend. Use this after reading the main [README.md](./README.md).

---

## Backend (FastAPI)

- **Option A — Docker**  
  From `backend/`:  
  `docker build -t sales-intel-api . && docker run -p 8000:8000 --env-file .env sales-intel-api`

- **Option B — Railway / Render / Fly.io**  
  Connect repo, set root to `sales-intelligence-system/backend` (or build from `backend/`).  
  Set env vars from `backend/.env.example`.  
  Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

- **CORS:** Set `CORS_ORIGINS` to your frontend URL(s), e.g. `https://your-app.vercel.app`

---

## Frontend (Next.js)

- **Option A — Vercel**  
  Connect repo, set root to `sales-intelligence-system/frontend-next`.  
  Add env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL=https://your-backend-url`

- **Option B — Manual**  
  `npm run build && npm run start` (set `NEXT_PUBLIC_API_URL` in `.env.production` or build env)

---

## Cron (digests)

Call these at 8 AM, 2 PM, 6 PM IST (or your chosen times):

- `GET https://your-backend-url/api/cron/digest-morning`
- `GET https://your-backend-url/api/cron/digest-afternoon`
- `GET https://your-backend-url/api/cron/digest-evening`

Use cron-job.org, Render cron, or Vercel cron; optionally add a secret header and validate in the backend.

---

## Database

Run all SQL files in `database/` in order (001 through 011) in the Supabase SQL editor before going live.
