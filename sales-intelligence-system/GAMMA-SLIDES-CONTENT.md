# Sales Intelligence System — Gamma Slide Deck Content

Use this document in **Gamma.app** to generate a ~10-slide deck. In Gamma: create a new presentation, then use "Add with AI" or paste each section as the prompt/outline for one slide. You can also copy slide-by-slide into bullet points manually.

---

## Slide 1 — Title

**Title:** Sales Intelligence System  
**Subtitle:** AI-powered pipeline visibility and smart alerts for Onsite Teams  
**Optional line:** Internal product — ABEYAANTRIX TECHNOLOGY PRIVATE LIMITED

---

## Slide 2 — The problem we solve

**Title:** Why we built this

- Sales pipeline lives in CRM exports (CSV); reps and managers don't always see what's due **today** or **overdue**.
- **Notes and remarks** in the CRM often contain next steps — but nobody gets alerted when they need action.
- Multiple AI providers (Claude, GPT, OpenRouter, Moonshot) — we wanted **one place** to choose models and store API keys, without touching .env.
- Alerts were scattered or manual; we needed **structured digests** (morning / afternoon / evening) and **testable** delivery (e.g. Telegram).

**Guidance for Gamma:** Use a simple "problem statement" layout; 4 short bullets.

---

## Slide 3 — Solution in one line

**Title:** What it does in one sentence

**One sentence:**  
Upload a pipeline CSV → the system scores leads, detects anomalies, surfaces follow-up dates and "notes that need action," and sends **smart alerts** and **daily digests** (Telegram + email) so reps and founders never miss the next best action.

**Guidance for Gamma:** Single big quote or one sentence in the center; minimal text.

---

## Slide 4 — End-to-end flow (high level)

**Title:** How data flows

1. **Upload** — Manager/admin uploads CRM/pipeline CSV (Deal Owner, Stage, Followup Date, Notes, etc.).
2. **Process** — Backend (FastAPI) parses, normalizes columns, stores in Supabase; AI scores and ranks leads.
3. **Alert** — Smart alerts (overdue, due today, due tomorrow, notes need action, high-value) batched per user.
4. **Deliver** — Telegram and/or email; 3× daily digests (morning / afternoon / evening, IST).
5. **Act** — Dashboard and Alerts page show what to do next; "Send test alert" validates delivery.

**Guidance for Gamma:** Numbered flow or simple diagram (Upload → Process → Alert → Deliver → Act).

---

## Slide 5 — Features (Part 1): Pipeline & Alerts

**Title:** Core features — Pipeline and smart alerts

- **CSV-driven pipeline** — Flexible column names (Followup Date, notes/remarks, Deal Owner). Cached in Supabase for dashboard and alerts.
- **Smart alert types** — Overdue follow-up, due today, due tomorrow, **notes need action** (lead name + phone + snippet), high-value, anomaly.
- **User preferences** — Each user turns alert types on/off, adds Telegram Chat ID, and can trigger "Send test alert."
- **Batched delivery** — On CSV upload, one batched message per user (Telegram/email) so reps aren't spammed.

**Guidance for Gamma:** 4 bullets; optional icons for "Pipeline," "Alerts," "Preferences," "Batched."

---

## Slide 6 — Features (Part 2): Digests, LLM, Telegram

**Title:** Core features — Digests, LLM, and Telegram

- **3× daily digests** — Morning (8 AM), afternoon (2 PM), evening (6 PM) IST. Structured templates; cron hits backend routes.
- **LLM & model selection** — Admins set API keys (Anthropic, OpenAI, OpenRouter, Moonshot) in **Settings**; keys stored in DB. Choose **Primary**, **Fast**, and **Fallback** models from a curated list (e.g. Claude Sonnet, Haiku, GPT-4o, OpenRouter models).
- **Telegram** — Manager+ adds bot token in Settings (stored in DB). Users add Chat ID on Alerts page. "Send test alert" confirms delivery with clear errors (no token, no Chat ID, or API failure).

**Guidance for Gamma:** 3 bullets or 3 columns (Digests | LLM | Telegram).

---

## Slide 7 — Use cases (who uses it and how)

**Title:** Who uses it and how

| Role | Use case |
|------|----------|
| **Rep** | See dashboard, turn on/off alert types, add Telegram Chat ID, get digests and smart alerts; act on "due today" and "notes need action." |
| **Team lead / Manager** | Upload pipeline CSV; configure Telegram bot token; see team-level view; ensure test alerts work. |
| **Founder / Admin** | Set LLM API keys and Primary/Fast/Fallback models in Settings; manage users; view AI usage; control cost and provider mix. |

**Guidance for Gamma:** Table or 3 short cards (Rep | Manager | Admin) with 1–2 lines each.

---

## Slide 8 — Tech stack (one line each)

**Title:** Tech stack

- **Backend:** FastAPI, Supabase (DB + auth), LangChain (Anthropic, OpenAI, OpenRouter, Moonshot), APScheduler (cron), Resend (email).
- **Frontend:** Next.js, Tailwind, Recharts; dashboard, Alerts, Settings.
- **Data:** CSV upload → normalized pipeline; `app_config` for API keys, Telegram token, model selection; smart_alerts and alert_delivery_channels for preferences.

**Guidance for Gamma:** 3 bullets or 3 stacks (Backend | Frontend | Data). Keep wording short.

---

## Slide 9 — Model selection (for founders)

**Title:** How we choose AI models

- **No .env for keys** — Admins set OpenAI, Anthropic, OpenRouter, Moonshot in **Settings → LLM Providers**; stored in DB.
- **Three slots** — **Primary** (complex tasks), **Fast** (scoring/ranking), **Fallback** (when primary fails). Dropdowns show a fixed list of top models (aligned with Angelina/Vercel-style options).
- **One place** — Backend builds the right client (Anthropic, OpenAI, OpenRouter, Moonshot) from the selected model id; no code change needed to switch providers.

**Guidance for Gamma:** 3 bullets; optional screenshot of Settings model dropdowns.

---

## Slide 10 — Deployment and next steps

**Title:** Deployment and next steps

- **Deploy today:** Backend → Railway / Render / Fly (Docker or `uvicorn`). Frontend → Vercel or `npm run build && npm run start`. Cron → call `/api/cron/digest-morning`, `-afternoon`, `-evening` on schedule.
- **Already done:** CSV pipeline, smart alerts (including follow-up dates and notes need action), 3× digests, Telegram + email, LLM keys + model selection in UI, test alert.
- **Next (optional):** Zoho sync, WhatsApp (Gupshup), more alert types, role-based dashboard filters.

**Guidance for Gamma:** 3 short sections: Deploy | Done | Next. End with a "Questions?" or contact line if you like.

---

## How to use this in Gamma

1. Go to [gamma.app](https://gamma.app) and create a new presentation.
2. For each slide, use **"Add with AI"** and paste the **Title** + bullets (or table) from the section above. Gamma will generate a designed slide.
3. Or add a blank slide and type/paste the content manually for full control.
4. Keep **GAMMA-SLIDES-CONTENT.md** in the repo so that when you say "you have the idea" later, we can refer to this file for context and extend the deck (e.g. more use cases, screenshots, roadmap).

---

## Quick reference: slide titles only

1. Sales Intelligence System (title)  
2. Why we built this  
3. What it does in one sentence  
4. How data flows  
5. Core features — Pipeline and smart alerts  
6. Core features — Digests, LLM, Telegram  
7. Who uses it and how  
8. Tech stack  
9. How we choose AI models  
10. Deployment and next steps  
