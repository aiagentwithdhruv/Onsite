'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Users,
  ArrowUpDown,
} from 'lucide-react'
import { getLeads } from '@/lib/api'
import { formatCurrency, formatRelative, getStageColor } from '@/lib/utils'
import type { Lead } from '@/lib/types'
import ScoreBadge from '@/components/ui/ScoreBadge'

const STAGES = ['All', 'new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
const SORT_OPTIONS = [
  { label: 'Score (High-Low)', value: 'score' },
  { label: 'Deal Value', value: 'deal_value' },
  { label: 'Last Activity', value: 'last_activity' },
  { label: 'Created', value: 'created_at' },
]
const PAGE_SIZE = 20

export default function LeadsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [leads, setLeads] = useState<Lead[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stageFilter, setStageFilter] = useState(searchParams?.get('stage') || 'All')
  const [sortBy, setSortBy] = useState(searchParams?.get('sort') || 'score')
  const [searchQuery, setSearchQuery] = useState(searchParams?.get('search') || '')
  const [page, setPage] = useState(Number(searchParams?.get('page')) || 1)

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        sort_by: sortBy,
        per_page: PAGE_SIZE.toString(),
        page: page.toString(),
      }
      if (stageFilter !== 'All') params.stage_filter = stageFilter
      if (searchQuery.trim()) params.search = searchQuery.trim()

      const res = await getLeads(params)
      const data = res.data as { leads?: Lead[]; total?: number; total_pages?: number }
      const list = data?.leads || []
      setLeads(list)
      setTotalCount(data?.total ?? list.length)
      setTotalPages(Math.max(1, data?.total_pages ?? 1))

      const next = new URLSearchParams(searchParams?.toString() || '')
      if (stageFilter !== 'All') next.set('stage', stageFilter)
      else next.delete('stage')
      if (sortBy !== 'score') next.set('sort', sortBy)
      else next.delete('sort')
      if (searchQuery) next.set('search', searchQuery)
      else next.delete('search')
      if (page > 1) next.set('page', page.toString())
      else next.delete('page')
      router.replace(`/leads?${next.toString()}`, { scroll: false })
    } catch (err) {
      console.error('Failed to fetch leads:', err)
      setError('Failed to load leads')
    } finally {
      setLoading(false)
    }
  }, [stageFilter, sortBy, searchQuery, page, router, searchParams])

  useEffect(() => {
    fetchLeads()
  }, [fetchLeads])

  useEffect(() => {
    const t = setTimeout(() => {
      if (page !== 1) setPage(1)
      else fetchLeads()
    }, 400)
    return () => clearTimeout(t)
  }, [searchQuery])

  const companyName = (l: Lead) => (l as Lead & { company_name?: string }).company_name || l.company

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Leads</h2>
          <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
            {totalCount} total lead{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900/50">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[200px] flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search company or contact..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 bg-zinc-50 py-2 pl-9 pr-3 text-sm text-zinc-800 placeholder:text-zinc-400 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <Filter className="h-4 w-4 text-zinc-400" />
            <select
              value={stageFilter}
              onChange={(e) => {
                setStageFilter(e.target.value)
                setPage(1)
              }}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-amber-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? 'All Stages' : s}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="h-4 w-4 text-zinc-400" />
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value)
                setPage(1)
              }}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-amber-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-800/50" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <p className="mb-3 text-zinc-500 dark:text-zinc-400">{error}</p>
          <button onClick={fetchLeads} className="text-sm font-medium text-amber-600 hover:text-amber-500">
            Retry
          </button>
        </div>
      ) : leads.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-16 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
          <Users className="mx-auto mb-4 h-16 w-16 text-zinc-200 dark:text-zinc-600" />
          <h3 className="mb-1 text-lg font-medium text-zinc-700 dark:text-zinc-300">No leads found</h3>
          <p className="text-sm text-zinc-400 dark:text-zinc-500">
            {searchQuery ? `No results for "${searchQuery}".` : 'Adjust filters or add new leads.'}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900/50">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-100 bg-zinc-50/80 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:border-zinc-800 dark:bg-zinc-800/50 dark:text-zinc-400">
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Stage</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Deal Value</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Last Activity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-white/5"
                    onClick={() => router.push(`/leads/${lead.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-zinc-900 dark:text-white">{companyName(lead)}</div>
                      {lead.industry && (
                        <div className="mt-0.5 text-xs text-zinc-400 dark:text-zinc-500">{lead.industry}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-zinc-700 dark:text-zinc-300">{lead.contact_name}</div>
                      {lead.email && (
                        <div className="mt-0.5 text-xs text-zinc-400 dark:text-zinc-500">{lead.email}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${getStageColor(lead.stage)}`}
                      >
                        {lead.stage?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={lead.score ?? lead.score_numeric} size="sm" />
                    </td>
                    <td className="px-4 py-3 font-medium text-zinc-700 dark:text-zinc-300">
                      {formatCurrency(lead.deal_value || 0)}
                    </td>
                    <td className="px-4 py-3 capitalize text-zinc-500 dark:text-zinc-400">
                      {lead.source?.replace('_', ' ') || '–'}
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500 dark:text-zinc-400">
                      {lead.last_activity_at ? formatRelative(lead.last_activity_at) : '–'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-zinc-100 px-4 py-3 dark:border-zinc-800">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                {(page - 1) * PAGE_SIZE + 1} – {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const pageNum =
                    totalPages <= 5 ? i + 1 : page <= 3 ? i + 1 : page >= totalPages - 2 ? totalPages - 4 + i : page - 2 + i
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`inline-flex h-8 w-8 items-center justify-center rounded-lg text-sm font-medium transition-colors ${
                        page === pageNum
                          ? 'bg-amber-500 text-zinc-900'
                          : 'border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
