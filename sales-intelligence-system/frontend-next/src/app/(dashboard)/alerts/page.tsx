'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Bell, Loader2, CheckCheck, MessageCircle, Send, Save, AlertTriangle, CalendarClock, FileText } from 'lucide-react'
import { getAlerts, markAlertRead, getNotificationPreferences, updateNotificationPreferences, sendTestAlert } from '@/lib/api'
import { formatRelative, getSeverityColor } from '@/lib/utils'
import type { Alert } from '@/lib/types'

const PAGE_SIZE = 15

const TYPE_ICONS: Record<string, string> = {
  stale_leads: '📊',
  high_value: '💎',
  anomaly: '⚠️',
  followup_overdue: '🔴',
  followup_due_today: '🟡',
  followup_due_tomorrow: '🟢',
  notes_need_action: '📝',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [markingId, setMarkingId] = useState<string | null>(null)

  // Notification preferences
  const [prefsLoaded, setPrefsLoaded] = useState(false)
  const [telegramEnabled, setTelegramEnabled] = useState(false)
  const [emailEnabled, setEmailEnabled] = useState(false)
  const [telegramChatId, setTelegramChatId] = useState('')
  const [prefsSaving, setPrefsSaving] = useState(false)
  const [prefsError, setPrefsError] = useState<string | null>(null)
  const [prefsSuccess, setPrefsSuccess] = useState(false)

  // Test alert
  const [testSending, setTestSending] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testError, setTestError] = useState<string | null>(null)

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, string> = { limit: String(PAGE_SIZE) }
      if (filter === 'unread') params.is_read = 'false'
      const res = await getAlerts(params)
      const data = res.data as { alerts?: Alert[] } | Alert[]
      setAlerts(Array.isArray(data) ? data : data?.alerts ?? [])
    } catch {
      setError('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  useEffect(() => {
    getNotificationPreferences()
      .then((r) => {
        const d = r.data as Record<string, unknown>
        setTelegramEnabled(!!d?.notify_via_telegram)
        setEmailEnabled(!!d?.notify_via_email)
        setTelegramChatId((d?.telegram_chat_id as string) || '')
      })
      .catch(() => {})
      .finally(() => setPrefsLoaded(true))
  }, [])

  async function handleMarkRead(alertId: string) {
    setMarkingId(alertId)
    try {
      await markAlertRead(alertId)
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a)))
    } catch {}
    setMarkingId(null)
  }

  async function savePrefs() {
    setPrefsSaving(true)
    setPrefsError(null)
    setPrefsSuccess(false)
    try {
      await updateNotificationPreferences({
        notify_via_telegram: telegramEnabled,
        notify_via_email: emailEnabled,
        telegram_chat_id: telegramChatId.trim() || null,
      })
      setPrefsSuccess(true)
      setTimeout(() => setPrefsSuccess(false), 3000)
    } catch (e: unknown) {
      const msg =
        e && typeof e === 'object' && 'response' in e
          ? String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Save failed')
          : e instanceof Error
          ? e.message
          : 'Save failed'
      setPrefsError(msg)
    } finally {
      setPrefsSaving(false)
    }
  }

  async function handleTestAlert() {
    setTestSending(true)
    setTestResult(null)
    setTestError(null)
    const timeoutMs = 15000
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Test alert timed out. Check backend and Telegram bot token.')), timeoutMs)
    )
    try {
      const res = await Promise.race([sendTestAlert(), timeoutPromise])
      const d = res.data as Record<string, unknown>
      if (d?.telegram) {
        const tg = d.telegram as { sent?: boolean; reason?: string; error?: string }
        if (tg.sent) {
          setTestResult('Test alert sent to Telegram!')
        } else {
          const reason = tg.reason || tg.error || 'unknown'
          if (reason === 'no_bot_token') setTestError('Telegram Bot Token not set. Ask an admin to add it in Settings.')
          else if (reason === 'no_chat_id') setTestError('No Chat ID saved. Enter your Chat ID above and save first.')
          else setTestError(`Telegram failed: ${reason}`)
        }
      } else {
        setTestResult('Test sent (check your channels).')
      }
    } catch (e: unknown) {
      setTestError(e instanceof Error ? e.message : 'Test alert failed.')
    } finally {
      setTestSending(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">Alerts</h2>
        <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
          Stale leads, priority updates, and notifications
        </p>
      </div>

      {/* Notification preferences */}
      <div className="rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
        <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-zinc-900 dark:text-white">
          <MessageCircle className="h-5 w-5 text-sky-500" />
          Notification preferences
        </h3>
        {!prefsLoaded ? (
          <div className="flex items-center gap-2 text-sm text-zinc-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-6">
              <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                <input type="checkbox" checked={telegramEnabled} onChange={(e) => setTelegramEnabled(e.target.checked)} className="rounded" />
                Telegram
              </label>
              <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                <input type="checkbox" checked={emailEnabled} onChange={(e) => setEmailEnabled(e.target.checked)} className="rounded" />
                Email
              </label>
            </div>
            {telegramEnabled && (
              <div className="flex flex-wrap items-center gap-2">
                <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Chat ID:</label>
                <input
                  type="text"
                  placeholder="Your Telegram Chat ID (e.g. 123456789)"
                  value={telegramChatId}
                  onChange={(e) => { setTelegramChatId(e.target.value); setPrefsError(null); setPrefsSuccess(false) }}
                  className="min-w-[220px] rounded-lg border border-zinc-200 bg-zinc-50/80 px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-violet-400 focus:outline-none dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                  Message @userinfobot on Telegram to get your Chat ID.
                </p>
              </div>
            )}
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={savePrefs}
                disabled={prefsSaving}
                className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-2 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50"
              >
                {prefsSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                Save
              </button>
              <button
                type="button"
                onClick={handleTestAlert}
                disabled={testSending}
                className="flex items-center gap-1.5 rounded-lg border border-sky-500/50 bg-sky-500/10 px-3 py-2 text-xs font-medium text-sky-700 hover:bg-sky-500/20 disabled:opacity-50 dark:text-sky-400"
              >
                {testSending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                Send test alert
              </button>
            </div>
            {prefsSuccess && <p className="text-xs text-green-600 dark:text-green-400">Preferences saved.</p>}
            {prefsError && <p className="text-xs text-red-600 dark:text-red-400" role="alert">{prefsError}</p>}
            {testResult && <p className="text-xs text-green-600 dark:text-green-400">{testResult}</p>}
            {testError && <p className="text-xs text-red-600 dark:text-red-400" role="alert">{testError}</p>}
          </div>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
            filter === 'all'
              ? 'bg-violet-600 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
            filter === 'unread'
              ? 'bg-violet-600 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300'
          }`}
        >
          Unread
        </button>
      </div>

      {/* Alerts list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-400">
          {error}
        </div>
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-zinc-200/80 bg-white py-16 dark:border-zinc-700/50 dark:bg-zinc-900/40">
          <Bell className="h-8 w-8 text-zinc-300 dark:text-zinc-600" />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No alerts</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`rounded-xl border p-4 transition-colors ${
                alert.is_read
                  ? 'border-zinc-200/60 bg-white/50 dark:border-zinc-800/60 dark:bg-zinc-900/20'
                  : 'border-violet-200/60 bg-violet-50/30 dark:border-violet-900/30 dark:bg-violet-950/10'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${getSeverityColor(alert.severity || 'low')}`}>
                      {alert.severity || 'info'}
                    </span>
                    <span className="text-xs text-zinc-400">{formatRelative(alert.created_at || new Date().toISOString())}</span>
                    {alert.alert_type && (
                      <span className="text-xs text-zinc-400">
                        {TYPE_ICONS[alert.alert_type] || ''} {alert.alert_type.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-zinc-800 dark:text-zinc-200">{alert.title}</p>
                  {alert.message && (
                    <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400 line-clamp-2">{alert.message}</p>
                  )}
                </div>
                {!alert.is_read && (
                  <button
                    onClick={() => handleMarkRead(alert.id)}
                    disabled={markingId === alert.id}
                    className="flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-violet-600 hover:bg-violet-50 disabled:opacity-50 dark:text-violet-400 dark:hover:bg-violet-950/30"
                  >
                    {markingId === alert.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <CheckCheck className="h-3.5 w-3.5" />
                    )}
                    Mark read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
