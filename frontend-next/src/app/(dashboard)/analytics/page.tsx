'use client'

import { useEffect, useState, useRef } from 'react'
import { BarChart3, Users, TrendingUp, Loader2 } from 'lucide-react'
import { getRepPerformance, getPipelineFunnel, getSourceAnalysis } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import type { RepPerformance, PipelineFunnel, SourceAnalysis } from '@/lib/types'
import { useAuth } from '@/contexts/AuthContext'

export default function AnalyticsPage() {
  const { session, loading: authLoading } = useAuth()
  const [repPerf, setRepPerf] = useState<RepPerformance[]>([])
  const [funnel, setFunnel] = useState<PipelineFunnel[]>([])
  const [sources, setSources] = useState<SourceAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
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
        const [repRes, funnelRes, sourceRes] = await Promise.allSettled([
          getRepPerformance(),
          getPipelineFunnel(),
          getSourceAnalysis(),
        ])
        if (repRes.status === 'fulfilled') {
          const data = repRes.value.data as RepPerformance[] | { data?: RepPerformance[] }
          setRepPerf(Array.isArray(data) ? data : data?.data ?? [])
        }
        if (funnelRes.status === 'fulfilled') {
          const data = funnelRes.value.data as PipelineFunnel[] | { data?: PipelineFunnel[] }
          setFunnel(Array.isArray(data) ? data : data?.data ?? [])
        }
        if (sourceRes.status === 'fulfilled') {
          const data = sourceRes.value.data as SourceAnalysis[] | { data?: SourceAnalysis[] }
          setSources(Array.isArray(data) ? data : data?.data ?? [])
        }
      } catch {
        setError('Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [authLoading])

  if (loading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-amber-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
        <p className="text-zinc-500 dark:text-zinc-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Analytics</h2>
        <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
          Pipeline, rep performance, and source analysis
        </p>
      </div>

      {funnel.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
            <BarChart3 className="h-5 w-5 text-amber-500" />
            Pipeline Funnel
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {funnel.map((f) => (
              <div
                key={f.stage}
                className="rounded-lg border border-zinc-100 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-800/30"
              >
                <p className="text-xs font-medium uppercase text-zinc-500 dark:text-zinc-400">
                  {f.stage?.replace('_', ' ')}
                </p>
                <p className="mt-1 text-xl font-bold text-zinc-900 dark:text-white">{f.count}</p>
                {f.total_value != null && (
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {formatCurrency(f.total_value)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {repPerf.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
            <Users className="h-5 w-5 text-amber-500" />
            Rep Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-100 text-left text-xs font-medium uppercase text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
                  <th className="pb-2 pr-4">Rep</th>
                  <th className="pb-2 pr-4">Leads</th>
                  <th className="pb-2 pr-4">Won</th>
                  <th className="pb-2 pr-4">Value</th>
                  <th className="pb-2">Conversion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {repPerf.map((r) => (
                  <tr key={r.user_id || r.rep_id || r.name || ''}>
                    <td className="py-3 pr-4 font-medium text-zinc-900 dark:text-white">
                      {r.rep_name || r.name || '–'}
                    </td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{r.total_leads}</td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">{r.won ?? 0}</td>
                    <td className="py-3 pr-4 text-zinc-600 dark:text-zinc-300">
                      {formatCurrency(r.total_value ?? 0)}
                    </td>
                    <td className="py-3">
                      <span className="font-medium text-emerald-600 dark:text-emerald-400">
                        {((r.conversion_rate ?? 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sources.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
            <TrendingUp className="h-5 w-5 text-amber-500" />
            Source Analysis
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sources.map((s) => (
              <div
                key={s.source}
                className="rounded-lg border border-zinc-100 px-4 py-3 dark:border-zinc-800"
              >
                <p className="font-medium text-zinc-900 dark:text-white">{s.source}</p>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  {(s.total_leads ?? s.lead_count ?? 0)} leads ·{' '}
                  {((s.conversion_rate ?? 0) * 100).toFixed(1)}% conversion
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {funnel.length === 0 && repPerf.length === 0 && sources.length === 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <BarChart3 className="mx-auto mb-3 h-12 w-12 text-zinc-300 dark:text-zinc-600" />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No analytics data yet</p>
        </div>
      )}
    </div>
  )
}
