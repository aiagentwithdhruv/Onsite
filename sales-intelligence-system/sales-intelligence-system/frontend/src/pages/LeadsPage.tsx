import { useEffect, useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Users,
  ArrowUpDown,
} from 'lucide-react'
import { getLeads } from '../lib/api'
import {
  formatCurrency,
  formatRelative,
  getStageColor,
} from '../lib/utils'
import type { Lead } from '../lib/types'
import ScoreBadge from '../components/ui/ScoreBadge'
import { TableSkeleton } from '../components/ui/LoadingSkeleton'

const STAGES = ['All', 'New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']
const SOURCES = ['All', 'Website', 'Referral', 'LinkedIn', 'Trade Show', 'Cold Call']
const SORT_OPTIONS = [
  { label: 'Score (High-Low)', value: 'score' },
  { label: 'Deal Value', value: 'deal_value' },
  { label: 'Last Activity', value: 'last_activity' },
  { label: 'Created Date', value: 'created_at' },
]
const PAGE_SIZE = 20

export default function LeadsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [leads, setLeads] = useState<Lead[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter state
  const [stageFilter, setStageFilter] = useState(searchParams.get('stage') || 'All')
  const [sourceFilter, setSourceFilter] = useState(searchParams.get('source') || 'All')
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'score')
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '')
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1)

  useEffect(() => {
    fetchLeads()
  }, [stageFilter, sourceFilter, sortBy, page])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page !== 1) {
        setPage(1)
      } else {
        fetchLeads()
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [searchQuery])

  async function fetchLeads() {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {
        sort_by: sortBy,
        limit: PAGE_SIZE.toString(),
        offset: ((page - 1) * PAGE_SIZE).toString(),
      }
      if (stageFilter !== 'All') params.stage = stageFilter.toLowerCase()
      if (sourceFilter !== 'All') params.source = sourceFilter.toLowerCase().replace(' ', '_')
      if (searchQuery.trim()) params.search = searchQuery.trim()

      const res = await getLeads(params)
      const data = res.data
      const leadsList = data?.leads || (Array.isArray(data) ? data : [])
      setLeads(leadsList)
      setTotalCount(data?.total ?? data?.count ?? leadsList.length)

      // Update URL params
      const newParams = new URLSearchParams()
      if (stageFilter !== 'All') newParams.set('stage', stageFilter)
      if (sourceFilter !== 'All') newParams.set('source', sourceFilter)
      if (sortBy !== 'score') newParams.set('sort', sortBy)
      if (searchQuery) newParams.set('q', searchQuery)
      if (page > 1) newParams.set('page', page.toString())
      setSearchParams(newParams, { replace: true })
    } catch (err) {
      console.error('Failed to fetch leads:', err)
      setError('Failed to load leads')
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  function handleStageChange(value: string) {
    setStageFilter(value)
    setPage(1)
  }

  function handleSourceChange(value: string) {
    setSourceFilter(value)
    setPage(1)
  }

  function handleSortChange(value: string) {
    setSortBy(value)
    setPage(1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {totalCount} total lead{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search company or contact..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder:text-gray-400"
            />
          </div>

          {/* Stage Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={stageFilter}
              onChange={(e) => handleStageChange(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? 'All Stages' : s}
                </option>
              ))}
            </select>
          </div>

          {/* Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => handleSourceChange(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
          >
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s === 'All' ? 'All Sources' : s}
              </option>
            ))}
          </select>

          {/* Sort */}
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="w-4 h-4 text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
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

      {/* Leads Table */}
      {loading ? (
        <TableSkeleton rows={8} cols={8} />
      ) : error ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500 mb-3">{error}</p>
          <button
            onClick={fetchLeads}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Retry
          </button>
        </div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <Users className="w-16 h-16 text-gray-200 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-1">No leads found</h3>
          <p className="text-sm text-gray-400">
            {searchQuery
              ? `No results for "${searchQuery}". Try a different search term.`
              : 'Adjust your filters or add new leads to get started.'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Stage</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Deal Value</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Last Activity</th>
                  <th className="px-4 py-3">Assigned To</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {leads.map((lead) => {
                  const score =
                    (lead as any).score?.overall_score ??
                    (lead as any).overall_score ??
                    0
                  return (
                    <tr
                      key={lead.id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/leads/${lead.id}`)}
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">
                          {lead.company_name}
                        </div>
                        {lead.industry && (
                          <div className="text-xs text-gray-400 mt-0.5">
                            {lead.industry}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-gray-700">{lead.contact_name}</div>
                        {lead.contact_email && (
                          <div className="text-xs text-gray-400 mt-0.5">
                            {lead.contact_email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStageColor(
                            lead.stage
                          )}`}
                        >
                          {lead.stage}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <ScoreBadge score={score} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-gray-700 font-medium">
                        {formatCurrency(lead.deal_value)}
                      </td>
                      <td className="px-4 py-3 text-gray-500 capitalize">
                        {lead.source?.replace('_', ' ') || '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {lead.last_activity_at
                          ? formatRelative(lead.last_activity_at)
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {lead.assigned_rep_name || lead.assigned_to || '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3">
              <p className="text-xs text-gray-500">
                Showing {(page - 1) * PAGE_SIZE + 1}
                {' - '}
                {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex items-center justify-center w-8 h-8 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (page <= 3) {
                    pageNum = i + 1
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = page - 2 + i
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                        page === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'border border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="inline-flex items-center justify-center w-8 h-8 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
