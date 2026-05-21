# Dispatch — Sprint 3: Support Tier 1+2 (renumbered from §6's "Sprint 5")

> **NOTE on numbering:** This is `dispatch-sprint-5-support.md` to match the original §6 plan name, but in the current `ROADMAP-ADDON.md` it's actually Sprint **3** (flipped before Training per Angelina's pushback). Filename stays for continuity with dispatch §9 deliverables list.
> **For:** Atlas (paste as first message of a FRESH Claude Code session — AFTER Sprint 1 RAG has merged)
> **From:** Angelina, PM for Onsite Task AI
> **Date dispatched:** 2026-05-19
> **Branch:** `feat/support-tier-1-2` off latest `onsite-hub` main
> **Duration:** 2 days (D11-D13 in `ROADMAP-ADDON.md`)
> **Spec source:** This file + `Onsite/task-ai/HLD-ADDON.md` § 3.3 + `ANGELINA-ADDON-DISPATCH.md` § 11 Support row

You are Atlas, the engineer for Support Tier 1+2. Job: confidence-gated RAG answers, ticket creation with category + urgency, duplicate suppression, immutable audit log, admin queue page. **Tier 3 (escalation cron + Telegram/email pager) is the NEXT sprint** — out of scope here. **Lift, don't invent.** Every file has a reference.

---

## §A — Read before writing any code (60 min)

In order:

1. `Onsite/task-ai/HLD-ADDON.md` § 3.3 — Support architecture (READ DIAGRAM)
2. `Onsite/task-ai/PRD-ADDON.md` § 3.3 — goals + non-goals + hard-routed category whitelist
3. `Onsite/task-ai/DECISIONS-ADDON.md` D3 — own queue + webhook-out for future Onsite forward
4. `Onsite/task-ai/ANGELINA-ADDON-DISPATCH.md` § 11 Support row
5. `euron-references/REPORT-shallow-scan.md` § MedAssist — audit decorator + escalation pattern source
6. `Onsite/onsite-hub/src/app/api/task-bot/route.ts` — the tool registry you'll extend
7. `Onsite/task-ai/database/` — existing migrations to model after
8. `~/.claude/projects/.../memory/reference_dhruv_rules.md` — 17 rules
9. `~/.claude/projects/.../memory/reference_supabase_cli_migrations.md` — migration workflow

Reply: "Read complete. Starting Sprint 3 (Support Tier 1+2)." Then proceed.

---

## §B — Files you'll create (with lift-from references)

Per `ANGELINA-ADDON-DISPATCH.md` § 11 Support row.

| # | New file (absolute path) | Lift from |
|---|---|---|
| S1 | `Onsite/task-ai/database/007_support.sql` | 📐 SQL in `HLD-ADDON.md` § 3.3 — `support_tickets` + `support_audit_log` + `CREATE RULE no_delete_audit` + RLS policies. Run via `supabase db push`. |
| S2 | `Onsite/onsite-hub/src/lib/support/audit_log.ts` | 📐 MedAssist `@audit_phi_access` decorator — port to a TS `withAudit(handler)` wrapper. Same immutable promise. Logs every Tier-1 resolve + ticket create + Tier-2 escalate event with hashed user_id, query, response. |
| S3 | `Onsite/onsite-hub/src/lib/support/auto_resolve_gate.ts` | 📐 New — hard whitelist on category: if `category in {account_issue, security, billing}` → ALWAYS escalate, regardless of RAG score. Server-side enforced. |
| S4 | `Onsite/onsite-hub/src/lib/support/duplicate_guard.ts` | 📐 New — `sha256(user_id + ':' + category + ':' + normalize(description))`. Check Redis 5-min TTL. If exists, return existing ticket_id; don't create new row. |
| S5 | `Onsite/onsite-hub/src/lib/support/confidence_gate.ts` | 📐 New — single function `shouldAutoAnswer({ ragScore, category }): boolean`. Returns true ONLY if `ragScore >= 0.7 AND category NOT in whitelist`. |
| S6 | `Onsite/onsite-hub/src/app/api/task-bot/support/create-ticket/route.ts` | 📐 Model after existing `/api/task-bot/route.ts` validation + dispatch shape |
| S7 | New tool def `create_support_ticket` in `Onsite/onsite-hub/src/app/api/task-bot/route.ts` | 📐 existing `create_task_dependency` tool definition shape (Sprint 1's `search_knowledge_base` is now also a precedent) |
| S8 | Confidence-gate logic in `/api/task-bot/route.ts` after `search_knowledge_base` returns | When chunks come back, evaluate confidence; if low, set context flag → next LLM turn prompts user for ticket creation |
| S9 | `Onsite/onsite-hub/src/components/task-bot/TicketCard.tsx` | 📐 existing `DependencyCard.tsx` pattern — same gradient header, Plus Jakarta Sans, `#c73e5a`. Shows category, urgency, ticket_id, status badge. |
| S10 | `Onsite/onsite-hub/src/app/task-bot/admin/support/page.tsx` | 📐 existing `/task-bot/admin/page.tsx` — same admin shell, swap inner table to ticket queue. Shows: ticket list (sortable by urgency / created_at), 24h deflection rate KPI, top categories. |

---

## §C — Tool registration

Add to TOOLS array in `Onsite/onsite-hub/src/app/api/task-bot/route.ts`:

```ts
{
  type: 'function',
  function: {
    name: 'create_support_ticket',
    description: 'Log a support ticket for issues the bot couldn\'t resolve. Confirm category and urgency with user before calling. NEVER call this for action requests like "create dependency" — only for bug reports, feature requests, account issues, data questions, or general help.',
    parameters: {
      type: 'object',
      properties: {
        category: { type: 'string', enum: ['bug', 'feature_request', 'account_issue', 'data_question', 'general'] },
        urgency: { type: 'string', enum: ['critical', 'high', 'normal', 'low'] },
        description: { type: 'string' },
        related_project_id: { type: 'string' },
        related_task_id: { type: 'string' }
      },
      required: ['category', 'urgency', 'description']
    }
  }
}
```

Add system prompt RULE 0.8:

```
RULE 0.8: When RAG returns chunks with low confidence (<0.7) OR no chunks AT ALL OR the topic is account/billing/security, do NOT fabricate. Acknowledge honestly: "I don't have docs on that — would you like me to create a support ticket?" If user agrees, ASK for category (bug/feature_request/account_issue/data_question/general) and urgency (critical/high/normal/low) BEFORE firing create_support_ticket. Never assume — never auto-fire with default values.
```

---

## §D — Confidence-gate flow inside `/api/task-bot/route.ts`

After the `search_knowledge_base` tool returns, before the second Claude call:

```ts
// Inside the existing tool-dispatch switch, after search_knowledge_base case:
import { shouldAutoAnswer } from '@/lib/support/confidence_gate'
import { logAudit } from '@/lib/support/audit_log'

// ... existing search_knowledge_base case ...
const chunks = result.chunks ?? []
const topScore = chunks[0]?.score ?? 0
const queryCategory = inferQueryCategory(args.query as string)  // simple regex categorizer

const canAutoAnswer = shouldAutoAnswer({ ragScore: topScore, category: queryCategory })

if (!canAutoAnswer) {
  // Append a system-hint to next LLM call: "Low confidence (score 0.4). Acknowledge honestly. Offer ticket creation."
  systemHints.push(`RAG_LOW_CONFIDENCE: top_score=${topScore}, category=${queryCategory}. Apply RULE 0.8.`)
}

await logAudit({
  user_id: userId,
  event_type: canAutoAnswer ? 'tier_1_resolved' : 'tier_1_low_confidence',
  query_text: args.query,
  metadata: { rag_score: topScore, category: queryCategory },
})
```

---

## §E — Database migration

Path: `Onsite/task-ai/database/007_support.sql`. Full SQL from `HLD-ADDON.md` § 3.3. Run:

```bash
cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai"
supabase db push
```

Per `reference_supabase_cli_migrations.md` — do NOT paste into dashboard.

**Verify `CREATE RULE no_delete_audit AS ON DELETE TO support_audit_log DO INSTEAD NOTHING;` is the IMMUTABLE lock.** Test: try `DELETE FROM support_audit_log WHERE id = ...` from the SQL editor → confirm it silently no-ops. Document the verification in PR description.

---

## §F — Acceptance gates

1. ✅ Query "How do I reset my password" → confidence low + category=account_issue → bot honors RULE 0.8 + offers ticket (NEVER auto-answers)
2. ✅ Query "How do I create a dependency" → RAG returns chunks score >0.7 → bot answers + 👎 button visible
3. ✅ 👎 click → bot routes to ticket creation flow, asks for category + urgency
4. ✅ Duplicate query within 5 min → `duplicate_guard` returns existing ticket_id, no new row
5. ✅ Admin page at `/task-bot/admin/support` shows tickets sorted by urgency DESC then created_at DESC
6. ✅ `CREATE RULE no_delete_audit` confirmed: DELETE attempt on audit table = no-op
7. ✅ Every ticket creation writes 1 row to `support_audit_log`
8. ✅ Tests against `testapi.onsiteteams.in` first
9. ✅ TypeScript clean: `npx tsc --noEmit --skipLibCheck | grep task-bot` empty
10. ✅ STATE.md batch 24 entry with commit SHAs

---

## §G — Hard rules (do NOT violate)

(Same as Sprint 1 §G + support-specific:)

1. **Token never logged, never sent to LLM.** Audit log stores hashed user_id, not the JWT.
2. **Hard-routed categories** (`account_issue`, `security`, `billing`) — these ALWAYS escalate. Whitelist enforced server-side. NEVER auto-resolve regardless of RAG confidence.
3. **No `--no-verify`, no `--amend`.**
4. **Repo split.** Code in onsite-hub. Docs in `Onsite/task-ai/`. Cross-reference SHAs.
5. **Mobile-first.** TicketCard renders correctly at 375px viewport.
6. **No half-finished.** Tier 3 (escalation, pager) is the NEXT sprint — don't ship partial escalation code.
7. **TypeScript strict.** No `any`.
8. **PR review.** Branch + PR + Dhruv merges per `feedback_pr_workflow_setu`.
9. **No spawning agents.**
10. **No mock data.** Test tickets get `[TEST]` prefix in description, deletable via admin (BUT audit_log entries persist — this is the immutability point).

---

## §H — Commit etiquette

1. Branch `feat/support-tier-1-2` on `onsite-hub`
2. Commits: `feat(support): <thing>`
3. Docs commit in `Onsite` repo cross-references SHA
4. PR title: `feat(support): tier 1 + 2 — confidence-gated answers + ticket creation`
5. Tag Dhruv reviewer

---

## §I — When you finish

Reply to Dhruv with:
1. Commit SHAs (both repos)
2. Acceptance gate checklist with proof
3. Audit-log immutability test result (screenshot of the failed DELETE attempt)
4. Tier-1 deflection rate baseline (synthetic test load: 10 queries, X auto-answered, Y escalated)
5. STATE.md batch 24 entry text

Then standby. Sprint 4 (Tier 3 escalation + pager) fires after this merges.

---

## §J — When you're stuck

Allowed escalations:
- RULE `DO INSTEAD NOTHING` blocks operations you didn't expect (e.g., admin testing) → switch to soft-delete column for the audit_log, document the tradeoff in `docs/decisions.md`
- Onsite's existing ticket system is real and Akshansh wants forward → wire the `OUTBOUND_TICKET_WEBHOOK_URL` env var (already reserved in HLD-ADDON.md § 3.3). Stays disabled by default for Sprint 3.
- Confidence threshold of 0.7 seems wrong on first synthetic test → flag it; Sprint 9 hardening tunes thresholds. Don't tune in this sprint.

NOT allowed:
- "Should I make the threshold 0.6 or 0.7" — use 0.7 per HLD-ADDON.md §3.3; that's the spec.
- Building Tier-3 escalation cron here.
- Touching the existing `/api/task-bot/route.ts` tool-dispatch order in a way that affects Sprint 1's RAG flow.

---

**Start by replying:** "Read complete. Starting Sprint 3 (Support Tier 1+2)." Then build.
