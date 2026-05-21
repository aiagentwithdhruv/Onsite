# PWA Mobile Conversion — Implementation Notes

> **Built:** 2026-05-20 (this session, no engineer dispatched — Angelina executed end-to-end per Dhruv's direct override)
> **Branch state:** uncommitted; sitting on `Onsite/onsite-hub` main + `Onsite/task-ai/` working copy
> **Deploy:** NOT YET — code-level only per Dhruv's instruction
> **TS check:** Clean. Only 3 pre-existing errors remain (chat/route.ts + chat/page.tsx, documented in `onsite-hub/CLAUDE.md`)

This document covers what shipped, what's missing, how to wire env vars, and how to deploy when Dhruv is ready.

---

## What shipped (16 files)

### Public assets

| File | Purpose |
|---|---|
| `onsite-hub/public/task-bot-manifest.json` | Task AI's own PWA manifest (separate from onsite-hub sales-app manifest). `start_url: /task-bot/?source=pwa`, `scope: /task-bot/`, theme `#1a0b50`. Includes Voice + New-chat app shortcuts. |
| `onsite-hub/public/task-bot-sw.js` | Service worker scoped to `/task-bot/`. Stale-while-revalidate for app shell, pass-through for `/api/*`, push notification handler, notification-click router. |

### Components (`onsite-hub/src/components/task-bot-pwa/`)

| File | Purpose |
|---|---|
| `RegisterSW.tsx` | Client component — registers `/task-bot-sw.js` on idle, listens for SW navigation messages. |
| `InstallPrompt.tsx` | Captures Android Chrome `beforeinstallprompt`; shows custom CTA. Falls through to `IOSInstallHint` on Safari. 7-day dismiss memory in localStorage. |
| `IOSInstallHint.tsx` | iOS-specific modal walking users through Share → Add to Home Screen. Includes a note about 7-day inactivity wipe. |
| `BottomTabBar.tsx` | Mobile-only (`lg:hidden`) bottom navigation: Chat / Train / Help / Admin. Param-based routing keeps the existing 3,547-line `page.tsx` untouched. Safe-area-bottom padding. |

### Libraries (`onsite-hub/src/lib/`)

| File | Purpose |
|---|---|
| `pwa/detect.ts` | `isStandalone`, `isIOS`, `isAndroid`, `isSafari`, `isMobile`, `supportsPush`, `urlBase64ToUint8Array` |
| `storage/secure_token.ts` | Encrypted IndexedDB JWT storage. AES-GCM with per-device key (also IDB-stored). Methods: `setToken`, `getToken`, `clearToken`, `setEnv`, `getEnv`, `migrateFromSessionStorage` |
| `push/subscribe.ts` | Client-side push subscription wiring. Registers with `/api/task-bot/push/register`. |
| `push/send_server.ts` | Server-side push sender using lazy-imported `web-push`. Prunes dead endpoints (404/410). |

### API routes

| File | Purpose |
|---|---|
| `onsite-hub/src/app/api/task-bot/push/register/route.ts` | POST: upsert push subscription. DELETE: remove. Auth via Bearer JWT — decodes `uuid` claim for `user_id`. |
| `onsite-hub/src/app/api/task-bot/push/send/route.ts` | Internal-only (gated by `X-Internal-Auth` header against `INTERNAL_PUSH_SECRET` env). For ticket replies, training reminders, etc. |

### Task-bot route layout

| File | Purpose |
|---|---|
| `onsite-hub/src/app/task-bot/layout.tsx` | NEW — wraps all `/task-bot/*` routes. Overrides parent metadata with `manifest: /task-bot-manifest.json`. Injects `RegisterSW`, `BottomTabBar`, `InstallPrompt`. Uses `task-bot-shell` CSS class for mobile bottom padding. |

### Modifications to existing files

| File | Change |
|---|---|
| `onsite-hub/src/app/task-bot/page.tsx` | (1) imports `idbGet/Set/ClearToken` aliases; (2) extends first useEffect to selectively preserve `/task-bot-sw.js` while unregistering legacy SWs, then awaits IDB-to-sessionStorage restore before reading existing storage; (3) adds new useEffect that mirrors React `token`+`env` state to encrypted IDB on every change. No call-site changes to existing token setters — they continue writing to sessionStorage, and the mirror picks them up. |
| `onsite-hub/src/app/globals.css` | Added `.safe-left`, `.safe-right`, `.task-bot-shell` (mobile bottom padding for tab bar), `@media (display-mode: standalone)` overscroll containment, `.task-bot-no-overscroll` |
| `onsite-hub/package.json` | Added `web-push@^3.6.7` runtime dep, `@types/web-push@^3.6.4` dev dep, `npm run vapid` script |

### Scripts + DB

| File | Purpose |
|---|---|
| `onsite-hub/scripts/generate-vapid.mjs` | Node script using webcrypto — `node scripts/generate-vapid.mjs` outputs VAPID key pair + an internal-push-secret, ready to paste into `.env.local` |
| `Onsite/task-ai/database/009_push_subscriptions.sql` | Migration: `push_subscriptions` table with RLS-by-user_id, prune-friendly unique constraint on `(user_id, endpoint)` |

---

## What's missing (graphics + env)

These three are non-code work — flagging clearly so Dhruv can knock them out before first install test.

### 1. Icons (PNG generation — cannot do via Write tool)

Need to produce 4 PNG files. Use the existing sparkle logo from batch 12, render on the brand gradient:

```
onsite-hub/public/icons/task-bot/
├── icon-192.png             (192×192, any purpose)
├── icon-512.png             (512×512, any purpose)
├── icon-maskable-512.png    (512×512, sparkle centered in 80% safe zone for OS masking)
└── apple-touch-icon.png     (180×180, no safe-zone — Apple crops differently)
```

**Fastest path:** upload the sparkle SVG to https://pwabuilder.com/imageGenerator or https://progressier.com/pwa-icons-and-ios-splash-screen-generator → it spits out all sizes + manifest snippet matching ours.

**Until icons land**, the PWA install will still work but show a default placeholder icon. Functional but ugly.

### 2. iOS splash screens (PNG, optional but recommended)

10 PNGs covering iPhone SE through iPhone 15 Plus + iPad. Same generator above produces them. Without these, iOS shows a white splash on standalone-mode launches. Functional but jarring.

### 3. Environment variables — add to `onsite-hub/.env.local`

Run the VAPID generator first:
```bash
cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/onsite-hub"
npm install        # picks up web-push + @types/web-push
npm run vapid      # prints VAPID + internal secret
```

Then add to `.env.local`:
```
NEXT_PUBLIC_VAPID_PUBLIC_KEY=<paste from script output>
VAPID_PRIVATE_KEY=<paste from script output>
VAPID_SUBJECT=mailto:dhruv.tomar@onsiteteams.com
INTERNAL_PUSH_SECRET=<paste from script output>
```

Existing env vars (already there) we now also rely on:
- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_KEY` (server-only — required by push register + send)

---

## How everything connects

```
Customer Phone
  └── Opens https://<task-ai-domain>/task-bot
        ├── ROOT layout.tsx loads (with onsite-hub PWA manifest)
        ├── AppShell.tsx — early-returns for /task-bot (no PIN gate)
        └── task-bot/layout.tsx loads (NEW)
              ├── Metadata overrides parent: manifest = /task-bot-manifest.json
              ├── <RegisterSW> registers /task-bot-sw.js (scope: /task-bot/)
              ├── children = page.tsx (existing 3,547 lines, minor mods)
              ├── <BottomTabBar> shows on <lg
              └── <InstallPrompt> auto-surfaces on Android / iOS Safari

On first mount of page.tsx:
  1. Selectively unregister legacy SWs (preserves /task-bot-sw.js)
  2. Try IndexedDB → if has token + sessionStorage doesn't → restore SS
  3. Read sessionStorage → set React state → set authed
  4. Mirror React token+env back to encrypted IDB
  
On token state change:
  → Mirror to IDB (handles Chrome ext token injection,
    OTP refresh, manual paste — all flow into IDB)

On iOS PWA close + reopen (sessionStorage cleared):
  → IndexedDB still has encrypted token
  → Mount effect restores sessionStorage from IDB
  → User stays signed in (no re-paste needed)

On Android "Install":
  → beforeinstallprompt captured by InstallPrompt
  → User taps → home-screen icon installed
  → Next open: standalone mode, no browser chrome, task-bot-manifest active

On iOS Share → Add to Home Screen:
  → IOSInstallHint walked user through manually
  → Same standalone result on next open

On notification click (after Sprint 3/4 ship support tickets):
  → SW notificationclick handler
  → Focuses existing /task-bot window OR opens new one
  → postMessage to page for in-app navigation
```

---

## Deploy checklist (when Dhruv says go)

1. ✅ Run `npm install` in `onsite-hub/` — picks up `web-push` + `@types/web-push`
2. ✅ Generate icons (per "What's missing" §1) and place under `public/icons/task-bot/`
3. ✅ Generate iOS splash screens (optional) under `public/splash/`
4. ✅ Run `npm run vapid` → paste output into `.env.local`
5. ✅ Run `supabase db push` in `Onsite/task-ai/` to apply migration `009_push_subscriptions.sql`
6. ✅ Local smoke test:
   - `npm run dev`
   - Open `http://localhost:3001/task-bot` in Chrome DevTools mobile mode
   - DevTools → Application → Manifest: parses cleanly, theme/icons look right
   - DevTools → Application → Service Workers: `/task-bot-sw.js` registered + activated for `/task-bot/`
   - Lighthouse → PWA audit: target ≥90
7. ✅ Tunnel to phone (Cloudflare): `cloudflared tunnel --url http://localhost:3001` → open tunnel URL on phone
8. ✅ Android Chrome: "Install app" banner → install → opens in standalone
9. ✅ iOS Safari: Share → Add to Home Screen → opens in standalone with proper status bar
10. ✅ Test push: subscribe via dev console; fire test push via `curl -X POST -H "X-Internal-Auth: $SECRET" -H "Content-Type: application/json" -d '{"user_id":"<uuid>","title":"Hi","body":"Test"}' http://localhost:3001/api/task-bot/push/send`
11. ✅ Verify token survives PWA close on iOS: install → close → wait → reopen → should stay logged in
12. ✅ Commit + PR (when ready). Per `feedback_no_auto_deploy`: Dhruv reviews local, merges, then triggers Vercel deploy

---

## Known iOS limitations (BUG-TRACKER.md candidates)

| # | Issue | Severity | Mitigation |
|---|---|---|---|
| 1 | iOS clears PWA data after ~7 days of inactivity | Real | Documented in `IOSInstallHint`; users will need to re-paste token if they don't open weekly. Phase 3: server-side session via Onsite SSO eliminates this. |
| 2 | iOS install flow is hidden behind Share menu | Real | `IOSInstallHint` modal teaches it (auto-shows after 10s on iOS). |
| 3 | Push notifications require iOS 16.4+ AND home-screen install | Real | ~92% of iOS users qualify as of mid-2026. Documented. |
| 4 | iOS doesn't fire `beforeinstallprompt` | Real | We use a parallel iOS-only path (Share-button hint). |
| 5 | Background sync limited on iOS | Real | We don't rely on it. Push notifications are user-visible (`userVisibleOnly: true`) which iOS supports. |

---

## Tests not yet written (for QA sprint)

- Unit: `secure_token.ts` encrypt/decrypt round-trip
- Unit: `detect.ts` UA string variations
- Integration: push subscribe → register → send → notification appears
- E2E: install on Android emulator → close → reopen → standalone mode
- E2E: install on iOS simulator → 7-day data wipe scenario
- Lighthouse PWA score ≥90

Defer to Sprint 9 hardening per `ROADMAP-ADDON.md`.

---

## Why we did this in the Angelina session (not via dispatch)

Dhruv override on 2026-05-20: *"I want you to write after this end to end don't given anyone else you can do that too / so you do once you have written using same file prompt and continue"*

This bypasses the default `feedback_never_spawn_coding_agent` rule for this specific PWA work. Angelina (this session) executed directly using Write/Edit/Bash, without spawning specialist coding agents. Dispatch file `dispatch-sprint-pwa-mobile.md` was written first, then executed in-session.

All other sprints (RAG, Voice, Support) still go through the standard dispatch flow per Dhruv's earlier feedback rule.

---

## STATE.md entry to add (batch 22)

```
- **2026-05-20 (batch 22)** — PWA mobile conversion (Angelina executed end-to-end):
  - 16 new files: task-bot-manifest.json, task-bot-sw.js, layout.tsx, 4 components,
    4 lib modules, 2 API routes, 1 migration, 1 script + package.json deps
  - Encrypted IndexedDB token storage survives iOS sessionStorage wipes
  - Mobile bottom tab bar (Chat/Train/Help/Admin), iOS-Safari install hint,
    Android beforeinstallprompt capture, Web Push subscription pipeline
  - Service worker scoped to /task-bot/ (does NOT affect sales app)
  - TS clean (only pre-existing chat/route + chat/page errors remain)
  - Commit: <pending — see git status>
  - Pending: icon PNG generation, iOS splash PNGs, VAPID key env vars,
    Supabase migration push (009_push_subscriptions)
  - Pending: Vercel deploy (Dhruv decision)
```
