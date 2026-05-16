# Roadmap — Onsite Task AI

**Owner:** Dhruv Tomar | **Last updated:** 2026-05-17

> Five phases from MVP-in-localhost to "Sumit shows this in every demo to close deals."

---

## Phase Snapshot

| Phase | Goal | Status | Timeline | Blockers |
|-------|------|--------|----------|----------|
| **1. MVP** | Prove the concept: AI → real Onsite API | ✅ Done | 2026-05-17 | — |
| **2. Customer-grade** | Real customers can use it without DevTools | 🟡 Planning | 2 weeks | API specs from Akshansh |
| **3. Production launch** | Embedded in Onsite, multi-language, audit log | 🔴 Not started | 6 weeks | Phase 2 ship + Sumit sign-off |
| **4. Expansion** | Beyond tasks: materials, inspections, reports | 🔴 Not started | 10 weeks | Phase 3 traction |
| **5. Intelligence** | Predictive insights, suggestions, alerts | 🔴 Not started | 16+ weeks | Phase 4 data volume |

---

## Phase 1 — MVP (✅ COMPLETE)

**Goal:** Prove that an AI bot can take a natural-language request and execute it against the real Onsite API.

**Shipped:**
- ✅ Chat UI at `/task-bot` (mobile + desktop)
- ✅ Voice input (en-IN)
- ✅ Bearer token auth (manual paste)
- ✅ Tool: `create_task_dependency`
- ✅ Tool: `record_task_progress`
- ✅ Stateless multi-tenant backend
- ✅ Production-verified: 2 real dependencies + 1 progress entry in Soul Space project

**Cost so far:** ~$0 (one Vercel project we already had, no new infra)

**Decision point reached:** Continue investing or pivot? → **Continue** (Sumit will buy this; competitive moat is real).

---

## Phase 2 — Customer-Grade (🟡 NEXT)

**Goal:** Make it usable by a real customer (site engineer with a phone) without any developer assistance.

**Timeline:** 2 weeks from API specs unblock

**Blocker:** Need API specs from Akshansh for 7 endpoints (see § "Akshansh API request" below).

### What ships in Phase 2

**New tools:**
- `list_projects(company_id?)` → so user can say "Soul Space project" instead of UUID
- `list_tasks(project_id, query?)` → so user can say "Electrical panel" instead of `22200f57-...`
- `list_subactivities(ba_id)` → bot auto-resolves "Location 1" vs "Location 2"
- `update_task_dependency(id, type?, lag?)` → "change that dependency to 3-day lag"
- `delete_task_dependency(id)` → "remove that dependency I just made"
- `add_task(workorder_id, parent_id?, name, ...)` → "add a sub-task 'Wire Testing' under Electrical panel Setup"
- `update_task(ba_id, ...)` → "rename that task to 'Power Wiring'"

**UX improvements:**
- **Name-based references:** User can say "make plastering depend on brickwork" — bot looks up both tasks, asks for confirmation, then acts
- **Multi-step flows:** Bot remembers context across multiple turns ("create a dependency", "primary is Foundation", "secondary is Wall Construction", "finish to start", "0 lag")
- **Pre-flight confirmation for destructive ops:** Delete/update tools always ask "confirm?" before firing
- **Error messages in Hindi-English mix:** Match user's language register
- **Conversation memory with tool history:** Send Claude the full tool-call history so it can reference past actions

**Tech improvements:**
- Vitest integration test suite (against `testapi.onsiteteams.in`)
- LLM eval suite (20 utterances → expected tool dispatch + args)
- Structured logging (no PII; just timing + tool name + success)
- Hindi voice input (`lang = 'hi-IN'` toggle)

**Deploy to Vercel** as a public URL (`task-ai-staging.vercel.app` or similar) so Akshansh + Sumit can test from their phones.

### Akshansh API request (send as one message)

```
Akshansh bhai, AI task bot ke liye 7 v3 API ke specs chahiye.
Same format jaise taskdependency wala diya tha — endpoint + method + payload example + handler form input.

1. POST /apis/v3/list/billingactivity (with filters: project_id, workorder_id, search_query)
2. POST /apis/v3/list/billingsubactivity (filter: billing_activity_id)
3. POST /apis/v3/list/project (filter: company_id)
4. POST /apis/v3/update/taskdependency (id + new type/lag)
5. POST /apis/v3/delete/taskdependency (id)
6. POST /apis/v3/add/billingactivity (workorder_id, parent_id, name, unit, etc.)
7. POST /apis/v3/update/billingactivity (id + fields to change)

If swagger / postman export available, that works too — I'll extract.
```

### Phase 2 acceptance criteria

- [ ] All 7 new tools shipped
- [ ] Customer can complete a dependency creation flow using only task names (zero UUIDs)
- [ ] Voice input works in Hindi
- [ ] Conversation tested across 10 real customer scenarios (write into test-results.md)
- [ ] Deployed to a public Vercel URL
- [ ] Sumit + Akshansh test from their phones and approve

### Phase 2 demo script (for Sumit when ready)

```
1. Open the URL on phone
2. Paste token (or auto-auth if Phase 3 done)
3. Say: "Soul Space project mein Electrical panel Setup ke baad
        Fixture installation start hona chahiye"
4. Bot: "Got it. Creating finish-to-start dependency. Confirm?"
5. Say: "Yes"
6. Bot: "Done. Fixture installation now waits for Electrical panel Setup."
7. Open Onsite app → show the Gantt arrow appearing live
```

If Sumit doesn't say "WOW, this changes everything" at step 7, we have feedback to integrate.

---

## Phase 3 — Production Launch (🔴 FUTURE)

**Goal:** Sumit can sell this as a feature. Customers use it daily.

**Timeline:** 6 weeks after Phase 2 ships

### What ships in Phase 3

**Embedded in Onsite app:**
- Bot opens in an iframe / overlay inside `web.onsiteteams.com`
- Auto-auth via `postMessage` from parent frame (no token paste)
- "AI Assistant" button in Onsite's nav
- Mobile app integration (React Native WebView wrapper or native screen)

**Multi-language:**
- UI strings: en, hi, ta, te (i18next)
- Voice input: en-IN, hi-IN, ta-IN, te-IN
- LLM responses in user's language (system prompt instruction)

**Audit log:**
- Every bot action logged with: timestamp, user_id, company_id, tool_name, args, success
- Admins can view audit log per project ("show me everything the bot did in Soul Space this week")
- Required for trust + compliance + customer-facing transparency

**Rate limiting:**
- Per-customer: 100 messages/hour soft cap, 500/hour hard cap (via Upstash Redis)
- Prevents runaway costs + abusive automation

**Cost tracking:**
- Per-customer LLM cost tracking (which company spent how much)
- Feeds pricing model decisions (free tier? paid tier? bundled?)

**Smart routing:**
- Use Haiku 4.5 for simple acknowledgements / clarifications
- Sonnet 4.6 only for tool-call decisions and complex multi-step
- Target: 50% cost reduction

**Production polish:**
- Custom domain (`task-ai.onsiteteams.com` or similar)
- Real monitoring (Vercel Analytics + Logflare/Better Stack)
- Synthetic user health checks
- Status page

### Phase 3 acceptance criteria

- [ ] Embedded in Onsite web app (production)
- [ ] 4 languages live (en, hi, ta, te)
- [ ] Audit log visible to admins
- [ ] Rate limits enforced
- [ ] 99.5% uptime measured over 30 days
- [ ] 10 customer companies actively using daily

---

## Phase 4 — Expansion (🔴 FUTURE)

**Goal:** Bot becomes the universal interface for Onsite, not just task dependencies.

**Timeline:** 10 weeks after Phase 3 ships

### What ships in Phase 4

**New domains:**
- **Material requests:** "Order 50 bags of OPC 43 cement for Soul Space, urgent"
- **Inspections:** "Mark the electrical inspection passed for Foundation Wall"
- **Photos:** "Here's a progress photo of Wiring Installation" (vision API + auto-tagging)
- **DPR (Daily Progress Report):** "Generate yesterday's DPR for Soul Space"
- **RA Bills:** "Draft RA Bill for contractor X, 75% complete on Wiring"
- **Quotations:** "Create a quotation for the new villa client"
- **Issues:** "Raise an issue: water leak in basement"
- **Tasks across projects:** "What are my top 5 overdue tasks across all projects?"

**Architectural changes:**
- Multi-tool composition (one user message → bot calls 3 endpoints in sequence)
- Persistent conversation history (opt-in, encrypted, per-customer)
- Voice + image multimodal (Claude vision for "what's wrong with this photo")

**Each domain adds ~5–10 tools.** Total tool count by end of Phase 4: ~50.

### Phase 4 acceptance criteria

- [ ] 50% of customer's Onsite interactions go through the bot (not the app UI)
- [ ] Multi-step bot flows tested across 5 domains
- [ ] Photo upload + analysis working
- [ ] Conversation history (opt-in) shipped

---

## Phase 5 — Intelligence (🔴 FUTURE)

**Goal:** Bot doesn't just respond — it suggests, predicts, alerts.

**Timeline:** 16+ weeks (after Phase 4 has data volume to learn from)

### What ships in Phase 5

**Predictive features:**
- "You're 3 weeks behind on Insulation. Want me to compress the schedule?"
- "Foundation Wall has had no progress in 8 days. Should I create a task to follow up with the contractor?"
- "Soul Space is 12% over budget. Top 3 overspend categories: cement, labor, transport. Want a deep dive?"

**Suggestion features:**
- "Typical next step after Electrical panel Setup is Fixture Installation. Want me to set that dependency?"
- "Other Onsite users who built a similar structure usually add a Waterproofing task here. Add it?"
- "Photos suggest the foundation work is 90% done but progress entries show 60%. Want to update?"

**Cross-customer learning:**
- Anonymous aggregate insights: "Construction projects similar to yours typically have these 12 dependencies. Want to bulk-create?"
- Benchmarks: "Your project's progress velocity is 30% above industry average for this stage."

**Architectural changes:**
- Vector DB of past project structures (pgvector / Pinecone)
- Cross-customer training pipeline (privacy-safe aggregation)
- Periodic "morning briefing" push to project managers

**Caution:** All cross-customer features require explicit opt-in. Data isolation principles from Phase 1 still hold for action data; only anonymized aggregates flow across.

---

## Decision Gates Between Phases

After each phase, decide before investing in the next:

| Gate | Question | Decision threshold |
|------|----------|-------------------|
| 1→2 | Is the MVP actually used by humans (not just Dhruv)? | Akshansh + Sumit both used it ≥3 times in a week |
| 2→3 | Do customers come back? | ≥30% Week-2 retention in 50-customer pilot |
| 3→4 | Is task management traction enough to expand scope? | ≥20% of Onsite monthly users have used the bot |
| 4→5 | Is there a learning signal in the data? | Action data volume ≥100K events/month |

If a gate fails, **stop and re-evaluate** rather than push forward.

---

## What We're Explicitly Not Building

- **A general-purpose chatbot.** No "what's the weather", no "write a poem", no "summarize this PDF" — keep scope tight.
- **A replacement for Onsite's UI.** The app's screens remain primary; bot augments.
- **Customer support / FAQ bot.** That's a different product (Onsite already has one or could build one).
- **A standalone product sold separately.** This is an Onsite feature. Bundle pricing, not standalone.

---

## What Could Kill This Project

1. **Akshansh / Sumit don't see customer pull** — pivot or stop after Phase 2 pilot
2. **LLM costs spiral above ₹50/user/month** — switch to smaller model or limit features
3. **Onsite competitive product launches** — re-evaluate positioning
4. **A tenant isolation bug ships** — pause feature work, fix, audit, then resume

---

## References

- [PRD.md](PRD.md) — what we're building and why
- [HLD.md](HLD.md) — architecture
- [LLD.md](LLD.md) — implementation
- [STATE.md](STATE.md) — what's live right now
