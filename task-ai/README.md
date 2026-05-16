# Onsite Task AI

> **Natural-language AI inside Onsite construction management software.**
> Say what you want. The bot does it.

[![Phase 1](https://img.shields.io/badge/Phase%201-Shipped-success)]()
[![Phase 2](https://img.shields.io/badge/Phase%202-Planning-yellow)]()
[![Production verified](https://img.shields.io/badge/Production-Verified-green)]()
[![Stack](https://img.shields.io/badge/Stack-Next.js%2015%20%2B%20Claude%20Sonnet%204.6-blue)]()

**Owner:** Dhruv Tomar (`dhruv.tomar@onsiteteams.com`) · **Last updated:** 2026-05-17

---

## 📌 TL;DR

A chatbot embedded inside Onsite. Construction site teams describe what they want (in English, Hindi, or Hindi-English mix), and the bot performs the real Onsite API operation — creating task dependencies, logging progress, more coming.

**Without the bot** (current Onsite UX):
> Open app → Project → Tasks → Find task A → Find task B → Add Dependency → Pick type → Save
> *8 taps · 30 seconds · error-prone on mobile · impossible with gloves on*

**With the bot:**
> *"Plastering ko brickwork ke baad start karna hai"*
> *one message · 3 seconds · works on phone with one hand*

---

## ✅ Production-Verified (2026-05-17)

Real test against `api.onsiteteams.in` with Dhruv Construction account:

| Action | Result | Onsite ID |
|--------|--------|-----------|
| Create dependency: Electrical panel Setup → Fixture installation (FS, lag 0) | ✅ | `d374d749-0270-40fb-80c1-a672e9824341` |
| Create dependency: New Electric Test → Electrical panel Setup (FS, lag 0) | ✅ | `9ba0c664-c188-41f4-832e-93384b67625f` |
| Record progress: +3 numbers on Electrical panel Setup | ✅ | Visible in Onsite UI Progress tab |

All three created via the actual chatbot UI, end-to-end. The `0.2 FS` dependency arrows are live on the Soul Space Gantt right now.

---

## 🗂 GitHub Repos

| Repo | Purpose | Visibility |
|------|---------|------------|
| [aiagentwithdhruv/onsite-hub](https://github.com/aiagentwithdhruv/onsite-hub) | **Code** — Next.js app containing the task-bot page + API route | Private |
| [aiagentwithdhruv/Onsite](https://github.com/aiagentwithdhruv/Onsite/tree/main/task-ai) | **Docs** — this folder (`task-ai/`) inside the Onsite repo | Private |

Code commit: `cc9b9bc` · Docs commit: `264a22d`

---

## 🏗 Architecture (60-second version)

```
Customer's Browser
   │ types/speaks: "make plastering wait for brickwork"
   ▼
/task-bot page (Next.js, sessionStorage-only token)
   │ POST /api/task-bot { messages, token, baseUrl }
   ▼
/api/task-bot route (stateless, no DB)
   │ ① Claude Sonnet 4.6 (via OpenRouter) with tool definitions
   │ ② If tool_call → fetch Onsite API w/ customer's Bearer JWT
   │ ③ Claude again, with tool result, for natural-language reply
   │ ④ Return { reply, tool_called, success, card }
   ▼
Customer's Browser renders:
   - Text bubble (Claude's friendly reply)
   - Rich tool-result card (green/blue/red, structured data)
```

**Stateless by design** = multi-tenancy is structural. One deploy serves 10K customers. Token never persisted, never sent to LLM, never logged. → [HLD.md § Multi-Tenancy](HLD.md#3-multi-tenancy-architecture)

---

## 🎯 What's Working

| Feature | Status |
|---------|--------|
| Chat UI (text + voice) | ✅ Live |
| Voice input (en-IN) | ✅ |
| Bearer token auth | ✅ |
| Create task dependency (4 types, 0–999 day lag) | ✅ Production-verified |
| Record task progress | ✅ Production-verified |
| Hindi-English bilingual responses | ✅ (confirmed working) |
| Rich tool-result cards (not just markdown) | ✅ |
| Stateless multi-tenant | ✅ Structural |
| Sanitized error messages (no raw API jargon) | ✅ |
| Sessionstorage token isolation | ✅ |

## 🚧 What's Next

| Phase | Goal | Blockers | Timeline |
|-------|------|----------|----------|
| **Phase 2** | Name-based task references · update/delete deps · add tasks · Hindi voice · Vercel deploy | Need 7 API specs from Akshansh ([template](ROADMAP.md#akshansh-api-request-send-as-one-message)) | 2 weeks |
| **Phase 3** | Embedded in Onsite app · 4 languages · audit log · rate limiting · SSO auth | Phase 2 ship + Sumit sign-off | 6 weeks |
| **Phase 4** | Materials · inspections · DPRs · RA bills · photos | Phase 3 traction | 10 weeks |
| **Phase 5** | Predictive insights · suggestions · alerts | Phase 4 data volume | 16+ weeks |

→ Full plan: [ROADMAP.md](ROADMAP.md)

---

## 🚀 Quick Start (Local Dev)

```bash
# Clone the code repo
git clone https://github.com/aiagentwithdhruv/onsite-hub.git
cd onsite-hub

# Install + run
npm install
npm run dev -- --port 3001

# Open in browser
open http://localhost:3001/task-bot
```

**Required env var** (in `onsite-hub/.env.local`):
```
OPENROUTER_API_KEY=sk-or-v1-...
```

That's it. No database, no Redis, no other infra.

---

## 🧪 How to Test End-to-End

### 1. Get your Onsite Bearer token

Open [web.onsiteteams.com](https://web.onsiteteams.com) → log in → DevTools Console → paste:

```js
copy(JSON.parse(localStorage.getItem('token')).token)
```

Token is now on your clipboard.

### 2. Pick 2 leaf-level task BA IDs

Either:
- **Via UI:** Click any task in Onsite → grab UUID from the task detail URL
- **Via Network tab:** Click any task → look for the `detail/billingactivity/<UUID>` request → that UUID is the BA ID

**Or use these (already in Soul Space, all leaf nodes):**

| Task | BA ID |
|------|-------|
| Electrical panel Setup | `22200f57-402b-4755-811c-faf67ed02135` |
| Fixture and outlet installation | `54a68548-e2b6-48f4-b883-94e75f156497` |
| New Electric Test | `1b8f2e76-bdd6-44c9-82c9-a8082aa5b243` |

Sub-activity for progress: `be32dae2-e675-4204-b0e7-f13e3094d7a0` (Location 1 under Electrical panel Setup)

### 3. Send a message

In the bot, type/speak something like:

```
Make Fixture installation depend on Electrical panel Setup, FS, lag 0.
Primary: 22200f57-402b-4755-811c-faf67ed02135
Secondary: 54a68548-e2b6-48f4-b883-94e75f156497
```

Or just chat naturally:

> *"Plastering ko brickwork ke baad start karna hai"*

Bot will ask for the IDs, you provide them, it acts.

### 4. Verify

- ✅ Green dependency card appears in chat with both task names + FS arrow + lag badge
- ✅ Refresh Soul Space in Onsite — the `FS` arrow shows on the Gantt
- ✅ Click the dependent task → Dependencies field went from 0 → 1

---

## 📚 Documentation Map

> Read order for new contributors: **CLAUDE.md → MEMORY.md → STATE.md** then dive in.

| File | What it covers | When you need it |
|------|----------------|------------------|
| [CLAUDE.md](CLAUDE.md) | Master AI context (auto-loaded by Claude Code) | Before touching code |
| [MEMORY.md](MEMORY.md) | Learnings, gotchas, "we already tried that" | Before debugging |
| [PRD.md](PRD.md) | Vision · personas · success metrics · risks | Scope discussions |
| [HLD.md](HLD.md) | Architecture · multi-tenancy · cost · threat model | Architecture decisions |
| [LLD.md](LLD.md) | Data contracts · tool registry · code patterns | Implementing a feature |
| [ROADMAP.md](ROADMAP.md) | 5-phase delivery plan + Akshansh API template | Sprint planning |
| [STATE.md](STATE.md) | Living capability matrix · what's live right now | Status check |
| [API-SPECS.md](API-SPECS.md) | Onsite v3 endpoints (built · observed · needed) | Integrating a new endpoint |
| [BUG-TRACKER.md](BUG-TRACKER.md) | Open + resolved issues by severity | Bug triage |
| [docs/data-model.md](docs/data-model.md) | BA · sub-activity · progress · dependency model | Understanding what the bot manipulates |
| [docs/multi-tenancy.md](docs/multi-tenancy.md) | Tenant isolation deep dive · threat model · DPDP compliance | Security questions |
| [docs/competitive-analysis.md](docs/competitive-analysis.md) | vs Procore Copilot · Powerplay · Onsite's existing bot | Positioning discussions |
| [docs/decisions.md](docs/decisions.md) | 8 ADRs with rationale + tradeoffs | "Why did we choose X?" |
| [docs/test-results.md](docs/test-results.md) | End-to-end test log | Regression debugging |

---

## 🛠 Tech Stack

- **Framework:** Next.js 15 App Router · React 19 · TypeScript strict
- **Styling:** Tailwind CSS 4 · custom dark theme · Plus Jakarta Sans
- **Frontend:** Client component · Web Speech API (voice STT) · sessionStorage (token)
- **Backend:** Next.js Route Handler · stateless · no DB
- **LLM:** Claude Sonnet 4.6 via OpenRouter (OpenAI-compatible tool use)
- **Auth:** Onsite Bearer JWT (per-request, never stored)
- **Deploy target:** Vercel (not yet deployed — pending Dhruv approval)
- **Storage:** Zero by design — see [ADR-001](docs/decisions.md)

---

## 💰 Cost Model (Phase 1 scale)

Per chat message with tool call: **~$0.011** (Claude Sonnet 4.6, 2 round-trips)
Per text-only chat reply: **~$0.006**

At 10K monthly active customers × 30 messages each = 300K messages/month → **~$1,500/month** LLM cost.
Vercel function cost is negligible. No DB cost (no DB).

Pricing hypothesis (refine with Sumit): ₹100/user/month → 87% gross margin at scale.
→ [HLD.md § Cost Architecture](HLD.md#6-cost-architecture)

---

## 🔒 Security Model (the short version)

- Token lives in customer's browser `sessionStorage` (clears on tab close)
- Token sent with each API request, used by our route to call Onsite
- **Token NEVER:** logged · persisted · stored · sent to LLM provider
- **No database** = no shared tables = structurally impossible to leak data across customers
- LLM provider receives only the customer's prose message + sanitized tool results

Anticipated question from Sumit: *"Can customer A see customer B's tasks?"*
Answer: **No, structurally impossible.** Detailed in [docs/multi-tenancy.md](docs/multi-tenancy.md).

---

## 🤝 Contributing

Before writing code, read in order:

1. [CLAUDE.md](CLAUDE.md) — master context
2. [MEMORY.md](MEMORY.md) — what we've already learned the hard way
3. [STATE.md](STATE.md) — current capability inventory
4. [API-SPECS.md](API-SPECS.md) — does Onsite have the endpoint? If not, you're blocked on Akshansh
5. **The Dhruv Rules** (in your memory file `reference_dhruv_rules.md`): minimal diffs · no half-finished implementations · type everything · test through real UI

After any change, update at least [STATE.md](STATE.md).

---

## 📞 Contact

| Role | Person | Reach |
|------|--------|-------|
| Product owner / builder | Dhruv Tomar | `dhruv.tomar@onsiteteams.com` |
| Onsite CEO | Akshansh Agarwal | (internal) |
| Onsite founder · primary contact | Sumit Garg | `sumit@onsiteteams.com` · +91 9560209605 |

For bug reports: open an issue at [aiagentwithdhruv/onsite-hub](https://github.com/aiagentwithdhruv/onsite-hub/issues) or add to [BUG-TRACKER.md](BUG-TRACKER.md).

---

## 📜 License

Proprietary · © Abeyaantrix Technology Private Limited (Onsite Teams)
