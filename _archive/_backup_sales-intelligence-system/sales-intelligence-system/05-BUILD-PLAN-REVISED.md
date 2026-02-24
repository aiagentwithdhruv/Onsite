# Build Plan — Revised (10 Weeks)

**Why 10 weeks instead of 6:** The original 6-week plan doesn't account for Zoho API integration complexity, WhatsApp Business approval timeline, prompt iteration with real data, and the fact that there are 4 separate AI agents + 5 dashboard screens + 3 integration APIs (Zoho, WhatsApp, Email).

---

## Pre-Week 0: Kickoff (Before Development Starts)

**Owner: Client (Onsite Teams)**

- [ ] Get Zoho CRM API credentials (client_id, client_secret, authorization_code)
- [ ] Confirm Zoho CRM plan (need to know API rate limits)
- [ ] Start Meta Business Verification for WhatsApp Business API (takes 1-3 weeks)
- [ ] Register Gupshup account + submit WhatsApp message templates for approval
- [ ] Provide list of all 20 sales reps: name, email, phone, team, Zoho user ID
- [ ] Provide list of managers + founder with same details
- [ ] Confirm: what Zoho modules are being used? (Leads vs Deals vs both?)
- [ ] Confirm: what are the current lead stages in Zoho? (need exact stage names)
- [ ] Confirm: what lead sources exist in Zoho?

**Owner: Developer**
- [ ] Set up Supabase project
- [ ] Set up Railway account
- [ ] Set up Vercel account
- [ ] Get Claude API key (Anthropic)
- [ ] Get OpenAI API key (fallback)
- [ ] Set up LangSmith account
- [ ] Set up Resend account (email)

---

## Week 1-2: Foundation + Zoho Sync

### Week 1: Backend + Database
- [ ] Create all Supabase tables (copy SQL from `03-DATABASE-SCHEMA.md`)
- [ ] Enable pgvector extension
- [ ] Configure RLS policies
- [ ] Set up FastAPI project structure
- [ ] Implement Supabase client + auth middleware
- [ ] Build user authentication endpoints (login, logout, me)
- [ ] Build role-based access middleware
- [ ] Deploy FastAPI to Railway (basic health check endpoint)

### Week 2: Zoho Integration
- [ ] Implement Zoho OAuth flow (authorize + token refresh)
- [ ] Build delta sync: leads module
- [ ] Build delta sync: notes module
- [ ] Build delta sync: activities module
- [ ] Build delta sync: deals module (if using)
- [ ] Build sync scheduler (APScheduler: delta every 2h, full at 2AM)
- [ ] Build sync state tracking (sync_state table)
- [ ] Implement rate limit handling + exponential backoff
- [ ] Set up Zoho webhook for new leads
- [ ] Test with real Zoho data: verify all fields map correctly

**Deliverable:** Zoho data flowing into Supabase every 2 hours. Developer can query Supabase and see real CRM data.

---

## Week 3-4: AI Agent Layer

### Week 3: Daily Pipeline Agent
- [ ] Set up LangGraph project structure
- [ ] Implement shared LLM config (Haiku + Sonnet + fallback)
- [ ] Build Node 1: Fetch CRM Data (from Supabase, not Zoho directly)
- [ ] Build Node 2: Score Leads (Haiku, batched, with prompt)
- [ ] Build Node 3: Rank Priority (sort logic)
- [ ] Build Node 4: Detect Stale Leads (pure logic)
- [ ] Build Node 5: Detect Anomalies (Haiku)
- [ ] Build Node 6: Generate Briefs (Sonnet)
- [ ] Build Node 7: Save Results (Supabase write)
- [ ] Connect LangSmith for tracing
- [ ] Schedule agent to run at 7:30 AM daily
- [ ] Test with real data: are scores sensible? Are briefs readable?
- [ ] Iterate on prompts until scoring matches client's intuition

### Week 4: Research Agent
- [ ] Build Node 1: Gather CRM Context
- [ ] Build Node 2: Web Research (Claude + search API — Tavily or Perplexity)
- [ ] Build Node 3: Analyze Notes (Sonnet)
- [ ] Build Node 4: Match Past Wins (pgvector setup + similarity function)
- [ ] Generate embeddings for all existing WON deals
- [ ] Build Node 5: Generate Close Strategy (Sonnet)
- [ ] Build Node 6: Save & Display
- [ ] Build FastAPI endpoint: POST /api/research/{lead_id}
- [ ] Test: research 5 real leads. Is the close strategy useful?
- [ ] Iterate on research prompts

**Deliverable:** AI scores all leads every morning. Research agent generates intel card on demand. Both traceable in LangSmith.

---

## Week 5-6: Dashboard (Frontend)

### Week 5: Sales Rep Dashboard
- [ ] Set up React + Vite + Tailwind + shadcn/ui project
- [ ] Build login page with Supabase Auth
- [ ] Build layout with sidebar navigation
- [ ] Build "My Leads" page: leads table with AI score badges
- [ ] Build "Today's Call List" section: priority-ranked cards
- [ ] Build Lead Detail page: timeline, notes, AI score
- [ ] Add "Research This Lead" button → calls research API → shows loading → shows intel card
- [ ] Build Quick Actions: mark as Called / Not Reachable / Meeting / Won / Lost (syncs to Zoho)
- [ ] Build "My Stats" widget: calls, conversion, pipeline
- [ ] Deploy to Vercel
- [ ] Test with 2-3 real reps: is it usable?

### Week 6: Manager Dashboard + Analytics
- [ ] Build Team Overview page: rep cards with status (Green/Yellow/Red)
- [ ] Build Pipeline Funnel visualization
- [ ] Build Stale Leads Alert page with one-click reassign
- [ ] Build AI Insights Panel
- [ ] Build Analytics page: conversion trends chart, source analysis, leaderboard
- [ ] Build Revenue Forecast widget
- [ ] Build drill-down: click rep → see their lead list

**Deliverable:** Full dashboard live. Reps see their leads + AI scores. Managers see team overview + analytics.

---

## Week 7: Alerts + Assignment Agent

- [ ] Integrate Gupshup WhatsApp API (templates should be approved by now)
- [ ] Build morning brief delivery: WhatsApp + Email
- [ ] Build alert triggers: stale 7d, stale 14d, hot no-followup 3d
- [ ] Build escalation logic: stale 14d → rep + manager
- [ ] Build deal won/lost notifications
- [ ] Build Smart Assignment Agent (auto-assign new leads from webhook)
- [ ] Test assignment with 5 test leads: does it pick the right rep?
- [ ] Build Weekly Report Agent
- [ ] Schedule weekly report for Monday 8 AM
- [ ] Test email delivery of weekly report

**Deliverable:** Reps get WhatsApp morning brief. Alerts fire automatically. New leads auto-assigned.

---

## Week 8: Admin + Polish

- [ ] Build Admin Settings page: user management, role assignment
- [ ] Build Zoho connection settings (sync status, last sync time)
- [ ] Build alert settings (who gets what, via which channel)
- [ ] Mobile responsive pass on all screens
- [ ] Add WebSocket for real-time dashboard updates
- [ ] Add "Last synced X minutes ago" indicator on dashboard
- [ ] Error boundary components (graceful failure on frontend)
- [ ] Loading states for all async operations

**Deliverable:** Admin can manage users + settings. Dashboard works on mobile.

---

## Week 9: Testing + Prompt Tuning

- [ ] Load test: simulate 20 concurrent users on dashboard
- [ ] Test full daily pipeline with all 500 leads
- [ ] Review AI scores with client: do they match client's intuition?
- [ ] Tune scoring prompt based on feedback (2-3 iterations)
- [ ] Tune brief prompt: is it the right length for WhatsApp?
- [ ] Test research agent on 10 leads: are close strategies useful?
- [ ] Test all alert scenarios (stale, hot, new lead, deal won)
- [ ] Test role-based access: can a rep see another rep's data? (should be no)
- [ ] Test Zoho sync edge cases: deleted lead, merged lead, changed owner
- [ ] Verify cost tracking: is ai_usage_log accurate?
- [ ] Fix all bugs found

**Deliverable:** System stable under load. AI outputs validated by client.

---

## Week 10: Launch

- [ ] Training session with sales reps (30 min): how to use dashboard + research
- [ ] Training session with managers (30 min): team view + analytics
- [ ] Training session with founder (20 min): full overview + weekly report
- [ ] Monitor first live morning brief delivery (7:30 AM)
- [ ] Monitor first research agent usage
- [ ] Monitor Zoho sync health
- [ ] Monitor AI costs
- [ ] Go live for all 20 reps
- [ ] Set up alerting: if agent fails, notify developer
- [ ] Handoff: documentation, env vars, deployment process

**Deliverable:** Full system live. All 20 reps + managers + founder using it daily.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Zoho API rate limits hit during full sync | High | Medium | Delta sync reduces calls 80%. Monitor credits daily. |
| WhatsApp templates rejected by Meta | Medium | High | Submit templates in Week 0. Have email-only fallback. |
| AI scores don't match client intuition | Medium | High | Plan 2-3 prompt iteration cycles in Week 9. |
| Zoho has messy/inconsistent data | High | Medium | Build data cleaning layer. Handle nulls everywhere. |
| Real-time WebSocket scaling issues | Low | Medium | Start with polling (30s refresh). Add WebSocket in Week 8. |
| Client changes requirements mid-build | Medium | High | Freeze scope after Week 2. Track changes in separate backlog. |
| Claude API outage during morning brief | Low | High | GPT-4o fallback + cached last brief. |

---

## Dependencies (Critical Path)

```
Week 0: Zoho credentials + WhatsApp approval MUST start
    ↓
Week 1-2: Supabase + Zoho sync (backend foundation)
    ↓
Week 3-4: AI agents (need real data from Zoho sync)
    ↓
Week 5-6: Dashboard (needs API endpoints from backend)
    ↓
Week 7: Alerts (needs WhatsApp approval from Week 0)
    ↓
Week 8-9: Polish + testing
    ↓
Week 10: Launch
```

**Blocker alert:** If Zoho credentials are delayed, EVERYTHING shifts. If WhatsApp approval is delayed, alerts go email-only until approved.
