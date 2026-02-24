'use client'

import { useEffect, useState, useRef } from 'react'
import { FileText, Lightbulb, Calendar, Loader2 } from 'lucide-react'
import { getTodayBrief, getBriefHistory } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { DailyBrief } from '@/lib/types'
import { useAuth } from '@/contexts/AuthContext'

export default function BriefsPage() {
  const { session, loading: authLoading } = useAuth()
  const [todayBrief, setTodayBrief] = useState<DailyBrief | null>(null)
  const [history, setHistory] = useState<DailyBrief[]>([])
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
        const [todayRes, historyRes] = await Promise.all([getTodayBrief(), getBriefHistory()])
        const todayData = todayRes.data as { brief?: DailyBrief } | null
        setTodayBrief(todayData?.brief ?? null)
        const histData = historyRes.data as { briefs?: DailyBrief[] } | DailyBrief[]
        setHistory(Array.isArray(histData) ? histData : histData?.briefs ?? [])
      } catch {
        setError('Failed to load briefs')
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

  const rawContent = todayBrief?.brief_content ?? (todayBrief as { content?: unknown })?.content
  const content = typeof rawContent === 'string' ? rawContent : null

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white sm:text-3xl">Daily Briefs</h2>
        <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
          Your AI-generated morning briefs and history
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10">
            <Lightbulb className="h-5 w-5 text-amber-500" />
          </span>
          <h3 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-white">Today&apos;s Brief</h3>
        </div>
        {content ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
            {content}
          </p>
        ) : (
          <p className="py-6 text-center text-sm text-zinc-400 dark:text-zinc-500">
            No brief generated for today. Briefs are created each morning.
          </p>
        )}
      </div>

      <div className="overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
        <div className="flex items-center gap-3 border-b border-zinc-100 px-6 py-4 dark:border-zinc-800">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
            <Calendar className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </span>
          <h3 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-white">Brief History</h3>
        </div>
        {history.length === 0 ? (
          <div className="flex items-center gap-3 px-6 py-8 text-sm text-zinc-500 dark:text-zinc-400">
            <FileText className="h-10 w-10 shrink-0 text-zinc-300 dark:text-zinc-600" />
            No past briefs
          </div>
        ) : (
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {history.slice(0, 14).map((b) => (
              <li key={b.id} className="px-6 py-4">
                <div className="flex items-center justify-between gap-4">
                  <span className="font-medium text-zinc-900 dark:text-white">
                    {formatDate(b.brief_date)}
                  </span>
                  {b.lead_count != null && (
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {b.lead_count} leads
                    </span>
                  )}
                </div>
                {(typeof b.brief_content === 'string' || (b as unknown as Record<string, unknown>).content != null) ? (
                  <p className="mt-1 line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
                    {typeof b.brief_content === 'string' ? b.brief_content : String((b as unknown as Record<string, unknown>).content ?? '')}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
