# Low-Level Design — Onsite Task AI v2

> **Status:** Final | **Date:** 2026-05-22 | **Supersedes:** `LLD.md`
> **Read alongside:** [ARCHITECTURE-V3.md](./ARCHITECTURE-V3.md) · [HLD-V3.md](./HLD-V3.md)

---

## 1. Repository layout

```
onsite-hub/                       (code — github.com/aiagentwithdhruv/onsite-hub, PRIVATE)
├── src/
│   ├── app/
│   │   ├── task-bot/
│   │   │   ├── page.tsx                    Chat UI (3-view: setup/dashboard/chat)
│   │   │   ├── layout.tsx                  PWA shell (RegisterSW, BottomTabBar, InstallPrompt)
│   │   │   ├── admin/page.tsx              Admin 24h stats
│   │   │   └── admin/labels/page.tsx       Phase 7 — labeling UI
│   │   └── api/task-bot/
│   │       ├── route.ts                    Main chat — LangGraph ReAct loop
│   │       ├── chat-log/route.ts           Persist single turn
│   │       ├── sessions/route.ts           List/load/rename/delete sessions
│   │       ├── feedback/route.ts           👍/👎 capture
│   │       ├── my-stats/route.ts           Per-user time-saved
│   │       ├── admin-stats/route.ts        Tenant 24h KPIs
│   │       ├── export-training-data/route.ts JSONL export
│   │       ├── memory/
│   │       │   ├── save/route.ts           save_memory tool endpoint
│   │       │   └── recall/route.ts         recall_memory tool endpoint
│   │       ├── rag/
│   │       │   ├── ingest/route.ts         Document/media upload → Modal
│   │       │   └── query/route.ts          Hybrid search → SSE answer
│   │       ├── vision/
│   │       │   ├── analyze-document/route.ts  2-pass extraction
│   │       │   └── analyze-image/route.ts     Free-form vision Q&A
│   │       ├── voice/
│   │       │   ├── realtime/route.ts        WSS proxy → Gemini Live / OpenAI
│   │       │   └── transcribe/route.ts      Groq Whisper async
│   │       ├── alerts/
│   │       │   ├── config/route.ts          Per-tenant rule config
│   │       │   └── log/route.ts             List alert history
│   │       ├── webhooks/
│   │       │   ├── config/route.ts          Per-tenant webhook endpoint
│   │       │   └── deliver/route.ts         Outbound dispatch
│   │       ├── docs/
│   │       │   ├── upload/route.ts          Multipart upload
│   │       │   └── [id]/route.ts            Get extracted fields
│   │       ├── reports/
│   │       │   └── schedule/route.ts        Cron-triggered weekly/daily reports
│   │       ├── whatsapp/
│   │       │   ├── webhook/route.ts         Meta Cloud API webhook
│   │       │   ├── start-link/route.ts      OTP flow start
│   │       │   └── test-send/route.ts       Outbound test
│   │       └── push/
│   │           ├── register/route.ts        Web push subscription
│   │           └── send/route.ts            Internal sender
│   ├── components/
│   │   ├── task-bot-pwa/                   PWA shell components
│   │   └── AppShell.tsx                    Bypass PIN gate for /task-bot
│   └── lib/
│       ├── agent/
│       │   ├── graph.ts                    LangGraph state machine
│       │   ├── router.ts                   2-tier LLM router
│       │   ├── tools.ts                    Tool registry + RBAC filter
│       │   ├── actions.ts                  Propose→confirm→execute helpers
│       │   └── connectors/
│       │       ├── base.ts                 BaseConnector ABC
│       │       ├── onsite.ts               14 Onsite v3 tools wrapped
│       │       └── registry.ts             Plugin registry
│       ├── memory/
│       │   ├── repository.ts               4-tier memory CRUD
│       │   ├── embed.ts                    Gemini embedding wrapper
│       │   └── heartbeat.ts                Pattern miner + reminder surface
│       ├── rag/
│       │   ├── pipeline.ts                 Orchestration (calls Modal)
│       │   ├── embedding.ts                Gemini Embedding 2 wrapper
│       │   ├── vectorstore.ts              pgvector + tsvector
│       │   └── processors/                 (ported from Multimodal-RAG-System)
│       │       ├── text.ts
│       │       ├── pdf.ts
│       │       ├── image.ts
│       │       ├── audio.ts
│       │       └── video.ts
│       ├── vision/
│       │   ├── document.ts                 2-pass extraction
│       │   ├── schemas/                    Per-doc-type schemas
│       │   │   ├── gst_invoice.ts
│       │   │   ├── delivery_challan.ts
│       │   │   ├── purchase_order.ts
│       │   │   ├── petty_cash.ts
│       │   │   ├── labor_slip.ts
│       │   │   ├── boq_screenshot.ts
│       │   │   ├── site_photo.ts
│       │   │   └── generic.ts
│       │   └── validators.ts               GSTIN, PAN, sum-of-items, dates
│       ├── voice/
│       │   ├── realtime-proxy.ts           WSS bridge (lifted from hireai + QH)
│       │   ├── gemini-live.ts              Gemini 3.1 Flash native audio client
│       │   └── openai-realtime.ts          QH-locked config
│       ├── alerts/
│       │   ├── rules/                      10 rule implementations
│       │   ├── delivery.ts                 WhatsApp/push/email dispatch
│       │   └── dedup.ts                    SHA-256 hash check
│       ├── domain/
│       │   ├── weather.ts                  OpenWeatherMap client
│       │   ├── geo.ts                      Geo capture + EXIF
│       │   ├── critical-path.ts            CPM algorithm
│       │   └── vendor-score.ts             Performance scoring
│       ├── python-runner/
│       │   ├── runner.ts                   Sandbox subprocess
│       │   └── scripts/                    Curated script library
│       ├── cache/
│       │   └── upstash.ts                  Semantic + exact cache
│       ├── ratelimit/
│       │   └── upstash.ts                  Sliding window limits
│       ├── pii/
│       │   └── scrubber.ts                 Regex-based PII strip
│       ├── obs/
│       │   ├── sentry.ts
│       │   ├── langfuse.ts                 @observe decorator
│       │   └── posthog.ts
│       ├── push/                           web-push pipeline
│       ├── pwa/                            install/detect helpers
│       ├── storage/                        secure token in IDB
│       └── whatsapp/                       Meta Cloud API client + linking
├── public/
│   ├── task-bot-manifest.json              PWA manifest
│   ├── task-bot-sw.js                      Service worker
│   └── icons/task-bot/                     PWA icons (Phase 1)
├── scripts/
│   ├── generate-vapid.mjs
│   ├── deploy-to-vercel.sh
│   └── eval/                               RAGAS golden test suite
└── modal/                                  Python microservice (RAG + Doc AI)
    ├── app.py                              Modal entry
    ├── rag_ingest.py                       Lift from Multimodal-RAG-System
    ├── document_extract.py                 2-pass vision
    └── requirements.txt

Onsite/task-ai/                  (docs — github.com/aiagentwithdhruv/Onsite, PRIVATE)
├── BRD-V3.md                    Business requirements (this set)
├── PRD-V3.md                    Product requirements
├── ARCHITECTURE-V3.md           Master architecture
├── HLD-V3.md                    High-level design
├── LLD-V3.md                    Low-level design (this doc)
├── CLAUDE.md                    Master AI context
├── MEMORY.md                    Persistent learnings
├── STATE.md                     Living state log
├── API-SPECS.md                 Onsite v3 endpoints
├── BUG-TRACKER.md               Known issues
├── docs/                        Deep-dive docs
├── runbooks/                    Deploy + DR runbooks
└── database/                    SQL migrations 001-018
```

---

## 2. Database — all migrations

### Already applied (001-010)
1. `001_task_ai_actions.sql` — audit log
2. `002_relax_not_null.sql` — schema tweak
3. `003_task_ai_messages.sql` — chat persistence + feedback
4. `004_task_ai_session_meta.sql` — title + project_context
5-8. (reserved)
9. `009_push_subscriptions.sql` — PWA web push
10. `010_wa_user_link.sql` — WhatsApp phone↔user linking

### New (V3 — 011-018)

#### `011_memory_entries.sql`
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memory_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  topic TEXT NOT NULL,
  content TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('conversation','fact','preference','task','decision','client','project')),
  tags TEXT[] DEFAULT '{}',
  importance TEXT NOT NULL CHECK (importance IN ('low','med','high')),
  due_at TIMESTAMPTZ,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now(),
  archived_at TIMESTAMPTZ
);

CREATE INDEX memory_user_idx ON memory_entries(tenant_id, user_id);
CREATE INDEX memory_type_idx ON memory_entries(type);
CREATE INDEX memory_due_idx ON memory_entries(due_at) WHERE archived_at IS NULL;
CREATE INDEX memory_embedding_idx ON memory_entries USING hnsw (embedding vector_cosine_ops);

ALTER TABLE memory_entries ENABLE ROW LEVEL SECURITY;
CREATE POLICY memory_iso ON memory_entries
  USING (tenant_id::text = current_setting('app.tenant_id', true));
```

#### `012_documents.sql`
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  project_id UUID,
  task_id UUID,
  storage_path TEXT NOT NULL,
  doc_type TEXT,
  extracted_fields JSONB,
  validation_status TEXT CHECK (validation_status IN ('pending','valid','auto_corrected','needs_review')),
  confidence NUMERIC,
  pass_count INT DEFAULT 1,
  reviewer_id UUID,
  reviewed_at TIMESTAMPTZ,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX documents_proj_idx ON documents(tenant_id, project_id, task_id);
CREATE INDEX documents_review_idx ON documents(validation_status) WHERE validation_status = 'needs_review';
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_iso ON documents
  USING (tenant_id::text = current_setting('app.tenant_id', true));
```

#### `013_rag_chunks.sql`
```sql
CREATE TABLE rag_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('document','memory','manual','web')),
  source_id UUID,
  modality TEXT NOT NULL CHECK (modality IN ('text','pdf','image','audio','video')),
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536),
  tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX rag_chunks_tenant_idx ON rag_chunks(tenant_id);
CREATE INDEX rag_chunks_emb_idx ON rag_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX rag_chunks_tsv_idx ON rag_chunks USING gin(tsv);
ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY rag_chunks_iso ON rag_chunks
  USING (tenant_id::text = current_setting('app.tenant_id', true));
```

#### `014_alerts.sql`
```sql
CREATE TABLE alert_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  rule_id TEXT NOT NULL,
  enabled BOOLEAN DEFAULT true,
  config JSONB,
  UNIQUE(tenant_id, rule_id)
);

CREATE TABLE alert_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID,
  project_id UUID,
  rule_id TEXT NOT NULL,
  severity TEXT CHECK (severity IN ('low','med','high','critical')),
  payload JSONB NOT NULL,
  hash TEXT NOT NULL,
  delivered_channels TEXT[],
  acknowledged_by UUID,
  acknowledged_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX alert_dedup_idx ON alert_log(hash, date_trunc('day', created_at));
ALTER TABLE alert_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY alert_log_iso ON alert_log
  USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE TABLE alert_prefs (
  user_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  channels JSONB NOT NULL,
  quiet_hours JSONB
);
```

#### `015_webhooks.sql`
```sql
CREATE TABLE webhook_endpoints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  url TEXT NOT NULL,
  events TEXT[] NOT NULL,
  secret TEXT NOT NULL,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE webhook_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint_id UUID REFERENCES webhook_endpoints(id),
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT CHECK (status IN ('pending','delivered','failed','dead_letter')),
  attempts INT DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `016_progress_geo.sql`
```sql
CREATE TABLE progress_geo (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  progress_id UUID NOT NULL,
  user_id UUID NOT NULL,
  lat NUMERIC(10,7),
  lon NUMERIC(10,7),
  accuracy_meters NUMERIC,
  captured_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX progress_geo_progress_idx ON progress_geo(progress_id);
```

#### `017_vendor_scores.sql`
```sql
CREATE TABLE vendor_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  vendor_id UUID NOT NULL,
  on_time_rate NUMERIC,
  quantity_accuracy NUMERIC,
  invoice_cleanness NUMERIC,
  compound_score NUMERIC,
  computed_at TIMESTAMPTZ DEFAULT now()
);
```

#### `018_consent_audit.sql`
```sql
CREATE TABLE consent_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  scope TEXT NOT NULL,
  granted BOOLEAN NOT NULL,
  granted_at TIMESTAMPTZ DEFAULT now(),
  ip TEXT,
  user_agent TEXT
);

-- Make task_ai_actions append-only + SHA-chained
ALTER TABLE task_ai_actions ADD COLUMN prev_hash TEXT;
ALTER TABLE task_ai_actions ADD COLUMN curr_hash TEXT;
REVOKE UPDATE, DELETE ON task_ai_actions FROM service_role;
```

---

## 3. API contracts (every internal endpoint)

### Convention
- All endpoints: `POST` with JSON body
- Auth: `Authorization: Bearer <onsite_jwt>` (customer) or `Authorization: Bearer <supabase_token>` (admin)
- Error shape: `{ error: string, code?: string, details?: any }`

### Chat
- **`POST /api/task-bot`** — main chat
  - Body: `{ messages, token, baseUrl, session_id?, session_title?, model? }`
  - Response: `{ reply, tool_called?, tool_name?, success?, card?, suggestions? }`

### Memory
- **`POST /api/task-bot/memory/save`**
  - Body: `{ topic, content, type, importance, tags?, due_at? }`
  - Response: `{ id, embedding_dim }`

- **`POST /api/task-bot/memory/recall`**
  - Body: `{ query, limit?, type_filter? }`
  - Response: `{ hits: [{ id, content, similarity, ... }] }`

### RAG
- **`POST /api/task-bot/rag/ingest`** (multipart)
  - Body: file + `{ doc_type?, project_id?, task_id? }`
  - Response: `{ doc_id, status: 'queued', estimated_seconds }`
  - Async via Modal

- **`POST /api/task-bot/rag/query`**
  - Body: `{ query, top_k?, filters? }`
  - Response: SSE stream with `{ chunk, sources, tokens }`

### Vision
- **`POST /api/task-bot/vision/analyze-document`**
  - Body: `{ file_url, doc_type? }`
  - Response: `{ doc_id, extracted_fields, confidence, validation_status, pass_count }`

- **`POST /api/task-bot/vision/analyze-image`**
  - Body: `{ file_url, question }`
  - Response: `{ answer, confidence }`

### Voice
- **`POST /api/task-bot/voice/transcribe`** (multipart)
  - Body: audio file
  - Response: `{ text, language, confidence }`

- **`/api/task-bot/voice/realtime`** (WebSocket)
  - Upgrade WSS, server proxies to Gemini Live or OpenAI Realtime
  - Token minted server-side (key never to client)

### Alerts
- **`POST /api/task-bot/alerts/config`** (admin)
  - Body: `{ rule_id, enabled, config? }`
  - Response: `{ saved: true }`

- **`POST /api/task-bot/alerts/log`**
  - Body: `{ limit?, since?, severity_filter? }`
  - Response: `{ alerts: [...] }`

### Webhooks
- **`POST /api/task-bot/webhooks/config`** (admin)
  - Body: `{ url, events, secret }`
  - Response: `{ endpoint_id }`

### Reports
- **`POST /api/task-bot/reports/schedule`** (admin)
  - Body: `{ frequency, time, recipients }`
  - Response: `{ schedule_id }`

### Docs
- **`POST /api/task-bot/docs/upload`** (multipart)
  - Body: file
  - Response: `{ doc_id, storage_path }`

- **`GET /api/task-bot/docs/[id]`**
  - Response: `{ doc, extracted_fields, validation_status, source_url }`

### WhatsApp (existing)
- **`POST /api/task-bot/whatsapp/webhook`** — Meta inbound
- **`POST /api/task-bot/whatsapp/start-link`** — OTP start
- **`POST /api/task-bot/whatsapp/test-send`** — outbound test

### Admin
- **`POST /api/task-bot/admin-stats`** — tenant KPIs
- **`POST /api/task-bot/my-stats`** — per-user time-saved
- **`POST /api/task-bot/export-training-data`** — JSONL

---

## 4. Tool catalogue — full specifications

(Each tool: name, scope, params, returns, RBAC, error modes)

### 4.1 Onsite v3 connector (14 existing — no spec change)
`list_companies` · `list_projects` · `list_tasks` · `list_subactivities` · `list_dependencies` · `list_progress_history` · `create_task_dependency` · `update_task_dependency` · `delete_task_dependency` · `record_task_progress` · `delete_task_progress` · `add_task` · `add_subactivity` · `get_project_stats`

### 4.2 New tools (Phase 1+)

**`save_memory(topic, content, type, importance, tags?, due_at?)`**
- Roles: all
- Returns: `{ id }`

**`recall_memory(query, limit?, type_filter?)`**
- Roles: all
- Returns: `{ hits: [{ id, content, similarity }] }`

**`python_run(script_id, args_json)`**
- Roles: pm, admin
- Whitelist of 8 scripts initially
- Returns: `{ stdout, stderr, exit_code }`

**`rag_search(query, top_k?, filters?)`**
- Roles: all
- Returns: `{ chunks: [{ content, similarity, source }] }`

**`web_search(query, top_k?)`**
- Roles: site_engineer, pm, admin
- Tavily fallback
- Returns: `{ results: [...] }`

**`analyze_document(file_url, doc_type?)`**
- Roles: all
- 2-pass Vision
- Returns: `{ extracted_fields, validation_status, confidence }`

**`analyze_image(file_url, question)`**
- Roles: all
- Returns: `{ answer }`

**`validate_document(json, doc_type)`**
- Roles: all
- Returns: `{ valid, failures: [{ field, reason }] }`

**`link_document_to_task(doc_id, task_id)`**
- Roles: site_engineer, pm, admin
- Returns: `{ linked: true }`

**`vendor_performance(vendor_id?)`**
- Roles: pm, admin
- Returns: `{ scores: [...] }`

**`create_support_ticket(category, severity, description)`**
- Roles: all
- Returns: `{ ticket_id }`

---

## 5. Sequence diagrams — critical flows

### 5.1 Document upload + 2-pass extract

```
User → PWA: drag-drop GST invoice
PWA → /api/task-bot/docs/upload: multipart POST
Edge: validate auth + tenant + size
Edge → Supabase Storage: upload file
Edge → DB: insert documents (status=pending)
Edge → Modal: trigger analyze_document(doc_id)
Edge → PWA: { doc_id, status: 'queued' }
PWA → polling /api/task-bot/docs/[id]

Modal:
  fetch file from Storage
  preprocess (rotate/deskew/denoise)
  Pass 1: Gemini Flash + JSON schema
  run validators
  if all pass:
    UPDATE documents SET extracted_fields=..., status='valid', confidence=...
  else:
    Pass 2: Gemini Pro on failing fields only
    re-run validators
    if now pass:
      UPDATE ... status='auto_corrected', pass_count=2
    else:
      UPDATE ... status='needs_review'
  fire webhook document.uploaded
  ingest to rag_chunks for cross-modal search
```

### 5.2 Voice realtime (browser)

```
PWA: open mic, init WS connection
PWA → /api/task-bot/voice/realtime: WSS upgrade
Edge: validate auth, get role, get session
Edge → Gemini Live: open WSS with server-side API key
Edge: bidirectional proxy
  mic chunk → Gemini Live: PCM16 24kHz base64
  Gemini Live → audio response: PCM16 stream → PWA

When Gemini emits function_call:
  Edge: intercept, dispatch into LangGraph tool
  Edge: tool result → Gemini Live as function_response
  Gemini: continues speaking

On end:
  Edge: log full turn to task_ai_messages
  Edge: extract facts to memory
  Edge: Langfuse trace
```

### 5.3 Heartbeat reminder loop

```
Vercel Cron (hourly): GET /api/task-bot/heartbeat
Edge:
  for each tenant:
    SELECT memory_entries WHERE due_at <= now() AND archived_at IS NULL
    for each due memory:
      SELECT user's last_session
      INSERT into session_preludes (surfaced on next user open)
  for each tenant:
    pattern miner: detect "every Monday 9am asks about X"
    pre-warm RAG cache for X
  decay:
    UPDATE memory_entries SET archived_at = now()
    WHERE importance='low' AND created_at < now() - interval '90 days'
```

---

## 6. File-level checklists per phase

### Phase 0 (demo polish)
- [ ] `lib/obs/sentry.ts` — install SDK
- [ ] `lib/obs/langfuse.ts` — @observe decorator
- [ ] Demo tenant seed script in `scripts/seed-demo.ts`

### Phase 1 (memory)
- [ ] `database/011_memory_entries.sql` apply via `supabase db push`
- [ ] `lib/memory/repository.ts` — port from Angelina
- [ ] `lib/memory/embed.ts` — Gemini Embedding 2 wrapper
- [ ] `app/api/task-bot/memory/{save,recall}/route.ts`
- [ ] Wire save/recall into `lib/agent/graph.ts` tool catalogue

### Phase 2 (router + cache + cost caps)
- [ ] `lib/agent/router.ts` — port MSBC router.py to TS
- [ ] `lib/cache/upstash.ts` — semantic + exact
- [ ] `lib/ratelimit/upstash.ts` — sliding window
- [ ] Per-tenant cost cap check in route.ts

### Phase 5 (RAG)
- [ ] `modal/rag_ingest.py` — lift Multimodal-RAG-System wholesale
- [ ] `database/013_rag_chunks.sql`
- [ ] `lib/rag/pipeline.ts` — orchestration calling Modal
- [ ] `app/api/task-bot/rag/{ingest,query}/route.ts`

### Phase 5.5 (vision)
- [ ] `database/012_documents.sql`
- [ ] `lib/vision/document.ts` — 2-pass extract
- [ ] `lib/vision/schemas/*.ts` — 8 doc-type schemas
- [ ] `lib/vision/validators.ts` — GSTIN, PAN, sums, dates
- [ ] `app/api/task-bot/vision/*/route.ts`

### Phase 10 (alerts + domain)
- [ ] `database/014_alerts.sql` + `016_progress_geo.sql` + `017_vendor_scores.sql`
- [ ] `lib/alerts/rules/*.ts` — 10 rule impls
- [ ] `lib/alerts/delivery.ts` — WhatsApp/push/email
- [ ] `lib/domain/{weather,geo,critical-path,vendor-score}.ts`
- [ ] Cron in `vercel.json` for nightly scans

---

## 7. Environment variables — final list

```
# Existing (Phase 0-1)
OPENROUTER_API_KEY
ANTHROPIC_API_KEY
GOOGLE_AI_API_KEY
TASK_AI_SUPABASE_URL
TASK_AI_SUPABASE_SERVICE_KEY
ONSITE_WHATSAPP_ACCESS_TOKEN
ONSITE_WHATSAPP_PHONE_ID
ONSITE_WHATSAPP_GRAPH_VERSION
ONSITE_WHATSAPP_WEBHOOK_VERIFY_TOKEN
ONSITE_WHATSAPP_APP_SECRET
WA_LINK_ENCRYPTION_KEY
INTERNAL_PUSH_SECRET
NEXT_PUBLIC_VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY
VAPID_SUBJECT
ONSITE_API_BASE

# New (Phase 2+)
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
SENTRY_DSN
SENTRY_AUTH_TOKEN
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
POSTHOG_KEY
POSTHOG_HOST
TENANT_DAILY_LLM_CAP_INR=500
TENANT_MONTHLY_LLM_CAP_INR=15000

# Phase 5
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
TAVILY_API_KEY
GROQ_API_KEY

# Phase 6 (voice)
OPENAI_API_KEY   # for realtime fallback + Whisper
ELEVENLABS_API_KEY

# Phase 10 (alerts + domain)
OPENWEATHER_API_KEY
RESEND_API_KEY

# Phase 11 (billing)
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
```

---

## 8. Tests — golden suite

- 52 SQL/tool-call golden tests (port from MSBC)
- 100 GST invoice samples for vision accuracy benchmark
- 50 voice transcription samples (Hindi/English/mix)
- 20 multi-modal RAG queries with expected source chunks
- 30 alert-rule trigger tests
- E2E test: full WhatsApp conversation flow from link to action

Run nightly via GitHub Actions or Modal scheduled job. Results tracked in Posthog.
