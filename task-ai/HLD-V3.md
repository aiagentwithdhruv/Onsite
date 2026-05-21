# High-Level Design — Onsite Task AI v2

> **Status:** Final | **Date:** 2026-05-22 | **Supersedes:** `HLD.md` + `HLD-ADDON.md`
> **Read alongside:** [ARCHITECTURE-V3.md](./ARCHITECTURE-V3.md) for the big diagram + decisions

---

## 1. System decomposition

```
┌──────────────────────────────────────────────────────────────────┐
│                      CLIENT TIER                                  │
│  PWA (Vercel)  ·  Mobile (Capacitor)  ·  WhatsApp  ·  Phone/Voice │
└────────────────────────┬─────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  EDGE (Vercel)      │  SSE streams · auth · static
              │  Next.js 15 + SW     │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────────────────────────────┐
              │       AGENT TIER (LangGraph ReAct)           │
              │   Plan → Tool select → Execute → Reflect     │
              └──────────┬──────────────────────────────────┘
                         │
       ┌──────┬──────────┼──────────┬──────────┬──────────┬─────────┐
       │      │          │          │          │          │         │
  ┌────▼──┐┌──▼───┐ ┌────▼───┐ ┌────▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌─▼──────┐
  │ LLM   ││MEMORY│ │ RAG    │ │ CACHE   │ │ALERTS  │ │OBSERV. │ │ACTION  │
  │ 2-tier││ 4-t  │ │ multi  │ │ Upstash │ │ engine │ │ Sentry │ │ tier   │
  └───┬───┘└──┬───┘ └────┬───┘ └────┬────┘ └───┬────┘ │Langfuse│ └────────┘
      │       │          │          │          │       │Posthog │
      └───────┴──────────┴──────────┴──────────┘       └────────┘
                          │
              ┌───────────▼───────────┐
              │ Supabase Postgres     │
              │ + pgvector + RLS      │
              └───────────────────────┘
```

---

## 2. Component contracts

### 2.1 Edge tier
- **Tech:** Next.js 15 App Router on Vercel
- **Owns:** PWA shell, service worker (push, offline), static assets, thin API routes that proxy to Agent tier
- **Auth:** Onsite JWT (customer) + Supabase magic-link (admin)
- **Output formats:** SSE streams, JSON, multipart for uploads
- **SLA:** P50 < 200ms (excluding LLM call)

### 2.2 Agent tier — LangGraph ReAct
- **Tech:** LangGraph.js inside Next.js API route (initially) → Modal worker when scale demands
- **State:** `AgentState` = `{messages, tools_called, memory_hits, rag_hits, last_tool_result, tenant_id, role, project_id?}`
- **Loop:** Plan → Tool select → Execute → Reflect → Reply (max 8 iterations)
- **Hallucination guard:** Force-recall if reply claims action without firing tool
- **Phase state machine:** Optional overlay for Support flows (TRIAGE→INVESTIGATE→RESOLVE→CONFIRM)

### 2.3 LLM tier (2-tier router)
- **Tier A (~70%):** Gemini 2.0 Flash direct API ($0.10/M tokens, 1-3s latency)
- **Tier B (~30%):** Claude Haiku 4.5 default, Sonnet 4.5 for action verbs + complex reasoning ($0.8-3/M tokens, 2-5s)
- **Routing:** `pickModel(messages)` heuristic — action verbs, query complexity, history depth
- **Fallback:** OpenRouter same model id when direct provider returns 5xx/429
- **Cost guardrail:** Per-tenant LLM spend cap; hard cutoff with friendly message
- **Future Tier C (Ollama):** Deferred (decision #2); public APIs only for now

### 2.4 Memory tier (4 levels)

| Level | Storage | Scope | Heartbeat? |
|---|---|---|---|
| T1 session | JS process memory | Per request chain | No |
| T2 conversation | Postgres `task_ai_messages` | Per session_id | No |
| T3 persistent | Postgres `memory_entries` + pgvector | Per user, cross-session | **Yes** (Vercel Cron hourly) |
| T4 knowledge graph | Postgres `kg_entities` + `kg_edges` | Per tenant | Yes (deferred Phase 12) |

### 2.5 RAG tier (multimodal)
- **Storage:** `rag_chunks` table — Postgres pgvector + tsvector hybrid index
- **Embeddings:** `gemini-embedding-2` at 1536-dim Matryoshka
- **Modalities:** text · PDF · image · audio · video — all in one space
- **Search:** BM25 (tsvector) + dense (pgvector HNSW) + Reciprocal Rank Fusion → top-K
- **Ingest:** Modal Python microservice (lift Multimodal-RAG-System wholesale)
- **Web fallback:** Tavily when retrieval scores all <0.3

### 2.6 Cache tier (Upstash Redis)
- **Semantic cache:** cosine >0.95 on query embedding → reuse answer (saves ~30% LLM)
- **Exact cache:** identical `tool::args::tenant` → reuse result (5-min TTL)
- **Rate limits:** sliding window per user + per tenant
- **Auto-invalidate:** any successful mutation invalidates user's tool cache

### 2.7 Action tier
- **Onsite v3 connector:** 14 tools wrapping the Onsite REST API
- **Python runner:** sandboxed subprocess for complex deterministic flows (8 curated scripts → grow to 50)
- **Document AI:** 2-pass Gemini Vision (Flash → Pro on validator failures)
- **Voice realtime:** Gemini 3.1 Flash native audio (browser) + OpenAI gpt-4o-mini-realtime (Twilio bridge)
- **Memory tools:** save/recall via T3 store
- **Propose → confirm → execute:** all mutating actions confirmed before execution

### 2.8 Alerts engine
- Scheduled Modal jobs + on-event triggers
- 10 alert rules (see ARCHITECTURE-V3 §13)
- Delivery: WhatsApp templates, push, email, in-app
- Dedup via SHA-256 hash per rule+entity+date

### 2.9 Observability stack
- **Sentry:** errors with source maps, alerting
- **Langfuse:** every LLM/tool call (`@observe` decorator) — prompt, response, latency, cost
- **Posthog:** product analytics, A/B flag service, funnels

---

## 3. Cross-cutting concerns

### 3.1 Auth + RBAC

```
Onsite JWT → decodeJwt() → claims: { tenant_id, user_id, role, project_ids?, exp }
                                          │
                                          ▼
                             toolFilter(role) — registry-based
                                          │
                                          ▼
                             LangGraph tool catalogue narrowed
```

- 5 roles: `admin`, `pm`, `site_engineer`, `worker`, `vendor`
- Tool registry maps `tool_id → allowed_roles[]`
- Every tool call validates: tenant_id matches resource owner + role allowed + project scope intersects

### 3.2 Tenant isolation
- Every table has `tenant_id UUID NOT NULL`
- RLS policy: `tenant_id = current_setting('app.tenant_id')::uuid`
- Service role bypasses RLS; only server-side code uses it
- Per-tenant `app.tenant_id` set at start of each request

### 3.3 PII handling (DPDP compliance)
- Pre-LLM scrubber strips: phones (`+91 \d{10}`), GSTIN, PAN, bank account numbers, Aadhar
- Replaces with placeholders (`[PHONE_1]`, `[GSTIN_1]`)
- LLM response post-processed: placeholders restored before user sees them
- Original values stored in scrubber session (in-memory, request-scoped)

### 3.4 Rate limits + cost guardrails

| Layer | Limit | Action on breach |
|---|---|---|
| Per user, per minute | 100 requests | 429 with retry-after |
| Per tenant, per day | 10K requests | 429 + admin email |
| Per tenant LLM spend, per day | ₹500 (configurable) | Hard cutoff, friendly chat message |
| Per tenant LLM spend, per month | ₹15K (configurable) | Hard cutoff + email |
| Per tool, per turn | 8 iterations | Stop, return "couldn't complete" |

### 3.5 Failure modes + handling

| Failure | Detection | Recovery |
|---|---|---|
| Gemini 5xx | HTTP code | OpenRouter fallback (same model id) |
| Anthropic 429 | HTTP code + retry-after | Wait + backoff + OpenRouter |
| Supabase throttle | HTTP 503 | Retry 3× with jitter, fail with message |
| Onsite v3 API down | HTTP 5xx / timeout | Circuit breaker (5 fails / 30s → fail-fast 30s) |
| Webhook delivery fail | Non-2xx after 3 retries | Dead-letter queue, admin notify |
| Voice WS drops | Connection closed | Auto-reconnect, replay last 5s of audio |
| LLM cost cap hit | Spend tracker check | Friendly cutoff message, next-day reset |

---

## 4. Data flow — three critical paths

### 4.1 Text chat turn

```
User msg
  → Edge (auth) → Agent tier
  → Pre-LLM PII scrub
  → Recall memory (T2 + T3 via embedding query)
  → Semantic cache check (cosine >0.95)
     ├── hit → return cached answer
     └── miss → pickModel(messages) → LLM call
        → LLM emits tool_call or final answer
           ├── tool_call → execute → reflect → loop
           └── final answer → post-process (restore PII) → return SSE
  → Persist message to T2
  → Heartbeat: extract facts into T3 if importance>=med
  → Log to Langfuse + audit log
```

### 4.2 Document upload + extract

```
User uploads file (PDF/image)
  → Edge multipart → store in Supabase Storage
  → Trigger async job (Modal): analyze_document
     → Preprocess (auto-rotate, deskew)
     → Pass 1: Gemini 3.1 Flash + JSON schema → fields
     → Run validators
        ├── all pass → status='valid' → insert documents row
        └── any fail → Pass 2: Gemini 3.1 Pro on failing fields
           ├── now valid → status='auto_corrected'
           └── still fail → status='needs_review' → admin queue
  → Embed full doc into rag_chunks (cross-modal search later)
  → Webhook tenant.webhooks → document.uploaded event
```

### 4.3 Voice realtime (browser)

```
PWA mic → WebSocket /api/task-bot/voice/realtime → server proxy
  → server mints Gemini Live token (server-side OAuth, never exposed)
  → opens WSS to Gemini Live (native audio gemini-3.1-flash-native-audio)
  → bidirectional audio (PCM16 24kHz)
  → Gemini emits function_call → server intercepts → dispatches into LangGraph agent
     → agent's tool result → server sends as tool_call_response back to Gemini
  → Gemini continues speaking with result
  → all turns logged to task_ai_messages + Langfuse
```

---

## 5. Deployment topology

### 5.1 Phase 1-9 (Next.js sufficient)
- Vercel: frontend + API routes (Hobby → Pro at 50K req/day)
- Supabase: Postgres + Storage + Auth (Pro plan)
- Upstash: Redis (free → $30/mo)
- Modal: Python workers for RAG ingest + Document AI + scheduled jobs ($50-200/mo)
- Sentry + Langfuse + Posthog: hosted SaaS

### 5.2 Phase 10+ (when scale demands)
- Move agent tier to Modal/ECS Fargate (long-running streams, WebSocket fanout)
- Add Cloudflare in front (geo routing, DDoS protection)
- Read replicas in 2 regions (Mumbai primary, Singapore secondary)

### 5.3 Mobile (Phase 9)
- Capacitor 6 wrap of PWA → iOS + Android binaries
- App Store + Play Store distribution
- Native push notifications (FCM + APNs)

---

## 6. Integration points

| External system | Integration | Purpose |
|---|---|---|
| **Onsite v3 API** | REST + JWT | All 100+ Onsite operations |
| **Meta WhatsApp Cloud API** | Webhook + REST | Inbound voice notes, outbound replies, templates |
| **Razorpay** | API + webhooks | Billing (Phase 11+) |
| **OpenWeatherMap** | REST polling | Rule #6 weather alerts |
| **Google Calendar / Outlook** | OAuth + REST | Voice-created task → calendar event |
| **Resend** | SMTP-via-API | Transactional email |
| **Twilio** (later) | Voice WSS | Phone-based voice (QH stable-v11.2 config) |
| **Gemini API** | REST + WSS | LLM, embedding, native audio voice |
| **Anthropic API** | REST | LLM (Haiku/Sonnet) |
| **OpenRouter** | REST | LLM fallback |
| **Groq** | REST | Whisper transcription |
| **Tavily** | REST | Web search RAG fallback |
| **Sentry / Langfuse / Posthog** | SDK | Observability |

---

## 7. Scaling story (cost + capacity)

| Stage | Users | Monthly cost (text + voice + infra) | Migration trigger |
|---|---|---|---|
| 0-1K | Demo + pilot | <$300 | — |
| 1K-10K | First cohort | ~$1,500 | Add Modal for Python runner + RAG ingest |
| 10K-50K | Growth | ~$5,000 | Cache hit rate >40%, monitor closely |
| 50K-1L | Scale | ~$14,000 | Migrate agent tier to Modal, add multi-region |
| 1L+ | Hyperscale | ~$40K | Consider Tier 3 Ollama, custom infra |

---

## 8. Anti-patterns to avoid (hard-learned rules)

1. Don't put JWT in LLM payload (token never logged, never sent to LLM, ever)
2. Don't auto-execute mutating actions — always propose → confirm → execute
3. Don't run unsanitized strings through Python runner — strict whitelist only
4. Don't write to prod Supabase from agent tier without RLS check
5. Don't trust EXIF / geo from client — verify against project location server-side
6. Don't ship a voice change without testing against QH `stable-v11.2-voice-live` precedent
7. Don't add a 26th tool without checking if Python runner covers it
8. Don't skip the embedding incompatibility check — `gemini-embedding-2` ≠ `gemini-embedding-001`
9. Don't bypass cost cap for "just one query" — single tenant can drain ₹10K/day
10. Don't deploy without Sentry + Langfuse breadcrumbs in place
