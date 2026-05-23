# Memory — Onsite Task AI

> **Hard-earned learnings.** Each entry below cost us debugging time, an API failure, or a wrong-call decision. **Read this before you assume.**
> **Last updated:** 2026-05-22 (V3 architecture finalized)

---

## V3 architecture (May 22, 2026 — new this cycle)

### M-01. Embedding model: `gemini-embedding-2` (NOT 001)
I dismissed "Gemini Embedding 2" as marketing — wrong. It IS a separate, newer model, GA April 2026. Natively multimodal (text+image+video+audio+PDF), 8192 token input (4× 001), 128-3072 flexible dim. **Embedding space INCOMPATIBLE with 001.** Don't mix vectors. Use at 1536-dim Matryoshka.

### M-02. Voice realtime — locked config from QuotaHit
QH `stable-v11.2-voice-live` had a one-day bug where OpenAI's GA migration renamed audio events. Defensive listen for BOTH:
```python
if t in ("response.output_audio.delta", "response.audio.delta"):
```
**For Onsite browser voice:** default to Gemini 3.1 Flash native audio (3× cheaper). **Phone/Twilio:** stay on OpenAI gpt-4o-mini-realtime (locked path).

### M-03. Vision document AI = 2-pass, not 1-pass
Pure Vision LLM hallucinates on dense invoices (95-97% acc). Pure Document AI = ₹15L/mo at lakhs scale. **Apply:** Pass 1 Gemini Flash + JSON schema → validators (GSTIN, line-sum, taxes-sum) → if any fail, Pass 2 Gemini Pro on failing fields only → still fail → human review. Cost ~$0.10/doc at 99.5%.

### M-04. 2-tier LLM routing is the cost killer
Pure Claude at 30M calls/mo = $45K. 2-tier = $20K. + semantic cache (30% reuse) = $14K. **Per-tenant cost cap is required** — single tenant can drain ₹10K/day if you forget.

### M-05. Semantic cache saves ~30% LLM calls
Construction-domain queries repeat (many users ask "list my projects" daily). Cosine >0.95 on query embedding → reuse answer. 5-min TTL on exact `tool::args::tenant` key. Auto-invalidate on any mutation by same user.

### M-06. RAG: hybrid > dense alone
KnowledgeForge uses ILIKE only (poor recall). MSBC uses BM25 + dense + Reciprocal Rank Fusion (87%+). **Apply:** Postgres tsvector + pgvector HNSW + RRF. No Pinecone/Weaviate — same DB, zero ops cost.

### M-07. PII handling = DPDP requirement (mandatory)
India DPDP Act enforces this. Construction data has phones, GSTIN, PAN, Aadhar. **Apply:** Pre-LLM scrubber (regex) → placeholders → restore in response. Track consent per tenant. Pattern lift: medassist `@audit_phi_access` decorator.

### M-08. Multimodal-RAG-System (Dhruv's own) is the RAG reference
Built March 10, 2026 by Dhruv using Gemini Embedding 2 Preview. 5 modality processors + vision describer + Whisper + frame extractor + SSE streaming. **Lift wholesale as Modal Python microservice** (faster than TS port). At `Euron/AI Architech Mastery/Multimodal-RAG-System/`.

### M-09. Angelina app has the action archetype
22 production tools including `vps_execute` (Python runner pattern), `save_memory`, `recall_memory`. Memory tiers already implemented with `memory_entries` schema (importance/type/tags + pgvector). **Apply:** Mirror tool-folder pattern (`src/app/api/tools/<tool>/route.ts`). Lift memory schema directly.

### M-10. Hireai has the phase state machine
`InterviewPhase` enum + per-phase prompts + `round_change` events. **Apply to Onsite Support** (Sprint 3): `TRIAGE → INVESTIGATE → RESOLVE → CONFIRM`. Each phase = own system prompt template.

### M-11. Smart AI Data Agent (MSBC) is the spine
`BaseConnector` ABC future-proofs for any new ERP/data source. `tenant_id` discipline. RAGAS eval at 87%+. **Wrap our 14 Onsite tools as one connector** — easy to add Morpheus / DarwinBox later without rewriting agent.

### M-12. Heartbeat is what makes it feel alive
A bot that just replies = transactional. A bot that surfaces "yesterday you mentioned X" = alive. **Apply:** Vercel Cron hourly. Scan `memory_entries.due_at <= now()`. Pattern miner. Decay old/low-importance memories.

### M-13. Python runner = speed + reliability win
"Export CSV" via LLM = 5s + $0.005. Same via pandas script = 200ms + ₹0. **Apply:** Sandboxed `python3` subprocess, 30s timeout, 512MB RAM, no network unless whitelisted. Start 8 curated scripts.

### M-14. Demo tenant from day 1
"Can't show bot live because it might break Soul Space" is real. **Apply:** `DEMO_TENANT=true` env switches to Supabase schema with realistic seed (5 projects, 80 tasks, 200 progress, 30 BOQs, 20 invoices, 50 photos).

### M-15. Alert rules: 10 production-grade
Lifted from Onsite Sales Intelligence System. Construction-adapted: stale task, critical path slip, cost overrun, material shortage, vendor late, **weather risk**, compliance deadline, **geo-mismatch**, inactive site, **safety incident**. Dedup via SHA-256 hash per rule+entity+date.

### M-16. Geo + weather + photo EXIF are domain unlocks
`navigator.geolocation` on every `record_task_progress` (with consent). OpenWeatherMap free tier (1M calls/mo) for Rule #6. Pillow EXIF extraction → photo location vs project location mismatch alert. Gemini Vision classifier tags photos for safety risk.

---

## Production gotchas (pre-V3)

### M-17. JWT token never in LLM payload
Multi-tenancy story = stateless agent + customer's JWT per-request. **Audit every code path** — JWT never in `messages` array sent to LLM. Errors from Onsite API are surfaced WITHOUT auth header content.

### M-18. AppShell.tsx PIN bypass is load-bearing
Line 13: `if (pathname.startsWith('/task-bot')) return <>{children}</>`. Two products in one Next.js app (sales team PIN-gated + customer task-bot bypass). Don't refactor away.

### M-19. JWT copy/paste typos cause 401
401 "token signature is invalid" → usually OCR-style typos (`l` vs `1` vs `I`). Re-copy from `web.onsiteteams.com` localStorage via console.

### M-20. Dependencies link LEAF BAs only
400 "only leaf node can be dependency" → BA has children. Verify `is_leaf=true` for both BAs before proposing dep chain.

### M-21. Same-workorder rule for dependencies
400 "Primary and secondary must be in same workorder" → cross-workorder = error. Surface in UI: "those two tasks are in different workorders."

### M-22. Progress logs against sub-activity, not BA
`record_task_progress` requires `billing_sub_activity_id`. New tasks have ZERO sub-activities until manually added. Check before proposing.

### M-23. Hallucination guard regex tuned (May 17)
Bug: bot said "✅ Done!" but no tool fired. **Apply:** `replyClaimsSuccess` regex matches first-person past-tense ("I created", "Done!", "Successfully logged") NOT passing "done"/"added" in data dumps. Triggers force-recall if action verb in context but no tool fired.

### M-24. Multi-workorder discovery
Project with multiple workorders silently undercounted (May 19 fix). **Try in order:** `/list/progressorder?project_id=` → `/list/workorder?project_id=` → fall back to `/detail/project/progressorder/<id>`. Aggregate across all workorders.

### M-25. Stat card labels match Onsite UI
"Total tasks: 75" confused users (Onsite Task tab showed 6-10 main rows). **Label tiles "Main / Sub / Leaf / With Deps"** — matches what user counts visually.

### M-26. Chat persistence on refresh (May 17)
Refresh lost chat because seed greeting fired before restore. **Apply:** `restoreFinished` flag gates seed. `restoreStartedRef` ref (not state) prevents effect re-run. `finally` always flips `restoreFinished = true`. Two-step restore: current session_id → fallback to most-recent.

### M-27. Supabase migrations via CLI, never dashboard paste
`source ~/.aiwithdhruv-secrets && export SUPABASE_ACCESS_TOKEN=$SUPABASE_ACCESS_TOKEN_TASK_AI && supabase db push --password 'Dhruvtomar7008@'`. Mirror existing remote-only migrations into local before pushing new ones.

### M-28. WhatsApp signature verification has dev bypass
Without App Secret can't HMAC-verify. **Dev mode** (NODE_ENV != production + no `ONSITE_WHATSAPP_APP_SECRET`) → accept webhook. **Production** refuses unsigned. Get App Secret from Meta dashboard → App Settings → Basic.

### M-29. Cloudflare quick tunnels are ephemeral
URL dies after hours of inactivity. For sustained dev, restart `cloudflared tunnel --url http://localhost:3001`. For prod, deploy to Vercel with stable custom domain.

### M-30. Build errors ≠ TS-check errors
`npx tsc --noEmit` passed but `npm run build` failed three different ways:
- `web-push` peer dep not installed
- chat/route.ts `Record<string,unknown>` → `[]` cast needed `unknown` intermediate
- `useSearchParams()` needs Suspense wrapper in Next 15 static prerender

**Always run `npm run build` before deploy.**

### M-31. Onsite JWTs last ~6 months, no refresh endpoint
**Store encrypted JWT directly** in `wa_user_link.access_token_encrypted`. Re-link prompt fires near expiry (`token_expires_at` from JWT claims).

### M-32. Per-tenant cost cap is critical
One looping client can drain $1000s overnight. **Hard cutoff in route.ts** after spend tracker breaches daily cap. Friendly message: "AI quota used today, resets at midnight."

### M-33. Vision LLMs lie about amounts under load
Even Gemini Pro hallucinates GSTIN digits or swaps CGST/SGST values on dense invoices. **Validators are not optional.** Σ(line items) must equal subtotal, Σ(subtotal + CGST + SGST + IGST) must equal total, GSTIN regex must match. Trust the validator, not the LLM.

### M-34. EXIF lat/lon is not trustworthy alone
Photo metadata can be edited or stripped. Server-side validation against project site coords is the source of truth. **For geo-fraud detection:** flag if photo lat/lon differs >500m from project site OR if EXIF is absent on critical uploads.

### M-35. Weather API caching matters
OpenWeatherMap free tier = 1M calls/mo. At 1 lakh users × 1 lookup/day = 100K/month — within free tier IF cached. **Cache per project location for 6h** in Redis. Without cache, you'll burn through free tier in days.

### M-36. Port 3001 owned by @agentron/web — onsite-hub uses 3002
2026-05-22 dev session: Next.js task-bot startup failed silently while onsite-hub processes existed but didn't bind. Root cause: `@agentron/web` (separate project, `next-server v15.5.12`, PID 3669 since 1:42 PM) already owned port 3001. **Apply:** Always check `lsof -i :3001` before starting onsite-hub dev. If contested, use `--port 3002`. Update the tunnel + `.env.local` `BASE_URL` accordingly. Long term: assign each AIwithDhruv project a stable dev port (onsite-hub=3001, quothit=3010, angelina=3020 etc).

### M-37. Sentry instrumentation peer-dep warning is harmless
2026-05-22: First `npm run dev` after installing `@sentry/nextjs` printed `⚠ Package import-in-the-middle can't be external` from `@fastify/otel` and `@prisma/instrumentation` nested deps. Not from our code. **Apply:** Ignore. If Sentry traces stop working we'll add `import-in-the-middle@3.0.1` as a direct dep. Don't try to fix proactively — adds 100+ packages to the lockfile.

### M-38. Cost-cap = char-count / 4 estimate until streaming lands
2026-05-22 Phase 2: route.ts wraps `callClaude` with `recordSpend` but the underlying `/v1/messages` and OpenRouter call don't return token usage in the result chain. Used `Math.ceil(charCount / 4)` as a token estimate — works ±30% which is plenty for budget enforcement at ₹200/day. **Apply:** When Phase 2.5 adds streaming, plumb true `usage.input_tokens` / `usage.output_tokens` from the Anthropic response and replace estimates. Don't over-engineer this until streaming is needed for UX.

### M-48. 3-tier model stack — GPT-4o-mini fast, DeepSeek V4 Pro default, Haiku escalation

**2026-05-23 hard bench confirmed:** DeepSeek V4 Pro matches Haiku 4.5 on 8/8 multi-step UUID-fidelity tests (including update + delete + Hindi write) at 2.7× lower cost. GPT-4o-mini is 2× faster than Haiku on trivial replies at 7× lower cost but missed 1/8 on RULE 0.65. Sonnet 4.6 retired entirely (cost was ~$0.18/call × multi-iter = unsustainable).

**Apply (shipped 2026-05-23):**

3-tier routing in `pickModel()`:
- **FAST_MODEL** = `openai/gpt-4o-mini` — greetings, yes/no, acks ("hi", "thanks", "ok", "haan")
- **DEFAULT_MODEL** = `deepseek/deepseek-v4-pro` — every read + write turn; multi-step UUID work
- **ESCALATION_MODEL** = `anthropic/claude-haiku-4-5` — when DeepSeek slips on a UUID guard (M-40/41/44)
- **COMPLEX_MODEL** = `anthropic/claude-sonnet-4-6` — last-resort, max 1/turn, almost never fires
- All env-overridable: `TASK_BOT_FAST_MODEL` / `TASK_BOT_MODEL` / `TASK_BOT_ESCALATION_MODEL` / `TASK_BOT_COMPLEX_MODEL`

Classifier rules (route to FAST_MODEL only when ALL hold):
- ≤5 words AND ≤80 chars
- Matches `TRIVIAL_PATTERNS` (hi/hello/thanks/ok/yes/no/haan/namaste/got it/...) OR ≤3 words with no domain/action signal
- No action verbs (log/record/mark/create/delete/update/add/show/list/...)
- No domain words (project/task/dep/coupler/drilling/...)
- No numbers (numbers signal quantity → write turn)

Anything else → DEFAULT_MODEL (DeepSeek V4 Pro).

**Cost at 100K turns/month:**
- Before (all-Haiku): ~$1200/mo
- After (3-tier): ~$244/mo
- **Net: ~5× cheaper** (~₹80K/mo saved)

**Why this stack works:**
- DeepSeek V4 Pro proved 8/8 on hard tests = same correctness as Haiku at 1/3 cost. Slightly slower (2.1s vs 1.6s) but still <2.2s.
- GPT-4o-mini's 1 miss (RULE 0.65) doesn't matter because we only route to it for chitchat that doesn't need tools.
- Haiku as escalation means worst-case cost still bounded (DeepSeek slip → 1 Haiku retry max).
- Sonnet stays bannable — code path exists but virtually never triggers.

**Pricing table in `cost_cap.ts` updated** with deepseek-v4-pro ($0.435 in/$0.87 out per M tokens), gpt-4o-mini ($0.15/$0.60 per M), accurate INR conversion.

### M-47. Project anchor — one project per chat, server-enforced, slashes cost

**2026-05-23:** Every chat used to re-do `list_companies → list_projects` on every single turn. Two problems: (a) burning Onsite API budget, (b) giving the LLM repeated opportunities to fabricate UUIDs (M-41) or pick the wrong company UUID (M-44). Also the user explicitly asked: "make the onboarding fixed, not random — every new chat should anchor to one project and stay there."

**Apply (shipped 2026-05-23):**

1. Migration 017 added `project_anchor JSONB` column to `task_ai_session_meta`. Stores `{project_id, project_name, company_id, company_name, anchored_at}`.

2. **Onboarding flow (anchor-null state):** RULE 0.4 in system prompt locks the bot to ONE action — ask "which project?" + accept user's reply + call `list_projects(search_query=name)` once. No other tools allowed.

3. **Auto-anchor:** when `list_projects` returns exactly ONE match during onboarding (no anchor + session_id + unambiguous match), server auto-persists the anchor + auto-renames the session title to the project name. No bot action needed. Tool result includes `chat_locked_to_project: {tell_user: "..."}` so the bot's reply acknowledges the lock.

4. **Anchored state:** RULE 0.4 swaps to a different prompt fragment that injects the anchor as hardcoded facts. Bot uses the IDs directly — NO list_companies / list_projects every turn. If user mentions a different project name, bot refuses to switch and suggests `+ New chat`.

5. **M-46 partial revert (cost):** Sonnet-as-default-for-writes was costing $0.15-0.18/call × multi-iter = unsustainable. Reverted to Haiku-only default. What makes Haiku safe NOW: the anchor short-circuits multi-step resolution. Haiku doesn't need to chase list_companies → list_projects → list_tasks → list_subactivities anymore — the first three IDs come from the anchor, only the leaf needs lookup. Guards (M-40/41/44) still catch fabrication.

**Why this works for cost:** Per write turn:
- Before anchor: list_companies + list_projects + list_tasks + list_subactivities + record = ~5 Haiku iters + occasional Sonnet escalation = ₹0.30+
- After anchor: list_tasks (cached) + list_subactivities + record = ~3 Haiku iters = ₹0.05

**Net: 6× cheaper, and more reliable because anchor removes the entire UUID-resolution failure surface.**

### M-46. Write-tool turns belong on Sonnet, not Haiku — and the UI shouldn't show recovery as failure

**2026-05-23 (Earth Work incident):** User said `"Log progress on Earth Work, 50 units"`. Haiku 4.5 fabricated SHA256-hash IDs (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), placeholder strings (`"dhruv-construction"`), 8e3e-pattern fake UUIDs (`c9b7c8f2-8e3e-4e3e-8e3e-8e3e8e3e8e3e`) across three different retry iterations. All caught by M-40/M-41/M-44 guards. Bot eventually got to the right Onsite UUID at iter=4 — but `MAX_ITERATIONS=8` ran out before it could complete the write. User saw an "I tried several steps but couldn't complete that fully" reply + a red error card from the FIRST failed iteration. **Looked like a total failure when the system was actually self-correcting.**

**Three compounding bugs, three fixes (shipped same day):**

1. **Haiku misroutes write-turns.** Detect action verbs (`log progress`, `record progress`, `mark`, `create dep`, `delete`, `update`, `add task`, `undo`, plus Hindi equivalents) in the user's latest message and start the turn on Sonnet 4.6 instead. Haiku still handles read-only turns (cost preserved). Net: write success on first try, fewer total LLM calls than the Haiku-retry-then-escalate path.

2. **Error card message was hardcoded to "position number"** — fired for fabricated-UUID and wrong-type violations too. Now tracks `violationKind: 'shape' | 'fabricated' | 'wrong_type'` and renders type-specific copy. User sees "Bot tried to use a made-up UUID" vs "Bot used a UUID from the wrong list" vs "Bot passed an invalid ID."

3. **UUID-guard trips are recovery steps, not failures.** They shouldn't render to the user. Card now only emits when the FINAL state is failure — if a later iter succeeded, the leftover error card is cleared. UI only shows what actually matters.

4. **`MAX_ITERATIONS` 8 → 12.** UUID-guard recoveries can chew 4 list_* calls before the write succeeds (companies → projects → tasks → subactivities). 8 was too tight; 12 gives breathing room without runaway loops.

**Apply:** trust the multi-guard recovery loop. The bot WILL fabricate IDs occasionally — that's the LLM. Defense in depth (M-40/41/44 + Sonnet-for-writes + larger iter budget) makes it self-heal.

### M-44. Typed UUID provenance — BA UUIDs ≠ sub-activity UUIDs

**2026-05-23:** Even with shape (M-40) and provenance (M-41) guards, the model can still mix UUID *types*. A Billing Activity UUID and a Sub-Activity UUID look identical to a regex but mean different things to Onsite. If the bot grabs a UUID from a `list_tasks` result and passes it as `billing_sub_activity_id`, Onsite's API will reject it — but only after the round-trip, wasting tokens and risking partial-state writes for transactional tools.

**Apply (shipped 2026-05-23):**
- Server-side walks each `(assistant w/ tool_calls → tool result)` pair in `workingMessages`, tags every UUID in the result with the SOURCE tool's entity type via `TOOL_TO_TYPE` map:
  - `list_companies` → `company`
  - `list_projects` → `project`
  - `list_tasks` / `search_tasks` → `ba`
  - `list_subactivities` → `sub_activity`
  - `list_dependencies` → `dep`
  - `list_progress_history` → `progress`
- Each ID-shaped arg field is mapped to its EXPECTED type via `FIELD_TO_TYPE`:
  - `billing_sub_activity_id` → expects `sub_activity`
  - `billing_activity_id` / `ba_id` / `primary_ba_id` / `secondary_ba_id` → expects `ba`
  - `project_id` → expects `project`
  - `company_id` → expects `company`
  - `progress_history_id` → expects `progress`
  - `dep_id` → expects `dep`
- Guard fires when the UUID exists in a DIFFERENT type bucket than expected. Error message names both the actual and expected types + the resolver tool to call.
- Only fires when we KNOW the source type. UUIDs from user paste (typed nowhere) fall through to the looser M-41 provenance check — they're accepted on conversation presence alone.

**Why this matters:** the three guards now stack:
1. M-40 shape — rejects `"3.1"`, `"the-raft-work-ba-id"`, etc.
2. M-41 provenance — rejects fabricated UUID-shaped strings
3. M-44 typed — rejects right-shape, real-but-wrong-type UUIDs

Together they make "the bot fired the wrong tool args" virtually impossible — every failure mode now produces a structured server error the bot must address.

### M-45. Memory dedup at save — same fact, repeated, doesn't help recall

**2026-05-23:** When system-prompt RULE 0.7 instructs the bot to "proactively save memories", it tends to save the SAME fact (e.g. `topic=name, content=Dhruv`) once per session — accumulating 5 identical rows by week's end. Each adds noise to recall (same fact returned 5×) and bloats the embedding index.

**Apply (shipped 2026-05-23):** `saveMemory` now pre-checks for an existing row in the same tenant + type with a similar topic (case-insensitive ILIKE). If found, the dedup heuristic compares normalized content:
- Exact match (after lowercasing + whitespace collapse) → UPDATE existing row
- Substring containment in either direction (5+ chars) → UPDATE existing row
- Otherwise → INSERT new row

When deduped, the existing row's content + tags + importance + embedding + `updated_at` are refreshed. Returns `{id, deduped: true}` so callers can distinguish.

Trade-off: small overhead per save (one extra SELECT). Worth it — memory hygiene compounds.

### M-42. Bot picks wrong sub-activity from a list + lies about the name

**2026-05-22 (Drilling/Coupler incident):** User asked "mark 1 unit progress in task 3.1 Coupler". Bot correctly resolved Drilling's BA UUID via `list_tasks`, then called `list_subactivities` which returned BOTH **Coupler** (the actual sub-activity) AND **"Location 1"** (Drilling's auto-default sub-activity). Bot picked Location 1's UUID, called `record_task_progress`, API succeeded with `sub_activity_name="Location 1"` — but bot then COMPOSED its reply as `"✓ Done! Logged 1 unit on Coupler"`. Onsite UI showed Drilling 28.57% and Coupler 0/1 — because progress landed on Location 1, not Coupler.

UUID provenance check (M-41) PASSED because both UUIDs came from a legit `list_subactivities` result. Bot just chose the wrong one AND lied in text about which one it chose.

**Apply (shipped 2026-05-22):**
1. **System prompt RULE 0.8** — "your reply text MUST reference the EXACT task_name and sub_activity_name returned by the API, NOT what the user originally asked for. If they don't match, flag the mismatch explicitly."
2. **Server-side name-match check** in `record_task_progress` handler. Scans last 3 user messages for capitalized/quoted tokens; if any of them looks like a sub-activity name AND the actual returned `sub_activity_name` doesn't appear in user text, append `name_mismatch_warning` to the tool result. Forces bot to either retract or own up to the mismatch.
3. **`assistant_must_reference` field** added to record_task_progress success response. Bot can't claim it didn't see the canonical names.

**Why not just block the wrong pick?** Detecting "user meant Coupler" vs "user accepted Location 1" needs NLP intent — fragile. The warning approach lets the bot still write progress when ambiguous, but forces transparent reporting about WHERE it landed.

### M-43. Vision LLMs hallucinate vendor names from context, not pixels

**2026-05-22:** User uploaded a random image (not an invoice) to the Vision Upload modal. Gemini 2.5 Flash returned `{vendor_name: "AiwithDhruv", line_items: []}`. The image had no AiwithDhruv text at all — model pattern-matched from system prompt context ("Indian construction app", user's brand) and confidently fabricated a vendor name.

**Apply (shipped 2026-05-22):** Tightened `src/lib/vision/extract.ts` system prompt with explicit anti-hallucination block:
- "DO NOT INFER. DO NOT GUESS. If a field is not VISIBLY PRESENT, OMIT it."
- "If the image is NOT actually a \<doc_type\>, return `{not_a_<doc_type>: true, what_is_it: '...'}`. Do NOT fake extract."
- Specific rules: vendor/company names only if you can READ them; amounts only digits you can see, no estimation.

This is a model-level reliability fix. Validators (M-33) catch arithmetic errors but can't catch "the LLM made up a vendor name out of thin air." Prompt is the only defense for that class.

### M-41. UUID shape alone isn't enough — bot hallucinates plausible UUIDs

**2026-05-22 (~30 min after M-40 fix):** With the UUID-shape guard live, Haiku 4.5 stopped passing `"3.1"` — but immediately started passing **fabricated UUID-shaped strings** like `"8c3d4e5f-2b1a-4c9d-8e7f-1a2b3c4d5e6f"` (note the sequential hex bytes, classic LLM confabulation). Used the SAME made-up UUID as `billing_sub_activity_id` AND `project_id` across two tool calls in iter=0/iter=1.

**Root cause:** When the model is asked for an ID it doesn't have, regex-shape validation lets the model "satisfy" the constraint by inventing UUID-shaped garbage. The shape is necessary but not sufficient.

**Apply (shipped 2026-05-22 same session):**
- **UUID provenance check** at the dispatcher boundary. Build `KNOWN_UUIDS` set by scanning ALL prior message text (user + assistant + tool result) for the UUID regex pattern. Every ID-shaped tool arg must already be in `KNOWN_UUIDS` to be accepted.
- A real UUID can only enter the conversation via (a) a user paste, or (b) a prior tool result. The model cannot conjure one that wasn't shown to it.
- Triggers error: `"<uuid>" looks like a UUID, but has NEVER appeared in any prior tool result or user message. You almost certainly fabricated it. Call list_* to get the REAL UUID.`
- Defense in depth on top of M-40 shape guard. Both run on every tool call.

**Why this works:** LLMs can mimic the SHAPE of a UUID (32 hex chars + dashes) but can't guess the actual contents that match a real database row. By keeping a ledger of UUIDs the model has been told about, we anchor it to ground truth without needing schema knowledge of every endpoint.

### M-40. Position numbers as UUIDs — Onsite silently 200s, bot fakes success

**2026-05-22:** Haiku 4.5 passed `"3.1"` as `billing_sub_activity_id` (the tree position of Coupler under Drilling) and `"3"` as `billing_activity_id`. Onsite's `/apis/v3/...` endpoints returned **HTTP 200** on those bad IDs — either by writing to an orphan record nobody can see, or by silently 404ing. Bot then reported `"✅ Done! +2 meter logged"` while the actual Onsite UI still showed `0/1 numbers, NotStarted, No Progress Update Added` for the real Coupler.

This is a **prompt-following lapse** by Haiku — system prompt RULE -1 explicitly forbids using list positions as IDs, but the model still slipped under phrasing like "on drilling mark 1 progress" right after a numbered-list reply.

The existing hallucination guard (M-23) didn't catch it because it looks for "I created X" claims with NO tool firing — here a tool DID fire, just with the wrong ID.

**Apply:**
1. **Hard UUID guard at the tool boundary** in route.ts (shipped 2026-05-22 commit). Validates every ID-shaped arg against `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i` BEFORE the fetch. Returns a structured error forcing the bot to call `list_*` to resolve the real UUID.
2. Guard covers: `primary_ba_id`, `secondary_ba_id`, `billing_sub_activity_id`, `billing_activity_id`, `progress_history_id`, `dep_id`, `ba_id`, `ba_id_2`, `project_id`, `company_id`, `workorder_id`.
3. Logs every trip as `[task-bot] UUID guard tripped iter=… field=… value=…` so you can grep `/tmp/onsite-hub-dev.log` for it.
4. **Trust no LLM output for IDs** — even when the system prompt is explicit. The bug surface is too wide; defense at the API boundary is the only durable fix.

### M-39. Embedding model env var is `gemini-embedding-001` for now
Per M-01 the V3 doctrine is `gemini-embedding-2`. Per the actual `ai.google.dev` model list as of Apr 2026, the API name is `gemini-embedding-001` (the marketing 2.0 announcement uses the same identifier in the v1beta endpoint). **Apply:** Code reads model name from `GEMINI_EMBEDDING_MODEL` env var (default `gemini-embedding-001`). When Google publishes a separate `gemini-embedding-2` identifier OR confirms the rebrand, flip the env. Vectors written today at 1536-dim Matryoshka are intended to be forward-compatible with `gemini-embedding-2` per Google's published roadmap.

---

## Where to find more

- **`~/.claude/projects/.../memory/`** — cross-session memory (40+ entries) — includes Dhruv's working-style feedback rules, voice configs, Supabase patterns, GitHub repo map
- **`Onsite/task-ai/BUG-TRACKER.md`** — symptom → root cause → fix per ticket
- **Git log:** `git log --oneline | grep -i "fix\|bug\|patch"` for historical fixes
- **V3 doc set:** `BRD-V3.md`, `PRD-V3.md`, `ARCHITECTURE-V3.md`, `HLD-V3.md`, `LLD-V3.md`

---

**Rule:** Every bullet above is a bug or gotcha we already paid for. **Read this before changing anything.** Add new entries (M-36, M-37, ...) when you fix something non-obvious.
