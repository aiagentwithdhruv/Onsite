# Onsite Sales Intelligence — Next.js Frontend

Next.js 16 + Tailwind CSS frontend for the Sales Intelligence System. Connects to the FastAPI backend and Supabase Auth.

## Design

- **Dark sidebar** (zinc-900) with amber accent
- **Light main content** with cards and subtle borders
- **Responsive** layout with collapsible sidebar and mobile menu
- **Same features** as the Vite frontend: Dashboard, Leads, Lead Detail, Briefs, Analytics, Alerts, Admin, Settings

## Setup

1. **Env**

   ```bash
   cp .env.example .env.local
   ```

   Set in `.env.local`:

   - `NEXT_PUBLIC_SUPABASE_URL` — Supabase project URL  
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase anon key  
   - `API_URL` — Backend base URL (e.g. `http://localhost:8000`). Used by Next.js rewrites to proxy `/api/*` to the backend.

2. **Install & run**

   ```bash
   npm install
   npm run dev
   ```

   App: [http://localhost:3000](http://localhost:3000)

3. **Backend**

   Start the FastAPI backend (e.g. on port 8000). The frontend rewrites `/api/*` to `API_URL/api/*`, so the backend must serve routes under `/api` (e.g. `/api/auth`, `/api/leads`, …).

## Scripts

- `npm run dev` — Dev server (port 3000)
- `npm run build` — Production build
- `npm run start` — Run production build

## Wrapping with backend

- Backend runs separately (e.g. `uvicorn app.main:app --reload` in `backend/`).
- In development, set `API_URL=http://localhost:8000` in `.env.local`.
- For production, set `API_URL` to your deployed backend URL; Next.js rewrites will proxy API calls.
