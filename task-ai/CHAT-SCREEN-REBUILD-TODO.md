# Chat Screen Rebuild — TODO for fresh session

> Dhruv asked to align the chat interface end-to-end with the prototype
> mockup. Context was 80% used by the time we got to it — flagging the
> full rebuild here so the next session can start fresh.

## Source files
- `/Users/apple/Downloads/Onsite AI Prototype _standalone_.html` — the rendered HTML prototype Dhruv shared
- `/Users/apple/Downloads/Oniste Task Ai.zip` — extracted to `/tmp/onsite-mockup/`
- `/tmp/onsite-mockup/screens-chat.jsx` — chat-screen reference
- `/tmp/onsite-mockup/screens-desktop.jsx` — desktop variant
- `/tmp/onsite-mockup/styles.css` — design tokens

## What's already aligned (do NOT rebuild)
- ✅ Dashboard (hero time-saved tile with bar chart, full-width progress card with line chart, color-coded activity icons)
- ✅ History drawer (rename + delete)
- ✅ Start-chatting picker modal
- ✅ Service-worker cleanup on mount
- ✅ Skeleton placeholders
- ✅ Numbered options are clickable (pre-fill input)
- ✅ Session rename + project-context anchor
- ✅ Always-on chat persistence + refresh restore

## What still needs to align with the mockup (chat-screen specific)

### Header
- Title becomes `Onsite AI · <Project Name>` on a single line
- LIVE pill (green dot + "LIVE") moves under the title
- "auto-saved" muted text next to the LIVE pill
- Back arrow + Sparkle avatar + title + clock + plus + LIVE + sign-out

### DependencyCard polish
- Vertical gradient line connecting Row 1 → Row 2 (linear-gradient(180deg, #10b981, #8b5cf6))
- The "Finish → Start · 3d lag" pill sits on the connector line, not next to the row
- Bigger row-number badges (22px squares with gradient bg)

### ProgressCard polish
- Sectioned: TASK row | ADDED + TOTAL grid | NOTE row
- Each section separated by 1px slate-100 border
- ADDED column gets violet color label, TOTAL gets slate

### Task tree
- Each parent row shows duration tag on the right ("16d")
- Sub-rows show `🔗N` deps count + `N%` progress on the right
- Slimmer chevron, lighter parent background

### Follow-up chips
- "Suggested next" chips already exist but make them feel more clickable
- White bg with violet border + tiny right-arrow icon

### Input bar
- Pill style, 56px height, slate-100 background
- Mic icon → EN/हिं lang toggle pill → text input → gradient circular send button
- Placeholder updated to "Talk to me… create a dependency, log progress, or just ask" (already done)

### Thinking indicator
- Sparkle avatar + bubble with 3 dots + rotating stage text on a separate line
- Already implemented — just polish the bubble shape (rounded-tl-md style)

### Desktop variant
- 3-column layout on lg+ breakpoints:
  - Left sidebar: chat list (always visible, not drawer)
  - Middle: chat
  - Right sidebar: PROJECT CONTEXT + AT A GLANCE stat tiles + MENTIONED THIS CHAT + TIPS
- Mobile breakpoint stays single-column

## Implementation plan (when fresh context)

1. Read `screens-chat.jsx` + `screens-desktop.jsx` + `styles.css` fully
2. Update the chat header component
3. Polish DependencyCard + ProgressCard
4. Polish input bar
5. Add desktop 3-column layout with right context panel
6. Test on 375px mobile + 1440px desktop
7. Commit + update STATE.md + this file gets deleted after

## Don't forget

- Brand gradient is `linear-gradient(110deg, #1a0b50 0%, #5b21b6 52%, #c73e5a 100%)` (110deg, not 90 or 135)
- Font is Plus Jakarta Sans (already loaded)
- The mockup uses CSS vars: `--ink-900/700/500/400/300/200/100` for text greys
- Tabular nums on every numeric value
- All buttons get `active:scale-[0.97]` for the press effect
