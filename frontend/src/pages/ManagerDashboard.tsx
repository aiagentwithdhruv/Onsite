import { useState, useEffect } from 'react'
import {
  Users,
  Trophy,
  AlertTriangle,
  TrendingUp,
  Medal,
  ChevronRight,
  Loader2,
  Target,
  IndianRupee,
  BarChart3,
  Clock,
  Send,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { getRepPerformance, getPipelineFunnel, getLeads } from '../lib/api'
import type { RepPerformance, PipelineFunnel, Lead } from '../lib/types'
import { formatCurrency, cn } from '../lib/utils'

const FUNNEL_COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#0891b2']

interface StaleLeadInfo {
  id: string
  company_name: string
  assigned_rep_name?: string
  days_stale: number
  deal_value: number
}

export default function ManagerDashboard() {
  const [reps, setReps] = useState<RepPerformance[]>([])
  const [funnel, setFunnel] = useState<PipelineFunnel[]>([])
  const [staleLeads, setStaleLeads] = useState<StaleLeadInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nudgingId, setNudgingId] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      setLoading(true)
      setError(null)
      const [repRes, funnelRes, leadsRes] = await Promise.all([
        getRepPerformance(),
        getPipelineFunnel(),
        getLeads({ status: 'active' }),
      ])

      setReps(repRes.data?.data || repRes.data || [])
      setFunnel(funnelRes.data?.data || funnelRes.data || [])

      // Compute stale leads (no activity in 7+ days)
      const allLeads: Lead[] = leadsRes.data?.data || leadsRes.data || []
      const now = new Date()
      const stale = allLeads
        .filter((lead) => {
          if (!lead.last_activity_at) return true
          const lastActivity = new Date(lead.last_activity_at)
          const daysDiff = Math.floor(
            (now.getTime() - lastActivity.getTime()) / 86400000
          )
          return daysDiff >= 7
        })
        .map((lead) => ({
          id: lead.id,
          company_name: lead.company_name,
          assigned_rep_name: lead.assigned_rep_name || 'Unassigned',
          days_stale: lead.last_activity_at
            ? Math.floor(
                (now.getTime() - new Date(lead.last_activity_at).getTime()) /
                  86400000
              )
            : 30,
          deal_value: lead.deal_value,
        }))
        .sort((a, b) => b.days_stale - a.days_stale)
        .slice(0, 10)

      setStaleLeads(stale)
    } catch (err) {
      setError('Failed to load manager dashboard data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function getConversionColor(rate: number): string {
    if (rate >= 20) return 'text-green-600'
    if (rate >= 10) return 'text-yellow-600'
    return 'text-red-600'
  }

  function getConversionBgColor(rate: number): string {
    if (rate >= 20) return 'bg-green-500'
    if (rate >= 10) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  function getConversionBorderColor(rate: number): string {
    if (rate >= 20) return 'border-green-200 bg-green-50/50'
    if (rate >= 10) return 'border-yellow-200 bg-yellow-50/50'
    return 'border-red-200 bg-red-50/50'
  }

  function getRankIcon(index: number) {
    if (index === 0) return <Medal className="h-5 w-5 text-yellow-500" />
    if (index === 1) return <Medal className="h-5 w-5 text-gray-400" />
    if (index === 2) return <Medal className="h-5 w-5 text-amber-700" />
    return (
      <span className="inline-flex h-5 w-5 items-center justify-center text-xs font-semibold text-slate-500">
        {index + 1}
      </span>
    )
  }

  function handleNudge(leadId: string) {
    setNudgingId(leadId)
    // Simulated nudge - in production this would call an API
    setTimeout(() => setNudgingId(null), 1500)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-slate-600">Loading manager dashboard...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-red-500" />
        <p className="mt-2 text-red-700">{error}</p>
        <button
          onClick={fetchData}
          className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  const sortedReps = [...reps].sort((a, b) => b.conversion_rate - a.conversion_rate)
  const totalPipelineValue = funnel.reduce((sum, s) => sum + s.total_value, 0)

  return (
    <div className="space-y-8">
      {/* Section Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
          <Users className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Team Overview</h2>
          <p className="text-sm text-slate-500">
            {reps.length} reps &middot; {formatCurrency(totalPipelineValue)} total pipeline
          </p>
        </div>
      </div>

      {/* Team Performance Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {reps.map((rep) => (
          <div
            key={rep.rep_id}
            className={cn(
              'rounded-xl border p-5 transition-shadow hover:shadow-md',
              getConversionBorderColor(rep.conversion_rate)
            )}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">{rep.rep_name}</h3>
                <p className="mt-0.5 text-xs text-slate-500">
                  {rep.total_leads} leads &middot; {rep.won_deals} won
                </p>
              </div>
              <span
                className={cn(
                  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
                  rep.conversion_rate >= 20
                    ? 'bg-green-100 text-green-700'
                    : rep.conversion_rate >= 10
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-red-100 text-red-700'
                )}
              >
                {rep.conversion_rate.toFixed(1)}%
              </span>
            </div>

            {/* Stats Row */}
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-xs text-slate-500">Leads</p>
                <p className="text-sm font-semibold text-slate-800">{rep.total_leads}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Won</p>
                <p className="text-sm font-semibold text-slate-800">{rep.won_deals}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Avg Score</p>
                <p className="text-sm font-semibold text-slate-800">
                  {rep.avg_score.toFixed(0)}
                </p>
              </div>
            </div>

            {/* Conversion Rate Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Conversion</span>
                <span className={cn('font-medium', getConversionColor(rep.conversion_rate))}>
                  {rep.conversion_rate.toFixed(1)}%
                </span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn('h-full rounded-full transition-all', getConversionBgColor(rep.conversion_rate))}
                  style={{ width: `${Math.min(rep.conversion_rate, 100)}%` }}
                />
              </div>
            </div>

            {/* Revenue */}
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3">
              <span className="text-xs text-slate-500">Revenue</span>
              <span className="text-sm font-semibold text-slate-800">
                {formatCurrency(rep.total_value)}
              </span>
            </div>
          </div>
        ))}

        {reps.length === 0 && (
          <div className="col-span-full rounded-lg border border-dashed border-slate-300 p-8 text-center">
            <Users className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">No rep performance data available</p>
          </div>
        )}
      </div>

      {/* Pipeline Funnel */}
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="mb-6 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-600" />
          <h3 className="text-base font-semibold text-slate-900">Pipeline Funnel</h3>
        </div>

        {funnel.length > 0 ? (
          <>
            {/* Visual Funnel Bars */}
            <div className="mb-6 space-y-3">
              {funnel.map((stage, i) => {
                const maxCount = Math.max(...funnel.map((s) => s.count), 1)
                const widthPct = Math.max((stage.count / maxCount) * 100, 8)
                return (
                  <div key={stage.stage} className="flex items-center gap-4">
                    <div className="w-28 text-right">
                      <span className="text-sm font-medium capitalize text-slate-700">
                        {stage.stage}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div
                        className="flex items-center justify-between rounded-lg px-3 py-2 text-white transition-all"
                        style={{
                          width: `${widthPct}%`,
                          backgroundColor: FUNNEL_COLORS[i % FUNNEL_COLORS.length],
                          minWidth: '80px',
                        }}
                      >
                        <span className="text-sm font-semibold">{stage.count}</span>
                        <span className="text-xs opacity-80">
                          {formatCurrency(stage.total_value)}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Recharts Bar Chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnel}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="stage"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v: string) =>
                      v.charAt(0).toUpperCase() + v.slice(1)
                    }
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    }}
                    formatter={(value: number, name: string) => {
                      if (name === 'total_value') return [formatCurrency(value), 'Value']
                      return [value, 'Count']
                    }}
                    labelFormatter={(label: string) =>
                      label.charAt(0).toUpperCase() + label.slice(1)
                    }
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {funnel.map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <div className="py-12 text-center">
            <BarChart3 className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">No pipeline data available</p>
          </div>
        )}
      </div>

      {/* Stale Leads Alert */}
      <div className="rounded-xl border border-orange-200 bg-orange-50/30 p-6">
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-600" />
          <h3 className="text-base font-semibold text-slate-900">Stale Leads</h3>
          <span className="ml-2 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
            {staleLeads.length} leads
          </span>
        </div>

        {staleLeads.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-orange-200/50">
                  <th className="pb-2 text-left font-medium text-slate-600">Company</th>
                  <th className="pb-2 text-left font-medium text-slate-600">Rep</th>
                  <th className="pb-2 text-center font-medium text-slate-600">
                    Days Inactive
                  </th>
                  <th className="pb-2 text-right font-medium text-slate-600">
                    Deal Value
                  </th>
                  <th className="pb-2 text-right font-medium text-slate-600">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-orange-100">
                {staleLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-orange-50">
                    <td className="py-3 font-medium text-slate-800">
                      {lead.company_name}
                    </td>
                    <td className="py-3 text-slate-600">{lead.assigned_rep_name}</td>
                    <td className="py-3 text-center">
                      <span
                        className={cn(
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                          lead.days_stale >= 14
                            ? 'bg-red-100 text-red-700'
                            : 'bg-orange-100 text-orange-700'
                        )}
                      >
                        <Clock className="h-3 w-3" />
                        {lead.days_stale}d
                      </span>
                    </td>
                    <td className="py-3 text-right font-medium text-slate-800">
                      {formatCurrency(lead.deal_value)}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleNudge(lead.id)}
                        disabled={nudgingId === lead.id}
                        className={cn(
                          'inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                          nudgingId === lead.id
                            ? 'bg-green-100 text-green-700'
                            : 'bg-orange-600 text-white hover:bg-orange-700'
                        )}
                      >
                        {nudgingId === lead.id ? (
                          'Nudged!'
                        ) : (
                          <>
                            <Send className="h-3 w-3" />
                            Nudge Rep
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center">
            <Target className="mx-auto h-8 w-8 text-green-500" />
            <p className="mt-2 text-sm text-green-700">
              No stale leads! All leads have recent activity.
            </p>
          </div>
        )}
      </div>

      {/* Team Leaderboard */}
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="mb-4 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <h3 className="text-base font-semibold text-slate-900">Team Leaderboard</h3>
        </div>

        {sortedReps.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="pb-3 text-left font-medium text-slate-500">Rank</th>
                  <th className="pb-3 text-left font-medium text-slate-500">Rep Name</th>
                  <th className="pb-3 text-center font-medium text-slate-500">Won Deals</th>
                  <th className="pb-3 text-right font-medium text-slate-500">Revenue</th>
                  <th className="pb-3 text-right font-medium text-slate-500">
                    Conversion %
                  </th>
                  <th className="pb-3 text-right font-medium text-slate-500">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sortedReps.map((rep, index) => (
                  <tr
                    key={rep.rep_id}
                    className={cn(
                      'transition-colors hover:bg-slate-50',
                      index < 3 && 'bg-yellow-50/30'
                    )}
                  >
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        {getRankIcon(index)}
                      </div>
                    </td>
                    <td className="py-3">
                      <span className="font-medium text-slate-800">{rep.rep_name}</span>
                    </td>
                    <td className="py-3 text-center">
                      <span className="inline-flex items-center gap-1 text-slate-700">
                        <TrendingUp className="h-3.5 w-3.5 text-green-500" />
                        {rep.won_deals}
                      </span>
                    </td>
                    <td className="py-3 text-right font-medium text-slate-800">
                      {formatCurrency(rep.total_value)}
                    </td>
                    <td className="py-3 text-right">
                      <span
                        className={cn(
                          'font-semibold',
                          getConversionColor(rep.conversion_rate)
                        )}
                      >
                        {rep.conversion_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
                        {rep.avg_score.toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center">
            <Trophy className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">No performance data available yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
