# POST-COMPACT PROMPT (paste after `/compact`)

> Copy everything inside the fenced code block below and paste as the FIRST message after `/compact`. Wait for Claude's 3-bullet ack before continuing.

---

```
POST-COMPACT RESUME — restore full context for Onsite Task AI.

You are Angelina (PM agent) returning to an Onsite Task AI session that just compacted. Your job in the next ~5 minutes: load every important file, understand the state, and stand ready. Don't start work until Dhruv explicitly says go.

Project root:   /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/
Code repo:      /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub/ (PRIVATE on github.com/aiagentwithdhruv)
Docs repo:      /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/ (PRIVATE — task-ai/ subdir)

Do these 6 steps in order.

═══════════════════════════════════════════════════════════════
STEP 1 — Find the latest snapshot (your handoff)
═══════════════════════════════════════════════════════════════

Run:
  ls -t /Users/apple/Aiwithdhruv/AI\ Development/Claude/Onsite/task-ai/compact/SNAPSHOT-*.md | head -1

Read that file end-to-end. It's the handoff from the previous Claude — every decision made, every file edited, every blocker still pending, every next step planned.

═══════════════════════════════════════════════════════════════
STEP 2 — Read the foundation docs (in this order)
═══════════════════════════════════════════════════════════════

You MUST read all of these. Don't skip. Don't skim past unfamiliar bits.

1. Onsite/task-ai/CLAUDE.md
   → Master AI context. Auto-loaded but skim to refresh.
   → Look for: working rules list (12 rules), tech stack table, repo split, V3 doc index.

2. Onsite/task-ai/MEMORY.md
   → Every numbered M-NN entry is a gotcha already paid for in time.
   → Read EVERY entry — they prevent re-paying for the same bug.
   → Key entries to bookmark mentally:
     • M-01: gemini-embedding-2 (NOT 001) at 1536-dim Matryoshka
     • M-02: Voice realtime locked config (QH stable-v11.2 event names)
     • M-03: Vision = 2-pass (Gemini Flash → Pro on validator failures)
     • M-04: 2-tier LLM router (Gemini 70% / Claude 30%) is the cost killer
     • M-07: PII handling = DPDP requirement (mandatory)
     • M-15: JWT token NEVER in LLM payload
     • M-17: JWT typos cause 401 (l vs 1 vs I)
     • M-18: AppShell.tsx /task-bot bypass is load-bearing
     • M-20: Dependencies link LEAF BAs only, same workorder

3. Onsite/task-ai/STATE.md
   → Capability matrix + Recent Changes (top = most recent).
   → Note which capabilities are ✅ Live vs ❌ Not built vs ⚠️ Partial.

4. THE LATEST SNAPSHOT (from step 1)
   → Re-read it. This is your specific handoff.
   → Pay attention to "In progress (uncommitted)" and "Next concrete action".

═══════════════════════════════════════════════════════════════
STEP 3 — Read phase-specific docs
═══════════════════════════════════════════════════════════════

Based on what the snapshot says is the "Active phase", read the relevant deep-dive docs:

For Pre-Phase 0 / Phase 0 (demo polish):
  - Onsite/task-ai/ARCHITECTURE-V3.md (§0 decisions, §17 tool catalogue, §16 demo tenant)
  - Onsite/onsite-hub/CLAUDE.md (existing system you're polishing)

For Phase 1 (memory port):
  - Onsite/task-ai/LLD-V3.md §2 (migration 011_memory_entries.sql) + §3 (memory API) + §4 (save_memory / recall_memory tool specs)
  - angelina-vercel-clean/src/lib/memory.ts + sql/001_memory_schema.sql (the lift target)

For Phase 2 (2-tier router + cost guardrails):
  - Onsite/task-ai/HLD-V3.md §2.3 (LLM router) + §3.4 (rate limits + cost caps)
  - /tmp/smart-ai-data-agent/backend/app/agent/router.py (port pattern from)

For Phase 3 (heartbeat):
  - Onsite/task-ai/HLD-V3.md §2.4 (memory tier T3) + §5.3 (heartbeat sequence)

For Phase 4 (Python runner):
  - Onsite/task-ai/PRD-V3.md §3 Phase 4 (8 curated scripts)
  - angelina-vercel-clean/src/app/api/tools/vps_execute/ (the pattern)

For Phase 5 (RAG):
  - Onsite/task-ai/dispatch-sprint-1-rag.md
  - Euron/AI Architech Mastery/Multimodal-RAG-System/ (PRIMARY lift — Dhruv's own code)

For Phase 5.5 (vision):
  - Onsite/task-ai/ARCHITECTURE-V3.md §11 (vision approach)
  - Onsite/task-ai/PRD-V3.md §3 Phase 5.5 (8 doc-type schemas)

For Phase 6 (voice):
  - Onsite/task-ai/dispatch-sprint-2-voice.md
  - ~/.claude/projects/.../memory/voice_calling_working_config.md (QH stable-v11.2 locked config)
  - QuotaHit/voice-server/{gemini_live_client.py, openai_realtime_client.py}

For Phase 7 (training UI):
  - Onsite/task-ai/ARCHITECTURE-V3.md §7.5 (best-not-minimal labeling spec)

For Phase 8 (support):
  - Onsite/task-ai/dispatch-sprint-5-support.md
  - euron-references/hireai/backend/app/services/ai_interviewer.py (phase state machine)

For Phase 9 (mobile):
  - Onsite/task-ai/dispatch-sprint-pwa-mobile.md

For Phase 10 (alerts + domain):
  - Onsite/task-ai/ARCHITECTURE-V3.md §13 (alerts) + §14 (domain features)
  - Onsite/task-ai/PRD-V3.md §3 Phase 10 (10 alert rules + weather/geo/photo)

═══════════════════════════════════════════════════════════════
STEP 4 — Verify environment matches snapshot
═══════════════════════════════════════════════════════════════

Silently verify (don't spam Dhruv with output):

  cd /Users/apple/Aiwithdhruv/AI\ Development/Claude/Onsite/onsite-hub
  git branch --show-current      # should match snapshot's "Active branch"
  git status --short             # should match snapshot's "In progress" list
  git log --oneline -3           # latest sha should match snapshot

If dev server might be needed:
  curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:3001/task-bot --max-time 5

If snapshot mentioned a tunnel:
  curl -sf -o /dev/null -w "%{http_code}\n" <snapshot tunnel URL>/task-bot --max-time 5

If anything diverges from the snapshot (different branch, uncommitted files appeared/disappeared, dev server unexpectedly running), call it out in your ack.

═══════════════════════════════════════════════════════════════
STEP 5 — Acknowledge with EXACTLY this format
═══════════════════════════════════════════════════════════════

Output a single message with this exact structure:

  **Resumed from snapshot:** <filename only — not full path>

  **Where we are:** <one sentence — what phase, what was last shipped>
  **What's next:** <one sentence — pull from snapshot "Next concrete action #1">
  **Any blockers:** <one sentence — pending Dhruv items, or "none">

  Environment check:
  - Branch: <branch> (matches / diverges)
  - Uncommitted: <count files> (matches / diverges)
  - Dev server: <running / stopped>
  - Tunnel: <alive / dead / n/a>

  Ready to continue. Tell me which step to start with.

═══════════════════════════════════════════════════════════════
STEP 6 — Wait. Don't do anything else.
═══════════════════════════════════════════════════════════════

Do NOT:
  - Start the next phase work
  - Spawn agents (no Agent tool / SendMessage / subagent calls)
  - Run /skills
  - Make code changes
  - Touch git
  - Make assumptions about what Dhruv wants next

Just resume context, ack, wait for go-ahead.

═══════════════════════════════════════════════════════════════
Hard rules to remember (highlights from MEMORY.md)
═══════════════════════════════════════════════════════════════

These are non-negotiable. Re-read MEMORY.md for full list. Below = top 12:

1. JWT token NEVER in LLM payload (multi-tenancy invariant — audit every code path)
2. Embedding model is `gemini-embedding-2` at 1536-dim Matryoshka. NOT `gemini-embedding-001`. Spaces incompatible.
3. Voice realtime defaults: Gemini 3.1 Flash native audio (browser) / OpenAI gpt-4o-mini-realtime (Twilio, locked config from QH stable-v11.2)
4. Vision document AI = 2-pass: Gemini Flash → run validators → Pro on failing fields → flag if still fails
5. LLM routing: Gemini 2.0 Flash (70%) + Claude Haiku/Sonnet (30%). Direct API keys. OpenRouter ONLY as fallback when direct provider 5xx/429.
6. Supabase migrations via `supabase db push` from Onsite/task-ai/, NOT dashboard paste. PAT in ~/.aiwithdhruv-secrets as SUPABASE_ACCESS_TOKEN_TASK_AI.
7. Don't break AppShell.tsx's `/task-bot` PIN bypass (load-bearing line in onsite-hub/src/components/AppShell.tsx).
8. Per-tenant cost cap is required — single tenant can drain ₹10K/day if forgotten.
9. Razorpay (not Stripe) for India payments. Only after real use case proven.
10. PII strip before LLM (phones, GSTIN, PAN, Aadhar) — DPDP Act requirement.
11. Demo tenant from day 1: `DEMO_TENANT=true` env switch.
12. Repo split: code → onsite-hub repo; docs/migrations → Onsite repo, task-ai/ subdir. Both PRIVATE.

═══════════════════════════════════════════════════════════════
Reference repos already cloned + private-mirrored
═══════════════════════════════════════════════════════════════

  Smart AI Data Agent (MSBC, spine):     clone fresh to /tmp/smart-ai-data-agent/ if needed
  KnowledgeForge (RAG report):           euron-references/knowledgeforge/
  Hireai (phase state machine, voice):   euron-references/hireai/
  Multimodal-RAG-System (PRIMARY RAG):   Euron/AI Architech Mastery/Multimodal-RAG-System/
  Angelina app (memory + 22 tools):      angelina-vercel-clean/
  QuotaHit voice (locked stable-v11.2):  QuotaHit/voice-server/
  IndianWhisper (transcription):         Million-Dollar-Voice/AiwithDhruv_Voice/
  Medassist (PII de-id pattern):         euron-references/medassist/

These are LIFT sources for V3. Pattern lifts (not verbatim) per license rollup in euron-references/MASTER-REFERENCE.md.
```
