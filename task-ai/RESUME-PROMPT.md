# Resume Prompt — Onsite Task AI

> Copy the entire code block below after running `/compact`. Self-contained: no priors needed.

---

```
Resume work on Onsite Task AI — a natural-language AI chatbot embedded in
Onsite construction management software. Owner: Dhruv Tomar (AI Builder
at Onsite). Status: working end-to-end, demo-ready, localhost-only (not
deployed to Vercel yet).

═══════════════════════════════════════════════════════════════
READ FIRST (in this order)
═══════════════════════════════════════════════════════════════

1. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/CLAUDE.md
   — Master AI context, capability matrix, where code lives.
2. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/STATE.md
   — Recent changes (batches 1-8), open TODO list.
3. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/MEMORY.md
   — Hard-earned learnings (API quirks, leaf-task rules, auth).
4. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/CHAT-SCREEN-REBUILD-TODO.md
   — The currently-pending chat-screen alignment work.
5. /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/docs/UI-UX-DESIGN-SPEC.md
   — Full design system: colors, typography, components, tone, prompts for AI image tools.
6. /Users/apple/.claude/projects/-Users-apple-Aiwithdhruv-AI-Development-Claude/memory/project_onsite_task_ai.md
   — Cross-session memory pointer with UX commitments.
7. /Users/apple/.claude/projects/-Users-apple-Aiwithdhruv-AI-Development-Claude/memory/reference_supabase_cli_migrations.md
   — How to run Supabase migrations (use the CLI, never ask Dhruv to dashboard-paste SQL).

═══════════════════════════════════════════════════════════════
REPO SPLIT (critical — commit to the right one)
═══════════════════════════════════════════════════════════════

CODE (page.tsx, route.ts, all API endpoints, Chrome ext content scripts):
  → onsite-hub repo
  → /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub/
  → github.com/aiagentwithdhruv/onsite-hub (PRIVATE)

DOCS, migrations, prototype files, runbooks:
  → Onsite repo, under task-ai/
  → /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/
  → github.com/aiagentwithdhruv/Onsite (PRIVATE)

Both repos are PRIVATE. Both are pushed to the same GitHub org.

═══════════════════════════════════════════════════════════════
KEY FILES
═══════════════════════════════════════════════════════════════

onsite-hub/src/app/task-bot/page.tsx
  — The whole frontend: Setup screen + Dashboard + Chat + History drawer
    + Picker modal + Rename + Delete + Stats card + Suggestion chips.
    All in one file (~1900 lines). Three view states: 'setup' (no auth),
    'dashboard', 'chat'. Persisted to sessionStorage.

onsite-hub/src/app/task-bot/admin/page.tsx
  — Admin dashboard at /task-bot/admin. 24h stats, per-tool, errors.
    "Export training data" button downloads JSONL.

onsite-hub/src/app/api/task-bot/route.ts
  — Main backend. 11 tools (list_companies/projects/tasks/subactivities/
    dependencies + create_task_dependency + update + delete + record_progress
    + delete_progress + get_project_stats). Multi-iteration tool-call loop
    (MAX_ITERATIONS = 8). System prompt has RULE -1 (numbers are positions,
    not UUIDs) and RULE 0 (never ask user for UUIDs).

onsite-hub/src/app/api/task-bot/{chat-log,feedback,sessions,my-stats,admin-stats,export-training-data}/route.ts
  — All Supabase-backed endpoints. Service-role writes, RLS-locked tables.

onsite-hub/src/app/api/task-bot/activity.ts
  — JWT decode helper, fetchWithRetry, logAction, persistence client.

onsite-hub/src/components/AppShell.tsx
  — One line carving /task-bot/* out of the PIN-auth gate: line 13
    `if (pathname.startsWith('/task-bot')) return <>{children}</>`
    LOAD-BEARING. Don't refactor away.

═══════════════════════════════════════════════════════════════
SUPABASE
═══════════════════════════════════════════════════════════════

Project: xcvrdjhnvngfzczumquq.supabase.co
Tables:
  - task_ai_actions          (audit log, every tool call)
  - task_ai_messages         (chat persistence, opt-in originally, now always-on)
  - task_ai_session_meta     (per-session title + project_context)

Migrations live in Onsite/task-ai/database/*.sql

To apply a migration (don't ask Dhruv to dashboard-paste):
  PAT in ~/.aiwithdhruv-secrets as SUPABASE_ACCESS_TOKEN_TASK_AI
  Workspace at /tmp/task-ai-supabase/
  Drop SQL into supabase/migrations/<timestamp>_<name>.sql
  Run: cd /tmp/task-ai-supabase && \
       SUPABASE_ACCESS_TOKEN=<PAT> supabase db push \
       --password 'Dhruvtomar7008@' --include-all

Env vars in onsite-hub/.env.local:
  TASK_AI_SUPABASE_URL=https://xcvrdjhnvngfzczumquq.supabase.co
  TASK_AI_SUPABASE_SERVICE_KEY=<service_role_jwt>
  OPENROUTER_API_KEY=<dhruv's key>
  ANTHROPIC_API_KEY=<optional, gates direct Anthropic API>
  TASK_AI_ADMIN_USERS=<comma-separated user_ids, optional>

═══════════════════════════════════════════════════════════════
MODELS & ROUTING
═══════════════════════════════════════════════════════════════

  - DEFAULT_MODEL: anthropic/claude-haiku-4-5  (fast list/show)
  - COMPLEX_MODEL: anthropic/claude-sonnet-4-6  (action chains)
  - pickModel(messages) heuristic: routes to Sonnet when latest user
    message contains an action verb (create/make/add/log/update/delete/
    depedy/dependency/progress) AND a two-word entity name.
  - If ANTHROPIC_API_KEY is set in env, calls go direct to Anthropic API
    (callClaudeViaAnthropic). Otherwise falls back to OpenRouter
    (callClaudeViaOpenRouter). OpenRouter routes through Vertex/Bedrock —
    direct Anthropic is faster and Dhruv wants to switch when ready.

═══════════════════════════════════════════════════════════════
SHIPPED (do NOT rebuild)
═══════════════════════════════════════════════════════════════

✓ 3-view structure: Setup → Dashboard → Chat (persisted via taskbot_view in sessionStorage)
✓ Setup screen with manual token paste + Chrome ext auto-inject
✓ Dashboard with:
    - Hero "Time saved" tile (full-width gradient, lightning icon, mini bar chart)
    - Total actions + Deps created tiles (side-by-side)
    - Progress logged tile (full-width, mini line chart)
    - "What I can do for you" 2x2 suggestion cards
    - "Continue a past chat" (top 5 sessions)
    - Recent activity with color-coded bubble icons
    - Floating compact "Start chatting" pill bottom-right
    - Skeleton placeholders during async load (no layout shift)
✓ Picker modal on "Start chatting" — New chat vs Resume past
✓ Chat screen with:
    - Header (back arrow, sparkle, "Onsite AI", session title in violet)
    - Suggestion cards on first turn (no more past chats here — clean)
    - Welcome message
    - Hierarchical task tree (collapsible, parents auto-collapsed if >20 nodes)
    - 4 tool result cards: dependency_created, progress_recorded, task_stats, error
    - Numbered options pre-fill the input box (with right-arrow icon)
    - Suggested next chips below latest bot message
    - Thumbs feedback per assistant message
    - Smart loading indicator: 5 rotating stages + contextual "Looking up data in <Project>…" after 12s
    - Voice input (en-IN / hi-IN toggle)
    - Input placeholder: "Talk to me… create a dependency, log progress, or just ask"
✓ History drawer (clock icon top-right):
    - Lists sessions, hover reveals pencil + trash icons
    - Inline rename + delete-with-confirm
    - "+ New chat" gradient pill at top
✓ Always-on chat persistence (task_ai_messages)
✓ Session rename → injected as bot's project anchor in system prompt
✓ Refresh restore (initialRestoreDone flag, replays messages + title + sets view='chat')
✓ Service-worker cleanup on mount (kills stale sw.js from prior builds)
✓ Admin page /task-bot/admin
✓ Training-data JSONL export
✓ Server cache (5-min TTL per user, auto-invalidated on mutations)
✓ Stale chat from Image 95 (old dark UI) — solved by SW unregister
✓ "0 projects" hallucination (Image 98) — solved by RULE -1 in prompt
✓ Layout shift on refresh (Image 94) — solved by skeleton placeholders
✓ Brand: linear-gradient(110deg, #1a0b50 0%, #5b21b6 52%, #c73e5a 100%)
✓ Font: Plus Jakarta Sans

═══════════════════════════════════════════════════════════════
CURRENT TODO (the chat-screen rebuild)
═══════════════════════════════════════════════════════════════

The dashboard is fully aligned with Dhruv's mockup. The chat screen is
NOT — see CHAT-SCREEN-REBUILD-TODO.md for the punch list:

  - Header: "Onsite AI · <Project>" on one line + LIVE pill below
  - DependencyCard: gradient vertical line connector between rows
  - ProgressCard: sectioned TASK / ADDED+TOTAL / NOTE grid
  - Task tree: duration tag right, 🔗N + N% inline on sub-rows
  - Input bar: pill, taller, slate-100 bg
  - Desktop 3-col layout: left sidebar (chats) + middle (chat) +
    right panel (PROJECT CONTEXT, AT A GLANCE, MENTIONED, TIPS)

Mockup source files in /tmp/onsite-mockup/ (extracted from
~/Downloads/Oniste Task Ai.zip). Look at:
  - screens-chat.jsx (mobile chat)
  - screens-desktop.jsx (desktop 3-col)
  - styles.css (design tokens, CSS vars)

═══════════════════════════════════════════════════════════════
HARD-LOCKED RULES
═══════════════════════════════════════════════════════════════

1. NEVER ask the user for UUIDs (in code, in UI, or in bot replies).
2. User numbered references ("19. Dhruv Construction") = LIST POSITIONS,
   NOT IDs. Resolve via list_companies/list_projects first.
3. Chat title is a HINT to the bot, never ground truth. Bot must
   verify via list_projects every action chain.
4. Don't deploy to Vercel without Dhruv saying so.
5. Don't change default model (Haiku 4.5 stays default, Sonnet via routing
   heuristic, override via TASK_BOT_MODEL env).
6. Don't break the AppShell.tsx PIN-bypass for /task-bot.
7. Don't break the Chrome extension auto-auth flow.
8. Don't add features outside the TODO without asking.
9. Push code → onsite-hub, docs → Onsite/task-ai (cross-ref in commit messages).
10. Test in browser (hard refresh after each ship) — TS check is not enough.

═══════════════════════════════════════════════════════════════
DEV WORKFLOW
═══════════════════════════════════════════════════════════════

Start the dev server (background it):
  cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub"
  pkill -f "next dev" 2>/dev/null; sleep 1
  nohup npm run dev -- --port 3001 > /tmp/onsite-hub-dev.log 2>&1 &
  disown

Smoke check:
  curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3001/task-bot

TypeScript check:
  cd onsite-hub && npx tsc --noEmit --skipLibCheck

Live URL: http://localhost:3001/task-bot
Admin URL: http://localhost:3001/task-bot/admin

═══════════════════════════════════════════════════════════════
NEXT STEPS (do these in order)
═══════════════════════════════════════════════════════════════

A) Read all 7 docs listed at the top.
B) Open /tmp/onsite-mockup/{screens-chat,screens-desktop,styles.css}.jsx
C) Update Onsite/onsite-hub/src/app/task-bot/page.tsx — chat screen
   block only. Reference the dashboard you ALREADY aligned for style.
D) After each ship: TS check → restart dev server → tell Dhruv to test
   on hard refresh (Cmd+Shift+R) → wait for his feedback.
E) Update STATE.md with each ship.
F) Delete CHAT-SCREEN-REBUILD-TODO.md when fully done.
G) Update CLAUDE.md capability matrix when done.

═══════════════════════════════════════════════════════════════
DHRUV'S WORKING STYLE
═══════════════════════════════════════════════════════════════

- Tests every change personally with screenshots — be ready for iteration
- Often types in Hindi-English mix or with typos; parse intent, don't ask
  to clarify trivial typos
- Wants honest "I broke this" responses; don't sugar-coat
- Memory + CLAUDE.md must stay current — update whenever shipping
- Don't spawn subagents (PM rule, see memory feedback_never_spawn_coding_agent)
- Don't use git --no-verify, --no-edit, --amend without explicit approval
- For UI changes: actually open the browser and test, don't just trust
  the TS compiler

Start by reading the 7 docs, then ack with a 3-bullet summary of what
you understood + your plan, then begin.
```

---

## How to use

1. Run `/compact` to clear context
2. Copy the entire fenced code block above
3. Paste as your next message
4. Claude will read everything and ack with a plan before starting

## File locations summary

| What | Where |
|---|---|
| This resume prompt | `Onsite/task-ai/RESUME-PROMPT.md` (on GitHub: aiagentwithdhruv/Onsite) |
| Chat rebuild TODO | `Onsite/task-ai/CHAT-SCREEN-REBUILD-TODO.md` |
| Full design spec | `Onsite/task-ai/docs/UI-UX-DESIGN-SPEC.md` |
| Master context | `Onsite/task-ai/CLAUDE.md` |
| State + recent changes | `Onsite/task-ai/STATE.md` |
| Hard-earned learnings | `Onsite/task-ai/MEMORY.md` |
| Mockup source | `/tmp/onsite-mockup/` (extracted) + `~/Downloads/Oniste Task Ai.zip` |
