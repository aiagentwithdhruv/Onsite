import { useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  TrendingUp,
  IndianRupee,
  Users,
  Target,
  Loader2,
  AlertTriangle,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Medal,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import {
  getRepPerformance,
  getPipelineFunnel,
  getSourceAnalysis,
  getConversionTrends,
} from '../lib/api'
import type { RepPerformance, PipelineFunnel, SourceAnalysis } from '../lib/types'
import { formatCurrency, cn } from '../lib/utils'

const CHART_COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#0891b2']

const STAGE_COLORS: Record<string, string> = {
  new: '#2563eb',
  contacted: '#7c3aed',
  qualified: '#db2777',
  proposal: '#ea580c',
  negotiation: '#16a34a',
  won: '#0891b2',
}

type DateRange = 'week' | 'month' | 'quarter' | 'custom'

interface ConversionTrend {
  period: string
  conversion_rate: number
  leads: number
  won: number
}

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange>('month')
  const [reps, setReps] = useState<RepPerformance[]>([])
  const [funnel, setFunnel] = useState<PipelineFunnel[]>([])
  const [sources, setSources] = useState<SourceAnalysis[]>([])
  const [trends, setTrends] = useState<ConversionTrend[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const dateRangeParam = useCallback((): Record<string, string> => {
    const now = new Date()
    let startDate: Date

    switch (dateRange) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 86400000)
        break
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1)
        break
      case 'quarter':
        startDate = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1)
        break
      default:
        startDate = new Date(now.getFullYear(), now.getMonth(), 1)
    }

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: now.toISOString().split('T')[0],
    }
  }, [dateRange])

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params = dateRangeParam()
      const [repRes, funnelRes, sourceRes, trendRes] = await Promise.all([
        getRepPerformance(params),
        getPipelineFunnel(params),
        getSourceAnalysis(params),
        getConversionTrends(params),
      ])

      setReps(repRes.data?.data || repRes.data || [])
      setFunnel(funnelRes.data?.data || funnelRes.data || [])
      setSources(sourceRes.data?.data || sourceRes.data || [])
      setTrends(trendRes.data?.data || trendRes.data || [])
    } catch (err) {
      setError('Failed to load analytics data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [dateRangeParam])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Compute KPIs
  const totalPipelineValue = funnel.reduce((sum, s) => sum + s.total_value, 0)
  const totalLeads = funnel.reduce((sum, s) => sum + s.count, 0)
  const wonStage = funnel.find((s) => s.stage === 'won')
  const winRate = totalLeads > 0 ? ((wonStage?.count || 0) / totalLeads) * 100 : 0
  const avgDealSize =
    wonStage && wonStage.count > 0
      ? wonStage.total_value / wonStage.count
      : totalLeads > 0
      ? totalPipelineValue / totalLeads
      : 0

  const sortedReps = [...reps].sort((a, b) => b.conversion_rate - a.conversion_rate)
  const sortedSources = [...sources].sort((a, b) => b.conversion_rate - a.conversion_rate)

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600" />
          <p className="mt-3 text-slate-600">Loading analytics...</p>
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
            onClick={fetchData}
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
      {/* Header + Date Range */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
          <p className="mt-1 text-sm text-slate-500">
            Pipeline performance and conversion insights
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {(
            [
              { key: 'week', label: 'This Week' },
              { key: 'month', label: 'This Month' },
              { key: 'quarter', label: 'This Quarter' },
            ] as { key: DateRange; label: string }[]
          ).map((item) => (
            <button
              key={item.key}
              onClick={() => setDateRange(item.key)}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                dateRange === item.key
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              )}
            >
              {item.label}
            </button>
          ))}
          <button
            onClick={() => setDateRange('custom')}
            className={cn(
              'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              dateRange === 'custom'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            )}
          >
            <Calendar className="h-3.5 w-3.5" />
            Custom
          </button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Pipeline Value */}
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Total Pipeline Value</span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
              <IndianRupee className="h-4 w-4 text-blue-600" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {formatCurrency(totalPipelineValue)}
          </p>
          <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
            <ArrowUpRight className="h-3.5 w-3.5" />
            <span>Across {funnel.length} stages</span>
          </div>
        </div>

        {/* Win Rate */}
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Win Rate</span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-50">
              <Target className="h-4 w-4 text-green-600" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{winRate.toFixed(1)}%</p>
          <div
            className={cn(
              'mt-1 flex items-center gap-1 text-xs',
              winRate >= 15 ? 'text-green-600' : 'text-red-600'
            )}
          >
            {winRate >= 15 ? (
              <ArrowUpRight className="h-3.5 w-3.5" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5" />
            )}
            <span>
              {wonStage?.count || 0} won of {totalLeads}
            </span>
          </div>
        </div>

        {/* Avg Deal Size */}
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Avg Deal Size</span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-50">
              <BarChart3 className="h-4 w-4 text-purple-600" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {formatCurrency(avgDealSize)}
          </p>
          <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
            <span>Per deal average</span>
          </div>
        </div>

        {/* Leads This Period */}
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Leads This Month</span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50">
              <Users className="h-4 w-4 text-amber-600" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{totalLeads}</p>
          <div className="mt-1 flex items-center gap-1 text-xs text-blue-600">
            <TrendingUp className="h-3.5 w-3.5" />
            <span>{sources.length} sources</span>
          </div>
        </div>
      </div>

      {/* Row 2: Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pipeline Funnel Bar Chart */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="mb-4 text-base font-semibold text-slate-900">Pipeline Funnel</h3>
          {funnel.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnel}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="stage"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)}
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                      fontSize: '13px',
                    }}
                    formatter={(value: number, name: string) => {
                      if (name === 'total_value') return [formatCurrency(value), 'Total Value']
                      return [value, 'Lead Count']
                    }}
                    labelFormatter={(label: string) =>
                      label.charAt(0).toUpperCase() + label.slice(1)
                    }
                  />
                  <Legend />
                  <Bar dataKey="count" name="Lead Count" radius={[4, 4, 0, 0]}>
                    {funnel.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          STAGE_COLORS[entry.stage] ||
                          CHART_COLORS[index % CHART_COLORS.length]
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-80 items-center justify-center">
              <p className="text-sm text-slate-500">No pipeline data available</p>
            </div>
          )}
        </div>

        {/* Conversion Trends Line Chart */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="mb-4 text-base font-semibold text-slate-900">Conversion Trends</h3>
          {trends.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends}>
                  <defs>
                    <linearGradient id="convGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                      fontSize: '13px',
                    }}
                    formatter={(value: number) => [
                      `${value.toFixed(1)}%`,
                      'Conversion Rate',
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="conversion_rate"
                    stroke="#2563eb"
                    strokeWidth={2}
                    fill="url(#convGradient)"
                    dot={{ r: 4, fill: '#2563eb' }}
                    activeDot={{ r: 6 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-80 items-center justify-center">
              <p className="text-sm text-slate-500">No trend data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Row 3: Tables */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Rep Leaderboard */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="mb-4 flex items-center gap-2">
            <Medal className="h-5 w-5 text-yellow-500" />
            <h3 className="text-base font-semibold text-slate-900">Rep Leaderboard</h3>
          </div>

          {sortedReps.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="pb-2.5 text-left font-medium text-slate-500">#</th>
                    <th className="pb-2.5 text-left font-medium text-slate-500">Name</th>
                    <th className="pb-2.5 text-center font-medium text-slate-500">Leads</th>
                    <th className="pb-2.5 text-center font-medium text-slate-500">Won</th>
                    <th className="pb-2.5 text-right font-medium text-slate-500">Revenue</th>
                    <th className="pb-2.5 text-right font-medium text-slate-500">Conv. %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sortedReps.map((rep, i) => (
                    <tr key={rep.rep_id} className="hover:bg-slate-50">
                      <td className="py-2.5">
                        {i < 3 ? (
                          <Medal
                            className={cn(
                              'h-4 w-4',
                              i === 0
                                ? 'text-yellow-500'
                                : i === 1
                                ? 'text-gray-400'
                                : 'text-amber-700'
                            )}
                          />
                        ) : (
                          <span className="text-xs text-slate-500">{i + 1}</span>
                        )}
                      </td>
                      <td className="py-2.5 font-medium text-slate-800">{rep.rep_name}</td>
                      <td className="py-2.5 text-center text-slate-600">{rep.total_leads}</td>
                      <td className="py-2.5 text-center text-slate-600">{rep.won_deals}</td>
                      <td className="py-2.5 text-right font-medium text-slate-800">
                        {formatCurrency(rep.total_value)}
                      </td>
                      <td className="py-2.5 text-right">
                        <span
                          className={cn(
                            'font-semibold',
                            rep.conversion_rate >= 20
                              ? 'text-green-600'
                              : rep.conversion_rate >= 10
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          )}
                        >
                          {rep.conversion_rate.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-slate-500">
              No rep data available
            </div>
          )}
        </div>

        {/* Source Analysis */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <h3 className="text-base font-semibold text-slate-900">Source Analysis</h3>
          </div>

          {sortedSources.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="pb-2.5 text-left font-medium text-slate-500">Source</th>
                    <th className="pb-2.5 text-center font-medium text-slate-500">Leads</th>
                    <th className="pb-2.5 text-center font-medium text-slate-500">Won</th>
                    <th className="pb-2.5 text-right font-medium text-slate-500">Revenue</th>
                    <th className="pb-2.5 text-right font-medium text-slate-500">Conv. %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sortedSources.map((source, i) => {
                    const isBest = i === 0 && sortedSources.length > 1
                    const isWorst = i === sortedSources.length - 1 && sortedSources.length > 1
                    return (
                      <tr
                        key={source.source}
                        className={cn(
                          'hover:bg-slate-50',
                          isBest && 'bg-green-50/50',
                          isWorst && 'bg-red-50/30'
                        )}
                      >
                        <td className="py-2.5">
                          <div className="flex items-center gap-2">
                            <span className="font-medium capitalize text-slate-800">
                              {source.source}
                            </span>
                            {isBest && (
                              <span className="rounded-full bg-green-100 px-1.5 py-0.5 text-[10px] font-semibold text-green-700">
                                BEST
                              </span>
                            )}
                            {isWorst && (
                              <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">
                                LOW
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2.5 text-center text-slate-600">
                          {source.lead_count}
                        </td>
                        <td className="py-2.5 text-center text-slate-600">
                          {source.won_count}
                        </td>
                        <td className="py-2.5 text-right font-medium text-slate-800">
                          {formatCurrency(source.total_value)}
                        </td>
                        <td className="py-2.5 text-right">
                          <span
                            className={cn(
                              'font-semibold',
                              source.conversion_rate >= 20
                                ? 'text-green-600'
                                : source.conversion_rate >= 10
                                ? 'text-yellow-600'
                                : 'text-red-600'
                            )}
                          >
                            {source.conversion_rate.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-slate-500">
              No source data available
            </div>
          )}
        </div>
      </div>

      {/* Row 4: Source Performance Pie Chart */}
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h3 className="mb-4 text-base font-semibold text-slate-900">
          Lead Distribution by Source
        </h3>

        {sources.length > 0 ? (
          <div className="flex flex-col items-center gap-6 lg:flex-row">
            <div className="h-80 w-full lg:w-1/2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sources}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={120}
                    paddingAngle={3}
                    dataKey="lead_count"
                    nameKey="source"
                    label={({
                      source,
                      percent,
                    }: {
                      source: string
                      percent: number
                    }) => `${source} ${(percent * 100).toFixed(0)}%`}
                  >
                    {sources.map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      fontSize: '13px',
                    }}
                    formatter={(value: number, name: string) => [
                      `${value} leads`,
                      name.charAt(0).toUpperCase() + name.slice(1),
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Source stats summary */}
            <div className="w-full space-y-3 lg:w-1/2">
              {sources.map((source, index) => {
                const totalLeadCount = sources.reduce((s, src) => s + src.lead_count, 0)
                const pct =
                  totalLeadCount > 0
                    ? ((source.lead_count / totalLeadCount) * 100).toFixed(1)
                    : '0'
                return (
                  <div
                    key={source.source}
                    className="flex items-center gap-3 rounded-lg border border-slate-100 p-3"
                  >
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{
                        backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                      }}
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium capitalize text-slate-800">
                        {source.source}
                      </p>
                      <p className="text-xs text-slate-500">
                        {source.lead_count} leads &middot; {pct}% of total
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-800">
                        {formatCurrency(source.total_value)}
                      </p>
                      <p
                        className={cn(
                          'text-xs font-medium',
                          source.conversion_rate >= 20
                            ? 'text-green-600'
                            : source.conversion_rate >= 10
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        )}
                      >
                        {source.conversion_rate.toFixed(1)}% conv.
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <p className="text-sm text-slate-500">No source data available</p>
          </div>
        )}
      </div>
    </div>
  )
}
