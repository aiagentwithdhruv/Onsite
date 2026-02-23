# Sales Intelligence System — AI Skill Context

> Everything an AI agent needs to work on, improve, or extend this system.
> Includes: architecture, codebase map, market research, competitor patterns, technical recipes, and best practices.

---

## System Identity

**What:** AI-powered sales intelligence layer on Zoho CRM for construction SaaS
**Who:** Onsite Teams (ABEYAANTRIX TECHNOLOGY) — 16 sales reps, ~500 leads
**Status:** BUILT, NOT DEPLOYED (locally verified on port 8000/3000)
**Blockers:** Zoho OAuth creds from client, Supabase production setup, Railway/Vercel deploy

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  Next.js 16 + Tailwind 4 + Recharts                │
│  10 pages, Supabase Auth, Axios → Backend           │
│  Port: 3000                                         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (JWT in header)
┌──────────────────────▼──────────────────────────────┐
│                    BACKEND                           │
│  FastAPI + LangGraph + APScheduler                  │
│  39 Python files, 40+ API endpoints                 │
│  Port: 8000                                         │
├─────────────────────────────────────────────────────┤
│  5 Agents:                                          │
│  ├── Daily Pipeline (LangGraph, 8 nodes, 7:30 AM)  │
│  ├── Research Agent (LangGraph, 6 nodes, on-demand) │
│  ├── Smart Assignment (async func, on webhook)      │
│  ├── Weekly Report (async func, Monday 8 AM)        │
│  └── Smart Alerts (rule engine, 14 rules, on CSV)   │
├─────────────────────────────────────────────────────┤
│  Delivery Channels:                                 │
│  Telegram → Discord → WhatsApp (Gupshup) → Email   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               DATA LAYER                             │
│  Supabase (PostgreSQL + pgvector)                   │
│  11 migrations, JSONB summaries (~1-2MB)            │
│  Project: jfuvhaampbngijfxgnnf                      │
│  Connection: aws-1-ap-south-1.pooler.supabase.com   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               DATA SOURCES                           │
│  Primary: CSV upload (Zoho CRM export) ← WORKING   │
│  Future: Zoho CRM API v8 (OAuth, webhooks) ← BLOCKED│
└─────────────────────────────────────────────────────┘
```

---

## Codebase Map

### Backend (`backend/app/`)

**Core:**
| File | What It Does |
|------|-------------|
| `main.py` | FastAPI app, CORS, lifespan, router registration |
| `core/config.py` | Pydantic Settings (Supabase, AI, Zoho, WhatsApp, Resend) |
| `core/auth.py` | JWT decode, user lookup (email-only works), role guards |
| `core/supabase_client.py` | Supabase client singletons (anon + service role) |
| `core/llm.py` | LLM factory, fallback chain, cost tracking, `tracked_llm_call()` |
| `core/llm_config.py` | API key resolution (DB first, then env), model selection |
| `core/llm_models.py` | 21 model definitions across 4 providers |

**Agents:**
| File | Framework | Schedule | Key Detail |
|------|-----------|----------|------------|
| `agents/daily_pipeline.py` | LangGraph 8-node | 7:30 AM IST | Haiku for scoring (batches of 20), Sonnet for briefs. HOT/WARM/COLD. Fallback to cold/10 on failure |
| `agents/research_agent.py` | LangGraph 6-node | On-demand | Parallel branches: web_research + analyze_notes. Sonnet for strategy. 15-30 sec response |
| `agents/assignment_agent.py` | Async function | On webhook | Haiku for assignment. Factors: capacity (<30), conversion rate, geography, industry match |
| `agents/weekly_report.py` | Async function | Monday 8 AM | Sonnet. 7-section report. Email to founder + managers |
| `agents/smart_alerts.py` | Rule engine | On CSV upload | 14 rules, NO LLM. Severity: critical/high/medium/info |

**API Routes (40+ endpoints):**
| Prefix | Key Endpoints |
|--------|--------------|
| `/api/auth` | login, logout, me |
| `/api/leads` | list (paginated), detail, quick action (called/won/lost), timeline |
| `/api/research` | trigger + get results |
| `/api/briefs` | today, history |
| `/api/alerts` | list, mark read, unread count, notification prefs, telegram link, test send |
| `/api/analytics` | rep-performance, pipeline-funnel, source-analysis, conversion-trends |
| `/api/intelligence` | CSV upload + compute, get/delete summary, deal-owners, team-attention |
| `/api/agents` | list profiles, get profile, add notes |
| `/api/admin` | users CRUD, sync status/trigger, AI usage, telegram config, LLM config |
| `/api/cron` | morning/afternoon/evening digest, generate-intelligence-briefs |

**Services:**
| File | Purpose |
|------|---------|
| `services/scheduler.py` | APScheduler: daily pipeline, delta sync (2h), full sync (2 AM), weekly report, digests |
| `services/zoho_sync.py` | OAuth refresh, rate limiting (tenacity), delta/full sync, upsert leads/notes/activities |
| `services/email.py` | Resend email |
| `services/whatsapp.py` | Gupshup + WhatsApp Cloud API |
| `services/telegram.py` | Telegram Bot API |
| `services/discord.py` | Discord webhooks |
| `services/alert_delivery.py` | Multi-channel delivery engine with batching + logging |
| `services/digests.py` | Morning/afternoon/evening digest builders |
| `services/intelligence_brief.py` | Brief generation from CSV data |

### Frontend (`frontend-next/src/`)

**Pages (10):**
| Page | What It Shows |
|------|-------------|
| Login | Supabase Auth |
| Dashboard Home | Greeting, stat cards, today's brief, priority call list, recent alerts |
| Leads | Paginated list with search, score/stage filters |
| Lead Detail | Timeline, research results, quick actions |
| Briefs | Today's brief + history |
| Alerts | Alert cards with severity badges |
| Analytics | Rep performance, pipeline funnel, source analysis, conversion trends (Recharts) |
| Intelligence | **8-tab dashboard** (Sales, Overview, Pipeline, Team, Sources, Aging, Trends, Deep Dive) — CSV upload powered |
| Agents | Rep profiles with performance stats, strengths/concerns, monthly history |
| Admin | User CRUD, role/deal_owner assignment, sync, AI usage, LLM provider management |

**Key Libs:**
| Package | Version | Purpose |
|---------|---------|---------|
| next | 16.1.6 | Framework |
| react | 19.2.3 | UI |
| @supabase/supabase-js | ^2.95.3 | Auth |
| recharts | ^3.7.0 | Charts |
| axios | ^1.13.5 | HTTP |
| papaparse | ^5.5.3 | CSV parsing |
| dexie | ^4.3.0 | IndexedDB cache |
| lucide-react | ^0.567.0 | Icons |

### Database (11 migrations)

| Migration | Tables/Changes |
|-----------|---------------|
| 001 | users, leads, lead_scores, lead_notes, lead_activities, lead_research, daily_briefs, weekly_reports, alerts, ai_usage_log, sync_state, pipeline_runs |
| 002 | Seed Dhruv as admin |
| 004 | intelligence_cache |
| 005 | dashboard_summary (JSONB) |
| 006 | agent_profiles |
| 007 | Extended alert columns (severity, title, agent_name, metadata) |
| 008 | users.deal_owner_name, dashboard_summary.summary_by_owner |
| 009 | Alert delivery channels (telegram_chat_id, notify_via_*, delivery log, link tokens) |
| 010 | Discord webhook support |
| 011 | app_config key-value table (LLM keys, model selection) |

---

## Known Issues & Tech Debt

| Issue | Severity | Fix |
|-------|----------|-----|
| Supabase user lookup: auth_id → 400, id → 406 | Medium | Only email lookup works. Keep using email. |
| Weekly report column mismatches (`stage` vs `status`, `company` vs `company_name`) | Medium | Align with actual leads table schema |
| `v_rep_performance` view referenced but not in migrations | High | Create view in new migration or inline the query |
| pgvector similarity NOT implemented | Medium | Research agent uses SQL heuristic instead. Add embeddings later |
| WebSocket real-time updates NOT implemented | Low | Polling works fine for now |
| Hydration mismatch warning | Cosmetic | Browser extension related |
| sw.js 404 console spam | Cosmetic | No service worker registered |

---

## Competitor Intelligence — What Top Tools Do

### What to Learn From Each

| Tool | What They Do Well | Our Takeaway |
|------|------------------|-------------|
| **Gong** ($50K+/yr) | Conversation intelligence, deal scoring from call signals, coaching playlists | Build "winning behavior" benchmarks from top reps |
| **Clari** ($100+/user/mo) | Time-series deal tracking, pipeline velocity, RevOps controls | Track how deals CHANGE over time, not just snapshots |
| **People.ai** ($50+/user/mo) | Zero-input activity capture, relationship mapping, buying group detection | Multi-stakeholder tracking as deal health signal |
| **6sense** ($55K+/yr) | Intent data, buying stage classification, predictive scoring | Classify leads: Awareness → Consideration → Decision |
| **ZoomInfo** ($15K+/yr) | Firmographic + technographic data, executive movement tracking | New leadership = buying signal. Track CTO/VP changes |
| **Apollo.io** ($49-119/user/mo) | Aggressive free tier, advanced filtering, parallel dialer | Low-cost entry point drives adoption |
| **Salesloft** ($125+/user/mo) | Cadence automation, key moment detection in calls | Structured multi-touch sequences with timing rules |
| **Outreach** ($100+/user/mo) | Next-best-action AI, "plays" triggered by signals | Pre-built playbooks triggered by deal signals |
| **HubSpot** ($20-150/seat/mo) | Breeze AI, free CRM, daily digest email | Credit-based AI pricing, daily digest pattern |
| **Freshsales** ($9-59/user/mo) | Freddy AI scoring, contact journey, low price point | Journey timeline + contextual recommendations inside CRM |
| **Zoho Zia** (included) | Win probability (engagement velocity + stakeholder involvement + competitive signals + historical rates + team capacity) | Steal this win probability formula for our scoring |

### Our Competitive Edge
- **10-100x cheaper** than Gong/Clari/6sense
- **Construction-specific intelligence** (seasonal patterns, project signals, RERA/GST context)
- **Zoho CRM native** (most competitors target Salesforce/HubSpot)
- **India-first** (INR pricing, Hindi support, WhatsApp delivery)

---

## Lead Scoring Model

### Recommended Architecture (Hybrid LLM + Rules)

```
TOTAL SCORE = (Fit × 0.4) + (Intent × 0.35) + (Engagement × 0.25)

Fit Score (0-100):
  Company size match:     0-25 (construction, 50-500 employees = 25)
  Industry match:         0-25 (infrastructure/commercial = 25)
  Revenue/budget match:   0-25 (10M-500M revenue = 25)
  Tech stack compat:      0-25 (using Excel/paper = 25, competitor = 10)

Intent Score (0-100):
  Website behavior:       0-30 (pricing page = 30, features = 15, blog = 5)
  Content engagement:     0-25 (demo request = 25, whitepaper = 15, webinar = 10)
  Third-party intent:     0-25 (researching construction software)
  Company events:         0-20 (funding = 20, leadership change = 15, expansion = 10)

Engagement Score (0-100):
  Email responsiveness:   0-30
  Meeting attendance:     0-30
  Multi-thread:           0-25 (multiple contacts from same company)
  Recency:               0-15 (last activity within 7 days = 15)
```

### Construction-Specific Buy Signals

**Hot (Score 80-100, act within 24 hours):**
- Won a large new project → needs tools to manage it
- Hiring project managers or IT staff → tech readiness
- Compliance deadline approaching → urgent need
- Currently using spreadsheets for tracking → acute pain
- Multiple cost overruns → proven need
- Requested demo after visiting pricing page

**Warm (Score 50-79, nurture 30-60 days):**
- Attended construction tech trade show
- New leadership (VP Ops, CTO)
- Growing residential → commercial
- Expanding to new regions
- Searching "construction project management software"

**Cold (Score 0-49, automated drip only):**
- No engagement after 3+ touches
- < 10 employees (too small)
- Wrong industry segment
- Already on competitor with multi-year contract

---

## Sales Cycle Intelligence

### Construction SaaS Cycle
- **Average cycle:** 147 days (nearly 5 months)
- **Average deal size:** $89,300 ACV
- **Win rate:** ~16%
- **Pipeline velocity:** $2,456/day

### Stage Mapping
```
Stage 1: Discovery (Days 1-30)
  Key Q: "How many active projects do you manage?"

Stage 2: Education (Days 30-60)
  Key action: Calculate their cost of inefficiency

Stage 3: Technical Evaluation (Days 60-90)
  Key action: Pilot on one project. Get a champion.

Stage 4: Business Case (Days 90-120)
  Key action: ROI doc for owner/CFO

Stage 5: Negotiation & Close (Days 120-147)
  Key action: Handle budget cycle objections
```

### Seasonal Buying Patterns
```
Q1 (Jan-Mar): PRIME SEASON — Budget allocation, pre-season prep. PUSH HARD.
Q2 (Apr-Jun): DIFFICULT — Peak construction, teams too busy. Pipeline build only.
Q3 (Jul-Sep): MIXED — Mid-year reviews, some evaluating for next year.
Q4 (Oct-Dec): SECOND WINDOW — Construction slows, "use it or lose it" budgets.
```

**Key insight:** Best selling windows are Q1 + Q4 when teams have time to evaluate and implement.

---

## Morning Brief Best Practices

### What Reps Need at 7:30 AM (Priority Order)

1. **Today's Agenda** (30 seconds):
   - Meetings with context (who, stage, key points from last interaction)
   - Overdue tasks (follow-ups, proposals, calls)
   - Time-sensitive opportunities

2. **Hot Signals Overnight** (1 minute):
   - Website visitors after hours
   - Email replies needing response
   - New inbound demo requests
   - Deal stage changes

3. **Pipeline Snapshot** (15 seconds):
   - Pipeline value vs quota
   - Deals closing this week/month with win probability
   - Deals at risk (stalled, negative sentiment)

4. **Coaching Nudge** (10 seconds):
   - One specific tip based on their data
   - Example: "Your response time to hot leads was 4.2 hours. Top performers: <15 minutes."

**Format:** Plain text, <300 words, mobile-friendly, scannable bullets, clickable CRM links.

---

## Alert Strategy

### Alert Priority Matrix

```
CRITICAL (Push + SMS, max 3/day):
  - Pricing page visited 3+ times in 7 days
  - Deal champion changed jobs
  - Contract renewal <30 days with no engagement
  - Competitor mentioned in prospect activity

HIGH (Push notification):
  - New inbound demo request
  - Deal stalled >2x average stage time
  - Multiple stakeholders from same account
  - Meeting no-show

MEDIUM (Morning brief):
  - Weekly deal score changes
  - New contacts added to accounts
  - Upcoming tasks
  - Team metrics

INFO (Dashboard only):
  - Top performer recognition
  - Revenue milestones
  - Pipeline health updates
```

---

## Technical Recipes

### LLM Prompting Patterns

**Lead Scoring (Haiku, batch of 20):**
```
You are a B2B sales intelligence analyst for construction management SaaS.
Score each lead 0-100 and classify as HOT/WARM/COLD.

SCORING CRITERIA:
1. ICP Fit (0-40): Construction company, 50-500 employees, $10M-$500M revenue
2. Intent (0-35): Demo requests, pricing visits, content downloads
3. Engagement (0-25): Email responses, meetings, multi-stakeholder

Return JSON array: [{lead_id, score_label, score_numeric, reasoning, next_action}]
```

**Deal Strategy (Sonnet):**
```
Generate close strategy for this construction SaaS deal.
Think step by step:
1. Deal velocity (faster/slower than 147-day average?)
2. Stakeholder engagement (who's involved, who's missing?)
3. Competitive threats (any competitor mentions?)
4. Budget alignment (sized right for their company?)
5. Overall health assessment

Output: approach, talking_points, objection_handling, pricing_suggestion, next_step, risk_factors
```

**Morning Brief (Sonnet, per rep):**
```
Generate personalized morning brief. Under 300 words. WhatsApp-friendly.
Start with #1 priority action. List meetings with 1-sentence context.
Flag deals needing attention. One coaching tip from their data.
```

### Zoho CRM Integration Patterns

**OAuth Token Manager:**
- Access token: valid 1 hour, refresh with 5-min buffer
- Max 15 active tokens per refresh token
- Max 10 refresh requests per 10-minute window
- Thread-safe with Lock

**Rate Limiting:**
- Min 4,000 requests/day/org, max 25,000 or 500/user license
- GET: max 200 records/request
- Write: max 100 records/request
- Use `If-Modified-Since` for delta sync
- Use Composite API to batch 5 calls into 1

**Sync Strategy (Hybrid):**
```
PRIMARY: Webhooks (real-time, <1 sec)
  Max 6 per workflow rule, max 10 fields per webhook

FALLBACK: Polling every 15 min
  GET /crm/v8/Deals?modified_since={last_sync}

NIGHTLY: Full reconciliation at 2 AM
  Compare all records, rebuild scores/embeddings
```

### pgvector Similarity (NOT YET IMPLEMENTED)

```sql
-- Schema for deal embeddings
ALTER TABLE deals ADD COLUMN deal_embedding vector(1536);
CREATE INDEX ON deals USING hnsw (deal_embedding vector_cosine_ops);

-- Find similar won deals
SELECT *, 1 - (deal_embedding <=> query_embedding) AS similarity
FROM deals
WHERE won = true
  AND 1 - (deal_embedding <=> query_embedding) > 0.75
ORDER BY deal_embedding <=> query_embedding
LIMIT 5;
```

**Embedding text format:**
```
Company: {name}, Industry: {industry}, Size: {employees} employees,
Deal Amount: ${amount}, Products: {products}, Pain Points: {pain_points},
Decision Makers: {titles}, Sales Cycle: {days} days, Region: {region}
```

### Dashboard UX Pattern

```
TOP ROW:    KPI Cards (5-6 max)
            [Pipeline] [Quota %] [Closing This Month] [Win Rate] [Avg Deal] [Speed to Lead]

MIDDLE:     Pipeline Funnel Visualization
            Prospect → Qualified → Proposal → Negotiate → Won
            $120K      $340K       $220K      $180K      $95K

BOTTOM-L:   Deals at Risk          BOTTOM-R:   Activity Feed
            - Deal A: Stalled 14d              - 10:30 Email from...
            - Deal B: No exec                  - 09:15 Meeting w/...
```

---

## Performance Measurement (Non-Creepy)

### Measure (Outcomes)
- Pipeline coverage ratio (pipeline / quota — healthy is 3-4x)
- Win rate by deal size and segment
- Average deal cycle time vs team benchmark
- Activity-to-outcome ratios (meetings per demo, demos per close)
- Speed to lead (time from inbound to first contact)
- Deal progression rate (% advancing each week)

### Don't Measure (Surveillance)
- Keystroke tracking or screen recording
- Exact minutes in CRM
- GPS location
- Personal social media usage

### Present As
- Trends (weekly rolling averages), not daily snapshots
- Team benchmarks, not public rankings
- Coaching opportunities, not punishment
- Self-serve dashboards first, manager drill-down only when coaching

---

## Next Steps (Prioritized)

### Phase 1: Deploy (Week 1-2)
1. Get Zoho CRM OAuth credentials from Sumit
2. Run all 11 migrations on Supabase production
3. Deploy backend to Railway, frontend to Vercel
4. Configure APScheduler cron jobs
5. Set up Telegram bot for alert delivery

### Phase 2: Fix & Polish (Week 3-4)
6. Fix weekly report column mismatches
7. Create missing `v_rep_performance` view
8. Test end-to-end Zoho sync (delta + full)
9. Configure WhatsApp (Gupshup) credentials
10. Set up Resend for email delivery

### Phase 3: Enhance (Week 5-8)
11. Implement pgvector deal similarity
12. Add seasonal intelligence layer
13. Build next-best-action recommendations
14. Add pipeline forecasting (ML model)
15. Implement WebSocket real-time updates

### Phase 4: Advanced (Week 9-10)
16. Conversation intelligence integration
17. Competitive mention tracking
18. Self-improving scoring models (feedback loop)
19. Multi-language morning briefs (Hindi)

---

## Key CRM Fields (Zoho Export CSV)

```
lead_name, deal_owner, lead_status, sale_done, sale_done_date,
annual_revenue (Rs. format), price_pitched (Rs. format),
demo_done, demo_booked, lead_source, state_mobile, region,
user_date, last_touched_date_new, company_name, sales_stage,
is_prospect, lead_owner_manager, pre_qualification, Team_size,
user_profession, call_disposition, campaign_name, lead_notes, notes_date
```

**Revenue parsing:** Handle "Rs. 42,000.00" format → strip Rs., commas, parse float
**Revenue counting:** Only from `sale_done=1` records
**Primary field:** `deal_owner` (NOT `lead_owner`) for all analytics

---

## Self-Update Rules

### After Every Coding Session
1. If you fixed a bug → add to Known Issues table with fix description
2. If you added an endpoint → update the API Routes table
3. If you changed an agent → update the Agents table (framework, schedule, key detail)
4. If you added a migration → update the Database migrations table
5. If you discovered a new pattern → add to Technical Recipes section
6. If you changed frontend pages → update the Pages table

### After Every Deployment
1. Update "Current state" from "NOT DEPLOYED" to deployed URLs
2. Update Blockers list (remove resolved, add new)
3. Test all delivery channels (Telegram, Discord, WhatsApp, Email), record which work
4. Update LOADOUT.md changelog with deployment date

### After Market Changes
1. New sales intelligence tool launches → add to Competitor Intelligence table + `knowledge/sales-intelligence-tools.md`
2. Zoho CRM API changes → update Zoho Integration Patterns in Technical Recipes
3. Construction market data updates → update Sales Cycle Intelligence + `knowledge/construction-market.md`
4. New scoring model research → update Lead Scoring Model section

### Cross-File Updates
When updating this file, also check:
- `../LOADOUT.md` — version bump, changelog entry
- `../.claude/CLAUDE.md` — if architecture or known issues changed
- `../knowledge/sales-intelligence-tools.md` — if competitor data changed

---

## File Structure

```
sales-intelligence-system/
├── SKILL.md                        ← THIS FILE
├── 01-SYSTEM-DESIGN-UPDATED.md     ← Architecture v2.0
├── 02-ZOHO-INTEGRATION-SPEC.md     ← Zoho API spec
├── 03-DATABASE-SCHEMA.md           ← All tables + migrations
├── 04-LANGGRAPH-AGENTS-SPEC.md     ← Agent specifications
├── 05-BUILD-PLAN-REVISED.md        ← 10-week plan
├── PROGRESS.md                     ← Current build status
├── DEPLOY.md                       ← Deployment instructions
├── GAMMA-SLIDES-CONTENT.md         ← 10-slide deck content
├── backend/
│   ├── requirements.txt            ← Python deps (FastAPI, LangGraph, etc.)
│   ├── Dockerfile
│   └── app/
│       ├── main.py                 ← FastAPI entry
│       ├── core/                   ← Config, auth, LLM, Supabase
│       ├── agents/                 ← 5 AI agents
│       ├── api/routes/             ← All API endpoints
│       ├── services/               ← Zoho, email, WhatsApp, Telegram, Discord
│       └── models/                 ← Pydantic schemas
├── frontend-next/
│   ├── package.json
│   └── src/
│       ├── app/                    ← 10 pages (Next.js App Router)
│       ├── components/             ← Header, Sidebar, ScoreBadge
│       ├── contexts/               ← AuthContext
│       └── lib/                    ← API client, types, utils, Supabase, Dexie
└── database/
    ├── 001_initial_schema.sql      ← Core tables
    ├── 002-011                     ← Progressive migrations
    └── (run in order on Supabase)
```
