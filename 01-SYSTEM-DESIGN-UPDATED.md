# Sales Intelligence Agent System — Updated Design Document

**Version:** 2.0 (Updated with production-readiness fixes)
**Client:** Onsite Teams
**Date:** February 2026
**Stack:** LangGraph + Claude API + React + Supabase + Zoho CRM

---

## 1. What We Are Building

An AI-powered sales intelligence system that sits on top of Zoho CRM and does three things:

| # | Function | What It Means |
|---|----------|--------------|
| 1 | **Prioritize** | Tells each sales rep exactly which lead to call first, second, third — with reasons |
| 2 | **Research & Advise** | Rep clicks a lead → AI researches the company, reads all CRM notes, and suggests how to close the deal |
| 3 | **Alert & Report** | Daily morning briefs, stale lead alerts, weekly performance reports — via WhatsApp + Email + Dashboard |

20 sales reps get their own dashboard. Managers see all. Founder sees everything + analytics.

**Key principle:** Zoho CRM remains the source of truth. Reps keep working in Zoho. This system is the intelligence layer on top.

---

## 2. Tech Stack (Final)

| Layer | Tool | Why This One | Est. Cost/Month |
|-------|------|-------------|----------------|
| Agent Brain | LangGraph (Python) | Best for stateful, multi-step AI workflows with branching | Free (open source) |
| LLM (Primary) | Claude API (Sonnet 4.5) | Best reasoning + cost efficient | $30-80 |
| LLM (Fallback) | GPT-4o via OpenAI API | Auto-fallback when Claude is down | $10-20 (backup only) |
| LLM (Cheap tasks) | Claude Haiku 4.5 | Lead scoring, stale detection, simple classification | Included in $30-80 |
| Backend API | FastAPI (Python) | Async, fast, perfect for AI + API serving | Free |
| Database | Supabase (PostgreSQL + pgvector) | Auth, real-time, RLS, vector search for similar deals | Free-$25 |
| Frontend | React + Tailwind + shadcn/ui | Modern, fast, mobile-ready | Free |
| Auth & Roles | Supabase Auth | Email login, role-based access, built-in | Included |
| CRM Data | Zoho CRM REST API v8 | Full access to leads, deals, notes, activities | Included in plan |
| WhatsApp | Gupshup (primary) or Twilio | Reliable in India, API-friendly | Rs 2-5K |
| Email Alerts | Resend | Transactional emails, generous free tier | Free-$20 |
| Hosting | Railway (backend) + Vercel (frontend) | Simple deploy, auto-scaling | $10-30 |
| Monitoring | LangSmith | Trace every AI decision, debug easily | Free tier |
| Scheduler | APScheduler (in-process) | Runs agent pipeline on schedule | Free |
| Vector DB | Supabase pgvector | Similar deal matching via embeddings | Included |

**Total estimated infra cost:** Rs 5,000-12,000/month
**Total estimated AI cost (optimized):** $30-80/month for 20 reps, ~500 leads

---

## 3. How Data Flows

```
Zoho CRM (source of truth)
    │
    ▼ [Delta sync every 2 hours via Modified_Time filter]
    │
Supabase PostgreSQL (mirror + enrichment store)
    │
    ├──▶ LangGraph Daily Agent (7:30 AM) ──▶ Scores, Rankings, Briefs
    │                                            │
    │                                            ├──▶ WhatsApp (morning brief)
    │                                            └──▶ Email (morning brief)
    │
    ├──▶ LangGraph Research Agent (on-demand) ──▶ Intel Cards
    │
    ├──▶ LangGraph Assignment Agent (webhook) ──▶ Auto-assign + WhatsApp alert
    │
    ├──▶ LangGraph Weekly Agent (Monday 8 AM) ──▶ Email report
    │
    └──▶ FastAPI ──▶ React Dashboard (WebSocket for real-time)
```

| # | Step | Detail |
|---|------|--------|
| 1 | Zoho CRM Delta Sync | Every 2 hours: fetch ONLY records modified since last sync using `Modified_Time` filter. Upsert on `zoho_lead_id`. |
| 2 | Store in Supabase | Raw CRM data stored in PostgreSQL. Historical data preserved. Embeddings generated for deal matching. |
| 3 | LangGraph Agent Runs | Scheduled at 7:30 AM daily. Agent scores leads, ranks priority, generates briefs. |
| 4 | Enriched Data Stored | AI scores, priority rankings, recommendations saved back to Supabase. |
| 5 | Dashboard Reads | React dashboard pulls enriched data from Supabase via FastAPI. Real-time via WebSocket. |
| 6 | Alerts Sent | Morning brief → WhatsApp + Email. Urgent alerts → WhatsApp instantly. |
| 7 | Rep Takes Action | Rep calls lead, logs notes in Zoho CRM. Next sync picks up the new data. |

---

## 4. Changes from v1.0

| Issue in v1.0 | Fix in v2.0 | Why It Matters |
|--------------|------------|---------------|
| No Zoho rate limit handling | Delta sync with `Modified_Time` filter + exponential backoff | Zoho API has 5000 requests/day limit. Full sync every 2 hours will hit it. |
| No OAuth token refresh | Auto-refresh with `refresh_token` before expiry | Zoho tokens expire in 1 hour. System will silently stop syncing without this. |
| "Match Past Wins" underspecified | pgvector embeddings + cosine similarity on deal attributes | Without concrete similarity logic, AI will produce garbage matches. |
| 6-week timeline unrealistic | Revised to 10 weeks with buffer | Single dev can't build 4 agents + 5 screens + integrations in 6 weeks. |
| No AI fallback strategy | Auto-fallback: Claude → GPT-4o. Cached "last known good" briefs. | If Claude is down at 7:30 AM, reps get no morning brief. Unacceptable. |
| WhatsApp approval not planned | Start Meta Business Verification in Week 1 | Takes 1-3 weeks for template approval. Can't start in Week 4. |
| No lead deduplication | Upsert on `zoho_lead_id` with conflict resolution | 2-hour sync will create duplicates without upsert logic. |
| No database indexes | Indexes on all query-hot columns | Dashboard will get slow with 500+ leads x 20 reps without indexes. |
| No error handling for agents | Retry logic, dead letter queue, fallback briefs | Production system needs graceful failure, not silent crashes. |
| No logging/audit trail | Every AI decision logged with input/output/cost | Founder needs to trust the system. Traceability is non-negotiable. |

---

## 5. What to Read Next

| Document | What It Covers |
|----------|---------------|
| `02-ZOHO-INTEGRATION-SPEC.md` | Delta sync, OAuth refresh, rate limits, API endpoints, field mapping |
| `03-DATABASE-SCHEMA.md` | All tables, indexes, RLS policies, pgvector setup, migration SQL |
| `04-LANGGRAPH-AGENTS-SPEC.md` | All 4 agents: nodes, state, prompts, error handling, fallbacks |
| `05-BUILD-PLAN-REVISED.md` | 10-week timeline, weekly deliverables, dependencies, risk register |
