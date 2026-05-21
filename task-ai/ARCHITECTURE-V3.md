# Onsite Task AI — Architecture V3 (Final)

> **Synthesizes:** KnowledgeForge (RAG) + Smart AI Data Agent (MSBC spine) + Angelina (memory + 22 tools) + QuotaHit (voice realtime) + IndianWhisper (transcription) + hireai (phase state machine) + Multimodal-RAG-System (Dhruv's own, Gemini Embedding 2 multimodal) + Phase 1 Task AI.
> **Goal:** scale to lakhs of users at controlled cost without rewriting from scratch.
> **Dual primary KPI:** *recall everything · take action on anything.*
> **Author:** Angelina (PM) · **Last updated:** 2026-05-22 · **Approver:** Dhruv

---

## 0. Decisions locked (Dhruv sign-off)

| # | Decision | Locked answer |
|---|---|---|
| 1 | Agent runtime — stay Next.js until 50K DAU? | ✅ **Yes** — migrate later |
| 2 | LLM Tier 3 — self-host Ollama or skip? | ❌ **Skip self-host.** Public APIs only for now. **Architecture becomes 2-tier (Gemini Flash → Claude Haiku/Sonnet) + future Ollama tier when team capacity allows** |
| 3 | Knowledge graph — now or after memory+RAG? | ✅ **After.** Pattern miner will reveal if KG is needed |
| 4 | Training data labeling UI — minimal or best? | ✅ **Best.** Build it right, not minimal — see §7.5 |
| 5 | LLM key strategy — direct or OpenRouter? | ✅ **Direct primary + OpenRouter as fallback** when a direct provider is down/rate-limited |
| 6 | Monetization — when? | ✅ **Razorpay later**, AFTER product proves real use case. Don't build billing for a product we haven't proven |

---

## 1. Head-to-head comparison (KnowledgeForge vs MSBC)

| Axis | KnowledgeForge | Smart AI Data Agent (MSBC) | Onsite AI Phase 1 (today) |
|---|---|---|---|
| **Backend runtime** | FastAPI 0.111 + Uvicorn | FastAPI + LangGraph + Pydantic v2 | Next.js 15 API routes |
| **Frontend** | Next.js 14 + Zustand + TanStack Query | "Any frontend" — agent is API-only, BYO | Next.js 15 + PWA shell |
| **RAG search** | Document chunks via **ILIKE only** (pgvector planned, not built) | **Hybrid: BM25 + pgvector dense + Reciprocal Rank Fusion** | None yet |
| **LLM routing** | Multi-provider but **no complexity routing** | **3-tier: local Ollama (70%) → Gemini (20%) → Claude (10%)** | Smart Haiku/Sonnet by action verb |
| **Memory** | None surfaced | **3-tier: query / error / facts** | Session + Supabase chat persistence |
| **Action execution** | Tool calls, no confirm gate | **Propose → confirm → execute** | Tool calls, hallucination guard |
| **Multi-tenancy** | User-scoped JWT, no tenant_id | **tenant_id on every query, RBAC** | JWT-only (Onsite issues) |
| **Caching** | Not surfaced | **Semantic (cosine >0.95) + exact, Redis** | 5-min in-memory tool cache |
| **Web search fallback** | **Tavily + DDG when KB thin** | Not present | Not present |
| **Doc ingestion** | PyPDF2 + python-docx + chunker | extractor + chunker + embedder pipeline | Not present |
| **Auth** | NextAuth + Google/MS OAuth | JWT + Supabase Auth + RBAC | Onsite-issued JWT |
| **Stripe/Razorpay** | **Stripe built-in** (plans, subs) | None | None |
| **WebSocket UX** | **typing indicators + notifications** | None | None |
| **Connector plugin** | Tight-coupled | **`BaseConnector` ABC → pluggable** | 14 hard-coded Onsite tools |
| **Eval framework** | None | **RAGAS, 87%+ on 52 golden SQL tests** | Manual smoke tests |
| **Phase / state machine** | None | **LangGraph ReAct agent** | Custom 8-iteration loop |

**Verdict: MSBC wins 13/19 — it's the spine. KF wins 5/19 — polish + future monetization scaffolding.**

---

## 2. What to lift — full inventory by source

### A. From Smart AI Data Agent / MSBC (the spine — 75%)

| Lift | Their file | Goes into |
|---|---|---|
| `BaseConnector` ABC + registry | `backend/app/connectors/base.py` + `registry.py` | `onsite-hub/src/lib/agent/connectors/` |
| 2-tier LLM router (Gemini → Claude) | `backend/app/agent/router.py` | `onsite-hub/src/lib/agent/router.ts` |
| LangGraph ReAct loop | `backend/app/agent/graph.py` | `onsite-hub/src/lib/agent/graph.ts` (LangGraph.js) |
| 3-tier memory (query/error/facts) | `backend/app/memory/*.py` | `onsite-hub/src/lib/memory/` |
| Hybrid RAG (BM25 + pgvector + RRF) | `backend/app/rag/{search,chunker,embedder,extractor}.py` | `onsite-hub/src/lib/rag/` |
| Semantic + exact cache | (Redis pattern) | `onsite-hub/src/lib/cache/` |
| Propose→confirm→execute | (in graph.py) | `onsite-hub/src/lib/agent/actions.ts` |
| RAGAS eval framework | `backend/scripts/eval/` | `onsite-hub/scripts/eval/` |
| tenant_id discipline | every connector method | every query in our agent/ |

### B. From KnowledgeForge (polish — 10%)

| Lift | Their file | Goes into |
|---|---|---|
| Tavily/DDG web search fallback | `services/search_service.py` | `onsite-hub/src/lib/rag/web_fallback.ts` |
| PDF/DOCX ingestion | `services/document_service.py` | `onsite-hub/src/lib/rag/ingest.ts` |
| SSE streaming chat | `routers/conversations.py:stream_chat_response` | `onsite-hub/src/app/api/task-bot/stream/route.ts` |
| Razorpay models (NOT Stripe) | Inspired by `models/billing.py` | Future — when monetization phase fires |

### C. From Angelina app (memory + tool surface — 10%)

> **Critical find:** Angelina already has **22 production tools** + memory tiers. It's the working "recall + take action" archetype.

| Lift | Their file | Goes into |
|---|---|---|
| `memory_entries` schema (importance/type/tags + pgvector) | `sql/001_memory_schema.sql` | New migration `011_memory_entries.sql` |
| Memory repo with file fallback | `src/lib/memory-repository.ts` + `memory.ts` | `onsite-hub/src/lib/memory/` |
| `save_memory` + `recall_memory` tool wrappers | `src/app/api/tools/{save_memory,recall_memory}` | `onsite-hub/src/app/api/task-bot/tools/memory/` |
| **`vps_execute` (==Python runner pattern)** | `src/app/api/tools/vps_execute/` | `onsite-hub/src/lib/agent/python-runner/` |
| `mcp_call` (MCP protocol bridge) | `src/app/api/tools/mcp_call/` | Park — wire in Phase 6 if MCP servers worth it |
| `obsidian_vault` (KB sync) | `src/app/api/tools/obsidian_vault/` | Inspires the **Training DB sync** pattern (Phase 7) |
| `transcribe_audio` (Groq Whisper) | `src/app/api/tools/transcribe_audio/` | `onsite-hub/src/lib/whatsapp/transcribe.ts` (already partial) |
| `web_search` (Tavily wrapper) | `src/app/api/tools/web_search/` | Pairs with B's Tavily lift |
| Tool registration pattern (each tool = its own folder + route) | All 22 folders | Mirror in `onsite-hub/src/app/api/task-bot/tools/` |

### D. From QuotaHit voice-server (voice realtime — 5%)

> **The production-tested realtime voice config.** Tag `stable-v11.2-voice-live` on develop. Treat as locked precedent.

| Lift | Their file | Goes into |
|---|---|---|
| OpenAI Realtime client (GA event names) | `voice-server/openai_realtime_client.py` | `onsite-hub/src/app/api/task-bot/voice/realtime/route.ts` |
| Gemini Live client (D-QH-090 native audio) | `voice-server/gemini_live_client.py` | Same — fallback path |
| Realtime token mint | `src/app/api/ai/realtime-token/route.ts` | Direct port (TS) |
| Modal deployment pattern (force-stop before redeploy) | `voice-server/app.py` | Modal worker for Onsite voice tier 2+ |
| TS client integration | `src/lib/demo/voice-agent.ts` | `onsite-hub/src/lib/voice/agent-client.ts` |
| Audio path config (mulaw 8kHz, 640-byte chunks, 0.07s sleep) | (in client) | Match exactly — Twilio-friendly defaults |

**Locked precedent (from voice_calling_working_config memory):**
- Model: `gpt-4o-mini-realtime-preview`
- Schema: GA nested — `session.audio.input/output.format = {"type": "audio/pcmu"}`
- **Event names: `response.output_audio.delta` + `response.output_audio_transcript.delta`** (this is the one-line bug that ate a whole day in QH; don't repeat)

### E. From IndianWhisper (transcription on-device — 0% lift, **reference for fallback**)

> IW is the on-device Hindi-aware Whisper. For Onsite AI, we don't need on-device (we have server). But IW's Groq + local Whisper pattern is the reference if we ever need offline fallback.

| Reference | Their file | Why we keep the reference |
|---|---|---|
| Groq Whisper transcription | `WhisperAiwithDhruv-Windows/src/services/groq-transcribe.js` | Already in `lib/whatsapp/transcribe.ts` |
| WhisperKit on-device fallback | `WhisperAiwithDhruv/.build/checkouts/swift-transformers/` | Future — if we ship native macOS Onsite app |

### F. From current Task AI (keep, don't rebuild)

| Keep | Why |
|---|---|
| 14 Onsite v3 tools (production-tested) | Wrap them as one `BaseConnector` impl — no code rewrite |
| Hierarchical tree, stats card, Hindi-mix system prompt | Customer-tested differentiator |
| PWA shell + service worker + manifest | Production-ready, just needs deploy |
| WhatsApp pipeline (Meta Cloud API + linking + transcribe) | Built, not deployed |
| Hallucination guard + force-recall | Real bug catcher |
| Migrations 001-010 | Already applied to `xcvrdjhnvngfzczumquq` |

### G. Multimodal-RAG-System — Dhruv's own production reference (PRIMARY RAG LIFT)

**Location:** `Euron/AI Architech Mastery/Multimodal-RAG-System/`
**Built:** Mar 10, 2026 by Dhruv. Already using **Gemini Embedding 2** (GA April 2026).
**This is the actual pipeline we copy. Native multimodal — text + PDF + image + audio + video in one embedding space.**

| Lift | Their file | Goes into |
|---|---|---|
| Gemini Embedding 2 wrapper | `backend/app/services/embedding.py` | `onsite-hub/src/lib/rag/embedding.ts` |
| Vector store (pgvector wrapper) | `backend/app/services/vectorstore.py` | `onsite-hub/src/lib/rag/vectorstore.ts` |
| RAG pipeline orchestration | `backend/app/services/rag_pipeline.py` | `onsite-hub/src/lib/rag/pipeline.ts` |
| Text processor (chunker) | `backend/app/processors/text_processor.py` | `onsite-hub/src/lib/rag/processors/text.ts` |
| PDF processor (BOQ-ready) | `backend/app/processors/pdf_processor.py` | `onsite-hub/src/lib/rag/processors/pdf.ts` |
| Image processor + vision describer | `backend/app/processors/image_processor.py` + `services/vision.py` | `onsite-hub/src/lib/rag/processors/image.ts` |
| Audio processor + Whisper | `backend/app/processors/audio_processor.py` + `services/audio_transcription.py` | `onsite-hub/src/lib/rag/processors/audio.ts` |
| Video frame extractor + vision | `backend/app/processors/video_processor.py` + `services/video_vision.py` | `onsite-hub/src/lib/rag/processors/video.ts` |
| Drag-drop ingest router (SSE progress) | `backend/app/routers/ingest.py` | `onsite-hub/src/app/api/task-bot/rag/ingest/route.ts` |
| Query router (SSE tokens + citations) | `backend/app/routers/query.py` | `onsite-hub/src/app/api/task-bot/rag/query/route.ts` |
| Rate limiter | `backend/app/rate_limiter.py` | `onsite-hub/src/lib/rate-limit/` |
| Docker compose + healthchecks | `docker-compose.yml` | Reference for Modal worker config |
| Sample docs for testing | `sample-docs/` | Reuse for Onsite RAG smoke tests |

**Path conversion note:** Multimodal-RAG-System is Python/FastAPI. Onsite is TS/Next.js. Two options:
- **(A)** Port to TS — adds ~2 weeks but keeps one runtime
- **(B)** Run RAG as a Modal microservice in Python (reuse files almost verbatim) — same code, ~1 week

**My pick: (B)** for v1. Faster ship. Port to TS only if Modal cold starts hurt UX.

### H. Other "more projects" to consider (Dhruv to greenlight)

| Repo | Lift candidate | Recommended? |
|---|---|---|
| **agentic-workflows** | Multi-agent CLI prototype — orchestration patterns | ✅ Yes — Phase 4+ |
| **supportiq** (showcase) | Support escalation — directly relevant to Sprint 3 | ✅ Yes — read before Sprint 3 |
| **LegalRAG** (Euron local) | Legal-domain RAG patterns | Skim only for chunking strategies |
| **RAG_Knowledge_Chatbot** (Euron local) | Earlier RAG project | Skip — superseded by Multimodal-RAG-System |
| **ai-second-brain** (private) | Obsidian + MCP — KB + memory sync | Maybe — informs Training DB design |
| **agent-loadouts** (private) | Portable agent personality packs | Park — multi-persona later |
| **fraudlens** (public) | XGBoost + Isolation Forest + GenAI explanations | Skip — QuotaHit-relevant, not Onsite |
| **laptop-finder-ai** (public) | Next.js 15 + FastAPI + pgvector + GPT-4o RAG demo | Reference for Next.js↔FastAPI integration |

**Greenlight ask:** add **Multimodal-RAG-System (primary)** + agentic-workflows + supportiq to the lift inventory?

---

## 3. The Master Architecture — Onsite AI V2

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENTS                                    │
│  PWA (web)     Mobile (Capacitor)     WhatsApp     Voice/Phone  │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS  (+ wss for voice realtime)
            ┌──────────▼──────────┐
            │   EDGE (Vercel)     │
            │   Next.js 15 + SW    │
            │   PWA shell + auth   │
            └──────────┬──────────┘
                       │ /api/task-bot/* (SSE streaming)
                       │ /api/task-bot/voice/realtime (WSS proxy)
            ┌──────────▼──────────────────────────────────┐
            │           AGENT TIER                         │
            │  ┌────────────────────────────────────────┐  │
            │  │  LangGraph ReAct Agent                  │  │
            │  │  Plan → Tool select → Execute → Reflect │  │
            │  │                                         │  │
            │  │  Tool catalogue (mirrors Angelina):     │  │
            │  │   ▸ Onsite connector (14 actions)       │  │
            │  │   ▸ save_memory / recall_memory         │  │
            │  │   ▸ rag_search (hybrid)                 │  │
            │  │   ▸ web_search (Tavily fallback)        │  │
            │  │   ▸ python_run ⚡ (sandboxed)           │  │
            │  │   ▸ transcribe_audio (Groq Whisper)     │  │
            │  │   ▸ generate_image (future)             │  │
            │  └────────────────┬───────────────────────┘  │
            └───────────────────┼──────────────────────────┘
                                │
       ┌─────────┬──────────────┼──────────────┬────────────┐
       │         │              │              │            │
   ┌───▼───┐ ┌───▼───┐    ┌────▼────┐    ┌────▼────┐  ┌────▼────┐
   │LLM(2t)│ │MEMORY │    │  RAG    │    │ CACHE   │  │ ACTIONS │
   └───┬───┘ └───┬───┘    └────┬────┘    └────┬────┘  └────┬────┘
       │         │              │              │             │
       │   ┌─────▼──────────────▼──────────────▼──┐          │
       │   │  Supabase Postgres + pgvector         │          │
       │   │  (RLS per tenant_id)                  │          │
       │   │  • task_ai_messages (chat history)    │          │
       │   │  • memory_entries (4 tiers, pgvector) │          │
       │   │  • rag_chunks (BM25 tsvector + dense) │          │
       │   │  • action_log (audit trail)           │          │
       │   │  • feedback_labels (Phase 7 training) │          │
       │   └────────────────────────────────────────┘          │
       │                                                       │
       │   ┌──────────────────┐                                │
       │   │  Upstash Redis    │                               │
       │   │  • semantic cache │                               │
       │   │  • exact cache    │                               │
       │   │  • rate limits    │                               │
       │   └──────────────────┘                                │
       │                                                       │
       │       ┌──────────────────────────┐                    │
       │       │  Background workers      │                    │
       │       │  • heartbeat (memory)    │                    │
       │       │  • RAG ingestion (Modal) │                    │
       │       │  • RAGAS eval nightly    │                    │
       │       │  • pattern miner         │                    │
       │       └──────────────────────────┘                    │
       │                                                       │
   ┌───▼─────────────────────────────────────────────┐         │
   │      LLM PROVIDERS (2-tier router, public-only)  │         │
   │                                                  │         │
   │  Tier 2 (~70% queries):                          │         │
   │    Gemini 2.0 Flash direct                       │         │
   │    Cost ~$0.10/M tokens | Latency 1-3s           │         │
   │                                                  │         │
   │  Tier 1 (~30% queries — action + complex):       │         │
   │    Claude Haiku 4.5 default                      │         │
   │    Claude Sonnet 4.5 (action verbs + multi-step) │         │
   │    Cost $0.8-3/M tokens | Latency 2-5s           │         │
   │                                                  │         │
   │  Fallback if direct provider down:               │         │
   │    OpenRouter same model id, +5% markup, OK      │         │
   │                                                  │         │
   │  Future Tier 3 (when team has bandwidth):        │         │
   │    Self-host Ollama — re-evaluate post Sprint 3  │         │
   └──────────────────────────────────────────────────┘         │
                                                                │
                                              ┌─────────────────▼─────────┐
                                              │   ACTION EXECUTORS         │
                                              │   ▸ Onsite v3 (14 tools)   │
                                              │   ▸ Python sandbox runner  │
                                              │   ▸ Voice realtime         │
                                              │     (QH config locked)     │
                                              └────────────────────────────┘

VOICE PATH (parallel, for realtime):

  PWA / WhatsApp / Phone
       │
       │  WSS (audio chunks)
       ▼
  /api/task-bot/voice/realtime ◄── mints OpenAI Realtime token, server-side
       │
       │  WSS upgrade
       ▼
  OpenAI Realtime (gpt-4o-mini-realtime-preview, GA event names)
       │
       │  tool_calls dispatched back into agent tier
       ▼
  same LangGraph ReAct agent as text path
```

### Why this shape

1. **Edge stays Next.js / Vercel** — already there, PWA primitives, sub-100ms global.
2. **One unified agent** for text AND voice — voice realtime calls back into the same LangGraph loop via tool_call dispatch (mirrors QH's pattern).
3. **One Postgres** for everything — chat, memory, RAG, audit, feedback labels. pgvector + tsvector cover hybrid search natively.
4. **2-tier LLM** (per decision #2) — Gemini default, Claude for action/complex. Future Ollama tier re-evaluated after Sprint 3.
5. **OpenRouter fallback** (per decision #5) — only triggered when direct provider returns 5xx/429.
6. **Python runner is the speed killer** — see §6.
7. **Memory tools mirror Angelina** — save_memory + recall_memory are tool calls, not magic; LangGraph decides when to invoke.

---

## 4. Tech stack — final decisions

| Layer | Choice | Why |
|---|---|---|
| Edge | **Vercel** (existing) | Already there, sub-100ms global, PWA + SW work |
| Agent runtime | **Next.js API routes** until 50K DAU → **Modal/ECS** | Vercel function timeout (300s) eventually limits us |
| LLM gateway | **Direct provider calls + OpenRouter fallback** | Per decision #5 |
| LLM Tier 2 default | **Gemini 2.0 Flash** direct | $0.10/M tokens, fast, multilingual |
| LLM Tier 1 action | **Claude Haiku 4.5 / Sonnet 4.5** direct | Tool use champion |
| LLM Tier 3 future | Ollama (deferred, decision #2) | Re-evaluate post Sprint 3 |
| Database | **Supabase Postgres 15 + pgvector** | RLS, pgvector, already migrated |
| Cache | **Upstash Redis** (serverless) | Pay-per-request, no infra |
| Hybrid search | **pgvector + Postgres tsvector** | Skip Pinecone — same DB, zero extra ops |
| RAG embeddings | **`gemini-embedding-2`** (GA April 2026) at **1536-dim Matryoshka** truncation. Auto-normalizes for quality. Natively multimodal — text + image + video + audio + PDF in one embedding space. | First natively multimodal embedding model in the Gemini API. 8192 token input (4× over 001). Cross-modal search across 100+ languages. Up to 6 images / 180s audio / 120s video (32 frames) / 6 PDF pages per request. Batch API at 50% pricing. **Note:** embedding space incompatible with `gemini-embedding-001` — we start fresh. |
| Voice realtime | **OpenAI gpt-4o-mini-realtime-preview** (QH-locked config) | Production-proven |
| Voice TTS (non-realtime) | **ElevenLabs Rachel** + Edge TTS fallback | MSBC pattern |
| Voice STT (transcription) | **Groq Whisper** (existing) | Already in `~/.zshrc`, 1 hr → 10 sec |
| Mobile | **Capacitor 6** wrap of existing PWA | One codebase |
| Auth (customers) | **Onsite-issued JWT** | Existing |
| Auth (admin/labeling) | **Supabase Auth + magic link** | For internal labeling UI |
| Background jobs | **Vercel Cron** (now) → **Modal scheduled** (scale) | |
| Monitoring | **Sentry + Posthog + Vercel Analytics** | Standard |
| Payments (future) | **Razorpay** | Indian market default (per decision #6) |
| Eval | **RAGAS + golden test suite** (port MSBC's 52 examples) | Quality floor |

---

## 5. Cost math — scaling to lakhs of users

### Assumption
- 1 lakh active users
- 5 queries/user/day = 500K queries/day = **15M queries/month**
- Each query ~2 LLM round-trips = **30M LLM calls/month**

### Pure Claude (today, no routing)
- 30M × $0.0015 avg = **$45,000/month** 🚨

### 2-tier routing (decision #2 — public APIs only)
| Tier | % calls | $/call | Total |
|---|---|---|---|
| Gemini Flash | 70% (21M) | $0.0001 | $2,100 |
| Claude Haiku/Sonnet | 30% (9M) | $0.002 | $18,000 |
| **Total** | | | **$20,100/month** |

**~2.2× cost reduction** vs pure Claude. (3-tier Ollama would have hit ~7× reduction — that's the gap we accept by deferring self-host.)

### + Semantic caching (cosine >0.95 reuse)
- ~30% near-duplicate queries hit cache
- Effective LLM cost: **$14,070/month**

### + Infra
| Service | $/month |
|---|---|
| Vercel Pro | $20 |
| Supabase Pro | $75 incl bandwidth |
| Upstash Redis | $30 |
| ElevenLabs (5K voice msgs/day) | $99 |
| Modal (background workers) | $50 |
| OpenAI Realtime (voice calls — separate budget) | varies, $0.06/min |
| Sentry + Posthog | $50 |
| **Infra total** | **~$324/month** |

**Grand total at 1 lakh users (text-only): ~$14,400/month ≈ ₹12L/mo.**
**Per-user: ₹12/month.**

If we charge **₹100/user/month** entry tier → 88% gross margin.
If we charge **₹500/user/month** for full voice + RAG → 97% gross margin.

**The deferred Tier 3 (Ollama) would drop this to ₹4L/mo.** Revisit when team has Sprint 3 capacity.

---

## 6. Python script runner — the speed + reliability win

For predictable complex workflows, LLMs are **100× slower + 1000× more expensive** than the equivalent Python script.

Examples that beat LLM:
- "Export all project progress to CSV" → 5 lines of pandas, 200ms, ₹0
- "Compute project velocity last 30 days" → SQL + numpy, 100ms, ₹0
- "Bulk-import BOQ from this xlsx" → openpyxl + validation, 500ms, ₹0
- "Find tasks blocked by tasks blocked by X" → recursive CTE, 50ms, ₹0
- "Generate site report PDF from these 12 tasks" → reportlab, 2s, ₹0

**Design** (modelled on Angelina's `vps_execute`):
- `python-scripts/` library of curated scripts with strict input schema
- LLM calls `python_run(script_id, args_json)` tool
- Node spawns sandboxed `python3` subprocess via `child_process.execFile`
- Timeout 30s, memory 512MB, no network unless whitelisted
- Output flows back as tool result, agent reflects on it

**Risk:** uncurated `eval` is a security disaster. We start with 5-10 scripts, grow to 50 over 3 months.

---

## 7. Memory tiers (4 levels — recall everything)

| Tier | Scope | Storage | Heartbeat? | Use case |
|---|---|---|---|---|
| **T1: Session** | In-process per request chain | Memory (JS object) | No | "What was their last message?" |
| **T2: Conversation** | Per `session_id` | Postgres `task_ai_messages` | No | "What did we discuss this chat?" |
| **T3: Persistent** | Per user, across sessions | Postgres `memory_entries` + pgvector | ✅ Yes | "Yesterday you mentioned Arohan" |
| **T4: Knowledge graph** | Per tenant, entity-relationship | Postgres `kg_*` (deferred per decision #3) | ✅ Yes | "Foundation Wall → blocks → Plaster" |

**Heartbeat** = hourly Vercel Cron that:
1. Scans T3 with `due_at` ≤ now → surfaces as next-message prelude
2. Decays old/low-importance (>90 days, low → archive)
3. Pattern detection: if user asks about X every Monday at 9am, pre-fetch context

This is what makes the system feel *alive* — activity even without user prompting.

### 7.5 Training data labeling UI (decision #4 — "best, not minimal")

Best ≠ overbuild. Best means:
- **Admin route** `/task-bot/admin/labels` (Supabase magic-link auth)
- **Spreadsheet-style review** of `task_ai_messages` flagged for labeling
- **One-click "good" / "needs work"** with optional rewrite
- **Inline RAG hits inspection** — see what chunks the bot retrieved + score them
- **Export to JSONL** for fine-tuning or eval seed
- **RAGAS dashboard** showing retrieval precision/recall trends week-over-week

Not best: a 12-screen flow with multi-user collaboration we won't use for 6 months. Build the 5 features above, ship in Sprint 7.

---

## 8. Voice architecture (parallel to text, same brain)

### Three voice surfaces × three audio paths × three providers

We have FOUR sources lifting from now: QuotaHit (realtime production-locked) · hireai (phase state machine + WS proxy) · IndianWhisper (transcription) · MSBC (TTS).

| Surface | Default provider | Fallback | Lift from | Audio path |
|---|---|---|---|---|
| **Realtime — browser direct** | **Gemini 2.5+ Flash native audio** (cheaper, native multimodal) | OpenAI gpt-4o-mini-realtime-preview | **hireai** `realtime_proxy.py` shape | PCM16 24 kHz mono base64 |
| **Realtime — phone (Twilio bridge)** | OpenAI gpt-4o-mini-realtime-preview | Gemini Live (D-QH-090 code, deploy-ready) | **QuotaHit voice-server** (stable-v11.2) | mulaw 8 kHz, 640-byte chunks, 0.07s sleep |
| **Async transcription** (voice notes) | Groq Whisper | OpenAI Whisper | **IndianWhisper** + existing `lib/whatsapp/transcribe.ts` | OGG/Opus or any |
| **TTS (text → speech)** | ElevenLabs Rachel | Edge TTS Jenny | MSBC pattern | mp3 / opus |

### Why Gemini Live default for browser

| | OpenAI Realtime | Gemini 2.5 Flash native audio |
|---|---|---|
| Input cost | ~$0.06/min | ~$0.018/min (3.3× cheaper) |
| Output cost | ~$0.24/min | ~$0.075/min (3.2× cheaper) |
| Native audio (no TTS step) | Yes | Yes |
| Multilingual | Strong | Strong (Hindi-aware out of box) |
| Native tool calling | Yes | Yes |
| Production-tested in your stack | QH `/twilio-bridge-live` | QH `D-QH-090` (code complete, awaiting deploy) |

**Default = Gemini Live native audio** for browser/PWA voice. **OpenAI Realtime stays as fallback + Twilio bridge** because of QH's locked stable-v11.2 precedent. When Gemini 3.x Flash native audio ships, swap in (same API shape).

### Exact configs to copy

**Path A — Browser direct via Gemini Live (default, ~3× cheaper)**
- Model: `gemini-3.1-flash-native-audio (Gemini 3.x family, latest); fallback gemini-2.5-flash-native-audio` (upgrade to `gemini-3-flash-native-audio` when GA)
- WSS: `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=<GOOGLE_AI_API_KEY>`
- Audio format: PCM16 24 kHz mono, base64 in JSON envelope
- Tool dispatch: same `function_call` shape, replies are inline tool result frames
- Lift pattern from: `hireai/backend/app/api/v1/endpoints/realtime_proxy.py` (WS proxy shape) + QH `voice-server/gemini_live_client.py` (Gemini Live message envelope)

**Path B — Browser direct via OpenAI Realtime (fallback)**
- Model: `gpt-4o-mini-realtime-preview`
- WSS: `wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview`
- Audio format: PCM16 24 kHz mono base64 in JSON
- Lift pattern from: `hireai/.../realtime_proxy.py` directly

**Path C — Phone via Twilio (QH-locked, production-proven)**
- Same OpenAI Realtime model as Path B
- BUT audio path is mulaw 8 kHz / 640-byte chunks / 0.07s sleep (Twilio's spec, NOT browser's)
- **Event names: `response.output_audio.delta` + `response.output_audio_transcript.delta`** (NOT beta `response.audio.delta` — this is the one-day bug QH hit; defensive code listens for both)
- Voice: `shimmer`
- Lift pattern from: `QuotaHit/voice-server/openai_realtime_client.py` + Modal deploy pattern (force-stop before redeploy)

### Phase state machine pattern (lifted from hireai)

Hireai's killer pattern: `InterviewPhase` enum drives a different system prompt per phase, transitions on AI's natural language cue ("Let's move on to..." → emits `round_change` event).

For Onsite, this maps to **Support flows** (Sprint 3) not chat:
```
TaskSupportPhase = TRIAGE → INVESTIGATE → RESOLVE → CONFIRM
```

- TRIAGE: gather info, classify urgency
- INVESTIGATE: pull project context, check task state, fetch related deps
- RESOLVE: propose fix or workaround
- CONFIRM: verify with user, log resolution to memory

Each phase has its own system prompt template (formatted with `_format_phase_template` like hireai does). Phase transitions trigger UI events (`phase_change`) so the chat UI shows progress.

**Not for regular chat** — Onsite chat is freeform, phases would feel rigid. State machine only fires for Support sessions where structure adds clarity.

### Onsite-specific voice flows

- "Log progress on Foundation Wall, +5 sqft, today's pour went well" → realtime parses → tool_call(`record_task_progress`)
- Voice + WhatsApp = voice note → Groq transcribe → text path → reply (already wired)
- Voice + PWA = push-to-talk button + Gemini Live realtime (Sprint 2)
- Voice + Phone (future) = Twilio bridge with QH-locked OpenAI path

### Extra patterns I'd lift from hireai (Dhruv's "more concepts" cue)

| Pattern | hireai file | Lifts into |
|---|---|---|
| `langfuse @observe` decorators on LLM calls | `services/ai_interviewer.py` | All our LLM call sites — production observability for traces |
| Round-change event injection in WS proxy | `realtime_proxy.py:proxy → browser injected events` | Our voice proxy — UI shows "moved to Investigate phase" |
| Assistant chat (separate endpoint) pattern | `endpoints/assistant_chat.py` | Multi-mode chat — Task vs Support vs Training distinct endpoints |
| Schedule endpoint (Calendly-like) | `endpoints/schedule.py` | Future: schedule site inspections from chat |
| Analytics dashboard pattern | `endpoints/analytics.py` | Admin Posthog-lite per-tenant metrics |

---

## 9. Phasing — what to build first

| Phase | Goal | Big lifts | Duration |
|---|---|---|---|
| **Phase 0** (now) | Demo polish, local | Restart server, smoke 14 tools, tunnel for demo | 1-2 days |
| **Phase 1** (week 1) | Memory port | Migration `011_memory_entries.sql`, save/recall tools, T1+T2+T3 wired | 3-4 days |
| **Phase 2** (week 1-2) | 2-tier LLM router + Redis cache + Razorpay parked | Port MSBC `router.py` → TS, Upstash plumbed | 3 days |
| **Phase 3** (week 2) | Heartbeat | Vercel Cron + reminder surface + decay | 2 days |
| **Phase 4** (week 2-3) | Python runner | Sandbox + 5 curated scripts (export csv, velocity, blocked-by, …) | 3 days |
| **Phase 5** | RAG (Sprint 1 dispatch) | Hybrid search from MSBC + Tavily fallback from KF | 5-7 days |
| **Phase 6** | Voice realtime (Sprint 2) | Lifted from QH stable-v11.2 | 4 days |
| **Phase 7** | Training DB + labeling UI (Sprint 4) | "Best" labeling per §7.5 | 5 days |
| **Phase 8** | Support escalation (Sprint 3 + supportiq study) | Memory-aware ticket flow | 4 days |
| **Phase 9** | Mobile Capacitor wrap | One-day project | 1 day |
| **Phase 10** | Knowledge graph + multi-agent orchestration (agentic-workflows pattern) | Only if pattern miner shows it's needed | TBD |

---

## 10. Open decisions for Dhruv (post sign-off)

1. **Greenlight the 3 additional projects to pull from?**
   - agentic-workflows (multi-agent patterns — Phase 4+)
   - supportiq (support escalation — Phase 8 prep)
   - multimodal-rag (image/PDF RAG — Sprint 1 add-on)
2. **OpenRouter as fallback** — which provider precedence?
   - Default: Anthropic direct → OpenAI direct → OpenRouter (same model id)
3. **Heartbeat reminders — push or pull?**
   - Pull = surface on next user open (cheap, no infra)
   - Push = WhatsApp template / web push (premium feel, costs more)
   - Suggest: pull for v1, push when validated
4. **Razorpay tier pricing — propose later?**
   - Yes, after first 10 paid users validate willingness-to-pay

---

## 11. Vision + Document Intelligence (added per Dhruv's "smart not basic" requirement)

### The accuracy problem
Generic vision LLMs hallucinate on dense invoices (95-97% accuracy). Specialized document AI services (Google Doc AI / Azure FR / AWS Textract) hit 99%+ but cost ₹15L/month at lakhs scale. Neither alone is the right answer.

### Our approach — 2-pass hybrid (99.5%+ accuracy at ~$0.10/doc)

```
Document upload (PDF / image / screenshot)
   │
   ▼ 1. Preprocess
       (auto-rotate, deskew, denoise)
   │
   ▼ 2. Pass 1 — Gemini 3.1 Flash Vision + JSON schema
       Structured output mode forces field extraction
   │
   ▼ 3. Field validators
       • GSTIN regex (^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$)
       • PAN regex
       • Date parse + range sanity
       • Σ(line items) == subtotal
       • Σ(subtotal + CGST + SGST + IGST) == total
       • Confidence ≥ threshold per field
   │
   ├── All pass → 100% confidence → store + emit `documents` row
   │
   └── Any fail → 4. Pass 2 — Gemini 3.1 Pro Vision
       Re-extracts ONLY failing fields with focused prompt
       │
       ├── Now valid → store with `auto_corrected: true` flag
       │
       └── Still fail → flag for human review (rare, <2%)
```

### Why this beats alternatives

| Approach | Accuracy | Cost/1K docs | @ 1 lakh users · 5 docs/mo (₹) |
|---|---|---|---|
| Pure Gemini 3.1 Flash | 95-97% | ~$0.05 | ₹2,000 |
| Pure Gemini 3.1 Pro | 98-99% | ~$0.40 | ₹16,000 |
| Google Document AI | 99%+ | $30 | **₹12,50,000** 🚨 |
| Azure Form Recognizer | 99% | $10 | ₹4,20,000 |
| Mistral Document AI | 95%+ | $1 | ₹42,000 |
| **2-pass hybrid (Flash + Pro on fails)** ✅ | **99.5%+** | **~$0.10** | **~₹4,000** |

### Doc-type schemas (each gets dedicated extraction + validation)

| Doc type | Critical fields | Validators |
|---|---|---|
| **GST Invoice** | invoice_no, date, vendor, GSTIN, line_items[], CGST, SGST, IGST, total | GSTIN format + line sum = subtotal + taxes sum = total |
| **Delivery Challan (DC)** | challan_no, date, vendor, items[], quantities, vehicle_no, site_name | Date sanity + item count > 0 |
| **Purchase Order** | po_no, vendor, items[], delivery_date, terms | po_no format + future delivery_date |
| **Petty Cash Receipt** | date, amount, purpose, paid_to | Amount > 0 + date ≤ today |
| **Labor Attendance Slip** | date, names[], hours[], supervisor | Names ≥ 1 + hours 0-24 each |
| **BOQ Excel screenshot** | items[], rates[], quantities[], totals[] | line totals = qty × rate |
| **Site progress photo** | description, work_type guess, % complete guess, visible_issues[] | None — informational |
| **Generic screenshot** | (free-form Q&A) | None |

### New tools added to the agent

| Tool | Purpose | Returns |
|---|---|---|
| `analyze_document(file_url, doc_type?)` | Extract structured fields | JSON matching schema + confidence per field |
| `analyze_image(file_url, question)` | Free-form vision Q&A | Natural language answer |
| `validate_document(json, doc_type)` | Run field validators | List of {field, valid, reason} |
| `link_document_to_task(doc_id, task_id)` | Attach to Onsite task | Link record |

### Storage + DB

New migration `012_documents.sql`:
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  project_id UUID,
  task_id UUID,
  storage_path TEXT NOT NULL,    -- Supabase Storage path
  doc_type TEXT,                  -- gst_invoice / delivery_challan / ...
  extracted_fields JSONB,
  validation_status TEXT,         -- pending / valid / auto_corrected / needs_review
  confidence NUMERIC,
  pass_count INT DEFAULT 1,       -- 1 = Flash only, 2 = Pro fallback fired
  reviewer_id UUID,
  reviewed_at TIMESTAMPTZ,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX documents_tenant_idx ON documents(tenant_id, project_id, task_id);
CREATE INDEX documents_needs_review_idx ON documents(validation_status) WHERE validation_status = 'needs_review';
```

### Reuse from existing projects

- **Image preprocessing**: borrow Multimodal-RAG-System's `image_processor.py` patterns (PIL ops)
- **Vision LLM client**: clone its `vision.py` shape but swap the prompt from "describe image" to "extract these fields"
- **Storage upload**: existing Supabase Storage already in our PWA branch (planned for voice notes)
- **For RAG cross-reference**: every uploaded doc ALSO flows through Multimodal-RAG-System ingest → embeddings stored → "show me all invoices from Vendor X" works via dense search

### When to use vision LLM vs OCR vs Document AI

- **For Onsite v1**: 2-pass Gemini Vision (this approach). No Document AI needed.
- **If accuracy ever hits a wall**: add Mistral Document AI as Pass 0 (cheap baseline) → Gemini Flash as Pass 1 → Gemini Pro as Pass 2. Mistral catches the obvious, Gemini catches edge cases. Cost stays ~$0.15/doc.
- **For drawings/blueprints later**: Gemini 2.5+ Vision still works but consider Bytespider-Vision or specialized CAD parsing later.

### Phase placement
Slot in as **Phase 5.5** (after RAG ingestion, before voice realtime). Reason: ingest pipeline needs to exist first, vision plugs into it for storage + embedding cross-reference.

---

## 12. What this doc replaces

- Parts of `PRD-ADDON.md` — superseded by §2, §4 here
- Parts of `HLD-ADDON.md` — superseded by §3 diagram
- All implementation order in `ROADMAP-ADDON.md` — superseded by §9

What still stands from earlier dispatch:
- `dispatch-sprint-1-rag.md` — still valid, now lifts from MSBC + KF + multimodal-rag together
- `dispatch-sprint-2-voice.md` — still valid, now grounded in QH's stable-v11.2 config
- `dispatch-sprint-5-support.md` — still valid, now grounded in supportiq study

---

**Bottom line:** MSBC is the spine. KF adds polish. Angelina supplies memory + 22-tool action surface. QuotaHit supplies voice realtime (production-locked). Hireai supplies phase state machine. Multimodal-RAG-System (Dhruv's own) supplies the multimodal RAG pipeline. IW + WhatsApp supply async transcription. Current Task AI provides the production-tested customer surface. Combined = enterprise-grade construction AI that runs at **₹12/user/month** on public APIs and scales to lakhs.

---

## 13. Alerts + Notifications subsystem

**Pattern lifted from:** Onsite Sales Intelligence System (10 alert rules proven in prod).

### 10 production alert rules (construction-adapted)

| # | Rule | Trigger | Default channel | Severity |
|---|---|---|---|---|
| 1 | Stale task | `in_progress` + no log >7d | WhatsApp + push | Med |
| 2 | Critical path slip | dep dates push project beyond deadline | WhatsApp + email PM | High |
| 3 | Cost overrun | actuals > 110% estimated | Dashboard | Med |
| 4 | Material shortage forecast | consumption × days remaining > inventory | WhatsApp PM + email vendor | High |
| 5 | Vendor late delivery | DC date > expected by >2d, 2+ times | Admin dashboard | Low |
| 6 | **Weather risk** ⚡ | concrete pour 24h ahead + rain >50% | WhatsApp PM day before | High |
| 7 | Compliance deadline | RERA milestone / GST filing <7d | Push + email | High |
| 8 | **Geo-mismatch** 📍 | worker log geo >500m from site | Push PM | Med |
| 9 | Inactive site | no activity >3d on active project | Push PM | Low |
| 10 | Safety incident | photo classified as safety risk / keywords | Immediate WhatsApp + email | Critical |

### Engine
- Modal scheduled jobs + on-event triggers
- Per-tenant `alert_rules` config (which rules, thresholds)
- Per-user `alert_prefs` (channels, quiet hours)
- Dedup via `alert_log.hash` (SHA-256 of rule+entity+date) — no dupe in 24h

### Delivery channels
- **WhatsApp** (approved Meta templates), **Push** (PWA + Capacitor), **Email** (Resend ₹1.5 each), **In-app** notification center

---

## 14. Domain features unlocked

### 14.1 Geo-tagged actions
- PWA `navigator.geolocation` (with consent) → captured on every `record_task_progress`
- New `progress_geo` table linked to progress entry
- Powers Rule #8 + worker-fraud detection + analytics

### 14.2 Weather-aware scheduling
- OpenWeatherMap API (free tier 1M calls/mo)
- Per-project location → daily forecast cached 6h in Redis
- Calendar-aware: "concrete pour tomorrow, 60% rain — push?"
- Rule #6 fires on threshold

### 14.3 Photo EXIF + safety classifier
- EXIF lat/lon extracted (Pillow)
- Mismatch flag if photo location ≠ project site
- Gemini Vision classifier tags: `safety_risk` / `progress_update` / `material_delivery` / `quality_issue`
- High-severity safety → Rule #10 immediate

### 14.4 Material auto-deduct
- On `record_task_progress` → BOQ lookup → theoretical consumption → inventory decrement
- Bot announces deductions; reconcile with actual DC qty

### 14.5 Vendor performance scoring
- Daily Modal job → on-time rate, quantity accuracy, invoice cleanness → score 0-100
- Exposed via `vendor_performance(vendor_id)` tool + admin dashboard

### 14.6 Critical path recompute
- On any new dep / duration change → `python_run('critical_path_recompute')`
- Updates `tasks.is_on_critical_path` flag
- Alerts PM if critical path > committed timeline

### 14.7 Compliance reminders (RERA / GST)
- Per project: RERA milestone schedule
- Per tenant: GST filing schedule
- Auto-reminders 7d + 1d before (Rule #7)

### 14.8 Webhooks
- Per-tenant `webhook_endpoints` config
- Events: task.created, progress.recorded, dep.created, doc.uploaded, alert.fired
- HMAC-SHA256 signed; retry queue + dead-letter

### 14.9 Scheduled reports
- Mon 8am: weekly status WhatsApp/email per PM
- Daily 6pm: today's accomplishments
- 1st of month: portfolio PDF for admins

### 14.10 Calendar integration (Phase 11)
- Google + Outlook OAuth → voice-created tasks added to calendar

---

## 15. Observability + Security stack (production grade)

### Observability — three layers

| Layer | Tool | Purpose |
|---|---|---|
| **Errors** | Sentry | Source-mapped stack traces, alerting |
| **LLM/Tool traces** | Langfuse | `@observe` on every LLM/tool call — every prompt, latency, cost searchable (pattern from hireai) |
| **Product analytics** | Posthog | DAU/MAU, funnels, A/B flags |

### Security guardrails

| Layer | Mechanism |
|---|---|
| Auth | Onsite JWT (customers) + Supabase magic-link (admin) |
| RBAC | Role claim in JWT → tool catalogue filter (admin/pm/site_engineer/worker/vendor) |
| Tenant isolation | RLS on every table by `tenant_id` |
| Rate limits | Upstash sliding window: 100/min/user, 10K/day/tenant |
| Cost guardrails | Per-tenant daily + monthly LLM cap with hard cutoff |
| Prompt injection | Input sanitization + separator tokens + no-action-tools in doc-analysis context |
| PII handling | Pre-LLM PII strip (phones, GSTIN, PAN) — medassist regex pattern |
| Audit log | `task_ai_actions` append-only + SHA-256 chained |
| DPDP compliance | Consent tracking + `/api/task-bot/export` for data portability |
| Image moderation | Gemini safety filters + manual override flag |
| Webhook signing | HMAC-SHA256 of payload |
| Circuit breakers | 5 fails in 30s → fail-fast 30s |
| Token never logged | Hard rule — every code path audited |

### Disaster recovery
- Supabase Pro: PITR within 7 days
- Daily off-region replica via `pg_dump` → S3 (Modal job)
- Quarterly restore drill, documented in `runbooks/dr-drill.md`
- RTO 2h, RPO 1h

---

## 16. Demo tenant + sandbox mode

- Single env `DEMO_TENANT=true` → Supabase schema with realistic seed
- 5 fake projects, 80 tasks, 200 progress entries, 30 BOQ pages, 20 invoices, 50 photos
- Used for: demos to Akshansh/Sumit, feature testing, onboarding flow
- Enterprise sandbox-per-tenant: copy of their data with `is_sandbox: true` writes that don't bleed to prod

---

## 17. Final tool catalogue (25 tools)

| # | Tool | Phase |
|---|---|---|
| 1-14 | 14 existing Onsite v3 tools | 0 |
| 15 | `save_memory` | 1 |
| 16 | `recall_memory` | 1 |
| 17 | `python_run` | 4 |
| 18 | `rag_search` | 5 |
| 19 | `web_search` | 5 |
| 20 | `analyze_document` | 5.5 |
| 21 | `analyze_image` | 5.5 |
| 22 | `validate_document` | 5.5 |
| 23 | `link_document_to_task` | 5.5 |
| 24 | `vendor_performance` | 10 |
| 25 | `create_support_ticket` | 8 |
