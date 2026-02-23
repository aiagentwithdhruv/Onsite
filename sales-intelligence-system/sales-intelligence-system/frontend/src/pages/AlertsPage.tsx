import { useState, useEffect, useCallback } from 'react'
import {
  Bell,
  BellOff,
  Loader2,
  AlertTriangle,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  MessageSquare,
  Mail,
  Filter,
  RefreshCw,
  AlertCircle,
  Info,
  AlertOctagon,
  Flame,
} from 'lucide-react'
import { getAlerts, markAlertRead } from '../lib/api'
import type { Alert } from '../lib/types'
import { formatRelative, getSeverityColor, cn } from '../lib/utils'

type FilterTab = 'all' | 'unread' | 'critical' | 'high' | 'medium' | 'low'

const TABS: { key: FilterTab; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'unread', label: 'Unread' },
  { key: 'critical', label: 'Critical' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
]

const PAGE_SIZE = 10

function getSeverityIcon(severity: string) {
  switch (severity) {
    case 'critical':
      return <Flame className="h-4 w-4" />
    case 'high':
      return <AlertOctagon className="h-4 w-4" />
    case 'medium':
      return <AlertCircle className="h-4 w-4" />
    case 'low':
      return <Info className="h-4 w-4" />
    default:
      return <Bell className="h-4 w-4" />
  }
}

function getSentViaIcon(channel: string) {
  switch (channel.toLowerCase()) {
    case 'whatsapp':
      return <MessageSquare className="h-3.5 w-3.5 text-green-600" />
    case 'email':
      return <Mail className="h-3.5 w-3.5 text-blue-600" />
    default:
      return <Bell className="h-3.5 w-3.5 text-slate-500" />
  }
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [page, setPage] = useState(1)
  const [markingRead, setMarkingRead] = useState<string | null>(null)
  const [markingAllRead, setMarkingAllRead] = useState(false)

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, string> = {}
      if (activeTab === 'unread') params.is_read = 'false'
      if (['critical', 'high', 'medium', 'low'].includes(activeTab))
        params.severity = activeTab

      const res = await getAlerts(params)
      setAlerts(res.data?.data || res.data || [])
    } catch (err) {
      setError('Failed to load alerts')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    setPage(1)
    fetchAlerts()
  }, [fetchAlerts])

  async function handleMarkRead(alertId: string) {
    try {
      setMarkingRead(alertId)
      await markAlertRead(alertId)
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      )
    } catch (err) {
      console.error('Failed to mark alert as read:', err)
    } finally {
      setMarkingRead(null)
    }
  }

  async function handleMarkAllRead() {
    try {
      setMarkingAllRead(true)
      const unreadAlerts = alerts.filter((a) => !a.is_read)
      await Promise.all(unreadAlerts.map((a) => markAlertRead(a.id)))
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })))
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    } finally {
      setMarkingAllRead(false)
    }
  }

  // Pagination
  const totalPages = Math.ceil(alerts.length / PAGE_SIZE)
  const paginatedAlerts = alerts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const unreadCount = alerts.filter((a) => !a.is_read).length

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600" />
          <p className="mt-3 text-slate-600">Loading alerts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center">
          <AlertTriangle className="mx-auto h-10 w-10 text-red-500" />
          <p className="mt-2 text-lg font-medium text-red-700">{error}</p>
          <button
            onClick={fetchAlerts}
            className="mt-4 rounded-lg bg-red-600 px-5 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
          <p className="mt-1 text-sm text-slate-500">
            {unreadCount > 0
              ? `${unreadCount} unread alert${unreadCount > 1 ? 's' : ''}`
              : 'All caught up!'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAlerts}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingAllRead}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {markingAllRead ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCheck className="h-4 w-4" />
              )}
              Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-white p-1">
        <Filter className="ml-2 h-4 w-4 shrink-0 text-slate-400" />
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            )}
          >
            {tab.label}
            {tab.key === 'unread' && unreadCount > 0 && (
              <span className="ml-1.5 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Alert List */}
      {paginatedAlerts.length > 0 ? (
        <div className="space-y-2">
          {paginatedAlerts.map((alert) => (
            <div
              key={alert.id}
              onClick={() => !alert.is_read && handleMarkRead(alert.id)}
              className={cn(
                'group cursor-pointer rounded-xl border p-4 transition-all hover:shadow-md',
                alert.is_read
                  ? 'border-slate-200 bg-white'
                  : 'border-blue-200 bg-blue-50/30'
              )}
            >
              <div className="flex items-start gap-4">
                {/* Severity Icon */}
                <div
                  className={cn(
                    'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                    getSeverityColor(alert.severity)
                  )}
                >
                  {getSeverityIcon(alert.severity)}
                </div>

                {/* Content */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3
                          className={cn(
                            'text-sm',
                            alert.is_read
                              ? 'font-medium text-slate-700'
                              : 'font-semibold text-slate-900'
                          )}
                        >
                          {alert.title}
                        </h3>

                        {/* Unread indicator */}
                        {!alert.is_read && (
                          <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
                        )}
                      </div>

                      <p className="mt-1 text-sm text-slate-600">{alert.message}</p>

                      {/* Meta row */}
                      <div className="mt-2 flex flex-wrap items-center gap-3">
                        {/* Severity Badge */}
                        <span
                          className={cn(
                            'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                            getSeverityColor(alert.severity)
                          )}
                        >
                          {alert.severity}
                        </span>

                        {/* Timestamp */}
                        <span className="text-xs text-slate-500">
                          {formatRelative(alert.created_at)}
                        </span>

                        {/* Sent via badges */}
                        {alert.sent_via &&
                          alert.sent_via.length > 0 &&
                          alert.sent_via.map((channel) => (
                            <span
                              key={channel}
                              className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs text-slate-600"
                            >
                              {getSentViaIcon(channel)}
                              {channel}
                            </span>
                          ))}

                        {/* Lead link */}
                        {alert.lead_id && (
                          <a
                            href={`/leads/${alert.lead_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View Lead
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Mark as read button */}
                    {!alert.is_read && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleMarkRead(alert.id)
                        }}
                        disabled={markingRead === alert.id}
                        className="shrink-0 rounded-lg border border-slate-200 bg-white p-2 text-slate-500 opacity-0 transition-opacity hover:bg-slate-50 group-hover:opacity-100"
                        title="Mark as read"
                      >
                        {markingRead === alert.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCheck className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
            <BellOff className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-800">No alerts found</h3>
          <p className="mt-1 text-sm text-slate-500">
            {activeTab === 'unread'
              ? 'You have read all your alerts. Great job!'
              : activeTab !== 'all'
              ? `No ${activeTab} severity alerts at the moment.`
              : 'No alerts have been generated yet. They will appear here as your leads progress.'}
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
          <p className="text-sm text-slate-600">
            Showing {(page - 1) * PAGE_SIZE + 1}-
            {Math.min(page * PAGE_SIZE, alerts.length)} of {alerts.length} alerts
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={cn(
                  'inline-flex h-8 w-8 items-center justify-center rounded-lg text-sm font-medium transition-colors',
                  page === p
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                )}
              >
                {p}
              </button>
            ))}

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
