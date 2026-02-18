'use client'

import { useEffect, useState, useRef } from 'react'
import { Settings, RefreshCw, Loader2, Users, Database } from 'lucide-react'
import { getUsers, getSyncStatus, triggerSync, getAIUsage } from '@/lib/api'
import type { User } from '@/lib/types'
import { useAuth } from '@/contexts/AuthContext'

export default function AdminPage() {
  const { session, loading: authLoading } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [syncStatus, setSyncStatus] = useState<{ last_sync_at?: string; status?: string } | null>(null)
  const [aiUsage, setAIUsage] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const hasFetched = useRef(false)

  useEffect(() => {
    if (authLoading) return
    if (!session) {
      setLoading(false)
      return
    }
    if (hasFetched.current) return
    hasFetched.current = true
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
      } catch {
        // non-critical
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [authLoading])

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
        <Loader2 className="h-10 w-10 animate-spin text-amber-500" />
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
              <Database className="h-5 w-5 text-amber-500" />
              Zoho Sync
            </h3>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-medium text-zinc-900 transition-colors hover:bg-amber-400 disabled:opacity-50"
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
              <Settings className="h-5 w-5 text-amber-500" />
              AI Usage
            </h3>
            <pre className="overflow-auto rounded-lg bg-zinc-50 p-3 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
              {JSON.stringify(aiUsage, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
          <Users className="h-5 w-5 text-amber-500" />
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
                    <td className="py-3 text-zinc-600 dark:text-zinc-300">{u.role}</td>
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
