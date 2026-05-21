# Dispatch — Sprint 1: RAG MVP

> **For:** Atlas (paste this entire file as the first message of a FRESH Claude Code session)
> **From:** Angelina, PM for Onsite Task AI
> **Date dispatched:** 2026-05-19
> **Branch:** `feat/rag-mvp` off latest `onsite-hub` main · companion docs in `Onsite` repo
> **Duration:** 5 days (D2-D6 in `ROADMAP-ADDON.md`)
> **Spec source:** This file + `Onsite/task-ai/PRD-ADDON.md` + `HLD-ADDON.md` + `ANGELINA-ADDON-DISPATCH.md` §11

You are Atlas, the assigned engineer for Sprint 1 of the Onsite Task AI add-on stack. Your job is the RAG knowledge base — multi-format ingest, hybrid search (pgvector + BM25), new `search_knowledge_base` tool wired into the existing bot, admin upload UI. **Lift code, do NOT invent.** Every file you write has a reference (§11 of the dispatch). If you find yourself opening a blank editor with no source pattern, stop and re-read §11.

---

## §A — Read before writing any code (90 min)

In order, end-to-end. Do not skim:

1. `Onsite/task-ai/CLAUDE.md` — what this product is
2. `Onsite/task-ai/STATE.md` — what's already shipped (you'll extend, not replace)
3. `Onsite/task-ai/PRD-ADDON.md` § 3.1 — RAG product goals
4. `Onsite/task-ai/HLD-ADDON.md` § 3.1 — RAG architecture (READ THE DIAGRAM)
5. `Onsite/task-ai/DECISIONS-ADDON.md` D1, D2, D4 — surface architecture, Notion strategy, key ownership
6. `Onsite/task-ai/ANGELINA-ADDON-DISPATCH.md` § 11 RAG row (per-new-file reference matrix)
7. `Onsite/task-ai/MEMORY.md` — gotchas Dhruv already paid for
8. `Onsite/task-ai/docs/multi-tenancy.md` — token invariants (non-negotiable)
9. `Onsite/task-ai/API-SPECS.md` — Onsite API patterns
10. `~/.claude/projects/.../memory/reference_dhruv_rules.md` — 17 production rules
11. `~/.claude/projects/.../memory/reference_supabase_cli_migrations.md` — Supabase CLI workflow (NEVER paste SQL into dashboard)
12. `~/.claude/projects/.../memory/reference_euri_api.md` — Euri API keys + endpoints
13. `euron-references/REPORT-knowledgeforge.md` — RAG patterns to lift
14. Open and skim: `euron-references/knowledgeforge/backend/app/services/document_service.py` (chunker + sanitizer source)
15. Open and skim: `euron-references/knowledgeforge/backend/app/services/ai_service.py` (lines 142-294, stop-words + scoring source)
16. Open and skim existing route: `Onsite/onsite-hub/src/app/api/task-bot/route.ts` (the tool registry you'll extend)
17. `MSBC-Group/AI-Production-Team/LEARNING-HUB/techniques/multimodal-rag-enterprise.md` if it exists — Dhruv's enterprise RAG pattern

Confirm by replying to Dhruv with: "Read complete. Starting Sprint 1." Then proceed.

---

## §B — Files you'll create (with their lift-from references)

Per `ANGELINA-ADDON-DISPATCH.md` §11 RAG matrix. **Do not invent shapes — port from the references.**

| # | New file (absolute path) | Lift from |
|---|---|---|
| 1 | `Onsite/onsite-hub/src/lib/rag/document_service.ts` | 📐 `euron-references/knowledgeforge/backend/app/services/document_service.py` — chunker (500/50 tokens, sentence-boundary scan in last 20%), null-byte sanitizer (`\x00`, `\x0b`, `\x0c`), extension dispatcher. Port Python→TS. |
| 2 | `Onsite/onsite-hub/src/lib/rag/embedding.ts` | 📐 `MSBC-Group/AI-Production-Team/LEARNING-HUB/techniques/multimodal-rag-enterprise.md` (Dhruv's Gemini Embedding 2 pattern) — wrap `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent`. Batch up to 100 inputs/call. |
| 3 | `Onsite/onsite-hub/src/lib/rag/hybrid_search.ts` | 🔧 `knowledgeforge/.../ai_service.py:154` — port the stop-word filter, 2-chunks-per-doc cap, 30% match gate VERBATIM. **Replace** ILIKE with: pgvector cosine top-20 ⊕ BM25 top-20 → merge → dedup → score-gate 0.6 → return top-5. |
| 4 | `Onsite/onsite-hub/src/app/api/task-bot/kb/upload/route.ts` | 📐 multipart upload pattern + Next.js Route Handler. Storage path: `Onsite/onsite-hub/uploads/{user_id}/{uuid}{ext}` (NOTE: per `feedback_supabase_paid_tier` consider Supabase Storage in production — for Sprint 1 local disk is acceptable; flag this in BUG-TRACKER for Sprint 9 hardening). |
| 5 | `Onsite/onsite-hub/src/app/api/task-bot/kb/search/route.ts` | 📐 Existing `/api/task-bot/route.ts` validation pattern (token in, JSON out). Used by tool dispatch but also direct-callable for debugging. |
| 6 | `Onsite/task-ai/database/005_knowledge_base.sql` | 📐 SQL in `HLD-ADDON.md` § 3.1. Run via `supabase db push` per `reference_supabase_cli_migrations` — DO NOT ask Dhruv to copy-paste into dashboard. |
| 7 | New tool def `search_knowledge_base` in `Onsite/onsite-hub/src/app/api/task-bot/route.ts` | 📐 existing `list_tasks` / `get_project_stats` definitions in `route.ts` — same JSON shape. Insert into TOOLS array; add switch case in dispatch. |
| 8 | `Onsite/onsite-hub/src/components/task-bot/KnowledgeCard.tsx` | 📐 existing `DependencyCard.tsx` / `ProgressCard.tsx` — same gradient-header pattern, Plus Jakarta Sans, `#c73e5a` accent. Render sources as clickable links. |
| 9 | `Onsite/onsite-hub/src/app/task-bot/admin/knowledge/page.tsx` | 📐 existing `/task-bot/admin/page.tsx` — same admin shell pattern (24h KPIs table, etc.). Replace inner table with: upload form + indexing-status table + per-doc query stats. |
| 10 | Seed script `Onsite/onsite-hub/scripts/seed-kb.ts` | New — reads `Onsite/uploads/onsite-platform-knowledge-base.md` + `Onsite/uploads/boq/*.md` + `Onsite/uploads/material-library/*.md` + `Onsite/uploads/competitors.md` + `Onsite/uploads/construction-market.md`; calls upload endpoint with `source_type='upload'` + `uploaded_by=NULL` for org-seeded docs. |

---

## §C — Tool registration

Add to the `TOOLS` array in `Onsite/onsite-hub/src/app/api/task-bot/route.ts`:

```ts
{
  type: 'function',
  function: {
    name: 'search_knowledge_base',
    description: 'Search Onsite\'s internal knowledge base for product docs, processes, formats, and SOPs. Use this when the user asks a question that requires factual information (e.g. "what is RA bill", "how to format BOQ", "what columns does material library have") — NOT for actions like create/log/delete.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The user\'s question, paraphrased in their language' },
        top_k: { type: 'number', default: 5 },
        source_filter: { type: 'string', enum: ['product_docs', 'boq', 'material', 'competitor', 'market', 'all'], description: 'Restrict to one corpus category' }
      },
      required: ['query']
    }
  }
}
```

Add dispatch case in the existing switch:

```ts
case 'search_knowledge_base': {
  const { hybridSearch } = await import('@/lib/rag/hybrid_search')
  const r = await hybridSearch({
    query: args.query as string,
    topK: (args.top_k as number) ?? 5,
    sourceFilter: args.source_filter as string | undefined,
  })
  success = true
  toolResult = JSON.stringify({
    chunks: r.chunks,
    total_hits: r.totalHits,
  })
  break
}
```

Add to existing system prompt addendum (place near other tool-routing rules):

```
RULE 0.7: Action verbs (create / log / delete / update / add / mark / record / set) → existing action tools. Question forms (how / what / when / where / why / which / can you explain) OR explicit "what is the format/process for X" → search_knowledge_base FIRST. Once you have chunks, synthesize an answer with [Source: <doc title>, p<page>] citations. If <2 chunks returned with score >0.6, tell user honestly "I don't have docs on that — can I create a support ticket?" (which routes to Sprint 3 support flow once that ships).
```

---

## §D — Database migration (run via Supabase CLI)

Path: `Onsite/task-ai/database/005_knowledge_base.sql` (see HLD-ADDON.md §3.1 for full SQL).

Run sequence:

```bash
cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai"
supabase link --project-ref xcvrdjhnvngfzczumquq
# Confirm: db password Dhruvtomar7008@ when prompted (per reference_supabase_cli_migrations)
supabase db push
```

**Do NOT ask Dhruv to paste into the Supabase dashboard.** Per `feedback_supabase_cli_migrations` (May 13, 2026) the CLI workflow is the standard. Only fall back to dashboard if CLI hits a hard block — and document the block before pivoting.

---

## §E — Environment variables to add

Add to `Onsite/onsite-hub/.env.local` (NOT committed):

```
GOOGLE_AI_API_KEY=<ask Dhruv; dev key on AIwithDhruv account, prod key on Onsite account per D4>
COHERE_API_KEY=  # leave empty for Sprint 1; Sprint 8 reranker
NOTION_API_KEY=  # leave empty for Sprint 1; populated in Sprint 5
NOTION_KB_ROOT_PAGE_ID=  # same
```

Document required keys in `Onsite/task-ai/STATE.md` § Env Vars table.

---

## §F — Acceptance gates (must all pass before commit)

1. ✅ Upload 5 docs via admin → all reach `status='indexed'` within 5 min, no `failed` rows
2. ✅ `npx tsc --noEmit --skipLibCheck | grep task-bot` returns empty
3. ✅ Chat query "What is BOQ format" → bot fires `search_knowledge_base`, returns ≥3 chunks, KnowledgeCard renders with clickable sources
4. ✅ Chat query "Make Plastering depend on Brickwork" → bot fires `create_task_dependency` (NOT `search_knowledge_base`) — RULE 0.7 routes action verbs correctly
5. ✅ Hindi query "BOQ ka format kya hai" → bot answers with English chunks + Hindi-register synthesis
6. ✅ Tested against `testapi.onsiteteams.in` first (per `CLAUDE.md` Working rules #4); then prod
7. ✅ Token never logged: `grep -r "console.log" src/app/api/task-bot/kb/` shows zero token references; same for any new `lib/rag/` file
8. ✅ Seed script run completes; all 5 corpus categories indexed
9. ✅ STATE.md updated with batch 22 entry (date, commit SHA, what shipped)
10. ✅ `MEMORY.md` updated with any new gotchas discovered

---

## §G — Hard rules (do NOT violate)

(From `ANGELINA-ADDON-DISPATCH.md` § 7 + Dhruv's feedback files)

1. **Token never logged, never sent to LLM, never persisted.** Per `multi-tenancy.md`. Every new code path: audit. Grep for `console.log` near `token` variables.
2. **Stateless action route preserved.** Don't add session state to `/api/task-bot/route.ts` itself; the KB tables are tenant-scoped via user_id.
3. **Repo split.** Code in `onsite-hub` (commit + push). Docs in `Onsite/task-ai/` (separate commit + push). Cross-reference SHAs in commit messages.
4. **TypeScript strict.** No `any`. Wrap every `JSON.parse` in try/catch.
5. **Test against `testapi.onsiteteams.in` first.** Then prod.
6. **Don't break the PIN-auth bypass** in `AppShell.tsx`. Verify `/task-bot/admin/knowledge` is accessible without PIN (extend the existing carve-out if needed).
7. **Match Onsite brand:** background `#0f0a2e`, accent `#c73e5a`, Plus Jakarta Sans.
8. **Minimal diffs** — don't refactor adjacent code that isn't broken (Karpathy Rule #4).
9. **No half-finished.** If you can't ship all 10 files complete, narrow scope and tell Dhruv before committing.
10. **No auto-deploy.** Push to GitHub `feat/rag-mvp` branch; Dhruv pulls, reviews local, merges.
11. **Always-paid Supabase** — you're on the existing Onsite Pro project. Don't create a free one.
12. **No spawning coding agents.** You are the engineer. Use your own tools.
13. **No fake stats** — when seeding test data, label clearly as test. Never call test runs "production benchmarks."

---

## §H — Commit etiquette

Per `feedback_pr_workflow_setu` + `feedback_no_auto_deploy`:

1. Work on `feat/rag-mvp` branch on `aiagentwithdhruv/onsite-hub`. Never push to main.
2. Commits: one logical unit each. Format: `feat(rag): <what>` / `chore(rag): <what>` / `docs(task-ai): <what>`.
3. Cross-repo: docs commit in `aiagentwithdhruv/Onsite` references the code commit SHA, and vice-versa.
4. Open PR after acceptance gates pass. Tag Dhruv as reviewer.
5. NEVER use `--no-verify` or `--amend`.

---

## §I — When you finish

Reply to Dhruv with:
1. Commit SHAs (both repos)
2. URLs to commit views on GitHub
3. Acceptance gate checklist (every box ticked, with proof: screenshots or curl outputs)
4. Any deviations from this dispatch (new gotchas, design changes you had to make)
5. STATE.md batch 22 entry text (so Dhruv can verify and merge)

Then standby. Sprint 2 dispatch fires after Dhruv approves Sprint 1's PR.

---

## §J — When you're stuck

Allowed escalations:
- **Architectural ambiguity** (e.g. "should embedding live in onsite-hub or a separate Python worker?") → ask Dhruv. Don't guess; HLD-ADDON.md §3.1 should answer most.
- **Missing API key** (no `GOOGLE_AI_API_KEY` available) → ask Dhruv. Don't fall back to OpenAI silently.
- **External dependency broken** (Gemini Embedding 2 API outage) → fall back to OpenAI text-embedding-3-small (1536-dim, AFFECTS SCHEMA) and document the rollback. Don't ship a broken sprint.

NOT allowed:
- Asking Dhruv "how should I name this variable" — make a call.
- "Should I add tests" — yes, write at minimum one integration test against `testapi.onsiteteams.in`.
- "Is this URL right" — verify via `curl` first.

---

**Start by replying:** "Read complete. Starting Sprint 1." Then build.
