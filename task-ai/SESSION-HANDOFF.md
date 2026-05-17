# Session Handoff — 2026-05-17 (end of day)

> Read this when resuming after `/compact`. Has the compact prompt + full TODO list + current state.

---

## 📋 THE COMPACT PROMPT (paste after `/compact`)

```
Resume work on Onsite Task AI. We hit context limit so reload state from disk.

READ FIRST (in order):
1. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/CLAUDE.md
2. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/MEMORY.md
3. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/SESSION-HANDOFF.md (this file)
4. /Users/apple/.claude/projects/-Users-apple-Aiwithdhruv-AI-Development-Claude/memory/reference_supabase_cli_migrations.md

CURRENT STATE: Bot has 9 tools live in production-style testing. Audit Layer writes to Supabase `xcvrdjhnvngfzczumquq.task_ai_actions`. Chrome extension auto-bridges token. Premium light UI shipped. Last commits: 5e1332f (onsite-hub), 979bdab (Onsite).

WHAT'S LEFT FOR DEMO (from SESSION-HANDOFF.md):
- P0 critical bugs (4 items)
- P1 demo-quality (4 items)
- P2 nice-to-have (rest)

START WITH: P0 #1 (fix progress card task name), then proceed through P0 → P1 → P2 in order. Do NOT over-engineer. The bot works — we are polishing for Sumit's demo.

KEEP DOING:
- Haiku 4.5 as default, Sonnet 4.6 swappable via env var (DO NOT change this)
- Push to BOTH repos correctly (code → onsite-hub, docs → Onsite/task-ai)
- Use Supabase CLI for any migrations (PAT in ~/.aiwithdhruv-secrets as SUPABASE_ACCESS_TOKEN_TASK_AI)
- Test through actual chat UI, not just curl
- Update STATE.md and SESSION-HANDOFF.md after each major change

DON'T:
- Don't ask which repo (memory has the split)
- Don't ask if it's safe to push (both repos are private, verified)
- Don't ask for Supabase access (CLI is set up)
- Don't deploy to Vercel without explicit Dhruv approval
- Don't add features outside the TODO without asking

Start with P0 #1. Tell me when each item is shipped + verified.
```

---

## 🎯 TODO — Sorted by priority

### P0 — Critical bugs blocking the demo (fix first)

1. **Progress card shows "task" instead of real task name**
   - When `record_task_progress` succeeds, Onsite returns `monkey_patch_billing_activity_name` but it's empty/null sometimes
   - Fix: after a successful progress write, follow up with a lookup of the BA name via existing list_tasks data OR a `detail/billingactivity/<id>` call
   - Files: `src/app/api/task-bot/route.ts` — `record_task_progress` handler
   - Done when: progress card shows "Electrical panel Setup" not "task"

2. **Bot hallucinates "deleted!" without firing the tool (root cause, not just guard)**
   - Current state: guard catches it but bot still tries
   - Fix: when Claude returns plain text after a destructive intent in user message, FORCE a re-call by appending a synthetic user message: "You said you would [action] but didn't call the tool. Call it now or report the actual error."
   - Loop continues, Claude has to either fire tool or admit failure
   - Done when: 5 deletes in a row all show audit rows, zero fake-success replies

3. **List dependencies "between A and B" doesn't filter by both names**
   - Current: bot calls `list_dependencies` with no ba filter, returns ALL deps
   - Fix: have the bot resolve A and B to BA IDs first via `list_tasks`, then call `list_dependencies` with `ba_id` filter, then post-filter the response to only deps where both BA IDs appear
   - Done when: "show deps between Electrical panel Setup and Fixture installation" returns just the matching pair

4. **Multi-action requests sometimes only fire one tool**
   - Currently: "Delete A. Then delete B." → only one delete fires
   - Fix: after a successful destructive tool call, check if user message contained multiple destructive verbs; if so, prompt Claude with "did you complete all requested actions?" — forces second call
   - Done when: "delete X. then delete Y." fires both tools, both audit rows appear

### P1 — Demo quality (do after P0)

5. **Streaming reply for perceived speed**
   - Current: user waits ~6-12s with bouncing dots, no feedback on what bot is doing
   - Fix: stream the second-Claude-call's text response token-by-token so user sees the reply form in real time
   - Files: `route.ts` (return SSE), `page.tsx` (consume stream)
   - Done when: text appears character-by-character, latency feels half what it is

6. **Live "thinking" status with tool name**
   - Show: "Looking up Soul Space..." or "Finding Electrical panel Setup..." or "Calling Onsite API..."
   - Better than generic dots
   - Done when: loading indicator shows the current tool being called

7. **Hindi voice input (hi-IN)**
   - Currently hardcoded `lang = 'en-IN'`
   - Add: small toggle in input bar EN ↔ HI, store preference in sessionStorage
   - Done when: clicking HI lets user dictate in Hindi and the text appears in input

8. **Better suggestion cards on first turn**
   - Current suggestions use generic examples
   - Replace with: 4 cards that match exact demo flow:
     1. "Show me dependencies on Electrical panel Setup in Soul Space"
     2. "Make Fixture installation depend on Electrical panel Setup, FS no lag"
     3. "Log 5 numbers of progress on Electrical panel Setup"
     4. "Plastering ko brickwork ke baad start karna hai" (Hindi mix)
   - Done when: clicking any card runs the full demo flow

### P2 — Polish + persistence (do after P0+P1)

9. **Opt-in chat persistence (`task_ai_messages` table)**
   - New Supabase table with: `(id, session_id, company_id, user_id, role, content, created_at)`
   - UI: small "💾 Save chat" toggle in header (off by default)
   - When on: every send/receive writes a row
   - Privacy: scoped by company_id with RLS, user can delete via /task-bot/history
   - Apply migration via Supabase CLI (already have access)
   - Done when: toggle persists, rows appear in Supabase when on, no rows when off

10. **Admin view at `/task-bot/admin`**
    - Read-only dashboard reading `task_ai_actions`
    - Show: total actions today, top tools, success rate, p95 latency, errors
    - Auth: gate to specific user IDs (Dhruv only for now)
    - Done when: visiting URL shows the metrics, refreshes every 30s

11. **Undo last destructive action**
    - Button on dependency/progress cards: "Undo"
    - Implementation: look up the most recent successful `task_ai_actions` row matching the user, call inverse
    - Done when: clicking "undo" on a dependency_created card actually deletes it

### P3 — Reliability hardening (do after P0+P1+P2)

12. **Smarter primary-company detection**
    - Cache the company that owned the LAST successful action per user in sessionStorage
    - Bot prefers that company on next turn for project lookups
    - Done when: after working with Dhruv Construction once, bot doesn't fan across all 23 next turn

13. **Better mobile responsiveness**
    - Test on 375px width (iPhone SE)
    - Tap targets ≥44px
    - Cards readable
    - Done when: full demo runs without horizontal scroll on 375px

14. **Error cards: add Retry button**
    - When an action fails, the error card should have "Try again" button
    - Re-sends the previous user message with same args
    - Done when: clicking retry on a 500 error re-fires the tool

---

## 📦 What's already SHIPPED today (don't redo)

| Capability | Commit |
|------------|--------|
| 9 tools (deps + tasks + progress) | `b97460b` |
| Activity Layer (Supabase + JSON logs) | `00a4c9e`, `b372585` |
| Premium light UI | `adffd87` |
| Cross-company project fan-out | `a6243c8` |
| Hallucination guard (server-side) | `5e1332f` |
| Chrome extension auto-auth | `8637f28` |
| Supabase CLI workflow + memory note | (memory file) |

---

## 🚫 What NOT to do

- Don't deploy to Vercel (Dhruv said "later")
- Don't add features outside this TODO without asking
- Don't change the default model (Haiku 4.5 stays default, Sonnet swappable)
- Don't break the Chrome extension auto-auth flow
- Don't ask Akshansh for API specs (we've discovered enough endpoints to ship)
- Don't bloat the UI with too many controls — the chat-first feel is the value

---

## ✅ Test commands you can verify each fix with

| Fix | Test command (paste in bot) |
|-----|------------------------------|
| P0 #1 | "Add 3 numbers of progress on Electrical panel Setup in Soul Space" — card should show real task name |
| P0 #2 | "Delete dependency X" (use real ID) → check audit log for real row |
| P0 #3 | "Show deps between Electrical panel Setup and Fixture installation" → returns 1 (or 0 if cleaned) |
| P0 #4 | "Delete A. Then delete B." → check audit log shows 2 delete rows |
| P1 #5 | Visual: text streams character-by-character |
| P1 #6 | Visual: loading shows tool name |
| P1 #7 | Click HI toggle → speak Hindi → input gets Hindi text |
| P1 #8 | Click each suggestion card → flow completes |
| P2 #9 | Toggle save → send message → verify Supabase task_ai_messages row |
| P2 #10 | Visit /task-bot/admin → see metrics |
| P2 #11 | Click "Undo" on dep card → dep gone in Onsite |

---

## 🔗 References

- Code repo: https://github.com/aiagentwithdhruv/onsite-hub (PRIVATE)
- Docs repo: https://github.com/aiagentwithdhruv/Onsite/tree/main/task-ai (PRIVATE)
- Supabase project: https://supabase.com/dashboard/project/xcvrdjhnvngfzczumquq
- Live URL: http://localhost:3001/task-bot
- Onsite API token: see `~/.aiwithdhruv-secrets`
- Supabase PAT (task-ai): `SUPABASE_ACCESS_TOKEN_TASK_AI` in `~/.aiwithdhruv-secrets`

---

## 🎬 Demo target

After P0 + P1 + P2 #9 ship, the demo is:

> Sumit (on phone, in Onsite app): *"Watch this."*
> [Opens Onsite AI from in-app button]
> [Says in Hindi]: *"Soul Space mein Electrical panel Setup ke baad Fixture installation start hona chahiye"*
> [Bot, in 4 seconds, with streaming reply]: *"Theek hai — Electrical panel Setup pehle finish hoga, phir Fixture installation. FS dependency banata hoon."* [Green card appears]
> [Sumit switches to Onsite UI tab]: FS arrow live on Gantt
> [Sumit shows audit log]: every action timestamped, company-scoped
> [Sumit, to customer]: *"This is the AI feature. Procore doesn't have this. Powerplay doesn't have this."*

Demo. Closes deals. Built today.
