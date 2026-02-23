'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Phone, Mail, Building2, Loader2, Search } from 'lucide-react'
import { getLeadDetail, performLeadAction, triggerResearch } from '@/lib/api'
import { formatCurrency, formatDate, getStageColor } from '@/lib/utils'
import type { LeadDetail as LeadDetailType } from '@/lib/types'
import ScoreBadge from '@/components/ui/ScoreBadge'

export default function LeadDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const [lead, setLead] = useState<LeadDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [researchLoading, setResearchLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    async function fetchLead() {
      try {
        setLoading(true)
        const res = await getLeadDetail(id)
        setLead((res.data as { lead: LeadDetailType })?.lead ?? null)
      } catch (err) {
        console.error(err)
        setError('Failed to load lead')
      } finally {
        setLoading(false)
      }
    }
    fetchLead()
  }, [id])

  async function handleAction(action: string) {
    if (!id) return
    setActionLoading(action)
    try {
      await performLeadAction(id, action)
      const res = await getLeadDetail(id)
      setLead((res.data as { lead: LeadDetailType })?.lead ?? null)
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleResearch() {
    if (!id) return
    setResearchLoading(true)
    try {
      await triggerResearch(id)
      const res = await getLeadDetail(id)
      setLead((res.data as { lead: LeadDetailType })?.lead ?? null)
    } catch (err) {
      console.error(err)
    } finally {
      setResearchLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-violet-500" />
      </div>
    )
  }

  if (error || !lead) {
    return (
      <div className="text-center">
        <p className="text-zinc-500 dark:text-zinc-400">{error || 'Lead not found'}</p>
        <Link href="/leads" className="mt-2 inline-block text-sm font-medium text-violet-600 hover:text-violet-500">
          Back to Leads
        </Link>
      </div>
    )
  }

  const company = (lead as LeadDetailType & { company_name?: string }).company_name || lead.company
  const research = Array.isArray(lead.research) ? lead.research[0] : lead.research

  const actions = [
    { key: 'called', label: 'Called' },
    { key: 'not_reachable', label: 'Not reachable' },
    { key: 'meeting_scheduled', label: 'Meeting scheduled' },
    { key: 'won', label: 'Won' },
    { key: 'lost', label: 'Lost' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">{company || 'Unknown'}</h1>
            <p className="mt-1 text-zinc-500 dark:text-zinc-400">{lead.contact_name}</p>
            <div className="mt-3 flex flex-wrap gap-3">
              <ScoreBadge score={lead.score ?? lead.latest_score?.score ?? lead.score_numeric} size="md" />
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${getStageColor(lead.stage)}`}>
                {lead.stage?.replace('_', ' ')}
              </span>
              {lead.deal_value != null && (
                <span className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                  {formatCurrency(lead.deal_value)}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {actions.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => handleAction(key)}
                disabled={actionLoading === key}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
              >
                {actionLoading === key ? <Loader2 className="inline h-4 w-4 animate-spin" /> : label}
              </button>
            ))}
            <button
              onClick={handleResearch}
              disabled={researchLoading}
              className="glow-btn flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-50"
            >
              {researchLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Research
            </button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 border-t border-zinc-100 pt-6 dark:border-zinc-800 sm:grid-cols-2">
          {lead.email && (
            <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
              <Mail className="h-4 w-4 shrink-0" />
              <a href={`mailto:${lead.email}`} className="hover:text-violet-600 dark:hover:text-violet-400">
                {lead.email}
              </a>
            </div>
          )}
          {lead.phone && (
            <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
              <Phone className="h-4 w-4 shrink-0" />
              <a href={`tel:${lead.phone}`} className="hover:text-violet-600 dark:hover:text-violet-400">
                {lead.phone}
              </a>
            </div>
          )}
          {lead.industry && (
            <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
              <Building2 className="h-4 w-4 shrink-0" />
              {lead.industry}
            </div>
          )}
        </div>
      </div>

      {research && (
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">AI Research</h3>
          {research.close_strategy && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase text-zinc-500 dark:text-zinc-400">Close strategy</p>
              <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{research.close_strategy}</p>
            </div>
          )}
          {research.web_research && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase text-zinc-500 dark:text-zinc-400">Research</p>
              <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{research.web_research}</p>
            </div>
          )}
          {research.talking_points && research.talking_points.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase text-zinc-500 dark:text-zinc-400">Talking points</p>
              <ul className="mt-1 list-inside list-disc text-sm text-zinc-700 dark:text-zinc-300">
                {research.talking_points.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">Activities</h3>
          {lead.activities?.length ? (
            <ul className="mt-3 space-y-2">
              {lead.activities.slice(0, 10).map((a) => (
                <li key={a.id} className="flex justify-between text-sm">
                  <span className="text-zinc-700 dark:text-zinc-300">{a.subject || a.activity_type}</span>
                  <span className="text-zinc-400 dark:text-zinc-500">{formatDate(a.activity_date)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-500">No activities yet</p>
          )}
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">Notes</h3>
          {lead.notes?.length ? (
            <ul className="mt-3 space-y-2">
              {lead.notes.slice(0, 10).map((n) => (
                <li key={n.id} className="text-sm text-zinc-700 dark:text-zinc-300">
                  {n.note_text}
                  {n.note_date && (
                    <span className="ml-2 text-zinc-400 dark:text-zinc-500">{formatDate(n.note_date)}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-500">No notes yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
