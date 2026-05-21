# Product Requirements — Onsite Task AI Add-On Stack

> **Extends:** `PRD.md` (Phase 1 MVP, shipped May 17, 2026)
> **Adds:** RAG · Real-Time Voice · Training · Support/Escalation
> **Owner:** Dhruv Tomar (AI Builder at Onsite) | **PM:** Angelina
> **Last updated:** 2026-05-19 | **Status:** Draft v1.0

This PRD layers four add-ons onto the existing `/task-bot` surface. Read `PRD.md` first for the foundation product; this doc covers only what changes.

---

## 1. Why now

The existing bot solves "I want to take an action without 8 taps." Customer demos surface three related problems we haven't yet solved:

1. **Customers can't find answers in the app.** They paste questions into Notion (vendor-locked, weak search), email Onsite support, or call Sumit's team. Cost on Onsite's side: ~30 support hours/week. RAG removes most of this.
2. **New users churn at week-2 because they can't learn the app.** Per Apr 14-24 Fireflies analysis (216 demos), "app too complex" is the #1 cited friction. Training removes this.
3. **Site engineers want hands-free.** Voice-input ships in MVP, but it's typing-via-mic. A true voice loop (gloves on, eyes off the screen, machinery noise) doesn't exist yet.

Add-ons make the bot the **primary AI surface inside Onsite**, not a dependency-creator. Sumit's sales narrative becomes "your team learns Onsite by talking to it."

---

## 2. Personas (deltas from `PRD.md`)

### 2.1 New persona — "Suresh, the new site supervisor (week 1)"

- Just hired by a construction company that bought Onsite 3 weeks ago
- Knows construction, doesn't know software
- Cares about: not looking dumb in front of project manager; getting his first DPR submitted without help
- **What he says about Training:** *"AI ne mujhe sikha diya, ek-do baar mein samajh aa gaya."*
- Failure mode without us: he stops using Onsite by week 2, his team falls back to WhatsApp, the company hits the "app too complex" cancellation moment around month 3.

### 2.2 New persona — "Priya, Onsite's customer support lead"

- 4-person support team, 200+ tickets/week, ~30% are "how do I" questions
- Cares about: ticket deflection (her capacity is the bottleneck on Onsite's growth)
- **What she says about Support add-on:** *"Tier-1 questions ab AI handle kar leta hai, hum sirf real problems pe focus karte hain."*

### 2.3 Updated persona — "Rakesh, the Project Manager" (existing)

- Now ALSO uses RAG for SOP lookups ("RA bill ka format dikhao") + voice for hands-free site walk-throughs ("Foundation Wall pe 12 sqft progress log karo")

### 2.4 Updated persona — "Sumit, founder" (existing)

- Now has a **single coherent sales story**: action + answer + onboarding + voice = "Onsite is the AI-native construction OS." Procore/Powerplay can't tell that story.

---

## 3. Goals & Non-goals (per add-on)

### 3.1 RAG (knowledge base)

**Goals:**
- Replace Notion as the QUERY surface for Onsite product docs. Notion stays as the AUTHORING surface (per `DECISIONS-ADDON.md` D2).
- Customer asks "how do I X" in any of EN / HI / Hinglish / TA — bot retrieves chunks + cites source + answers in user's register.
- Indexing of ~500 pages (Onsite KB + BOQ formats + Material Library + competitor / market context) within Sprint 1.
- Notion sync every 6 hrs (incremental diff via `last_edited_time`).

**Non-goals:**
- We do not replicate Notion's authoring UI (page editor, comments, sharing). Customers keep using Notion to write.
- We do not auto-retire Notion at any timeline (per D2).
- We do not index customer-side data (their project tasks live in Onsite's API, not in Notion). RAG corpus = Onsite product docs only.
- No public-facing KB SEO pages (out of scope; that's a marketing site project).

**Success metric:** 70% of question-shaped queries answered without escalating to support ticket. Measured via tier-1 deflection rate on Support add-on (see 3.3).

### 3.2 Real-Time Voice

**Goals:**
- Browser/mobile-web hands-free loop: user speaks, bot understands, calls tools, speaks back.
- Default: Gemini 3.1 Flash Live (Hindi/Hinglish wins, ~$1.40/hr — per `voice-models-comparison.pdf`). Fallback: GPT-4o-mini Realtime when user locale is English-only or Gemini fails health-check.
- Tool calling parity with text: every one of the 14 text-mode tools (plus new RAG / training / support tools) callable via voice.
- Push-to-talk mode for noisy sites (VAD threshold 0.9 or commit-on-button-release).
- 30-min wall-clock cap per session. 30 min/day Free, 200 min/day Pro per `DECISIONS-ADDON.md` D8.

**Non-goals:**
- PSTN / phone-call voice (out of scope MVP — Twilio Media Streams bridge is a separate sprint we'll size when Sumit asks).
- Native iOS / Android apps. Browser + WebView only.
- Voice cloning. We use stock Gemini / OpenAI voices.
- TTS in languages outside EN/HI/Hinglish/TA at MVP.

**Success metric:** ≥95% successful tool calls on voice path with no degradation vs text. p95 round-trip latency ≤700ms (mic-end → audio-out start).

### 3.3 Support / Escalation

**Goals:**
- 3-tier flow: RAG answer → ticket creation → human page.
- Tier-1 auto-resolve target: ≥60% of question-shaped queries by week 4 of production.
- Our own ticket queue (`support_tickets` table) with `external_ticket_id` reserved for future Onsite-system forward (D3).
- Immutable audit log (Postgres `CREATE RULE ... DO INSTEAD NOTHING` per MedAssist pattern).
- Urgency taxonomy: Critical (5 min), High (15 min), Normal (1 hr), Low (24 hr). Telegram + email pagers via existing creds.

**Non-goals:**
- Built-in CRM / agent assignment workflow (deferred).
- Customer-facing ticket portal (admin-side only at MVP — customers see status in chat).
- Auto-resolve on account / billing / security categories (hard-routed to humans regardless of RAG match — non-negotiable).

**Success metric:** Tier-1 deflection rate ≥60% by week 4; zero false auto-resolves on the security/billing whitelist.

### 3.4 AI Training / Onboarding

**Goals:**
- Phase-machine guided 7-module curriculum: Dependencies → Progress → RA Bills → BOQ → DPR → Attendance → Materials.
- ~5-8 min per module, voice-first with text fallback.
- M1 (Dependencies) + M2 (Progress) demo **real actions** in user's sandbox project. M3-M7 demo **RAG-explain mode** with embedded screenshots until Akshansh's API ships (D6).
- Auto-generated SM-2 flashcards (5-7 per module) for spaced review on days 1/3/7/14/30+.
- Daily 60-second review push on welcome screen: *"4 cards due. 1 min. Review?"*

**Non-goals:**
- Authored-by-Onsite content (we use the same RAG corpus; no separate CMS).
- Certification / quizzes-with-passing-scores at MVP (passes-on-completion only).
- Per-customer module customization at MVP (one curriculum for all tenants).

**Success metric:** ≥40% of net-new Onsite users complete Module 1 within 7 days; ≥25% complete Module 2 within 14 days.

---

## 4. Functional Requirements

### 4.1 Must-have (Sprint 1-7)

| ID | Requirement | Add-on |
|---|---|---|
| FA1 | Multi-format ingest (PDF/DOCX/XLSX/PPTX/TXT/MD/CSV/HTML, ≤50MB) | RAG |
| FA2 | Gemini Embedding 2 (768-dim) + pgvector cosine + BM25 hybrid + per-doc cap | RAG |
| FA3 | `search_knowledge_base` tool wired into existing route | RAG |
| FA4 | Citation card with `[Source: doc.pdf, p3]` clickable | RAG |
| FA5 | Notion 6-hourly diff sync | RAG |
| FA6 | Admin upload UI at `/task-bot/admin/knowledge` | RAG |
| FB1 | Gemini Live WS proxy (lift from QH `198dc29`) | Voice |
| FB2 | OpenAI Realtime mini fallback (lift from QH `stable-v11.2`) | Voice |
| FB3 | Dual event-name handler (`response.audio.delta` + `response.output_audio.delta`) | Voice |
| FB4 | 48kHz→24kHz worklet resample (lift HireAI `pcm-processor.js` verbatim) | Voice |
| FB5 | Mic-gate while AI speaks (lift LearnOS `useVoiceChat.ts:238-239`) | Voice |
| FB6 | Gapless PCM playback via `scheduledTimeRef` (lift LearnOS `:142-144`) | Voice |
| FB7 | Provider router (language + health-check + circuit breaker) | Voice |
| FB8 | Per-tenant daily minute cap (Redis counter) | Voice |
| FB9 | Push-to-talk toggle | Voice |
| FC1 | `create_support_ticket` tool + admin queue page | Support |
| FC2 | 3-tier urgency + escalation chain via Vercel Cron | Support |
| FC3 | Duplicate-suppression (5-min Redis fingerprint) | Support |
| FC4 | Immutable audit log (Postgres `RULE no_delete`) | Support |
| FD1 | `TrainingStateMachine` (port HireAI lines 138-292 to TS) | Training |
| FD2 | 7-phase prompt set (WELCOME/CHOOSE_MODULE/INTRO/DEMO/QUIZ/RECAP/COMPLETE) | Training |
| FD3 | Demo phase fires real tool in sandbox (M1+M2 only at launch) | Training |
| FD4 | RAG-explain demo mode for M3-M7 | Training |
| FD5 | SM-2 flashcards (port LearnOS `flashcards.py`) | Training |
| FD6 | Daily review push on welcome screen | Training |

### 4.2 Should-have (Sprint 8-10)

| ID | Requirement | Add-on |
|---|---|---|
| FA7 | Reranker (Cohere Rerank 3 or Gemini reranker) | RAG |
| FB10 | Telephone bridge (PSTN via Twilio Media Streams) | Voice |
| FC5 | Customer-facing ticket status view | Support |
| FD7 | Per-tenant module overrides | Training |
| FD8 | Cohort-level completion analytics | Training |

### 4.3 Nice-to-have (Phase 4+, after this stack ships)

| ID | Requirement |
|---|---|
| F-VOICE-CLONE | Voice cloning of Sumit / Akshansh as bot persona |
| F-MULTI-MODAL | Image upload in chat (progress photo → "log this") |
| F-RAG-FEDERATED | Index per-customer data (their projects/tasks) — requires consent + RLS audit |
| F-OFFLINE | Offline voice transcription (IndianWhisper integration) |

---

## 5. Non-Functional Requirements

### 5.1 Performance budgets

| Path | Target | Notes |
|---|---|---|
| RAG search (top-5 hybrid + rerank) | <800ms p95 | Embedding 100ms + pgvector 200ms + BM25 200ms + rerank 200ms + headroom |
| RAG-augmented chat reply | <2.5s p95 | RAG 800ms + Claude reasoning 1.5s |
| Voice mic→AI-speech | <700ms p95 | Per Gemini Live spec ~250-300ms; add WS overhead |
| Voice tool call latency | <1.5s p95 | Tool dispatch reuses text path |
| Training quiz advance | <1s p95 | LLM judge call only |
| Support ticket create | <1s p95 | DB write + escalation row only |

### 5.2 Reliability

- **RAG indexing watchdog:** doc stuck in `processing` >10 min → cron re-queues (per KnowledgeForge §10 gotcha #8).
- **Voice circuit breaker:** Gemini >5% error rate over 5-min sliding window → all-to-mini fallback flag.
- **Support escalation backstop:** cron runs every 60s; any ticket past its SLA without ack gets paged.
- **Training session recovery:** browser refresh during a module → restore from `training_progress` row, resume at last phase.

### 5.3 Security & Privacy (deltas from `HLD.md` §5)

- **JWT invariant preserved** for all 4 add-ons — token never logged, never sent to LLM, never persisted beyond the request lifecycle.
- **New persistent tables introduce tenant-scoped data.** RLS-by-`user_id` (NOT `company_id` — Onsite's JWT does not carry company_id reliably; see `MEMORY.md` 2026-05-17 auth notes). Every query filtered.
- **Voice transcripts retained 30 days** for QA + training-data export, then auto-purged. User can request deletion (DPDP compliance).
- **Audit log:** Support audit table is append-only via Postgres RULE. RAG queries logged with hashed user_id + query (no full content stored for >90 days).
- **Voice carries the JWT through to tool execution** but the LLM only sees the conversation messages; the WS proxy strips the token from any outbound message to Gemini/OpenAI.

### 5.4 Scale targets (Phase-2 stack at full Onsite scale)

| Metric | Target | Mechanism |
|---|---|---|
| Concurrent text+voice users | 1,500 | Vercel auto-scale (text) + Modal/Fly scale-to-zero (voice WS) |
| Daily chat messages | 100K | Existing |
| Daily voice minutes | 1.5M cumulative (10K customers × 5 min × 30 days; theoretical full-scale) | Per-tenant cap (D8) keeps real usage in budget |
| Daily RAG queries | 50K | pgvector with HNSW handles >1K QPS on Supabase Pro |
| Daily tickets | 500 | Trivial for Postgres + Telegram pager |
| Daily flashcard reviews | 20K | One row read per review, batched |

### 5.5 Localization

- RAG: query embeddings handle EN/HI/Hinglish/TA natively (Gemini Embedding 2). Citations rendered in user's language.
- Voice: Gemini Live primary for non-English; OpenAI mini fallback (English-strong).
- Training: 7 modules authored in EN; bot translates on the fly per user register.
- Support: bot acknowledges in user's register; escalation messages to ops in EN (single ops language).

---

## 6. Risks (deltas from `PRD.md` §8)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Notion sync silently drifts | Med | Med | Admin UI "last sync OK X min ago" + alert at 24h staleness |
| Voice 30-min cap surprises a user mid-demo | High | Low | Visual countdown last 5 min; friendly close + text-mode handover |
| Gemini Live preview SKU deprecates | Med | High | Env-flag override to OpenAI mini; A/B scripts kept in repo |
| Tier-1 auto-resolve false positives on security/billing | Low | High | Hard-coded category whitelist; security topics route to humans regardless of RAG match |
| Module 3-7 RAG-explain feels hollow vs real demo | High | Med | Pre-flight all 7 module queries against seeded corpus in Sprint 8 QA |
| Voice infra deploy hits Vercel WS limit | High | High | Voice WS server runs on Modal/Fly (D7), not Vercel |
| API key budget on Onsite's account hits caps | Med | Med | Set spend alerts on Onsite's billing dashboards; AIwithDhruv covers if Onsite cap not raised in time |
| Akshansh API for add_task/add_subactivity never ships | Med | Med | Training M3-M7 in RAG-explain mode (D6); RAG-only is still valuable |
| Cost spirals past $40K/mo at scale | Med | High | Per-tenant minute cap (D8); model routing pushes ≥80% to Gemini Flash |

---

## 7. Success Metrics (Phase-2 stack as a whole)

### 7.1 Adoption (first 4 weeks of production)

- ≥20% of Onsite's active monthly users try the bot at least once
- ≥40% of triers complete Training Module 1
- ≥10% of triers initiate a voice session

### 7.2 Quality

- RAG: ≥75% of question-shaped queries answered without follow-up clarification
- Voice: ≥95% tool-call parity vs text mode
- Support: ≥60% Tier-1 deflection rate by week 4
- Training: median module completion in ≤9 minutes

### 7.3 Business

- ≥25% reduction in "app too complex" support tickets (Priya's KPI)
- 1.5× increase in demo close rate when the full Phase-2 stack is shown (Sumit's KPI)
- Reduce mean time-to-first-meaningful-action for new users from 3.2 days → <1 day (Onboarding KPI)

---

## 8. Out-of-scope (explicit)

| Excluded | Reason |
|---|---|
| Notion authoring replacement | Customers like Notion's editor; we don't compete with it (D2) |
| Outbound PSTN voice | Twilio Media Streams bridge is a separate sprint |
| Native mobile apps | Browser/WebView only |
| Customer-specific KB tenancy | Initial corpus is Onsite product docs (org-level). Per-tenant KB indexing is Phase 4 |
| Auto-resolve on security/billing/account topics | Hard-routed to humans regardless of RAG confidence |
| Cross-customer ticket aggregation | Each tenant's tickets isolated by RLS |
| Self-service customer training-content authoring | Onsite-authored only at MVP |
| Stripe-style metered LLM billing back to customers | Onsite pays prod keys (D4); per-customer attribution is Phase 4 |

---

## 9. References

- `PRD.md` — Phase 1 foundation
- `HLD-ADDON.md` — architecture extensions for these 4 add-ons
- `ROADMAP-ADDON.md` — 10-sprint plan
- `DECISIONS-ADDON.md` — open-question resolutions
- `ANGELINA-ADDON-DISPATCH.md` §11 — code-copy reference index
- `euron-references/REPORT-hireai.md`, `REPORT-knowledgeforge.md`, `REPORT-learnos.md`
- `euron-references/voice-models-comparison.pdf` — provider economics
