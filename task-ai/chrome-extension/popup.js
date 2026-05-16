// Popup UI: shows connection status, lets user open the bot, refresh, or clear token.

const TASK_BOT_URL = 'http://localhost:3001/task-bot'

function fmtDate(iso) {
  if (!iso) return null
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return null
  }
}

function fmtRelative(ms) {
  if (!ms) return null
  const diff = Date.now() - ms
  if (diff < 60_000) return 'just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return `${Math.floor(diff / 86_400_000)}d ago`
}

function render() {
  chrome.storage.local.get(['onsite_token', 'onsite_expire', 'last_synced'], (data) => {
    const el = document.getElementById('status')
    if (!data || !data.onsite_token) {
      el.className = 'status warn'
      el.innerHTML = `<strong>Not connected.</strong><br/>Open <span style="font-family:ui-monospace,monospace">web.onsiteteams.com</span> and log in. The token will sync automatically.`
      return
    }
    const expireDate = fmtDate(data.onsite_expire)
    const syncedRel = fmtRelative(data.last_synced)
    const isExpired = data.onsite_expire && new Date(data.onsite_expire).getTime() < Date.now()

    if (isExpired) {
      el.className = 'status warn'
      el.innerHTML = `<strong>Token expired.</strong><br/>Re-log into Onsite to get a fresh one.<div class="meta">Expired: ${expireDate}</div>`
    } else {
      el.className = 'status ok'
      el.innerHTML = `<strong>✓ Connected to Onsite.</strong><br/>Token is ready — open Task AI and it'll auto-connect.<div class="meta">Last synced: ${syncedRel || 'unknown'}${expireDate ? ' · expires ' + expireDate : ''}</div>`
    }
  })
}

document.getElementById('open-bot').addEventListener('click', () => {
  chrome.tabs.create({ url: TASK_BOT_URL })
})

document.getElementById('refresh').addEventListener('click', () => {
  // Find an open Onsite tab and reload its content script — easiest path is to just nudge the user
  chrome.tabs.query({ url: 'https://web.onsiteteams.com/*' }, (tabs) => {
    if (tabs.length === 0) {
      chrome.tabs.create({ url: 'https://web.onsiteteams.com' })
    } else {
      chrome.tabs.reload(tabs[0].id, {}, () => render())
    }
  })
  setTimeout(render, 2000)
})

document.getElementById('clear').addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'clear_onsite_token' }, () => render())
})

render()
