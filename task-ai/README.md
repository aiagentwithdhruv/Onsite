# Onsite Task AI

> Natural-language AI inside Onsite construction management software. Say what you want, the bot does it.

**Status:** MVP shipped (Phase 1 ✅). Phase 2 planning. | **Last update:** 2026-05-17 | **Owner:** Dhruv Tomar

---

## What This Is

An AI chatbot embedded in Onsite. Customers (builders, site engineers, project managers) speak or type in plain English/Hindi/Tamil, and the bot performs real Onsite operations — creating task dependencies, logging progress, managing project state.

**Instead of this** (current Onsite UX):
```
Open app → Project → Tasks → Find task A → Find task B → Add Dependency → Pick type → Save
(8 taps, 30 seconds, error-prone on mobile)
```

**The customer does this:**
```
"make plastering wait for brickwork to finish"
(one message, 3 seconds)
```

---

## What's Working Right Now

✅ Chat UI (text + voice) at `localhost:3001/task-bot`
✅ Create task dependencies via natural language
✅ Record task progress via natural language
✅ Production-verified: 2 real dependencies + 1 progress entry created in Soul Space project
✅ Bearer token auth (manual paste; sessionStorage-only)
✅ Stateless multi-tenant (one deployment serves all customers, zero data leakage risk)

## What's Next

🟡 Phase 2 (2 weeks once API specs unblock): name-based task references, list/update/delete operations, Hindi voice, deployment
🔴 Phase 3 (6 weeks): embedded in Onsite app, multi-language, audit log, rate limiting
🔴 Phase 4+ (10+ weeks): materials, inspections, DPRs, RA bills, predictive insights

Full plan → [ROADMAP.md](ROADMAP.md)

---

## Quick Start (developer)

```bash
cd "Onsite/onsite-hub"
npm install                          # only first time
npm run dev -- --port 3001
open http://localhost:3001/task-bot
```

**To test end-to-end:**
1. Open `web.onsiteteams.com` in another tab, log in
2. Open DevTools Console, run:
   ```js
   copy(JSON.parse(localStorage.getItem('token')).token)
   ```
3. In the task-bot tab, paste token → select **Production** → Start Chat
4. Grab 2 BA IDs from Network tab (click a task → grab UUID from the detail URL)
5. Send: `Make <id1> depend on <id2>, finish-to-start, lag 0`
6. Verify the FS arrow appears in the Onsite Gantt view

---

## Documentation Map

| File | What's in it | When to read |
|------|--------------|--------------|
| [CLAUDE.md](CLAUDE.md) | Master AI context — auto-loaded by Claude Code | Before any code change |
| [MEMORY.md](MEMORY.md) | Persistent learnings, gotchas, "we already tried that" | Before debugging |
| [PRD.md](PRD.md) | Product Requirements: users, goals, success metrics | Before scope discussions |
| [HLD.md](HLD.md) | High-Level Design: architecture, multi-tenancy, scale | Before architecture decisions |
| [LLD.md](LLD.md) | Low-Level Design: data shapes, components, tool patterns | Before implementing a new tool |
| [ROADMAP.md](ROADMAP.md) | 5-phase plan from MVP to full product | When planning next sprint |
| [STATE.md](STATE.md) | Current state of every feature | Status check |
| [API-SPECS.md](API-SPECS.md) | Onsite API endpoints we have + need | When integrating a new endpoint |
| [BUG-TRACKER.md](BUG-TRACKER.md) | Known issues with severity + status | Bug triage |
| [docs/data-model.md](docs/data-model.md) | Onsite domain model (BA, sub-activity, etc.) | Understanding what bot manipulates |
| [docs/multi-tenancy.md](docs/multi-tenancy.md) | Tenant isolation deep dive | Security questions |
| [docs/competitive-analysis.md](docs/competitive-analysis.md) | vs Onsite's own bot + Procore + Powerplay | Positioning discussions |
| [docs/decisions.md](docs/decisions.md) | ADRs — every architectural decision + rationale | "Why did we choose X?" |
| [docs/test-results.md](docs/test-results.md) | End-to-end test log | Regression debugging |

---

## Tech Stack (Phase 1)

- **Framework:** Next.js 15 App Router (lives inside `onsite-hub` project)
- **Frontend:** React 19 + Tailwind 4 + Web Speech API (voice)
- **Backend:** Next.js Route Handler (stateless, no DB)
- **LLM:** Claude Sonnet 4.6 via OpenRouter (OpenAI-compatible API + tool use)
- **Auth:** Onsite Bearer JWT (per-request, never stored)
- **Deploy:** Vercel (existing `onsite-hub` project)
- **Storage:** None (intentional — see [HLD § Stateless](HLD.md#21-stateless-by-design))

---

## Contributing

This is a small, focused project. Before writing code:

1. Read [CLAUDE.md](CLAUDE.md) and [MEMORY.md](MEMORY.md)
2. Check [STATE.md](STATE.md) for current capability inventory
3. Check [API-SPECS.md](API-SPECS.md) — does Onsite have the endpoint you need? If not, the work is blocked on Akshansh
4. Read the Dhruv Rules: `~/.claude/projects/.../memory/reference_dhruv_rules.md` (17 rules; especially "minimal diffs", "no half-finished implementations")
5. Test through the actual UI before claiming a feature works — curl ≠ UI ≠ customer

---

## Contact

- **Product owner:** Dhruv Tomar (`dhruv.tomar@onsiteteams.com`)
- **Onsite stakeholders:** Akshansh Agarwal (CEO), Sumit Garg (founder)
- **GitHub:** (pending push)
