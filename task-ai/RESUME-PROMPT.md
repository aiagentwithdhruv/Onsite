# Resume Prompt — Onsite Task AI (May 19, 2026, end-of-session)

> Copy the fenced block below after running `/compact`. Self-contained.

---

```
Resume work on Onsite Task AI. Status: demo-ready + cost-optimized.
Owner: Dhruv Tomar (AI Builder at Onsite). Multi-tenant, chat-first
NL interface to Onsite's construction APIs.

═══════════════════════════════════════════════════════════════
READ FIRST (in order)
═══════════════════════════════════════════════════════════════

1. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/CLAUDE.md
   Master AI context.
2. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/STATE.md
   Synced through batch 20.
3. /Users/apple/.claude/projects/-Users-apple-Aiwithdhruv-AI-Development-Claude/memory/project_onsite_task_ai.md
   Cross-session memory — toolset, rules, model routing, TODO.

═══════════════════════════════════════════════════════════════
REPO STATE
═══════════════════════════════════════════════════════════════

aiagentwithdhruv/onsite-hub @ 01f3757  (code — Haiku default)
aiagentwithdhruv/Onsite    @ (latest)  (docs synced through batch 21)

═══════════════════════════════════════════════════════════════
MODEL ROUTING (locked 2026-05-19, post-production-test)
═══════════════════════════════════════════════════════════════

TIER 1 default:     anthropic/claude-haiku-4-5    proven on real production
TIER 2 escalation:  anthropic/claude-sonnet-4-6   when Haiku hallucinates

IMPORTANT: Gemini 3 Flash Preview was the default for ~30 minutes
(commit d66f893) but failed on real Arohan project test — gave up
when first workorder probe returned empty instead of trying
fan-out. Reverted to Haiku in commit 01f3757. Mocked A/B passed
14/14 but didn't capture real-world multi-step persistence.

Gemini still accessible via TASK_BOT_MODEL env var if we re-test.
A/B scripts in Onsite/task-ai/scripts/ unchanged.

═══════════════════════════════════════════════════════════════
TOOLSET (14 tools)
═══════════════════════════════════════════════════════════════

list_companies / list_projects / list_tasks / list_subactivities /
list_dependencies / list_progress_history / get_project_stats /
create_task_dependency / update_task_dependency /
delete_task_dependency / record_task_progress / delete_task_progress /
search_tasks / add_task / add_subactivity

add_task and add_subactivity are SERVER-GATED by Onsite ("feature has
been upgraded" 400). Bot replies with plan-tier upsell language per
RULE 0.55 — never says "API"/"endpoint".

═══════════════════════════════════════════════════════════════
HARD RULES (system prompt)
═══════════════════════════════════════════════════════════════

RULE -1  User numbers = list positions, not IDs.
RULE 0   Never ask users for UUIDs.
RULE 0.5 Remember progress_history_id / dep_id from prior turns.
RULE 0.55 Plan-gated features → product upsell, no API jargon.
RULE 0.56 Never fake delete with negative entry — use list_progress_history.
RULE 0.6  Ambiguous project names → ASK, never pick silently.

═══════════════════════════════════════════════════════════════
WHAT'S WORKING (do NOT rebuild)
═══════════════════════════════════════════════════════════════

✓ 14 tools wired
✓ 3-tier routing with escalation ladder
✓ Multi-project disambiguation (ambiguous:true flag in list_projects)
✓ progress_history_id round-trip for clean deletes
✓ Plan-tier upsell language on server-gated endpoints
✓ Desktop 3-column layout (sidebar + main + right rail)
✓ Mobile single-column unchanged
✓ AT-A-GLANCE Option B (lifetime "via AI" stats, live refresh)
✓ Tap-to-paste project-aware tips in right rail
✓ Optimistic "+ New chat" sidebar insert
✓ Chat persists on refresh (two-step restore + ref-based gating)
✓ Living sparkle logo (breathe/glow/twinkle)
✓ Sidebar search + hover rename/delete
✓ Hallucination guard catches first-person action claims
✓ Chrome extension v0.2.0 auto-injects token

═══════════════════════════════════════════════════════════════
LIVE TODO (priority order)
═══════════════════════════════════════════════════════════════

1. Ask Akshansh for correct endpoint/headers for add_task and
   add_subactivity (currently 400 "feature has been upgraded").
   Once known: flip one line, bot creates tasks for real.

2. Ask Akshansh for endpoint that lists ALL workorders of a project.

3. Vercel deploy — pending Dhruv go-ahead.
   Env vars:
     TASK_AI_SUPABASE_URL=https://xcvrdjhnvngfzczumquq.supabase.co
     TASK_AI_SUPABASE_SERVICE_KEY=<paste>
     OPENROUTER_API_KEY=<already in Vercel>
     TASK_BOT_MODEL=google/gemini-3-flash-preview
     ANTHROPIC_API_KEY=<optional, gates direct path>

4. Production cost monitoring — verify Gemini 3 default holds up.
   If escalation rate >10%, tune system prompt or revert to Haiku
   via TASK_BOT_MODEL env.

5. Auth path: embed inside Onsite app (Akshansh discussion).

6. Hook training-data export to scheduled job.

═══════════════════════════════════════════════════════════════
TESTER KIT (ready to share)
═══════════════════════════════════════════════════════════════

URL: https://velocity-mls-boss-swim.trycloudflare.com/task-bot
     (rotates on terminal close — regenerate with cloudflared)

Zip: Onsite/task-ai/onsite-ai-helper-v0.2.0.zip
     (also in ~/Downloads/onsite-ai-helper-v0.2.0.zip)

Install flow:
  1. Unzip
  2. chrome://extensions → Developer mode ON → Load unpacked
  3. Log into web.onsiteteams.com
  4. Open tunnel URL → auto-connects

═══════════════════════════════════════════════════════════════
DEV WORKFLOW
═══════════════════════════════════════════════════════════════

Start dev:
  cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub"
  pkill -f "next dev"; sleep 1
  nohup npm run dev -- --port 3001 > /tmp/onsite-hub-dev.log 2>&1 &
  disown

Smoke check:
  curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3001/task-bot

TS check:
  cd onsite-hub && npx tsc --noEmit --skipLibCheck | grep task-bot

Tunnel:
  nohup cloudflared tunnel --url http://localhost:3001 > /tmp/cloudflared.log 2>&1 &
  disown
  sleep 8 && grep trycloudflare.com /tmp/cloudflared.log

A/B test models (run if Gemini behavior degrades):
  node Onsite/task-ai/scripts/3way-haiku-g2-g3.mjs

═══════════════════════════════════════════════════════════════
DHRUV'S WORKING STYLE
═══════════════════════════════════════════════════════════════

- Tests every change with screenshots
- Hindi-English typos common — parse intent
- Don't sugar-coat bugs
- Update memory + STATE.md when shipping
- No subagents
- Don't push to Vercel without explicit go-ahead
- No git --no-verify / --amend without approval
- No jargon in user-facing strings ("API"/"endpoint"/"server")

Start by reading the 3 docs at top. Ack with 3-bullet summary + plan.
Wait for direction.
```

---

## Compact-resume usage

1. Run `/compact` to clear context
2. Copy the entire fenced code block above
3. Paste as your next message — the next Claude reads the 3 docs and acks with a plan
