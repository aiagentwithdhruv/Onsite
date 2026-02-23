'use client'

import { useEffect, useState } from 'react'
import { Settings, RefreshCw, Loader2, Users, Database, Cpu, Zap, Hash } from 'lucide-react'
import { getUsers, getSyncStatus, triggerSync, getAIUsage } from '@/lib/api'
import type { User } from '@/lib/types'

function getRoleBadge(role: string): string {
  const colors: Record<string, string> = {
    founder: 'bg-violet-500/15 text-violet-600 dark:text-violet-400',
    admin: 'bg-rose-500/15 text-rose-600 dark:text-rose-400',
    manager: 'bg-fuchsia-500/15 text-fuchsia-600 dark:text-fuchsia-400',
    team_lead: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    rep: 'bg-sky-500/15 text-sky-600 dark:text-sky-400',
  }
  return colors[role] || 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400'
}

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([])
  const [syncStatus, setSyncStatus] = useState<{ last_sync_at?: string; status?: string } | null>(null)
  const [aiUsage, setAIUsage] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const [usersRes, syncRes, usageRes] = await Promise.allSettled([
          getUsers(),
          getSyncStatus(),
          getAIUsage(),
        ])
        if (usersRes.status === 'fulfilled') {
          const data = usersRes.value.data as User[] | { data?: User[] }
          setUsers(Array.isArray(data) ? data : data?.data ?? [])
        }
        if (syncRes.status === 'fulfilled') {
          setSyncStatus((syncRes.value.data as { last_sync_at?: string }) ?? null)
        }
        if (usageRes.status === 'fulfilled') {
          setAIUsage((usageRes.value.data as Record<string, unknown>) ?? null)
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  async function handleSync() {
    setSyncing(true)
    try {
      await triggerSync()
      const res = await getSyncStatus()
      setSyncStatus((res.data as { last_sync_at?: string }) ?? null)
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-violet-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Admin</h2>
        <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
          Users, sync status, and AI usage
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
              <Database className="h-5 w-5 text-violet-500" />
              Zoho Sync
            </h3>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="glow-btn flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-50"
            >
              {syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Sync now
            </button>
          </div>
          {syncStatus && (
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Last sync: {(syncStatus as { last_sync_at?: string }).last_sync_at || 'Never'}
            </p>
          )}
        </div>

        {aiUsage && (
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
              <Cpu className="h-5 w-5 text-violet-500" />
              AI Usage
            </h3>
            <AIUsageDisplay data={aiUsage} />
          </div>
        )}
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
          <Users className="h-5 w-5 text-violet-500" />
          Users
        </h3>
        {users.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No users</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-100 text-left text-xs font-medium uppercase text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
                  <th className="pb-2 pr-4">Name</th>
                  <th className="pb-2 pr-4">Email</th>
                  <th className="pb-2">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="py-3 pr-4 font-medium text-zinc-900 dark:text-white">
                      {u.name || u.full_name || '–'}
                    </td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{u.email}</td>
                    <td className="py-3">
                      <span className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold capitalize ${getRoleBadge(u.role)}`}>
                        {u.role?.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function AIUsageDisplay({ data }: { data: Record<string, unknown> }) {
  // Try to extract meaningful fields from the usage data
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined)

  // Check if it has known structure (total_calls, total_tokens, etc.)
  const knownMetrics: { key: string; label: string; icon: React.ReactNode; format?: (v: unknown) => string }[] = [
    { key: 'total_calls', label: 'Total API Calls', icon: <Zap className="h-4 w-4 text-violet-500" /> },
    { key: 'total_tokens', label: 'Total Tokens', icon: <Hash className="h-4 w-4 text-violet-500" /> },
    { key: 'total_cost', label: 'Total Cost', icon: <Settings className="h-4 w-4 text-emerald-500" />, format: (v) => `$${Number(v).toFixed(4)}` },
    { key: 'calls_today', label: 'Calls Today', icon: <Zap className="h-4 w-4 text-sky-500" /> },
    { key: 'tokens_today', label: 'Tokens Today', icon: <Hash className="h-4 w-4 text-sky-500" /> },
  ]

  const rendered = knownMetrics.filter(m => data[m.key] !== undefined)

  if (rendered.length > 0) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {rendered.map(m => (
            <div key={m.key} className="rounded-lg border border-zinc-100 bg-zinc-50/50 p-3 dark:border-zinc-800 dark:bg-zinc-800/30">
              <div className="mb-1 flex items-center gap-1.5">
                {m.icon}
                <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">{m.label}</span>
              </div>
              <p className="text-lg font-bold text-zinc-900 dark:text-white">
                {m.format ? m.format(data[m.key]) : Number(data[m.key]).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
        {/* Show remaining fields that weren't in known metrics */}
        {entries.filter(([k]) => !knownMetrics.some(m => m.key === k)).length > 0 && (
          <details className="group">
            <summary className="cursor-pointer text-xs font-medium text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300">
              Show raw data
            </summary>
            <pre className="mt-2 overflow-auto rounded-lg bg-zinc-50 p-3 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              {JSON.stringify(
                Object.fromEntries(entries.filter(([k]) => !knownMetrics.some(m => m.key === k))),
                null,
                2
              )}
            </pre>
          </details>
        )}
      </div>
    )
  }

  // Fallback: render all entries as a grid of key-value pairs
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        {entries.slice(0, 8).map(([key, value]) => (
          <div key={key} className="rounded-lg border border-zinc-100 bg-zinc-50/50 p-3 dark:border-zinc-800 dark:bg-zinc-800/30">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
              {key.replace(/_/g, ' ')}
            </p>
            <p className="mt-0.5 text-sm font-semibold text-zinc-900 dark:text-white">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </p>
          </div>
        ))}
      </div>
      {entries.length > 8 && (
        <details className="group">
          <summary className="cursor-pointer text-xs font-medium text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300">
            Show all ({entries.length} fields)
          </summary>
          <pre className="mt-2 overflow-auto rounded-lg bg-zinc-50 p-3 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            {JSON.stringify(data, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}
