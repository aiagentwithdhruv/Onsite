# Onsite Task AI — Master Context

> **Auto-loaded by Claude Code.** Anything you need to know to work on this product is here or linked from here. Read this BEFORE writing any code.

---

## What This Is

**A natural-language AI chatbot embedded inside Onsite's construction management SaaS.**

End-user customers (builders, contractors, site engineers) type or speak in plain English/Hindi/Tamil, and the bot performs real Onsite operations — creating task dependencies, logging progress, managing project state — via Onsite's REST API.

**One-line value prop:** *"Stop clicking through 7 menus. Just tell Onsite what you want."*

**Who it serves:**
- **Primary:** Onsite's customers (construction company admins, project managers, site supervisors) — they use the bot
- **Secondary:** Onsite founders (Akshansh, Sumit) — they sell it as a product differentiator
- **Tertiary:** Dhruv's team (Angelina, Atlas, Pixel) — we build/maintain it

**Owner:** Dhruv Tomar (AI Builder at Onsite) | **Status:** MVP working, 2 API actions live in production | **Last updated:** 2026-05-17

---

## Current State (read [STATE.md](STATE.md) for full detail)

| Capability | Status | Notes |
|------------|--------|-------|
| Chat UI (text + voice) | ✅ Live | localhost:3001/task-bot |
| Bearer token auth (JWT) | ✅ Live | Auto-bridge via Chrome ext, manual paste fallback |
| 10 tools (deps + progress + list) | ✅ Live | create / update / delete dep, log / delete progress, list_companies / projects / tasks / subactivities / dependencies |
| Hierarchical task tree (1, 1.1, 1.2…) | ✅ Live | Server emits `outline` field, frontend renders as collapsible tree |
| Tasks show inline dep count + % done + duration | ✅ Live | list_tasks enriches each task; matches Onsite UI columns |
| Smart model routing (Haiku → Sonnet) | ✅ Live | Sonnet for action-verb + entity-name messages, Haiku for reads |
| Server cache (5-min TTL, per-user) | ✅ Live | list_companies / projects / tasks. Auto-invalidated on mutations |
| Always-on chat persistence | ✅ Live | `task_ai_messages` Supabase table, scoped by user_id |
| Chat history sidebar + rename | ✅ Live | 🕐 icon in header; pencil to rename; renamed title becomes bot's project anchor |
| Per-session project context anchor | ✅ Live | Chat title pinned into bot's system prompt as "current project" |
| **AI auto-suggests chat rename** | ✅ Live | Banner appears when project name is clear + title is null |
| **Cross-chat resume suggestions** | ✅ Live | Welcome screen shows recent chats; active chat shows keyword-matched past chats |
| **Visual stats card (`task_stats`)** | ✅ Live | 2x2 stat grid + progress bars for "how many" / "breakdown" questions |
| **Direct Anthropic API** | ✅ Live (gated) | Auto-enables when `ANTHROPIC_API_KEY` is set; OpenRouter fallback |
| **Leaf check in dep chain proposals** | ✅ Live | System prompt enforces is_leaf=true verification before chain proposal |
| **Training-data JSONL export** | ✅ Live | `/api/task-bot/export-training-data` + button on admin page |
| Thumbs feedback for training data | ✅ Live | 👍/👎 on each reply → `task_ai_messages.feedback` |
| Admin dashboard | ✅ Live | `/task-bot/admin` — 24h KPIs, per-tool, errors |
| Hindi voice input | ✅ Live | EN↔हिं toggle next to mic |
| Hallucination guard + force-recall | ✅ Live | Server detects "deleted!" without tool call, forces retry |
| Undo on dependency cards | ✅ Live | Routes to bot's delete_task_dependency |
| Multi-language replies | ✅ Live | Bot responds in user's language register |
| Deployed to Vercel | ❌ Local only | Push pending Dhruv's approval |

---

## Architecture Snapshot (read [HLD.md](HLD.md) for full detail)

```
Customer Browser
   │ types/speaks: "make Plastering wait for Brickwork"
   ▼
Onsite Task AI (Next.js page on Vercel)
   │ POST /api/task-bot { messages, token, baseUrl }
   ▼
API Route (stateless, no DB)
   │ ① Call Claude Sonnet 4.6 with tool definitions
   ▼                                              
Claude (via OpenRouter)
   │ Returns: tool_call { name, args }            
   ▼                                              
API Route
   │ ② Calls Onsite API with customer's Bearer token
   ▼
Onsite v3 API (api.onsiteteams.in)
   │ Returns success/error
   ▼
API Route
   │ ③ Calls Claude again with tool result for natural reply
   ▼
Customer Browser (final assistant message)
```

**Stateless by design** — no database in MVP. Each chat round-trip carries the customer's JWT, used per-request, never persisted on our side. This is the multi-tenancy story: one codebase, infinite customers, zero data leakage risk.

---

## Where the Code Lives

The product is a feature inside the existing `onsite-hub` Next.js app:

```
Onsite/onsite-hub/src/
├── app/
│   ├── task-bot/page.tsx          ← Chat UI (standalone, bypasses PIN auth)
│   └── api/task-bot/route.ts      ← Backend: Claude tool use + Onsite API proxy
└── components/
    └── AppShell.tsx                ← Modified: skips auth for /task-bot routes
```

## ⚠️ REPO SPLIT — commit to the right one (never mix)

| What you're committing | Goes to | URL |
|------------------------|---------|-----|
| Page UI changes (page.tsx) | **onsite-hub** repo | github.com/aiagentwithdhruv/onsite-hub |
| Backend route (route.ts, activity.ts) | **onsite-hub** repo | same |
| AppShell, Chrome ext page-side changes | **onsite-hub** repo | same |
| Env vars `.env.local` (NOT committed) | onsite-hub locally | — |
| Docs (this file, MEMORY, PRD, HLD, LLD, ROADMAP, ADRs) | **Onsite** repo, under `task-ai/` | github.com/aiagentwithdhruv/Onsite/tree/main/task-ai |
| Chrome extension files (manifest, content scripts, popup) | **Onsite** repo, under `task-ai/chrome-extension/` | same |
| DB migrations (`database/*.sql`) | **Onsite** repo, under `task-ai/database/` | same |
| Test reports + bug tracker | **Onsite** repo, under `task-ai/` | same |

**Both repos are PRIVATE.** Verify before any push: `gh repo view aiagentwithdhruv/<repo> --json visibility`.

When publishing a feature that touches both (e.g., code + docs), do TWO separate commits — one in each repo — with messages that cross-reference each other.

---

This product's docs live separately at:
```
Onsite/task-ai/
├── CLAUDE.md       ← THIS FILE
├── MEMORY.md       ← persistent learnings index
├── README.md       ← human overview
├── PRD.md          ← Product Requirements
├── HLD.md          ← High-Level Design (architecture)
├── LLD.md          ← Low-Level Design (data model, APIs, components)
├── ROADMAP.md      ← 5-phase plan from MVP → full product
├── STATE.md        ← living current-state log
├── API-SPECS.md    ← Onsite API endpoints we have/need
├── BUG-TRACKER.md  ← known issues
├── docs/
│   ├── data-model.md           ← BA → Sub-activity → Progress relationship
│   ├── multi-tenancy.md        ← How we scale to N customers
│   ├── competitive-analysis.md ← vs Onsite's existing bot + Procore + Powerplay
│   ├── decisions.md            ← ADRs (architectural decision records)
│   └── test-results.md         ← end-to-end test log
└── runbooks/
    └── (deploy.md, debug.md — TBD)
```

---

## Onsite Data Model (CRITICAL — read [docs/data-model.md](docs/data-model.md))

```
Company (Dhruv Construction)
  └─ Projects (Soul Space, HVAC Project, ...)
       └─ Workorders (one project may have multiple)
            └─ Billing Activities (BA = "tasks") — tree structure
                 ├─ Internal nodes (parent tasks, have children)
                 └─ Leaf nodes ← dependencies can ONLY link these
                       └─ Sub-Activities (sometimes labeled "Location 1", "Floor A")
                              └─ Progress Entries (diff_quantity + date + notes)
```

**Critical gotchas:**
- Dependencies link **two leaf BAs** in the **same workorder**. Cross-workorder = API error.
- Progress logs against a **sub-activity**, NOT a BA. New tasks have zero sub-activities until manually added.
- `location_id` field exists in the progress payload but appears unused in practice (real entries have empty string). Sub-activity name plays the location role.

---

## API Surface — Onsite endpoints

**Discovered + wired into the bot (no Akshansh needed):**
- `GET  /apis/v3/list/company`
- `GET  /apis/v3/list/project?company_id=…`
- `GET  /apis/v3/list/billingactivity?workorder_id=…` (list tasks)
- `GET  /apis/v3/list/billingsubactivity?billing_activity_id=…`
- `GET  /apis/v3/list/taskdependency?company_id=…` — response wrapper varies: `taskdependencies` | `task_dependencies` | `dependencies` | `data` — try all
- `GET  /apis/v3/detail/project/progressorder/<id>` — resolves project → workorder
- `GET  /apis/v3/detail/billingactivity/<id>`
- `POST /apis/v3/add/taskdependency`
- `POST /apis/v3/add/billingprogresshistory`
- `PATCH /apis/v3/edit/taskdependency`
- `DELETE /apis/v3/delete/taskdependency/<id>`
- `DELETE /apis/v3/delete/billingprogresshistory/<id>`

**Internal endpoints (our backend):**
- `POST /api/task-bot` — main chat (messages, token, baseUrl, session_title, model)
- `POST /api/task-bot/chat-log` — write a single turn to Supabase (always-on)
- `POST /api/task-bot/feedback` — 👍/👎 on an assistant message
- `POST /api/task-bot/sessions` — list / load / rename chat sessions
- `POST /api/task-bot/admin-stats` — 24h metrics for `/task-bot/admin`

---

## Auth Model (read [docs/multi-tenancy.md](docs/multi-tenancy.md))

**MVP:** Customer pastes Bearer JWT once per session. Stored in `sessionStorage` (clears on browser close). Token sent with each chat request, used by our API route to call Onsite. **Never persisted, never logged, never sent to LLM.**

**Production:** Embed inside Onsite's web app (`web.onsiteteams.com`) — bot auto-inherits the logged-in session. Customer never sees a token paste step.

**Key invariants:**
1. Token never leaves the request lifecycle.
2. LLM receives only the user's prose message + tool-call results (no JWT, no PII unless user types it).
3. Errors from Onsite API are surfaced to the user with the underlying message (helps debugging without leaking secrets).

---

## Working on This Product — Rules

1. **Read MEMORY.md before making changes.** It has the gotchas we've already paid for in time.
2. **Type everything (TypeScript strict).** No `any`. The chatbot's tool args go through `JSON.parse` — wrap that in a try/catch and validate.
3. **No state in MVP.** If you feel tempted to add a database, stop and re-read HLD.md § "Why stateless." Conversation history lives in the browser only.
4. **Test against the test API first** (`testapi.onsiteteams.in`) before prod (`api.onsiteteams.in`). The chatbot has env switch — use it.
5. **Don't break the PIN-auth bypass.** `AppShell.tsx` has `if (pathname.startsWith('/task-bot')) return <>{children}</>` — that line is load-bearing. Don't refactor it away.
6. **Token never touches the LLM payload.** Audit any new code path: does the JWT ever appear in `messages: [{role: ..., content: ...}]`? If yes, fix it before commit.
7. **Match Onsite's brand.** Background `#0f0a2e`, accent `#c73e5a`. Plus Jakarta Sans. Dark theme. Mobile-first.

---

## How to Run / Test (Quick Start)

```bash
cd "Onsite/onsite-hub"
npm install                         # only first time
npm run dev -- --port 3001
# Open http://localhost:3001/task-bot
```

**Manual test:**
1. Grab JWT from `web.onsiteteams.com` browser console:
   ```js
   copy(JSON.parse(localStorage.getItem('token')).token)
   ```
2. Paste into the bot → Production → Start Chat
3. Get 2 BA IDs from Network tab (click any task → grab UUID from `/detail/...` URL)
4. Send: `"Make <id1> depend on <id2>, finish to start, lag 0"`
5. Verify in Onsite UI — the FS arrow appears on the Gantt view

**Automated test:** See [docs/test-results.md](docs/test-results.md) for the curl-based smoke test.

---

## When You Get Stuck

| Symptom | Most likely cause | Where to look |
|---------|-------------------|---------------|
| 401 "token signature is invalid" | JWT was copy-pasted with OCR error (`l` vs `1` vs `I`) | Re-copy from localStorage via Console |
| 400 "only leaf node can be dependency" | One of the BAs has children | Pick different tasks |
| 400 "Primary and secondary must be in same workorder" | Cross-workorder link attempt | Pick tasks from same workorder |
| Progress not appearing | Wrong sub-activity ID, or task has no sub-activities | Check task's child sub-activities |
| Bot doesn't call tool, just chats | Claude needs more info — let the conversation continue | Be more explicit in user message |
| Tool fires but UI doesn't update | Onsite frontend cache; refresh the page | Hard-refresh in browser |

---

## Reference Material (Onsite-wide)

- **Onsite company context:** `Onsite/.claude/CLAUDE.md` (pricing, leadership, competitors, sales playbook)
- **Onsite Hub (sales tool):** `Onsite/onsite-hub/CLAUDE.md` (the PWA we live inside)
- **Onsite product KB:** `Onsite/uploads/onsite-platform-knowledge-base.md` (modules, fields, CSV formats)
- **Dhruv Rules (production):** `~/.claude/projects/.../memory/reference_dhruv_rules.md`

---

## Self-Update Rules

When you change something material on this product, also update:

| Change | Update |
|--------|--------|
| New tool added to the bot | API-SPECS.md (mark as ✅), STATE.md, MEMORY.md |
| New endpoint discovered | API-SPECS.md + this file's "API Surface" section |
| Data-model gotcha learned | MEMORY.md + docs/data-model.md |
| Architectural decision made | docs/decisions.md (ADR entry) |
| Production deploy | STATE.md "Deployed to Vercel" row |
| Bug fixed | BUG-TRACKER.md (mark resolved) |

**Never write code without updating at least STATE.md.** Future-you and future-agents need to know what changed and why.
