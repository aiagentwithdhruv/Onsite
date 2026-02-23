# Onsite Teams - AI Master Context

> Auto-loaded by Claude Code. Contains everything an AI needs to understand this project, the company, the market, and how to help grow sales.

---

## Company Profile

| Field | Detail |
|-------|--------|
| **Legal Name** | Abeyaantrix Technology Private Limited |
| **Brand** | Onsite / Onsite Teams |
| **Product** | Construction Management Software & ERP (SaaS) |
| **Website** | https://www.onsiteteams.com |
| **CIN** | U72900DL2021PTC379359 |
| **Founded** | March 2021, New Delhi |
| **Office** | C-93, 3rd Floor, Sector 2, Noida, UP 201301 |
| **Employees** | ~23 (as of 2024) |
| **Claimed Users** | 10,000+ companies |
| **Markets** | India, UAE, Global |

### Leadership
- **Akshansh Agarwal** — CEO & Co-Founder (IIT Kanpur + ISB)
- **Dheeraj Kumar Anand** — Co-Founder & Director
- **Sumit Garg** — Co-Founder & Director
- **Sumit** — Primary contact for Dhruv (sumit@onsiteteams.com, +91 9560209605)

### Funding & Financials
- **Total Raised:** $1.72M (Seed: $1.5M from Artha Venture Fund, Foundamental)
- **Valuation:** INR 81.6 Crore (~$9.7M)
- **Notable Angel:** Varun Alagh (Mamaearth co-founder)
- **Revenue Trajectory:** Under INR 1Cr (FY22) → 16,383% growth in FY23
- **Profitability:** Not yet (investing in growth)
- **Promoter Holding:** 92.83%

---

## Product — What Onsite Sells

### Core Modules
- Project Management (DPR automation, issue tracking, cost alerts)
- Material Management (procurement, inventory, wastage tracking)
- Labor & Workforce (attendance, wages, salary processing)
- Financial Management (budgeting, invoicing, accounting)
- Procurement (centralized, RFQ, POs)
- Quality Management
- Design Management
- Reporting & Dashboards

### Pricing

**National (INR):**

| Plan | Per User/Year | Lump Sum |
|------|--------------|----------|
| Business | 12,000 | — |
| Business+ | 15,000 | — |
| Enterprise | — | 12,00,000 |
| White Label Web | — | 3,00,000 |
| White Label Android | — | 3,50,000 |
| White Label iOS | — | 4,00,000 |

**International (USD):**

| Plan | Per User/Year | Lump Sum |
|------|--------------|----------|
| Business | $200 | — |
| Business+ | $250 | — |
| Enterprise | — | $15,000 |
| White Label Web | — | $3,600 |
| White Label Android | — | $4,200 |
| White Label iOS | — | $4,800 |

**Add-ons (National/International):**
- GPS Attendance: 20K / $300
- Additional Company: 20K / $300
- Tally Integration: 20K + 5K AMC / $300 + $100 AMC
- Zoho Integration: 20K + 5K AMC / $300 + $100 AMC
- Additional Users: 5K/user/year / $60/user/year

**GST:** 18% on national orders. International = zero GST.

### Plan Features
- **Business:** Payments, Files, Labor Attendance/Salary, CRM, Inventory, Tasks, Issues, Subcon, Roles
- **Business+:** All Business + Design Mgmt, BOQ/RA Bills, Budget Control, Warehouse, RFQ, POs, Assets, Equipment, Payroll, Inspection, Multi-Level Approval
- **Enterprise:** All Business+ + Unlimited Users, GPS, Custom Roles/Dashboards, Accounting Integration, Vendor/Client Portals, White Label, SAP add-ons

### Key Claims & USPs
- ISO certified
- Implementation in 1-2 weeks (vs months for traditional ERP)
- Mobile-first design (site workers use phones, not laptops)
- Projects worth 5,000 Cr+ managed
- Up to 7% cost savings

---

## Dhruv's Role at Onsite

| Field | Detail |
|-------|--------|
| **Title** | AI Engineer / AI Automation Lead |
| **Tenure** | Jan 2023 — Present (3+ years) |
| **CTC** | ~20 LPA (fixed + variable + consulting) |
| **Scope** | 4 LangGraph agents, 210+ automation workflows, RAG knowledge systems, voice AI, quotation generator |

### Impact Metrics
- **Revenue:** 0 → 10 Cr ARR growth
- **Cost Reduction:** 60-70% across operations
- **Time Saved:** 15+ hrs/week per person
- **Onboarding:** 50% faster using AI assistants
- **Outreach:** 31% reply rate (vs ~8% industry average)
- **Sales Team:** 16-person team uses quotation generator daily
- **Lead Processing:** 500 leads/day scored by Daily Pipeline Agent

### Portfolio Pitch Angle
> "Enterprise AI that prioritizes your hottest leads daily"

---

## What Dhruv Has Built for Onsite

### 1. Quotation Generator (COMPLETE & IN PRODUCTION)

**Files:**
- `quotation-generator.html` — Sales team web form (70KB)
- `QuotationGenerator.gs` — Google Apps Script backend (40KB)

**What it does:**
- Sales team fills form → auto-generates branded PDF quotation
- Saves to Google Drive (National/International folders)
- Emails PDF to client + salesperson
- Supports all plans, add-ons, White Label, Additional Users
- Auto-calculates GST, discounts, totals
- Sequential numbering: ONS-2026-XXXX

**Impact:** 10-15 min → 2 min per quotation (2+ hrs saved daily)

**Credentials:**
- Google Drive (National): `19nxVxULJFIs0-gFW6J3mMWH1eWpfLveu`
- Google Drive (International): `1pL0A6B-dWmLww6ClR366MD__zglR3Haa`
- Bank: ICICI 401705000501, IFSC ICIC0004017
- Intl Payments: Currency Cloud (SWIFT: TCCLGB3L, London)

### 2. Sales Intelligence System (BUILT, NOT DEPLOYED)

**Path:** `sales-intelligence-system/`

AI-powered sales intelligence on top of Zoho CRM:
1. **Prioritize** — AI ranks leads Hot/Warm/Cold with reasons, daily call list
2. **Research & Advise** — Company research + CRM notes + close strategy
3. **Alert & Report** — Morning briefs, stale lead alerts, weekly reports

**Tech Stack:**
- Frontend: Next.js 16 + Tailwind 4 + Recharts
- Backend: FastAPI (Python)
- DB: Supabase (PostgreSQL + pgvector)
- AI: LangGraph + Claude (primary) + GPT-4o (fallback) + Haiku (cheap)
- CRM: Zoho CRM REST API v8
- Alerts: Telegram, Discord, WhatsApp (Gupshup), Email (Resend)
- Hosting Plan: Railway (backend) + Vercel (frontend)
- Supabase Project: `jfuvhaampbngijfxgnnf`

**4 AI Agents (detailed):**
- **Daily Pipeline Agent** (7:30 AM) — Scores 500 leads Hot/Warm/Cold. Dual-LLM: Haiku at $0.01/batch for scoring, Sonnet for reasoning. Generates personalized WhatsApp morning briefs per rep
- **Research Agent** (on-demand) — CRM notes analysis + web research + pgvector similarity matching against past won deals. Returns close strategy with talking points in 15 seconds
- **Smart Assignment Agent** (on webhook/sync) — Auto-assigns new leads to best rep based on capacity, conversion rate, and industry match
- **Weekly Report Agent** (Monday 8 AM) — Pipeline summary, per-rep scorecard, revenue forecast delivered to founder

**Current state:** CSV upload works (Zoho export). All pages built. Locally verified (port 8000/3000). NOT deployed to production.

**Completed Features (detailed):**
- Auth: Supabase login/session persistence, JWT decode
- Intelligence Dashboard: 8 tabs (Sales, Overview, Pipeline, Team, Sources, Aging, Trends, Deep Dive)
- Sales Tab: Revenue KPIs, monthly trend, region/source/owner analysis, dual leaderboards
- Agent Profiles: auto-computed per deal owner with performance, patterns, strengths, concerns
- Smart Alert Agent: 10 alert rules (stale leads, demo dropout, low conversion, hot prospects, priority overload, inactive agents, top performer, revenue milestone, pipeline risk, follow-up needed)
- Alert Delivery: Telegram, Discord, WhatsApp (Gupshup), Email (Resend)
- Deal-owner scoping: reps see only their data, managers see all
- Admin page: role + deal owner assignment per user
- Dashboard home: "Your next 3 things" from daily brief
- LLM provider management (Anthropic, OpenAI, OpenRouter, Moonshot) with Primary/Fast/Fallback model selection
- Revenue parsing: handles "Rs. 42,000.00" Zoho format
- Revenue counted from sale_done=1 records only
- Direct API calls (bypass Next.js proxy for auth headers)
- Gamma slide deck content (10 slides) prepared

**Data Architecture:**
- DO NOT store 300K raw leads (Supabase free tier 500MB limit)
- Store pre-computed summaries (~1-2MB JSONB) and agent profiles
- Deal Owner is primary field (not Lead Owner) for all analytics
- CSV columns: lead_name, deal_owner, lead_status, sale_done, sale_done_date, annual_revenue, price_pitched, demo_done, demo_booked, lead_source, state_mobile, region, company_name, sales_stage, call_disposition, lead_notes

**Role-Based Access:**
| Role | Access |
|------|--------|
| Sales Rep | Own leads/stats only (by deal_owner_name) |
| Team Lead | Their team's data |
| Manager | All teams |
| Founder | Everything + analytics |
| Admin | Full access including settings |

**Known Issues:**
- Supabase user lookup: auth_id returns 400, id returns 406 (only email works)
- Hydration mismatch warning (browser extension, harmless)
- Leads page empty until Zoho integration
- Dashboard home shows 0s until Zoho integration

**Blockers:**
- Zoho CRM OAuth credentials needed from client
- Supabase production setup
- Railway/Vercel deployment

**Design Docs:**
- `01-SYSTEM-DESIGN-UPDATED.md` — Architecture v2.0
- `02-ZOHO-INTEGRATION-SPEC.md` — Zoho API spec
- `03-DATABASE-SCHEMA.md` — 11 migrations, all tables
- `04-LANGGRAPH-AGENTS-SPEC.md` — Agent specs
- `05-BUILD-PLAN-REVISED.md` — 10-week plan

### 3. Other Systems Built for Onsite

- **Voice AI Agents** — ElevenLabs + telephony for outbound calling, demo booking, and support automation
- **RAG Knowledge Systems** — Internal knowledge base for sales enablement and team onboarding
- **Lead Analysis** — PLANNED (awaiting Google Sheet URL from client)

### 4. n8n Workflows for Onsite

**Active workflows (on n8n.aiwithdhruv.cloud):**
| Workflow | ID | Purpose |
|----------|----|---------|
| Onsite AI Rag Workflow | `SZ4C06KYyypDF3Ob` | RAG-based knowledge assistant |
| OnsiteUpload data from Drive to Pinecone | `mbxhJKeafeVgHGIb` | Data pipeline to vector DB |
| Email Auto followups | `qbWjLjqmTXha48b0` | Automated email follow-ups |

**Inactive workflows (available for reactivation):**
| Workflow | ID | Purpose |
|----------|----|---------|
| Onsite Email Taniya Australia/US | `AO5GCdBC2Z5rjUnv` | Email outreach — AU/US market |
| Onsite Email Taniya UAE | `oPl4eXNyom6qFpb5` | Email outreach — UAE market |
| Onsite Sales Data to Pinecone | `dplthdr709NaTOpI` | Sales data vectorization |
| Taniya LinkedIn | `dbL1DqoTx8pghvUP` | LinkedIn automation for Taniya |
| Warm/Cold Email Outreach | `SQiFNuZdkxMnbqKC` | General outreach campaign |

**n8n Credentials (Onsite-specific):**
- Gmail OAuth "Dhruv Onsite": `jTmenYUXq2LXzf6e`
- Taniya LinkedIn person ID: `EDRr5PtOm4`
- Google Sheet "Onsite Ai Automation": `1Bs2TXEsVlv4xxjZ-3k-DBYiTf6nw6ATUZ2GunQSIq3s`
- Google Sheet "Taniya LinkedIn Auto Post": `1YZk12lNR7ZpjtJ6pOB2ugIgVIyF15-oAGPhuzCg2KE4`
- Google Drive "LinkedIn N8n Taniya": `1Qh-s0dD3joJWQFVUvRM8MGyxKopBlmQC`

---

## Market Research — Construction Tech SaaS

### Market Size

| Metric | Value |
|--------|-------|
| Global Construction Software (2025) | $10.64B |
| Global Construction Software (2034) | $24.72B (9.7% CAGR) |
| India Construction Software (2025) | ~$0.28B (11.4% CAGR) |
| India Construction Industry (2025) | $740B / INR 22.77T |
| India Infra Budget (FY25-26) | INR 50.7T ($603B) |
| Asia-Pacific CAGR | 10.98% (fastest growing) |

### India Construction Drivers
- Government infra push: Delhi-Mumbai Expressway, Bharatmala (26,425 km), 20 new airports, Smart Cities (5,151 projects)
- Digital transformation mandate across construction
- 10-30% cost overruns creating urgent need for software
- RERA + GST compliance pushing digital adoption
- Labor shortages driving automation demand

### Competitors — India

| Company | Key Differentiator | Scale |
|---------|-------------------|-------|
| **Powerplay** | Budget-friendly, mobile-first | 700K+ users, 85K projects |
| **NYGGS** | AI-powered, IoT | Large infra (roads/highways) |
| **StrategicERP** | IITian-built, flexible | 1,000+ companies |
| **RDash** | Expert-led, design-to-handover | 9,000+ projects |
| **FalconBrick** | Offline capability | Site monitoring |
| **Highrise ERP** | Claims 15% cost savings | Builders/contractors |
| **NWAY ERP** | 480+ cities, IoT | Pan-India |

### Competitors — Global

| Company | Pricing | Scale |
|---------|---------|-------|
| **Procore** | $199-375/user/month | 3M+ projects, 150 countries |
| **Buildertrend** | $299-499/month (unlimited) | Residential SMB |
| **PlanGrid (Autodesk)** | $39-199/user/month | 2M+ projects |
| **Fieldwire** | Custom | 2M+ projects |
| **Oracle Aconex** | Enterprise | $9T managed |

### Onsite's Competitive Edge
- **10-20x cheaper than global players** ($200-250/user/year vs Procore at $2,388-4,500)
- **Fastest implementation** (1-2 weeks vs months)
- **Mobile-first** (aligned with Indian site workers)
- **Indian market understanding** (GST, RERA, Hindi support)

---

## Sales Playbook — What Works in Construction SaaS

### Buyer Psychology
- **Relationship-driven** — referrals > cold outreach. One contractor telling another is the #1 buying signal
- **Education-first** — most are buying software for the first time. Teach WHY before WHICH
- **ROI-obsessed** — "7% cost savings" and "reduce overruns by 15%" close deals. Abstract benefits don't
- **Phone-first** — builders answer calls. Cold calls > cold emails
- **Risk-averse** — free trials and pilot projects ("try on one site") reduce friction

### Sales Cycle
| ACV | Typical Cycle |
|-----|---------------|
| Under $5K | ~40 days |
| $5K-$100K | ~84 days |
| Over $100K | 170+ days |

### Decision Makers by Company Size
- **Small (1-50):** Owner decides directly
- **Mid (50-500):** Project Manager + Finance Head + Owner
- **Enterprise (500+):** 10-11 stakeholders, CFO has final say (79%)

### Top Pain Points (Why They Buy)
1. **Manual processes** (57%) — paper DPRs, Excel tracking, WhatsApp coordination
2. **Cost overruns** (10-30%) — no real-time budget visibility, material wastage, labor fraud
3. **Limited current tools** (22%) — Excel doesn't scale
4. **Cash flow blindness** — manual RA billing causes squeezes
5. **Multi-site chaos** — no single source of truth
6. **Compliance headaches** — GST, RERA, labor laws all manual

### Barriers to Overcome
1. **Lack of digital skills** (42%) → on-site training, mobile simplicity
2. **Budget constraints** (34%) → ROI calculator, cost-of-doing-nothing framing
3. **Resistance to change** → pilot project approach, reference customers
4. **Integration fears** → Tally/Zoho add-ons already built
5. **Data security concerns** → ISO certification, cloud security

### Objection Handling
| Objection | Response |
|-----------|----------|
| "Too expensive" | ROI calc: one material theft > annual subscription. 7% cost savings on a 10Cr project = 70L saved |
| "My team can't use it" | Mobile-first, Hindi support, on-site training. Simpler than WhatsApp groups |
| "We use Excel" | Show time saved, error reduction, real-time visibility across sites |
| "Data security" | ISO certified, enterprise cloud, data ownership guarantee |
| "Not the right time" | Cost overruns happening NOW. Every month without tracking = money lost |

### Best Sales Channels for Onsite
1. **Cold calling** — builders answer phones. Short 15-20 min demos beat hour-long presentations
2. **WhatsApp Business** — universal in Indian construction. Send quotes, follow up, share demos
3. **LinkedIn** — target construction company owners, post case studies with INR numbers
4. **Referral network** — happy customers referring peers is highest-conversion channel
5. **Industry events** — ACETECH, India Construction Festival, BuildTech India
6. **Partnerships** — material suppliers, CAs/auditors, architect firms (they advise builders)
7. **Associations** — CREDAI, BAI, CIDC for credibility + lead lists
8. **YouTube** — tutorials in Hindi showing real construction workflows

### Content That Converts
- Case studies with INR numbers ("Saved 45L on a 12Cr project")
- Before/after comparisons (manual vs Onsite)
- Short demo videos (under 5 min, in Hindi)
- ROI calculators
- Compliance checklists (RERA readiness, GST setup)

---

## Automation Opportunities (What Dhruv Can Build Next)

### High Impact (Revenue-Driving)
1. **Quotation Follow-Up Automation** — Auto emails at day 2, 5, 7 after quote sent. Alert manager if no response. Directly recovers lost deals.
2. **Deploy Sales Intelligence System** — Already built. Just needs Zoho creds + hosting. AI lead scoring = reps focus on hot leads first.
3. **CRM ↔ Quotation Integration** — Every quote auto-creates/updates a deal in Zoho. Pipeline visibility.
4. **WhatsApp Quote Delivery** — Send PDF via WhatsApp alongside email. Higher open rate in construction.

### Medium Impact (Efficiency)
5. **Win/Loss Dashboard** — Track which quotes converted, which didn't, why. Data to optimize pricing.
6. **Invoice Generator** — Natural extension of quotation system. Auto-generate invoices from won deals.
7. **Payment Reminder Automation** — Auto follow-up on overdue invoices.
8. **Lead Tracker** — Google Sheet or dashboard for tracking all leads from first contact to close.

### Future (Differentiators)
9. **AI Chatbot on Website** — Answer prospect questions 24/7, qualify leads, book demos
10. **Proposal Generator** — Auto-generate custom proposals based on client requirements
11. **Client Onboarding Automation** — Post-sale automated setup emails, training schedule, milestone tracking
12. **Contract Management** — Digital contracts with e-signatures

---

## Key Contacts & Credentials

| Service | Credential/ID |
|---------|---------------|
| **GSTIN** | 09AAVCA0250E1ZR |
| **PAN** | AAVCA0250E |
| **Bank** | ICICI 401705000501, IFSC ICIC0004017 |
| **Supabase Project** | jfuvhaampbngijfxgnnf |
| **Supabase URL** | https://jfuvhaampbngijfxgnnf.supabase.co |
| **Supabase Connection** | postgresql://postgres.jfuvhaampbngijfxgnnf@aws-1-ap-south-1.pooler.supabase.com:5432/postgres |
| **GitHub** | aiagentwithdhruv/Onsite (private) |
| **Google Drive National** | 19nxVxULJFIs0-gFW6J3mMWH1eWpfLveu |
| **Google Drive Intl** | 1pL0A6B-dWmLww6ClR366MD__zglR3Haa |
| **Gmail OAuth (n8n)** | "Dhruv Onsite" — jTmenYUXq2LXzf6e |
| **Google Sheet** | "Onsite Ai Automation" — 1Bs2TXEsVlv4xxjZ-3k-DBYiTf6nw6ATUZ2GunQSIq3s |
| **Dhruv Email** | dhruv.tomar@onsiteteams.com |
| **Sumit Email** | sumit@onsiteteams.com |
| **Sumit Phone** | +91 9560209605 |

### Team Members

| Person | Role | Context |
|--------|------|---------|
| Sumit | Founder/Primary Contact | Sees everything, signs off on features |
| Dhruv | AI Engineer/Automation Lead | Builds everything, admin access |
| Taniya | Sales/Marketing | LinkedIn + email outreach (AU/US/UAE) |
| ~16 sales reps | Sales team | End users of quotation generator + intelligence dashboard |

---

## File Structure

```
Onsite/
├── .claude/CLAUDE.md              ← THIS FILE (AI master context)
├── .context                       ← Project context (technical decisions, completed features)
├── quotation-generator.html       ← Quotation Generator UI (PRODUCTION)
├── QuotationGenerator.gs          ← Google Apps Script backend (PRODUCTION)
├── README.md                      ← Repo overview
├── QUOTATION-SYSTEM-COMPLETE.md   ← Quotation system status
├── QUOTATION-GENERATOR-SETUP.md   ← Setup instructions
├── SALES-TEAM-QUICK-START.md      ← Quick start for sales team
├── TROUBLESHOOTING.md             ← Debug guide
├── UPDATES_LOG.md                 ← Changelog (White Label, Additional Users)
├── Quotation_temp/                ← Reference templates (CSV + PDF)
├── sales_agent_system_design.docx.pdf  ← Original v1.0 design doc
└── sales-intelligence-system/     ← AI Sales Intelligence (NOT DEPLOYED)
    ├── 01-SYSTEM-DESIGN-UPDATED.md
    ├── 02-ZOHO-INTEGRATION-SPEC.md
    ├── 03-DATABASE-SCHEMA.md
    ├── 04-LANGGRAPH-AGENTS-SPEC.md
    ├── 05-BUILD-PLAN-REVISED.md
    ├── PROGRESS.md
    ├── DEPLOY.md
    ├── GAMMA-SLIDES-CONTENT.md
    ├── backend/                   ← FastAPI + LangGraph agents
    ├── frontend-next/             ← Next.js 16 dashboard
    └── database/                  ← 11 Supabase migrations
```

---

## Relevant Skills Library (from AiwithDhruv Skills)

If this folder is inside the larger n8n project, these skills from `.context/claude-skills/` are directly useful:

| Skill | Use For |
|-------|---------|
| `classify-leads` | AI lead scoring for Onsite's pipeline |
| `generate-report` | Automated sales reports |
| `gmail-inbox` | Multi-account email management |
| `modal-deploy` | Cloud deployment of Sales Intelligence System |
| `add-webhook` | Event-driven automation for Zoho integration |

---

## Regulatory Context (India Construction)

- **RERA** (Real Estate Regulation and Development Act) — Mandates transparency in projects. Software that helps RERA compliance = strong selling point
- **GST** — All construction billing must be GST-compliant. Built-in GST = table stakes
- **Labor Laws** — PF, ESI, minimum wage tracking required by law
- **ISO Certification** — Onsite is ISO certified (use in sales pitches)

---

## AI Instructions

When working on Onsite:
1. **Read this file first** — it has everything
2. **For quotation changes** — edit `quotation-generator.html` and `QuotationGenerator.gs` in sync (keep pricing in both files synchronized)
3. **For sales intelligence** — check `sales-intelligence-system/PROGRESS.md` for current state, and `.context` file for technical decisions
4. **For sales strategy** — reference the Sales Playbook section above
5. **For competitor analysis** — use the market research above, refresh from onsiteteams.com if needed
6. **For new features** — check Automation Opportunities section, prioritize revenue-driving ones
7. **Keep pricing data current** — verify against onsiteteams.com/onsite-pricing periodically
8. **For n8n workflows** — check the n8n Workflows section for existing workflow IDs and credentials
9. **For deployment** — see `sales-intelligence-system/DEPLOY.md` for Docker/Railway/Vercel instructions

### Tone for Onsite Communications
- Professional but practical (construction industry, not tech startups)
- Lead with ROI and cost savings, not features
- Use INR numbers for Indian clients, USD for international
- Reference specific construction workflows (DPR, RA bills, material tracking)
- Avoid jargon — "save 2 hours daily" beats "AI-powered automation"

### Key Regulatory Terms to Know
- **DPR** — Daily Progress Report (construction standard)
- **RA Bills** — Running Account Bills (contractor payment milestone system)
- **BOQ** — Bill of Quantities (cost estimation document)
- **RFQ** — Request for Quotation (procurement process)
- **PO** — Purchase Order
- **AMC** — Annual Maintenance Contract

---

## Self-Update Rules

### Auto-Update Triggers
After ANY of these events, update the relevant section of this file:

| Event | Update | Section |
|-------|--------|---------|
| New feature built | Add to "Completed Features" list | What Dhruv Has Built |
| Pricing change on onsiteteams.com | Update pricing tables | Product Pricing |
| New team member joins | Add to Team Members table | Key Contacts |
| New n8n workflow created | Add workflow ID + purpose | n8n Workflows |
| Credential rotated | Update credential ID | Key Contacts & Credentials |
| New competitor discovered | Add to competitor table + `knowledge/competitors.md` | Market Research |
| Bug fixed in codebase | Add to Known Issues (mark resolved) | Known Issues |
| Feature deployed to production | Move from "Blockers" to "Completed" | Sales Intelligence |
| Revenue/ARR change | Update Impact Metrics | Dhruv's Role |
| New runbook created | Update file list in LOADOUT.md | LOADOUT.md |

### Verification Schedule
| Section | Verify Every | How | Last Verified |
|---------|-------------|-----|---------------|
| Pricing tables | Monthly | Check onsiteteams.com/onsite-pricing | 2026-02-23 |
| Competitor data | Quarterly | Web search for construction SaaS India | 2026-02-23 |
| Market size numbers | Yearly | Check Fortune/Mordor Intelligence reports | 2026-02-23 |
| Credentials | On failure | Test each credential, update if expired | 2026-02-23 |
| Sales playbook | Quarterly | Check win/loss data, update objection handling | 2026-02-23 |

### Staleness Markers
When reading a section, if `last_verified` is older than the section's refresh cadence,
flag it: "This section may be stale (last verified: {date}). Verify before using."

### Cross-File Updates
When updating this file, also check if these files need updates:
- `LOADOUT.md` — file inventory, version, changelog
- `knowledge/competitors.md` — if competitor data changed
- `knowledge/construction-market.md` — if market data changed
- `sales-intelligence-system/SKILL.md` — if codebase/architecture changed
