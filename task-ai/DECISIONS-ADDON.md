# Decisions — Onsite Task AI Add-On Stack

> **PM:** Angelina | **Date:** 2026-05-19 | **Reviews:** Dhruv (single approver)
> **Companion to:** `PRD-ADDON.md`, `HLD-ADDON.md`, `ROADMAP-ADDON.md`
> **Status:** Open until Dhruv signs off. After sign-off, dispatches go out.

This doc answers the 6 open decisions in §5 of `ANGELINA-ADDON-DISPATCH.md` and adds 3 decisions I'm forcing myself to make that the dispatch left implicit. One-line rationale, one-line risk, what changes if Dhruv overrides.

---

## D1 — Single `/task-bot` surface, modular backend routes

**Decision:** All 4 add-ons live behind the existing `/task-bot` chat surface. Backend splits into 4 sibling routes under `/api/task-bot/*` for separation of concerns:

- `/api/task-bot` (existing) — action tools
- `/api/task-bot/kb/*` — RAG ingest, search, sync admin
- `/api/task-bot/voice/*` — session token, WS proxy, end
- `/api/task-bot/training/*` — module list, phase advance, flashcard review
- `/api/task-bot/support/*` — ticket create/list, escalation hooks

**Why:** Users don't want 4 URLs; engineers don't want 1 mega-route. Single chat reduces cognitive load for site engineers (already overloaded). Backend modularity keeps blast radius small — RAG bug doesn't break Voice.

**Risk:** Tool registry on the chat route grows from 14 → 18+ tools. Mitigation: dynamic registration by user plan/tenant feature flag.

**If Dhruv overrides → split UI routes:** Adds a /task-bot/kb · /task-bot/learn · /task-bot/help sibling, increases sidebar complexity, doesn't change backend modularity. Reversible.

---

## D2 — Notion: ongoing mirror, NO planned retirement

**Decision:** Pull-mirror Notion every 6 hrs into our RAG store. **Never auto-retire Notion.** Customers retire it themselves when they're ready.

**Pushback on Dhruv's lean (retire in 90 days):** RAG-over-docs is not a Notion replacement — Notion is also where Onsite *authors* and *shares* and *collaborates* on docs. We replace the **query surface**, not the **authoring surface**. Forcing customers to migrate authoring inside 90 days = change-management churn with no upside. Pull-mirror also means Notion stays the source of truth — when a customer updates a page, we re-index. We never have to ask them to migrate.

**Why:** Customer success > technical purity. Onsite already loses customers to "app too complex" (per Sales Intel May 2026 findings, 62% need-approval objection). Forcing a Notion migration is a second tax on the same buying committee. Skip it.

**Risk:** Two sources of truth (Notion + our index) → drift if sync fails silently. Mitigation: admin UI shows "last sync OK X minutes ago" + alerts at 24-hr-old data.

**If Dhruv overrides → 90-day retirement:** Add a migration date banner + customer-facing migration assistant. Adds ~5 dev-days of effort. Defer to Sprint 11 if at all.

---

## D3 — Build our own ticket queue; webhook-out adapter for future Onsite integration

**Decision:** Ship a fresh Supabase-hosted ticket queue (`support_tickets` + `support_audit_log` tables) with `external_ticket_id TEXT NULL` reserved for cross-link. Add a stub webhook-out hook (`POST {OUTBOUND_TICKET_WEBHOOK_URL}`) that's disabled by default. When Akshansh/Sumit tell us Onsite's ticket system, we flip the env var on and forward.

**Pushback on Dhruv's lean (default after 48h):** 48-hour wait is fake — Akshansh has been blocked on `add_task` API since May 17 (3 days). Waiting for "what's the existing ticket system" delays Sprint 5 by 2-3 weeks. Ship our own queue NOW. Forward later. Cost of building queue first = ~2 days of dev. Cost of waiting = 2-3 weeks of slip.

**Why:** Our own queue gives us: (1) full control of urgency taxonomy + SLAs, (2) audit log we own (compliance argument for enterprise tier), (3) zero dependency on Akshansh's reply velocity. Onsite integration becomes a 1-day adapter when they're ready.

**Risk:** If Onsite already has a Zendesk/Freshdesk and refuses our queue, we wasted 2 dev-days. Acceptable — the queue code is reusable for Setu / future clients anyway.

**If Dhruv overrides → wait 48h then decide:** Sprint 5 slips by at least 1 week. Sprint 6 (escalation) blocks on Sprint 5. Cascading.

---

## D4 — Onsite's account pays for production API keys; AIwithDhruv pays for dev/staging

**Decision:** Production env vars (`GOOGLE_AI_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `COHERE_API_KEY` if used) point to **Onsite's billing accounts**. Sumit/Akshansh provision and own the keys. Dev/staging keys are on AIwithDhruv accounts so we can iterate without burning their budget.

**Why:** Onsite owns the customer relationship and the revenue. Float risk on AIwithDhruv's side (we pay first, bill later) is a small-shop killer at 10K-customer scale. Standard SaaS-vendor hand-off pattern.

**Risk:** Onsite won't have all three accounts set up. Resolved by giving them a 1-page onboarding checklist before Sprint 0 closes.

**If Dhruv overrides → AIwithDhruv pays then bills:** Need a metering pipeline (per-tenant LLM cost attribution), monthly invoice generation, accounts-receivable workflow. Adds ~5 dev-days + ongoing finance ops. Defer until commercial model is signed with Sumit.

---

## D5 — Shailendra leads; Afeefa = architecture review only (1 hr/sprint)

**Decision:** Shailendra is build owner for all 10 sprints, working through Atlas/Pixel/QA dispatch sessions (NOT spawned coding agents — paste-launched per `feedback_never_spawn_coding_agent`). Afeefa reviews architecture at Sprint 1 kickoff (RAG schema + retrieval design), Sprint 2 kickoff (voice WS architecture), and Sprint 10 hardening (audit pass). Three 1-hour touchpoints. She stays on XLwear as primary.

**Why:** Afeefa is XLwear-lead-architect per memory; pulling her into Onsite full-time slows XLwear (revenue path) without speeding Onsite (already has Shailendra). Architecture review is high-leverage; full pair-build is not.

**Risk:** If Shailendra hits an architecture decision he can't make, blocks for Afeefa's next slot. Mitigation: Dhruv is the architectural decider; Afeefa is the second pair of eyes.

**If Dhruv overrides → full pair-build:** XLwear slips. Recommend not.

---

## D6 — Ship all 7 training modules NOW; M3-M7 run RAG-explain mode until Akshansh API lands

**Decision:** Build phase machine wrapper + all 7 modules in Sprint 7+8. Modules 1 (Dependencies) and 2 (Progress) get full demo-fire-tool flow because those endpoints exist. Modules 3-7 (RA Bills, BOQ, DPR, Attendance, Materials) demo via RAG-only "explain mode" — bot shows the user what the field/screen looks like in Onsite (via screenshots embedded as RAG sources) and walks through it, but doesn't fire a creating tool. When Akshansh's API ships, we add `is_demo_action_enabled` flag per module and flip M3-M7 over without rewriting the phase machine.

**Pushback on Dhruv's lean (defer M3-M7):** Deferring 5 modules cuts the training product's value 70%. Onsite's "50% faster onboarding" sales claim needs the full module set. RAG-explain is a 1-day-per-module variant of the phase machine, not a new product. Ship all 7.

**Why:** Sales narrative integrity. Sumit walks customers through "your team learns RA bills in 8 minutes via voice" — having only 2 modules in production undermines the demo.

**Risk:** RAG-explain mode quality depends on RAG corpus quality. Mitigation: pre-flight all 7 module RAG queries against the seeded corpus in Sprint 8 QA before SME review.

**If Dhruv overrides → defer M3-M7:** Cut sales narrative to "dependencies and progress training only" until Akshansh ships. Real cost: lose 1-2 demos / month for 6-12 weeks.

---

## D7 (forced by me — not in §5) — Sprint 2 voice does NOT lift the QH Modal bridge directly

**Decision:** Onsite-hub is Next.js on Vercel. QH `198dc29` is a Modal Python app. We **cannot** copy-paste the bridge. Voice for Onsite-hub will be either (a) a Next.js Edge WebSocket route proxying to Gemini Live / OpenAI Realtime directly OR (b) a separate Modal service that onsite-hub frontend talks to.

**Choice:** Option (a) for MVP. Next.js Route Handlers support WebSocket upgrade via `nextjs/serverless-websocket` or via the `node:ws` adapter on a long-lived serverful runtime. Vercel doesn't host long-lived WS, so we need to deploy the WS server **separately on Modal or Fly.io or Render**, and keep the rest of onsite-hub on Vercel.

**Why we deviate from dispatch §4:** The dispatch says "deploy QH 198dc29 Gemini bridge to onsite-hub" — that's a category error. Two different runtimes. Flagging this now so we don't burn 2 days finding out in Sprint 2.

**Risk:** Adds a second deploy target. Mitigation: lift QH's Modal app verbatim, swap kickoff prompt + tools, point onsite-hub WS client at the new Modal endpoint. Total real lift: ~1.5 days.

**If Dhruv overrides → keep voice in onsite-hub Vercel:** We hit Vercel's serverless function 60-second cap. Dead-on-arrival for 30-min voice sessions.

---

## D8 (forced) — Per-tenant voice minute cap from day 1

**Decision:** Hard cap each tenant at **30 voice-minutes/day** (Free) or **200 voice-minutes/day** (Pro), enforced at WS session start via Supabase counter. Reset at 00:00 IST. Configurable per-tenant override (Onsite admin can grant).

**Why:** Dispatch's $40K/month cost projection at 10K customers is pure runway risk. Without a cap, one runaway customer (forgot to hang up) = $50-100 / day burned. Cap from day one or get bitten.

**Risk:** Legitimate heavy users hit cap. Mitigation: friendly "You've hit today's voice budget — keep going in text mode" + admin override.

**If Dhruv overrides → no cap:** Add bill monitoring + alert on $X/day spend. Higher operational burden.

---

## D9 (forced) — Sprint 1 (RAG) must complete before Sprint 2 (Voice) starts wiring tools

**Decision:** Drop the §6 "Sprints 1 & 2 in parallel" overlap. RAG completes first (Day 2-5). Voice integration starts Day 6 with RAG-as-tool already wired. Saves the Sprint 3 ("RAG-in-voice") integration sprint entirely.

**Pushback on dispatch §6:** Parallel-build of RAG + voice means voice starts blind to whether `search_knowledge_base` exists. Sprint 3 then exists only to bridge the two. Sequential build = -2 days of integration debt.

**Why:** Tool calling in voice loop is identical to tool calling in text loop (per HireAI report §5 + §6). If RAG is wired into the text bot in Sprint 1, voice picks it up free in Sprint 2.

**Risk:** Total elapsed time +1 day. Acceptable for -2 days of rework.

**If Dhruv overrides → keep parallel:** Schedule still ships; just adds Sprint 3 back to roadmap.

---

## Summary table — Open decisions resolved

| # | Decision | Diverges from Dhruv's lean? |
|---|---|---|
| D1 | Single `/task-bot` UI, modular `/api/task-bot/*` backend | Aligned |
| D2 | Notion = ongoing mirror, NO auto-retire | **Push back** (no 90-day retire) |
| D3 | Build our own ticket queue + webhook-out adapter | **Aligned with tweak** (don't wait 48h) |
| D4 | Onsite pays prod API keys; AIwithDhruv pays dev/staging | Aligned |
| D5 | Shailendra leads; Afeefa 3× 1-hr architecture review | Aligned |
| D6 | Ship all 7 modules now; M3-M7 run RAG-explain mode | **Push back** (don't defer 5 modules) |
| D7 | Voice = separate Modal service; onsite-hub stays Vercel | Forced (dispatch had a category error) |
| D8 | Per-tenant voice minute cap from day 1 | Forced |
| D9 | RAG sequenced before voice; cut Sprint 3 integration sprint | Forced (overrides §6 sequencing) |

---

## Next step

After Dhruv signs off, dispatches go out:
1. `dispatch-sprint-1-rag.md` → fresh Claude session for Shailendra
2. `dispatch-sprint-2-voice.md` → fresh Claude session for Shailendra (after Sprint 1 commit lands)
3. `dispatch-sprint-5-support.md` → fresh Claude session for Atlas

Per `feedback_never_spawn_coding_agent`, Angelina does **NOT** invoke coding agents from her session. Dhruv paste-launches each dispatch.
