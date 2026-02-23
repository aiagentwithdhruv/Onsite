'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Users,
  Flame,
  Phone,
  IndianRupee,
  AlertTriangle,
  Lightbulb,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { getLeads, getTodayBrief, getAlerts } from '@/lib/api'
import { formatCurrency, formatRelative, getStageColor, getSeverityColor } from '@/lib/utils'
import type { Lead, Alert } from '@/lib/types'
import ScoreBadge from '@/components/ui/ScoreBadge'

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardHome() {
  const { user } = useAuth()
  const [leads, setLeads] = useState<Lead[]>([])
  const [briefData, setBriefData] = useState<{ brief?: { brief_content?: string; content?: unknown } } | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function fetchData() {
    setLoading(true)
    setError(null)
    try {
      const [leadsRes, briefRes, alertsRes] = await Promise.allSettled([
        getLeads({ sort_by: 'score', limit: '50' }),
        getTodayBrief(),
        getAlerts({ limit: '3' }),
      ])
        if (leadsRes.status === 'fulfilled') {
          const data = leadsRes.value.data as { leads?: Lead[] } | Lead[]
          setLeads(Array.isArray(data) ? data : (data?.leads ?? []))
        }
      if (briefRes.status === 'fulfilled') setBriefData(briefRes.value.data as { brief?: { brief_content?: string } } | null)
      if (alertsRes.status === 'fulfilled') {
        const alertData = (alertsRes.value.data as { alerts?: Alert[] })?.alerts || alertsRes.value.data
        setAlerts(Array.isArray(alertData) ? alertData : [])
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const displayName = user?.full_name || user?.name || user?.email || 'there'
  const firstName = displayName.split(' ')[0]
  const totalLeads = leads.length
  const hotLeads = leads.filter(
    (l) => l.score === 'hot' || (typeof l.score_numeric === 'number' && l.score_numeric >= 80)
  ).length
  const demoPending = leads.filter(
    (l) => l.stage === 'demo' || l.stage === 'proposal' || l.stage === 'meeting_scheduled'
  ).length
  const pipelineValue = leads.reduce((sum, l) => sum + (l.deal_value || 0), 0)
  const topLeads = leads.slice(0, 8)
  const brief = briefData?.brief
  const briefContent = brief?.brief_content ?? (typeof brief?.content === 'string' ? brief.content : null)

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-3 h-12 w-12 text-rose-400" />
          <p className="text-zinc-600 dark:text-zinc-400">{error}</p>
          <button
            onClick={() => fetchData()}
            className="mt-3 text-sm font-medium text-violet-600 hover:text-violet-500"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 overflow-hidden">
      <div>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">
          {getGreeting()}, {firstName}
        </h2>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Here&apos;s your sales intelligence for today
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-xl border border-zinc-200 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-800/50"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            icon={<Users className="h-5 w-5 text-sky-500" />}
            label="My Leads"
            value={totalLeads}
          />
          <StatCard
            icon={<Flame className="h-5 w-5 text-violet-500" />}
            label="Hot Leads"
            value={hotLeads}
          />
          <StatCard
            icon={<Phone className="h-5 w-5 text-emerald-500" />}
            label="Demos Pending"
            value={demoPending}
          />
          <StatCard
            icon={<IndianRupee className="h-5 w-5 text-violet-500" />}
            label="Pipeline Value"
            value={formatCurrency(pipelineValue)}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="glow-card rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-violet-500/10 dark:bg-zinc-900/50">
            <div className="mb-3 flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-violet-500" />
              <h3 className="text-base font-semibold text-zinc-900 dark:text-white">Today&apos;s Brief</h3>
            </div>
            {briefContent ? (
              <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
                {briefContent}
              </p>
            ) : (
              <p className="py-4 text-center text-sm text-zinc-400 dark:text-zinc-500">
                No brief for today
              </p>
            )}
          </div>

          <div className="glow-card overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-violet-500/10 dark:bg-zinc-900/50">
            <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-4 dark:border-zinc-800">
              <h3 className="flex items-center gap-2 text-base font-semibold text-zinc-900 dark:text-white">
                <Phone className="h-5 w-5 text-emerald-500" />
                Priority Call List
              </h3>
              <Link
                href="/leads"
                className="flex items-center gap-0.5 text-xs font-medium text-violet-600 hover:text-violet-500"
              >
                View all <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
            {loading ? (
              <div className="space-y-3 p-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800/50" />
                ))}
              </div>
            ) : topLeads.length === 0 ? (
              <div className="py-10 text-center">
                <Users className="mx-auto mb-2 h-10 w-10 text-zinc-300 dark:text-zinc-600" />
                <p className="text-sm text-zinc-400 dark:text-zinc-500">No leads yet</p>
              </div>
            ) : (
              <div className="divide-y divide-zinc-50 dark:divide-zinc-800">
                {topLeads.map((lead, idx) => {
                  const company = (lead as Lead & { company_name?: string }).company_name || lead.company || 'Unknown'
                  return (
                    <Link
                      key={lead.id}
                      href={`/leads/${lead.id}`}
                      className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-zinc-50 dark:hover:bg-white/5"
                    >
                      <span className="w-5 shrink-0 text-center text-xs font-medium text-zinc-400">
                        {idx + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-zinc-900 dark:text-white">
                          {company}
                        </p>
                        {lead.contact_name && (
                          <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                            {lead.contact_name}
                          </p>
                        )}
                      </div>
                      <ScoreBadge score={lead.score ?? lead.score_numeric} size="sm" />
                      <span className="w-20 shrink-0 text-right text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        {formatCurrency(lead.deal_value || 0)}
                      </span>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize ${getStageColor(lead.stage)}`}
                      >
                        {lead.stage?.replace('_', ' ')}
                      </span>
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-base font-semibold text-zinc-900 dark:text-white">
                <AlertTriangle className="h-5 w-5 text-violet-500" />
                Recent Alerts
              </h3>
              <Link href="/alerts" className="text-xs font-medium text-violet-600 hover:text-violet-500">
                View All
              </Link>
            </div>
            {alerts.length === 0 ? (
              <div className="py-8 text-center">
                <AlertTriangle className="mx-auto mb-2 h-10 w-10 text-zinc-200 dark:text-zinc-600" />
                <p className="text-sm text-zinc-400 dark:text-zinc-500">No recent alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <Link
                    key={alert.id}
                    href={alert.lead_id ? `/leads/${alert.lead_id}` : '/alerts'}
                    className="block rounded-lg border border-zinc-100 p-3 transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-white/5"
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${getSeverityColor(alert.severity || 'low')}`}
                      >
                        {(alert.severity || alert.alert_type || 'info').toString().replace('_', ' ')}
                      </span>
                      <span className="shrink-0 text-[10px] text-zinc-400 dark:text-zinc-500">
                        {formatRelative(alert.created_at || new Date().toISOString())}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
                      {alert.message || alert.title || 'New alert'}
                    </p>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: number | string
}) {
  return (
    <div className="glow-card rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-violet-500/10 dark:bg-zinc-900/50">
      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-500/10">
        {icon}
      </div>
      <p className="text-2xl font-bold text-zinc-900 dark:text-white">{value}</p>
      <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
    </div>
  )
}
