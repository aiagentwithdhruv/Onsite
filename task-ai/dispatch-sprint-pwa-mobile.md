# Dispatch — PWA Mobile-Native Conversion

> **For:** Atlas (paste this entire file as the first message of a FRESH Claude Code session)
> **From:** Angelina, PM for Onsite Task AI
> **Date dispatched:** 2026-05-20
> **Branch:** `feat/pwa-mobile` off latest `onsite-hub` main
> **Duration:** 3-4 days (parallel-able with Sprint 1 RAG; doesn't conflict)
> **Deploy:** NO. Code-only. Dhruv decides deploy + domain separately.
> **Spec source:** This file + existing mobile design in batches 11-14 (STATE.md)

You are Atlas, the engineer for the PWA conversion. Job: turn the existing `/task-bot` mobile responsive UI into a true installable Progressive Web App with native feel on iOS + Android. **No new product features** — this is a packaging + polish sprint. **Lift, don't invent.**

---

## §A — Read before writing any code (45 min)

In order:

1. `Onsite/task-ai/CLAUDE.md` — product context
2. `Onsite/task-ai/STATE.md` — what's shipped (especially batches 11, 12, 13, 14 — mobile + desktop layout)
3. `Onsite/onsite-hub/src/app/task-bot/page.tsx` — the existing UI you'll polish (do NOT rewrite; extend)
4. `Onsite/onsite-hub/src/app/layout.tsx` — where you'll add PWA meta tags
5. `Onsite/onsite-hub/next.config.js` — to confirm we're on Next.js 15 App Router (PWA setup differs from Pages router)
6. `Onsite/task-ai/MEMORY.md` — token gotchas
7. `Onsite/task-ai/docs/multi-tenancy.md` — token invariants (still apply, but JWT storage location changes)
8. `~/.claude/projects/.../memory/reference_dhruv_rules.md` — 17 rules
9. **Critical:** open the current chat-bot page on Chrome mobile DevTools at iPhone-SE width (375px) → walk through Setup → Dashboard → Chat → Voice → Sidebar to feel what's missing. Take screenshots. We're polishing what you observe.

Reply: "Read complete. Current mobile UI screenshotted. Starting PWA sprint." Then proceed.

---

## §B — Files you'll create / modify

### B.1 — PWA core files (NEW)

| # | File | Purpose |
|---|---|---|
| P1 | `Onsite/onsite-hub/public/manifest.json` | Web App Manifest — name, icons, theme color, display mode |
| P2 | `Onsite/onsite-hub/public/sw.js` | Service worker — offline shell cache, push handler, install lifecycle |
| P3 | `Onsite/onsite-hub/public/icons/icon-192.png` | Maskable icon (use the existing sparkle logo from batch 12, render at 192×192 with safe zone) |
| P4 | `Onsite/onsite-hub/public/icons/icon-512.png` | Same, 512×512 |
| P5 | `Onsite/onsite-hub/public/icons/icon-maskable-512.png` | Maskable variant — sparkle logo centered in 80% safe zone, 20% bleed for OS masking |
| P6 | `Onsite/onsite-hub/public/icons/apple-touch-icon.png` | 180×180, Apple's required size, NO maskable safe-zone (Apple crops differently) |
| P7 | `Onsite/onsite-hub/public/icons/favicon.ico` | 32×32 multi-resolution |
| P8 | `Onsite/onsite-hub/public/splash/` | 10 iOS splash PNGs (iPhone SE, 12 mini, 12/13/14, 14 Pro, 14 Pro Max, 15, 15 Plus, iPad mini, iPad Pro). Use design from batch 9 setup screen — gradient `#1a0b50 → #5b21b6` with centered sparkle. |
| P9 | `Onsite/onsite-hub/src/app/layout.tsx` | Add `<head>` PWA meta tags + apple-specific tags |
| P10 | `Onsite/onsite-hub/src/components/pwa/RegisterSW.tsx` | Client component that registers service worker on mount |
| P11 | `Onsite/onsite-hub/src/components/pwa/InstallPrompt.tsx` | Custom install CTA — captures `beforeinstallprompt` on Android; shows tutorial modal on iOS Safari |
| P12 | `Onsite/onsite-hub/src/components/pwa/IOSInstallHint.tsx` | iOS-only "Tap Share → Add to Home Screen" tooltip with screenshot |
| P13 | `Onsite/onsite-hub/src/lib/pwa/detect.ts` | Helpers: `isStandalone()`, `isIOS()`, `isInstallable()` |

### B.2 — Push notifications (NEW)

| # | File | Purpose |
|---|---|---|
| N1 | `Onsite/onsite-hub/src/lib/push/keys.ts` | VAPID public + private key wrappers (env-loaded) |
| N2 | `Onsite/onsite-hub/src/lib/push/subscribe.ts` | Client-side: `navigator.serviceWorker.pushManager.subscribe({applicationServerKey, userVisibleOnly: true})` |
| N3 | `Onsite/onsite-hub/src/app/api/push/register/route.ts` | POST endpoint: stores subscription in `push_subscriptions` table per user |
| N4 | `Onsite/onsite-hub/src/app/api/push/send/route.ts` | Server-only: internal endpoint to fire push via `web-push` npm lib |
| N5 | `Onsite/onsite-hub/src/lib/push/send_server.ts` | Server wrapper — used by ticket-reply notifications, training reminders, etc. |
| N6 | `Onsite/task-ai/database/009_push_subscriptions.sql` | New table with RLS-by-user_id |
| N7 | Update `public/sw.js` | Add `self.addEventListener('push', ...)` + `self.addEventListener('notificationclick', ...)` handlers |

### B.3 — Mobile-native polish (MODIFY existing)

| # | File | Change |
|---|---|---|
| M1 | `Onsite/onsite-hub/src/app/task-bot/page.tsx` | Add `<BottomTabBar>` for `<lg` viewport (4 tabs: Chat / Train / Help / Admin). Hide existing header icons on mobile (move actions to tab bar). |
| M2 | `Onsite/onsite-hub/src/components/task-bot/BottomTabBar.tsx` | NEW — fixed bottom, safe-area-inset-bottom padding, active tab gradient highlight, 56pt height |
| M3 | `Onsite/onsite-hub/src/app/globals.css` | Add `env(safe-area-inset-*)` handling for header (top) + bottom tab bar (bottom). Add `overscroll-behavior: contain` on chat scroll container (disable pull-to-refresh inside chat). |
| M4 | Input bar in `page.tsx` | On mobile: voice button 56pt diameter centered, send button 44pt right, text input fills space. On desktop: keep current ratio. |
| M5 | Audit tap targets | Sidebar pencil/trash currently ~24pt. Bump to ≥44pt with padding. Suggestion chips: ≥44pt height. |
| M6 | `<meta name="theme-color">` | Match `#0f0a2e` in `<head>` |
| M7 | iOS status bar style | `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">` so chat extends under status bar with our gradient visible |

### B.4 — JWT storage migration (security)

| # | File | Change |
|---|---|---|
| J1 | `Onsite/onsite-hub/src/lib/storage/secure_token.ts` | NEW — wraps IndexedDB; stores JWT encrypted with `crypto.subtle.encrypt` using a per-device key (also IndexedDB-stored). Methods: `set(token)`, `get()`, `clear()`. |
| J2 | `Onsite/onsite-hub/src/app/task-bot/page.tsx` | Migration: on mount, check `sessionStorage.taskbot_token` — if exists, migrate to IndexedDB then clear sessionStorage. New token reads come from IndexedDB. |
| J3 | Background refresh logic | Every 50 min, if token exp <10 min, call Onsite's `/refresh` (if it exists — verify with Akshansh or check MEMORY.md). Fallback: clear JWT + show "session expired" toast → user re-pastes. |

---

## §C — Manifest.json full content

```json
{
  "name": "Onsite Task AI",
  "short_name": "Onsite AI",
  "description": "Talk to Onsite. Tasks, progress, dependencies — voice or text.",
  "start_url": "/task-bot",
  "scope": "/task-bot/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#0f0a2e",
  "theme_color": "#0f0a2e",
  "lang": "en-IN",
  "dir": "ltr",
  "categories": ["business", "productivity", "utilities"],
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "shortcuts": [
    {
      "name": "New chat",
      "short_name": "New chat",
      "description": "Start a new conversation",
      "url": "/task-bot?action=new",
      "icons": [{ "src": "/icons/icon-192.png", "sizes": "192x192" }]
    },
    {
      "name": "Voice",
      "short_name": "Voice",
      "description": "Start voice mode",
      "url": "/task-bot?action=voice",
      "icons": [{ "src": "/icons/icon-192.png", "sizes": "192x192" }]
    }
  ],
  "prefer_related_applications": false
}
```

Place at `Onsite/onsite-hub/public/manifest.json`. Reference in `<head>` via `<link rel="manifest" href="/manifest.json">`.

---

## §D — Service Worker structure (sw.js)

```js
// Onsite/onsite-hub/public/sw.js
const CACHE_VERSION = 'onsite-ai-v1'
const APP_SHELL = ['/task-bot', '/manifest.json', '/icons/icon-192.png', '/icons/icon-512.png']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_VERSION).then((c) => c.addAll(APP_SHELL)))
  self.skipWaiting()
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  // Never cache API calls — they're per-request, per-user
  if (url.pathname.startsWith('/api/')) {
    return  // pass through to network
  }
  // Stale-while-revalidate for app shell
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const network = fetch(e.request).then((res) => {
        if (res.ok) {
          const clone = res.clone()
          caches.open(CACHE_VERSION).then((c) => c.put(e.request, clone))
        }
        return res
      })
      return cached || network
    })
  )
})

self.addEventListener('push', (e) => {
  if (!e.data) return
  const payload = e.data.json()
  e.waitUntil(
    self.registration.showNotification(payload.title || 'Onsite AI', {
      body: payload.body || '',
      icon: '/icons/icon-192.png',
      badge: '/icons/icon-192.png',
      tag: payload.tag || 'default',
      data: payload.data || {},
      requireInteraction: payload.urgent === true,
    })
  )
})

self.addEventListener('notificationclick', (e) => {
  e.notification.close()
  const target = e.notification.data?.url || '/task-bot'
  e.waitUntil(
    clients.matchAll({ type: 'window' }).then((wins) => {
      const existing = wins.find((w) => w.url.includes('/task-bot'))
      if (existing) {
        existing.focus()
        existing.postMessage({ type: 'navigate', target })
      } else {
        clients.openWindow(target)
      }
    })
  )
})
```

---

## §E — Layout.tsx PWA `<head>` additions

```tsx
// Add inside <head> in Onsite/onsite-hub/src/app/layout.tsx
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0f0a2e" />
<meta name="application-name" content="Onsite Task AI" />

{/* iOS */}
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-title" content="Onsite AI" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
{/* Splash screens — generate via https://progressier.com/pwa-icons-and-ios-splash-screen-generator from gradient + sparkle, drop into /public/splash/ */}
<link rel="apple-touch-startup-image" href="/splash/iphone-se.png" media="(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)" />
{/* ... 9 more splash entries per device size ... */}

{/* Android */}
<meta name="mobile-web-app-capable" content="yes" />

{/* Viewport — important: viewport-fit=cover enables safe-area-inset */}
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
```

---

## §F — Safe-area CSS (globals.css additions)

```css
/* In Onsite/onsite-hub/src/app/globals.css */

:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --safe-left: env(safe-area-inset-left, 0px);
  --safe-right: env(safe-area-inset-right, 0px);
}

body {
  /* Prevent overscroll bounce on iOS */
  overscroll-behavior-y: contain;
}

.app-header {
  padding-top: calc(var(--safe-top) + 12px);
}

.app-bottom-tabs {
  padding-bottom: calc(var(--safe-bottom) + 8px);
}

/* Standalone mode: hide install banner if installed */
@media all and (display-mode: standalone) {
  .install-prompt { display: none; }
}
```

---

## §G — BottomTabBar component shape

```tsx
// Onsite/onsite-hub/src/components/task-bot/BottomTabBar.tsx
'use client'
import { Sparkles, GraduationCap, HelpCircle, Settings } from 'lucide-react'

type Tab = 'chat' | 'train' | 'help' | 'admin'

export function BottomTabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; Icon: typeof Sparkles }[] = [
    { id: 'chat', label: 'Chat', Icon: Sparkles },
    { id: 'train', label: 'Train', Icon: GraduationCap },
    { id: 'help', label: 'Help', Icon: HelpCircle },
    { id: 'admin', label: 'Admin', Icon: Settings },
  ]
  return (
    <nav
      className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-[#0f0a2e]/95 backdrop-blur-md border-t border-white/10 app-bottom-tabs"
      role="tablist"
    >
      <div className="flex justify-around items-center h-14 max-w-md mx-auto">
        {tabs.map(({ id, label, Icon }) => {
          const isActive = active === id
          return (
            <button
              key={id}
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(id)}
              className={`flex flex-col items-center gap-0.5 min-w-[44px] min-h-[44px] px-3 py-1 rounded-xl transition-colors ${
                isActive
                  ? 'bg-gradient-to-br from-violet-500/30 to-pink-500/30 text-white'
                  : 'text-white/60 hover:text-white/90'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
```

Wire into `page.tsx`: existing main content gets `pb-20 lg:pb-0` to clear the bottom bar.

---

## §H — Push subscription wiring

```ts
// Onsite/onsite-hub/src/lib/push/subscribe.ts
export async function subscribeToPush(userId: string, jwt: string) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return null

  const reg = await navigator.serviceWorker.ready
  let sub = await reg.pushManager.getSubscription()
  if (!sub) {
    const vapidPublic = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublic),
    })
  }

  await fetch('/api/push/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
    body: JSON.stringify(sub),
  })
  return sub
}

function urlBase64ToUint8Array(base64: string) {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(b64)
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)))
}
```

VAPID keys: generate once with `npx web-push generate-vapid-keys`. Store private in env, public in env (also NEXT_PUBLIC_ prefix for client).

---

## §I — IndexedDB JWT storage

```ts
// Onsite/onsite-hub/src/lib/storage/secure_token.ts
const DB_NAME = 'onsite-ai-secure'
const STORE = 'tokens'
const KEY = 'jwt'

async function db(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function getDeviceKey(): Promise<CryptoKey> {
  const idb = await db()
  const tx = idb.transaction(STORE, 'readwrite')
  const store = tx.objectStore(STORE)
  const existing = await new Promise<JsonWebKey | undefined>((res) => {
    const r = store.get('deviceKey'); r.onsuccess = () => res(r.result); r.onerror = () => res(undefined)
  })
  if (existing) {
    return crypto.subtle.importKey('jwk', existing, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt'])
  }
  const key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt'])
  const jwk = await crypto.subtle.exportKey('jwk', key)
  store.put(jwk, 'deviceKey')
  return key
}

export async function setToken(token: string): Promise<void> {
  const key = await getDeviceKey()
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(token))
  const idb = await db()
  idb.transaction(STORE, 'readwrite').objectStore(STORE).put({ iv: Array.from(iv), ct: Array.from(new Uint8Array(ct)) }, KEY)
}

export async function getToken(): Promise<string | null> {
  const key = await getDeviceKey()
  const idb = await db()
  const data = await new Promise<{ iv: number[]; ct: number[] } | undefined>((res) => {
    const r = idb.transaction(STORE, 'readonly').objectStore(STORE).get(KEY)
    r.onsuccess = () => res(r.result); r.onerror = () => res(undefined)
  })
  if (!data) return null
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: new Uint8Array(data.iv) }, key, new Uint8Array(data.ct))
  return new TextDecoder().decode(pt)
}

export async function clearToken(): Promise<void> {
  const idb = await db()
  idb.transaction(STORE, 'readwrite').objectStore(STORE).delete(KEY)
}
```

Migration in `page.tsx`:
```ts
useEffect(() => {
  const legacy = typeof window !== 'undefined' ? sessionStorage.getItem('taskbot_token') : null
  if (legacy) {
    setToken(legacy).then(() => sessionStorage.removeItem('taskbot_token'))
  }
}, [])
```

---

## §J — Database migration (push_subscriptions)

`Onsite/task-ai/database/009_push_subscriptions.sql`:

```sql
CREATE TABLE push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  endpoint TEXT NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_used_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, endpoint)
);

CREATE INDEX push_subscriptions_user_idx ON push_subscriptions(user_id);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY push_subscriptions_user_iso ON push_subscriptions
  FOR ALL USING (user_id = auth.uid()::uuid);
```

Run via:
```bash
cd "/Users/apple/Aiwithdhruv/AI Development/Claude/Onsite/task-ai"
supabase db push
```

---

## §K — Env vars to add

`Onsite/onsite-hub/.env.local`:

```
NEXT_PUBLIC_VAPID_PUBLIC_KEY=<generated via npx web-push generate-vapid-keys>
VAPID_PRIVATE_KEY=<same command>
VAPID_SUBJECT=mailto:dhruv.tomar@onsiteteams.com
```

NPM install: `web-push` for server-side push send.

---

## §L — Acceptance gates (must all pass)

1. ✅ Chrome DevTools → Application → Manifest: parses without errors, all icons present
2. ✅ Chrome DevTools → Application → Service Workers: registered + activated for `/task-bot/`
3. ✅ Lighthouse PWA audit: ≥90 score on `/task-bot`
4. ✅ Android Chrome: "Install app" prompt fires; tap → installs to home screen; opens in standalone (no browser chrome)
5. ✅ iOS Safari: open `/task-bot` → tap Share → "Add to Home Screen" → tap home icon → opens in standalone mode with status bar matching theme color
6. ✅ Bottom tab bar appears on viewport <1024px (lg breakpoint); hidden ≥1024px
7. ✅ Tap each bottom tab → routes correctly
8. ✅ All tap targets ≥44pt × 44pt on mobile (audit with Chrome DevTools tap-target checker)
9. ✅ Safe-area insets: open on simulator iPhone 14 Pro (Dynamic Island) — header content not occluded; bottom tabs not occluded by home indicator
10. ✅ Voice button on mobile is 56pt diameter, bottom-center
11. ✅ Push notification: send test push from `/api/push/send` to a subscribed device → notification appears, tap → opens app to `/task-bot`
12. ✅ JWT migration: load app with `sessionStorage.taskbot_token = "test"` → reload → check IndexedDB has encrypted token, sessionStorage is empty
13. ✅ Token decryption round-trip: set, get, assert original value
14. ✅ Offline: turn off network, open installed app → cached shell loads (chat history may be empty — that's fine, API calls fail gracefully with retry button)
15. ✅ Pull-to-refresh inside chat does NOT refresh page (overscroll contained)
16. ✅ Type-check clean: `npx tsc --noEmit --skipLibCheck | grep -E "task-bot|pwa|push"` returns empty
17. ✅ STATE.md updated with batch entry: PWA conversion, all files shipped, commit SHA

---

## §M — Hard rules (do NOT violate)

(Carry forward from earlier dispatches + PWA-specific)

1. **No deploy.** Code-only. Push branch + PR. Dhruv decides deploy + domain.
2. **Token never logged, never sent to LLM.** IndexedDB encryption uses per-device key generated client-side.
3. **VAPID private key server-only.** Never in NEXT_PUBLIC_*.
4. **Service worker scope** is `/task-bot/` — do NOT register at root scope; would intercept onsite-hub's other pages.
5. **TypeScript strict.** No `any`. Wrap all `crypto.subtle` calls in try/catch.
6. **Don't break existing desktop layout.** Bottom tab bar must be `lg:hidden`. Existing 3-column intact.
7. **Don't break PIN-auth bypass** in `AppShell.tsx`.
8. **Match Onsite brand:** `#0f0a2e` bg, `#c73e5a` accent, Plus Jakarta Sans.
9. **Mobile-first.** All testing at 375px viewport before checking larger.
10. **No half-finished.** If push notifications can't ship complete, narrow to manifest + service worker + install prompt + bottom tab bar. Don't half-ship push.
11. **No spawning agents.** You are the engineer.
12. **No `--no-verify`, no `--amend`.**
13. **Repo split.** Code in onsite-hub. SQL migration + docs in `Onsite/task-ai/`. Cross-reference SHAs.
14. **iOS limitations honestly documented** in BUG-TRACKER.md: PWA storage wipes after 7 days inactivity, push needs iOS 16.4+, install flow is hidden.

---

## §N — Commit etiquette

1. Branch `feat/pwa-mobile` on `onsite-hub`
2. Commits: `feat(pwa): <what>` / `feat(mobile): <what>` / `chore(pwa): <icons|splash>`
3. Docs commit in `aiagentwithdhruv/Onsite` cross-references SHA
4. PR title: `feat(pwa): mobile-native conversion — manifest, SW, push, bottom nav, safe areas, IndexedDB tokens`
5. Tag Dhruv reviewer
6. NO Vercel deploy on push. PR + Dhruv reviews local + merge + deploy decision separate.

---

## §O — When you finish

Reply to Dhruv with:
1. Commit SHAs (both repos)
2. Acceptance gate checklist with proof (Lighthouse PWA score screenshot, install flow video on Android + iOS Safari, push notification screenshot, bottom nav at 375px screenshot)
3. iOS limitations doc updated in `BUG-TRACKER.md`
4. STATE.md batch entry text
5. Deploy decision needed: which Vercel project / domain config?
6. Mobile UX gaps you found while building (anything not covered in §B.3 above)

Then standby. Dhruv reviews, decides domain + deploy.

---

## §P — When you're stuck

Allowed escalations:
- Onsite's existing `/refresh` token endpoint may or may not exist → if missing, JWT refresh logic ships as "clear + show toast" fallback. Document.
- Splash screen generation is tedious → use https://progressier.com/pwa-icons-and-ios-splash-screen-generator (free) OR https://www.pwabuilder.com/imageGenerator. Just upload the sparkle logo + bg color.
- Service worker scope conflicts with another SW in onsite-hub → check `Onsite/onsite-hub/public/` for existing sw.js before adding ours.

NOT allowed:
- Deploying to Vercel.
- Picking a domain (Dhruv decides).
- Adding new product features (Train / Help / Admin tabs are STUBS — they route to existing pages or "coming soon" cards. Don't build them out in this sprint.)
- Rewriting the chat page (extend, don't rewrite).

---

**Start by replying:** "Read complete. Current mobile UI screenshotted. Starting PWA sprint." Then build.
