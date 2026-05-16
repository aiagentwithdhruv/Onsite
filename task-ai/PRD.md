# Product Requirements Document — Onsite Task AI

**Owner:** Dhruv Tomar | **Status:** Draft v1.0 | **Last updated:** 2026-05-17

---

## 1. Vision

> **Make Onsite as easy to use as sending a WhatsApp message.**

Today, a site engineer who wants to mark "plastering depends on brickwork" must: open the Onsite app → navigate to project → tasks → find brickwork → find plastering → click dependencies → "Add" → search for the other task → pick type → save. That's 8 taps minimum, with autocomplete dropdowns that don't work well on a phone, in a noisy site environment, possibly with one hand free.

With Onsite Task AI, the same engineer types or speaks **one sentence**: *"plastering ko brickwork ke baad start karna hai."* The bot does the 8 taps. The Gantt chart updates. Done in under 5 seconds.

## 2. The Problem

### 2.1 Quantified pain

Onsite customers do dozens of dependency/progress operations per project per day. Each manual operation takes ~45 seconds and is error-prone (wrong task picked, wrong direction of dependency). On a 200-task project, that's ~2.5 hours of manual data entry per project manager per week.

### 2.2 User research signals

From the recording with Akshansh's team (2026-05-17):
- *"User task dependency me jo tasks bane hain vo AI ko bolega"* — customers want to talk to AI, not navigate menus
- *"Customer ko interface dena hai"* — Akshansh has a working Claude-in-terminal version; needs a customer UI
- *"Standardize karni hogi"* — flow needs to be consistent across all customers

From the Apr 14-24 Fireflies analysis (216 demos): the #1 friction point cited by prospects is "the app is too complex for our site team to use."

### 2.3 Competitive context

Onsite already has *some* AI feature (per Dhruv). We've not yet seen what it does, but our hypothesis:
- It's an FAQ/support bot ("how do I export a BOQ?")
- It's NOT action-taking (doesn't actually modify project data)

This product is the action layer — natural language → real API operations.

## 3. Users

### 3.1 Primary persona — "Rakesh, the Project Manager"

- Age 35–55, runs 3–10 active projects
- Carries a phone constantly, laptop occasionally
- Mixes Hindi and English fluently; prefers Hindi for technical terms
- Cares about: deadlines, dependencies, who's blocked, cost overruns
- Pain: spends 30+ min/day on data entry his team should be doing
- **What he says about our bot:** *"Bas bol diya, ho gaya."*

### 3.2 Secondary persona — "Anil, the Site Engineer"

- Age 25–40, on-site daily, wears safety gloves often
- Voice-first user; types only when forced
- Cares about: logging progress, raising issues, requesting materials
- Pain: typing Hindi on phone keyboard with gloves is slow
- **What he says about our bot:** *"Mike pe bol ke, progress chala gaya."*

### 3.3 Tertiary persona — "Sumit, the Onsite founder"

- The buyer-of-the-buyers (Onsite sells this to construction companies)
- Cares about: differentiation vs Procore/Powerplay, churn reduction, expansion revenue
- Pain: customers cancel because their team "couldn't learn the app"
- **What he says about our bot:** *"Demo mein ye dikha dete hain, deal close ho jaata hai."*

## 4. Goals & Non-Goals

### 4.1 Goals (Phase 1 — MVP, shipped)

✅ Create task dependencies via natural language
✅ Record task progress via natural language
✅ Voice input (English + Hindi)
✅ Works on mobile and desktop
✅ Stateless multi-tenant (one deployment serves all Onsite customers)

### 4.2 Goals (Phase 2 — daily-driver readiness, target: 2 weeks)

- List tasks by project name (no UUID paste)
- List sub-activities under a task (auto-resolve "Location 1")
- Update / delete dependencies
- Add new task / sub-task
- Update task progress in plain language
- Conversation memory within a session
- Error messages in user's language

### 4.3 Goals (Phase 3 — production launch, target: 6 weeks)

- Embedded inside Onsite app (auto-auth, no token paste)
- Multi-language UI (Hindi, English, Tamil, Telugu)
- Audit log of bot actions (visible to project admins)
- Rate limiting per customer
- Bot suggestions ("3 tasks are typically linked after this one — want me to set those up?")

### 4.4 Non-goals (won't build)

- ❌ A general-purpose chatbot (we don't answer "what's the weather")
- ❌ Persistent chat history across sessions (privacy + complexity for marginal value)
- ❌ Document upload / OCR (separate product)
- ❌ Replacing Onsite's existing UI (we augment, not replace)
- ❌ Offline mode (depends on Onsite API; Onsite isn't fully offline either)

## 5. Functional Requirements

### 5.1 Must-have (Phase 1+2)

| ID | Requirement | Status |
|----|-------------|--------|
| F1 | Create task dependency (4 types, lag 0–999) | ✅ Done |
| F2 | Record task progress (quantity, date, notes) | ✅ Done |
| F3 | Voice input (en-IN, hi-IN) | ✅ en-IN done, hi-IN pending |
| F4 | List tasks in a project by name | ❌ Phase 2 |
| F5 | List sub-activities under a task | ❌ Phase 2 |
| F6 | Update dependency type/lag | ❌ Phase 2 |
| F7 | Delete dependency | ❌ Phase 2 |
| F8 | Add new task or sub-task | ❌ Phase 2 |
| F9 | Update task metadata (name, dates, assignee) | ❌ Phase 2 |
| F10 | Conversation memory in-session | ⚠️ Partial (history sent, but tool-call context not preserved) |
| F11 | Error messages user-friendly + multi-language | ⚠️ Partial |

### 5.2 Should-have (Phase 3)

| ID | Requirement |
|----|-------------|
| S1 | Auto-auth via Onsite SSO (no token paste) |
| S2 | Embedded UI inside Onsite app (iframe or in-app screen) |
| S3 | Audit log per customer (what did the bot do? when? for whom?) |
| S4 | Rate limiting per company_id |
| S5 | Hindi voice input + Hindi response |
| S6 | Tamil + Telugu UI strings |
| S7 | Cost-per-customer tracking (LLM tokens used) |

### 5.3 Nice-to-have (Phase 4+)

| ID | Requirement |
|----|-------------|
| N1 | Material request creation ("order 50 bags of cement for Wiring Installation") |
| N2 | Inspection completion ("mark electrical inspection passed") |
| N3 | Photo upload with auto-tagging ("here's a progress photo of Foundation Wall") |
| N4 | DPR (Daily Progress Report) generation |
| N5 | RA Bill draft generation |
| N6 | Quotation update |
| N7 | Predictive insights ("you're 3 weeks behind on Insulation") |
| N8 | Critical-path risk alerts |

## 6. Non-Functional Requirements

### 6.1 Performance

- Tool-call latency target: < 3 seconds end-to-end (user message → bot reply with API result)
- Conversation latency target: < 1.5 seconds for text-only replies (no API call)
- Voice STT latency: < 1 second (Web Speech API native)

### 6.2 Reliability

- 99.5% uptime in Phase 3+ (matches Onsite's SLA)
- Graceful degradation: if Onsite API is down, bot tells the user clearly ("Onsite servers are slow right now — try again in a minute")
- Graceful degradation: if LLM is down, fallback to a basic UI with form fields

### 6.3 Security

- Token never persisted server-side (see HLD § Auth)
- Token never sent to LLM provider
- No PII logging (chat messages may contain task names but never tokens/UUIDs in logs)
- HTTPS only
- CSP headers on the chat page
- LLM provider (OpenRouter → Anthropic) is contractually obligated not to train on inputs (verify ToS quarterly)

### 6.4 Scale

- Target: 1,000 concurrent customers (Onsite has ~10,000 companies on books, plan for 10% concurrency)
- Target: 100,000 chat messages per day across all customers
- Cost target: under ₹5/customer/month at this scale (~₹50K/month total at 10K customers)

### 6.5 Localization

- Phase 2: en-IN, hi-IN (UI + voice)
- Phase 3: ta-IN (Tamil), te-IN (Telugu)
- Phase 4: bn-IN, mr-IN, gu-IN (Bengali, Marathi, Gujarati) — based on Onsite's customer distribution

## 7. Success Metrics

### 7.1 Adoption (Phase 2 ship)

- 10% of Onsite's active monthly users try the bot in the first month
- 30% week-2 retention of those who tried it
- Median 3+ bot actions per active user per week

### 7.2 Activity quality (Phase 3)

- 80% of bot-initiated API calls succeed (no validation errors)
- < 5% of bot replies require user clarification beyond 1 turn
- < 1% of bot replies create wrong data (audit log spot-checks)

### 7.3 Business impact (Phase 3)

- 15% reduction in customer-reported "app too complex" tickets
- 20% increase in "tasks-per-active-project" metric (proxy: users doing more because friction is lower)
- 2x improvement in demo close rate when bot is shown (Sumit's KPI)

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Onsite blocks our customer-facing access | Low | High | Get explicit written sign-off from Akshansh + Sumit before launch |
| LLM hallucinates wrong UUID, modifies wrong data | Medium | High | Tool args validated server-side; Phase 2 pre-flight check before destructive ops |
| Cost spirals at scale | Medium | Medium | Per-customer rate limits; switch to Haiku for simple queries; aggressive caching |
| Customers confused by error messages | High | Medium | Iterate on error UX with real customer screenshots after Phase 2 launch |
| Hindi voice STT inaccurate | Medium | Medium | Web Speech API works well for Indian-accented Hindi; fall back to text input gracefully |
| Token signature errors confuse users | Medium | Low | Phase 3 SSO eliminates the paste step entirely |
| Multi-tenant isolation bug leaks data | Low | Catastrophic | Stateless architecture (HLD) makes this structurally near-impossible; quarterly audit |

## 9. Open Decisions

1. **Pricing model for Onsite (how Sumit charges customers):** add-on at ₹X/user/month? Bundled into Business+ plan? Free tier with usage cap? — Discuss with Sumit after Phase 2.
2. **Where the bot lives in the Onsite UI:** floating chat bubble (always-on)? Dedicated tab? Replacing the FAB on Tasks page? — A/B test in Phase 3.
3. **Default LLM:** Sonnet 4.6 (current) vs Haiku 4.5 (cheaper) vs Kimi K2.5 (good Hindi)? — Benchmark in Phase 2.
4. **Voice TTS for replies:** Web Speech API native (free) vs ElevenLabs (better Hindi)? — Phase 3 decision.
5. **Audit log retention:** 30 days? 90 days? Customer-configurable? — Compliance review needed.

## 10. References

- [HLD.md](HLD.md) — architecture, multi-tenancy
- [LLD.md](LLD.md) — data model, API contracts, components
- [ROADMAP.md](ROADMAP.md) — phased delivery plan
- [docs/competitive-analysis.md](docs/competitive-analysis.md) — vs Procore, Powerplay, Onsite's own bot
- [docs/multi-tenancy.md](docs/multi-tenancy.md) — scale to N customers
- Onsite company context: `Onsite/.claude/CLAUDE.md`
