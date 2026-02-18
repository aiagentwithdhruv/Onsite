'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { Settings, RefreshCw, Loader2, Users, Database, Edit2, Check, X, Target } from 'lucide-react'
import { getUsers, getSyncStatus, triggerSync, getAIUsage, getDealOwners, updateUser, getTeamAttention } from '@/lib/api'
import type { TeamAttentionItem } from '@/lib/api'
import type { User } from '@/lib/types'
import { useAuth } from '@/contexts/AuthContext'

const ROLES = ['rep', 'team_lead', 'manager', 'founder', 'admin'] as const

export default function AdminPage() {
  const { session, loading: authLoading } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [dealOwners, setDealOwners] = useState<string[]>([])
  const [syncStatus, setSyncStatus] = useState<{ last_sync_at?: string; status?: string } | null>(null)
  const [aiUsage, setAIUsage] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editRole, setEditRole] = useState<string>('rep')
  const [editDealOwner, setEditDealOwner] = useState<string>('')
  const [editDealOwnerCustom, setEditDealOwnerCustom] = useState<string>('') // when not in dropdown
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [teamAttention, setTeamAttention] = useState<TeamAttentionItem[]>([])
  const hasFetched = useRef(false)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [usersRes, syncRes, usageRes, dealOwnersRes, teamRes] = await Promise.allSettled([
        getUsers(),
        getSyncStatus(),
        getAIUsage(),
        getDealOwners(),
        getTeamAttention(),
      ])
      if (usersRes.status === 'fulfilled') {
        const data = usersRes.value.data as { users?: User[] } | User[]
        setUsers(Array.isArray(data) ? data : (data?.users ?? []))
      }
      if (syncRes.status === 'fulfilled') {
        setSyncStatus((syncRes.value.data as { last_sync_at?: string }) ?? null)
      }
      if (usageRes.status === 'fulfilled') {
        setAIUsage((usageRes.value.data as Record<string, unknown>) ?? null)
      }
      if (dealOwnersRes.status === 'fulfilled') {
        const d = dealOwnersRes.value.data as { deal_owners?: string[] }
        setDealOwners(d?.deal_owners ?? [])
      }
      if (teamRes.status === 'fulfilled' && teamRes.value.data) {
        const d = teamRes.value.data as { items?: TeamAttentionItem[] }
        setTeamAttention(d?.items ?? [])
      }
    } catch {
      // non-critical
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading) return
    if (!session) {
      setLoading(false)
      return
    }
    if (hasFetched.current) return
    hasFetched.current = true
    fetchData()
  }, [authLoading, session, fetchData])

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

  function startEdit(u: User) {
    setSaveError(null)
    setEditingId(u.id)
    setEditRole(u.role)
    const name = u.deal_owner_name ?? ''
    const inList = dealOwners.includes(name)
    setEditDealOwner(inList ? name : '')
    setEditDealOwnerCustom(inList ? '' : name)
  }

  async function saveEdit() {
    if (!editingId) return
    const finalDealOwner = editDealOwner || editDealOwnerCustom.trim() || null
    setSaving(true)
    setSaveError(null)
    try {
      await updateUser(editingId, { role: editRole, deal_owner_name: finalDealOwner })
      setUsers(prev => prev.map(u => u.id === editingId ? { ...u, role: editRole as User['role'], deal_owner_name: finalDealOwner } : u))
      setEditingId(null)
      setEditDealOwnerCustom('')
    } catch {
      setSaveError('Update failed. Check your connection and try again.')
    } finally {
      setSaving(false)
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

      {teamAttention.length > 0 && (
        <div className="rounded-2xl border border-amber-200/80 bg-gradient-to-br from-amber-50/80 to-orange-50/30 p-6 shadow-sm dark:border-amber-500/20 dark:from-amber-500/5 dark:to-amber-500/10">
          <h3 className="mb-2 flex items-center gap-3 text-lg font-semibold tracking-tight text-amber-800 dark:text-amber-200">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20">
              <Target className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </span>
            Team attention
          </h3>
          <p className="mb-5 text-xs text-zinc-600 dark:text-zinc-400">
            Who needs attention based on pipeline data. Use for 1:1s and coaching.
          </p>
          <div className="overflow-x-auto rounded-xl border border-amber-200/50 bg-white/60 dark:border-amber-500/10 dark:bg-zinc-900/30">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-amber-200/80 text-left text-xs font-semibold uppercase tracking-wider text-amber-700 dark:border-amber-500/20 dark:text-amber-300">
                  <th className="pb-2 pr-4">Name</th>
                  <th className="pb-2 pr-4">Stale</th>
                  <th className="pb-2 pr-4">Demos pending</th>
                  <th className="pb-2 pr-4">Sale %</th>
                  <th className="pb-2">Suggested action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-amber-100 dark:divide-amber-500/20">
                {teamAttention.map((row) => (
                  <tr key={row.deal_owner}>
                    <td className="py-3 pr-4 font-medium text-zinc-900 dark:text-white">{row.name}</td>
                    <td className="py-3 pr-4">
                      {row.stale_count > 0 ? (
                        <span className="rounded bg-red-100 px-1.5 py-0.5 text-red-700 dark:bg-red-500/20 dark:text-red-400">{row.stale_count}</span>
                      ) : (
                        <span className="text-zinc-500">0</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{row.demos_pending}</td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{row.sale_rate}%</td>
                    <td className="py-3">
                      <span className="text-amber-700 dark:text-amber-300">{row.suggested_action}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
          <Users className="h-5 w-5 text-amber-500" />
          Users & access
        </h3>
        <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
          Set Role and Deal owner (data access). Reps see only their deal owner&apos;s data; managers/admins see all. Match by email/first name or set explicitly (e.g. Amit.U → Amit Balasaheb Udagatti, Amit.K → Amit Kumar).
        </p>
        {saveError && (
          <div className="mb-4 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
            {saveError}
            <button type="button" onClick={() => setSaveError(null)} className="text-xs font-medium text-red-600 hover:underline dark:text-red-400">Dismiss</button>
          </div>
        )}
        {users.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No users</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-100 text-left text-xs font-medium uppercase text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
                  <th className="pb-2 pr-4">Name</th>
                  <th className="pb-2 pr-4">Email</th>
                  <th className="pb-2 pr-4">Role</th>
                  <th className="pb-2 pr-4">Deal owner (data access)</th>
                  <th className="pb-2 w-20">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {users.map((u) => (
                  <tr key={u.id}>
                    {editingId === u.id ? (
                      <>
                        <td className="py-2 pr-4 font-medium text-zinc-900 dark:text-white">{u.name || u.full_name || '–'}</td>
                        <td className="py-2 pr-4 text-zinc-600 dark:text-zinc-300">{u.email}</td>
                        <td className="py-2 pr-4">
                          <select value={editRole} onChange={e => setEditRole(e.target.value)} className="rounded border border-zinc-300 bg-white px-2 py-1 text-zinc-800 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200">
                            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                          </select>
                        </td>
                        <td className="py-2 pr-4">
                          <div className="flex flex-col gap-1">
                            <select value={editDealOwner} onChange={e => { setEditDealOwner(e.target.value); if (e.target.value) setEditDealOwnerCustom('') }} className="rounded border border-zinc-300 bg-white px-2 py-1 text-zinc-800 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200 max-w-[200px]">
                              <option value="">— All (manager/admin)</option>
                              {dealOwners.map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                            <input type="text" placeholder="Or type exact deal owner name" value={editDealOwnerCustom} onChange={e => { setEditDealOwnerCustom(e.target.value); if (e.target.value) setEditDealOwner('') }} className="max-w-[200px] rounded border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-800 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200" />
                          </div>
                        </td>
                        <td className="py-2">
                          <button onClick={saveEdit} disabled={saving} className="rounded p-1 text-green-600 hover:bg-green-500/10 dark:text-green-400"><Check className="h-4 w-4" /></button>
                          <button onClick={() => { setEditingId(null); setSaveError(null) }} className="ml-1 rounded p-1 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-700"><X className="h-4 w-4" /></button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-3 pr-4 font-medium text-zinc-900 dark:text-white">{u.name || u.full_name || '–'}</td>
                        <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{u.email}</td>
                        <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{u.role}</td>
                        <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{u.deal_owner_name || '—'}</td>
                        <td className="py-3">
                          <button onClick={() => startEdit(u)} className="rounded p-1.5 text-amber-500 hover:bg-amber-500/10 dark:text-amber-400" title="Edit role & access"><Edit2 className="h-4 w-4" /></button>
                        </td>
                      </>
                    )}
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
