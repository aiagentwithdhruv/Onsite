# Onsite — Automation Master Plan

> Created: March 2, 2026
> Goal: Automate everything from Sales → Pre-Sales → Marketing → Support
> Tools: n8n + Zoho CRM MCP + Facebook Ads MCP + Gallabox WhatsApp + Sales Intelligence System + Claude AI

---

## What We Already Have (Ready to Use)

| Tool | Status | What It Does |
|------|--------|-------------|
| **Zoho CRM MCP** | LIVE | 7 tools — query leads, phone lookup, pipeline, custom views (299K leads) |
| **Facebook Ads MCP** | LIVE | 11 tools — campaigns, spend, CPL, audience, dying campaign alerts |
| **Gallabox WhatsApp** | LIVE | Send text + template messages to any number |
| **Sales Intelligence System** | BUILT (not deployed) | Full backend (FastAPI) + frontend (Next.js) — 40+ APIs, 4 AI agents, 9 pages |
| **Supabase DB** | LIVE | 13 tables, RLS, vector search, auth |
| **n8n** | LIVE | 3 active workflows + 5 available |
| **Resend Email** | CONFIGURED | Transactional email from dhruv.tomra@onsiteteams.com |
| **Claude AI** | CONFIGURED | Haiku for scoring, Sonnet for analysis |

---

## THE AUTOMATION MAP

### PHASE 1: Quick Wins (This Week) — Direct Impact on Revenue

These can be done via n8n workflows or direct scripts. No system deployment needed.

---

#### 1. Daily Rep Scorecard on WhatsApp
**Problem:** Reps don't know their numbers until month-end. No accountability.
**Automation:**
- Every morning 9 AM → Query Zoho CRM for each rep's MTD numbers
- Calculate: demos done, sales, revenue, pipeline (VH/HP count), follow-ups due today
- Send personalized WhatsApp to each rep via Gallabox
- Send manager summary to Sumit + Akshansh

**How:** n8n workflow (Zoho COQL → Code node → Gallabox HTTP)
**Impact:** Reps self-correct daily instead of waiting for month-end review
**Effort:** 1 day

---

#### 2. Follow-Up Date Alerts
**Problem:** Reps set follow-up dates in CRM but forget to act on them. Hot leads go cold.
**Automation:**
- Every morning 8 AM → Query Zoho for leads where `Lead_Task` (Followup Date) = today or overdue
- Group by rep
- Send WhatsApp: "You have 5 follow-ups today: [Company 1, Company 2...]"
- Flag overdue (>3 days) as URGENT

**How:** n8n workflow (Zoho COQL → Code node → Gallabox)
**Impact:** Zero leads forgotten. Every follow-up acted on.
**Effort:** 1 day

---

#### 3. Demo Booked → No Demo Done Alert
**Problem:** 530 leads are "Demo Booked" but demo not done. Nobody tracks this.
**Automation:**
- Daily check → Leads with `Lead_Status = '6. Demo booked'` and `Demo_Done_Date` is null
- If booked > 3 days ago → Alert rep + pre-sales person
- If booked > 7 days ago → Escalate to Sumit

**How:** n8n workflow (Zoho COQL → Gallabox)
**Impact:** Recover lost demos. Each demo = Rs.8,305 avg revenue.
**Effort:** 0.5 day

---

#### 4. Website + WhatsApp Lead Priority Alert
**Problem:** Website (Rs.76K avg deal, 39% conversion) and WhatsApp leads (highest volume) are not prioritized. Reps treat all leads the same.
**Automation:**
- When new lead from `2.Website` or `4.Customer Support WA` enters CRM → Instant alert to assigned rep
- Tag as HIGH PRIORITY in CRM
- If not contacted within 2 hours → Escalate

**How:** Zoho Workflow Rule → n8n webhook → Gallabox
**Impact:** Fastest response = highest conversion. These are hottest leads.
**Effort:** 1 day

---

#### 5. CRM Hygiene Report (Weekly)
**Problem:** 59% of demos have no remarks, 59% no price pitched. Data is garbage.
**Automation:**
- Every Friday 5 PM → Query Zoho for this week's demos
- Check: remarks filled? Price pitched? Follow-up date set?
- Per-rep hygiene score (% complete)
- Send to Sumit + Akshansh: "Bhavya filled 3/8 demos this week (37%)"

**How:** n8n workflow (Zoho COQL → Code node → Gallabox)
**Impact:** Accountability. Hygiene improves when measured publicly.
**Effort:** 0.5 day

---

### PHASE 2: Sales Intelligence System (Week 2) — Deploy What's Built

The system is 100% coded. Just needs deployment + Zoho integration.

---

#### 6. Deploy Sales Intelligence Dashboard
**What's already built:**
- Home dashboard (KPIs, hot leads, action items)
- Intelligence (CSV upload → 8-tab analysis)
- Agent Profiles (33 reps, strengths, concerns, trends)
- Smart Alerts (10 rules — stale, demo dropout, low conversion, etc.)
- Daily Briefs (morning/afternoon/evening per rep)
- Weekly Reports (Friday review, Monday kickoff)
- Research Agent (AI close strategy per lead)
- Lead Scoring (Hot/Warm/Cold via Claude Haiku)

**What needs to be done:**
- Deploy backend to Railway
- Deploy frontend to Vercel
- Run database migrations on Supabase
- Connect Zoho CRM via webhook (endpoints already written)
- Seed user accounts for team

**Impact:** Complete visibility for Akshansh, Sumit, Dhruv. Reps get daily briefs.
**Effort:** 2-3 days

---

#### 7. Zoho → Supabase Real-Time Sync
**Problem:** Currently using CSV exports. Data is always stale.
**Automation:**
- Zoho Workflow Rule on Lead create/update → POST to our webhook
- Webhook receives lead data → Upsert in Supabase
- Triggers: lead scoring, smart alerts, brief generation

**Already built:** `/api/webhooks/zoho-lead-created`, `/api/webhooks/zoho-deal-updated`
**Impact:** Real-time data instead of weekly CSV exports
**Effort:** 1 day (Zoho workflow config + test)

---

### PHASE 3: Pre-Sales Automation (Week 2-3)

---

#### 8. Smart Lead Routing
**Problem:** All leads go to "Team" in CRM. No intelligent assignment.
**Automation:**
- New lead enters → AI scores: industry, geography, deal size, source
- Match to best rep by: capacity, conversion rate, specialization
- Auto-assign in Zoho + notify rep via WhatsApp
- ME leads → Route to Jyoti (or Shruti for churn/re-engagement)

**Already built:** Assignment Agent in Sales Intelligence System
**Impact:** Right lead → right rep → faster close
**Effort:** 2 days

---

#### 9. Pre-Sales Capacity Dashboard
**Problem:** Jyoti overloaded (159 demos/month), Shruti underutilized (74 demos). No visibility.
**Automation:**
- Daily count: demos booked per pre-sales person today/this week
- If Jyoti > 8 demos/day → Overflow to Chadni
- If Shruti < 3 demos/day → Flag underutilization
- Auto-route ME churn leads (404 sitting) to Shruti

**How:** n8n workflow (Zoho query → Capacity check → Route)
**Impact:** Balance load. Recover ME pipeline.
**Effort:** 1.5 days

---

### PHASE 4: Marketing Automation (Week 3)

---

#### 10. Campaign → Revenue Attribution Dashboard
**Problem:** Marketing can't see which ads generate actual sales. Devansh (MagicMond) claims "20% more leads" but we can't verify.
**Automation:**
- Combine: Facebook Ads MCP (spend/leads) + Zoho CRM (sales by Lead_Source)
- Calculate: Cost per Lead, Cost per Sale, ROI by campaign
- Auto-generate monthly report comparing MagicMond's claims vs reality
- Track: FB Instaform leads → Demo → Sale → Revenue

**How:** n8n workflow (FB Ads MCP + Zoho COQL → Google Sheet dashboard)
**Impact:** Data-backed marketing decisions. Hold MagicMond accountable.
**Effort:** 2 days

---

#### 11. Ad Fatigue & Dying Campaign Alerts
**Problem:** ME adset "PAN UAE old aud" running 12 months. Audience burnt out. Nobody notices.
**Automation:**
- Weekly → Run `dying_campaigns_alert` from FB Ads MCP
- Check CPL trend: if increasing >20% week-over-week → Alert
- Check frequency: if > 3.0 → Audience fatigue alert
- Send to Dhruv + marketing team

**Already built:** `dying_campaigns_alert()` tool in FB Ads MCP
**Impact:** Catch dying campaigns before they waste budget
**Effort:** 0.5 day

---

#### 12. Google Ads Scaling Alert
**Problem:** Google Ads has BEST metrics (Rs.88K avg deal, 38% conversion, 17-day close) but only 61 leads/month. Severely underinvested.
**Automation:**
- Monthly → Compare channel metrics (CPL, conversion, avg deal, close time)
- Flag when a channel has best ROI but lowest spend
- Generate recommendation: "Increase Google Ads budget by X to get Y more leads"

**How:** n8n (Zoho COQL by source → Code analysis → Report)
**Impact:** Redirect budget to highest-ROI channel
**Effort:** 1 day

---

### PHASE 5: Support Automation (Week 3-4)

---

#### 13. Renewal Reminder Sequence (90/60/30/15/7/3/1 day)
**Problem:** Renewal team (Ravi) checks Google Sheet manually. Customers lapse before contact.
**Automation:**
- Daily → Check subscription expiry dates from sales CSV / Zoho
- 90 days before: First touch — value recap WhatsApp
- 60 days: Check-in message
- 30 days: Renewal reminder + pricing
- 15 days: Follow-up + urgency
- 7 days: Manager escalation if no response
- 3 days: Final reminder
- 1 day: "Your access will expire tomorrow"
- 0 (expired): Access restricted message
- +7 days: Churn survey

**How:** n8n workflow (Zoho/Sheet → Date filter → Gallabox sequence)
**Impact:** Proactive renewals. Reduce churn by 30-50%.
**Effort:** 2-3 days

---

#### 14. Onboarding Follow-Up Automation
**Problem:** After onboarding session, no structured follow-up. Customers drop off.
**Automation:**
- After onboarding session → Auto-send follow-up WhatsApp:
  - What was covered
  - Next steps checklist
  - Link to help docs
  - Schedule next session
- Day 3: "How's it going?" check-in
- Day 7: "Have you set up your first project?"
- Day 14: Health check — is customer active?

**How:** n8n (Manual trigger / Calendar → Gallabox template sequence)
**Impact:** Higher onboarding completion → lower churn
**Effort:** 1.5 days

---

#### 15. Low Activity Customer Alert
**Problem:** Customers churn silently. No alert when they stop using the app.
**Automation:**
- Weekly → Check Onsite app login/activity data
- If customer hasn't logged in 7+ days → Alert support team
- If 14+ days → Alert Ravi (manager)
- If 30+ days → Trigger re-engagement WhatsApp to customer

**How:** n8n (Onsite App API → Activity check → Gallabox alert)
**Impact:** Catch churn before it happens
**Effort:** 2 days (depends on Onsite App API access)

---

#### 16. Auto DPR to Project Owners
**Problem:** Support manually compiles Daily Progress Reports and sends via WhatsApp. Repetitive.
**Automation:**
- Daily 6 PM → Pull DPR data from Onsite app
- Format: Today's work, materials used, attendance, photos
- Auto-send to project owner's WhatsApp
- CC to support team for tracking

**How:** n8n (Onsite App API → Code format → Gallabox)
**Impact:** Eliminate daily manual work. Owners get reports on time.
**Effort:** 2 days (depends on Onsite App API access)

---

### PHASE 6: AI-Powered (Month 2)

---

#### 17. AI Support Chatbot (WhatsApp)
**Problem:** Same questions asked repeatedly across 100+ customer WhatsApp groups. No FAQ bot.
**Automation:**
- Gallabox webhook → Incoming customer message
- Claude + RAG (trained on help docs, past tickets, FAQs)
- Auto-respond to common questions (80% auto-resolve target)
- Escalate complex issues to human

**Impact:** Support handles 5x more customers. Ravi's team freed up.
**Effort:** 2 weeks

---

#### 18. AI Lead Research Agent
**Problem:** Reps go into demos blind. No prep on company background.
**Automation:**
- Before demo → Auto-research company (web, CRM history, similar past wins)
- Generate: Talking points, pricing suggestion, objection handling
- Send to rep 30 min before demo via WhatsApp

**Already built:** Research Agent in Sales Intelligence System
**Impact:** Higher close rate. Reps feel prepared.
**Effort:** 1 day (just deploy + trigger)

---

#### 19. Win/Loss Analysis Agent
**Problem:** Nobody analyzes why deals are won or lost. No learning loop.
**Automation:**
- Monthly → Pull all won + lost deals
- Claude analyzes: patterns, common objections, best-performing pitches
- Generate insights: "Deals from Website close 2x faster than FB"
- Send to Akshansh + Sumit

**How:** n8n (Zoho → Claude analysis → Report)
**Impact:** Continuous improvement. Learn from every deal.
**Effort:** 2 days

---

## PRIORITY ORDER (What to Build First)

| # | Automation | Revenue Impact | Effort | Do When |
|---|-----------|---------------|--------|---------|
| 1 | Follow-Up Date Alerts | HIGH — recover hot leads | 1 day | This week |
| 2 | Demo Booked → No Demo Alert | HIGH — 530 demos stuck | 0.5 day | This week |
| 3 | Daily Rep Scorecard | MEDIUM — accountability | 1 day | This week |
| 4 | CRM Hygiene Report | MEDIUM — data quality | 0.5 day | This week |
| 5 | Website/WA Lead Priority | HIGH — fastest close | 1 day | This week |
| 6 | Ad Fatigue Alerts | MEDIUM — stop waste | 0.5 day | This week |
| 7 | Deploy Sales Intelligence | HIGH — full visibility | 2-3 days | Week 2 |
| 8 | Campaign → Revenue Attribution | HIGH — marketing accountability | 2 days | Week 2 |
| 9 | Smart Lead Routing | HIGH — right rep, right lead | 2 days | Week 2-3 |
| 10 | Renewal Reminder Sequence | HIGH — reduce churn | 2-3 days | Week 2-3 |
| 11 | Pre-Sales Capacity Dashboard | MEDIUM — balance load | 1.5 days | Week 3 |
| 12 | Google Ads Scaling Report | MEDIUM — redirect budget | 1 day | Week 3 |
| 13 | Onboarding Follow-Up | MEDIUM — reduce churn | 1.5 days | Week 3 |
| 14 | Low Activity Alert | MEDIUM — catch churn early | 2 days | Week 3-4 |
| 15 | Auto DPR | LOW — ops efficiency | 2 days | Week 4 |
| 16 | AI Lead Research | HIGH — close rate | 1 day | Week 2 (deploy) |
| 17 | Win/Loss Analysis | MEDIUM — learning loop | 2 days | Month 2 |
| 18 | AI Support Chatbot | HIGH — 5x support capacity | 2 weeks | Month 2 |
| 19 | AI Close Strategy before Demo | HIGH — prep reps | 1 day | Month 2 |

---

## Total Effort Estimate

| Phase | Automations | Days | Impact |
|-------|------------|------|--------|
| Phase 1 (This Week) | 6 quick wins | 4-5 days | Daily accountability, recover hot leads |
| Phase 2 (Week 2) | Deploy system + Zoho sync | 3-4 days | Full visibility dashboard |
| Phase 3 (Week 2-3) | Pre-sales routing | 3-4 days | Balance load, recover ME |
| Phase 4 (Week 3) | Marketing automation | 3-4 days | ROI tracking, stop waste |
| Phase 5 (Week 3-4) | Support automation | 7-8 days | Reduce churn, automate renewals |
| Phase 6 (Month 2) | AI-powered | 2-3 weeks | AI chatbot, research, analysis |

**Total: ~5-6 weeks to automate everything**

---

## What Changes for Each Team

### Sales Reps Get:
- Daily WhatsApp scorecard (their numbers)
- Follow-up alerts (what to do today)
- Demo prep (AI research before calls)
- Hot lead alerts (Website/WA priority)
- Weekly hygiene score (accountability)

### Pre-Sales Gets:
- Capacity balancing (no more overload)
- Smart lead routing (right leads to right person)
- ME lead pool alerts (404 churn leads activated)

### Marketing Gets:
- Campaign → Revenue attribution (which ads sell)
- Ad fatigue alerts (stop wasting budget)
- Channel ROI comparison (where to invest)
- MagicMond accountability report

### Support Gets:
- Renewal reminders (automated 90→0 day sequence)
- Onboarding follow-ups (structured, not ad-hoc)
- Low activity alerts (catch churn early)
- Auto DPR delivery (no manual compilation)
- AI chatbot (handle 80% of questions)

### Founders (Akshansh/Sumit) Get:
- Full Sales Intelligence Dashboard (real-time)
- Daily team summary
- Weekly performance reports
- Revenue forecasting
- Pipeline risk alerts
- Marketing ROI visibility

---

*Built with: Zoho CRM MCP + Facebook Ads MCP + Gallabox WhatsApp + Sales Intelligence System + n8n + Claude AI*
