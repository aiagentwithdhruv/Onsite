import { useState, useEffect } from 'react'
import {
  FileText,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Star,
  Lightbulb,
  CheckSquare,
  Calendar,
  User,
  Hash,
  RefreshCw,
} from 'lucide-react'
import { getTodayBrief, getBriefHistory, getRepBrief, getUsers } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import type { DailyBrief, User as UserType } from '../lib/types'
import { formatDate, cn } from '../lib/utils'

interface BriefContent {
  priority_leads?: Array<{
    name: string
    score: number
    reason?: string
  }>
  key_insights?: string[]
  suggested_actions?: string[]
  summary?: string
}

export default function BriefsPage() {
  const { user } = useAuth()
  const [todayBrief, setTodayBrief] = useState<DailyBrief | null>(null)
  const [history, setHistory] = useState<DailyBrief[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  // Manager-only: view other reps' briefs
  const isManager = user?.role === 'manager' || user?.role === 'founder' || user?.role === 'admin'
  const [reps, setReps] = useState<UserType[]>([])
  const [selectedRepId, setSelectedRepId] = useState<string>('')
  const [repBrief, setRepBrief] = useState<DailyBrief | null>(null)
  const [loadingRepBrief, setLoadingRepBrief] = useState(false)

  useEffect(() => {
    fetchBriefs()
    if (isManager) {
      fetchReps()
    }
  }, [])

  async function fetchBriefs() {
    try {
      setLoading(true)
      setError(null)
      const [todayRes, historyRes] = await Promise.all([
        getTodayBrief(),
        getBriefHistory(),
      ])

      setTodayBrief(todayRes.data?.data || todayRes.data || null)
      setHistory(historyRes.data?.data || historyRes.data || [])
    } catch (err) {
      setError('Failed to load briefs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function fetchReps() {
    try {
      const res = await getUsers()
      const users: UserType[] = res.data?.data || res.data || []
      setReps(users.filter((u) => u.role === 'rep' || u.role === 'team_lead'))
    } catch (err) {
      console.error('Failed to load reps:', err)
    }
  }

  async function handleRepSelect(repId: string) {
    setSelectedRepId(repId)
    if (!repId) {
      setRepBrief(null)
      return
    }
    try {
      setLoadingRepBrief(true)
      const res = await getRepBrief(repId)
      setRepBrief(res.data?.data || res.data || null)
    } catch (err) {
      console.error('Failed to load rep brief:', err)
      setRepBrief(null)
    } finally {
      setLoadingRepBrief(false)
    }
  }

  function toggleExpand(id: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  function parseBriefContent(brief: DailyBrief): BriefContent {
    const content = brief.content as BriefContent
    return {
      priority_leads: content?.priority_leads || [],
      key_insights: content?.key_insights || [],
      suggested_actions: content?.suggested_actions || [],
      summary: content?.summary || '',
    }
  }

  function renderBriefCard(brief: DailyBrief, isToday: boolean = false) {
    const content = parseBriefContent(brief)

    return (
      <div
        className={cn(
          'rounded-xl border bg-white p-6',
          isToday ? 'border-blue-200 shadow-md' : 'border-slate-200'
        )}
      >
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-lg',
                isToday ? 'bg-blue-100' : 'bg-slate-100'
              )}
            >
              <FileText
                className={cn('h-5 w-5', isToday ? 'text-blue-600' : 'text-slate-500')}
              />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                {isToday ? "Today's Brief" : `Brief - ${formatDate(brief.brief_date)}`}
              </h3>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                <Calendar className="h-3 w-3" />
                <span>{formatDate(brief.brief_date)}</span>
              </div>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
            <Hash className="h-3 w-3" />
            {brief.lead_count} leads
          </span>
        </div>

        {/* Summary */}
        {content.summary && (
          <p className="mb-5 text-sm leading-relaxed text-slate-600">{content.summary}</p>
        )}

        {/* Priority Leads */}
        {content.priority_leads && content.priority_leads.length > 0 && (
          <div className="mb-5">
            <div className="mb-2.5 flex items-center gap-2">
              <Star className="h-4 w-4 text-amber-500" />
              <h4 className="text-sm font-semibold text-slate-800">Priority Leads</h4>
            </div>
            <ol className="space-y-2 pl-1">
              {content.priority_leads.map((lead, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50/50 p-3"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-800">{lead.name}</span>
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-xs font-semibold',
                          lead.score >= 80
                            ? 'bg-green-100 text-green-700'
                            : lead.score >= 60
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-orange-100 text-orange-700'
                        )}
                      >
                        {lead.score}
                      </span>
                    </div>
                    {lead.reason && (
                      <p className="mt-0.5 text-xs text-slate-500">{lead.reason}</p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Key Insights */}
        {content.key_insights && content.key_insights.length > 0 && (
          <div className="mb-5">
            <div className="mb-2.5 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-purple-500" />
              <h4 className="text-sm font-semibold text-slate-800">Key Insights</h4>
            </div>
            <ul className="space-y-1.5 pl-1">
              {content.key_insights.map((insight, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400" />
                  {insight}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggested Actions */}
        {content.suggested_actions && content.suggested_actions.length > 0 && (
          <div>
            <div className="mb-2.5 flex items-center gap-2">
              <CheckSquare className="h-4 w-4 text-green-500" />
              <h4 className="text-sm font-semibold text-slate-800">Suggested Actions</h4>
            </div>
            <ul className="space-y-2 pl-1">
              {content.suggested_actions.map((action, i) => (
                <li key={i} className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-600">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Fallback if content is empty */}
        {!content.summary &&
          (!content.priority_leads || content.priority_leads.length === 0) &&
          (!content.key_insights || content.key_insights.length === 0) &&
          (!content.suggested_actions || content.suggested_actions.length === 0) && (
            <div className="rounded-lg bg-slate-50 p-4">
              <pre className="whitespace-pre-wrap text-xs text-slate-600">
                {JSON.stringify(brief.content, null, 2)}
              </pre>
            </div>
          )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600" />
          <p className="mt-3 text-slate-600">Loading your briefs...</p>
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
            onClick={fetchBriefs}
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
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Daily Briefs</h1>
          <p className="mt-1 text-sm text-slate-500">
            AI-generated daily action plans and priority leads
          </p>
        </div>
        <button
          onClick={fetchBriefs}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Manager: Rep Selector */}
      {isManager && reps.length > 0 && (
        <div className="rounded-xl border border-blue-100 bg-blue-50/30 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-slate-700">View rep brief:</span>
            </div>
            <select
              value={selectedRepId}
              onChange={(e) => handleRepSelect(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">-- My Brief --</option>
              {reps.map((rep) => (
                <option key={rep.id} value={rep.id}>
                  {rep.full_name} ({rep.role})
                </option>
              ))}
            </select>
            {loadingRepBrief && (
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            )}
          </div>

          {/* Selected rep's brief */}
          {selectedRepId && !loadingRepBrief && repBrief && (
            <div className="mt-4">{renderBriefCard(repBrief)}</div>
          )}
          {selectedRepId && !loadingRepBrief && !repBrief && (
            <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center">
              <FileText className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-2 text-sm text-slate-500">
                No brief available for this rep today
              </p>
            </div>
          )}
        </div>
      )}

      {/* Today's Brief */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Today&apos;s Brief</h2>
        {todayBrief ? (
          renderBriefCard(todayBrief, true)
        ) : (
          <div className="rounded-xl border border-dashed border-blue-200 bg-blue-50/30 p-10 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-100">
              <Loader2 className="h-7 w-7 animate-spin text-blue-600" />
            </div>
            <h3 className="mt-4 text-base font-semibold text-slate-800">
              Your daily brief is being generated...
            </h3>
            <p className="mt-1 text-sm text-slate-500">
              AI is analyzing your leads and preparing your personalized action plan.
              Check back shortly.
            </p>
          </div>
        )}
      </div>

      {/* Brief History */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Brief History</h2>

        {history.length > 0 ? (
          <div className="space-y-2">
            {history.map((brief) => {
              const isExpanded = expandedIds.has(brief.id)
              return (
                <div
                  key={brief.id}
                  className="rounded-xl border border-slate-200 bg-white transition-shadow hover:shadow-sm"
                >
                  {/* Accordion Header */}
                  <button
                    onClick={() => toggleExpand(brief.id)}
                    className="flex w-full items-center justify-between p-4 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
                        <FileText className="h-4 w-4 text-slate-500" />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-slate-800">
                          {formatDate(brief.brief_date)}
                        </span>
                        <span className="ml-2 inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          {brief.lead_count} leads
                        </span>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="h-5 w-5 text-slate-400" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    )}
                  </button>

                  {/* Accordion Content */}
                  {isExpanded && (
                    <div className="border-t border-slate-100 px-4 pb-4 pt-2">
                      {renderBriefCard(brief)}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center">
            <Calendar className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">No past briefs available yet</p>
            <p className="mt-1 text-xs text-slate-400">
              Briefs are generated daily based on your lead activity
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
