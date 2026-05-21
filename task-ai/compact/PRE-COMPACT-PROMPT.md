# PRE-COMPACT PROMPT (paste before `/compact`)

> Copy everything inside the fenced code block below and paste as a single message. Wait for Claude's "snapshot saved at <path>" confirmation. Only AFTER that, run `/compact`.

---

```
PRE-COMPACT CHECKPOINT — capture this session's state before context reset.

Project: Onsite Task AI (Smart Construction Intelligence Platform)
Project root: /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai/
Code repo:    /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub/
Docs repo:    /Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/ (with task-ai/ inside)

The canonical doc set (V3) lives at:
  - Onsite/task-ai/BRD-V3.md          Business requirements (market, ROI, personas, pricing)
  - Onsite/task-ai/PRD-V3.md          Product requirements (12 phases, 25 tools, acceptance)
  - Onsite/task-ai/ARCHITECTURE-V3.md Master architecture (decisions §0, tool catalogue §17)
  - Onsite/task-ai/HLD-V3.md          Component contracts, data flows, scaling, anti-patterns
  - Onsite/task-ai/LLD-V3.md          Migrations 011-018, API contracts, tool specs, file layout
  - Onsite/task-ai/CLAUDE.md          Master AI context (auto-loaded — points at V3 set)
  - Onsite/task-ai/MEMORY.md          Hard-earned learnings (M-01 through M-NN — read before changes)
  - Onsite/task-ai/STATE.md           Living state log (capability matrix + recent changes)

Reference repos already cloned + private-mirrored:
  - Smart AI Data Agent (MSBC, spine):     /tmp/smart-ai-data-agent/ (re-clone if missing)
  - KnowledgeForge (RAG report):           euron-references/knowledgeforge/
  - Hireai (phase state machine, voice):   euron-references/hireai/
  - Multimodal-RAG-System (PRIMARY RAG):   Euron/AI Architech Mastery/Multimodal-RAG-System/
  - Angelina app (memory + 22 tools):      angelina-vercel-clean/
  - QuotaHit voice (locked stable-v11.2):  QuotaHit/voice-server/
  - IndianWhisper (transcription):         Million-Dollar-Voice/AiwithDhruv_Voice/
  - Medassist (PII de-id pattern):         euron-references/medassist/

Do these 6 steps in order. Don't skip any. Don't ask for clarification — execute.

═══════════════════════════════════════════════════════════════
STEP 1 — Inventory both repos
═══════════════════════════════════════════════════════════════

For onsite-hub:
  cd /Users/apple/Aiwithdhruv/AI\ Development/Claude/Onsite/onsite-hub
  git branch --show-current
  git status --short
  git log --oneline -10

For Onsite (docs):
  cd /Users/apple/Aiwithdhruv/AI\ Development/Claude/Onsite
  git status --short task-ai/ database/
  git log --oneline -10

Note: which docs in task-ai/ are NEW vs MODIFIED vs UNCOMMITTED.

═══════════════════════════════════════════════════════════════
STEP 2 — Update Onsite/task-ai/STATE.md
═══════════════════════════════════════════════════════════════

Open Onsite/task-ai/STATE.md. Find the "## Recent Changes" section (near the top after the capability matrix). Insert a NEW entry at the TOP of that section (newest first ordering) with today's date.

Entry structure:
- **YYYY-MM-DD (label)** — one-line headline
  - Capability changed: <what>
  - Files created: <paths>
  - Files modified: <paths>
  - Commits landed: <sha + one-line msg>
  - In progress (uncommitted): <paths + "what's left">
  - New env vars: <list or none>
  - Migrations applied: <e.g. 011_memory_entries.sql or none>

ALSO update the Capability Matrix at the top if a row's status changed (e.g. ❌ Not built → ✅ Live). Update the "Last verified" date.

═══════════════════════════════════════════════════════════════
STEP 3 — Update Onsite/task-ai/MEMORY.md
═══════════════════════════════════════════════════════════════

For ANY non-obvious gotcha learned this session, add a new entry to MEMORY.md with the next sequential ID (M-NN where NN is one higher than the current max).

Non-obvious gotchas include:
  - A bug whose root cause surprised us (regex bug, race condition, schema mismatch)
  - A wrong assumption discovered (about pricing, model availability, API behavior)
  - A config that's load-bearing (env var, magic number, event name)
  - A failure mode not visible until prod-like conditions
  - A vendor quirk (Onsite API edge case, Supabase pgvector tuning, Gemini rate limit shape)

Entry format:
### M-NN. <One-line title>
<2-4 sentence body: what we learned, why it cost time, what to check next time>
**Apply:** <one-line action rule the next Claude must follow>

Don't add entries for things that are merely "we built X." Only add when "we built X and discovered Y was non-obvious." Skip step if nothing non-obvious surfaced.

═══════════════════════════════════════════════════════════════
STEP 4 — Update Onsite/task-ai/CLAUDE.md if applicable
═══════════════════════════════════════════════════════════════

CLAUDE.md is the auto-loaded master context. Update ONLY if one of these changed:
  - A new tool was added (update the §17 tool catalogue reference)
  - A new env var was added (update "Env vars" section)
  - A new internal endpoint shipped (update "Internal endpoints" section)
  - A repo location changed
  - A working rule was added/changed
  - The V3 doc set itself was extended (e.g. new "V4" docs)

If nothing applies, skip this step.

═══════════════════════════════════════════════════════════════
STEP 5 — Create the durable snapshot
═══════════════════════════════════════════════════════════════

Write a new file at:
  Onsite/task-ai/compact/SNAPSHOT-YYYY-MM-DD-HHMM.md

Use the actual current date + time IST. The filename ensures natural sort by alphabetical = latest = most recent.

The snapshot MUST contain ALL sections below (no sections skipped — write "none" if empty):

# Snapshot — YYYY-MM-DD HH:MM IST

**Session window:** <start → end approximate>
**Active phase:** <Pre-Phase 0 / Phase 0 demo polish / Phase 1 memory port / etc — pull from STATE.md or PRD-V3.md §3>
**Active branch (onsite-hub):** <git branch name>
**Last commit:** <onsite-hub sha + one-line message>
**Context budget at compact:** <approximate %>

## Goal of this session
<one paragraph: what we set out to do, what triggered the session>

## Shipped (durable — committed or saved files)
- file/path: short description of what changed
- commit sha: short description
- migration applied: <e.g. 011 — memory_entries — applied to xcvrdjhnvngfzczumquq>

## In progress (uncommitted — recoverable on resume)
- file/path: what's done vs what's left
- "feat: half-built X" pattern: <state>

## Decisions made this session
- decision: rationale (one-liner each — anything that should land in ARCHITECTURE-V3 §0 if architectural)

## Blockers / pending Dhruv input
- waiting on: <vercel login / token paste / Akshansh coord / PWA icons / API key / etc>

## New learnings added to MEMORY.md
- M-NN: <title>
- M-NN: <title>
(or "none" if nothing new)

## Next concrete action (when we resume)
1. step (be specific — file paths, commands, expected output)
2. step
3. step
4. step

## Read order for next Claude (always start with these in order)
1. Onsite/task-ai/CLAUDE.md (auto-loaded)
2. Onsite/task-ai/MEMORY.md (every M-NN entry)
3. Onsite/task-ai/STATE.md (top of file = most recent)
4. THIS snapshot file
5. Onsite/task-ai/ARCHITECTURE-V3.md (§0 decisions + §17 tool catalogue minimum)
6. Phase-specific docs (e.g. for memory work: LLD-V3.md §2 migrations + §3 memory API + §4 tools; angelina-vercel-clean/src/lib/memory.ts + sql/001_memory_schema.sql)

## Files actively being edited (if any)
- path: line range / current state
- (or "none — all clean")

## Tunnels / running processes to know about
- Cloudflare tunnel URL: <url or "dead">
- Dev server: <port or "stopped">
- Background tasks: <list or "none">
- Modal apps deployed: <list or "none">

## Supabase state
- Project ref: xcvrdjhnvngfzczumquq (Onsite_AI)
- Migrations applied so far: 001-010 (+ any new from this session)
- Migrations pending: <list>

## Tooling state (Vercel, Cloudflare, etc.)
- Vercel CLI authed: <yes/no>
- Vercel project linked: <yes/no — name if yes>
- Vercel envs synced: <count or "none">
- DNS subdomain: <yes/no — domain if yes>

═══════════════════════════════════════════════════════════════
STEP 6 — Confirm + remind Dhruv
═══════════════════════════════════════════════════════════════

After writing all the files in steps 2-5, output a single message containing exactly:

1. Path to the new snapshot file
2. Count + titles of any new M-NN entries added to MEMORY.md (or "none")
3. One-line summary of what was added to STATE.md
4. Whether CLAUDE.md was updated (yes — section + reason | no — nothing changed)
5. Uncommitted files Dhruv may want to commit BEFORE /compact (full git status --short of both repos)
6. Reminder line: "Run /compact now. After compact, paste contents of Onsite/task-ai/compact/POST-COMPACT-PROMPT.md."

Do NOT:
  - Use the Agent / SendMessage tools
  - Run /skills
  - Commit the snapshot to git (that's Dhruv's call)
  - Make any code changes
  - Spawn background tasks

Just write the files and respond.
```
