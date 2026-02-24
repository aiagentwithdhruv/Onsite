# Research: Sales Team Automation & Lead-Based Decisions

**Goal:** Make the system so automated that the team does **not** need to discuss every task—they know in the morning, afternoon, and evening what to do and how to perform. Help both **reps** (execution) and **managers** (decisions based on lead/pipeline data).

---

## 1. What Top Sales Orgs Do (Best Practices)

- **Single source of truth:** One place (CRM + pipeline) so no “whose list is right?” discussions.
- **Daily focus list:** Each rep gets a **prioritized list** (who to call today) so they don’t decide from a 300-row sheet.
- **Time-of-day cadence:** Morning = “Here’s your day.” Afternoon = “What’s left / reprioritise.” Evening = “Tomorrow’s prep” (optional).
- **Manager visibility without meetings:** Managers see team health, who’s stuck, who’s winning, and **suggested coaching** (e.g. “Anjali: 12 stale leads—suggest 15-min sync”).
- **Lead-based decisions:** Decisions (who to help, where to focus) are driven by **lead/pipeline data** (stale, hot, demo dropout, conversion by source), not gut feel.
- **Clear “next best action” per lead and per rep:** So the rep doesn’t have to think “what should I do next?”—the system says it.

---

## 2. How This Maps to Our System Today

| Need | Current system | Gap |
|------|----------------|-----|
| Morning “what to do” | Daily brief (from pipeline agent) + Dashboard home (brief + leads + alerts) | Briefs use **Zoho/leads table**; when only CSV/Intelligence is used, no brief. Dashboard home shows 0 leads if no Zoho. |
| Afternoon “what’s left” | None | No midday/afternoon refresh or “rest of day” view. |
| Evening / tomorrow prep | None | No end-of-day summary or “tomorrow’s top 5”. |
| Manager: team health | Intelligence Team tab, Agent profiles, Alerts | Good. Missing: one **manager home** with “who needs attention” and suggested 1:1s. |
| Lead-based decisions | Intelligence (stale, sources, aging, sales), Smart alerts, Agent next_best_action | Strong. Can surface more **per-lead** “do this next” on dashboard. |
| No-meeting clarity | Alerts (Telegram/Discord/WhatsApp/Email), Smart actions, Next best action on agents | Good. Missing: **scheduled delivery** (e.g. morning brief + afternoon digest) so they don’t have to open the app to “know”. |

---

## 3. What to Build (Prioritised)

### A. Fix & unify “morning” (so briefs work end-to-end)

- **Done:** Pipeline agent now saves `brief_content` and `priority_list` so briefs show correctly in Briefs page and Dashboard home.
- **Optional:** When **no Zoho** (only Intelligence CSV):
  - **Intelligence-powered brief:** Generate a short “Today” text from `dashboard_summary` + `agent_profiles` (e.g. “You have 12 stale leads; top priority: follow up X, Y, Z. Next: complete 3 pending demos.”) and store it as today’s brief for that user (by deal_owner → user). Then Dashboard home and Briefs page show it even without Zoho.

### B. “Afternoon” and “Evening” (no-meeting clarity)

- **Afternoon digest (e.g. 2–3 PM):**  
  - One message (Telegram/Email/Discord): “Rest of day: N calls left, M stale to touch, K demos pending.”  
  - Optional: “Top 3 leads to call next” (from priority list or Intelligence).
- **Evening / tomorrow prep (e.g. 6 PM):**  
  - Short summary: “Tomorrow: N hot leads, M follow-ups, your next best action: …”  
  - Can reuse same delivery channels (Telegram, etc.) so reps get it without opening the app.

Implementation: reuse **alert_delivery** (Telegram, Discord, WhatsApp, Email). Add scheduled jobs (cron/n8n) that:
1. Build “afternoon digest” and “evening summary” from Intelligence summary + agent profiles (and Zoho when available).
2. Send to each user’s enabled channels (same as alerts).

### C. Manager: one screen to “take better decisions based on lead”

- **Manager dashboard / home:**  
  - One view: team list with **per-rep** summary: leads, stale count, demos pending, conversion, “suggested action” (e.g. “Sync: 12 stale”, “Celebrate: top closer”).  
  - Data from: `dashboard_summary.summary_by_owner`, `agent_profiles`, `smart_alerts` (filter by agent).  
- **Lead-based decisions:**  
  - “Who to help”: sort/filter by stale, demo dropout, low conversion.  
  - “Where to focus”: use existing Intelligence (Sources, Aging, Team) so manager sees which rep/source/region needs attention.  
- **Suggested 1:1s:**  
  - e.g. “Anjali: 15 stale, 3 demo dropouts → suggest 15-min call.”  
  - Can be a small “Manager actions” block on Admin or a dedicated “Manager” tab.

### D. Rep: “know exactly what to do” without opening the app

- **Morning:**  
  - Brief (and optional Intelligence one-liner) delivered via Telegram/WhatsApp/Email at a fixed time.  
  - “Today: N leads to follow up, M demos to close, your next best action: …”
- **In-app:**  
  - Dashboard home: **first block = “Your next 3 things”** (from next_best_action + smart actions + today’s priority list if we have it).  
  - So even if they don’t read the message, the first screen says what to do.
- **Alerts:**  
  - Already delivered to Telegram/Discord/WhatsApp/Email; keep critical/high visible so they act without a meeting.

### E. Smoothness and automation (100% no-discussion goal)

- **Scheduled sends:**  
  - Morning brief (already in pipeline): ensure it’s sent at 7:30 AM (or configurable).  
  - Afternoon digest + evening summary: new jobs, same delivery stack.  
- **One “Daily plan” per rep:**  
  - Stored or generated: “Call these 5, follow up these 3, close these 2.”  
  - Shown on Dashboard home and (optionally) in brief/digest.  
- **All by lead data:**  
  - Every suggestion (next action, manager 1:1, afternoon/evening) comes from **lead/pipeline/agent data**, not manual input, so decisions are consistent and auditable.

---

## 4. Quick Wins (Already Done or Small Additions)

- **Done:** Daily pipeline saves `brief_content` and `priority_list` so briefs appear in UI.
- **Easy:** Dashboard home “Your next 3 things” block: show `summary.action_items` (or agent `next_best_action`) when user has Intelligence data; when they have a brief, show “1. Read today’s brief” plus top 2 action items.
- **Easy:** Manager view: add an “Admin” or “Team” section that lists reps with stale count, next_best_action, and “Suggested: 15-min sync” when stale > threshold.

---

## 5. Summary

| Who | Morning | Afternoon | Evening | In-app |
|-----|---------|-----------|---------|--------|
| **Rep** | Brief + (optional) Intelligence one-liner via Telegram/WhatsApp/Email | Digest: “Rest of day: N calls, M stale” | “Tomorrow: top 5 + next action” | Dashboard: “Your next 3 things” + alerts |
| **Manager** | Same channels: team summary + “Who needs attention” | Digest: team stats + suggested 1:1s | Optional: tomorrow’s team focus | Manager home: rep list + suggested actions (lead-based) |

**Outcome:** The team knows what to do and how to perform **without** discussing every task in meetings; managers take better decisions **based on lead data** (stale, conversion, source, rep) in one place.
