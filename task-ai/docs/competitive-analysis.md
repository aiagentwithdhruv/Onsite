# Competitive Analysis — Onsite Task AI

> Why this product wins. Skeleton — fill in details after research.

**Status:** Skeleton v1.0 — needs Phase 2 research

---

## The Competitive Map

```
Action-taking         │ Onsite Task AI (us)
AI bots in            │ (Phase 1: build) ← we are here
construction SaaS     │
─────────────────────┼─────────────────────────────────
                      │ Procore Copilot (US, mature)
Q&A AI bots          │ Buildxact AI (AU)
in construction      │ Onsite's existing bot (unknown scope)
                      │
─────────────────────┼─────────────────────────────────
                      │ Microsoft Copilot (general)
No AI / chatbot      │ Powerplay (India)
(traditional UI)      │ NYGGS, StrategicERP, RDash
                      │ FalconBrick, Highrise, NWAY
```

**Our position:** First action-taking AI in India construction SaaS.

---

## Direct Competitor: Onsite's Existing AI Bot

> **Status:** Need to research. Dhruv mentioned it exists, scope unknown.

**Research questions:**
- What features does it have? (Q&A, BOQ extraction, sales coach, internal vs customer-facing?)
- Where in the UI does it live?
- Is it monetized separately, or bundled?
- What's its monthly usage?
- Does it modify project data, or just answer questions?

**Our positioning options:**
1. **Complementary:** Existing bot = "ask anything", our bot = "do anything." Co-existence.
2. **Replacement:** Our bot subsumes the old one. Higher risk, bigger win.
3. **Distinct product:** Sold separately as a premium add-on.

**Recommended:** Talk to Akshansh in Phase 2 to align. He may already have a vision.

---

## Indirect Competitor: Procore Copilot (USA)

**Procore** is the global category leader ($199–375/user/month). Their Copilot launched 2024 and does:
- Q&A over project data ("what's the schedule for Phase 2?")
- Document summarization (RFI responses, change orders)
- Predictive insights (cost overrun warnings)
- Not (yet) action-taking on the same scale we're building

**Our advantages:**
- **India-first:** Hindi-English code-switching, Indian construction terminology (RA Bills, BOQ, DPR, GST), regional language voice input
- **Action-taking:** We modify project data; they mostly answer questions
- **Onsite-native:** Embedded in Onsite, not a bolt-on
- **Price:** Procore's bot bundled with $200+/user/month plans; we can be priced for India (~₹100/user/month feasible)

**Their advantages:**
- Mature data model + integrations (BIM, scheduling tools)
- Massive training data from years of projects
- Existing customer trust + sales motion

**Lesson to steal:** Their action-taking will come. Move fast to establish position in India before they pivot global.

---

## Indirect Competitor: Powerplay (India)

**Powerplay** is Onsite's #1 India competitor. Budget-friendly, mobile-first, 700K+ users, 85K projects.

**Status of their AI:** No customer-facing action-taking bot as of 2026-Q1 (verify before Phase 3 launch).

**If they ship a similar bot:**
- Likely 6+ months behind us if we ship Phase 3 by Q3 2026
- Their advantage: larger install base, more data
- Our advantage: first-mover; integrations with Onsite's existing differentiators (Tally, Zoho)

**Lesson:** Phase 3 timing matters. Earlier = bigger moat.

---

## Indirect Competitor: ChatGPT / Claude.ai (General LLMs)

A customer COULD type their question into ChatGPT and get good text. They cannot:
- Take action on their actual Onsite data
- Access their projects (without manually pasting context)
- Get auditable, role-permissioned execution
- Use Hindi voice integrated into their workflow

**This is our defensive moat:** General LLMs are read-only narrators of the world. We're the actuator into Onsite.

---

## Feature Comparison Matrix

| Feature | Onsite Task AI (us, Phase 3 target) | Procore Copilot | Powerplay (none yet) | ChatGPT |
|---------|-------------------------------------|----------------|---------------------|---------|
| Create dependencies via NL | ✅ | ❌ (Q&A only) | ❌ | ❌ |
| Log progress via NL | ✅ | ❌ | ❌ | ❌ |
| Hindi voice input | ✅ Phase 3 | ❌ | ❌ | ⚠️ (no Onsite integration) |
| Embedded in app | ✅ | ✅ | N/A | ❌ |
| Audit log per action | ✅ Phase 3 | ✅ | N/A | ❌ |
| Cost per active user/month | ₹100 target | $30+ | N/A | Free / $20 |
| Modify real project data | ✅ | Partial | ❌ | ❌ |
| Multi-language (4 Indian langs) | ✅ Phase 3 | ❌ | ❌ | ⚠️ |

---

## Pricing Positioning Hypothesis (refine with Sumit)

| Plan | Onsite price (current) | Bot pricing options |
|------|------------------------|---------------------|
| Business (₹12K/user/yr) | Bot as paid add-on at ₹100/user/month |  |
| Business+ (₹15K/user/yr) | Bot bundled (used as upsell hook) |  |
| Enterprise (₹12L lump) | Bot included; emphasized as premium feature |  |

**Hypothesis:** Bot as a "Business+ upsell driver" yields more revenue than as a separate paid feature on Business. Customers upgrade plans to get the bot.

---

## What Could Beat Us

1. **Onsite kills the project** (internal politics, refocus elsewhere)
2. **A competitor (Procore India entry, or a startup) ships a similar bot first** — but they'd need: Onsite-grade construction data model, Indian language support, integration with an installed SaaS base
3. **LLM cost spikes** make ₹100/user/month margins unfeasible — mitigated by smart routing (Haiku for simple ops)
4. **A bug ships that loses customer data** — destroys trust; recoverable but expensive

---

## What Makes Sumit's Demo Win

Imagine the demo:

> Sumit: *"Watch this."* [opens Onsite on phone, taps the AI button]
> Sumit (speaks): *"Soul Space mein Electrical panel Setup ke baad Fixture installation start hona chahiye."*
> Bot (replies in Hindi): *"Theek hai, FS dependency banata hoon. 0 days lag, confirm?"*
> Sumit: *"Haan."*
> Bot: *"Done. Aap Gantt mein dekh sakte hain."*
> Sumit (shows Gantt with the new FS arrow live): *"Yeh feature hai. Koi aur software India mein nahi de raha."*

That's the demo that closes deals. Phase 3 must enable this exact moment.

---

## Research TODO (Phase 2)

- [ ] Find and screenshot Onsite's existing AI bot (where is it? what does it do?)
- [ ] Check Procore Copilot's latest features (their changelog / blog)
- [ ] Check if Powerplay / NYGGS / RDash have shipped any AI features
- [ ] Survey 5 Onsite customers on what they wish the app could do via voice
- [ ] Find pricing examples of B2B AI features in vertical SaaS (Salesforce Einstein, HubSpot Breeze)
