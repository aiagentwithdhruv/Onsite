# Resume Prompt — Onsite Task AI (May 19, 2026)

> Copy the fenced block below after running `/compact`. Self-contained.

---

```
Resume work on Onsite Task AI. Demo-ready as of 2026-05-19.
Owner: Dhruv Tomar (AI Builder at Onsite). Multi-tenant, chat-first
NL interface to Onsite's construction APIs.

═══════════════════════════════════════════════════════════════
READ FIRST (in order — full project state is here)
═══════════════════════════════════════════════════════════════

1. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/CLAUDE.md
   Master AI context.
2. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/STATE.md
   Synced to batch 19 (today). Has commit hashes for every batch.
3. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/MEMORY.md
   Hard-earned learnings.
4. /Users/apple/.claude/projects/-Users-apple-Aiwithdhruv-AI-Development-Claude/memory/project_onsite_task_ai.md
   Cross-session memory — toolset, rules, UX commitments, TODO.

═══════════════════════════════════════════════════════════════
REPO STATE — both clean, both pushed
═══════════════════════════════════════════════════════════════

aiagentwithdhruv/onsite-hub @ 74e98e2  (code)
aiagentwithdhruv/Onsite    @ 39f1655  (docs + chrome ext zip)

Code path: Onsite/onsite-hub/src/app/task-bot/
           Onsite/onsite-hub/src/app/api/task-bot/
Docs path: Onsite/task-ai/

═══════════════════════════════════════════════════════════════
WHAT'S WORKING (do NOT rebuild)
═══════════════════════════════════════════════════════════════

✓ 14 tools wired: list_companies / list_projects / list_tasks /
  list_subactivities / list_dependencies / list_progress_history /
  create_task_dependency / update_task_dependency /
  delete_task_dependency / record_task_progress /
  delete_task_progress / get_project_stats / add_task /
  add_subactivity / search_tasks

✓ Multi-project disambiguation — list_projects returns ambiguous:true
  + exact_name_duplicates[] when names collide across companies.
  RULE 0.6 forbids silent picks.

✓ record_task_progress returns progress_history_id so bot can delete
  the just-created entry without re-asking. Casts wide net across
  7 response shapes × 11 field-name variants.

✓ list_progress_history returns individual entries with UUIDs for
  proper deletes. RULE 0.56 forbids fake -N reversal "deletes".

✓ add_task / add_subactivity hit Onsite's server gate ("This feature
  has been upgraded, Please Update App!"). Bot replies with PRODUCT
  upsell language per RULE 0.55 — "Upgrade to Enterprise" or "Add
  directly in Onsite app" — no API/endpoint jargon. Red 400 card
  suppressed for this specific error.

✓ Desktop 3-column layout (lg+): sidebar (brand, +New chat, nav,
  search, recent chats with hover-reveal rename/delete, user card)
  + main + right rail (project anchor, AT-A-GLANCE Option B lifetime
  "via AI" stats with live refresh after every tool call, tap-to-
  paste project-aware tips, Pro Tip card).

✓ Mobile single-column unchanged.

✓ Living sparkle logo (breathe + glow + twinkle, respects
  prefers-reduced-motion).

✓ Sidebar search filters recent chats by title + preview.

✓ Optimistic "+ New chat" — new entry appears in sidebar
  immediately, no refresh needed.

✓ Chat persists on refresh — two-step restore + restoreStartedRef
  ref-based gating prevents cancel races.

✓ Hallucination guard catches first-person action claims without
  tool calls. Doesn't misfire on "12% done" in list output.

✓ Chrome extension v0.2.0 — auto-injects token from
  web.onsiteteams.com. Whitelists localhost, vercel.app, *.tryclouflare.com,
  *.ngrok.io. Zip at Onsite/task-ai/onsite-ai-helper-v0.2.0.zip
  (in repo) + ~/Downloads/onsite-ai-helper-v0.2.0.zip (local).

═══════════════════════════════════════════════════════════════
HARD-LOCKED RULES (system prompt)
═══════════════════════════════════════════════════════════════

RULE -1   User numbers = list positions, not IDs.
RULE 0    Never ask users for UUIDs.
RULE 0.5  Remember progress_history_id / dep_id from prior turns.
RULE 0.55 Plan-gated features → product upsell language.
RULE 0.56 Never fake delete with negative entry — use list_progress_history.
RULE 0.6  Ambiguous project names → ASK, never pick silently.

═══════════════════════════════════════════════════════════════
LIVE TODO (priority order)
═══════════════════════════════════════════════════════════════

1. Ask Akshansh for the correct endpoint/headers for add_task and
   add_subactivity (currently 400 "feature has been upgraded").
   Once known: flip one line, bot creates tasks for real.

2. Ask Akshansh for the endpoint that lists ALL workorders of a
   project (currently we guess at /list/progressorder and /list/workorder,
   both unconfirmed). Without this, multi-workorder projects may
   silently miss tasks.

3. Vercel deploy — pending Dhruv go-ahead after Akshansh discussion.
   Env vars needed:
     TASK_AI_SUPABASE_URL=https://xcvrdjhnvngfzczumquq.supabase.co
     TASK_AI_SUPABASE_SERVICE_KEY=<paste>
     OPENROUTER_API_KEY=<already in Vercel>
     ANTHROPIC_API_KEY=<optional, gates direct path>
     TASK_AI_ADMIN_USERS=<optional, gates /task-bot/admin>

4. Auth path for end users (Dhruv's product direction): embed inside
   Onsite app at web.onsiteteams.com. User logs in with mobile + OTP
   → redirected to Onsite AI if entitled. Needs Akshansh involvement.

5. Tester kit ready to share once tunnel/Vercel sorted:
   - Zip: ~/Downloads/onsite-ai-helper-v0.2.0.zip
   - Tunnel URL last issued: velocity-mls-boss-swim.trycloudflare.com
     (rotates on terminal close — regenerate with
      `cloudflared tunnel --url http://localhost:3001`)

6. Hook training-data export to a scheduled job (currently manual
   button on /task-bot/admin).

═══════════════════════════════════════════════════════════════
DEV WORKFLOW
═══════════════════════════════════════════════════════════════

Start dev server:
  cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub"
  pkill -f "next dev" 2>/dev/null; sleep 1
  nohup npm run dev -- --port 3001 > /tmp/onsite-hub-dev.log 2>&1 &
  disown

Smoke check:
  curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3001/task-bot

TS check:
  cd onsite-hub && npx tsc --noEmit --skipLibCheck | grep task-bot

Tunnel for sharing (regenerates URL each time):
  nohup cloudflared tunnel --url http://localhost:3001 > /tmp/cloudflared.log 2>&1 &
  disown
  sleep 8 && grep trycloudflare.com /tmp/cloudflared.log

═══════════════════════════════════════════════════════════════
DHRUV'S WORKING STYLE
═══════════════════════════════════════════════════════════════

- Tests every change with screenshots
- Hindi-English typos common — parse intent, don't ask to clarify
- Don't sugar-coat bugs; say "I broke X"
- Update memory + STATE.md whenever shipping
- No subagents (PM rule)
- Don't push to Vercel without explicit go-ahead
- Don't use git --no-verify / --no-edit / --amend without approval
- Avoid jargon in user-facing strings (no "API", "endpoint", "server")

Start by reading the 4 docs at top. Then ack with a 3-bullet summary
of where the project is + your plan for the next session. Then wait
for direction.
```

---

## Compact-resume usage

1. Run `/compact` to clear conversation context
2. Copy the entire fenced code block above
3. Paste as your next message
4. Claude reads the 4 referenced docs and acks with a plan
