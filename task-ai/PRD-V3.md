# Product Requirements — Onsite Task AI v2

> **Status:** Final | **Date:** 2026-05-22 | **Supersedes:** `PRD.md` + `PRD-ADDON.md`
> **Companion docs:** [BRD-V3.md](./BRD-V3.md) · [ARCHITECTURE-V3.md](./ARCHITECTURE-V3.md) · [HLD-V3.md](./HLD-V3.md) · [LLD-V3.md](./LLD-V3.md)

---

## 1. One-line product

A natural-language AI assistant inside Onsite that lets any user — worker to founder — run every Onsite operation by talking (text/voice/photo/video) in English, Hindi, or mix, while feeling alive with memory, alerts, and proactive nudges.

## 2. Personas + access matrix

| Persona | Auth source | Tool catalogue available | Memory tier |
|---|---|---|---|
| **Worker** | Onsite JWT (role: `worker`) | read-only + `record_task_progress` (own tasks), `upload_photo`, voice notes | session + conversation only |
| **Site Engineer** | Onsite JWT (role: `site_engineer`) | + `create_task_dependency` (within assigned project), `list_*`, `analyze_document` | + persistent memory per project |
| **Project Manager** | Onsite JWT (role: `pm`) | + all create/update/delete on assigned projects, `get_project_stats`, `python_run` library | + cross-project pattern miner |
| **Admin / Owner** | Onsite JWT (role: `admin`) | + all tools, all projects, `vendor_performance`, `cost_overrun_alerts` | + portfolio-level KG (Phase 10) |
| **Vendor / Subcontractor** | Magic link (no Onsite acct) | Upload-only: `analyze_document` (invoices, DCs), submit progress | none (transactional) |

**RBAC enforcement:** every tool call is gated by `tenant_id + role + project_id` claim in JWT. Server-side filter.

---

## 3. Feature catalogue (organized by phase)

### Phase 0 — Demo polish (done by week 1)
- ✅ 14 production-tested Onsite v3 tools
- ✅ Hierarchical task tree rendering
- ✅ Stats card with Main/Sub/Leaf/With-Deps
- ✅ Hindi-mix system prompt
- ✅ PWA shell + service worker
- ✅ WhatsApp pipeline
- ✅ Hallucination guard + force-recall
- 🆕 Demo tenant with realistic seed data (avoids touching live customer data during demos)
- 🆕 Sentry + Langfuse instrumentation baseline

### Phase 1 — Memory layer (week 1-2)
- 🆕 Tier 1 session memory (in-process)
- 🆕 Tier 2 conversation memory (existing `task_ai_messages`)
- 🆕 Tier 3 persistent memory (new `memory_entries` table, pgvector, types: conversation/fact/preference/task/decision/client/project)
- 🆕 `save_memory(content, type, importance, tags, due_at?)` tool
- 🆕 `recall_memory(query, limit, type_filter?)` tool — hybrid BM25+dense
- 🆕 Long-term summary sync (nightly job)
- **Acceptance:** "Remember my project Arohan" works across sessions, weeks later

### Phase 2 — 2-tier LLM routing + cost guardrails (week 2-3)
- 🆕 `pickModel(query)` complexity classifier (action verbs → Sonnet, else Haiku/Gemini Flash)
- 🆕 Gemini Flash for 70% of queries (default)
- 🆕 Claude Haiku/Sonnet for action + complex (30%)
- 🆕 OpenRouter fallback when direct provider returns 5xx/429
- 🆕 Semantic cache (cosine >0.95 reuse) + exact cache in Upstash Redis
- 🆕 Per-tenant daily + monthly LLM spend cap with friendly cutoff
- 🆕 Rate limits per user (100 req/min) + per tenant (10K req/day)
- 🆕 Circuit breakers on external APIs
- **Acceptance:** Cost per query ≤ ₹0.10 measured over 10K queries

### Phase 3 — Heartbeat / alive (week 3)
- 🆕 Hourly Vercel Cron scans Tier 3 memory for `due_at` ≤ now
- 🆕 Reminder surface: next user open shows "Yesterday you mentioned X — finished?"
- 🆕 Pattern miner: detects recurring user behavior, pre-fetches context
- 🆕 Memory decay: low-importance + >90 days → archived
- **Acceptance:** Bot proactively surfaces ≥1 useful reminder/user/week

### Phase 4 — Python action runner (week 3-4)
- 🆕 Sandboxed `python3` subprocess (30s timeout, 512MB RAM, no network unless whitelisted)
- 🆕 Curated script library (`python-scripts/`) — start with 8:
  1. `export_progress_csv(project_id)`
  2. `compute_velocity(project_id, days)`
  3. `find_blocked_chain(task_id, depth)`
  4. `bulk_import_boq(xlsx_path)`
  5. `generate_site_report_pdf(project_id, date_range)`
  6. `vendor_performance_score(vendor_id)`
  7. `critical_path_recompute(project_id)`
  8. `material_consumption_summary(project_id, date_range)`
- 🆕 `python_run(script_id, args_json)` tool
- **Acceptance:** Complex multi-step queries 10× faster + cheaper than pure-LLM equivalent

### Phase 5 — RAG (multimodal) (week 4-5)
- 🆕 Lift Multimodal-RAG-System wholesale (Modal Python microservice OR TS port)
- 🆕 Document ingestion endpoint (`/api/task-bot/rag/ingest`) — accepts PDF, image, audio, video, text
- 🆕 5 processors: text, PDF, image (vision describe), audio (Whisper), video (frame extract + vision)
- 🆕 Gemini Embedding 2 (1536-dim Matryoshka, multimodal)
- 🆕 Hybrid search: pgvector dense + Postgres tsvector BM25 + Reciprocal Rank Fusion
- 🆕 Tavily web fallback when KB retrieval scores low
- 🆕 `rag_search(query, top_k, filters)` tool
- 🆕 Citations + source highlights in UI
- **Acceptance:** RAGAS retrieval precision ≥ 0.85, latency ≤ 2s P50

### Phase 5.5 — Vision + Document AI (week 5-6)
- 🆕 2-pass extraction: Gemini 3.1 Flash → Gemini 3.1 Pro on validator failures
- 🆕 Field validators per doc type (GSTIN, PAN, sum-of-items, date sanity)
- 🆕 8 doc-type schemas: GST Invoice, Delivery Challan, Purchase Order, Petty Cash, Labor Slip, BOQ Screenshot, Site Photo, Generic Screenshot
- 🆕 Image preprocessing (auto-rotate, deskew, denoise) via Pillow
- 🆕 `analyze_document(file_url, doc_type?)` tool
- 🆕 `analyze_image(file_url, question)` tool — free-form vision Q&A
- 🆕 `validate_document(json, doc_type)` tool
- 🆕 `link_document_to_task(doc_id, task_id)` tool
- 🆕 Documents table with auto-corrected/needs-review flags
- 🆕 Human review queue in admin UI (Phase 7)
- **Acceptance:** 99.5% accuracy on standard GST invoice + DC formats; <2% needs-review rate

### Phase 6 — Voice realtime (week 6-7)
- 🆕 **Browser realtime (PWA)**: Gemini 3.1 Flash native audio (default) via WSS proxy. Fallback OpenAI gpt-4o-mini-realtime.
  - Audio: PCM16 24kHz, base64-in-JSON
  - Tool dispatch via `function_call` flows back to same LangGraph agent
- 🆕 **Phone realtime (Twilio bridge, later)**: OpenAI gpt-4o-mini-realtime (QH stable-v11.2 config locked)
  - Audio: mulaw 8kHz / 640-byte chunks / 0.07s sleep
  - **Event names: `response.output_audio.delta`** (NOT beta names — QH bug)
- 🆕 **Async voice notes (WhatsApp)**: Groq Whisper transcribe → bot brain → reply (already wired)
- 🆕 TTS for non-realtime: ElevenLabs Rachel + Edge TTS fallback
- 🆕 EN ↔ हिं language toggle per user preference
- **Acceptance:** Voice latency ≤ 800ms P50, language detection works first-message

### Phase 7 — Training + labeling UI (week 7-8)
- 🆕 Admin route `/task-bot/admin/labels` (Supabase magic-link auth)
- 🆕 Spreadsheet review of flagged messages
- 🆕 Inline RAG hits inspection (which chunks retrieved + their scores)
- 🆕 Document needs-review queue (one-click approve/correct)
- 🆕 One-click "good"/"needs work" with optional rewrite
- 🆕 JSONL export for fine-tuning / eval seed
- 🆕 RAGAS dashboard (retrieval precision/recall trends week-over-week)
- 🆕 A/B test flags (Posthog) for prompt variants
- **Acceptance:** 200 labeled examples produced in first 2 weeks; eval suite running nightly

### Phase 8 — Support escalation (week 8)
- 🆕 Phase state machine (lifted from hireai): `TRIAGE → INVESTIGATE → RESOLVE → CONFIRM`
- 🆕 `create_support_ticket(category, severity, description)` tool
- 🆕 Escalation routing: Tier 1 = AI auto-resolve; Tier 2 = human support; Tier 3 = Onsite engineering
- 🆕 SLA tracking + auto-escalate on stale
- 🆕 Pattern miner: identifies recurring issues for product backlog
- **Acceptance:** 70% of support tickets resolved by AI Tier 1 without human

### Phase 9 — Mobile (Capacitor wrap) (week 9)
- 🆕 Capacitor 6 wrap of existing PWA → iOS + Android App Store / Play Store binaries
- 🆕 Native push notifications (replaces web push on mobile)
- 🆕 Native camera + photo gallery integration for document upload
- 🆕 Offline queue (IndexedDB) → sync when online
- **Acceptance:** App Store + Play Store live, < 2 min to install

### Phase 10 — Alerts + Notifications + Domain features (week 10+)

#### 🆕 Alerts subsystem (the "smart" alerts)

10 alert rules ported from Onsite Sales Intelligence System pattern, adapted for construction:

| # | Rule | Trigger | Delivery |
|---|---|---|---|
| 1 | **Stale task** | No progress in >7 days on in-progress task | WhatsApp + push |
| 2 | **Critical path slip** | Dependency dates push project beyond deadline | WhatsApp + email to PM |
| 3 | **Cost overrun** | Task actuals > 110% of estimated | Dashboard alert |
| 4 | **Material shortage forecast** | Consumption rate × days remaining > inventory | WhatsApp to PM + email to vendor |
| 5 | **Vendor late delivery** | DC date > expected by >2 days, 2+ times | Admin dashboard |
| 6 | **Weather risk** ⚡ | Concrete pour scheduled in next 24h + rain forecast > 50% | WhatsApp to PM the day before |
| 7 | **Compliance deadline** | RERA milestone or GST filing < 7 days away | Push + email |
| 8 | **Geo-mismatch** | Worker logs progress with geo-tag > 500m from site | Push to PM (verification check) |
| 9 | **Inactive site** | No activity logs >3 days on active project | Push to PM |
| 10 | **Safety incident** | Photo classified as safety issue OR keyword detected | Immediate WhatsApp + email |

**Implementation:** scheduled Modal jobs scan DB nightly + on-event triggers; deliver via WhatsApp template / push / email per user preference.

#### 🆕 Geo-tagged actions
- Every `record_task_progress` captures `lat/lon` from PWA geolocation (if granted)
- Stored in `progress_geo` table
- Used by Rule #8 (geo-mismatch) + analytics
- Site location set per project; alert if worker > 500m off-site

#### 🆕 Photo geo + EXIF validation
- Uploaded photos extract EXIF lat/lon (if present)
- Compare to project site location → flag if mismatch
- AI-classified work_type from photo content (lifts vision pipeline)

#### 🆕 Weather-aware scheduling
- OpenWeatherMap API integration (free tier covers 1M calls/mo)
- Per-project location → daily forecast
- Rule #6 triggers on rain risk
- Calendar-aware: "you scheduled concrete pour on Mar 15, 60% rain forecast — push to Mar 17?"

#### 🆕 Material auto-deduct
- On `record_task_progress` → look up BOQ line item → deduct theoretical consumption from inventory
- Bot announces deductions on chat: "Logged 5 sqm. Auto-deducted 50kg cement + 8 bags sand from inventory."
- Reconcile with actual delivery slips (DCs)

#### 🆕 Vendor performance scoring
- Daily Modal job computes per vendor:
  - On-time delivery rate (DC date vs expected)
  - Quantity accuracy (DC qty vs PO qty)
  - Invoice cleanness (% needs-review)
- Surfaced as score 0-100 in vendor profile + ranks in `vendor_performance` admin tool

#### 🆕 Critical path recompute
- On any `create_task_dependency` or duration change → Python runner recomputes CPM
- Highlights critical path tasks in red in task tree
- Alerts PM if new critical path is longer than committed timeline

#### 🆕 RERA / GST compliance reminders
- Per project: RERA milestone schedule (% built dates)
- Per tenant: GST filing schedule (GSTR-1, GSTR-3B)
- Auto-reminders 7 days + 1 day before each deadline

#### 🆕 Safety incident classifier
- Site photos auto-classified for safety risks (missing helmet, scaffolding issue, electrical exposure)
- Threshold = HIGH severity → immediate WhatsApp + email
- Manual override + false-positive feedback feeds training loop

#### 🆕 Webhooks for events
- Outbound webhooks subsystem
- Per-tenant webhook URL config
- Events: task.created, progress.recorded, dependency.created, document.uploaded, alert.fired
- Retry queue with exponential backoff, max 3 attempts then dead-letter

#### 🆕 Scheduled reports
- Monday 8am: weekly project status email/WhatsApp to PMs
- Daily 6pm: today's accomplishments summary
- Monthly 1st: contractor admin sees portfolio health PDF

#### 🆕 Calendar integration (Google Calendar + Outlook)
- Voice-created tasks added to calendar
- Calendar-aware scheduling for site visits

### Phase 11 — Multi-tenant maturity (post-MVP)
- 🆕 Per-tenant custom system prompt overlay
- 🆕 Per-tenant tone config (formal/casual/Hindi-first)
- 🆕 Sandbox per tenant (test before promoting to prod)
- 🆕 Data export endpoint (DPDP compliance)
- 🆕 Backup/DR drills quarterly

### Phase 12 — Knowledge graph (deferred until pattern miner shows value)
- 🆕 Entity-relationship store (`kg_entities` + `kg_edges`)
- 🆕 Triple extraction from chat memory + RAG corpus
- 🆕 Graph traversal queries for "what blocks what"

---

## 4. Out-of-scope (decisions documented)

| Feature | Decision | Reason |
|---|---|---|
| Self-host Ollama (Tier 3) | Defer | Decision #2 — public APIs only for now |
| Stripe billing | Defer | Decision #6 — Razorpay later when monetization proven |
| Knowledge graph | Phase 12 | Decision #3 — only if pattern miner shows it's needed |
| Multi-region | Phase 11+ | <10% users outside India today |
| FastAPI migration | Phase 11+ | Decision #1 — Next.js sufficient until 50K DAU |
| Custom drawings parser | Future | Specialized; phase after BOQ ingestion proves |
| Telegram/Discord channels | Future | WhatsApp + PWA covers 95% |
| AI agent multi-persona | Future | One persona "Angelina-style" sufficient for v1 |

---

## 5. Acceptance criteria summary (Definition of Done per phase)

| Phase | Key acceptance |
|---|---|
| 0 | Demo runs end-to-end on tunnel, Akshansh + Sumit sign-off |
| 1 | Memory recall works week-over-week, ≥80% relevance on test set |
| 2 | Cost ≤ ₹0.10/query verified over 10K queries |
| 3 | Heartbeat surfaces ≥1 useful reminder/user/week |
| 4 | Python scripts return 10× faster than LLM equivalent on 5 benchmark tasks |
| 5 | RAGAS retrieval precision ≥ 0.85, multimodal ingest works for all 5 modalities |
| 5.5 | 99.5% accuracy on 100 sample GST invoices + DCs |
| 6 | Voice latency ≤ 800ms P50, language switching works |
| 7 | 200 labeled examples in 2 weeks, eval running nightly |
| 8 | 70% support tickets resolved by AI Tier 1 |
| 9 | App Store + Play Store live, offline queue works |
| 10 | All 10 alert rules firing correctly in test tenant |

---

## 6. Open questions for Akshansh + Sumit

1. **OpenWeatherMap API key — Onsite-owned or our cost?** Suggest Onsite-owned (their cost, our integration).
2. **Photo storage budget — Supabase Storage at ₹0.021/GB-month** — at 1 lakh users × 50 photos × 5MB each = 25TB → ₹52K/month. Acceptable?
3. **WhatsApp template approval — who owns Meta dashboard for templates?** Need template registry for proactive messages.
4. **GST filing automation — auto-generate GSTR-1?** Big value-add, but compliance liability — defer or build?
5. **Vendor portal — separate URL or under main Onsite?** Affects auth flow.
6. **Pricing rollout — when to switch from free to paid for existing customers?** Need grace period strategy.
