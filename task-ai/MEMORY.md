# Onsite Task AI — Memory

> Persistent learnings. Each entry below cost us debugging time, an API failure, or a wrong-call decision. **Read this before you assume.**

Last updated: 2026-05-17

---

## How to Use This File

This is the project's **institutional memory** — separate from CLAUDE.md which is the master context. CLAUDE.md tells you *what the product is*; MEMORY.md tells you *what we've learned the hard way*.

**When to read:** Before any non-trivial change. Before debugging. Before adding a feature you think is "easy."

**When to write:** Every time you (or any AI agent) discovers something non-obvious — an API quirk, a workaround, a decision rationale, a "we tried X and it broke." Add a dated entry below.

**Format:** `### YYYY-MM-DD — Title` then 3 short sections: **What we learned**, **Why it matters**, **How to apply**.

---

## Data-Model Memories

### 2026-05-17 — Sub-activity is the real progress target, not BA

**What we learned:** The Onsite API expects `billing_sub_activity_id` for progress entries, not the parent Billing Activity ID. A task ("Electrical panel Setup") is a BA. Under each BA are one or more *sub-activities* (labeled "Location 1", "Floor A", etc. in the UI). Progress is logged against a sub-activity, not the BA itself.

**Why it matters:** Brand-new tasks have ZERO sub-activities by default. If a customer says "log 5 ft of progress on this new task," the bot must first check if sub-activities exist; if not, surface a friendly error ("This task needs a Location added in Onsite before progress can be recorded").

**How to apply:**
- Tool definition for `record_task_progress` takes `billing_sub_activity_id`, not BA ID
- Bot system prompt explains this terminology so Claude doesn't confuse the two
- Phase 2 must add a "list sub-activities under a BA" API call so the bot auto-resolves "log progress on Electrical panel Setup" → asks "which location: 1, 2, or 3?"

---

### 2026-05-17 — location_id field is empty in real entries

**What we learned:** The payload spec Akshansh shared has `location_id: "f636c742-..."` but actual progress entries in production have `location_id: ""` (empty string). The `monkey_patch_sub_activity_name` field carries the "Location 1" display label — it's not a real location entity.

**Why it matters:** Our tool spec originally required `location_id`. That caused Claude to ask the customer for a location ID, which they had no way to find (and the field is unused anyway). We made `location_id` optional (defaults to empty string).

**How to apply:** Always default `location_id: ""` in the request body. Unless Akshansh confirms locations are coming back as a feature, treat this field as deprecated cruft to satisfy the schema.

---

### 2026-05-17 — Dependency rules (enforced server-side)

**What we learned:** The `taskdependency` handler enforces strict rules:
1. Both BAs must be **leaf nodes** (no children) — "only leaf node can be dependency"
2. Both BAs must be in the **same workorder** — cross-workorder = 400 error
3. **No cycles** allowed (server runs cycle detection)
4. `lag` must be ≤ 1000
5. 4 valid types: `finish_to_start` | `finish_to_finish` | `start_to_start` | `start_to_finish`

**Why it matters:** When the bot fails, customers blame the bot. We must catch these BEFORE calling the API where possible (need a "list BAs" call to check leaf status + workorder match), or surface the server error gracefully when we can't.

**How to apply:** Phase 2 should add a pre-flight check using `list/billingactivity` to detect leaf status and workorder grouping before the dependency call.

---

## Auth Memories

### 2026-05-17 — JWT signature errors are usually OCR misreads

**What we learned:** First test failed with `401 token signature is invalid: signature is invalid`. Root cause: I had OCR'd the token from a screenshot and confused `I` (uppercase i) with `l` (lowercase L). One wrong char = invalid signature. The correct token came from `JSON.parse(localStorage.getItem('token')).token` via browser Console.

**Why it matters:** Any token-related debug must start with "is the token byte-identical to localStorage?" before chasing other hypotheses.

**How to apply:**
- In setup screen, show a small `Tip` link: "Run `copy(JSON.parse(localStorage.getItem('token')).token)` in your Onsite tab Console to get an error-free copy"
- For Phase 3 (Onsite-embedded), bypass the paste step entirely — read token from the parent frame's localStorage via postMessage

---

### 2026-05-17 — Token is in localStorage key `token`, JSON object with `.token` + `.expire`

**What we learned:** Onsite's web app stores auth as:
```js
localStorage.getItem('token')
// → JSON string: {"token":"eyJ...","expire":"2026-07-15T19:47:36.640548541Z"}
```

**Why it matters:** Future scripts that need to fetch the token must parse the JSON, not just read the localStorage value directly.

**How to apply:** `JSON.parse(localStorage.getItem('token')).token`

---

### 2026-05-17 — Custom headers Onsite frontend sends (we currently don't)

**What we learned:** The Onsite Angular frontend sends these custom headers on every API call:
- `Project-Company-Id: <company-uuid>`
- `Project-Id: <project-uuid>`
- (And per CORS allow-headers: `enterprise-id`, `version-code`, `X-Razorpay-Signature`, `api-secret`)

Our chatbot currently only sends `Authorization` and `Content-Type`. It worked for `taskdependency` and `billingprogresshistory` — both endpoints derive context from the request body and JWT, not headers.

**Why it matters:** Other endpoints (especially listing/searching) may require `Project-Id` to scope the query. If a new endpoint returns "empty results" or 400 unexpectedly, try adding these headers.

**How to apply:** When integrating a new endpoint, first check the Onsite UI's Network request for that endpoint and replicate all custom headers it sends.

---

## Architecture Memories

### 2026-05-17 — Stateless design = trivial multi-tenancy

**What we learned:** By NOT persisting any customer data (no DB, no logs of tokens or content), we get multi-tenancy for free. Each request is fully self-contained: `{ messages, token, baseUrl }`. The same backend serves customer A and customer B with zero risk of data crossover because nothing is stored.

**Why it matters:** Sumit's first question will be "can a customer see another customer's tasks?" The answer is structurally "no" — we'd have to actively break this to leak data. Compare to a system with shared DB tables + customer_id filters, where one missing WHERE clause = catastrophic leak.

**How to apply:** Resist the urge to add Supabase / logging / "just save the chat history" without re-reading HLD.md. If you add persistence, you must also add per-customer isolation (RLS, encrypted-at-rest, audit trail, GDPR/India DPDP compliance review).

---

### 2026-05-17 — Bypass PIN auth via pathname check in AppShell

**What we learned:** The onsite-hub app wraps every page in `AppShell.tsx` which gates everything behind PIN login. For a customer-facing route, this is wrong. We added one early-return:
```tsx
if (pathname.startsWith('/task-bot')) return <>{children}</>
```

**Why it matters:** This is load-bearing. Any refactor of AppShell.tsx must preserve this carve-out, or the task-bot becomes inaccessible to anyone without an internal Onsite PIN.

**How to apply:** When more customer-facing routes are added (e.g., `/customer-portal`), add them to the same check. Long-term, restructure with Next.js route groups: `(internal)` vs `(public)`.

---

### 2026-05-17 — Claude tool use via OpenRouter (OpenAI format) works for Sonnet 4.6

**What we learned:** OpenRouter's OpenAI-compatible chat-completions endpoint supports Claude tool use. We pass:
```json
{ "model": "anthropic/claude-sonnet-4-6", "messages": [...], "tools": [...], "tool_choice": "auto" }
```
Response shape matches OpenAI exactly: `choices[0].message.tool_calls[]` with `{id, type:'function', function:{name, arguments}}`.

**Why it matters:** We don't need the Anthropic SDK or a separate Anthropic API key — the existing `OPENROUTER_API_KEY` in onsite-hub's env works.

**How to apply:** Use the same pattern for any new tool. Make sure the second call (after tool execution) includes the original assistant message *and* a `{role: 'tool', tool_call_id, content}` message, in that order.

---

## Product / UX Memories

### 2026-05-17 — Customers won't find BA IDs in DevTools

**What we learned:** During testing, even Dhruv (a developer) needed step-by-step guidance to find a BA ID from the Network tab. End customers (site engineers, project managers) will never do this.

**Why it matters:** Phase 2 is not optional. Without a "list tasks by name" capability, the product is unusable for real customers.

**How to apply:** Treat the BA-ID-paste UX as a developer-only stopgap. Phase 2 priority is integrating list/search APIs so the bot says: "I see 12 tasks in Soul Space. Which one is the predecessor: a) Footing Installation b) Foundation Wall c)..."

---

### 2026-05-17 — Hindi-English code-switching is the default

**What we learned:** From the recording with Akshansh's team, conversations naturally mix Hindi and English. Site engineers may say things like *"task A ko complete karna hai pehle, phir B start karenge"*.

**Why it matters:** A pure-English bot will feel foreign. Claude Sonnet 4.6 handles code-switching natively, but we need to nudge it via system prompt so it responds in the user's mixed register.

**How to apply:** Phase 2 system prompt: "Reply in the same language the user uses. If they mix Hindi-English, mix back. Default to Hindi-English for construction terminology when unsure." Add native Hindi voice-input language to Web Speech API (`lang = 'hi-IN'` toggle).

---

### 2026-05-17 — Mobile-first because site engineers are on phones

**What we learned:** Onsite's whole value prop is "mobile-first for site workers." If our bot is desktop-only or even just desktop-best, it misses the primary user.

**Why it matters:** Voice input is not a nice-to-have — site workers wear gloves, are in noisy environments, need hands-free. The mic button must be prominent, the language pickup robust.

**How to apply:** Every UI change must be tested at iPhone-SE viewport width (375px). Tap targets ≥ 44px. Voice button equal weight to send button.

---

## Process Memories

### 2026-05-17 — One PRD-quality message to Akshansh > many small asks

**What we learned:** Akshansh is busy. Getting one API endpoint spec at a time would take weeks. Better to send him a single, formatted message listing all 7 endpoints we need with the exact format we want (same as the original taskdependency spec).

**Why it matters:** Velocity. If Phase 2 is blocked on his API specs and we drip-feed requests, Phase 2 takes 3 weeks instead of 3 days.

**How to apply:** See [ROADMAP.md § Phase 2](ROADMAP.md) for the exact WhatsApp template to send Akshansh. Send it once. Get all 7 back. Build all 7.

---

### 2026-05-17 — Verify visually before claiming "fixed"

**What we learned:** The first version of this product was tested via curl, not via the actual chatbot UI. When Dhruv used the UI with the same token (which I had mis-OCR'd from a screenshot), it failed with 401 — making it look like the UI was broken when actually the token was wrong.

**Why it matters:** Always test through the real UI path before claiming end-to-end success. Curl ≠ UI ≠ customer.

**How to apply:** After any change, do the full flow: open localhost:3001/task-bot → paste fresh token → send a real message → verify in Onsite UI. Screenshot the success state.

---

## Open Questions (research these next time)

1. **What does Onsite's existing AI bot do?** They have one in their app (per Dhruv). Where is it? What features? What's its position in the UI? Knowing this lets us position differently OR replace it.
2. **Is there a Project-Locations API?** The `location_id` field exists but seems unused. Did it represent something else originally (warehouse locations? site zones?)?
3. **What's the rate limit on Onsite's API?** If 1,000 customers hammer the bot, will we hit a per-IP cap?
4. **Does `add/billingactivity` create a leaf or a parent?** Need to know to support "add a sub-task" intent correctly.
5. **What's the right intermediate model for batching?** Sonnet 4.6 at ~$3/$15 per Mtok costs roughly $0.01 per chat turn. Haiku 4.5 could handle simple tool dispatching at 1/5 the cost. Worth exploring after volume justifies it.
6. **i18n strategy: per-request prompt vs UI translations vs both?** Most efficient is to instruct Claude in system prompt + translate UI strings via i18next.

---

## Decision Log Pointer

Architectural decisions with their tradeoffs and rationale → [docs/decisions.md](docs/decisions.md).
