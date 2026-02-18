'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Bell, CheckCheck, AlertTriangle, Flame, TrendingDown, Users,
  Trophy, DollarSign, Clock, Target, BarChart3, Zap, ShieldAlert,
  Send, Mail, MessageCircle, Calendar, FileText,
} from 'lucide-react'
import { getAlerts, markAlertRead, getNotificationPreferences, updateNotificationPreferences, sendTestAlert } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SmartAlert = Record<string, any>

const SEVERITY_CONFIG: Record<string, { bg: string; border: string; icon: string; badge: string }> = {
  critical: { bg: 'bg-red-500/5', border: 'border-red-500/30', icon: 'text-red-500', badge: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400' },
  high: { bg: 'bg-orange-500/5', border: 'border-orange-500/30', icon: 'text-orange-500', badge: 'bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400' },
  medium: { bg: 'bg-amber-500/5', border: 'border-amber-500/30', icon: 'text-amber-500', badge: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400' },
  low: { bg: 'bg-blue-500/5', border: 'border-blue-500/30', icon: 'text-blue-500', badge: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400' },
  info: { bg: 'bg-green-500/5', border: 'border-green-500/30', icon: 'text-green-500', badge: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' },
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  stale_30d: Clock,
  stale_14d: Clock,
  stale_7d: Clock,
  demo_dropout: TrendingDown,
  low_conversion: TrendingDown,
  hot_no_followup: Flame,
  priority_overload: Zap,
  inactive_agent: ShieldAlert,
  top_performer: Trophy,
  revenue_milestone: DollarSign,
  pipeline_risk: BarChart3,
  follow_up_needed: AlertTriangle,
  followup_overdue: Calendar,
  followup_due_today: Calendar,
  followup_due_tomorrow: Calendar,
  notes_need_action: FileText,
  performance_drop: TrendingDown,
  custom: Bell,
}

export default function AlertsPage() {
  const { session, loading: authLoading } = useAuth()
  const [alerts, setAlerts] = useState<SmartAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'info'>('all')
  const [markingId, setMarkingId] = useState<string | null>(null)
  const [prefs, setPrefs] = useState<{ notify_via_telegram: boolean; notify_via_discord: boolean; notify_via_whatsapp: boolean; notify_via_email: boolean; telegram_linked: boolean; discord_linked: boolean } | null>(null)
  const [discordWebhook, setDiscordWebhook] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [prefsSaving, setPrefsSaving] = useState(false)
  const [testSending, setTestSending] = useState(false)
  const [testResult, setTestResult] = useState<{ sent?: boolean; channels?: Record<string, { status?: string; reason?: string; error?: string }> } | null>(null)
  const hasFetched = useRef(false)

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getAlerts({ per_page: '100' })
      const data = res.data as { alerts?: SmartAlert[] } | SmartAlert[]
      const list = Array.isArray(data) ? data : data?.alerts ?? []
      setAlerts(list)
    } catch {
      setError('Could not load alerts. Check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading) return
    if (!session) { setLoading(false); return }
    if (hasFetched.current) return
    hasFetched.current = true
    fetchAlerts()
  }, [authLoading, session, fetchAlerts])

  useEffect(() => {
    if (!session) return
    getNotificationPreferences().then(r => {
      const d = r.data as { notify_via_telegram?: boolean; notify_via_discord?: boolean; notify_via_whatsapp?: boolean; notify_via_email?: boolean; telegram_linked?: boolean; discord_linked?: boolean }
      setPrefs({
        notify_via_telegram: !!d?.notify_via_telegram,
        notify_via_discord: !!d?.notify_via_discord,
        notify_via_whatsapp: d?.notify_via_whatsapp !== false,
        notify_via_email: d?.notify_via_email !== false,
        telegram_linked: !!d?.telegram_linked,
        discord_linked: !!d?.discord_linked,
      })
    }).catch(() => {})
  }, [session])

  async function togglePref(key: 'notify_via_telegram' | 'notify_via_discord' | 'notify_via_whatsapp' | 'notify_via_email') {
    if (!prefs) return
    const next = { ...prefs, [key]: !prefs[key] }
    setPrefsSaving(true)
    try {
      await updateNotificationPreferences({ [key]: next[key] })
      setPrefs(next)
    } finally {
      setPrefsSaving(false)
    }
  }

  async function saveTelegramChatId() {
    if (!prefs) return
    setPrefsSaving(true)
    try {
      await updateNotificationPreferences({ telegram_chat_id: telegramChatId.trim() || null })
      setPrefs(prev => prev ? { ...prev, telegram_linked: !!telegramChatId.trim() } : null)
      setTelegramChatId('')
    } finally {
      setPrefsSaving(false)
    }
  }

  async function saveDiscordWebhook() {
    if (!prefs) return
    setPrefsSaving(true)
    try {
      await updateNotificationPreferences({ discord_webhook_url: discordWebhook.trim() || undefined })
      setPrefs(prev => prev ? { ...prev, discord_linked: !!discordWebhook.trim() } : null)
      setDiscordWebhook('')
    } finally {
      setPrefsSaving(false)
    }
  }

  async function handleSendTestAlert() {
    setTestSending(true)
    setTestResult(null)
    try {
      const res = await sendTestAlert()
      const data = res.data as { ok?: boolean; sent?: boolean; channels?: Record<string, { status?: string; reason?: string; error?: string }> }
      setTestResult({ sent: data?.sent, channels: data?.channels })
    } catch {
      setTestResult({ sent: false })
    } finally {
      setTestSending(false)
    }
  }

  async function handleMarkRead(alertId: string) {
    setMarkingId(alertId)
    try {
      await markAlertRead(alertId)
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, read_at: new Date().toISOString() } : a))
    } finally {
      setMarkingId(null)
    }
  }

  // Normalize: base schema may only have message, sent_at, alert_type
  const norm = (a: SmartAlert): SmartAlert => ({
    ...a,
    severity: a.severity || 'medium',
    created_at: a.created_at || a.sent_at,
    title: a.title || (a.message ? a.message.split('\n')[0]?.trim() || a.message : 'Alert'),
    message: a.message,
  })

  const filteredAlerts = alerts.map(norm).filter(a => {
    if (filter === 'all') return true
    if (filter === 'critical') return a.severity === 'critical' || a.severity === 'high'
    if (filter === 'high') return a.severity === 'high' || a.severity === 'medium'
    if (filter === 'info') return a.severity === 'info'
    return true
  })

  const critCount = alerts.filter(a => (a.severity || 'medium') === 'critical').length
  const highCount = alerts.filter(a => (a.severity || 'medium') === 'high').length
  const infoCount = alerts.filter(a => (a.severity || 'medium') === 'info').length
  const unreadCount = alerts.filter(a => !a.read_at).length

  if (loading) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center py-32 transition-opacity duration-200">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-zinc-300 border-t-amber-500" />
        <p className="text-sm text-zinc-500">Loading alerts...</p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white">Smart Alerts</h1>
          <p className="text-sm text-zinc-500">
            {alerts.length} alerts &middot; {unreadCount} unread &middot; Auto-generated from your data
          </p>
        </div>
        <button
          onClick={() => { hasFetched.current = false; fetchAlerts() }}
          className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:border-amber-500 hover:text-amber-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
        >
          Refresh
        </button>
      </div>

      {/* Delivery: Telegram (priority), WhatsApp, Email */}
      {prefs && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-800 dark:text-zinc-200">
            <Send className="h-4 w-4 text-amber-500" />
            Alert delivery
          </h3>
          <div className="flex flex-wrap items-center gap-6">
            <label className="flex flex-wrap items-center gap-2">
              <input type="checkbox" checked={prefs.notify_via_telegram} onChange={() => togglePref('notify_via_telegram')} disabled={prefsSaving} className="h-4 w-4 rounded border-zinc-300 text-amber-500" />
              <MessageCircle className="h-4 w-4 text-sky-500" />
              <span className="text-sm text-zinc-700 dark:text-zinc-300">Telegram</span>
              {prefs.telegram_linked ? (
                <span className="flex items-center gap-1">
                  <span className="text-xs text-green-600 dark:text-green-400">Linked</span>
                  <button type="button" onClick={() => updateNotificationPreferences({ telegram_chat_id: '' }).then(() => setPrefs(prev => prev ? { ...prev, telegram_linked: false } : null))} className="text-xs text-zinc-500 hover:underline dark:text-zinc-400">Change</button>
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <input type="text" placeholder="Chat ID" value={telegramChatId} onChange={e => setTelegramChatId(e.target.value)} className="w-32 rounded border border-zinc-300 bg-white px-2 py-0.5 text-xs dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200" />
                  <button type="button" onClick={saveTelegramChatId} disabled={prefsSaving || !telegramChatId.trim()} className="text-xs font-medium text-amber-600 hover:underline disabled:opacity-50 dark:text-amber-400">Save</button>
                </span>
              )}
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input type="checkbox" checked={prefs.notify_via_discord} onChange={() => togglePref('notify_via_discord')} disabled={prefsSaving} className="h-4 w-4 rounded border-zinc-300 text-amber-500" />
              <MessageCircle className="h-4 w-4 text-indigo-500" />
              <span className="text-sm text-zinc-700 dark:text-zinc-300">Discord</span>
              {prefs.discord_linked ? (
                <span className="flex items-center gap-1">
                  <span className="text-xs text-green-600 dark:text-green-400">Linked</span>
                  <button type="button" onClick={() => { updateNotificationPreferences({ discord_webhook_url: '' }).then(() => setPrefs(prev => prev ? { ...prev, discord_linked: false } : null)) }} className="text-xs text-zinc-500 hover:underline dark:text-zinc-400">Change</button>
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <input type="url" placeholder="Webhook URL" value={discordWebhook} onChange={e => setDiscordWebhook(e.target.value)} className="w-48 rounded border border-zinc-300 bg-white px-2 py-0.5 text-xs dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200" />
                  <button type="button" onClick={saveDiscordWebhook} disabled={prefsSaving || !discordWebhook.trim()} className="text-xs font-medium text-amber-600 hover:underline disabled:opacity-50 dark:text-amber-400">Save</button>
                </span>
              )}
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input type="checkbox" checked={prefs.notify_via_whatsapp} onChange={() => togglePref('notify_via_whatsapp')} disabled={prefsSaving} className="h-4 w-4 rounded border-zinc-300 text-amber-500" />
              <MessageCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm text-zinc-700 dark:text-zinc-300">WhatsApp</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input type="checkbox" checked={prefs.notify_via_email} onChange={() => togglePref('notify_via_email')} disabled={prefsSaving} className="h-4 w-4 rounded border-zinc-300 text-amber-500" />
              <Mail className="h-4 w-4 text-zinc-500" />
              <span className="text-sm text-zinc-700 dark:text-zinc-300">Email</span>
            </label>
          </div>
          {!prefs?.telegram_linked && <p className="mt-1 text-[11px] text-zinc-500 dark:text-zinc-400">Get your Chat ID from @userinfobot on Telegram, then paste it above and Save.</p>}
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-zinc-200 pt-3 dark:border-zinc-700">
            <button
              type="button"
              onClick={handleSendTestAlert}
              disabled={testSending}
              className="rounded-lg border border-amber-500/50 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-500/20 disabled:opacity-50 dark:text-amber-400 dark:hover:bg-amber-500/20"
            >
              {testSending ? 'Sending…' : 'Send test alert'}
            </button>
            {testResult !== null && (
              <span className="text-xs text-zinc-600 dark:text-zinc-400">
                {testResult.sent
                  ? '✅ Test sent to your enabled channels. Check Telegram (or Discord/email).'
                  : (() => {
                      const ch = testResult.channels?.telegram
                      const reason = ch?.reason || ch?.error
                      if (reason === 'no_bot_token') return '❌ Telegram: Bot token not set. Save it in Settings → Telegram Bot. If already saved, run database migration 011_app_config.sql in Supabase and restart the backend.'
                      if (reason === 'no_chat_id') return '❌ Telegram: Chat ID missing. Enter your Chat ID above and Save.'
                      if (ch?.error) return `❌ Telegram: ${ch.error}`
                      if (ch?.reason) return `❌ Telegram: ${ch.reason}`
                      return '❌ Could not send. Check token in Settings and that you have Chat ID + Telegram enabled.'
                    })()}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Summary KPIs */}
      {alerts.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 dark:border-red-500/20 dark:bg-red-500/5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-red-600">Critical</p>
            <p className="text-2xl font-bold text-red-600">{critCount}</p>
          </div>
          <div className="rounded-xl border border-orange-200 bg-orange-50 p-3 dark:border-orange-500/20 dark:bg-orange-500/5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-orange-600">High</p>
            <p className="text-2xl font-bold text-orange-600">{highCount}</p>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/20 dark:bg-amber-500/5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">Total Alerts</p>
            <p className="text-2xl font-bold text-amber-600">{alerts.length}</p>
          </div>
          <div className="rounded-xl border border-green-200 bg-green-50 p-3 dark:border-green-500/20 dark:bg-green-500/5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-green-600">Positive</p>
            <p className="text-2xl font-bold text-green-600">{infoCount}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2">
        {[
          { key: 'all' as const, label: 'All', count: alerts.length },
          { key: 'critical' as const, label: 'Critical & High', count: critCount + highCount },
          { key: 'info' as const, label: 'Positive', count: infoCount },
        ].map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${filter === f.key ? 'bg-amber-500 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400'}`}>
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      {/* Alert Cards */}
      {error ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <Bell className="mx-auto mb-3 h-12 w-12 text-zinc-300 dark:text-zinc-600" />
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{error}</p>
          <button onClick={() => { hasFetched.current = false; fetchAlerts() }} className="rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-400">Retry</button>
        </div>
      ) : alerts.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50 transition-opacity duration-200">
          <Bell className="mx-auto mb-3 h-12 w-12 text-zinc-300 dark:text-zinc-600" />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No alerts yet. Upload a CSV in Intelligence to generate smart alerts.</p>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <Bell className="mx-auto mb-3 h-12 w-12 text-zinc-300 dark:text-zinc-600" />
          <p className="text-sm text-zinc-500">No alerts in this category</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map(alert => {
            const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.medium
            const Icon = TYPE_ICONS[alert.alert_type] || Bell
            const isRead = !!alert.read_at
            const body = alert.message && alert.message.includes('\n') ? alert.message.split('\n').slice(1).join('\n').trim() : (alert.title !== alert.message ? alert.message : null)

            return (
              <div
                key={alert.id}
                className={`rounded-xl border ${isRead ? 'border-zinc-200 dark:border-zinc-800' : sev.border} ${isRead ? 'bg-white dark:bg-zinc-900/50 opacity-60' : sev.bg} p-4 transition-all`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${isRead ? 'bg-zinc-100 dark:bg-zinc-800' : sev.bg}`}>
                      <Icon className={`h-4.5 w-4.5 ${isRead ? 'text-zinc-400' : sev.icon}`} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${sev.badge}`}>
                          {alert.severity}
                        </span>
                        {alert.agent_name && alert.agent_name !== 'system' && (
                          <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-400">
                            {alert.agent_name}
                          </span>
                        )}
                        <span className="text-[10px] text-zinc-400">
                          {(alert.created_at || alert.sent_at) ? new Date(alert.created_at || alert.sent_at).toLocaleString() : ''}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">
                        {alert.title || alert.message}
                      </h3>
                      {body && (
                        <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                          {body}
                        </p>
                      )}
                    </div>
                  </div>
                  {!isRead && (
                    <button
                      onClick={() => handleMarkRead(alert.id)}
                      disabled={markingId === alert.id}
                      className="flex shrink-0 items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium text-amber-600 hover:bg-amber-500/10 dark:text-amber-400"
                    >
                      <CheckCheck className="h-3.5 w-3.5" />
                      {markingId === alert.id ? '...' : 'Read'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
