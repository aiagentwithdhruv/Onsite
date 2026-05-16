# Onsite AI Helper — Chrome Extension

> Auto-connects Onsite Task AI to your logged-in `web.onsiteteams.com` session. Customer never has to copy/paste a token.

**Version:** 0.1.0 · **Status:** Sideload-only (not yet published to Chrome Web Store)

---

## What it does

```
You log into web.onsiteteams.com (normal flow, nothing changes)
        ↓
Extension silently reads your Bearer token from that tab's localStorage
        ↓
Extension stores it in chrome.storage.local (your device only)
        ↓
You open task-ai.onsiteteams.com (or localhost:3001/task-bot)
        ↓
Extension auto-injects the token into the bot page
        ↓
Bot opens, already signed in. Zero clicks.
```

**Privacy:** The token never leaves your machine. The extension communicates only between your own browser tabs via Chrome's local APIs. No external servers.

---

## Install (developer / sideload — 30 seconds)

1. Open Chrome → go to `chrome://extensions/`
2. Toggle **Developer mode** on (top-right)
3. Click **Load unpacked**
4. Select the folder: `Onsite/task-ai/chrome-extension/`
5. The "Onsite AI Helper" extension appears in your toolbar with a puzzle-piece icon (pin it for easy access)

That's it. Now open `web.onsiteteams.com` and log in if you haven't already.

---

## How to test it

1. **Install** the extension (steps above)
2. **Log into Onsite** at `web.onsiteteams.com`
3. **Click the extension icon** in your Chrome toolbar — the popup should say `✓ Connected to Onsite` with a "last synced" timestamp
4. **Click "Open Task AI"** in the popup (or manually open `http://localhost:3001/task-bot`)
5. The bot should **skip the token-paste screen entirely** and land you straight in the chat with a small badge "Auto-connected via Helper"

If the bot lands on the setup screen instead, the popup will show **"Not connected"** — open Onsite in a tab, log in, refresh.

---

## File structure

```
chrome-extension/
├── manifest.json         Manifest V3 declarations (permissions, content scripts)
├── background.js         Service worker — stores token in chrome.storage.local
├── onsite-reader.js      Content script on web.onsiteteams.com — reads localStorage
├── taskbot-injector.js   Content script on /task-bot — postMessage to page
├── popup.html            Toolbar popup UI
├── popup.js              Popup logic (status, open, refresh, clear)
└── README.md             This file
```

---

## Permissions explained

The manifest declares minimal permissions. Here's what each one does:

| Permission | Why |
|------------|-----|
| `storage` | Save the token in `chrome.storage.local` so it persists between sessions on this device |
| `host: https://web.onsiteteams.com/*` | Read the token from Onsite's localStorage |
| `host: http://localhost:3001/*` | Inject token into the dev bot page |
| `host: https://*.onsiteteams.com/*` and `https://*.onsiteteams.in/*` | Inject token into the production bot page when deployed |
| `host: https://onsite-hub.vercel.app/*` | Inject token into the Vercel preview deploy |

**The extension does NOT have:**
- Permission to read arbitrary browsing history
- Permission to read other websites
- Network access beyond what the content scripts implicitly use
- Any analytics or telemetry

---

## How the token flows

```
┌──────────────────────────────┐
│ web.onsiteteams.com tab      │
│                              │
│ localStorage['token']        │   ← User logs in normally,
│ = {"token":"eyJ...","expire":│     Onsite stores token here
│ "2026-07-15T..."}            │
└──────────────┬───────────────┘
               │ (1) onsite-reader.js reads this
               ▼
┌──────────────────────────────┐
│ Extension service worker     │
│                              │
│ chrome.storage.local         │   ← (2) Stored locally,
│ { onsite_token,              │       persists across sessions
│   onsite_expire,             │
│   last_synced }              │
└──────────────┬───────────────┘
               │ (3) taskbot-injector.js retrieves
               ▼
┌──────────────────────────────┐
│ Task AI page                 │
│ (localhost / Vercel)         │
│                              │
│ window.postMessage(          │   ← (4) Injected via postMessage
│   {source:'onsite-ai-helper',│       Page listens, auto-authenticates
│    token: '...'},            │
│   window.location.origin)    │
└──────────────────────────────┘
```

The token never:
- Touches any HTTP server outside the customer's browser
- Gets logged or telemetry-tracked
- Gets sent to LLM providers
- Gets persisted to disk in plaintext (chrome.storage.local is encrypted at rest in modern Chrome)

---

## Compatibility

- **Chrome 88+** — Manifest V3 required
- **Edge** — should work (Chromium-based, same MV3)
- **Brave / Arc / Vivaldi** — should work (Chromium-based)
- **Firefox** — not supported yet (MV3 status differs); could be ported with manifest adjustments
- **Safari** — not supported (different extension model)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Popup says "Not connected" but I'm logged in | Click "↻ Re-sync from Onsite tab" — that reloads the Onsite tab content script |
| Token expired warning | Re-log into `web.onsiteteams.com` — Onsite will issue a fresh JWT |
| Bot still asks me to paste a token | Make sure the extension is enabled in `chrome://extensions/` and that the bot URL matches one of the patterns in `manifest.json` |
| Extension stopped working after Chrome restart | Re-pin it via the puzzle icon |
| Need to test against a different bot URL | Edit `host_permissions` and the second `content_scripts` block in `manifest.json`, then click the refresh icon on the extension in `chrome://extensions/` |

---

## Roadmap

- **v0.2:** Add icons (16/48/128 px)
- **v0.3:** Status indicator in toolbar badge (green dot when connected)
- **v0.4:** Settings page (choose dev vs prod bot URL)
- **v1.0:** Publish to Chrome Web Store with proper signing + auto-update
- **v2.0:** Port to Firefox / Safari extensions

---

## Security notes

- Content scripts run in an **isolated world** — they cannot access page JS variables, only DOM and explicit messaging
- `window.postMessage` to the page uses `window.location.origin` as the target — won't broadcast to other origins
- The page validates `event.origin === window.location.origin` and `event.data.source === 'onsite-ai-helper'` before trusting any message
- `chrome.storage.local` is per-user, per-device, encrypted at rest (Chrome's own encryption)
- The extension code is bundled in the install — no remote code execution, no auto-updates to scripts (until Chrome Web Store)

---

## License

Proprietary · © Abeyaantrix Technology Private Limited (Onsite Teams)
