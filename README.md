# Onsite — Internal Tools & Automation

**ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED** | [onsiteteams.com](https://www.onsiteteams.com)

Internal tools for Onsite Teams — Construction Management Software.

---

## Projects

| Project | Description | Status |
|---------|-------------|--------|
| [**Sales Intelligence**](sales-intelligence/) | AI-powered pipeline analysis, smart alerts, daily briefs | Running |
| [**Quotations**](quotations/) | Automated quotation/proforma invoice generator | Running |
| [**Task AI**](task-ai/) | Customer-facing AI chatbot — natural-language task dependencies + progress logging via Onsite v3 API. Code in [`aiagentwithdhruv/onsite-hub`](https://github.com/aiagentwithdhruv/onsite-hub) | MVP Shipped (2026-05-17) |
| [**Onsite Hub**](https://github.com/aiagentwithdhruv/onsite-hub) | Next.js PWA hosting (a) internal sales assistant for the 16-rep team and (b) the customer-facing Task AI chatbot at `/task-bot` | Local dev / pre-deploy |

---

## Structure

```
Onsite/
  sales-intelligence/       → AI Sales Intelligence (backend + frontend)
  quotations/                → Quotation generator + templates
  task-ai/                   → Task AI product docs (PRD, HLD, LLD, ROADMAP, ADRs)
  database/                  → Supabase SQL migrations
  docs/                      → Design specs + guides
  scripts/                   → Utility scripts
  knowledge/                 → Market research, competitors
  runbooks/                  → Deployment guides
```

> **Note:** The Task AI code lives in a separate repo ([`onsite-hub`](https://github.com/aiagentwithdhruv/onsite-hub)) because it's part of a customer-facing Next.js app. The `task-ai/` folder in this repo holds only the product documentation (architecture, decisions, roadmap, multi-tenancy strategy).

Each project has its own `README.md` with setup instructions and details.

---

## Team

| Name | Role |
|------|------|
| Dhruv Tomar | Founder / Admin |
| Sales Team (21 users) | Reps, Team Leads, Managers |

---

**Proprietary** — All rights reserved.
