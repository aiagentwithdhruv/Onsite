# Business Requirements — Onsite Task AI v2 (Smart Construction Intelligence Platform)

> **Status:** Final | **Date:** 2026-05-22 | **Owner:** Dhruv Tomar | **Approver:** Akshansh + Sumit
> **Companion docs:** [PRD-V3.md](./PRD-V3.md) · [ARCHITECTURE-V3.md](./ARCHITECTURE-V3.md) · [HLD-V3.md](./HLD-V3.md) · [LLD-V3.md](./LLD-V3.md)

---

## 1. Executive summary (one paragraph)

Onsite Task AI v2 is a natural-language AI assistant embedded in Onsite's construction-management SaaS that lets contractors, project managers, site engineers, and workers run **all 100+ Onsite operations** by talking — in text, voice, photo, or video. Built on a 2-tier LLM (Gemini Flash → Claude), hybrid multimodal RAG (Gemini Embedding 2), 4-tier memory, vision-based document AI, voice realtime, and a Python action runner. Targets **₹12/user/month at 99.5% accuracy** and scales to **lakhs of users** without a rewrite. Differentiates Onsite from Procore/Powerplay/RDash with a UX no competitor has shipped.

## 2. Market opportunity

| Metric | Value |
|---|---|
| Global construction software (2025 → 2034) | $10.64B → $24.72B (9.7% CAGR) |
| India construction software (2025) | ~$0.28B (11.4% CAGR) |
| India construction industry (2025) | $740B / ₹22.77T |
| India infra budget (FY25-26) | ₹50.7T / $603B |
| Asia-Pacific software CAGR | 10.98% (fastest growing region) |

**Indian-market unique drivers:** Government infra push (Bharatmala 26,425 km, Smart Cities 5,151 projects) · RERA + GST compliance forcing digital adoption · 10-30% cost overruns creating urgent demand · 42% of contractors cite "lack of digital skills" → AI-natural-language solves directly.

## 3. Onsite's current position (baseline)

- 10,000+ companies using the platform, ₹81.6 Cr valuation, $1.72M raised
- ₹200-250/user/year subscription (10-20× cheaper than Procore)
- Existing differentiators: ISO certified, mobile-first, Hindi support, 1-2 week implementation
- **Gap competitors will close in 12-18 months**: voice/conversational AI, multimodal doc intelligence, predictive recommendations

## 4. Why AI now

1. **Window is closing** — Powerplay, NYGGS, RDash will add AI in 2026. Whoever ships first owns the narrative.
2. **Costs collapsed** — Gemini Embedding 2 + 2-tier LLM routing makes ₹12/user/mo economics work. In 2024 same stack would cost ₹120.
3. **Adoption blocker is solved** — 42% "lack of digital skills" was the #1 sales objection. Natural-language voice + Hindi removes it entirely.
4. **Compliance accelerator** — RERA / GST automation reduces 60-70% manual workload — selling on ROI gets easy.
5. **Mobile-first matches reality** — site workers use phones, not laptops. Our PWA + voice + WhatsApp pipeline fits the actual workflow.

## 5. Business objectives

| Objective | 90-day target | 12-month target |
|---|---|---|
| Activate users | 200 pilot users across 10 customers | 50,000 DAU |
| Conversion (free → paid) | 30% on existing Onsite tenants | 60% |
| Cost per query (LLM + infra) | ₹0.10 | ₹0.04 |
| Gross margin | 85%+ | 95%+ |
| ARR add-on | ₹50L | ₹15Cr |
| Customer NPS lift | +20 vs Onsite baseline | +35 |
| Time saved per user/day | 30 min | 60 min |

## 6. Target users + personas

| Persona | Job | Daily AI use | Pain we solve |
|---|---|---|---|
| **Site Worker** | Logs progress, uploads photos | Voice notes via WhatsApp, photos with auto-classify | Can't type, low literacy, Hindi-first |
| **Site Engineer** | Manages 3-5 tasks/day, reports issues | Voice + chat, "log 5 sqm on Foundation Wall" | Loses time in menus, forgets to log |
| **Project Manager** | Oversees 20-50 tasks across 2-5 projects | Chat + reports + alerts | Spends 40% time chasing status |
| **Admin / Owner** | Sees portfolio health, makes decisions | Reports, vendor performance, cost overrun alerts | Information lives in 5 tools |
| **Vendor / Subcontractor** | Submits delivery slips, invoices | Photo upload + auto-extract | Manual entry on customer's side delays payment |

## 7. Success metrics (KPIs)

**Product:**
- 7-day retention ≥ 60% (vs 35% industry avg for construction software)
- Tool success rate ≥ 95% (action completes without retry)
- Time-saved per user ≥ 30 min/day (tracked in `my_stats`)
- RAGAS retrieval precision ≥ 0.85 (RAG quality)
- Document extraction accuracy ≥ 99.5% (auto + auto-corrected)

**Business:**
- Customer Acquisition Cost ≤ ₹2,000/user
- LTV / CAC ≥ 5
- Gross margin ≥ 85% within 6 months
- Net Revenue Retention ≥ 120% (customers expand)

**Technical:**
- P50 response latency ≤ 1.5 s (text)
- P50 voice latency ≤ 800 ms
- Uptime ≥ 99.5%
- Cost per query ≤ ₹0.10

## 8. Pricing strategy (Razorpay, India default)

| Tier | Price (₹/user/month) | Includes | Target |
|---|---|---|---|
| **Free** | ₹0 | 100 chat msgs/mo, basic actions, no voice/RAG | Onsite existing customers (entry) |
| **Pro** | ₹100 | Unlimited text + memory + RAG + 100 voice min + 50 doc uploads | Mid-market contractors |
| **Enterprise** | ₹500 | Pro + unlimited voice + 500 docs + custom prompts + SLA | Enterprise contractors (Procore alternative) |
| **White-Label** | ₹2L lump sum + ₹100/user/mo | Branded as customer's own AI | OEM channel |

**Gross margin** at ₹100 tier with our ₹12/user/mo infra cost = 88%.

## 9. Stakeholders + RACI

| Role | Person | Accountable for |
|---|---|---|
| Product owner | Akshansh (CEO) | Strategic direction, customer relationships |
| Co-owner | Sumit | Sales enablement, customer feedback |
| AI architect | Dhruv | Architecture, build, deploy |
| Implementation team | Angelina (PM) + Atlas/Pixel/QA (eng) | Sprint execution |
| QA | Mehul + power-user contractors | Acceptance testing |

## 10. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM costs spike | Med | High | Per-tenant cost caps + semantic cache (cuts 30% of LLM calls) |
| Gemini API rate-limit | Med | High | OpenRouter fallback + circuit breakers |
| Prompt injection from uploaded docs | High | High | PII de-id + input sanitization + no-actions-during-doc-context |
| DPDP Act violation | Low | Critical | PII stripping before LLM, data export endpoint, consent tracking |
| Akshansh's existing webhooks break | Med | Med | Separate Onsite Task AI phone number (when budget allows) |
| Competitor catches up | High | Med | Ship continuously, build moat via memory + connector ecosystem |
| Mac Studio dies (Tier 3 future) | Low | Low | Public APIs only for now (decision #2); revisit Ollama later |
| Onsite API breaking changes | Med | High | Tool versioning + Akshansh coord protocol |

## 11. Timeline (90-day MVP, 6-month full launch)

| Quarter | Deliverable |
|---|---|
| **Q1 (May-Jun)** | Phase 0-2: demo polish + memory + 2-tier routing + cost guardrails |
| **Q2 (Jun-Jul)** | Phase 3-5: heartbeat, Python runner, RAG MVP, vision/doc intelligence, voice realtime |
| **Q3 (Jul-Aug)** | Phase 6-8: training UI, support escalation, scheduled reports, alerts |
| **Q4 (Aug-Sep)** | Phase 9-10: mobile Capacitor wrap, RBAC, public launch, billing live |

## 12. What success looks like (12 months out)

> A contractor in Sangli wakes up, opens WhatsApp, says "log yesterday's pour and check if Foundation Wall is on schedule." Bot replies in Hindi-English with the log confirmation, a photo of the wall from auto-scheduled drone footage, the BOQ page for that line item, and a calendar-aware reminder that the next dependency starts tomorrow if weather holds. Total: 8 seconds. Cost to us: ₹0.07. He paid ₹100 last month for this experience and just renewed.

**This is what we're building. The architecture in V3 makes every clause above technically feasible at ₹0.10/query and 99.5% accuracy.**
