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

---

## Where to find more

- **`~/.claude/projects/.../memory/`** — cross-session memory (40+ entries) — includes Dhruv's working-style feedback rules, voice configs, Supabase patterns, GitHub repo map
- **`Onsite/task-ai/BUG-TRACKER.md`** — symptom → root cause → fix per ticket
- **Git log:** `git log --oneline | grep -i "fix\|bug\|patch"` for historical fixes
- **V3 doc set:** `BRD-V3.md`, `PRD-V3.md`, `ARCHITECTURE-V3.md`, `HLD-V3.md`, `LLD-V3.md`

---

**Rule:** Every bullet above is a bug or gotcha we already paid for. **Read this before changing anything.** Add new entries (M-36, M-37, ...) when you fix something non-obvious.
