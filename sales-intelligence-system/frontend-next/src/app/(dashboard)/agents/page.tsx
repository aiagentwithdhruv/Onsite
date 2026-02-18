'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Users, TrendingUp, Target, Flame, AlertTriangle, CheckCircle, ChevronDown,
  ChevronUp, MessageSquarePlus, Send, BarChart3, Phone, Award, Clock,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from 'recharts'
import { getAgentProfiles, addAgentNote } from '@/lib/api'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Profile = Record<string, any>

export default function AgentsPage() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [noteText, setNoteText] = useState('')
  const [addingNote, setAddingNote] = useState(false)
  const [sortBy, setSortBy] = useState<'leads' | 'conversion' | 'stale'>('leads')

  useEffect(() => {
    getAgentProfiles().then(res => {
      setProfiles(res.data?.profiles || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleAddNote = useCallback(async (agentId: string) => {
    if (!noteText.trim()) return
    setAddingNote(true)
    try {
      await addAgentNote(agentId, noteText.trim())
      setNoteText('')
      const res = await getAgentProfiles()
      setProfiles(res.data?.profiles || [])
    } catch { /* ignore */ }
    setAddingNote(false)
  }, [noteText])

  const sorted = [...profiles].sort((a, b) => {
    const pa = a.performance || {}
    const pb = b.performance || {}
    if (sortBy === 'conversion') return (pb.sale_rate || 0) - (pa.sale_rate || 0)
    if (sortBy === 'stale') return (pb.stale_30 || 0) - (pa.stale_30 || 0)
    return (pb.total_leads || 0) - (pa.total_leads || 0)
  })

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-zinc-300 border-t-amber-500" />
        <p className="text-sm text-zinc-500">Loading agent profiles...</p>
      </div>
    )
  }

  if (profiles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <Users className="mb-4 h-16 w-16 text-zinc-300" />
        <h2 className="mb-2 text-xl font-bold text-zinc-700 dark:text-zinc-300">No Agent Profiles Yet</h2>
        <p className="max-w-md text-sm text-zinc-500">
          Upload a CSV in the Intelligence page to auto-generate profiles for every deal owner.
          Profiles include performance, patterns, strengths, concerns, and monthly trends.
        </p>
      </div>
    )
  }

  // Summary KPIs
  const totalAgents = profiles.length
  const totalLeads = profiles.reduce((s, p) => s + (p.performance?.total_leads || 0), 0)
  const totalSales = profiles.reduce((s, p) => s + (p.performance?.sales_done || 0), 0)
  const avgConversion = totalLeads ? (totalSales / totalLeads * 100).toFixed(2) : '0'
  const topPerformer = [...profiles].sort((a, b) => (b.performance?.sale_rate || 0) - (a.performance?.sale_rate || 0))[0]
  const mostConcerns = [...profiles].sort((a, b) => (b.concerns?.length || 0) - (a.concerns?.length || 0))[0]

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-zinc-900 dark:text-white">Agent Profiles</h1>
        <p className="text-sm text-zinc-500">{totalAgents} deal owners &middot; Performance memory that learns with every upload</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <KpiCard icon={Users} label="Agents" value={totalAgents} color="text-blue-500" />
        <KpiCard icon={Target} label="Total Leads" value={totalLeads} color="text-purple-500" />
        <KpiCard icon={TrendingUp} label="Total Sales" value={totalSales} color="text-green-500" />
        <KpiCard icon={BarChart3} label="Avg Conv %" value={`${avgConversion}%`} color="text-amber-500" />
        <KpiCard icon={Award} label="Top Performer" value={topPerformer?.name || '-'} color="text-indigo-500" small />
      </div>

      {/* Sort */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-zinc-400">Sort by:</span>
        {[
          { key: 'leads' as const, label: 'Most Leads' },
          { key: 'conversion' as const, label: 'Best Conversion' },
          { key: 'stale' as const, label: 'Most Stale' },
        ].map(s => (
          <button key={s.key} onClick={() => setSortBy(s.key)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${sortBy === s.key ? 'bg-amber-500 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400'}`}>
            {s.label}
          </button>
        ))}
      </div>

      {/* Profile Cards */}
      <div className="space-y-3">
        {sorted.map(profile => {
          const p = profile.performance || {}
          const isExpanded = expandedId === profile.id
          const convColor = (p.sale_rate || 0) > 5 ? 'text-green-500' : (p.sale_rate || 0) > 2 ? 'text-amber-500' : 'text-red-500'

          return (
            <div key={profile.id} className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
              {/* Card Header */}
              <div
                className="flex cursor-pointer items-center justify-between px-5 py-4"
                onClick={() => setExpandedId(isExpanded ? null : profile.id)}
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-500/15 text-sm font-bold text-amber-600">
                    {profile.name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-zinc-800 dark:text-white">{profile.name}</h3>
                    <p className="text-xs text-zinc-400">{profile.manager ? `Manager: ${profile.manager}` : 'Deal Owner'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <Stat label="Leads" value={p.total_leads || 0} />
                  <Stat label="Demos" value={p.demos_done || 0} />
                  <Stat label="Sales" value={p.sales_done || 0} />
                  <Stat label="Conv %" value={`${p.sale_rate || 0}%`} className={convColor} />
                  {(p.stale_30 || 0) > 0 && (
                    <div className="flex items-center gap-1 rounded-lg bg-red-50 px-2 py-1 dark:bg-red-500/10">
                      <AlertTriangle className="h-3 w-3 text-red-500" />
                      <span className="text-xs font-semibold text-red-600">{p.stale_30} stale</span>
                    </div>
                  )}
                  {isExpanded ? <ChevronUp className="h-4 w-4 text-zinc-400" /> : <ChevronDown className="h-4 w-4 text-zinc-400" />}
                </div>
              </div>

              {/* Expanded Detail */}
              {isExpanded && (
                <div className="border-t border-zinc-100 px-5 py-4 dark:border-zinc-800">
                  <div className="grid gap-4 lg:grid-cols-3">
                    {/* Left: Strengths & Concerns */}
                    <div className="space-y-3">
                      {(profile.strengths || []).length > 0 && (
                        <div>
                          <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-green-600"><CheckCircle className="h-3.5 w-3.5" /> Strengths</h4>
                          <ul className="space-y-1">
                            {profile.strengths.map((s: string, i: number) => (
                              <li key={i} className="rounded bg-green-50 px-2.5 py-1.5 text-xs text-green-700 dark:bg-green-500/10 dark:text-green-400">{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(profile.concerns || []).length > 0 && (
                        <div>
                          <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-red-600"><AlertTriangle className="h-3.5 w-3.5" /> Concerns</h4>
                          <ul className="space-y-1">
                            {profile.concerns.map((c: string, i: number) => (
                              <li key={i} className="rounded bg-red-50 px-2.5 py-1.5 text-xs text-red-700 dark:bg-red-500/10 dark:text-red-400">{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Patterns */}
                      <div>
                        <h4 className="mb-1.5 text-xs font-semibold text-zinc-500">Patterns</h4>
                        {(profile.patterns?.top_sources || []).length > 0 && (
                          <p className="text-xs text-zinc-500"><span className="font-medium text-zinc-700 dark:text-zinc-300">Top sources:</span> {profile.patterns.top_sources.join(', ')}</p>
                        )}
                        {(profile.patterns?.top_regions || []).length > 0 && (
                          <p className="text-xs text-zinc-500"><span className="font-medium text-zinc-700 dark:text-zinc-300">Top regions:</span> {profile.patterns.top_regions.join(', ')}</p>
                        )}
                        <p className="text-xs text-zinc-500"><span className="font-medium text-zinc-700 dark:text-zinc-300">Avg/month:</span> {profile.patterns?.avg_leads_per_month || 0} leads</p>
                      </div>
                    </div>

                    {/* Center: Performance Metrics */}
                    <div className="space-y-3">
                      <h4 className="text-xs font-semibold text-zinc-500">Performance</h4>
                      <div className="grid grid-cols-2 gap-2">
                        <MiniStat label="Demo Rate" value={`${p.demo_rate || 0}%`} />
                        <MiniStat label="Demo→Sale" value={`${p.demo_to_sale || 0}%`} />
                        <MiniStat label="Priority" value={p.priority || 0} />
                        <MiniStat label="Prospects" value={p.prospects || 0} />
                        <MiniStat label="Recent 7d" value={p.recent_7d_touches || 0} />
                        <MiniStat label="Demo Booked" value={p.demo_booked || 0} />
                      </div>

                      {/* Monthly Trend Chart */}
                      {(profile.monthly_history || []).length > 0 && (
                        <div>
                          <h4 className="mb-1 text-xs font-semibold text-zinc-500">Monthly Trend</h4>
                          <ResponsiveContainer width="100%" height={150}>
                            <BarChart data={profile.monthly_history}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                              <XAxis dataKey="month" tick={{ fontSize: 8 }} />
                              <YAxis tick={{ fontSize: 8 }} />
                              <Tooltip />
                              <Bar dataKey="leads" fill="#6366f1" radius={[2, 2, 0, 0]} />
                              <Bar dataKey="sales" fill="#22c55e" radius={[2, 2, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>

                    {/* Right: Notes */}
                    <div className="space-y-3">
                      <h4 className="flex items-center gap-1.5 text-xs font-semibold text-zinc-500">
                        <MessageSquarePlus className="h-3.5 w-3.5" /> Notes & Context
                      </h4>

                      {(profile.notes || []).length > 0 ? (
                        <div className="max-h-40 space-y-1.5 overflow-auto">
                          {profile.notes.map((n: { text: string; added_by?: string; added_at?: string }, i: number) => (
                            <div key={i} className="rounded bg-zinc-50 px-2.5 py-2 dark:bg-zinc-800/50">
                              <p className="text-xs text-zinc-700 dark:text-zinc-300">{n.text}</p>
                              <p className="mt-0.5 text-[10px] text-zinc-400">{n.added_by} &middot; {n.added_at ? new Date(n.added_at).toLocaleDateString() : ''}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-zinc-400">No notes yet. Add context about this person.</p>
                      )}

                      <div className="flex gap-2">
                        <input
                          value={noteText}
                          onChange={e => setNoteText(e.target.value)}
                          placeholder="Add a note..."
                          className="flex-1 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs text-zinc-700 placeholder:text-zinc-400 focus:border-amber-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                          onKeyDown={e => { if (e.key === 'Enter') handleAddNote(profile.id) }}
                        />
                        <button
                          onClick={() => handleAddNote(profile.id)}
                          disabled={addingNote || !noteText.trim()}
                          className="rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-400 disabled:opacity-50"
                        >
                          <Send className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <p className="mt-3 text-right text-[10px] text-zinc-400">
                    <Clock className="mr-1 inline h-3 w-3" />
                    Last updated: {profile.last_updated ? new Date(profile.last_updated).toLocaleString() : 'N/A'}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function KpiCard({ icon: Icon, label, value, color, small }: { icon: React.ElementType; label: string; value: string | number; color: string; small?: boolean }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-1 flex items-center gap-1.5">
        <Icon className={`h-3.5 w-3.5 ${color}`} />
        <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">{label}</span>
      </div>
      <p className={`font-bold ${color} ${small ? 'text-sm' : 'text-xl'}`}>{typeof value === 'number' ? value.toLocaleString() : value}</p>
    </div>
  )
}

function Stat({ label, value, className = '' }: { label: string; value: string | number; className?: string }) {
  return (
    <div className="hidden text-center sm:block">
      <p className={`text-sm font-bold ${className || 'text-zinc-700 dark:text-zinc-200'}`}>{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-[10px] text-zinc-400">{label}</p>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-zinc-50 px-2.5 py-1.5 dark:bg-zinc-800/50">
      <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-200">{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-[10px] text-zinc-400">{label}</p>
    </div>
  )
}
