import { useState, useEffect } from 'react'
import {
  Shield,
  Users,
  RefreshCw,
  Cpu,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  IndianRupee,
  Zap,
  Database,
  ShieldAlert,
  Activity,
  Hash,
} from 'lucide-react'
import { getUsers, getSyncStatus, triggerSync, getAIUsage } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../lib/types'
import { formatDate, formatRelative, cn } from '../lib/utils'

type AdminTab = 'users' | 'sync' | 'ai-usage'

interface SyncStatusData {
  last_sync_at: string | null
  status: 'success' | 'failed' | 'running' | 'idle'
  records_synced: number
  error_message?: string
  history?: Array<{
    id: string
    synced_at: string
    status: string
    records_synced: number
    duration_seconds?: number
    error_message?: string
  }>
}

interface AIUsageData {
  total_cost: number
  calls_today: number
  avg_cost_per_call: number
  usage_by_model?: Array<{
    model: string
    calls: number
    total_cost: number
    avg_cost: number
  }>
  recent_calls?: Array<{
    id: string
    model: string
    endpoint: string
    tokens_used: number
    cost: number
    created_at: string
  }>
}

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  founder: 'bg-purple-100 text-purple-700',
  manager: 'bg-blue-100 text-blue-700',
  team_lead: 'bg-indigo-100 text-indigo-700',
  rep: 'bg-green-100 text-green-700',
}

const ALLOWED_ROLES = ['manager', 'founder', 'admin']

export default function AdminPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<AdminTab>('users')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Users state
  const [users, setUsers] = useState<User[]>([])

  // Sync state
  const [syncStatus, setSyncStatus] = useState<SyncStatusData | null>(null)
  const [triggeringSyncNow, setTriggeringSyncNow] = useState(false)

  // AI Usage state
  const [aiUsage, setAiUsage] = useState<AIUsageData | null>(null)

  // Access check
  if (!user || !ALLOWED_ROLES.includes(user.role)) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-xl border border-red-200 bg-red-50 p-10 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <ShieldAlert className="h-8 w-8 text-red-600" />
          </div>
          <h2 className="mt-4 text-xl font-bold text-red-800">Access Denied</h2>
          <p className="mt-2 text-sm text-red-600">
            You do not have permission to access the admin panel.
            <br />
            This page is restricted to managers, founders, and admins.
          </p>
        </div>
      </div>
    )
  }

  useEffect(() => {
    fetchTabData()
  }, [activeTab])

  async function fetchTabData() {
    try {
      setLoading(true)
      setError(null)

      switch (activeTab) {
        case 'users': {
          const res = await getUsers()
          setUsers(res.data?.data || res.data || [])
          break
        }
        case 'sync': {
          const res = await getSyncStatus()
          setSyncStatus(res.data?.data || res.data || null)
          break
        }
        case 'ai-usage': {
          const res = await getAIUsage()
          setAiUsage(res.data?.data || res.data || null)
          break
        }
      }
    } catch (err) {
      setError(`Failed to load ${activeTab} data`)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleTriggerSync() {
    try {
      setTriggeringSyncNow(true)
      await triggerSync()
      // Refresh sync status after triggering
      const res = await getSyncStatus()
      setSyncStatus(res.data?.data || res.data || null)
    } catch (err) {
      console.error('Failed to trigger sync:', err)
    } finally {
      setTriggeringSyncNow(false)
    }
  }

  function formatCost(amount: number): string {
    if (amount < 0.01) return `$${amount.toFixed(4)}`
    return `$${amount.toFixed(2)}`
  }

  // Tab configs
  const tabs: { key: AdminTab; label: string; icon: React.ReactNode }[] = [
    { key: 'users', label: 'Users', icon: <Users className="h-4 w-4" /> },
    { key: 'sync', label: 'Sync Status', icon: <RefreshCw className="h-4 w-4" /> },
    { key: 'ai-usage', label: 'AI Usage', icon: <Cpu className="h-4 w-4" /> },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Admin Panel</h1>
            <p className="text-sm text-slate-500">
              System management and monitoring
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600" />
            <p className="mt-3 text-slate-600">Loading {activeTab} data...</p>
          </div>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center">
          <AlertTriangle className="mx-auto h-10 w-10 text-red-500" />
          <p className="mt-2 text-lg font-medium text-red-700">{error}</p>
          <button
            onClick={fetchTabData}
            className="mt-4 rounded-lg bg-red-600 px-5 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="rounded-xl border border-slate-200 bg-white">
              <div className="border-b border-slate-200 px-6 py-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-slate-900">
                    Team Members
                  </h3>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                    {users.length} users
                  </span>
                </div>
              </div>

              {users.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 bg-slate-50/50">
                        <th className="px-6 py-3 text-left font-medium text-slate-500">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left font-medium text-slate-500">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left font-medium text-slate-500">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left font-medium text-slate-500">
                          Team
                        </th>
                        <th className="px-6 py-3 text-center font-medium text-slate-500">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-50">
                          <td className="px-6 py-3.5">
                            <div className="flex items-center gap-3">
                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                                {u.full_name
                                  .split(' ')
                                  .map((n) => n[0])
                                  .join('')
                                  .toUpperCase()
                                  .slice(0, 2)}
                              </div>
                              <span className="font-medium text-slate-800">
                                {u.full_name}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3.5 text-slate-600">{u.email}</td>
                          <td className="px-6 py-3.5">
                            <span
                              className={cn(
                                'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                                ROLE_COLORS[u.role] || 'bg-gray-100 text-gray-700'
                              )}
                            >
                              {u.role.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-3.5 text-slate-600">
                            {u.team || (
                              <span className="text-slate-400">--</span>
                            )}
                          </td>
                          <td className="px-6 py-3.5 text-center">
                            {u.is_active ? (
                              <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
                                <CheckCircle className="h-3 w-3" />
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600">
                                <XCircle className="h-3 w-3" />
                                Inactive
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center">
                  <Users className="mx-auto h-8 w-8 text-slate-400" />
                  <p className="mt-2 text-sm text-slate-500">No users found</p>
                </div>
              )}
            </div>
          )}

          {/* Sync Status Tab */}
          {activeTab === 'sync' && syncStatus && (
            <div className="space-y-6">
              {/* Current Status */}
              <div className="rounded-xl border border-slate-200 bg-white p-6">
                <h3 className="mb-4 text-base font-semibold text-slate-900">
                  Current Sync Status
                </h3>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {/* Last Sync */}
                  <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Clock className="h-4 w-4" />
                      Last Sync
                    </div>
                    <p className="mt-1 text-lg font-semibold text-slate-800">
                      {syncStatus.last_sync_at
                        ? formatRelative(syncStatus.last_sync_at)
                        : 'Never'}
                    </p>
                    {syncStatus.last_sync_at && (
                      <p className="mt-0.5 text-xs text-slate-500">
                        {formatDate(syncStatus.last_sync_at)}
                      </p>
                    )}
                  </div>

                  {/* Status */}
                  <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Activity className="h-4 w-4" />
                      Status
                    </div>
                    <div className="mt-1">
                      <span
                        className={cn(
                          'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium capitalize',
                          syncStatus.status === 'success'
                            ? 'bg-green-100 text-green-700'
                            : syncStatus.status === 'failed'
                            ? 'bg-red-100 text-red-700'
                            : syncStatus.status === 'running'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-100 text-gray-700'
                        )}
                      >
                        {syncStatus.status === 'success' && (
                          <CheckCircle className="h-3.5 w-3.5" />
                        )}
                        {syncStatus.status === 'failed' && (
                          <XCircle className="h-3.5 w-3.5" />
                        )}
                        {syncStatus.status === 'running' && (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        )}
                        {syncStatus.status}
                      </span>
                    </div>
                  </div>

                  {/* Records */}
                  <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Database className="h-4 w-4" />
                      Records Synced
                    </div>
                    <p className="mt-1 text-lg font-semibold text-slate-800">
                      {syncStatus.records_synced.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Error message */}
                {syncStatus.error_message && (
                  <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                      <p className="text-sm text-red-700">{syncStatus.error_message}</p>
                    </div>
                  </div>
                )}

                {/* Trigger Sync Button */}
                <div className="mt-5">
                  <button
                    onClick={handleTriggerSync}
                    disabled={triggeringSyncNow || syncStatus.status === 'running'}
                    className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {triggeringSyncNow ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    {triggeringSyncNow ? 'Triggering...' : 'Trigger Sync Now'}
                  </button>
                </div>
              </div>

              {/* Sync History */}
              {syncStatus.history && syncStatus.history.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white">
                  <div className="border-b border-slate-200 px-6 py-4">
                    <h3 className="text-base font-semibold text-slate-900">Sync History</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 bg-slate-50/50">
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Time
                          </th>
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Status
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Records
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Duration
                          </th>
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Error
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {syncStatus.history.map((entry) => (
                          <tr key={entry.id} className="hover:bg-slate-50">
                            <td className="px-6 py-3 text-slate-700">
                              {formatRelative(entry.synced_at)}
                            </td>
                            <td className="px-6 py-3">
                              <span
                                className={cn(
                                  'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                                  entry.status === 'success'
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-red-100 text-red-700'
                                )}
                              >
                                {entry.status === 'success' ? (
                                  <CheckCircle className="h-3 w-3" />
                                ) : (
                                  <XCircle className="h-3 w-3" />
                                )}
                                {entry.status}
                              </span>
                            </td>
                            <td className="px-6 py-3 text-right text-slate-700">
                              {entry.records_synced.toLocaleString()}
                            </td>
                            <td className="px-6 py-3 text-right text-slate-600">
                              {entry.duration_seconds
                                ? `${entry.duration_seconds}s`
                                : '--'}
                            </td>
                            <td className="max-w-xs truncate px-6 py-3 text-xs text-red-600">
                              {entry.error_message || '--'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'sync' && !syncStatus && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <RefreshCw className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-2 text-sm text-slate-500">
                No sync status data available
              </p>
              <button
                onClick={handleTriggerSync}
                disabled={triggeringSyncNow}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {triggeringSyncNow ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Trigger First Sync
              </button>
            </div>
          )}

          {/* AI Usage Tab */}
          {activeTab === 'ai-usage' && aiUsage && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-500">Total Cost</span>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-50">
                      <IndianRupee className="h-4 w-4 text-green-600" />
                    </div>
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {formatCost(aiUsage.total_cost)}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-500">Calls Today</span>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
                      <Zap className="h-4 w-4 text-blue-600" />
                    </div>
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {aiUsage.calls_today}
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-500">
                      Avg Cost/Call
                    </span>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-50">
                      <Activity className="h-4 w-4 text-purple-600" />
                    </div>
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {formatCost(aiUsage.avg_cost_per_call)}
                  </p>
                </div>
              </div>

              {/* Usage by Model */}
              {aiUsage.usage_by_model && aiUsage.usage_by_model.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white">
                  <div className="border-b border-slate-200 px-6 py-4">
                    <h3 className="text-base font-semibold text-slate-900">
                      Usage by Model
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 bg-slate-50/50">
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Model
                          </th>
                          <th className="px-6 py-3 text-center font-medium text-slate-500">
                            Calls
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Total Cost
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Avg Cost
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {aiUsage.usage_by_model.map((model) => (
                          <tr key={model.model} className="hover:bg-slate-50">
                            <td className="px-6 py-3">
                              <span className="inline-flex items-center gap-2 font-medium text-slate-800">
                                <Cpu className="h-4 w-4 text-slate-400" />
                                {model.model}
                              </span>
                            </td>
                            <td className="px-6 py-3 text-center text-slate-600">
                              {model.calls}
                            </td>
                            <td className="px-6 py-3 text-right font-medium text-slate-800">
                              {formatCost(model.total_cost)}
                            </td>
                            <td className="px-6 py-3 text-right text-slate-600">
                              {formatCost(model.avg_cost)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Recent Calls */}
              {aiUsage.recent_calls && aiUsage.recent_calls.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white">
                  <div className="border-b border-slate-200 px-6 py-4">
                    <h3 className="text-base font-semibold text-slate-900">Recent Calls</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 bg-slate-50/50">
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Model
                          </th>
                          <th className="px-6 py-3 text-left font-medium text-slate-500">
                            Endpoint
                          </th>
                          <th className="px-6 py-3 text-center font-medium text-slate-500">
                            Tokens
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Cost
                          </th>
                          <th className="px-6 py-3 text-right font-medium text-slate-500">
                            Time
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {aiUsage.recent_calls.map((call) => (
                          <tr key={call.id} className="hover:bg-slate-50">
                            <td className="px-6 py-3 font-medium text-slate-800">
                              {call.model}
                            </td>
                            <td className="px-6 py-3">
                              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700">
                                {call.endpoint}
                              </span>
                            </td>
                            <td className="px-6 py-3 text-center">
                              <span className="inline-flex items-center gap-1 text-slate-600">
                                <Hash className="h-3 w-3" />
                                {call.tokens_used.toLocaleString()}
                              </span>
                            </td>
                            <td className="px-6 py-3 text-right font-medium text-slate-800">
                              {formatCost(call.cost)}
                            </td>
                            <td className="px-6 py-3 text-right text-xs text-slate-500">
                              {formatRelative(call.created_at)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'ai-usage' && !aiUsage && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <Cpu className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-2 text-sm text-slate-500">
                No AI usage data available yet
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
