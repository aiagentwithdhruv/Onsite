# Angelina Dispatch — Onsite Task AI: 4 Add-Ons (RAG · Training · Support · Real-Time Voice)

> **From:** Dhruv Tomar
> **To:** Angelina (PM, Onsite Task AI)
> **Date:** 2026-05-19
> **Phase:** Add-on plan, sitting alongside the existing Phase 1 production-verified bot
> **Read first:** This file is self-contained. Don't ask Dhruv questions you can answer by reading the files listed in §2. Surface tradeoffs, make decisions, push back on weak parts of this plan.

---

## §0 — TL;DR (60 seconds)

Onsite's customers (construction company admins, project managers, site supervisors) currently use:
- **Notion** as their knowledge base (manual upload, generic Notion AI search)
- **The Task AI bot** you already shipped — types/speaks commands, performs 10 real Onsite operations

We are now adding **4 add-ons to the same bot**, replacing the Notion-as-KB workflow and turning the bot into Onsite's primary AI surface:

1. **RAG** — knowledge base over Onsite product docs, SOPs, BOQ formats, material library. Replaces Notion.
2. **AI Training / Onboarding** — guided voice/chat modules for new Onsite users (RA bills, BOQ, DPR, dependencies, attendance, etc.)
3. **Support / Escalation** — Tier 1 RAG answers, Tier 2 ticket creation, Tier 3 human escalation
4. **Real-Time Voice** — proper STT↔LLM↔TTS loop using Gemini 3.1 Flash Live (Hindi/Hinglish wins), GPT-4o-mini Realtime fallback

All 4 ship as extensions to the existing `/task-bot` page + `/api/task-bot` route. Stateless invariants preserved. Multi-tenancy preserved.

**Your job:** evaluate, accept/reject/modify, produce PRD-ADDON / HLD-ADDON / ROADMAP-ADDON, then dispatch implementation to Atlas/Pixel/QA. Push back where this plan is wrong.

---

## §1 — Mission

Decide what we build, what we don't, what we sequence first. Then dispatch.

Specifically:

1. Read everything in §2 first (you'll already know most of it).
2. For each of the 4 add-ons in §4, decide: SHIP / SHIP-LATER / SKIP, with reasoning.
3. For the 6 open questions in §5, write your decisions with one-line rationale each.
4. Produce 3 docs: `PRD-ADDON.md`, `HLD-ADDON.md`, `ROADMAP-ADDON.md` — extending existing equivalents.
5. Produce one decision doc: `DECISIONS-ADDON.md` covering §5 open questions.
6. Dispatch first sprint to Atlas + Pixel + QA via prompt files in `task-ai/` (do NOT spawn coding agents from your session — write the prompts as files Dhruv will paste into fresh sessions, per `feedback_never_spawn_coding_agent`).

---

## §2 — Required reading (in this order)

| # | File | Why |
|---|---|---|
| 1 | `Onsite/task-ai/CLAUDE.md` | Current master context — auto-loaded |
| 2 | `Onsite/task-ai/STATE.md` | What's live today (14 batches shipped) |
| 3 | `Onsite/task-ai/PRD.md` + `HLD.md` + `LLD.md` | Existing product foundation |
| 4 | `Onsite/task-ai/MEMORY.md` | Gotchas already paid for in time |
| 5 | `Onsite/task-ai/API-SPECS.md` | What Onsite endpoints we have + what's blocked on Akshansh |
| 6 | `Onsite/task-ai/docs/multi-tenancy.md` | Non-negotiable security invariants |
| 7 | `Onsite/.claude/CLAUDE.md` | Onsite company context — customer, pricing, competitors, sales playbook |
| 8 | `euron-references/MASTER-REFERENCE.md` | Pattern map of 6 reference codebases |
| 9 | `euron-references/REPORT-knowledgeforge.md` | RAG / chat / voice patterns to lift |
| 10 | `euron-references/REPORT-hireai.md` | GPT-4o Realtime + phase state machine (lift for Training) |
| 11 | `euron-references/REPORT-learnos.md` | SM-2 spaced repetition + mic-gate (lift for Training + Voice) |
| 12 | `euron-references/REPORT-shallow-scan.md` | MedAssist escalation pattern (lift for Support) |
| 13 | `euron-references/voice-models-comparison.pdf` | Gemini Live vs GPT-4o Realtime vs mini decision matrix |
| 14 | `~/.claude/projects/.../memory/voice_calling_working_config.md` | The QH working voice config (stable-v11.2) — direct precedent |
| 15 | `~/.claude/projects/.../memory/reference_dhruv_rules.md` | The 17 production rules every dispatch must honor |

**Total read time: ~90 minutes.** Do it before writing anything.

---

## §3 — Current Task AI state recap (you already know this; here for grounding)

**What's live (May 19, batch 14):**
- Chat UI + voice input (en-IN), text mode default, Hindi voice toggle
- 10 tools wired against Onsite v3 API: create/update/delete `task_dependency`, log/delete `task_progress`, list `companies / projects / tasks / subactivities / dependencies`, plus `get_project_stats`
- Smart model routing — Haiku 4.5 for reads, Sonnet 4.6 for action-verb messages, both via OpenRouter (Anthropic direct also supported when `ANTHROPIC_API_KEY` set)
- Hierarchical task tree rendering with collapsible nodes, dep counts, % done, duration markers
- 5-min server cache per-user, auto-invalidated on mutations
- Chat persistence in Supabase `task_ai_messages` (always-on, RLS-protected)
- Chat history sidebar with rename + delete + search
- Per-session project anchor → injected into bot's system prompt
- AI auto-suggests chat rename when project becomes clear
- Cross-chat resume suggestions (keyword match)
- `task_stats` visual card with 2x2 stat grid + progress bars
- 👍/👎 thumbs feedback → training data column
- Hallucination guard + force-recall (server detects "deleted!" without tool call)
- Undo button on dependency cards (routes back through `delete_task_dependency`)
- Multi-language replies in user's register
- Admin dashboard at `/task-bot/admin` — 24h KPIs, per-tool, errors, 30s refresh
- JSONL training-data export for future fine-tuning
- Desktop 3-column layout (sidebar + main + context rail) on `lg+`, mobile single-column

**What's NOT yet live (and these add-ons fill these gaps):**
- ❌ RAG over docs (Notion is current stopgap — vendor-locked, weak, no citations)
- ❌ Real-time voice loop (only voice INPUT today, no TTS, no streaming)
- ❌ Training / onboarding flow
- ❌ Support ticket / escalation flow
- ❌ Vercel deploy (still local-only; pending Dhruv's approval — separate decision from this dispatch)

**Stack constraints you must respect:**
- Next.js 15 App Router · React 19 · TypeScript strict
- Tailwind CSS 4 · Plus Jakarta Sans · dark theme `#0f0a2e` background, `#c73e5a` accent
- Backend: Next.js Route Handlers, stateless, no DB for the action route (chat logs OK via Supabase)
- LLM: Claude Sonnet 4.6 + Haiku 4.5 (OpenRouter primary, Anthropic direct as alt)
- Auth: Onsite Bearer JWT, per-request, never stored, never to LLM
- Repo split: code → `onsite-hub` repo · docs → `Onsite/task-ai/` in `Onsite` repo (CRITICAL — never mix commits)

---

## §4 — The 4 Add-Ons (full spec)

### ADD-ON 1 — RAG (Notion replacement)

**Goal:** Replace Onsite's current "upload to Notion + search there" workflow with a structured RAG knowledge base inside the same bot. Customer asks "how do I create RA bill" or "what's the BOQ format" → bot retrieves chunks + cites source + answers in user's language.

**Scope of corpus (initial):**

| Corpus | Source | Volume estimate |
|---|---|---|
| Onsite product knowledge base | `Onsite/uploads/onsite-platform-knowledge-base.md` | ~50 pages of structured notes |
| BOQ formats + fix guides | `Onsite/uploads/boq/` | ~10 documents |
| Material library specs | `Onsite/uploads/material-library/` | ~15 documents |
| Construction-market context | `Onsite/uploads/construction-market.md` | Reference |
| Competitor positioning | `Onsite/uploads/competitors.md` | Reference for sales-team queries |
| Existing Notion KB | Migrate via Notion API | Ask Onsite for export — likely 100-500 pages |

**Architecture:**

```
Customer types/speaks: "What's the process for RA bill submission?"
   │
   ▼
Claude reasoning step → decides this is a KNOWLEDGE query, not an ACTION
   │
   ▼
Calls new tool: search_knowledge_base(query="RA bill submission", top_k=5, lang="en")
   │
   ▼
Backend:
   1. Generate query embedding (Gemini Embedding 2 — handles EN+HI+TA natively)
   2. Hybrid retrieve: pgvector cosine top-20 + BM25 top-20 → merge → rerank → top 5
   3. Per-doc cap: max 2 chunks per source document
   4. Relevance gate: skip chunks with score < 0.6
   │
   ▼
Returns: { chunks: [{ text, source, page, score }], total_hits }
   │
   ▼
Claude generates citation-anchored reply: "RA bills are submitted via... [Source: BOQ-Format-Guide.pdf, p3]"
```

**Tech choices:**

| Layer | Decision | Why |
|---|---|---|
| Embeddings | Gemini Embedding 2 (Gemini API) | One model handles EN/HI/Hinglish/Tamil — matches Onsite's customer mix |
| Vector store | pgvector in **existing Onsite Supabase** (`jfuvhaampbngijfxgnnf`) | Already wired, RLS already in place, no new infra |
| Reranker | Cohere Rerank 3 OR Gemini reranker | Lift improvement on hybrid results |
| Chunking | 500 tokens with 50-token overlap, sentence-boundary scan in last 20% of chunk | Lifted from KnowledgeForge `document_service.py:40` |
| Ingestion | Multi-format extractor: PyPDF2, python-docx, openpyxl, python-pptx, raw text | KnowledgeForge pattern |
| Sanitizer | Strip `\x00`, `\x0b`, `\x0c` before insert | KnowledgeForge pattern (Postgres safety) |
| Background processing | `BackgroundTasks` (in-process) for MVP — flag risk: no retry on failure. Plan Celery/RQ for Phase B if volume warrants. | Lifted from KnowledgeForge, with the gotcha called out |
| Notion sync | Pull via Notion API every 6 hrs, diff against last sync, re-index changed pages only | New build; Notion API has stable cursor pagination |

**New tools added to bot's existing registry:**

```typescript
{
  name: "search_knowledge_base",
  description: "Search Onsite's internal knowledge base for product docs, processes, formats, and SOPs. Use this when the user asks a question that requires factual information (not an action).",
  parameters: {
    query: { type: "string", required: true },
    top_k: { type: "number", default: 5 },
    source_filter: { type: "string", required: false, enum: ["product_docs", "boq", "material", "all"] }
  }
}
```

**Bot decision logic (system prompt addendum):**
- Action verbs (create / log / delete / update / add / mark / record / set) → existing tools
- Question forms (how / what / when / where / why / which / can you explain) → `search_knowledge_base` first, then action tools if follow-up
- Bilingual: query embedding works regardless of input language; cite in user's language

**New DB tables (Alembic migration in `Onsite/task-ai/database/`):**

```sql
CREATE TABLE knowledge_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT NOT NULL,           -- "upload" | "notion_sync" | "url_import"
  source_id TEXT,                       -- Notion page ID or URL
  title TEXT NOT NULL,
  file_path TEXT,                       -- S3/Supabase storage path if uploaded
  category TEXT,                        -- "product_docs" | "boq" | "material" | ...
  language TEXT DEFAULT 'en',
  page_count INT,
  status TEXT DEFAULT 'processing',     -- processing | indexed | failed
  uploaded_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  indexed_at TIMESTAMPTZ
);

CREATE TABLE knowledge_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  token_count INT,
  embedding VECTOR(768),                -- Gemini Embedding 2 dim
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX knowledge_chunks_embedding_idx ON knowledge_chunks
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX knowledge_chunks_bm25_idx ON knowledge_chunks
  USING gin(to_tsvector('english', content));
```

**Admin UI additions:**
- `/task-bot/admin/knowledge` — upload docs, see indexing status, trigger re-index, view per-doc stats (queries, hit-rate)
- Drag-and-drop multi-file upload (PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, HTML, max 50MB/file)
- Notion sync button + last-sync timestamp

**Cost (Onsite tenant scale):**
- Embedding: Gemini Embedding 2 ≈ $0.025/M tokens. 500 documents @ 5K tokens avg = 2.5M tokens = $0.06 one-time + $0.001/query at runtime
- Vector storage: free in existing Supabase Pro tier
- Per-query: <$0.001 total
- Negligible — well within Phase-1 cost model

**Lift from:** `euron-references/knowledgeforge/backend/app/services/document_service.py` + `ai_service.py` (patterns only — KnowledgeForge license is proprietary, reimplement)

**Risks:**
1. **Onsite's Notion has 500+ pages.** Initial sync may take ~30 min and cost ~$5. One-time. Run off-peak.
2. **Gemini Embedding 2 768-dim vs OpenAI 1536-dim.** If you ever swap, full re-embed required. Document this irreversibility in `decisions.md` ADR.
3. **`BackgroundTasks` is in-process.** If the Next.js function dies mid-ingest, document gets stuck in `processing` status. Add a watchdog cron that retries documents in `processing` for >10 min.

---

### ADD-ON 2 — AI Training / Onboarding

**Goal:** Guide new Onsite users through their first 30 days with bite-sized voice/chat lessons. Reduce the support ticket volume Onsite already sees on basic features. Match the "50% faster onboarding via AI assistants" claim Onsite makes in sales pitches.

**Pedagogical model (lifted from HireAI phase machine):**

```
WELCOME → CHOOSE_MODULE → MODULE_INTRO → DEMO → QUIZ → RECAP → MARK_COMPLETE → NEXT_MODULE_PROMPT
```

**Initial module set (7 modules):**

| Module | What it teaches | Demo (calls existing tools) | Quiz format |
|---|---|---|---|
| 1. Task Dependencies | What FS/SS/FF/SF mean, when to use each | Create real test dependency in user's sandbox project | 3 questions |
| 2. Recording Progress | How to log daily progress, sub-activities, locations | Log a small progress entry | 3 questions |
| 3. RA Bills | What RA bills are, how to submit, milestones | RAG-explain (no action tool yet) | 3 questions |
| 4. BOQ Basics | BOQ structure, line items, quantity types | RAG-explain | 3 questions |
| 5. DPR (Daily Progress Report) | What DPR is, how it ties to progress entries | Show today's DPR summary via list_tasks + get_project_stats | 3 questions |
| 6. Attendance | How attendance flows, mobile capture, wage tracking | RAG-explain | 3 questions |
| 7. Materials & Procurement | RFQ → PO → receipt → inventory flow | RAG-explain | 3 questions |

Each module is ~5-8 minutes via voice. Voice-first by design (eyes-free on construction sites). Text fallback for noisy environments.

**Phase machine internals (lift HireAI `ai_interviewer.py:138-292`):**

- `InterviewStateMachine` → rename to `TrainingStateMachine`
- Phase enum: `WELCOME | CHOOSE_MODULE | INTRO | DEMO | QUIZ | RECAP | COMPLETE`
- Per-phase min turns: intro=2, demo=3, quiz=4, recap=2
- Phase advance trigger: turn count + LLM-judged completion (not just turn count alone)
- Hard guard: `if user_turns == 0 and ai_turns > 0: return False` (prevents AI advancing on echo — verbatim from HireAI)
- Per-phase system prompt swap via `session.update` (don't open new sessions — preserves Realtime context, saves cost)

**Spaced repetition (lift LearnOS `flashcards.py`):**

- After each module completion, auto-generate 5-7 flashcards via Claude
- Store in `task_ai_flashcards` table
- SM-2 algorithm: review on days 1, 3, 7, 14, 30+ based on user's quality rating (Again/Hard/Good/Easy → 0/3/4/5)
- Ease factor clamped at 1.3 (prevents "ease hell")
- Daily 60-second review push via bot welcome screen: "You have 4 cards due. 60 seconds. Want to review?"

**New DB tables:**

```sql
CREATE TABLE training_modules (
  id TEXT PRIMARY KEY,                  -- e.g. "task-dependencies"
  title TEXT NOT NULL,
  description TEXT,
  estimated_minutes INT,
  order_index INT,
  phases JSONB NOT NULL,                -- per-phase system prompt + min_turns
  active BOOLEAN DEFAULT true
);

CREATE TABLE training_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  module_id TEXT REFERENCES training_modules(id),
  current_phase TEXT NOT NULL DEFAULT 'WELCOME',
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  quiz_score INT,                       -- 0-100
  voice_minutes_used REAL DEFAULT 0,
  UNIQUE(user_id, module_id)
);

CREATE TABLE training_flashcards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  module_id TEXT REFERENCES training_modules(id),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  ease_factor REAL DEFAULT 2.5,
  interval_days INT DEFAULT 1,
  repetitions INT DEFAULT 0,
  total_lapses INT DEFAULT 0,
  next_review_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**New bot triggers:**
- Slash command `/train` or `/training` → enters training mode
- Natural language: "I want to learn RA bills" → bot suggests module 3
- Voice command: "Onsite, train me on dependencies" → starts module 1
- Welcome screen card: "📚 Daily review (4 cards due, 60 sec)" → review session

**Admin additions:**
- `/task-bot/admin/training` — completion funnel per module, quiz pass rate, voice-minute usage per user
- Module authoring UI (write phase prompts + quiz JSON) OR keep as code-only for MVP

**Cost ceiling:**
- Per module: ~6 min voice on Gemini Live ≈ $0.15
- 7 modules: ~$1.05/user lifetime
- Spaced review: ~30 sec/day × 90 days × $0.024/min Gemini ≈ $1.08/user lifetime
- **Total: ~$2.13/user lifetime** — negligible vs Onsite's $200/user/year revenue

**Lift from:** HireAI `ai_interviewer.py` (state machine + phase prompts) + LearnOS `flashcards.py` (SM-2)

**Risks:**
1. **Demo phase needs SAFE sandbox tasks.** Don't let training quizzes create real dependencies in production projects. Add `is_sandbox=true` filter to dependency-create tool when called from training mode.
2. **Voice quality on Hindi technical terms.** "Billing Activity," "Sub-Activity," "Workorder" are English-only. Gemini Live may pronounce them oddly. Test 7 module intros end-to-end before shipping any one module.
3. **Module content needs SME review.** Dhruv knows Onsite product but the 7 module prompts should be reviewed by Akshansh or Sumit before live rollout.

---

### ADD-ON 3 — Support / Escalation

**Goal:** Reduce ticket volume on Onsite's support team by auto-resolving ~70% of common questions, route the rest to humans with full context.

**3-tier flow:**

```
User: "Why is my dependency not saving?"
         │
         ▼
TIER 1: Bot tries RAG first
         │
         ├─ Found relevant chunks with high confidence → answer + cite
         │     └─ User clicks 👍 → resolved (logged as TIER_1_RESOLVED)
         │     └─ User clicks 👎 OR types "this didn't help" → escalate to TIER 2
         │
         └─ No relevant chunks OR low confidence → escalate to TIER 2
                  │
                  ▼
            TIER 2: Bot offers ticket creation
                  Bot: "I'll log this for support. What's the urgency — Critical / High / Normal / Low?"
                  │
                  ▼
            Calls create_support_ticket() → goes to Onsite's existing ticket system (or new queue if none)
                  │
                  ▼
            TIER 3 trigger (auto): if category=Critical AND no response in 5min → page on-call via Telegram
                                  if category=High AND no response in 15min → email ops
                                  if category=Normal AND no response in 1hr → batch digest to ops
```

**New tools added to bot's registry:**

```typescript
{
  name: "create_support_ticket",
  description: "Log a support ticket when the user has an issue the bot couldn't resolve. Confirm category and urgency before calling.",
  parameters: {
    category: { type: "string", enum: ["bug", "feature_request", "account_issue", "data_question", "general"] },
    urgency: { type: "string", enum: ["critical", "high", "normal", "low"] },
    description: { type: "string", required: true },
    related_project_id: { type: "string", required: false },
    related_task_id: { type: "string", required: false }
  }
}
```

**Escalation chain (lift MedAssist Celery Beat pattern, simplify since we don't need clinical SLAs):**

| Urgency | Auto-page after | Channel |
|---|---|---|
| Critical | 5 min | Telegram on-call group + SMS to ops lead |
| High | 15 min | Email ops@onsiteteams.com |
| Normal | 1 hr | Daily digest at 9 AM IST |
| Low | 24 hr | Weekly digest Monday 9 AM IST |

**Duplicate suppression:** Same `user_id + category + similar description` within 5 min → batch into single ticket. Prevents accidental triple-creation.

**Immutable audit log (MedAssist pattern):**

```sql
CREATE TABLE support_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  event_type TEXT NOT NULL,             -- tier_1_resolved | ticket_created | escalated | resolved
  ticket_id UUID,
  query_text TEXT,
  agent_response TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Prevent any DELETE on this table
CREATE RULE no_delete_audit AS ON DELETE TO support_audit_log DO INSTEAD NOTHING;

CREATE INDEX support_audit_user_idx ON support_audit_log(user_id, created_at DESC);
```

**Admin additions:**
- `/task-bot/admin/support` — ticket queue, escalation timers, per-category metrics, deflection rate (TIER_1_RESOLVED / total queries)
- Auto-resolution rate goal: ≥60% by week 4 of production

**Cost:** Negligible for the bot side (RAG is already free at this volume). Real cost is opportunity cost of NOT auto-resolving — directly saves Onsite support hours.

**Risks:**
1. **TIER 1 confidence threshold needs tuning.** Too aggressive → bot wrongly resolves real issues. Too conservative → high escalation, no time saved. Start at score≥0.7 for auto-answer, ship with admin override.
2. **Bot must NEVER auto-resolve account/billing/security issues.** Hard-route those to humans regardless of RAG match. Add a category whitelist for auto-resolve.
3. **Onsite's existing ticket system unknown.** Open question — see §5.

**Lift from:** MedAssist `@audit_phi_access` decorator pattern + Celery Beat escalation chain (simplified)

---

### ADD-ON 4 — Real-Time Voice

**Goal:** Proper voice loop. User speaks (any language), bot understands, calls tools, speaks back. Eyes-free, gloves-on usable.

**Stack decision (already locked, see `euron-references/voice-models-comparison.pdf`):**

| Mode | Model | When |
|---|---|---|
| Primary | **Gemini 3.1 Flash Live native audio** (`gemini-3.1-flash-live-preview`) | Hindi/Hinglish/Tamil or detected non-English |
| Fallback | **GPT-4o-mini Realtime** (`gpt-4o-mini-realtime-preview`) | English-only OR Gemini health-check fails |

**Why NOT full GPT-4o Realtime:** 3× cost vs mini, marginal quality gain for this use case. Reserve for HireAI-style scored interviews if we ever ship that.

**Pre-call routing logic:**

```typescript
async function selectVoiceProvider(userLocale: string, opts: { healthCheckTimeout: 200 }) {
  // 1. Language gate
  const isMultilingualNeed = ['hi', 'ta', 'pa', 'mr', 'gu', 'bn'].includes(userLocale);

  if (isMultilingualNeed) {
    // 2. Health-check Gemini
    const healthy = await pingGemini({ timeout: opts.healthCheckTimeout });
    if (healthy) return 'gemini';

    // 3. Fallback to mini + log alert
    log('gemini_fallback', { reason: 'health_check_failed' });
    return 'openai_mini';
  }

  // 4. English-only → straight to mini
  return 'openai_mini';
}
```

**Circuit breaker:** If Gemini error rate > 5% over 5 min sliding window → ALL traffic to mini until recovered. Manual override flag in admin panel.

**Audio pipeline (lifted verbatim from HireAI + LearnOS):**

```
Browser
  └── getUserMedia({ audio: true, sampleRate: 24000 hint, ignored by Chrome })
        └── AudioContext (runs at 48kHz, browser-mandated)
              └── AudioWorkletNode: pcm-processor.js (LIFT FROM HireAI)
                    └── Resample 48kHz → 24kHz inside the worklet (browser ignores sampleRate hint)
                          └── Base64 PCM16 chunks @ 100ms
                                └── WebSocket → /api/voice (new route)
                                      │
                                      ▼
                                FastAPI route forwards to:
                                  - Gemini Live WSS (existing 198dc29 bridge)
                                  - OR OpenAI Realtime WSS (existing stable-v11.2 path)
                                      │
                                      ▼
                                Model emits response.audio.delta (Gemini) OR response.output_audio.delta (OpenAI GA)
                                  ⚠️ HANDLE BOTH EVENT NAMES — single point of failure
                                      │
                                      ▼
                                WebSocket back to browser
                                      │
                                      ▼
                                Decode PCM16 → AudioBufferSourceNode
                                Schedule via scheduledTimeRef for GAPLESS playback (LIFT FROM LearnOS)
                                Mic-gate: if isAISpeakingRef.current === true, IGNORE incoming mic chunks (LIFT FROM LearnOS)
```

**Tool calling in voice loop:**

Both Gemini Live and OpenAI Realtime support function calling natively. The bot can:

1. User speaks: "Log 3 numbers progress on Electrical panel"
2. Model emits `tool_call` event with `record_task_progress(...)` args
3. Backend executes via existing route logic
4. Backend sends result back as `conversation.item.create` with role=tool
5. Backend sends `response.create` → model speaks confirmation: "Done — logged 3 numbers."

**ALL 10 existing tools + new RAG tool + new training/support tools wired into voice = single bot, voice or text, same capability.**

**Push-to-talk mode (construction site noise):**

- Toggle in chat header: 🎙️ Always-on VAD (default) ↔ 👆 Push-to-talk
- Push-to-talk: disable `turn_detection.server_vad`, send `input_audio_buffer.commit` manually on button release
- Lift pattern from HireAI gotcha #10 (Section 10 of `REPORT-hireai.md`)

**Wall-clock cap:** 30 min per call → auto-end with summary. Cost ceiling.

**Per-user quota:** Free tier 30 min/day voice. Paid Onsite users unlimited. Gate at WebSocket session start, count via Redis.

**New API routes:**
- `POST /api/voice/session` — issue ephemeral token (similar to LearnOS pattern)
- `WS /api/voice/stream/:session_id` — proxy WS between browser and Gemini/OpenAI
- `POST /api/voice/end` — explicit session close + final transcript flush

**New env vars:**
- `GOOGLE_AI_API_KEY` (already set on QH Vercel — replicate to onsite-hub Vercel)
- `OPENAI_API_KEY` (already exists for fallback)
- `VOICE_DAILY_FREE_MINUTES` (default 30)

**Hard gotchas to handle (lift from `REPORT-hireai.md` §10 + `REPORT-learnos.md`):**

1. ✅ Dual audio event names (`response.audio.delta` + `response.output_audio.delta`) — Dhruv's session_handoff_may10 confirms this was the ALL-DAY SILENT BOT BUG. Don't repeat.
2. ✅ Resample 48kHz → 24kHz in worklet (Chrome ignores sampleRate hint)
3. ✅ OpenAI Realtime temperature floor 0.6 (anything lower = API error)
4. ✅ AudioContext autoplay policy (must gate behind user click)
5. ✅ Mic-gate while AI speaks (prevents feedback)
6. ✅ Gapless PCM playback queue via `scheduledTimeRef`
7. ✅ WS `max_size=10MB` (default 1MB breaks on long audio bursts)
8. ✅ Phase-advance guard `if user_turns == 0: return False` — even for training mode

**Cost per 1-hour voice session:**

| Provider | User-heavy (70/30) | AI-heavy (30/70) |
|---|---|---|
| Gemini 3.1 Flash Live | ~$1.40 | ~$1.40 |
| GPT-4o-mini Realtime | ~$2.50 | ~$4.50 |

At Onsite's 10K customer scale × 5 min avg voice/day × 30 days = 1.5M voice minutes/month
- 80% Gemini = 1.2M min × $0.023 = **$27,600/month**
- 20% mini = 0.3M min × $0.04 = $12,000/month
- **Total: ~$40K/mo at full scale.** Need to validate with Onsite's gross margin model before promising "voice for all customers."

**Lift from:** HireAI `realtime_proxy.py` + `pcm-processor.js` + LearnOS `useVoiceChat.ts` mic-gate + gapless queue + existing QH `198dc29` Gemini bridge

**Risks:**
1. **Gemini Live is newer than OpenAI Realtime.** LearnOS started a Gemini migration that was never finished — that's a tell. Watch error rate first 2 weeks. Vishal should set up Sentry alert on Gemini WS connection failures.
2. **Two SDKs = 2 code paths to maintain.** When you add a new tool, ship it on ONE path first, then port. Otherwise maintenance doubles.
3. **Construction site noise.** Default VAD threshold 0.5 will fire constantly on machinery. Tune to 0.75-0.8 by default; expose push-to-talk for high-noise.
4. **PSTN out of scope for MVP.** Browser/mobile-app only. If Onsite wants outbound phone calls to vendors, that's a separate sprint with Twilio Media Streams bridge.

---

## §5 — Open decisions (you must answer these in `DECISIONS-ADDON.md`)

| # | Question | My lean (challenge it) | Why I'm uncertain |
|---|---|---|---|
| 1 | **All 4 add-ons inside `/task-bot`, or split into sibling routes?** | All in one bot UI, separate internal modules | One bot is simpler for users; multiple routes is cleaner for code ownership |
| 2 | **Notion sync: pull-replace OR pull-mirror (keep Notion as primary)?** | Pull-mirror initially, plan to retire Notion in 90 days | Customer change management — abrupt removal of Notion may break habits |
| 3 | **Support tickets: integrate with Onsite's existing system or build new queue?** | Ask Sumit/Akshansh what exists; default to new queue if no answer in 48h | Cannot decide without Onsite-side info |
| 4 | **API key budget: charge Onsite's account directly, or AIwithDhruv pays then bills?** | Onsite's account direct — they own the customer relationship | Billing complexity; depends on commercial model with Sumit |
| 5 | **Build owner: Shailendra solo (with Atlas/Pixel dispatched), or Afeefa+Shailendra pair?** | Shailendra leads with Atlas dispatches; Afeefa reviews architecture only (she's on XLwear lead) | Bandwidth — Afeefa is XLwear-anchored per memory |
| 6 | **Akshansh API blocker for Phase 2 (7 endpoints): ship without them, or wait?** | Ship Voice + RAG + Support without; Training Module 1+2 (dependencies + progress) can ship; modules 3-7 (RA bills, BOQ, DPR, attendance, materials) wait OR use RAG-only explain mode | Training depth depends on what API actions exist |

Decide each. If you disagree with my lean, write the counter-rationale.

---

## §6 — Sequencing recommendation

Build order I'd dispatch:

| Sprint | Days | Deliverable | Owner | Blockers |
|---|---|---|---|---|
| **0** (now) | Day 0-1 | You read all of §2, write PRD/HLD/ROADMAP/DECISIONS addon docs | You (Angelina) | None |
| **1** — RAG MVP | Day 2-5 | Multi-format ingest + pgvector + `search_knowledge_base` tool + admin upload UI | Shailendra | None |
| **2** — Voice loop deploy | Day 4-7 (overlap with sprint 1) | Deploy QH `198dc29` Gemini bridge to onsite-hub; wire all existing 10 tools | Shailendra | `GOOGLE_AI_API_KEY` on onsite-hub Vercel |
| **3** — RAG-in-voice | Day 6-8 | Voice path can call `search_knowledge_base`. Test in Hindi. | Shailendra | Sprint 1 + 2 |
| **4** — Notion migration | Day 7-10 | Pull Onsite's Notion KB into our store. Manual review of categorization. | Atlas/Pixel | Notion API access from Onsite |
| **5** — Support Tier 1+2 | Day 10-13 | `create_support_ticket` tool + audit log + admin queue page | Atlas | Decision #3 from §5 |
| **6** — Support Tier 3 escalation | Day 13-15 | Telegram/email pager + duplicate suppression + SLA timers | Atlas | Telegram bot + ops email |
| **7** — Training MVP (Modules 1+2) | Day 14-18 | Phase machine wrapper + Module 1 (Dependencies) + Module 2 (Progress) with quizzes | Pixel | Sprint 2 (voice) |
| **8** — Training Modules 3-7 | Day 18-22 | Remaining 5 modules — RAG-explain mode | Pixel | SME review (Sumit/Akshansh) |
| **9** — Spaced repetition (SM-2) | Day 22-25 | Auto-flashcard gen + daily review push | Pixel | Sprint 7 data |
| **10** — Hardening | Day 25-28 | Circuit breaker tuning, cost dashboards per add-on, load test, mobile responsive review | QA + Shailendra | All sprints |

**Total: ~4 weeks** to production-ready add-on stack. Each sprint is dispatchable in isolation. Sprints 1+2 can run parallel.

---

## §7 — Hard constraints (do NOT violate)

These are non-negotiable. If you find yourself wanting to break one, raise to Dhruv before writing the doc.

1. **Token never logged, never sent to LLM provider, never persisted server-side.** Per `multi-tenancy.md`. Audit every new code path.
2. **Stateless action route.** Chat logs and KB/training/support tables OK; bot's per-request logic stays stateless.
3. **Repo split rule.** Code in `onsite-hub`. Docs in `Onsite/task-ai/`. NEVER mix. Two commits, cross-reference SHAs.
4. **TypeScript strict.** No `any`. JSON.parse on tool args must be wrapped + validated.
5. **Test against `testapi.onsiteteams.in` first.** Then prod.
6. **Don't break the PIN-auth bypass.** `AppShell.tsx` `/task-bot` early return is load-bearing.
7. **Match Onsite's brand.** Background `#0f0a2e`, accent `#c73e5a`. Plus Jakarta Sans. Dark theme. Mobile-first.
8. **Minimal diffs.** Don't refactor adjacent code that isn't broken (Karpathy Rule #4).
9. **No half-finished implementations.** If you can't ship a sprint complete, narrow scope and ship the smaller thing complete (Karpathy + Dhruv's `feedback_finish_before_starting`).
10. **Never auto-deploy collaborator pushes.** Per `feedback_no_auto_deploy` — PR → Dhruv verifies → merge → deploy.
11. **Always-paid Supabase.** Per `feedback_supabase_paid_tier` — never free tier on Onsite production project.
12. **Never spawn coding agents from your session.** Per `feedback_never_spawn_coding_agent` — write prompt files for Dhruv to paste into fresh sessions.

---

## §8 — Resources you can lean on

| Resource | Path |
|---|---|
| 6 production AI codebases (study material) | `Aiwithdhruv/AI Development/Claude/euron-references/` |
| KnowledgeForge full code (RAG + voice + agents) | `euron-references/knowledgeforge/` |
| HireAI full code (GPT-4o Realtime + phase machine) | `euron-references/hireai/` |
| LearnOS full code (Gemini Live ref + SM-2 + mic-gate) | `euron-references/learnos-euron/` |
| MedAssist full code (HIPAA audit + escalation) | `euron-references/medassist/` |
| Detailed per-repo reports | `euron-references/REPORT-*.md` |
| Master pattern → product map | `euron-references/MASTER-REFERENCE.md` |
| Voice models 1-page PDF | `euron-references/voice-models-comparison.pdf` |
| Working Gemini Live bridge code (QH) | QH develop branch @ `198dc29` |
| Working OpenAI Realtime config | QH `stable-v11.2-voice-live` tag |
| Existing task-ai docs | `Onsite/task-ai/*.md` |

---

## §9 — Deliverables you produce

Write all 4 files in `Onsite/task-ai/`:

| File | Length | Contents |
|---|---|---|
| `PRD-ADDON.md` | ~2000 words | Personas, success metrics for each of 4 add-ons, scope boundaries, out-of-scope explicit |
| `HLD-ADDON.md` | ~3000 words | Architecture extensions per add-on, data flow diagrams, table schemas, new env vars, threat model deltas |
| `ROADMAP-ADDON.md` | ~1500 words | 10-sprint plan with daily granularity, gates, kill conditions, success KPIs per sprint |
| `DECISIONS-ADDON.md` | ~800 words | Your decisions on §5 open questions with one-line rationale each |

Plus 3 dispatch files (one per parallel-startable sprint):
- `dispatch-sprint-1-rag.md` — for Shailendra to paste into fresh session
- `dispatch-sprint-2-voice.md` — for Shailendra
- `dispatch-sprint-5-support.md` — for Atlas

After dispatch files written, hand back to Dhruv to paste-launch.

---

## §10 — Working style (mandatory)

1. **Make decisions, don't present menus.** "I'm doing X" not "here are 3 options." (Dhruv's `feedback_no_options`)
2. **Push back on weak parts of this plan.** If sequencing is wrong, say so with rationale. (Dhruv's `feedback_push_back`)
3. **Surface tradeoffs explicitly.** Speed vs quality, simplicity vs flexibility. (Karpathy Rule #3)
4. **Don't hide confusion.** If something in §4 doesn't add up, flag it. (Karpathy Rule #2)
5. **No half-finished sprints.** Narrow scope before shipping partial work. (Karpathy Rule + Dhruv's `feedback_finish_before_starting`)
6. **Minimal diffs in code.** Add-ons extend, don't refactor adjacent code. (Karpathy Rule #4)
7. **Update STATE.md after any material change.** (Existing rule in `CLAUDE.md`)

---

## §11 — Code-Copy Index (assemble, don't invent)

**Rule for the team:** for every new file we write, there should be 1-3 reference files to model after. If you find yourself inventing from scratch, you missed a reference. The matrix below covers every new file the 4 add-ons require.

> Notation: `📁 path/to/file` = lift verbatim · `🔧 path/to/file:L42-L88` = lift specific function · `📐 path/to/file` = pattern reference only (different domain, same shape)

### Existing Onsite Task AI artifacts to extend (NOT replace)

| Existing file | What you reuse |
|---|---|
| `Onsite/onsite-hub/src/app/api/task-bot/route.ts` (~250 lines) | The canonical action-route pattern. Every new tool extends this same route. Same Bearer-token plumbing. Same Claude tool-call loop. |
| `Onsite/onsite-hub/src/app/task-bot/page.tsx` (~380 lines) | The chat UI shell. Add new cards (RAG citation card, training quiz card, support ticket card) as new components, register in the same renderer. |
| `Onsite/onsite-hub/src/components/AppShell.tsx` | PIN-bypass for `/task-bot/*`. Extend bypass to `/task-bot/admin/*` already wired — same pattern if you add more sub-routes. |
| `Onsite/task-ai/database/` migrations | Existing schema for `task_ai_messages`, `task_ai_session_meta`. New tables (`knowledge_*`, `training_*`, `support_*`) follow the same Alembic numbering + RLS-by-user_id pattern. |
| `Onsite/task-ai/LLD.md` § Tool Registry | Existing 10 tools. New tools (`search_knowledge_base`, `create_support_ticket`, training-mode tools) follow the same JSON shape and registration spot. |
| `Onsite/task-ai/HLD.md` § Multi-Tenancy | Token invariants — every new code path inherits them. |

### Add-on 1: RAG — per-new-file reference matrix

| New file you'll write | Lift from |
|---|---|
| `onsite-hub/src/lib/rag/document_service.ts` | 📐 `euron-references/knowledgeforge/backend/app/services/document_service.py` — port from Python to TS, keep: chunking (500/50 tokens, sentence-boundary scan), null-byte sanitizer, dispatch by extension |
| `onsite-hub/src/lib/rag/embedding.ts` | 📐 `Aiwithdhruv/AI Development/Claude/MSBC-Group/AI-Production-Team/LEARNING-HUB/techniques/multimodal-rag-enterprise.md` (Dhruv's own Gemini Embedding 2 pattern) |
| `onsite-hub/src/lib/rag/hybrid_search.ts` | 🔧 `knowledgeforge/backend/app/services/ai_service.py:154` (ILIKE pattern — replace with pgvector cosine + BM25 merge; the stop-word filter + 2-chunks-per-doc cap + 30% match gate transfer verbatim) |
| `onsite-hub/src/app/api/knowledge/upload/route.ts` | 📐 `knowledgeforge/backend/app/routers/voice.py` (multipart upload + `BackgroundTasks` pattern in Next.js terms) |
| `onsite-hub/src/app/api/knowledge/search/route.ts` | New — model after existing `/api/task-bot/route.ts` validation + RLS check pattern |
| `onsite-hub/src/app/api/knowledge/notion-sync/route.ts` | New — `@notionhq/client` SDK; use `last_edited_time` filter for diff sync |
| Tool definition `search_knowledge_base` in route.ts | 📐 existing `list_tasks` / `get_project_stats` definitions in `route.ts` (same shape) |
| `onsite-hub/src/app/task-bot/admin/knowledge/page.tsx` | 📐 existing `/task-bot/admin/page.tsx` (same admin shell, swap inner table) |
| Alembic migration `005_knowledge_base.sql` | 📐 existing `004_session_meta.sql` (same Alembic header, same RLS pattern); SQL itself is in §4 Add-On 1 of this dispatch |
| Citation card component `KnowledgeCard.tsx` | 📐 existing `DependencyCard.tsx` / `ProgressCard.tsx` — same gradient-header pattern, Plus Jakarta Sans, `#c73e5a` accent |
| Onsite-specific corpus to ingest first | `Onsite/uploads/onsite-platform-knowledge-base.md` + `Onsite/uploads/boq/*.md` + `Onsite/uploads/material-library/*.md` + `Onsite/uploads/competitors.md` + `Onsite/uploads/construction-market.md` |

### Add-on 2: AI Training — per-new-file reference matrix

| New file you'll write | Lift from |
|---|---|
| `onsite-hub/src/lib/training/state_machine.ts` | 🔧 `euron-references/hireai/backend/app/services/ai_interviewer.py:138-292` — port `InterviewStateMachine` to TS, rename phases to WELCOME/CHOOSE_MODULE/INTRO/DEMO/QUIZ/RECAP/COMPLETE; KEEP the turn-count gating + the `if user_turns == 0: return False` echo guard at lines 235-237 |
| `onsite-hub/src/lib/training/system_preamble.ts` | 🔧 `hireai/backend/app/services/ai_interviewer.py:168-199` (`_session_preamble`) — adapt to construction training tone; keep the anti-hallucination + one-question-at-a-time discipline verbatim |
| `onsite-hub/src/lib/training/phase_prompts/*.ts` | 📐 `hireai/backend/app/services/ai_interviewer.py:39-135` (`PHASE_PROMPTS` dict) — same per-phase template structure, swap content for the 7 Onsite modules |
| `onsite-hub/src/lib/training/sm2.ts` | 📁 `euron-references/learnos-euron/backend/app/services/flashcards.py` — port verbatim to TS, ~120 lines; keep Anki→SM-2 mapping (Again/Hard/Good/Easy → 0/3/4/5), ease floor 1.3, XP per-quality (0/2/5/10) |
| `onsite-hub/src/lib/training/flashcard_generator.ts` | 📐 `learnos-euron/backend/app/services/flashcards.py` generate-from-content function — adapt to Claude Sonnet 4.6 call via existing OpenRouter client |
| `onsite-hub/src/app/api/training/start-module/route.ts` | New — model after existing `/api/task-bot/route.ts` (same auth + LLM call shape) |
| `onsite-hub/src/app/api/training/submit-quiz/route.ts` | New — calls state_machine.advance(), writes `training_progress`, returns next phase prompt |
| `onsite-hub/src/app/api/training/review-flashcards/route.ts` | New — reads `training_flashcards` where `next_review_date <= today`, calls sm2.ts on user response |
| Alembic migration `006_training.sql` | 📐 existing migrations + SQL in §4 Add-On 2 of this dispatch |
| Module content for 7 modules | Author yourself from `Onsite/uploads/onsite-platform-knowledge-base.md` + RAG corpus; SME-review with Akshansh/Sumit before live rollout |
| Quiz card component `QuizCard.tsx` | 📐 existing `task_stats` card (same 2x2 grid pattern) |
| Daily-review push UI on welcome screen | 📐 existing "Resume past chats" row on welcome screen — same component slot |

### Add-on 3: Support — per-new-file reference matrix

| New file you'll write | Lift from |
|---|---|
| `onsite-hub/src/lib/support/audit_log.ts` | 📐 `euron-references/medassist/` `@audit_phi_access` decorator pattern — port to TS; for Next.js use a wrapper function `withAudit(handler)` not a decorator; same immutable rule |
| `onsite-hub/src/lib/support/escalation.ts` | 📐 MedAssist Celery Beat 4-level chain — SIMPLIFY to 3 tiers per §4 Add-On 3 of this dispatch; use Vercel Cron (1-min granularity) instead of Celery |
| `onsite-hub/src/lib/support/duplicate_guard.ts` | New — fingerprint by `sha256(user_id + category + normalize(description))` with 5-min Redis TTL |
| `onsite-hub/src/app/api/support/create-ticket/route.ts` | New — model after `/api/task-bot/route.ts` validation pattern |
| `onsite-hub/src/app/api/support/escalate/route.ts` | New — Telegram bot send + Resend email; reuse existing Resend env if set |
| Tool definitions `create_support_ticket`, `escalate_to_human` | 📐 existing `create_task_dependency` tool definition shape |
| Alembic migration `007_support.sql` | 📐 existing migrations + SQL in §4 Add-On 3 of this dispatch (note the `CREATE RULE no_delete_audit` line — this is the immutability lock) |
| `/task-bot/admin/support/page.tsx` | 📐 existing `/task-bot/admin/page.tsx` |
| Telegram pager integration | Reuse existing Onsite Telegram bot if exists; otherwise new bot at `t.me/OnsiteSupportBot` — token via env |
| SLA timer cron | `vercel.json` cron config — 1-min ticks; reads tickets where `escalated_at IS NULL AND created_at + sla_window < now()` |

### Add-on 4: Real-Time Voice — per-new-file reference matrix

| New file you'll write | Lift from |
|---|---|
| `onsite-hub/src/app/api/voice/session/route.ts` | 🔧 `euron-references/learnos-euron/backend/app/routers/voice.py` ephemeral-token issuer pattern (port to TS) |
| `onsite-hub/src/app/api/voice/stream/[sessionId]/route.ts` (WS proxy) | 📁 `euron-references/hireai/backend/app/api/v1/endpoints/realtime_proxy.py` (full file, ~750 lines — port to Next.js Route Handler using `WebSocket` and `websockets` equivalent). KEEP: dual asyncio coroutines via `Promise.all`, dual event names (`response.audio.delta` + `response.output_audio.delta`), STT hallucination filter (lines 83-97), Redis session persistence (lines 267-280), max_size=10MB. |
| `onsite-hub/src/lib/voice/gemini_bridge.ts` | 📁 QH develop branch @ `198dc29` — copy your existing working Gemini Live bridge verbatim, then swap tool registry pointer to task-ai's |
| `onsite-hub/src/lib/voice/openai_bridge.ts` | 📁 QH `stable-v11.2-voice-live` tag — copy your existing OpenAI Realtime config verbatim |
| `onsite-hub/src/lib/voice/provider_router.ts` | New — implements language-detect + health-check + circuit-breaker per §4 Add-On 4 of this dispatch |
| `onsite-hub/src/lib/voice/circuit_breaker.ts` | New — sliding 5-min window error rate via Redis; >5% → all-to-mini flag |
| `onsite-hub/public/pcm-processor.js` | 📁 `euron-references/hireai/frontend/public/pcm-processor.js` — copy VERBATIM (zero changes needed) |
| `onsite-hub/src/hooks/useVoiceChat.ts` | 📁 `euron-references/learnos-euron/frontend/src/hooks/useVoiceChat.ts` — port mic-gate (lines 238-239) + gapless `scheduledTimeRef` queue (lines 142-144) + `onToolCall` callback pattern (line 66) |
| Voice UI component `VoiceButton.tsx` | 📐 existing voice-input toggle in `page.tsx` (extend with PTT mode toggle) |
| `onsite-hub/src/lib/voice/tool_router.ts` | New — receives `function_call` event from Gemini/OpenAI → dispatches to existing tool handlers in `/api/task-bot/route.ts` (single source of truth for tools) |
| Wall-clock 30-min cap | Server-side `setTimeout(closeSession, 30*60*1000)` per session |
| Per-user voice quota | Redis counter `voice_minutes:{user_id}:{date}` |

### Dhruv-side resources you can pull from without asking

| Resource | Path | When to use |
|---|---|---|
| AIwithDhruv 38-skill library | `Aiwithdhruv/AI Development/Claude/aiwithdhruv-skills/` | Reusable skills, especially: `multi-provider-router`, `audit-trail-decorator` (planned), `simple-rag-no-vector` (planned). Check what exists before building new patterns. |
| Dhruv's enterprise patterns hub | `MSBC-Group/AI-Production-Team/LEARNING-HUB/techniques/*.md` | 20 production patterns: `multimodal-rag-enterprise.md`, `guardrails-6-layer.md`, `mcp-a2a-agent-protocols.md`, `ai-architect-role.md`, etc. Read before building anything that overlaps. |
| The 17 Dhruv Rules | `~/.claude/projects/.../memory/reference_dhruv_rules.md` | Every dispatch you write to Atlas/Pixel must honor these |
| Dhruv's voice working config | `~/.claude/projects/.../memory/voice_calling_working_config.md` | The locked QH voice config — exact precedent for voice add-on |
| Master errors / mistake log | `/Aiwithdhruv/AI Development/Claude/ERRORS.md` | Check before debugging — Dhruv has paid for these in time |
| QuotaHit existing patterns | `Aiwithdhruv/AI Development/Claude/QuotaHit/` (and the 7-agent prompts in `agents/`) | Multi-agent orchestration patterns Dhruv has battle-tested |
| Existing Onsite product KB | `Onsite/uploads/onsite-platform-knowledge-base.md` | THE seed corpus for RAG add-on |
| Existing Onsite BOQ + material docs | `Onsite/uploads/boq/` + `Onsite/uploads/material-library/` | Additional RAG corpus |
| Existing skill: `create-rag-pipeline` | Skill in Setu-mode skills list — invoke if it fits, otherwise model after |
| Existing skill: `create-agent` | Same skills list — for the training-bot agent definition |
| Existing skill: `create-api` | For each new `/api/*` route |
| Existing skill: `create-migration` | For each Alembic migration |
| Existing skill: `create-test-suite` | For QA agent dispatch |
| Existing skill: `review-security` | For final pre-deploy audit on token-handling code |

### Cross-add-on shared code (write ONCE, reuse 4 times)

| Shared module | Add-ons using it |
|---|---|
| `onsite-hub/src/lib/llm/router.ts` (Claude/OpenAI/Gemini provider switch) | All 4 |
| `onsite-hub/src/lib/auth/token_validator.ts` (extend existing JWT plumbing) | All 4 |
| `onsite-hub/src/lib/audit/log_event.ts` (event-sourcing for compliance) | RAG + Training + Support |
| `onsite-hub/src/lib/rate_limit/per_user.ts` (Redis counter, sliding window) | All 4 |
| `onsite-hub/src/lib/cache/server_cache.ts` (already exists for list_*) — extend to KB + flashcards | RAG + Training |
| Component: `Citation.tsx`, `AudioWave.tsx`, `ProgressRing.tsx`, `QuizMC.tsx` | RAG + Voice + Training |

**Net effect of this index:** every new file in §6's 10-sprint plan has a concrete reference. Atlas/Pixel/QA, when dispatched, will paste from existing code rather than invent. Estimated time saving across the 4-week build: **~40% of engineering hours** (the "blank-page tax").

---

## §12 — When you're done

Reply to Dhruv with:
- Path to 4 docs you wrote (PRD-ADDON, HLD-ADDON, ROADMAP-ADDON, DECISIONS-ADDON)
- Path to 3 dispatch files (sprint-1-rag, sprint-2-voice, sprint-5-support)
- One paragraph: what surprised you in §2 reading, what you pushed back on in this plan, what you'd do differently
- One question if you have a real blocker (NOT a "should I do X?" — make those calls yourself)

Then standby. Dhruv reviews docs, approves or rewrites, then paste-launches dispatches.

---

**End of dispatch.** Read §2 in order, cross-reference §11 as you spec each new file, then start with `DECISIONS-ADDON.md` because the other 3 docs depend on your decisions.
