# Onsite Task AI — Master Context (v2)

> **Auto-loaded by Claude Code.** Everything needed to work on this product is here or linked. **Read this BEFORE writing any code.**
> **Last updated:** 2026-05-22 (V3 doc set landed)

---

## What This Is

A natural-language AI assistant embedded inside Onsite's construction-management SaaS. Users (workers → admins) run every Onsite operation by talking in text/voice/photo/video — in English, Hindi, or mix. Built on 2-tier LLM (Gemini Flash → Claude), hybrid multimodal RAG, 4-tier memory, vision document AI, voice realtime. Targets ₹12/user/mo at 99.5% accuracy. Scales to lakhs.

**One-line value prop:** *"Stop clicking through 7 menus. Just tell Onsite what you want."*

**Owner:** Dhruv Tomar | **PM:** Angelina | **Status:** V3 architecture locked May 22, 2026

---

## Read first — V3 doc set (canonical)

1. **[BRD-V3.md](./BRD-V3.md)** — business requirements (market, ROI, personas, KPIs, pricing, risks)
2. **[PRD-V3.md](./PRD-V3.md)** — product requirements (feature catalogue by phase, acceptance criteria)
3. **[ARCHITECTURE-V3.md](./ARCHITECTURE-V3.md)** — master architecture (decisions, components, cost math)
4. **[HLD-V3.md](./HLD-V3.md)** — high-level design (component contracts, data flows, scaling)
5. **[LLD-V3.md](./LLD-V3.md)** — low-level design (file structure, migrations 011-018, API contracts, 25 tools)
6. **[STATE.md](./STATE.md)** — what's live today
7. **[MEMORY.md](./MEMORY.md)** — gotchas already paid for in time (read before coding)
8. **[compact/](./compact/)** — session-boundary durability system. `PRE-COMPACT-PROMPT.md` (paste before `/compact`) + `POST-COMPACT-PROMPT.md` (paste after) + cumulative `SNAPSHOT-*.md` archive. Read latest snapshot first when resuming.

**Archived (V1 / addon docs):** `PRD.md`, `HLD.md`, `LLD.md`, `PRD-ADDON.md`, `HLD-ADDON.md`, `ROADMAP-ADDON.md` — superseded by V3. Sprint dispatches still valid: `dispatch-sprint-1-rag.md`, `dispatch-sprint-2-voice.md`, `dispatch-sprint-5-support.md`.

---

## Current state (May 22, 2026)

| Capability | Status |
|---|---|
| 14 production Onsite tools, hierarchical tree, stats card, Hindi-mix | ✅ Live (Phase 0) |
| PWA shell + service worker | ✅ Code complete, not deployed |
| WhatsApp Meta Cloud pipeline (linking + transcribe) | ✅ Code complete, not deployed |
| Supabase migrations 001-010 applied | ✅ to `xcvrdjhnvngfzczumquq` |
| Vercel deploy | ❌ Pending Dhruv `vercel login` |
| V3 architecture | ✅ Locked May 22 |
| Phases 1-12 | 📋 Planned per PRD-V3 |

---

## Locked decisions (V3 §0)

1. ✅ Stay Next.js until 50K DAU → migrate to FastAPI/Modal later
2. ✅ **Skip Ollama self-host** — public LLM APIs only for now (2-tier router)
3. ✅ Knowledge graph AFTER memory + RAG ship (Phase 12)
4. ✅ Labeling UI = best, not minimal (admin route + RAGAS + JSONL)
5. ✅ Direct LLM keys + OpenRouter fallback
6. ✅ Razorpay (not Stripe) — only after real use case proven

---

## Tech stack — final

| Layer | Choice |
|---|---|
| Edge | Vercel + Next.js 15 + PWA |
| Agent runtime | Next.js API routes → Modal at 50K DAU |
| Database | Supabase Postgres + pgvector + tsvector + RLS |
| LLM Tier A (70%) | Gemini 2.0 Flash direct |
| LLM Tier B (30%) | Claude Haiku 4.5 / Sonnet 4.5 direct + OpenRouter fallback |
| Embeddings | **`gemini-embedding-2`** (GA April 2026, multimodal: text/image/audio/video/PDF) at 1536-dim Matryoshka |
| Voice realtime (browser) | **Gemini 3.1 Flash native audio** (cheaper, native multimodal) |
| Voice realtime (phone/Twilio) | OpenAI `gpt-4o-mini-realtime-preview` (QH stable-v11.2 locked) |
| Voice STT async | Groq Whisper |
| TTS | ElevenLabs Rachel + Edge TTS fallback |
| Cache + rate limits | Upstash Redis (serverless) |
| Vision document AI | 2-pass Gemini 3.1 Flash → Pro on validator failures |
| Background jobs | Vercel Cron (now) + Modal (scale) |
| Observability | Sentry (errors) + Langfuse (LLM traces) + Posthog (analytics) |
| Mobile | Capacitor 6 wrap of PWA (Phase 9) |
| Auth (customers) | Onsite-issued JWT |
| Auth (admin) | Supabase magic-link |
| Payments | Razorpay (Phase 11) |
| Weather API | OpenWeatherMap (free tier) |

---

## Where code lives

```
onsite-hub/                     CODE — github.com/aiagentwithdhruv/onsite-hub (PRIVATE)
  src/app/task-bot/             UI: page.tsx (chat) + layout.tsx (PWA shell)
  src/app/api/task-bot/         All API routes
  src/lib/agent/                LangGraph + router + tools + connectors
  src/lib/memory/               4-tier memory
  src/lib/rag/                  Multimodal RAG (Modal microservice)
  src/lib/vision/               Document AI (2-pass + schemas + validators)
  src/lib/voice/                Realtime proxies (Gemini + OpenAI)
  src/lib/alerts/               10 rules + delivery + dedup
  src/lib/domain/               Weather + geo + critical-path + vendor scoring
  src/lib/whatsapp/             Meta Cloud API + linking
  src/lib/push/                 Web push pipeline
  src/lib/obs/                  Sentry + Langfuse + Posthog
  modal/                        Python microservice (RAG ingest + Doc AI)

Onsite/task-ai/                 DOCS — github.com/aiagentwithdhruv/Onsite (PRIVATE)
  V3 doc set above + database/ migrations + runbooks/
```

## ⚠️ Repo split — commit to right one

| Type of change | Repo |
|---|---|
| Page UI / API routes / lib code | **onsite-hub** |
| Migrations / docs / runbooks | **Onsite/task-ai/** |

Both PRIVATE. Verify before push: `gh repo view aiagentwithdhruv/<repo> --json visibility`.

Code + doc changes that go together = TWO commits with cross-reference in messages.

---

## Working rules (hard-learned)

1. **Read MEMORY.md before any change.** Gotchas paid for in time live there.
2. **Type everything (TS strict). No `any`.** Tool args go through JSON.parse — wrap in try/catch + validate.
3. **Token NEVER touches LLM payload.** Audit every code path. JWT never in `messages` array.
4. **No state in MVP customer chats.** Memory layer is separate; chat per-request is stateless re: Onsite API.
5. **Test against testapi.onsiteteams.in first.** Then prod. There's an env switch.
6. **Don't break AppShell.tsx PIN bypass:** `if (pathname.startsWith('/task-bot')) return <>{children}</>` is load-bearing.
7. **Match brand:** `#0f0a2e` bg, `#c73e5a` accent. Plus Jakarta Sans. Dark theme. Mobile-first.
8. **Voice config locked:** Don't touch QH `stable-v11.2-voice-live` event names. Defensive listen for both old + new.
9. **Embedding model locked:** `gemini-embedding-2` (NOT `gemini-embedding-001`). 1536-dim Matryoshka.
10. **Propose → confirm → execute** for all mutating actions. Never auto-fire.
11. **PII strip before LLM:** phones, GSTIN, PAN, Aadhar via regex (medassist pattern).
12. **Audit every external call** with Langfuse `@observe`.

---

## Onsite data model

```
Company → Projects → Workorders → BAs (tree: parent / leaf) → Sub-activities → Progress
```

- Dependencies link **two leaf BAs** in **same workorder**
- Progress logs against a **sub-activity**, not a BA
- `location_id` field is essentially unused in practice; sub-activity name plays the role

---

## API surface — Onsite v3 endpoints (no Akshansh needed)

```
GET  /apis/v3/list/{company,project,billingactivity,billingsubactivity,taskdependency}
GET  /apis/v3/detail/project/progressorder/<id>
GET  /apis/v3/detail/billingactivity/<id>
POST /apis/v3/add/{taskdependency,billingprogresshistory}
PATCH /apis/v3/edit/taskdependency
DELETE /apis/v3/delete/{taskdependency,billingprogresshistory}/<id>
```

**Multi-workorder:** try `/list/progressorder?project_id=` and `/list/workorder?project_id=` first; fall back to single `/detail/progressorder/<id>`.

---

## Internal endpoints — full surface (LLD-V3 §3)

Main: `/api/task-bot` · Sessions: `/api/task-bot/sessions` · Memory: `/api/task-bot/memory/{save,recall}` · RAG: `/api/task-bot/rag/{ingest,query}` · Vision: `/api/task-bot/vision/{analyze-document,analyze-image}` · Voice: `/api/task-bot/voice/{transcribe,realtime}` · Docs: `/api/task-bot/docs/{upload,[id]}` · Alerts: `/api/task-bot/alerts/{config,log}` · Webhooks: `/api/task-bot/webhooks/{config,deliver}` · Reports: `/api/task-bot/reports/schedule` · WhatsApp: `/api/task-bot/whatsapp/{webhook,start-link,test-send}` · Admin: `/api/task-bot/{admin-stats,my-stats,export-training-data,feedback,chat-log}` · Push: `/api/task-bot/push/{register,send}`

---

## Run / test locally

```bash
cd "Onsite/onsite-hub"
npm install   # first time
npm run dev -- --port 3001
# Open http://localhost:3001/task-bot
```

JWT for testing: `copy(JSON.parse(localStorage.getItem('token')).token)` in `web.onsiteteams.com` console.

Supabase migration: from `Onsite/task-ai/` directory:
```bash
source ~/.aiwithdhruv-secrets
export SUPABASE_ACCESS_TOKEN=$SUPABASE_ACCESS_TOKEN_TASK_AI
supabase db push --password 'Dhruvtomar7008@'
```

---

## When you get stuck

| Symptom | Cause | Fix |
|---|---|---|
| 401 "token signature invalid" | JWT typo (l vs 1 vs I) | Re-copy from console |
| 400 "only leaf node can be dependency" | BA has children | Pick different tasks |
| 400 "same workorder" | Cross-workorder dep | Same workorder pick |
| Progress not appearing | Wrong sub-activity ID | Check task's sub-activities |
| Bot chats but no tool fires | Claude wants more info | Be explicit in user msg |
| Voice silent / drops audio | OpenAI event name regression | See `voice_calling_working_config` memory |
| RAG returns empty | Embedding model mismatch | Check `gemini-embedding-2`, NOT 001 |
| Doc extract wrong amounts | Pass 2 didn't fire | Check field validators triggered |
| Cost spike | Cache miss / tier-A skipped | Inspect Langfuse traces |

---

## Reference repos (all cloned + private-mirrored)

| Repo | What we lift | Local path |
|---|---|---|
| Smart AI Data Agent (MSBC) | Spine: connector ABC, LangGraph, 3-tier memory, hybrid RAG, cache pattern | `/tmp/smart-ai-data-agent/` (clone fresh) |
| KnowledgeForge | RAG report, Tavily fallback, doc ingestion, SSE streaming | `euron-references/knowledgeforge/` |
| Hireai | Phase state machine, WS realtime proxy, langfuse @observe | `euron-references/hireai/` |
| Multimodal-RAG-System (Dhruv's own) | **PRIMARY RAG lift** — Gemini Embedding 2 multimodal pipeline | `Euron/AI Architech Mastery/Multimodal-RAG-System/` |
| Angelina app | 22-tool action surface, memory tiers, vps_execute (Python runner pattern) | `angelina-vercel-clean/` |
| QuotaHit voice-server | Voice realtime locked config | `QuotaHit/voice-server/` |
| IndianWhisper | Async transcription patterns | `Million-Dollar-Voice/AiwithDhruv_Voice/` |
| Medassist | PII de-identification pattern | `euron-references/medassist/` |

---

## Self-update rules

When you change something material, also update:

| Change | Update |
|---|---|
| New tool | LLD-V3 §4, ARCHITECTURE-V3 §17 tool table, STATE.md |
| New migration | LLD-V3 §2, apply via `supabase db push`, STATE.md |
| Architectural decision | ARCHITECTURE-V3 §0, write ADR in `docs/decisions.md` |
| Production deploy | STATE.md "Deployed to Vercel" row |
| Bug fixed | BUG-TRACKER.md, MEMORY.md if non-obvious |
| Phase shipped | STATE.md + ROADMAP-ADDON.md mark phase done |

**Never write code without updating at least STATE.md.**
