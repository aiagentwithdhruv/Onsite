# Architectural Decision Records (ADRs)

> Every meaningful architectural decision, with rationale and tradeoffs. Add a new ADR every time you make a call you'll regret if you forget the reasoning.

Format: `## ADR-NNN — Title (YYYY-MM-DD)` then **Context · Decision · Consequences · Alternatives considered**

---

## ADR-001 — Stateless backend (no database in MVP) (2026-05-17)

**Context:** A chatbot naturally suggests "save conversation history." But that immediately introduces tenant isolation concerns, GDPR/DPDP scope, infrastructure cost, and complexity.

**Decision:** MVP has zero server-side state. No database, no Redis, no logs of message content. Each request is self-contained `{messages, token, baseUrl}`. Browser holds conversation in memory; sessionStorage for token.

**Consequences:**
- ✅ Multi-tenancy is structural (can't leak what we don't store)
- ✅ Trivial deploy (Vercel functions, no infra)
- ✅ No compliance review needed for MVP
- ✅ Cost is minimal (no DB hosting)
- ❌ Conversation history lost on browser refresh (acceptable: tasks are atomic)
- ❌ No audit log for admins (Phase 3 will add)
- ❌ Can't power personalization features (Phase 4+)

**Alternatives considered:**
- Supabase + RLS from day 1 — rejected: premature, adds days of work for no MVP benefit
- localStorage instead of sessionStorage for token — rejected: token persistence across browser closes is a security risk

---

## ADR-002 — Tool use via OpenRouter, not Anthropic SDK direct (2026-05-17)

**Context:** Need to call Claude with tool use. Anthropic has its own SDK with native tool format; OpenRouter offers OpenAI-compatible format that also supports Claude tool use.

**Decision:** Use OpenRouter with OpenAI-compatible API. Model: `anthropic/claude-sonnet-4-6`.

**Consequences:**
- ✅ Reuses existing `OPENROUTER_API_KEY` in onsite-hub env
- ✅ Same code pattern works for swapping in GPT-4 / Gemini / Llama later
- ✅ One unified billing across models
- ❌ Slight indirection (one extra hop); minor latency cost
- ❌ Tool format is OpenAI-shaped, not Anthropic-native; minor mental model mismatch

**Alternatives considered:**
- Anthropic SDK direct — rejected: requires new API key, second billing relationship, more code paths
- Run our own inference (Llama 3.x) — rejected: way too early; revisit at 10K+ customers

---

## ADR-003 — Live inside `onsite-hub` Next.js app, not separate package (2026-05-17)

**Context:** Where does the task-bot code live? Options: new repo, new Next.js project, or feature in existing `onsite-hub`.

**Decision:** Feature inside `onsite-hub/src/app/task-bot/`. Bypass PIN auth via pathname check in `AppShell.tsx`.

**Consequences:**
- ✅ Single Vercel deploy
- ✅ Shared env vars, shared design tokens (Tailwind config, brand colors)
- ✅ No new GitHub repo to manage
- ❌ Tight coupling: if onsite-hub needs major refactor, task-bot is along for the ride
- ❌ AppShell bypass is a path-check, slightly fragile
- ❌ Mixing internal-only routes with customer-facing routes in same app

**Alternatives considered:**
- New Next.js project `task-ai/` — rejected: extra deploy, extra repo, no clear benefit for MVP
- Standalone HTML + Python backend — rejected: doesn't reuse existing infra

**Reconsider when:** task-bot grows beyond ~10 tools or needs different scaling characteristics from sales hub.

---

## ADR-004 — sessionStorage for token, NOT localStorage (2026-05-17)

**Context:** Where to store the customer's Bearer JWT in the browser? Options: localStorage (persistent), sessionStorage (per-tab), cookie (HTTP-only), in-memory only.

**Decision:** sessionStorage.

**Consequences:**
- ✅ Survives page reloads within a tab session
- ✅ Auto-clears on tab close (limits exposure)
- ✅ Same-origin only
- ❌ User must re-paste token if they close + reopen tab
- ❌ Still XSS-vulnerable (would be same with localStorage)

**Alternatives considered:**
- localStorage — rejected: persists indefinitely; if user shares computer, next user inherits the token
- HTTP-only cookie — rejected: requires backend session, contradicts stateless principle
- In-memory only — rejected: must re-paste every page load; bad UX even for MVP

**Reconsider when:** Phase 3 lands SSO auto-auth, at which point sessionStorage becomes irrelevant.

---

## ADR-005 — One tool per Onsite endpoint, not coarse "do_anything" tool (2026-05-17)

**Context:** When designing tool schemas for Claude, should we have one big tool (`call_onsite_api(endpoint, body)`) or N narrow tools (`create_dependency`, `record_progress`, etc.)?

**Decision:** Narrow tools, one per logical action.

**Consequences:**
- ✅ Claude reasons better with explicit schemas (better extraction accuracy)
- ✅ Each tool has clear required fields → fewer ambiguous calls
- ✅ Easier to audit "what did the bot do" (tool name is meaningful)
- ❌ More tool definitions to maintain
- ❌ Need to add a new tool for every new endpoint

**Alternatives considered:**
- One generic `call_onsite_api(method, path, body)` — rejected: Claude would have to know all of Onsite's API in the system prompt, brittle
- Hybrid (narrow tools for common ops, generic for rare) — rejected: complexity not worth it yet

---

## ADR-006 — `location_id` is optional, default empty string (2026-05-17)

**Context:** The progress endpoint payload spec includes `location_id: "<uuid>"` as if required. But real-world progress entries have `location_id: ""` (empty). Our first tool schema required it, causing Claude to ask customers for location IDs they couldn't find.

**Decision:** Mark `location_id` as optional in the tool schema. Default to `""` server-side.

**Consequences:**
- ✅ Removes a UX blocker (customer doesn't need to find a non-existent ID)
- ✅ Matches observed real-world API behavior
- ❌ If Onsite re-activates locations as a real concept later, we'll need to revisit

**Reconsider when:** Akshansh confirms what `location_id` is supposed to do (research item in MEMORY.md).

---

## ADR-007 — System prompt is checked into code, not loaded from external source (2026-05-17)

**Context:** System prompts could be hosted externally (database, S3, config service) for dynamic updates without deploys. But that introduces a supply-chain risk vector.

**Decision:** System prompt is a const in `route.ts`, version-controlled in git.

**Consequences:**
- ✅ Can't be tampered with without a code change + PR review
- ✅ Auditable history of prompt evolution via git log
- ❌ Prompt changes require deploy (acceptable; deploys are fast on Vercel)

**Alternatives considered:**
- Load from a config file at runtime — rejected: same as external source, just slower
- Load from environment variable — rejected: env vars get logged, leaked, harder to review

---

## ADR-008 — Bypass PIN auth via pathname check, not Next.js route groups (2026-05-17)

**Context:** The `onsite-hub` app has PIN-based auth wrapping every page via `AppShell.tsx`. Task-bot is customer-facing and must skip that.

**Decision:** Add `if (pathname.startsWith('/task-bot')) return <>{children}</>` early in AppShell.

**Consequences:**
- ✅ One-line change, minimally invasive
- ✅ Easy to extend (more customer-facing routes can be added to the check)
- ❌ Path-string match is fragile (if someone renames `/task-bot` to `/customer-bot`, the bypass breaks silently)
- ❌ Mixes internal + external routes in the same code path

**Reconsider when:** More than 3 customer-facing routes exist. Then restructure with Next.js route groups: `(internal)/...` vs `(public)/...`.

---

## ADR Template (copy this for new ADRs)

```
## ADR-NNN — Title (YYYY-MM-DD)

**Context:** What problem are we solving? What forces are at play?

**Decision:** What did we choose?

**Consequences:**
- ✅ Good things this gives us
- ❌ Tradeoffs accepted

**Alternatives considered:**
- Alt 1 — why rejected
- Alt 2 — why rejected

**Reconsider when:** What signal triggers a re-evaluation.
```
