'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import Link from 'next/link'
import { Bell, Loader2, CheckCheck } from 'lucide-react'
import { getAlerts, markAlertRead } from '@/lib/api'
import { formatRelative, getSeverityColor } from '@/lib/utils'
import type { Alert } from '@/lib/types'
import { useAuth } from '@/contexts/AuthContext'

const PAGE_SIZE = 15

export default function AlertsPage() {
  const { session, loading: authLoading } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [markingId, setMarkingId] = useState<string | null>(null)
  const lastFetchedFilter = useRef<'all' | 'unread' | null>(null)

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
    if (authLoading) return
    if (!session) {
      setLoading(false)
      return
    }
    if (lastFetchedFilter.current === filter) return
    lastFetchedFilter.current = filter
    fetchAlerts()
  }, [authLoading, filter, fetchAlerts])

  async function handleMarkRead(alertId: string) {
    setMarkingId(alertId)
    try {
      await markAlertRead(alertId)
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a)))
    } finally {
      setMarkingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Alerts</h2>
          <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
            Stale leads, priority updates, and notifications
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-amber-500 text-zinc-900'
                : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === 'unread'
                ? 'bg-amber-500 text-zinc-900'
                : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700'
            }`}
          >
            Unread
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-10 w-10 animate-spin text-amber-500" />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <p className="text-zinc-500 dark:text-zinc-400">{error}</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <Bell className="mx-auto mb-3 h-12 w-12 text-zinc-300 dark:text-zinc-600" />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No alerts</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`flex items-start justify-between gap-4 rounded-xl border px-4 py-3 transition-colors ${
                alert.is_read
                  ? 'border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50'
                  : 'border-amber-500/20 bg-amber-500/5 dark:border-amber-500/20 dark:bg-amber-500/5'
              }`}
            >
              <Link
                href={alert.lead_id ? `/leads/${alert.lead_id}` : '#'}
                className="min-w-0 flex-1"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${getSeverityColor(alert.severity || 'low')}`}
                  >
                    {alert.severity || alert.alert_type || 'info'}
                  </span>
                  <span className="text-xs text-zinc-400 dark:text-zinc-500">
                    {formatRelative(alert.created_at || new Date().toISOString())}
                  </span>
                </div>
                <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">
                  {alert.message || alert.title || 'Alert'}
                </p>
              </Link>
              {!alert.is_read && (
                <button
                  onClick={() => handleMarkRead(alert.id)}
                  disabled={markingId === alert.id}
                  className="flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-amber-600 hover:bg-amber-500/10 dark:text-amber-400"
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
          ))}
        </div>
      )}
    </div>
  )
}
