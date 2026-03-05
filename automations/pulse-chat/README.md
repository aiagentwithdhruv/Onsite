# Onsite Pulse Chat

> AI-powered sales assistant for Onsite Teams — CRM data + sales coaching + WhatsApp delivery, all in one chat interface.

**Live:** [onsite-pulse.vercel.app](https://onsite-pulse.vercel.app)

---

## What It Does

Pulse Chat is a web-based AI assistant that gives the Onsite sales team instant access to their CRM data AND intelligent sales coaching — right from their phone browser. Responses are automatically sent to WhatsApp for easy reference.

### CRM Data (Real-Time from Zoho)
- **Demos** — Count, list, with remarks/notes
- **Sales** — Closed deals, revenue, monthly trend
- **Pipeline** — VHP/HP/Prospect breakdown
- **Follow-ups** — Overdue + today's tasks
- **Rank** — Team leaderboard
- **Target** — Monthly progress + days left
- **Lead Search** — Find any lead by phone, name, or company (with CRM Notes)

### Sales Assistant (AI-Powered)
- **Pricing** — Full plan breakdown (INR + USD + GST + add-ons)
- **Email Drafting** — Personalized follow-up emails based on lead context
- **Objection Handling** — Ready-to-use rebuttals with ROI numbers
- **Competitor Comparison** — Procore, Powerplay, NYGGS positioning
- **Pitch Strategy** — How to approach specific client types
- **Product Knowledge** — Module features, USPs, implementation details

### Smart Features
- **Conversation Memory** — Remembers what you were discussing (Supabase PostgreSQL)
- **Context-Aware** — "Write email for that lead" works because it remembers the last lead searched
- **WhatsApp Delivery** — Useful responses auto-sent to your WhatsApp via Gallabox
- **Role-Based Access** — Reps see own data, Team Leads see team, Admins see all
- **Hinglish Support** — Works in English, Hindi, and Hinglish
- **Mobile-First UI** — Built for phone browsers with safe area insets, keyboard handling

---

## Architecture

```
User (Mobile/Desktop Browser)
    |
    v
[Vercel — Static HTML]  onsite-pulse.vercel.app
    |
    v  POST /webhook/pulse-chat
[n8n Workflow — Code Node]  (3 nodes: Webhook > Code > Respond)
    |
    |-- Zoho CRM API (COQL queries for leads, demos, sales, pipeline)
    |-- OpenRouter / Grok 4.1 Fast (AI intent classification + assistant)
    |-- Supabase PostgreSQL (conversation memory — pulse_chat_history)
    |-- Gallabox WhatsApp API (auto-send useful replies to rep's phone)
    |
    v
JSON Response → Chat UI
```

### Tech Stack

| Layer | Tech | Cost |
|-------|------|------|
| Frontend | Static HTML/CSS/JS | Free (Vercel) |
| Backend | n8n Code Node (JavaScript) | Free (self-hosted) |
| CRM | Zoho CRM v7 COQL API | Included |
| AI | Grok 4.1 Fast via OpenRouter | ~$0.20/M input, $0.50/M output |
| Memory | Supabase PostgreSQL | Free tier (500MB) |
| WhatsApp | Gallabox API | Existing plan |
| Hosting | Vercel (frontend) + Hostinger VPS (n8n) | $0 additional |

**Total additional cost: ~$0-2/month** (AI tokens only)

---

## File Structure

```
pulse-chat/
  index.html          -- Chat UI (mobile-first, deployed to Vercel)
  README.md           -- This file
  screenshots/        -- Desktop & mobile screenshots

../deploy_to_n8n.py   -- Deployment script (SHARED_JS + AUTO_9_JS = full backend)
../pulse-chat.html    -- Same as index.html (Vercel deploy source)
```

### Key Code Sections in `deploy_to_n8n.py`

| Section | Lines | What |
|---------|-------|------|
| `SHARED_JS` | ~23-188 | Zoho auth, COQL helpers, WhatsApp sender, config |
| `AUTO_9_JS` | ~993+ | Full Pulse Chat logic |
| PIN Auth | ~1000-1040 | 4-digit PIN per rep |
| Roles | ~1008-1023 | admin/team_lead/rep access control |
| Supabase Memory | ~1047-1090 | Conversation history (last 5 messages) |
| AI Intent Detection | ~1130-1210 | Grok 4.1 Fast classifier (12 intents) |
| CRM Handlers | ~1280-1540 | Demos, Sales, Pipeline, Follow-ups, Rank, Target, Notes, Lead Search |
| Sales Assistant | ~1545-1650 | Full Onsite knowledge context + AI response |
| WhatsApp Delivery | ~1660-1680 | Auto-send to rep's phone |

---

## Intents (12 Total)

| Intent | Trigger Examples | Response |
|--------|-----------------|----------|
| `demos` | "my demos", "feb demos", "Anjali demos" | Demo count + list from Zoho |
| `sales` | "my sales", "revenue this month" | Sales closed + revenue |
| `pipeline` | "my pipeline", "hot leads" | VHP/HP/Prospect count |
| `followups` | "my follow-ups", "pending calls" | Overdue + today's tasks |
| `rank` | "my rank", "leaderboard" | Team sales leaderboard |
| `target` | "my target", "progress" | Monthly stats + days left |
| `notes` | "my notes", "remarks" | Recent leads with notes |
| `lead_search` | "find lead BEI", "search 9876543210" | Lead details + CRM Notes |
| `assistant` | "our pricing", "write email", "handle objection" | AI response with full Onsite knowledge |
| `greeting` | "hi", "hello", "namaste" | Random greeting |
| `help` | "help", "what can you do" | Full command list |
| `chat` | anything else | Friendly redirect |

---

## WhatsApp Auto-Delivery Rules

| Intent | Auto-sends to WA? | Why |
|--------|-------------------|-----|
| `assistant` | Always | Emails, scripts, strategies — need on phone |
| `followups` | Always | Action items for calling |
| `lead_search` | Always | Lead details for reference |
| `demos`/`sales`/`notes` with notes | Yes | Detailed data |
| Any reply >500 chars | Yes | Long = useful to save |
| `greeting`, `help`, `chat` | Never | Not useful |

---

## Team Access

| Rep | Role | Can See |
|-----|------|---------|
| Dhruv, Sumit, Akshansh | Admin | All reps' data |
| Anjali | Team Lead | Own + Jyoti, Shruti, Chadni |
| Everyone else | Rep | Own data only |

Each rep has a unique 4-digit PIN. PINs are hardcoded in the workflow (not stored in DB).

---

## Supabase Schema

```sql
CREATE TABLE pulse_chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    message TEXT,
    reply TEXT,
    intent TEXT,
    lead_context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_pch_user ON pulse_chat_history(user_name, created_at DESC);
```

- **Project:** `jfuvhaampbngijfxgnnf` (Onsite_Data, ap-south-1)
- **Access:** Service role key (in workflow code)
- Stores last 5 messages per user for conversation context

---

## Onsite Knowledge Embedded

The Sales Assistant has the following Onsite knowledge baked into its system prompt:

- Full pricing tables (National INR + International USD + add-ons + GST)
- All product modules and plan feature breakdown
- 6 objection handling scripts with ROI calculations
- 7+ competitor comparisons (India + Global)
- Sales playbook (buyer psychology, pain points, decision makers)
- Email/message writing style guide
- Construction industry terminology (DPR, RA Bills, BOQ, etc.)

---

## Sample Prompts

### CRM Data
```
my demos
feb sales
Anjali pipeline
my follow-ups
find lead BEI Building
search lead 9876543210
my rank
last month sales with notes
```

### Sales Assistant
```
what is our pricing for Business+ plan?
write a follow-up email for a construction company that saw our demo 3 days ago
client is saying its too expensive, kya bolu?
compare us with Powerplay
how to approach a large infrastructure company
what modules are in Enterprise plan?
help me close this deal — they're High Prospect but haven't responded in a week
draft a WhatsApp message for demo reminder
what's the difference between Business and Business+?
```

### Context-Aware (uses conversation memory)
```
find lead BEI Building          → finds lead with details
write a follow-up for that lead → knows you mean BEI Building
what stage is same lead at?     → remembers the lead from history
```

---

## Deployment

### Frontend (Vercel)
```bash
cd automations/
npx vercel --prod --yes
# Deploys to onsite-pulse.vercel.app
```

### Backend (n8n)
```bash
cd automations/
python3 deploy_to_n8n.py 9
# Or update existing workflow:
python3 -c "
from deploy_to_n8n import build_workflow_json
import requests
wf = build_workflow_json('9')
requests.put('https://n8n.srv1184808.hstgr.cloud/api/v1/workflows/POQV33R1kjfaWvus',
    headers={'X-N8N-API-KEY': '<key>', 'Content-Type': 'application/json'}, json=wf)
"
```

### Workflow ID: `POQV33R1kjfaWvus`
### Webhook: `POST https://n8n.srv1184808.hstgr.cloud/webhook/pulse-chat`

---

## Changelog

| Date | Change |
|------|--------|
| 2026-03-04 | v1.0 — Initial release: CRM data queries (demos, sales, pipeline, follow-ups, rank, target) |
| 2026-03-04 | v1.1 — AI intent detection via Grok 4.1 Fast, lead search, Zoho Notes API |
| 2026-03-05 | v1.2 — Supabase conversation memory (last 5 messages per user) |
| 2026-03-05 | v1.3 — Sales Assistant with full Onsite knowledge (pricing, objections, competitors, email drafting) |
| 2026-03-05 | v1.4 — WhatsApp auto-delivery via Gallabox for useful responses |
| 2026-03-05 | v1.5 — Mobile-first UI overhaul (safe areas, keyboard handling, 100dvh, PWA meta) |

---

## Future Ideas

- [ ] "Send to client" — draft + send email directly from chat
- [ ] Voice input — speech-to-text for hands-free queries on site
- [ ] Daily digest — auto-send morning summary to each rep
- [ ] Lead scoring — AI rates pipeline leads hot/warm/cold
- [ ] Quick reply templates — one-tap responses to common client questions
- [ ] PWA install — add to home screen as native app
