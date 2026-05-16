# High-Level Design — Onsite Task AI

**Owner:** Dhruv Tomar | **Status:** Draft v1.0 | **Last updated:** 2026-05-17

---

## 1. System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Customer's Device (Browser / Mobile WebView)                            │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Onsite Task AI — Next.js Page                                   │    │
│  │   /task-bot/page.tsx                                            │    │
│  │   - Chat UI (text + voice)                                      │    │
│  │   - sessionStorage: { token, env }                              │    │
│  │   - In-memory: messages[]                                       │    │
│  └─────────────────────┬──────────────────────────────────────────┘    │
│                        │ POST /api/task-bot                              │
│                        │ { messages, token, baseUrl }                    │
└────────────────────────┼────────────────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Vercel — Next.js API Routes (stateless)                                 │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ /api/task-bot/route.ts                                          │    │
│  │   1. Receive { messages, token, baseUrl }                       │    │
│  │   2. Call Claude with tools                                     │    │
│  │   3. If tool_call → call Onsite API w/ token                    │    │
│  │   4. Call Claude again w/ tool result for natural reply         │    │
│  │   5. Return { reply, tool_called, success }                     │    │
│  │   - Token: never logged, never stored, never sent to LLM        │    │
│  │   - No DB, no cache, no session state                           │    │
│  └─────────────────┬────────────────────────┬─────────────────────┘    │
└────────────────────┼────────────────────────┼──────────────────────────┘
                     │ Bearer JWT             │ Bearer OpenRouter key
                     ▼                        ▼
        ┌──────────────────────────┐  ┌────────────────────────┐
        │ Onsite API v3            │  │ OpenRouter             │
        │ api.onsiteteams.in       │  │ Claude Sonnet 4.6      │
        │                          │  │ (tool use enabled)     │
        │ Customer-scoped data     │  │ Stateless inference    │
        └──────────────────────────┘  └────────────────────────┘
```

---

## 2. Core Architectural Principles

### 2.1 Stateless by Design

**No database. No session store. No persistent logs of user content.**

Each chat round-trip is fully self-contained: the browser sends `{messages[], token, baseUrl}` and the server returns `{reply}`. The server keeps nothing between requests.

**Why:**
- **Multi-tenancy is free.** No shared tables means no risk of customer A seeing customer B's data via a missing `WHERE` clause.
- **Compliance is simpler.** GDPR/India DPDP-friendly because we don't store personal data.
- **Security blast radius is tiny.** A breach of our infrastructure leaks nothing — the data is all in the customer's browser + Onsite's DB.
- **Deployment is trivial.** Pure Next.js on Vercel. No Postgres, no Redis, no migrations.

**Tradeoff accepted:** Conversation history doesn't survive a browser refresh. Acceptable because:
1. Each task action is atomic ("create this dependency" doesn't need 5 prior messages of context)
2. Customers don't expect a 30-day chat history (they're trying to do work, not chat)
3. Power-user feature can be added later as opt-in per-customer encrypted storage

### 2.2 Token Travels with the Request, Not the Server

The customer's Bearer JWT is the only mechanism that scopes data access. It:
- Lives in the customer's browser `sessionStorage`
- Is sent with each `/api/task-bot` request
- Is used by our API route to call Onsite (with `Authorization: Bearer <jwt>` header)
- Is **never** logged, **never** stored, **never** included in LLM prompts

**Why:**
- The JWT already encodes the user's company_id and user_id (Onsite validates server-side)
- We don't need to know who the user is — Onsite does
- Token theft from our infrastructure = impossible (we don't have any)

### 2.3 LLM Has No Token Access

The LLM (Claude via OpenRouter) receives only:
- The system prompt (static, identical for every user)
- The conversation messages (text only, no JWT)
- Tool definitions (schemas, not data)
- Tool results (sanitized — successful API responses or error messages, never raw API responses that might leak other fields)

**Why:**
- LLM provider gets zero credential access
- LLM provider gets minimum customer content (only what the user typed)
- Prompt injection that asks the LLM to "print the auth token" returns nothing — it never had it

### 2.4 Customer Code Path = Customer Data Path

Every line of code processes exactly one customer's request at a time. No batching, no background jobs, no cross-customer state.

Compare to a SaaS where requests are queued and processed in batches — that creates opportunities for accidental cross-tenant data flow. We avoid all of it.

---

## 3. Multi-Tenancy Architecture

> **Question to anticipate from Sumit:** *"If I have 10,000 customers on Onsite, can one of them see another's tasks via your bot?"*
> **Answer:** No, structurally impossible. Here's why.

### 3.1 Tenancy Model

**Single-tenant per request, multi-tenant in aggregate.**

```
Customer A          Customer B          Customer C
   │                   │                   │
   │ JWT_A             │ JWT_B             │ JWT_C
   ▼                   ▼                   ▼
   POST /api/task-bot  POST /api/task-bot  POST /api/task-bot
   │                   │                   │
   ▼                   ▼                   ▼
   [Stateless handler] [Stateless handler] [Stateless handler]
   │                   │                   │
   │ Authorization:    │ Authorization:    │ Authorization:
   │ Bearer JWT_A      │ Bearer JWT_B      │ Bearer JWT_C
   ▼                   ▼                   ▼
   Onsite API          Onsite API          Onsite API
   (returns A's data)  (returns B's data)  (returns C's data)
```

Onsite's API enforces tenant isolation (based on `company_id` claim in JWT). Our service trusts that — we don't try to replicate the boundary. We just pass through.

### 3.2 What Could Break Isolation (and Why It Won't)

| Failure mode | Why it's structurally prevented |
|--------------|--------------------------------|
| Cache cross-pollination | No cache exists |
| Session mix-up | No sessions exist |
| Database query without `WHERE company_id` | No database exists |
| Log files contain customer data | Logs contain only timing + status codes, never request body |
| LLM context carries over | Each LLM call is fresh; no `kv-cache` shared |
| Token leak in error message | Errors from Onsite API are pre-sanitized before display |
| Worker process keeps last user's data | Vercel functions are isolated invocations |

### 3.3 What We Add When Stateful Features Land

Some Phase 3+ features require persistence (audit log, conversation history, preferences). When we add them:

**Required:**
- Postgres + Row-Level Security (RLS) policies based on `company_id`
- All queries `WHERE company_id = :auth.company_id` enforced at DB
- No service-role queries from the API routes (use anon key + JWT)
- Quarterly penetration test against tenant isolation
- Per-customer data export endpoint (DPDP compliance)
- Per-customer data deletion endpoint (right-to-be-forgotten)

**Forbidden:**
- Cross-customer aggregate queries from user-facing code paths (move to a separate analytics service with its own boundary)
- Caching customer data on the application server (use Postgres or Redis with explicit per-customer keys)

### 3.4 Scale Targets

| Metric | Target | Mechanism |
|--------|--------|-----------|
| Concurrent customers | 1,000 | Vercel auto-scales functions; no shared state to bottleneck |
| Daily chat messages | 100,000 | At ~$0.01/msg with Sonnet, ~$1,000/day at full load; switch to Haiku for routing → ~$200/day |
| P95 latency | < 3s | Sonnet typical = 1.5s, Onsite API = ~500ms |
| Customer data retention | 0 (MVP) | No storage = no retention question |

---

## 4. Component Breakdown

### 4.1 Frontend — `/task-bot/page.tsx`

**Responsibility:** UI rendering, voice/text input, conversation display, session token management.

**Tech:**
- Next.js 15 App Router (client component)
- React 19 + Tailwind CSS 4
- Web Speech API (native browser; no third-party dep)
- `sessionStorage` for token (cleared on browser close)

**State (in-memory only):**
```ts
{
  token: string         // from sessionStorage
  env: 'test' | 'prod'  // from sessionStorage
  authed: boolean
  msgs: Msg[]           // conversation history this session
  input: string
  loading: boolean
  listening: boolean    // voice input active
}
```

**No external libraries beyond what onsite-hub already uses.** This keeps the bundle small and avoids new attack surface.

### 4.2 Backend — `/api/task-bot/route.ts`

**Responsibility:** Stateless proxy between user, Claude, and Onsite API.

**Tech:**
- Next.js Route Handler (Edge runtime compatible, currently Node)
- No DB client, no Redis, no auth library — just `fetch`

**Request handling:**
1. Parse `{messages, token, baseUrl}` from JSON body
2. Validate `token` present + `baseUrl` is one of the known Onsite hosts
3. Build messages array: `[{role:'system', content: SYSTEM_PROMPT}, ...messages]`
4. POST to OpenRouter with `tools: [...]` and `tool_choice: 'auto'`
5. If response has `tool_calls`:
   - Parse args (JSON.parse with try/catch)
   - Dispatch on tool name → call appropriate Onsite endpoint
   - Build follow-up messages: `[...messages, assistant_with_tool_call, tool_result]`
   - POST to OpenRouter again for natural-language confirmation
6. Return `{reply, tool_called, success, tool_args?}`

**Error handling:**
- Onsite API errors → surfaced verbatim in tool result, Claude rephrases for the user
- LLM errors → fallback static message ("AI is busy, please try again")
- Network errors → fallback static message ("Couldn't reach Onsite servers")

### 4.3 LLM Layer — OpenRouter → Claude Sonnet 4.6

**Why this stack:**
- OpenRouter: single API key, multi-provider routing, OpenAI-compatible format
- Claude Sonnet 4.6: best tool use in the market as of 2026-05; handles Hindi-English code-switching natively
- OpenAI-compatible tools format: future-proof; can swap to GPT-4.x or Gemini without code rewrite

**Tool registry (Phase 1):**
```ts
[
  { name: 'create_task_dependency', schema: {...} },
  { name: 'record_task_progress',   schema: {...} },
]
```

Phase 2 adds 5–7 more (see [ROADMAP.md](ROADMAP.md)).

### 4.4 Onsite API Client (inlined in route handler)

Not a separate service — direct `fetch` calls. Each tool corresponds to one or more Onsite endpoints. The mapping is in [API-SPECS.md](API-SPECS.md).

---

## 5. Auth Flow

### 5.1 MVP Auth (current)

```
1. Customer opens https://task-ai.onsiteteams.com (Phase 3 URL; currently localhost)
2. Setup screen asks for Bearer token
3. Customer runs `copy(JSON.parse(localStorage.getItem('token')).token)` in Onsite tab
4. Pastes into setup form → selects Test/Prod → Start Chat
5. Token stored in browser sessionStorage
6. Every chat request sends { messages, token } to our API
7. API uses token in Authorization header when calling Onsite
8. Sign-out clears sessionStorage
```

### 5.2 Production Auth (Phase 3)

```
1. Customer is logged into web.onsiteteams.com
2. Clicks "AI Assistant" button in Onsite UI
3. Onsite frontend opens our bot in an iframe (or in-app overlay)
4. Onsite passes the JWT via postMessage to the iframe on load
5. iframe stores token in memory only (no storage)
6. Bot works exactly as MVP otherwise
```

**Why postMessage and not URL params:**
- URL params leak in browser history + analytics
- postMessage is origin-scoped; can verify it came from web.onsiteteams.com

### 5.3 Trust Boundary

```
Trusted:   Customer browser ↔ Onsite app (same origin trust)
Trusted:   Our API ↔ Onsite API (Bearer token validates per-request)
Untrusted: LLM provider — never sees credentials
Untrusted: Anything else
```

---

## 6. Cost Architecture

### 6.1 Per-message cost breakdown

| Component | Typical cost per message |
|-----------|-------------------------|
| Claude Sonnet 4.6 (first call, ~1K tokens in, 200 tokens out) | $0.006 |
| Claude Sonnet 4.6 (second call after tool, ~1.2K in, 100 out) | $0.005 |
| Onsite API call | $0 (Onsite is already paid for) |
| Vercel function invocation | ~$0.0001 |
| **Total** | **~$0.011 per chat round (with tool call)** |
| **Text-only reply (no tool)** | **~$0.006** |

### 6.2 Optimization plan (Phase 2-3)

- **Smart routing:** Use Haiku 4.5 for simple acknowledgements and clarification questions. Sonnet only for tool-call decisions and complex multi-step reasoning. Expected: 60% of calls move to Haiku → -50% cost.
- **Prompt caching:** OpenRouter supports prompt caching for Claude. The system prompt is identical for all users → cache it. Expected: -30% cost on system prompt tokens.
- **Per-customer rate limit:** 100 messages/customer/hour at MVP. Prevents runaway costs from a single misbehaving customer.

### 6.3 Cost target

At 10,000 monthly active customers × 30 messages each = 300,000 messages/month × $0.005 (post-optimization) = **$1,500/month** total LLM cost.

If Sumit charges ₹100/user/month for the AI feature and 20% of Onsite users adopt:
- Revenue: ~10K active users × ₹100 = ₹10L/month
- Cost: ~$1,500 = ₹1.25L/month
- Gross margin: ~87%

This is napkin math; refine in Phase 3 with real telemetry.

---

## 7. Deployment Topology

### 7.1 MVP (this week)

- One Vercel project: `onsite-hub` (already exists)
- Add `/task-bot` route + `/api/task-bot` route within it
- Single domain: `onsite-hub.vercel.app` (will alias to `task.onsiteteams.com` later)
- Env vars: `OPENROUTER_API_KEY` (already in onsite-hub's env)

### 7.2 Production (Phase 3)

- Same Vercel project, custom domain `task-ai.onsiteteams.com`
- CSP headers + frame-ancestors set to allow `web.onsiteteams.com` iframing
- Monitoring: Vercel Analytics + custom event log to Supabase (or Posthog) for action metrics
- Per-customer rate limiter (Upstash Redis)

### 7.3 Region

- Vercel deployment: **iad1 (US East)** by default; switch to **bom1 (Mumbai)** in Phase 3 for India-local latency (Onsite's customer base is 95% India)

---

## 8. Observability

### 8.1 MVP

- Vercel function logs (no PII, just timings and status codes)
- Browser console errors (developer use only)

### 8.2 Phase 2

- Structured logs of `{timestamp, customer_company_id (from JWT decode, no token logged), tool_name, success, latency_ms}` to a log sink (Vercel Logs → Logflare or Better Stack)
- Dashboard: messages/hour, tool-call success rate, p95 latency, top failure modes

### 8.3 Phase 3

- Per-customer dashboard (visible to Onsite admins): "your team's bot usage this month"
- Alerting: tool-call success rate < 90% over 5 min → PagerDuty Sumit/Dhruv

---

## 9. Disaster Recovery

Since we have no state, "DR" is trivial:
- Vercel down → bot is down. SLA risk acceptable for MVP. Phase 3: multi-region or fallback static page.
- LLM provider down → bot is down. Fallback: show a "submit a request" form that emails the task to Onsite support.
- Onsite API down → bot can't act. Fallback: bot tells user to retry; conversation history persists in browser so retry is one-click.

No backups needed (no data to back up).

---

## 10. Tech Debt Inventory (what we'd refactor with more time)

1. **No tool-call history in conversation** — Phase 2 should send the assistant's tool_call message back to Claude in next turn for true memory.
2. **Synchronous double-LLM-call pattern** — Could be streamed to user for perceived latency win.
3. **`AppShell.tsx` path-check is fragile** — should restructure into Next.js route groups.
4. **No tests** — Phase 2 must add at least integration tests against `testapi.onsiteteams.in`.
5. **Error messages are English-only currently** — Phase 2 i18n.

---

## 11. Open Architecture Questions

- Should we run our own LLM inference (self-hosted Llama) at scale for cost? — Decide at 10K+ customers.
- Should we add a non-LLM "command palette" mode for power users who want speed over conversation? — User research in Phase 2.
- Should the bot have memory across sessions (opt-in)? — Privacy review needed; defer to Phase 4.

---

## 12. References

- [LLD.md](LLD.md) — implementation details, data model, API contracts
- [docs/multi-tenancy.md](docs/multi-tenancy.md) — deeper dive on tenant isolation
- [docs/decisions.md](docs/decisions.md) — architectural decision records
- [ROADMAP.md](ROADMAP.md) — phase-by-phase delivery
