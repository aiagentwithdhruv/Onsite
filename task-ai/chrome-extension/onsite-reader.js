// Content script: runs on web.onsiteteams.com
// Reads the Bearer JWT from localStorage and forwards it to the extension service worker.
// Re-syncs on storage change and every 30s in case of in-tab token refresh.

(function () {
  'use strict'

  function readToken() {
    try {
      const raw = localStorage.getItem('token')
      if (!raw) return null
      const parsed = JSON.parse(raw)
      if (parsed && typeof parsed.token === 'string' && parsed.token.length > 20) {
        return { token: parsed.token, expire: parsed.expire || null }
      }
    } catch (_) {
      /* ignore parse errors */
    }
    return null
  }

  function syncToken() {
    const data = readToken()
    if (!data) return
    try {
      chrome.runtime.sendMessage({
        type: 'onsite_token_update',
        token: data.token,
        expire: data.expire,
      })
    } catch (_) {
      /* extension context may be temporarily invalidated; will retry on next interval */
    }
  }

  // Initial sync (after the page finishes loading and Angular has populated localStorage)
  setTimeout(syncToken, 1200)

  // Cross-tab storage events — fires when another tab updates token
  window.addEventListener('storage', (e) => {
    if (e.key === 'token') syncToken()
  })

  // Periodic refresh — catches in-tab token updates (Angular setters don't fire 'storage' event)
  setInterval(syncToken, 30000)
})()
