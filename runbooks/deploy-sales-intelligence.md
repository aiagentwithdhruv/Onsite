# Runbook: Deploy Sales Intelligence System

> Step-by-step deployment of the Onsite Sales Intelligence System to production.

---

## Pre-Deployment Checklist

Before deploying, confirm ALL of these:

- [ ] Zoho CRM OAuth credentials obtained from Sumit
  - Client ID, Client Secret, Refresh Token
  - Redirect URI registered in Zoho API console
- [ ] Supabase production project ready (`jfuvhaampbngijfxgnnf`)
  - All 11 migrations run in order (001 → 011)
  - Dhruv seeded as admin (migration 002)
- [ ] Environment variables prepared:
  ```
  SUPABASE_URL=https://jfuvhaampbngijfxgnnf.supabase.co
  SUPABASE_ANON_KEY=<from Supabase dashboard>
  SUPABASE_SERVICE_ROLE_KEY=<from Supabase dashboard>
  ANTHROPIC_API_KEY=<Claude API key>
  OPENAI_API_KEY=<GPT-4o fallback>
  ZOHO_CLIENT_ID=<from Zoho>
  ZOHO_CLIENT_SECRET=<from Zoho>
  ZOHO_REFRESH_TOKEN=<from Zoho>
  TELEGRAM_BOT_TOKEN=<for alert delivery>
  RESEND_API_KEY=<for email delivery>
  GUPSHUP_API_KEY=<for WhatsApp, optional>
  DISCORD_WEBHOOK_URL=<for Discord alerts, optional>
  ```
- [ ] Domain/subdomain decided for frontend (e.g., `intelligence.onsiteteams.com`)

---

## Step 1: Run Database Migrations

```bash
# Connect to Supabase SQL Editor or use psql
psql "postgresql://postgres.jfuvhaampbngijfxgnnf@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

# Run migrations in order
\i database/001_initial_schema.sql
\i database/002_seed_admin.sql
# ... through 011
\i database/011_app_config.sql
```

**Verify:** Check that all tables exist:
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

Expected tables: users, leads, lead_scores, lead_notes, lead_activities, lead_research, daily_briefs, weekly_reports, alerts, ai_usage_log, sync_state, pipeline_runs, intelligence_cache, dashboard_summary, agent_profiles, app_config

---

## Step 2: Deploy Backend to Railway

```bash
cd sales-intelligence/backend

# Railway CLI
railway login
railway init  # or railway link if project exists
railway up

# Set environment variables
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_ANON_KEY=...
railway variables set SUPABASE_SERVICE_ROLE_KEY=...
railway variables set ANTHROPIC_API_KEY=...
# ... all env vars from checklist
```

**Verify:** Hit the health endpoint:
```bash
curl https://<railway-url>/health
# Expected: {"status": "ok"}
```

---

## Step 3: Deploy Frontend to Vercel

```bash
cd sales-intelligence/frontend-next

# Vercel CLI
vercel login
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_SUPABASE_URL
# NEXT_PUBLIC_SUPABASE_ANON_KEY
# NEXT_PUBLIC_API_URL=https://<railway-backend-url>
```

**Verify:** Open the deployed URL, confirm login page loads.

---

## Step 4: Configure Scheduled Jobs

The backend uses APScheduler. After deployment, verify cron jobs are running:

| Job | Schedule | Verify |
|-----|----------|--------|
| Daily Pipeline Agent | 7:30 AM IST | Check `pipeline_runs` table next morning |
| Delta Sync | Every 2 hours | Check `sync_state` table |
| Full Sync | 2:00 AM IST | Check `sync_state.last_full_sync` |
| Weekly Report | Monday 8:00 AM IST | Check `weekly_reports` table |
| Morning Digest | 7:30 AM IST | Check Telegram/email delivery |
| Afternoon Digest | 1:00 PM IST | Check delivery |
| Evening Digest | 6:00 PM IST | Check delivery |

---

## Step 5: Set Up Alert Delivery

### Telegram Bot
1. Create bot via @BotFather, get token
2. Set `TELEGRAM_BOT_TOKEN` env var
3. Each rep links their chat via `/api/alerts/telegram-link`

### Email (Resend)
1. Set `RESEND_API_KEY` env var
2. Verify domain in Resend dashboard

### WhatsApp (Gupshup) — Optional
1. Set `GUPSHUP_API_KEY` env var
2. Configure WhatsApp Business number

---

## Post-Deployment Verification

Run these checks after deployment:

1. **Login flow:** Open frontend → login with Dhruv's email → verify dashboard loads
2. **CSV upload:** Upload `Onsite_Entire_Leads.csv` → verify Intelligence tab populates
3. **Alert delivery:** Go to Admin → test Telegram send → confirm message received
4. **API health:** `curl <backend>/health` returns 200
5. **Agent run:** Trigger `/api/cron/morning-digest` manually → check delivery

---

## Rollback Procedure

If something breaks after deployment:

### Backend Rollback
```bash
# Railway: redeploy previous version
railway deployments
railway redeploy <previous-deployment-id>
```

### Frontend Rollback
```bash
# Vercel: instant rollback
vercel rollback
```

### Database Rollback
- Migrations are additive (no DROP statements)
- If a migration fails: fix the SQL and re-run
- For data issues: Supabase has point-in-time recovery (Pro plan)

---

## Contacts for Deployment Issues

| Issue | Contact |
|-------|---------|
| Zoho CRM credentials | Sumit (sumit@onsiteteams.com, +91 9560209605) |
| Supabase issues | Dhruv (dhruv.tomar@onsiteteams.com) |
| Railway/Vercel issues | Dhruv |
| Alert delivery | Check service status pages (Telegram, Resend, Gupshup) |
