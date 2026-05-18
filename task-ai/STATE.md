# State — Onsite Task AI

> Living document. Last source of truth for "what works right now."

**Last updated:** 2026-05-19 (batch 21 — reverted to Haiku default after Gemini failed real-world Arohan test)

---

## Capability Matrix

| Capability | Status | Last verified | Notes |
|------------|--------|--------------|-------|
| Chat UI renders | ✅ Live | 2026-05-17 | localhost:3001/task-bot |
| Setup screen (token + env) | ✅ Live | 2026-05-17 | sessionStorage persistence |
| Voice input (en-IN) | ✅ Built | Not tested live | Web Speech API native |
| Voice input (hi-IN) | ❌ Not built | — | Phase 2 |
| Voice output (TTS) | ❌ Not built | — | Phase 3 |
| Conversation memory in-session | ⚠️ Partial | 2026-05-17 | Text history sent, but tool_call history not preserved |
| Bearer token auth | ✅ Live | 2026-05-17 | Validated against real prod JWT |
| Sign out (clear token) | ✅ Live | 2026-05-17 | Clears sessionStorage |
| `create_task_dependency` tool | ✅ Production-verified | 2026-05-17 | 2 real deps created in Soul Space |
| `record_task_progress` tool | ✅ Production-verified | 2026-05-17 | 1 progress entry created on Electrical panel Setup |
| `list_projects` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `list_tasks` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `list_subactivities` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `update_task_dependency` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `delete_task_dependency` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `add_task` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `update_task` tool | ❌ Not built | — | Phase 2, blocked on Onsite API spec |
| `mark_task_started` tool | ❌ Not built | — | Endpoint observed in Network; Phase 2 |
| Error messages — English | ✅ Live | 2026-05-17 | Claude rephrases Onsite errors |
| Error messages — Hindi | ❌ Not built | — | Phase 2 (system prompt update) |
| Multi-tenant isolation | ✅ Structural | 2026-05-17 | No state → can't leak |
| Deployed to Vercel | ❌ Local only | — | Push pending Dhruv approval |
| Embedded in Onsite app | ❌ Not built | — | Phase 3 |
| Auto-auth via SSO | ❌ Not built | — | Phase 3 (postMessage from parent) |
| Audit log | ❌ Not built | — | Phase 3 |
| Rate limiting | ❌ Not built | — | Phase 3 |
| Cost tracking per customer | ❌ Not built | — | Phase 3 |
| Integration tests | ❌ Not built | — | Phase 2 (vitest + testapi.onsiteteams.in) |
| LLM eval suite | ❌ Not built | — | Phase 2 |
| Monitoring dashboard | ❌ Not built | — | Phase 3 |

---

## Production Data Created During Testing

(Living log — clean up later if Dhruv requests)

### 2026-05-17 — Soul Space Project, Wiring Installation section

| Type | ID | Notes |
|------|-----|-------|
| Dependency | `d374d749-0270-40fb-80c1-a672e9824341` | Electrical panel Setup → Fixture installation, FS, lag 0 |
| Dependency | `9ba0c664-c188-41f4-832e-93384b67625f` | New Electric Test → Electrical panel Setup, FS, lag 0 |
| Progress entry | (id in response) | +3 numbers on Electrical panel Setup, "Test progress entry from AI bot" |
| Task created | `1b8f2e76-bdd6-44c9-82c9-a8082aa5b243` | "New Electric Test" — created manually by Dhruv in Onsite UI (not by bot) |

These can be deleted in Onsite UI if needed for clean state.

---

## Code Locations (current)

| File | Lines | What |
|------|-------|------|
| `Onsite/onsite-hub/src/app/task-bot/page.tsx` | ~380 | Chat UI |
| `Onsite/onsite-hub/src/app/api/task-bot/route.ts` | ~250 | Backend API route |
| `Onsite/onsite-hub/src/components/AppShell.tsx` | +3 | PIN auth bypass |

---

## Env Vars (in onsite-hub/.env.local)

| Var | Status | Notes |
|-----|--------|-------|
| `OPENROUTER_API_KEY` | ✅ Set | Used for Claude calls |
| (No new vars added) | — | task-ai reuses onsite-hub's env |

---

## Open Decisions Awaiting Dhruv

1. **Push onsite-hub to GitHub?** No git remote configured. Pending approval.
2. **Deploy to Vercel?** OPENROUTER_API_KEY already in Vercel env. Just needs push + connect.
3. **Send Akshansh API spec request?** Draft is in ROADMAP § Phase 2.
4. **Pricing model with Sumit?** Defer until Phase 2 ships.

---

## Open TODO

(None as of 2026-05-17 evening — all batches 1-7 shipped. Next: live testing → polish.)

## Recent Changes

- **2026-05-19 (batch 21)** — Reverted default to Haiku 4.5 (commit `01f3757`).
  - Gemini 3 Flash Preview failed real Arohan project test: first workorder probe returned empty → Gemini gave up + told user "no active workorder" instead of trying fan-out path. Mocked 14-test A/B (14/14 pass) didn't catch this real-world failure mode.
  - **Active routing**: Haiku 4.5 default → Sonnet 4.6 escalation. Same as pre-batch-20.
  - **Cost trade-off accepted**: ~8× more per token vs Gemini, but correctness > cost on a demo-stage product.
  - A/B scripts still in repo for future re-testing. Gemini accessible via `TASK_BOT_MODEL` env var if needed.

- **2026-05-19 (batch 20)** — 3-tier model routing locked (commit `d66f893`).
  - **A/B-tested across 14 prompts** (`task-ai/scripts/3way-haiku-g2-g3.mjs`):
    - Gemini 3 Flash Preview: 14/14, 8× cheaper than Haiku ✅ NEW DEFAULT
    - Haiku 4.5: 14/14, baseline — now escalation tier
    - Sonnet 4.6: 14/14, 3× more expensive — now final retry only
    - Gemini 2.0 Flash: 11/14 (fails Hindi + memory recall) — REJECTED
  - **Escalation ladder**: Gemini fails → Haiku → Sonnet. Hallucination guard + completion check route tier-by-tier instead of jumping straight to Sonnet.
  - **Expected cost cut**: ~8× on top of Haiku-first commit. Total ~50× vs original Sonnet-heavy routing.
  - **Override path**: `TASK_BOT_MODEL` env. If Gemini preview SKU gets deprecated, flip to Haiku in one var.

- **2026-05-19 (batches 15-19)** — Bot reliability + product polish:
  - `3fa0238` — Three new tools: add_task / add_subactivity / search_tasks. record_task_progress now returns progress_history_id. New RULE 0.5 (remember last action).
  - `a1e1f13` — Multi-project disambiguation (RULE 0.6 + ambiguous flag in list_projects result). App-version headers attempted on add_task/add_subactivity.
  - `3978777` — Optimistic sidebar insert on "+ New chat" (no refresh needed). Honest error message instead of looping retries.
  - `3ce8c08` — Widened progress_history_id field search across 7 response shapes × 11 field-name variants. Server-logs response shape when nothing matches.
  - `8597e16` — list_progress_history tool. New RULE 0.56 forbids fake -N delete reversals. Suppressed red 400 card for server-gated features.
  - `74e98e2` — Plan-tier upsell language for gated endpoints ("Upgrade to Enterprise / add in Onsite app" instead of API jargon).
  - Chrome extension v0.2.0: manifest now whitelists `*.trycloudflare.com` and `*.ngrok.io` so tunnel-based testing works without manual token paste.

- **2026-05-19 (batch 14)** — Desktop polish round 3 (commits `4030087` + `7b51811`):
  - **AT A GLANCE rail switched to Option B** — four lifetime "via AI" tiles (Time saved, Deps, Progress logs, Actions) with a one-line "This chat · N turns" footer. All four read the same scope so it tells one consistent story.
  - **myStats live-refresh fix** — was only refreshing on dashboard view, so rail stayed at 0. Now refreshes on auth, on view change, AND after every tool call. Numbers bump up live as user works.
  - **Sidebar search** — `Search chats…` input filters Recent chats by title + preview. Counter shows matched/total, clear button, empty state.
  - **Desktop header cleanup** — removed duplicate clock (history) + sign-out + new-chat icons from chat & dashboard headers on lg+ (sidebar already has them). Mobile keeps them all.

- **2026-05-19 (batch 13)** — Right-rail tap-to-paste tips (commit `5dbe648`):
  - Project-aware tip list — switches between "For <project>" (when anchored) and "Try one of these" (generic onboarding).
  - Each tip is a button that pastes into the chat input + focuses the textarea with caret at end. Doesn't auto-send.
  - Pro Tip card at bottom (chained-command example) also tap-to-paste.

- **2026-05-19 (batch 12)** — Living logo + sidebar rename/delete + Best Tips card (commit `70fec00`):
  - Sparkle avatar gently breathes + glows + twinkles (respects prefers-reduced-motion).
  - Desktop sidebar chat rows get hover-reveal rename (pencil) + delete (trash). Inline rename input + Yes/No confirm for delete.
  - Dashboard's "Continue a past chat" removed on desktop (sidebar shows the list); replaced with a 2×2 "Best tips" card grid. Mobile keeps the past-chat list.

- **2026-05-19 (batch 11)** — Desktop 3-column layout shipped (commit `77470ee`):
  - Left sidebar (272px, lg+, persistent): brand · "+ New chat" · Dashboard/Chat nav · Recent chats list · user card.
  - Main pane (flex-1): dashboard turns into 4-up stat grid + 4-column suggestion grid; chat keeps a centered 3xl reading column inside.
  - Right context rail (280px, chat only, lg+): project anchor · stats · tips.
  - Mobile (< lg) renders single-column exactly as before.

- **2026-05-19 (batch 10)** — get_project_stats + hallucination guard refinements (commits `c6f98d0` / `38f5435`):
  - **Hallucination guard tightened** — was misfiring on innocent "tell me tasks" queries (regex matched "12% done" in list output). Now requires first-person action claims ("✅ Done!", "I created", "Successfully logged") to trigger a forced recall.
  - **Stat card labels** — `Total / Leaf / With Deps / Without Deps` → `Main / Sub / Leaf / With Deps` (matches Onsite UI's task tree).
  - **Multi-workorder aggregation** — get_project_stats now tries `/list/progressorder` and `/list/workorder` first, falls back to single-workorder via `/detail/progressorder`. Sums tasks/leaves/deps across every workorder for the project. Card title shows ` · N workorders` when >1.

- **2026-05-17 (batch 9, post-compact)** — End-to-end chat-screen rebuild matching the design package (oniste-task-ai bundle from Claude Design / screens-chat.jsx):
  - DependencyCard: emerald-gradient header, 22px gradient row badges (deep-violet → mid-violet), vertical emerald→violet connector with the type pill riding it, footer with copy + Undo pill chips
  - ProgressCard: violet-gradient header, sectioned TASK / ADDED+TOTAL grid / italic NOTE on slate-50 bg
  - TaskStatsCard: full primary-gradient header, 2×2 stat grid with internal slate dividers (was tinted ring tiles), progress-mix bar rows
  - ErrorCard: rose-gradient header + "!" badge + rose pill "Try again"
  - Chat header: back · sparkle · "Onsite AI · <Project>" one-line title + LIVE pill + auto-saved + Sandbox/Live env chip + 36px icon-btns
  - Task tree: parent rows get 90deg violet→pink gradient bg + right-aligned duration tag; sub-rows show right-aligned 🔗N + N% via new `extractTaskMeta()` parser (`🔗N · X% · Yd` markers from backend)
  - Suggested-next chips: `.suggest-chip` style — gradient soft bg, deep primary text, violet border, right-arrow icon, 12.5px
  - Input bar: pill style, 40px circular icon-btns + EN/हिं middle chip + textarea (rounded-[20px]) + gradient circular send button
  - Thinking indicator: sparkle + 3-dot bubble (rounded-bl-md) with rotating stage label on the side
  - Setup screen: glowing sparkle hero, segmented Sandbox/Production with status dots, dark code-block token-help reveal, Shield trust line
  - Welcome block: keeps bot intro bubble; adds "Resume a past chat" row + "Try one of these" labeled 2×2 grid with tinted icon backgrounds
  - Commit: onsite-hub@5c11e02

- **2026-05-17 (batch 7)** — All 6 open TODOs shipped in one batch:
  - AI auto-suggests chat rename (banner above latest reply when project is clear + title is null)
  - Welcome screen shows top 3 recent chats as "Resume" cards; active chats get a "Related past chats" chip row when keywords match
  - New `get_project_stats` tool + `task_stats` card with 2x2 stat grid and progress bars
  - Direct Anthropic API support gated on `ANTHROPIC_API_KEY` env (OpenRouter fallback)
  - System prompt drilled with leaf-vs-parent check before proposing dep chains
  - JSONL training-data export at `/api/task-bot/export-training-data` + admin button (positive-feedback or long-clean sessions only)

- **2026-05-17 (post-compact, batch 6)** — Collapsible tree + server cache:
  - MsgText now parses outline into a tree, renders with click-to-expand chevrons
  - Trees with >20 total nodes start fully collapsed (parents-only view)
  - Collapsed parents show "· N items · M total" inline preview
  - 5-min in-process cache for list_companies / projects / tasks
  - Cache auto-invalidates on any successful create/update/delete
  - Saves Onsite API calls + LLM tokens on repeated lookups

- **2026-05-17 (post-compact, batch 5)** — Hierarchical tree + dep enrichment:
  - list_tasks builds full parent-child tree (sorted by order_index), emits `outline` field
  - Each task line includes inline `🔗 N deps · X% done · Yd` markers
  - Aggregate counts: total_leaves, total_with_dependencies, total_without_dependencies
  - list_dependencies now fans out across all 25 companies (was hardcoded to first only — root cause of "0 deps" hallucination)
  - Tries multiple response shapes: taskdependencies / task_dependencies / dependencies / data
  - New delete_task_progress tool (Onsite UI supports it; bot now can too)
  - Smart model routing: Sonnet 4.6 on action-verb + entity-name messages, Haiku 4.5 elsewhere

- **2026-05-17 (post-compact, batch 4)** — Chat rename + session-scoped context:
  - New table `task_ai_session_meta` (session_id, user_id, title, project_context) — migration 004
  - History drawer: hover → pencil icon → inline rename
  - Saved title becomes bot's system-prompt anchor: "User named this chat X — treat unspecified references as X"
  - Header shows session title in violet when set

- **2026-05-17 (post-compact, batch 3)** — Thumbs feedback for training data:
  - Each assistant message has 👍/👎 below it (after first turn)
  - New `/api/task-bot/feedback` writes to `task_ai_messages` with `feedback` column
  - Smoke-tested: row writes confirmed via curl + Supabase REST GET
  - Click → "Thanks — your 👍 helps the AI learn."
- **2026-05-17 (post-compact, batch 2.5)** — Admin dashboard at `/task-bot/admin`:
  - 24h totals, success rate, p50/p95 latency
  - Per-tool breakdown with success-rate bars + avg latency
  - Last 20 errors with codes + timestamps
  - Gated by `TASK_AI_ADMIN_USERS` env allowlist (open if unset)
  - 30s auto-refresh
- **2026-05-17 (post-compact, batch 2)** — UI polish + P1/P2/P3 ship:
  - New suggestion cards with custom SVG icons + colored accents
  - Glassmorphism on setup screen + decorative background blurs
  - ThinkingIndicator with pulsing avatar + 5-stage rotating status
  - Mobile breakpoints — no horizontal scroll on 375px
  - Hindi voice toggle (EN ↔ हिं) next to mic — stored in sessionStorage
  - Header SAVE toggle for opt-in chat persistence
  - Undo button on dependency cards (uses bot multi-turn loop)
  - Retry button on error cards
  - New `/api/task-bot/chat-log` endpoint writes to `task_ai_messages` (Supabase, RLS-protected, service-role-only)
  - Migration 003: `task_ai_messages` table with feedback column, training-data ready
- **2026-05-17 (post-compact)** — P0 #2 + #4: force re-call on hallucinated success + multi-action completion check. Guard injects synthetic user message demanding Claude either fire tool or admit failure. Max 1 forced recall.
- **2026-05-17 (post-compact)** — P0 #3: `list_dependencies` pair-filter ("between A and B"). Tool spec accepts `ba_id_2`; system prompt instructs bot to resolve both names via `list_tasks` first.
- **2026-05-17 (post-compact)** — P0 #1 fix: progress card now resolves real task name. Tries multiple response paths first (`monkey_patch_billing_activity_name`, nested `billing_activity.name`, etc.); if all empty, follows up with `GET /apis/v3/detail/billingactivity/<id>` using the `billing_activity_id` from the response. Final fallback: "Task" string (was: always "task" lowercase when patch field was empty).
- **2026-05-17 02:00** — `location_id` made optional in `record_task_progress` tool (was breaking UX). Default to empty string.
- **2026-05-17 01:30** — End-to-end test through chatbot UI successful (after fixing token misread).
- **2026-05-17 01:00** — Initial MVP shipped (page + API route + AppShell bypass).
- **2026-05-17 00:30** — Project folder created with PRD/HLD/LLD/ROADMAP.
