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
  Target,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { getLeads, getTodayBrief, getAlerts, getDashboardSummary, getAgentProfiles } from '@/lib/api'
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
  const [actionItems, setActionItems] = useState<{ title: string; description?: string }[]>([])
  const [nextBestAction, setNextBestAction] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function fetchData() {
    setLoading(true)
    setError(null)
    try {
      const [leadsRes, briefRes, alertsRes, summaryRes, agentsRes] = await Promise.allSettled([
        getLeads({ sort_by: 'score', limit: '50' }),
        getTodayBrief(),
        getAlerts({ limit: '3' }),
        getDashboardSummary(),
        getAgentProfiles(),
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
      if (summaryRes.status === 'fulfilled' && summaryRes.value.data) {
        const sum = summaryRes.value.data as { action_items?: { title?: string; description?: string }[] }
        setActionItems((sum.action_items || []).slice(0, 3).map(a => ({ title: a.title || '', description: a.description })))
      }
      if (agentsRes.status === 'fulfilled' && agentsRes.value.data) {
        const profiles = (agentsRes.value.data as { profiles?: { performance?: { next_best_action?: string } }[] })?.profiles ?? []
        if (profiles.length === 1 && profiles[0]?.performance?.next_best_action) setNextBestAction(profiles[0].performance.next_best_action)
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
  const pipelineValue = leads.reduce((sum, l) => sum + (l.deal_value || 0), 0)
  const topLeads = leads.slice(0, 8)
  const brief = briefData?.brief
  const briefContent = brief?.brief_content ?? (typeof brief?.content === 'string' ? brief.content : null)

  const nextThings: { label: string; href?: string }[] = []
  if (briefContent) nextThings.push({ label: 'Read today\'s brief' })
  if (nextBestAction) nextThings.push({ label: nextBestAction })
  actionItems.forEach(a => { if (a.title) nextThings.push({ label: a.title, href: '/intelligence' }) })
  const topNext = nextThings.slice(0, 3)

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="rounded-2xl border border-zinc-200/80 bg-white p-8 text-center shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10">
            <AlertTriangle className="h-7 w-7 text-rose-500" />
          </div>
          <p className="text-zinc-600 dark:text-zinc-400">{error}</p>
          <button
            onClick={() => fetchData()}
            className="mt-4 rounded-xl bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 overflow-hidden">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white sm:text-3xl">
          {getGreeting()}, {firstName}
        </h2>
        <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
          Here&apos;s your sales intelligence for today
        </p>
      </div>

      {topNext.length > 0 && !loading && (
        <div className="rounded-2xl border border-amber-200/80 bg-gradient-to-br from-amber-50 to-orange-50/50 p-5 shadow-sm dark:border-amber-500/20 dark:from-amber-500/5 dark:to-amber-500/10">
          <h3 className="mb-3 flex items-center gap-2.5 text-sm font-semibold tracking-wide text-amber-800 dark:text-amber-200">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/20">
              <Target className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            </span>
            Your next 3 things
          </h3>
          <ol className="space-y-2 text-sm text-amber-800 dark:text-amber-200">
            {topNext.map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-xs font-bold text-amber-700 dark:text-amber-300">{i + 1}</span>
                {item.href ? (
                  <Link href={item.href} className="font-medium text-amber-700 underline decoration-amber-400/50 underline-offset-2 hover:text-amber-600 dark:text-amber-300">
                    {item.label}
                  </Link>
                ) : (
                  <span>{item.label}</span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-2xl border border-zinc-200/80 bg-white/80 dark:border-zinc-700/50 dark:bg-zinc-800/30"
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
            icon={<Flame className="h-5 w-5 text-amber-500" />}
            label="Hot Leads"
            value={hotLeads}
          />
          <StatCard
            icon={<Phone className="h-5 w-5 text-emerald-500" />}
            label="Calls Today"
            value={0}
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
          <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
            <div className="mb-4 flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10">
                <Lightbulb className="h-5 w-5 text-amber-500" />
              </span>
              <h3 className="text-base font-semibold tracking-tight text-zinc-900 dark:text-white">Today&apos;s Brief</h3>
            </div>
            {briefContent ? (
              <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
                {briefContent}
              </p>
            ) : (
              <p className="py-6 text-center text-sm text-zinc-400 dark:text-zinc-500">
                No brief for today
              </p>
            )}
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
            <div className="flex items-center justify-between border-b border-zinc-100 px-6 py-4 dark:border-zinc-800">
              <h3 className="flex items-center gap-3 text-base font-semibold tracking-tight text-zinc-900 dark:text-white">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10">
                  <Phone className="h-4 w-4 text-emerald-500" />
                </span>
                Priority Call List
              </h3>
              <Link
                href="/leads"
                className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-amber-600 transition-colors hover:bg-amber-500/10 hover:text-amber-700 dark:text-amber-400 dark:hover:bg-amber-500/10"
              >
                View all <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            {loading ? (
              <div className="space-y-2 p-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-14 animate-pulse rounded-xl bg-zinc-100/80 dark:bg-zinc-800/40" />
                ))}
              </div>
            ) : topLeads.length === 0 ? (
              <div className="py-12 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800">
                  <Users className="h-6 w-6 text-zinc-400 dark:text-zinc-500" />
                </div>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">No leads yet</p>
              </div>
            ) : (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {topLeads.map((lead, idx) => {
                  const company = (lead as Lead & { company_name?: string }).company_name || lead.company || 'Unknown'
                  return (
                    <Link
                      key={lead.id}
                      href={`/leads/${lead.id}`}
                      className="flex items-center gap-4 px-6 py-3.5 transition-colors hover:bg-zinc-50/80 dark:hover:bg-white/[0.03]"
                    >
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-xs font-semibold text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
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
          <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="flex items-center gap-3 text-base font-semibold tracking-tight text-zinc-900 dark:text-white">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                </span>
                Recent Alerts
              </h3>
              <Link href="/alerts" className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-amber-600 transition-colors hover:bg-amber-500/10 dark:text-amber-400">
                View All
              </Link>
            </div>
            {alerts.length === 0 ? (
              <div className="py-10 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800">
                  <AlertTriangle className="h-6 w-6 text-zinc-300 dark:text-zinc-600" />
                </div>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">No recent alerts</p>
              </div>
            ) : (
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <Link
                    key={alert.id}
                    href={alert.lead_id ? `/leads/${alert.lead_id}` : '/alerts'}
                    className="block rounded-xl border border-zinc-100 p-3.5 transition-colors hover:border-zinc-200 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-white/[0.03]"
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
    <div className="group rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:border-zinc-700/50 dark:bg-zinc-900/40 dark:hover:shadow-lg dark:hover:shadow-black/10">
      <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-100 transition-colors group-hover:bg-zinc-200/80 dark:bg-zinc-800 dark:group-hover:bg-zinc-700/80">
        {icon}
      </div>
      <p className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">{value}</p>
      <p className="mt-1 text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">{label}</p>
    </div>
  )
}
