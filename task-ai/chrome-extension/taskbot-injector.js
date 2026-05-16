// Content script: runs on the task-bot page (localhost + production).
// On load and on request, fetches the cached Onsite token and posts it to the page via window.postMessage.

(function () {
  'use strict'

  function injectToken() {
    try {
      chrome.runtime.sendMessage({ type: 'get_onsite_token' }, (data) => {
        if (chrome.runtime.lastError) return
        if (!data || !data.onsite_token) return
        window.postMessage(
          {
            source: 'onsite-ai-helper',
            type: 'onsite_token',
            token: data.onsite_token,
            expire: data.onsite_expire || null,
            last_synced: data.last_synced || null,
          },
          window.location.origin
        )
      })
    } catch (_) {
      /* extension may have reloaded; user can refresh the page */
    }
  }

  // Inject on initial load
  injectToken()

  // Re-inject when the page explicitly asks (e.g. after sign-out)
  window.addEventListener('message', (e) => {
    if (e.origin !== window.location.origin) return
    if (e.data && e.data.type === 'request_onsite_token') {
      injectToken()
    }
  })

  // Mark that the helper is present (so the page can show a nice "auto-connected" badge)
  window.postMessage(
    { source: 'onsite-ai-helper', type: 'helper_ready' },
    window.location.origin
  )
})()
