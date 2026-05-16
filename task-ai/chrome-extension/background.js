// Service worker: stores the latest Onsite token and serves it to the task-bot page.
// Token never leaves the user's machine; chrome.storage.local is per-user, per-device.

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.type === 'onsite_token_update' && typeof msg.token === 'string') {
    chrome.storage.local.set(
      {
        onsite_token: msg.token,
        onsite_expire: msg.expire || null,
        last_synced: Date.now(),
      },
      () => sendResponse({ ok: true })
    )
    return true // keep channel open for async response
  }

  if (msg && msg.type === 'get_onsite_token') {
    chrome.storage.local.get(['onsite_token', 'onsite_expire', 'last_synced'], (data) => {
      sendResponse(data || {})
    })
    return true
  }

  if (msg && msg.type === 'clear_onsite_token') {
    chrome.storage.local.remove(['onsite_token', 'onsite_expire', 'last_synced'], () =>
      sendResponse({ ok: true })
    )
    return true
  }
})

// Optional: auto-clear expired tokens hourly
chrome.alarms?.create('expire-check', { periodInMinutes: 60 })
chrome.alarms?.onAlarm.addListener((alarm) => {
  if (alarm.name !== 'expire-check') return
  chrome.storage.local.get(['onsite_expire'], (data) => {
    if (!data.onsite_expire) return
    const exp = new Date(data.onsite_expire).getTime()
    if (Number.isFinite(exp) && exp < Date.now()) {
      chrome.storage.local.remove(['onsite_token', 'onsite_expire', 'last_synced'])
    }
  })
})
