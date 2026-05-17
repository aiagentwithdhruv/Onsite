# Onsite Task AI — UI/UX Design Specification

> Feed this doc to v0, Lovable, Figma AI, ChatGPT Image, or any visual-generation tool to produce design variations. Everything below is a constraint, not a suggestion — if a generated screen ignores any of these, it's wrong.

**Last updated:** 2026-05-17
**Status:** Live in production at `localhost:3001/task-bot`
**Goal of this doc:** Let any designer/AI take this brief and generate a more futuristic, gradient-rich version of the existing 2-screen flow (Dashboard + Chat).

---

## 1. Brand & Positioning

**Product:** A natural-language AI chatbot embedded in Onsite (construction management SaaS). Site engineers / project managers speak or type in English / Hindi / mix, and the bot performs real Onsite operations (creating task dependencies, logging progress, listing tasks) via the REST API.

**One-line pitch:** *"Stop clicking 7 menus. Just tell Onsite what you want."*

**Audience:** Indian construction industry — site supervisors, PMs, foremen, sometimes the company owner. Often on phones. Often in noisy environments. Often code-switching Hindi↔English.

**Tone:** Warm, practical, construction-industry appropriate. Not techy. Not corporate.
- Good: *"Theek hai — Brickwork pehle finish hoga, phir Plastering."*
- Bad: *"Successfully created dependency record."*

---

## 2. Visual Identity

### 2.1 Colors (locked)

| Token | Hex | Use |
|---|---|---|
| `primary-deep` | `#1a0b50` | Brand gradient start, primary text on white |
| `primary-mid` | `#5b21b6` | Brand gradient middle |
| `primary-accent` | `#c73e5a` | Brand gradient end, destructive accents |
| `primary-gradient` | `linear-gradient(to right, #1a0b50, #5b21b6, #c73e5a)` | Hero, CTAs, brand text |
| `surface-bg` | `#fafafa` → `#fff` → `violet-50/30` | App background (light gradient top→bottom) |
| `surface-card` | `#fff` | Cards |
| `surface-card-elevated` | `#fff` with `shadow-md` + `border-slate-200` | Hovered/active cards |
| `accent-success` | `emerald-500` `#10b981` | Created dependencies, positive feedback |
| `accent-info` | `violet-500` `#8b5cf6` | Progress logging, AI thinking |
| `accent-warn` | `amber-500` `#f59e0b` | Sandbox env, in-progress |
| `accent-error` | `rose-500` `#f43f5e` | Errors, destructive actions |
| `accent-sky` | `sky-500` `#0ea5e9` | Tertiary stats (leaf tasks) |

**Never use:** pure black, pure white as primary text, orange, teal-mint, neon green.

### 2.2 Typography

- **Font family:** `Plus Jakarta Sans` (already loaded). Falls back to system sans.
- **Tabular numbers:** all stat numbers use `tabular-nums` class.
- **Type scale (px):** 10.5 (metadata) · 11 (chip) · 12.5 (body small) · 13 (body) · 14 (body large) · 15 (small header) · 16 (header) · 20 (stat) · 28 (hero stat) · 32 (page title)
- **Weights:** 400 body, 500 medium, 600 semibold, 700 bold. Use 700 sparingly — only on stat values + page titles.

### 2.3 Iconography

- **Source:** Lucide-style (lines, not solid). Stroke 2 to 2.5. Round caps.
- **Brand mark:** Sparkle (two stars: large + small) on gradient circle. Used as the AI avatar.
- Generated tools (Figma AI etc.) should match Lucide aesthetic.

### 2.4 Spacing

- **Border radii:** 8 (inputs) · 12 (chips, sub-cards) · 16 (cards) · 20 (hero) · 999 (pills).
- **Card padding:** 12–16px small, 16–20px medium, 20–24px large.
- **Vertical rhythm between blocks:** 24px between major sections.

### 2.5 Motion

- **Fade-in:** `transform: translateY(6px) → 0; opacity 0 → 1; 0.25s ease-out.` Applied to new messages, cards.
- **Slide from right:** drawers. `transform translateX(20px) → 0; cubic-bezier(0.16, 1, 0.3, 1); 0.25s`.
- **Bounce dots:** loading indicator, 3 dots with 0/150/300ms stagger.
- **Active press:** `active:scale-[0.98]` on buttons.

---

## 3. Application Structure

The app has **3 main views** (currently):

1. **Setup screen** — paste token / SSO (one-time)
2. **Dashboard** — landing after auth, shows stats + entry to chat
3. **Chat** — main interaction surface

There is also a **History drawer** (right-side slide-in, available from both Dashboard and Chat).

### 3.1 Navigation rules

- Dashboard → Chat (Start chatting CTA or Suggestion card)
- Chat → Dashboard (Back arrow, top-left of chat header)
- Either → History drawer (clock icon, top-right)
- Either → Sign out (sign-out icon, top-right)

---

## 4. View Specs

### 4.1 Setup screen

**Goal:** get a Bearer token. Should disappear after auth (Chrome extension auto-injects it in production).

**Layout (centered vertical):**
1. Hero: gradient sparkle avatar (64px) + glow blur behind, "Onsite AI" in gradient text, tagline *"Create dependencies, log progress. Bas bol diya — ho gaya."*
2. 3 benefit lines with green check icons.
3. Token form: password input + "how to get?" link → reveals console command + copy button.
4. Environment toggle (Sandbox / Production) as a 2-button segmented control.
5. Primary CTA: "Start Chat →" gradient button, full-width.
6. Footer privacy note.

**Mood:** mystical, gradient-heavy. Multiple soft blurred circles in violet & pink behind the main content (4 blurs: top-left, top-right, bottom-left, bottom-right, each ~256px, opacity 20%, blur-3xl).

### 4.2 Dashboard

**Goal:** Show value (time saved + actions taken) and surface entry points to chat.

**Layout (max-width 768px, centered):**

```
┌─────────────────────────────────────────────────┐
│ [Sparkle avatar] Onsite AI            🕐  ↩    │  ← Top bar
│                  Your assistant…              │
├─────────────────────────────────────────────────┤
│                                                 │
│  Hey there 👋                                   │  ← Greeting
│  Here's how I've been helping you save time.    │
│                                                 │
├──────────┬──────────┬──────────┬──────────────┤
│ TIME     │ TOTAL    │ DEPS     │ PROGRESS     │
│ SAVED    │ ACTIONS  │ CREATED  │ LOGGED       │
│  2h 15m  │   23     │   12     │    8         │  ← 4 stat tiles
│ 30 days  │ via chat │ created  │ entries      │
├─────────────────────────────────────────────────┤
│  WHAT I CAN DO FOR YOU                          │
│  ┌─────────────┬─────────────┐                  │
│  │ Create dep  │ Log progress│                  │  ← 4 suggestion cards
│  │ Find tasks  │ Hindi mix   │                  │
│  └─────────────┴─────────────┘                  │
├─────────────────────────────────────────────────┤
│  RECENT ACTIVITY                                │
│  ✓ Created dep: Wall putty → Polish  · 5m ago  │
│  ✓ Logged +1 sqm on Gypsum            · 2h ago │  ← Activity list
│  ✓ Created dep: Clearing → Removal    · 1d ago │
├─────────────────────────────────────────────────┤
│  CONTINUE A PAST CHAT                           │
│  🕐 S.S Interior Project · 28 msg · 1h ago →   │
│  🕐 Road project tasks   · 15 msg · 1d ago →   │
├─────────────────────────────────────────────────┤
│                                                 │
│         [ ✨ Start chatting ]  (sticky footer)  │
└─────────────────────────────────────────────────┘
```

**Stat tile design:**
- Time saved tile = filled gradient (violet 500→600), white text
- Other 3 tiles = white card, colored uppercase label, large dark number, gray sub-label

**Hero stat (Time saved):** the proudest number. Should feel important. Big tabular numbers. Sub-label "last 30 days".

**Background:** same light gradient + 2 large blurred circles (top-left, bottom-right).

### 4.3 Chat screen

**Goal:** the work surface. Conversation + tool result cards.

**Layout:**

```
┌─────────────────────────────────────────────────┐
│ ◀ [avatar] Onsite AI ▪Interior Project   🕐 + LIVE ↩ │  ← Sticky header
├─────────────────────────────────────────────────┤
│                                                 │
│  ✨ Hi! I'm Onsite AI.                          │  ← Welcome (1st turn only)
│  I can create task dependencies and …           │
│                                                 │
│  ┌─ RESUME A PAST CHAT ───┐                     │  ← Resume row (welcome only)
│  │ 🕐 S.S Interior Project │                     │
│  └─────────────────────────┘                     │
│                                                 │
│  ┌─[2x2 suggestion cards grid]─┐                │
│  │ Create dep │ Log progress  │                 │
│  │ Find tasks │ Hindi mix     │                 │
│  └─────────────────────────────┘                │
│                                                 │
│                  ┌─────────────────┐ U          │
│                  │ Show me tasks   │            │  ← User bubble (right)
│                  └─────────────────┘            │
│                                                 │
│  ✨ Here are 25 tasks…                          │  ← Bot bubble (left)
│     ┌─ Hierarchical tree (collapsible) ─┐       │
│     │ 1. CIVIL & CARPENTRY · 16d         │       │
│     │   ↳ 1.1 Gypsum… · 🔗1 dep · 12%   │       │
│     │   ↳ 1.2 Partition… · 🔗1 dep      │       │
│     │ 2. FLOORING                       │       │
│     └───────────────────────────────────┘       │
│     [👍] [👎]                                    │  ← Feedback per msg
│     [➤ Log progress…] [➤ Show deps…]            │  ← Suggested next chips
│                                                 │
├─────────────────────────────────────────────────┤
│ 🎤 [EN/हिं] Talk to me…              [send ➤] │  ← Input bar
└─────────────────────────────────────────────────┘
```

**Bubble styles:**
- User: gradient bubble (deep violet → mid violet), white text, right-aligned, tail on top-right
- Assistant: white bg, slate-200 border, slate-800 text, left-aligned, tail on top-left

**Tool result cards** (rendered alongside or below bot's text bubble):
- `dependency_created` — emerald accent header "DEPENDENCY CREATED", 2 numbered rows (1, 2), gradient arrow between them showing FS/SS/FF/SF + lag chip, copy + Undo buttons in footer
- `progress_recorded` — violet accent header "PROGRESS LOGGED", task name, sub-activity, big +N unit display, total quantity, optional notes block
- `task_stats` — multi-color stat grid + progress bars (Completed/In-progress/Not-started)
- `error` — rose accent header, message, "Try again" button

**Suggestion chips** (under latest bot message only):
- Pill shape, gradient violet-50 → pink-50 background, violet-200 border
- Small arrow icon left of text
- Click → fires as next user message

**Thinking indicator** (during load):
- Sparkle avatar + 3 bouncing dots
- Rotating status text every 1.8s: "Reading your request" → "Looking up your project" → … → "Wrapping up"
- After 12s: secondary line "Looking up data in <Project>…"

### 4.4 History drawer

**Layout (slides in from RIGHT, full-width mobile / 360px desktop):**

```
┌────────────────────────────────┐
│ Your chats                  ✕  │
│ Last 30 days · auto-saved      │
├────────────────────────────────┤
│  [+ New chat]                  │  ← Gradient pill button
├────────────────────────────────┤
│ ▸ S.S Interior Project ✏      │  ← Hover → pencil icon
│   28 msg · 1h ago              │
│                                │
│ ▸ Hey Hi                       │
│   59 msg · 11m ago             │
│                                │
│ ▸ Show me my interior projects │
│   28 msg · 1h ago              │
└────────────────────────────────┘
```

**Renaming flow:**
- Hover session row → pencil icon top-right
- Click pencil → inline input replaces the row
- Enter saves / Esc cancels
- Saved title becomes the bot's project anchor for that session

### 4.5 Layout variant for designers exploring alternatives

You may flip the layout — e.g., chat on the LEFT, history drawer on the LEFT, dashboard tiles on the right. Constraints to preserve:
- Brand gradient identity
- All 3 views (Setup → Dashboard → Chat) flow
- Back navigation from Chat to Dashboard
- Save indicator (always-on auto-save)

---

## 5. Mobile Design Guidance

### Breakpoints
- Mobile-first design. Tested at 375px (iPhone SE) and 390px (iPhone 14).
- `sm:` (640px) — split into 2 columns where appropriate.
- `lg:` (1024px) — 4-column stat grids.

### Tap targets
- All interactive elements ≥ 44×44px.
- Buttons in cards: 36px height min.

### Voice
- Mic button is **equal weight** to send button (site workers wear gloves).
- Language toggle (EN ↔ हिं) is a chip next to mic.

### Keyboard handling
- Input bar sits 16px above bottom safe area.
- Textarea auto-grows to max 112px.
- Enter submits, Shift+Enter newline.

---

## 6. Tool Result Card Design (canonical)

These cards are how the bot shows "I did the thing" instead of just text. They are the brand moments.

### 6.1 Dependency created

```
┌─────────────────────────────────────┐
│ ✓ DEPENDENCY CREATED                │  ← emerald header
├─────────────────────────────────────┤
│  [1]  Gypsum board false ceiling    │
│       44250d09…3bdc204f1            │
│       │                             │
│       │  ▶ Finish → Start · 3d lag  │  ← inline tag pill
│       │                             │
│  [2]  Partition work (Gypsum)       │
│       06500ba0…3d31bf12f3           │
├─────────────────────────────────────┤
│  ID: a7e5602c…629c   copy   ↩ Undo │  ← footer actions
└─────────────────────────────────────┘
```

### 6.2 Progress recorded

```
┌─────────────────────────────────────┐
│ ↗ PROGRESS LOGGED                   │  ← violet header
├─────────────────────────────────────┤
│  TASK                               │
│  Gypsum board false ceiling         │
│  Location 1                         │
│                                     │
│  ADDED              TOTAL           │
│  +1 sqm             412 sqm         │
│                                     │
│  NOTE                               │
│  "Test progress entry from AI bot"  │
└─────────────────────────────────────┘
```

### 6.3 Task stats

```
┌─────────────────────────────────────┐
│ ▌▌ INTERIOR PROJECT — AT A GLANCE  │  ← gradient header
├──────────────┬──────────────────────┤
│ TOTAL TASKS  │ LEAF TASKS           │
│     25       │     18               │
├──────────────┼──────────────────────┤
│ WITH DEPS    │ WITHOUT DEPS         │
│      2       │     16               │
├──────────────┴──────────────────────┤
│ PROGRESS MIX                        │
│ Completed   ███░░░░░░░ 30% (5)      │
│ In progress ███████░░░ 70% (12)     │
│ Not started ░░░░░░░░░░  0% (1)      │
└─────────────────────────────────────┘
```

### 6.4 Error

```
┌─────────────────────────────────────┐
│ ⓘ ERROR · 400                       │  ← rose header
├─────────────────────────────────────┤
│  One of the task IDs wasn't found.  │
│  Double-check the BA IDs.           │
│                                     │
│  [   ↻ Try again   ]                │  ← rose CTA
└─────────────────────────────────────┘
```

---

## 7. Voice & Tone for Bot Replies

- Lead with the result. Then a short explanation if useful.
- Use the user's language register (English / Hindi / mix). NEVER translate down to English when user used Hindi.
- Use **bold** for entity names ("Got it — **Interior Project**"), backticks for IDs only when essential.
- Append `Suggested next:` with 1–4 chip options after substantive replies. Frontend renders them as pills.
- Never apologize unless an error genuinely happened. No "Certainly!" / "I'd be happy to" filler.

---

## 8. AI Behavior Constraints (visible to designers)

These shape what the UI must support — keep them in mind when redesigning:

1. **Never asks for UUIDs.** Designers should never imagine a screen where the user is asked to paste an ID.
2. **Always-on auto-save.** No save toggle. No upload dialog. Auto.
3. **Smart caching.** The same question twice ≈ instant on the second hit. UX should communicate this implicitly (snappy response, not a re-loading state).
4. **Multi-step tool chains.** A single user message can trigger 3–5 server actions. The thinking indicator must NEVER feel stuck (rotating stages required).

---

## 9. When generating variants — checklist

Whatever AI tool is making the new design (v0, Lovable, Figma AI, etc.), it must satisfy:

- [ ] Brand gradient (`#1a0b50 → #5b21b6 → #c73e5a`) appears as the primary identity element on every screen
- [ ] Sparkle avatar (2-star icon) is the AI's visual stand-in everywhere
- [ ] At least one card type from §6 is rendered correctly
- [ ] Setup → Dashboard → Chat flow is preserved (or equivalent navigation)
- [ ] Mobile breakpoint at 375px works without horizontal scroll
- [ ] All tap targets ≥ 44px
- [ ] Voice input button is equal-weight to send button
- [ ] Auto-save indicator visible (not hidden in settings)
- [ ] No UUIDs asked of the user anywhere in copy

---

## 10. Prompts you can paste into image-gen tools

**For a hero mockup:**

> Design a mobile-first AI assistant dashboard for a construction-management product called "Onsite AI". Use a futuristic gradient palette: deep purple #1a0b50 to violet #5b21b6 to pink-red #c73e5a. Light theme with soft blurred gradient circles in the background (violet & pink at 20% opacity). The main screen shows 4 stat cards (Time Saved, Total Actions, Dependencies, Progress Logs), a "What I can do for you" section with 4 colorful action cards, and a Recent Activity list with green checkmark items. At the bottom, a large gradient CTA button "Start chatting". The brand mark is a sparkle icon on a gradient circle. Font: Plus Jakarta Sans. Border radius 16-20px on cards. Mobile dimensions 390x844. Premium, clean, slightly mystical.

**For the chat screen:**

> Design a mobile-first chat screen for an AI construction assistant. Header with back arrow, sparkle avatar, "Onsite AI · Interior Project" title, history clock icon and new-chat plus icon top-right, plus a green LIVE pill. Main chat area shows: user message bubble on the right (gradient violet→pink), AI response on the left (white card with subtle border) including a hierarchical task tree with collapsible parent rows (violet tinted background) and indented sub-rows with corner-arrow icons. Below the AI message: thumbs up/down feedback buttons, then pill-shaped suggestion chips. Input bar at bottom: mic button, EN/हिं language toggle, text input "Talk to me...", gradient send button. Background: light gradient with blurred violet/pink circles. Premium, futuristic, optimized for construction site workers on phones.

**For the dependency-created result card:**

> Design a result card for a successful task-dependency creation in an AI construction app. Card with emerald "DEPENDENCY CREATED" header strip. Two task rows: each shows a numbered chip (1, 2), the task name, and a faint UUID line below. Between them, a vertical connector and a violet pill labeled "Finish → Start · 3d lag" with arrow icon. Footer with monospace ID display, copy button, and a rose "Undo" button. Light card on white background, subtle shadow, rounded 16px. Modern, premium aesthetic.

---

## 11. Open design questions for future iteration

These are NOT decided yet — open to redesign:

- **Onboarding flow?** Currently zero — first turn just shows the welcome message and suggestion cards. Could add a 3-screen swipe ("Talk in any language" / "It saves time" / "Try it now") before first chat.
- **Voice-first mode?** Could replace the input bar with a giant mic when the device is in "site mode" (gloves on).
- **Dark mode?** Currently light-only. Construction sites in bright sun, so light is actually correct, but indoor offices may want dark.
- **Landscape on tablets?** Currently mobile-first / portrait; could explore a 2-column tablet layout (history on left, chat right).

---

## 12. Files / endpoints (for reference)

- Frontend: `Onsite/onsite-hub/src/app/task-bot/page.tsx`
- Admin: `Onsite/onsite-hub/src/app/task-bot/admin/page.tsx`
- Endpoints: `Onsite/onsite-hub/src/app/api/task-bot/*`
- Migrations: `Onsite/task-ai/database/*.sql`
- Live URL (local dev): `http://localhost:3001/task-bot`

---

*End of spec. Send PRs with design variants against `task-ai/` in the Onsite repo.*
