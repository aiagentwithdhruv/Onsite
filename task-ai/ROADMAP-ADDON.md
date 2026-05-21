# Roadmap — Onsite Task AI Add-On Stack

> **Extends:** `ROADMAP.md` (Phase 1 plan, mostly delivered May 17-19)
> **Adds:** 4 add-ons, 10 sprints, ~4 weeks
> **PM:** Angelina | **Build owner:** Shailendra (per `DECISIONS-ADDON.md` D5)
> **Last updated:** 2026-05-19 | **Status:** Draft v1.0 — pending Dhruv sign-off

Sequencing overrides the dispatch's §6 plan. The biggest change (per D9): RAG completes **before** voice integration starts, eliminating the dispatch's planned Sprint 3 ("RAG-in-voice"). Net saving: ~2 days of integration work.

---

## Sprint table — overview

| Sprint | Days | Owner | Deliverable | Add-on |
|---|---|---|---|---|
| 0 | D0-D1 (now) | Angelina | PRD-ADDON, HLD-ADDON, DECISIONS-ADDON, ROADMAP-ADDON, 3 dispatch files | Plan |
| 1 | D2-D6 | Shailendra | RAG MVP: ingest + pgvector + `search_knowledge_base` tool + admin upload UI | RAG |
| 2 | D7-D11 | Shailendra | Voice loop on Modal: Gemini + OpenAI mini, dual-event handler, mic-gate, tools | Voice |
| 3 | D11-D13 | Atlas | Support Tier 1+2: ticket tool + queue + admin page + 👍/👎 wired to deflection | Support |
| 4 | D13-D15 | Atlas | Support Tier 3: SLA cron + Telegram/email pager + duplicate guard | Support |
| 5 | D14-D17 | Atlas/Pixel | Notion sync: pull-mirror 6-hourly + admin trigger + drift alert | RAG ext |
| 6 | D17-D21 | Pixel | Training MVP: phase machine + Module 1 (Dependencies) + Module 2 (Progress) live demo | Training |
| 7 | D21-D25 | Pixel | Training M3-M7 in RAG-explain mode + SME review hooks | Training |
| 8 | D25-D27 | Pixel | SM-2 spaced repetition: flashcard generator + daily review push | Training |
| 9 | D27-D29 | QA | Cross-add-on hardening: load test, circuit breaker tuning, mobile review, telemetry | All |
| 10 | D29-D30 | Shailendra+Dhruv | Pre-production gate: end-to-end smoke, Vercel deploy decision, tester kit refresh | All |

**Original §6 plan had Sprint 1+2 running parallel** (D2-D7). Pushed back via D9. Result: voice starts on D7 with RAG already as a wired tool.

**Original §6 plan put Training BEFORE Support** (Sprint 7-9 vs Sprint 5-6). I flipped them. Reason: Support is higher value (ticket deflection is a hard money metric on Sumit's side) and lower complexity (3 components vs phase machine + SM-2 + 7 modules). Ship the easier higher-value thing first.

---

## Sprint 0 — Planning (D0-D1, today)

**Owner:** Angelina
**Output:** This roadmap + 3 sibling docs + 3 dispatch files
**Gate:** Dhruv signs off on `DECISIONS-ADDON.md` D1-D9.
**Kill condition:** None — planning sprint always completes.

---

## Sprint 1 — RAG MVP (D2-D6, 5 days)

**Owner:** Shailendra (dispatched via `dispatch-sprint-1-rag.md`)
**Status:** Pending Dhruv paste-launch
**Goal:** Customer asks a knowledge question, bot retrieves chunks + cites source, all working in the existing chat surface.

**Files to ship** (per dispatch §11 RAG matrix):
1. `onsite-hub/src/lib/rag/document_service.ts` (port KnowledgeForge `document_service.py`)
2. `onsite-hub/src/lib/rag/embedding.ts` (Gemini Embedding 2 wrapper)
3. `onsite-hub/src/lib/rag/hybrid_search.ts` (pgvector + BM25 + dedup + score gate)
4. `onsite-hub/src/app/api/task-bot/kb/upload/route.ts`
5. `onsite-hub/src/app/api/task-bot/kb/search/route.ts`
6. `Onsite/task-ai/database/005_knowledge_base.sql`
7. `search_knowledge_base` tool added to `route.ts` tool registry + dispatch switch
8. `onsite-hub/src/components/task-bot/KnowledgeCard.tsx`
9. `onsite-hub/src/app/task-bot/admin/knowledge/page.tsx`
10. Seed script: ingest `Onsite/uploads/onsite-platform-knowledge-base.md` + `Onsite/uploads/boq/*` + `Onsite/uploads/material-library/*` + `Onsite/uploads/competitors.md` + `Onsite/uploads/construction-market.md`

**Acceptance gates:**
- ✅ Upload 5 docs via admin → all reach `status='indexed'` within 5 min
- ✅ Chat query "What is BOQ format" → bot fires `search_knowledge_base`, returns ≥3 chunks with sources
- ✅ Citation card renders correctly with clickable source
- ✅ `task-ai/STATE.md` updated with batch 22 entry
- ✅ Test against `testapi.onsiteteams.in` first (per `CLAUDE.md` Working rules #4)
- ✅ Type-check clean: `npx tsc --noEmit --skipLibCheck | grep task-bot` returns empty

**Kill condition:** If pgvector HNSW index build >30s on 5 docs, abort and switch to flat index. If Gemini Embedding 2 unavailable on Onsite's Google account, abort and switch to OpenAI text-embedding-3-small (1536-dim — affects schema; reset migration).

**Cost ceiling:** $5 one-time ingest + $0.001/query at runtime. No alerts needed.

---

## Sprint 2 — Real-Time Voice (D7-D11, 5 days)

**Owner:** Shailendra (dispatched via `dispatch-sprint-2-voice.md`)
**Goal:** User clicks 🎙️, speaks "log 3 sqft progress on Foundation Wall", bot acknowledges via voice + fires tool. Same for KB queries.

**Files to ship** (per dispatch §11 Voice matrix):
1. **New Modal app** `onsite-voice-server/` — Python WS proxy lifted from QH `198dc29` + `stable-v11.2`
2. `onsite-hub/src/app/api/task-bot/voice/session/route.ts` (token issuer)
3. `onsite-hub/src/app/api/task-bot/voice/tool-exec/route.ts` (callback from Modal)
4. `onsite-hub/src/lib/voice/provider_router.ts`
5. `onsite-hub/src/lib/voice/circuit_breaker.ts` (Redis sliding window)
6. `onsite-hub/public/pcm-processor.js` (copy verbatim from HireAI)
7. `onsite-hub/src/hooks/useVoiceChat.ts` (port from LearnOS)
8. `onsite-hub/src/components/task-bot/VoiceButton.tsx` (extend existing voice toggle)
9. Wall-clock 30-min cap (`setTimeout` on session close)
10. Per-user Redis voice-minute counter

**Acceptance gates:**
- ✅ Hindi voice "EPC PEB project mein Foundation Wall ka status batao" → bot speaks back project stats
- ✅ English voice "Make Plastering depend on Brickwork" → bot fires `create_task_dependency`, speaks confirmation
- ✅ Voice-mode RAG: "RA bill ka process kya hai" → bot speaks answer with audio source citation
- ✅ p95 mic-to-speech ≤700ms (instrument with `console.time` markers)
- ✅ Push-to-talk toggle works (server VAD off, manual commit)
- ✅ 30-min cap → graceful close + visual countdown last 5 min
- ✅ Per-user cap → 30 min/day Free → friendly close

**Critical inheritances** (per `memory/voice_calling_working_config.md` + HireAI gotchas):
- Dual event names `response.audio.delta` + `response.output_audio.delta`
- 48kHz→24kHz worklet resample
- Temperature ≥ 0.6
- AudioContext gated behind user click
- Mic-gate while AI speaks
- WS `max_size=10MB`

**Kill condition:** If Gemini 3.1 Flash Live preview API unavailable on Onsite's Google account → skip Gemini provider, ship OpenAI mini only (acceptable degraded mode). If Modal deploy can't reach pgvector RPC times <50ms, switch tool-exec callback to Vercel (round-trip).

**Cost ceiling:** First-week budget alert at $50 voice spend.

---

## Sprint 3 — Support Tier 1+2 (D11-D13, 2 days, overlaps with Sprint 2 tail)

**Owner:** Atlas (dispatched via `dispatch-sprint-5-support.md`)
**Goal:** Bot answers via RAG with confidence gate; on 👎 or low confidence, asks for urgency and creates a ticket.

**Files to ship** (per dispatch §11 Support matrix):
1. `Onsite/task-ai/database/007_support.sql` (incl. `CREATE RULE no_delete_audit`)
2. `onsite-hub/src/lib/support/auto_resolve_gate.ts` (hard whitelist on security/billing)
3. `onsite-hub/src/lib/support/duplicate_guard.ts` (sha256 fingerprint, 5-min TTL)
4. `onsite-hub/src/lib/audit/log_event.ts` (shared module per HLD §4)
5. `onsite-hub/src/app/api/task-bot/support/create-ticket/route.ts`
6. `create_support_ticket` tool added to `route.ts` registry
7. `onsite-hub/src/components/task-bot/TicketCard.tsx`
8. `onsite-hub/src/app/task-bot/admin/support/page.tsx` (ticket queue)
9. Confidence gate logic in `/api/task-bot/route.ts` (when to escalate)

**Acceptance gates:**
- ✅ Query "How do I reset my password" → confidence low + category=account_issue → bot routes to ticket creation (NEVER auto-resolves)
- ✅ Query "How do I create dependency" → confidence high → bot answers + 👎 → escalate to ticket
- ✅ Duplicate query within 5 min → suppressed, returns existing ticket_id
- ✅ Admin page shows tickets sorted by created_at DESC
- ✅ Audit log row written for every tier_1_resolved + ticket_created event

**Kill condition:** If audit RULE `DO INSTEAD NOTHING` blocks expected operations (e.g., admin trying to clean up tests), reverse to soft-delete column. Document tradeoff in `docs/decisions.md`.

---

## Sprint 4 — Support Tier 3 escalation (D13-D15, 2 days)

**Owner:** Atlas
**Goal:** Tickets past their SLA window auto-page Telegram (Critical/High), email ops (Normal), batch into daily digest (Low).

**Files to ship:**
1. `onsite-hub/src/lib/support/escalation.ts` (the 3-tier dispatch)
2. `onsite-hub/src/app/api/task-bot/support/escalate/route.ts` (cron handler)
3. `onsite-hub/vercel.json` — cron config: `[{ "path": "/api/task-bot/support/escalate", "schedule": "* * * * *" }]`
4. Telegram integration (reuse Onsite Telegram bot if exists; new bot if not)
5. Resend email integration (reuse existing onsite-hub config)

**Acceptance gates:**
- ✅ Critical ticket → Telegram pager + on-call group within 5 min
- ✅ Normal ticket → ops email within 1 hr
- ✅ Cron runs 60 ticks without duplicate escalations
- ✅ `escalated_at` set correctly (single fire per ticket)

**Kill condition:** If Vercel Cron 1-min granularity causes the Critical 5-min SLA to slip past 6 min consistently, switch to Modal scheduler (better timing precision).

---

## Sprint 5 — Notion sync (D14-D17, 3 days, overlaps with Sprint 4)

**Owner:** Atlas/Pixel pair
**Goal:** Pull Onsite's Notion KB into our store every 6 hours; admin can trigger immediately.

**Files to ship:**
1. `onsite-hub/src/app/api/task-bot/kb/notion-sync/route.ts`
2. Vercel Cron: `0 */6 * * *` → POST to sync route
3. Admin button "Sync Notion now" with last-sync timestamp display
4. Drift alert (admin badge if last sync >24 hr old)

**Acceptance gates:**
- ✅ Notion root page configured via env → all pages indexed
- ✅ Incremental: only pages with `last_edited_time > last_sync_at` get re-embedded
- ✅ Deleted Notion page → `knowledge_documents.status='deleted'` (don't drop chunks immediately; tombstone for 30 days)
- ✅ Sync >500 pages completes in <30 min on first run

**Kill condition:** If Notion API rate-limits us, switch to chunked sync (50 pages/run, 6 runs/day). If Onsite's Notion isn't reachable via API token within 48 hrs, ship sprint without it (manual upload still works).

---

## Sprint 6 — Training MVP M1+M2 (D17-D21, 4 days)

**Owner:** Pixel (dispatched separately; not in initial 3 dispatch files since this comes later)
**Goal:** User says "/train" or "I want to learn dependencies" → bot enters phase-machine flow, demos a real action in their sandbox project, quizzes them, marks complete.

**Files to ship:**
1. `onsite-hub/src/lib/training/state_machine.ts` (port HireAI L138-292)
2. `onsite-hub/src/lib/training/system_preamble.ts` (port HireAI L168-199)
3. `onsite-hub/src/lib/training/phase_prompts/m1_dependencies.ts` + `m2_progress.ts`
4. `onsite-hub/src/app/api/task-bot/training/start-module/route.ts`
5. `onsite-hub/src/app/api/task-bot/training/advance/route.ts`
6. `Onsite/task-ai/database/006_training.sql` (modules + progress + flashcards tables, modules table seeded with M1+M2)
7. `onsite-hub/src/components/task-bot/QuizCard.tsx`
8. Sandbox-project safety: tool args get `is_training=true` flag; backend writes to `training_sandbox` partition (need confirmation from Akshansh — fallback: append `[TRAINING]` to task name in real project)

**Acceptance gates:**
- ✅ "/train" enters WELCOME phase, asks user to pick module
- ✅ M1 INTRO → DEMO phase fires `create_task_dependency` in user's sandbox; verified in Onsite UI
- ✅ Echo-guard: AI talking to itself doesn't advance phase
- ✅ Quiz: 3 questions correct → RECAP → COMPLETE; `training_progress.completed_at` set
- ✅ Voice + text both work for the phase loop

**Kill condition:** If no sandbox-safe demo mechanism exists (Akshansh can't give us a way to mark "this is training data, don't pollute real project"), revert M1+M2 to RAG-explain mode like M3-M7. Document the gap.

---

## Sprint 7 — Training M3-M7 + SME review (D21-D25, 4 days)

**Owner:** Pixel
**Goal:** All 5 remaining modules ship in RAG-explain mode. Each module's DEMO phase shows a chunk + embedded screenshot of the relevant Onsite screen, walks user through what to click.

**Files to ship:**
1. `phase_prompts/m3_ra_bills.ts` through `m7_materials.ts`
2. `lib/training/rag_explain_renderer.ts` — pulls chunks scored by module category, includes screenshots from KB
3. Module rows in `training_modules` seeded with `demo_mode='rag_explain'`
4. SME review hook: each module has a `dhruv_approved_at` timestamp column; bot won't activate module to non-test users until set
5. Test users env list: `TRAINING_TEST_USER_IDS` allowlist

**Acceptance gates:**
- ✅ M3-M7 each run end-to-end against test user
- ✅ Each module's RAG-explain step returns at least 2 sources with screenshots
- ✅ Quiz still works for RAG-explain modules (questions derived from chunks)
- ✅ Dhruv + Akshansh review each of M3-M7 → flip `dhruv_approved_at` per module
- ✅ Median module completion time ≤9 min in test runs

**Kill condition:** If Akshansh review takes >1 week, ship M3-M7 to test users only and document deferred GA.

---

## Sprint 8 — SM-2 Spaced Repetition (D25-D27, 2 days)

**Owner:** Pixel
**Goal:** Auto-generated flashcards on module completion; daily review push on welcome screen.

**Files to ship:**
1. `onsite-hub/src/lib/training/sm2.ts` (port LearnOS `flashcards.py` verbatim)
2. `onsite-hub/src/lib/training/flashcard_generator.ts` (Claude generates 5-7 cards per module)
3. `onsite-hub/src/app/api/task-bot/training/review-flashcards/route.ts`
4. `onsite-hub/src/components/task-bot/FlashcardCard.tsx`
5. Welcome screen integration: "You have N cards due, 60 sec" prompt

**Acceptance gates:**
- ✅ Module COMPLETE → 5-7 flashcards inserted with `next_review_date = today+1`
- ✅ Review session: 4 cards × Good rating → ease_factor updates correctly, intervals 1→3→7→14 days
- ✅ Ease floor 1.3 enforced (clamp test)
- ✅ XP per quality awarded (0/2/5/10)
- ✅ Welcome screen badge appears when cards due

**Kill condition:** If LLM flashcard generation produces malformed JSON consistently, fall back to template-based cards (extract Q/A pairs from module phase_prompts).

---

## Sprint 9 — Cross-Add-On Hardening (D27-D29, 2 days)

**Owner:** QA agent + Shailendra
**Goal:** Production-ready stack — load tested, circuit-broken, mobile-clean, telemetry wired.

**Tasks:**
- Load test: 100 concurrent text queries, 20 concurrent voice sessions (Modal load test tooling)
- Tune Gemini circuit breaker thresholds (current: 5% over 5 min — verify on synthetic failures)
- Mobile review at 375px (iPhone SE) — all 4 new card types render correctly
- Wire Sentry alerts: RAG zero-hit spike, voice WS error rate >5%, ticket escalation latency >SLA
- Admin dashboard tabs (`knowledge`, `support`, `training`) — finalize 24h KPIs
- Audit pass: `security-auditor` agent reviews token-handling code paths

**Acceptance gates:**
- ✅ Load test 100 RPS RAG queries with p95 <1s
- ✅ Voice WS load 20 concurrent sessions stable for 10 min
- ✅ All 4 card types mobile-clean
- ✅ Sentry alerts firing correctly on synthetic failure injection
- ✅ Security auditor PASS on token-handling pass

**Kill condition:** If load test reveals pgvector index degradation past 500 docs, ship with HNSW tuning or migrate to Pinecone (out of scope; would slip Sprint 10).

---

## Sprint 10 — Pre-production Gate (D29-D30, 1 day)

**Owner:** Shailendra + Dhruv
**Goal:** Decide whether the stack ships to production. Refresh tester kit. Update Vercel deploy decision.

**Tasks:**
- End-to-end smoke: full demo flow with Sumit-style customer (Onsite admin user)
  - Customer signs in via real JWT
  - Asks RAG question → cited answer
  - Speaks tool action via voice → real Onsite write
  - Hits 👎 on a bad answer → ticket created → escalation works
  - Tries Training Module 1 → completes → gets first flashcards
- Refresh Cloudflare tunnel URL (rotates on terminal close)
- Rebuild Chrome extension v0.3.0 (no manifest change expected; bump version)
- Tester-kit ZIP refresh: `onsite-ai-helper-v0.3.0.zip`
- Update `RESUME-PROMPT.md` with the new state
- Decision point: Vercel production deploy? (Dhruv approves or defers per `feedback_no_auto_deploy`)

**Acceptance gates:**
- ✅ End-to-end smoke passes
- ✅ STATE.md updated to batch 30+
- ✅ Tester kit URLs current
- ✅ Dhruv signs off (or rolls back)

**Kill condition:** Any acceptance gate from Sprints 1-9 still failing → defer Vercel deploy; keep on tunnel.

---

## Critical-path dependencies

```
S0 (plan) ──► S1 (RAG) ──► S2 (Voice)
                │             │
                ▼             ▼
              S3 (Support)  S6 (Training M1+M2)
                │             │
                ▼             ▼
              S4 (Escalation) S7 (M3-M7)
                │             │
              S5 (Notion)   S8 (SM-2)
                │             │
                └────► S9 (Hardening) ──► S10 (Gate)
```

S1 blocks S2 (per D9), S3, S6 (RAG-explain depends on RAG).
S2 blocks S6 voice path (but text path works without S2).
S6 blocks S7 (state machine reused).
S3 blocks S4.

---

## Gates summary

| Gate | When | Pass criteria |
|---|---|---|
| G1 — Plan signed off | End of Sprint 0 | Dhruv approves DECISIONS-ADDON.md |
| G2 — RAG accepting queries | End of Sprint 1 | 5 docs indexed, search tool fires |
| G3 — Voice loop live | End of Sprint 2 | Bilingual demo completes in voice |
| G4 — Support deflection working | End of Sprint 4 | Tickets created + escalated on synthetic load |
| G5 — Notion synced | End of Sprint 5 | All Notion pages in our index |
| G6 — M1+M2 SME-approved | End of Sprint 6 | Akshansh/Sumit acks both modules |
| G7 — All 7 modules ready | End of Sprint 7 | All approved or test-user-gated |
| G8 — Daily review push live | End of Sprint 8 | 1st reviewer completes session |
| G9 — Load tests pass | End of Sprint 9 | All p95 budgets met |
| G10 — Production deploy decision | End of Sprint 10 | Dhruv approves or defers |

---

## Kill-switch decision tree

Any time during sprints 1-10:

1. **Akshansh API gate persists past D21** → flip M3-M7 + future training to permanent RAG-explain (D6 decision); ship M1+M2 only on the live demo side.
2. **Voice cost spike >$50/day in dev** → drop Gemini default, ship OpenAI mini only (cheaper baseline despite lower Hindi quality).
3. **RAG zero-hit rate >40% on production queries** → corpus gap; pause new sprints, run a corpus audit before resuming.
4. **Sumit/Akshansh reject the stack at any gate** → revert that add-on; don't try to "fix in production." Each add-on is independently kill-able.
5. **Token leak found in any new code path** → STOP. Audit. No new sprint until cleaned.

---

## Out-of-scope (this roadmap)

- PSTN voice (Twilio bridge) — separate sprint, scope when Sumit asks
- Customer-specific KB tenancy — Phase 4 only
- Vercel production deploy — separate decision per `feedback_no_auto_deploy`
- Stripe-style metered LLM billing — Phase 4
- Native mobile apps — never
- Voice cloning — Phase 4 only
- Cross-customer ticket aggregation — never (security boundary)

---

## What I'd do differently from the dispatch's plan (push-backs summary)

1. **Sequenced RAG → Voice instead of parallel** (D9). Saves Sprint 3 entirely.
2. **Flipped Support before Training** (Sprint 3-4 instead of after Training). Higher value, lower complexity.
3. **Cut auto-Notion-retirement** (D2). Customers retire when ready.
4. **Build own ticket queue immediately** (D3). Don't wait 48 hrs on Akshansh.
5. **Per-tenant voice minute cap from day 1** (D8). Cost discipline.
6. **Voice on separate Modal deploy** (D7). Vercel can't host long-lived WS.
7. **Ship all 7 training modules NOW** (D6). RAG-explain for M3-M7 is a 1-day variant, not a new product.

These changes are in this roadmap and reflected in the dispatch files.

---

## Status tracker (live)

Update at each sprint close:

| Sprint | Status | Commit | Notes |
|---|---|---|---|
| 0 | ⏳ in progress | — | Awaiting Dhruv sign-off on DECISIONS-ADDON |
| 1 | ⏸ pending | — | Awaiting paste-launch of dispatch-sprint-1-rag |
| 2 | ⏸ pending | — | |
| 3 | ⏸ pending | — | |
| 4 | ⏸ pending | — | |
| 5 | ⏸ pending | — | |
| 6 | ⏸ pending | — | |
| 7 | ⏸ pending | — | |
| 8 | ⏸ pending | — | |
| 9 | ⏸ pending | — | |
| 10 | ⏸ pending | — | |
