'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Bell, CheckCheck, AlertTriangle, Flame, TrendingDown, Users,
  Trophy, DollarSign, Clock, Target, BarChart3, Zap, ShieldAlert,
} from 'lucide-react'
import { getAlerts, markAlertRead } from '@/lib/api'
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
  const hasFetched = useRef(false)

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getAlerts({ limit: '100' })
      const data = res.data as { alerts?: SmartAlert[] } | SmartAlert[]
      const list = Array.isArray(data) ? data : data?.alerts ?? []
      setAlerts(list)
    } catch {
      setError('No alerts yet. Upload a CSV in Intelligence to generate smart alerts.')
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

  async function handleMarkRead(alertId: string) {
    setMarkingId(alertId)
    try {
      await markAlertRead(alertId)
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, read_at: new Date().toISOString() } : a))
    } finally {
      setMarkingId(null)
    }
  }

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'all') return true
    if (filter === 'critical') return a.severity === 'critical' || a.severity === 'high'
    if (filter === 'high') return a.severity === 'high' || a.severity === 'medium'
    if (filter === 'info') return a.severity === 'info'
    return true
  })

  const critCount = alerts.filter(a => a.severity === 'critical').length
  const highCount = alerts.filter(a => a.severity === 'high').length
  const infoCount = alerts.filter(a => a.severity === 'info').length
  const unreadCount = alerts.filter(a => !a.read_at).length

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-zinc-300 border-t-amber-500" />
        <p className="text-sm text-zinc-500">Analyzing alerts...</p>
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
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{error}</p>
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
                          {alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">
                        {alert.title || alert.message}
                      </h3>
                      {alert.title && alert.message && (
                        <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                          {alert.message}
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
