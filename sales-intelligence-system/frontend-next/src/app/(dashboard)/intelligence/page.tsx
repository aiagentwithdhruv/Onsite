'use client'

import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import Papa from 'papaparse'
import {
  Upload, RefreshCw, Filter, TrendingUp, Users, Phone, Target, Flame, Award,
  Building2, AlertTriangle, ChevronDown, Database, Clock, GitMerge, Copy, Trash2, X,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts'
import {
  smartMerge, getAllLeads, getLeadCount, getUploadHistory, getPhoneMergeHistory,
  clearAllData, getLastUpload,
  type MergeResult, type UploadRecord, type PhoneMergeDetail,
} from '@/lib/dataStore'

type Row = Record<string, string>

const COLORS = ['#6366f1','#22c55e','#f59e0b','#ef4444','#3b82f6','#a855f7','#06b6d4','#ec4899','#14b8a6','#f97316','#8b5cf6','#84cc16','#e11d48','#0ea5e9']

const IMPORTANT_KEYWORDS = [
  'studio','corpo','indus','energ','civil','hous','found','struc',
  'limit','agency','contrac','home','servi','trad','associ','world','space','company','private',
  'cons','infra','tech','inte','enter','dev','build','engg','constru','plan','proj','arch','des','real',
  'prop','site','firm','group','hold','estate','pvt','llp','llc','eng','decor',
]

function parseDate(str: string | undefined): Date | null {
  if (!str) return null
  const d = new Date(str)
  return isNaN(d.getTime()) ? null : d
}

function daysBetween(d1: Date, d2: Date) {
  return Math.floor((d2.getTime() - d1.getTime()) / 86400000)
}

function pct(num: number, den: number) {
  return den ? ((num / den) * 100).toFixed(1) + '%' : '0%'
}

function matchesImportant(name: string) {
  if (!name) return false
  const raw = name.toLowerCase()
  return IMPORTANT_KEYWORDS.some(k => raw.includes(k))
}

function count(arr: Row[], field: string): [string, number][] {
  const c: Record<string, number> = {}
  arr.forEach(r => { const v = r[field] || ''; if (v) c[v] = (c[v] || 0) + 1 })
  return Object.entries(c).sort((a, b) => b[1] - a[1])
}

function sourceStats(arr: Row[], field: string, minCount: number) {
  const map: Record<string, { key: string; total: number; demo: number; sale: number }> = {}
  arr.forEach(r => {
    const key = r[field]
    if (!key) return
    if (!map[key]) map[key] = { key, total: 0, demo: 0, sale: 0 }
    map[key].total += 1
    if (r.demo_done === '1') map[key].demo += 1
    if (r.sale_done === '1') map[key].sale += 1
  })
  return Object.values(map)
    .filter(v => v.total >= minCount)
    .map(v => ({ ...v, saleRate: v.sale / Math.max(v.total, 1) }))
    .sort((a, b) => b.saleRate - a.saleRate)
}

const TABS = ['Overview', 'Pipeline', 'Team', 'Sources', 'Aging', 'Trends', 'Deep Dive'] as const
type Tab = typeof TABS[number]

export default function IntelligencePage() {
  const [allData, setAllData] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingText, setLoadingText] = useState('Loading saved data...')
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [mergeResult, setMergeResult] = useState<MergeResult | null>(null)
  const [uploadHistory, setUploadHistory] = useState<UploadRecord[]>([])
  const [phoneMerges, setPhoneMerges] = useState<PhoneMergeDetail[]>([])
  const [showPanel, setShowPanel] = useState<'history' | 'duplicates' | 'merge' | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  // Auto-load from IndexedDB on mount (survives refresh)
  useEffect(() => {
    async function loadSaved() {
      try {
        const count = await getLeadCount()
        if (count > 0) {
          setLoadingText(`Loading ${count.toLocaleString()} saved leads...`)
          const leads = await getAllLeads()
          setAllData(leads)
          const history = await getUploadHistory()
          setUploadHistory(history)
          const merges = await getPhoneMergeHistory()
          setPhoneMerges(merges)
        }
      } catch {
        // IndexedDB not available or empty
      }
      setLoading(false)
    }
    loadSaved()
  }, [])

  const handleFile = useCallback((file: File) => {
    setLoading(true)
    setLoadingText('Parsing CSV data...')
    setMergeResult(null)
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      transformHeader: (h: string) => h.trim().replace(/^\uFEFF/, ''),
      complete: async (results) => {
        const parsed = (results.data as Row[]).filter(r => r.lead_name?.trim())
        setLoadingText(`Smart merging ${parsed.length.toLocaleString()} leads...`)

        // Run smart merge (dedup by zoho_lead_id + phone detection)
        const result = await smartMerge(parsed, file.name, 'csv')
        setMergeResult(result)

        // Reload all data from IndexedDB (merged)
        setLoadingText('Loading merged data...')
        const allLeads = await getAllLeads()
        setAllData(allLeads)

        // Refresh history and duplicates
        const history = await getUploadHistory()
        setUploadHistory(history)
        const merges = await getPhoneMergeHistory()
        setPhoneMerges(merges)

        setLoading(false)
        setShowPanel('merge')
      },
      error: () => {
        setLoading(false)
        alert('Error parsing CSV. Please try again.')
      },
    })
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const handleClearAll = useCallback(async () => {
    if (!confirm('Clear all saved data? This cannot be undone.')) return
    await clearAllData()
    setAllData([])
    setUploadHistory([])
    setPhoneMerges([])
    setMergeResult(null)
    setShowPanel(null)
  }, [])

  const filterOptions = useMemo(() => {
    if (!allData.length) return {}
    const unique = (field: string) => [...new Set(allData.map(r => r[field]).filter(Boolean))].sort()
    return {
      lead_owner_manager: unique('lead_owner_manager'),
      deal_owner: unique('deal_owner'),
      lead_source: unique('lead_source'),
      region: unique('region'),
      lead_status: unique('lead_status'),
    }
  }, [allData])

  const filteredData = useMemo(() => {
    return allData.filter(r => {
      for (const [key, val] of Object.entries(filters)) {
        if (val && r[key] !== val) return false
      }
      return true
    })
  }, [allData, filters])

  // Upload screen (no data yet)
  if (!allData.length && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/20 text-amber-400">
          <TrendingUp className="h-8 w-8" />
        </div>
        <h1 className="mb-2 text-3xl font-bold text-zinc-900 dark:text-white">Sales Intelligence</h1>
        <p className="mb-8 max-w-md text-zinc-500 dark:text-zinc-400">
          Upload your Zoho CRM leads export (CSV) to get actionable insights, team performance metrics, and pipeline analysis.
          <br /><span className="mt-2 inline-block text-xs text-amber-500">Data persists locally — no re-upload on refresh</span>
        </p>
        <div
          className="group flex w-full max-w-md cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed border-zinc-300 bg-white px-12 py-10 transition-all hover:border-amber-500 hover:bg-amber-50/50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-amber-500 dark:hover:bg-amber-500/5"
          onClick={() => fileRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
        >
          <Upload className="mb-4 h-12 w-12 text-zinc-400 transition-colors group-hover:text-amber-500" />
          <p className="mb-1 text-lg font-semibold text-zinc-700 dark:text-zinc-200">Drop your CSV file here</p>
          <p className="text-sm text-zinc-400">or click to browse &middot; supports large files (300K+ rows)</p>
        </div>
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }} />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-zinc-300 border-t-amber-500" />
        <p className="text-sm text-zinc-500">{loadingText}</p>
      </div>
    )
  }

  const d = filteredData
  const total = d.length
  const demoBooked = d.filter(r => r.demo_booked === '1').length
  const demoDone = d.filter(r => r.demo_done === '1' || r.lead_status === 'Demo Done').length
  const saleDone = d.filter(r => r.sale_done === '1').length
  const purchased = d.filter(r => r.lead_status === 'Purchased').length
  const priority = d.filter(r => r.lead_status === 'Priority').length
  const prospects = d.filter(r => r.is_prospect === '1' || r.sales_stage?.includes('Prospect')).length
  const qualified = d.filter(r => r.lead_status === 'Qualified').length
  const importantCompanies = d.filter(r => matchesImportant((r.company_name || r.lead_name || ''))).length
  const totalRevenue = d.reduce((sum, r) => sum + (parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0), 0)
  const totalPricePitched = d.reduce((sum, r) => sum + (parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0), 0)
  const now = new Date()

  return (
    <div className="space-y-5">
      {/* Merge Result Banner */}
      {mergeResult && showPanel === 'merge' && (
        <div className="relative rounded-xl border border-green-200 bg-green-50 p-4 dark:border-green-500/20 dark:bg-green-500/5">
          <button onClick={() => setShowPanel(null)} className="absolute right-3 top-3 text-zinc-400 hover:text-zinc-600"><X className="h-4 w-4" /></button>
          <div className="mb-2 flex items-center gap-2">
            <GitMerge className="h-5 w-5 text-green-600 dark:text-green-400" />
            <h3 className="text-sm font-semibold text-green-700 dark:text-green-400">Smart Merge Complete</h3>
            <span className="text-xs text-zinc-400">({mergeResult.duration_ms}ms)</span>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div className="rounded-lg bg-white/80 p-2 text-center dark:bg-zinc-800/50">
              <p className="text-lg font-bold text-green-600">{mergeResult.newLeads.toLocaleString()}</p>
              <p className="text-[10px] font-medium uppercase text-zinc-500">New Leads</p>
            </div>
            <div className="rounded-lg bg-white/80 p-2 text-center dark:bg-zinc-800/50">
              <p className="text-lg font-bold text-blue-600">{mergeResult.updatedLeads.toLocaleString()}</p>
              <p className="text-[10px] font-medium uppercase text-zinc-500">Updated</p>
            </div>
            <div className="rounded-lg bg-white/80 p-2 text-center dark:bg-zinc-800/50">
              <p className="text-lg font-bold text-zinc-500">{mergeResult.unchangedLeads.toLocaleString()}</p>
              <p className="text-[10px] font-medium uppercase text-zinc-500">Unchanged</p>
            </div>
            <div className="rounded-lg bg-white/80 p-2 text-center dark:bg-zinc-800/50">
              <p className="text-lg font-bold text-amber-600">{mergeResult.phoneMerged.toLocaleString()}</p>
              <p className="text-[10px] font-medium uppercase text-zinc-500">Phone Merged</p>
            </div>
          </div>
          {mergeResult.changesByField.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="text-[10px] text-zinc-500">Fields changed:</span>
              {mergeResult.changesByField.slice(0, 8).map(f => (
                <span key={f.field} className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-500/15 dark:text-blue-400">
                  {f.field} ({f.count})
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white">Sales Intelligence Dashboard</h1>
          <div className="flex items-center gap-3 text-sm text-zinc-500">
            <span>Showing {d.length.toLocaleString()} of {allData.length.toLocaleString()} leads</span>
            <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400"><Database className="h-3 w-3" /> Saved locally</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPanel(showPanel === 'history' ? null : 'history')}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-600 transition-colors hover:border-blue-500 hover:text-blue-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400"
          >
            <Clock className="h-3.5 w-3.5" /> History ({uploadHistory.length})
          </button>
          {phoneMerges.length > 0 && (
            <button
              onClick={() => setShowPanel(showPanel === 'merges' ? null : 'merges')}
              className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-100 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400"
            >
              <GitMerge className="h-3.5 w-3.5" /> Phone Merges ({phoneMerges.length})
            </button>
          )}
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 transition-colors hover:border-amber-500 hover:text-amber-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
          >
            <Upload className="h-3.5 w-3.5" /> Upload / Update
          </button>
          <button
            onClick={handleClearAll}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-500 transition-colors hover:border-red-400 hover:text-red-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-500"
            title="Clear all saved data"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }} />
        </div>
      </div>

      {/* Upload History Panel */}
      {showPanel === 'history' && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold"><Clock className="h-4 w-4 text-blue-500" /> Upload History</h3>
            <button onClick={() => setShowPanel(null)} className="text-zinc-400 hover:text-zinc-600"><X className="h-4 w-4" /></button>
          </div>
          {uploadHistory.length === 0 ? (
            <p className="text-xs text-zinc-400">No uploads yet.</p>
          ) : (
            <div className="max-h-60 space-y-2 overflow-auto">
              {uploadHistory.map((u, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg bg-zinc-50 px-3 py-2 text-xs dark:bg-zinc-800/50">
                  <div>
                    <span className="font-medium text-zinc-700 dark:text-zinc-300">{u.fileName}</span>
                    <span className="ml-2 text-zinc-400">{new Date(u.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="flex gap-3 text-[10px]">
                    <span className="text-green-600">+{u.newLeads.toLocaleString()} new</span>
                    <span className="text-blue-600">{u.updatedLeads.toLocaleString()} updated</span>
                    <span className="text-zinc-400">{u.unchangedLeads.toLocaleString()} same</span>
                    {u.phoneMerged > 0 && <span className="text-amber-600">{u.phoneMerged} merged</span>}
                    <span className="text-zinc-400">{u.duration_ms}ms</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Phone Merges Panel */}
      {showPanel === 'merges' && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-500/20 dark:bg-amber-500/5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-400"><GitMerge className="h-4 w-4" /> Phone Merges — Leads merged by same phone number</h3>
            <button onClick={() => setShowPanel(null)} className="text-zinc-400 hover:text-zinc-600"><X className="h-4 w-4" /></button>
          </div>
          <p className="mb-2 text-xs text-zinc-500">Older user_date kept, newer lead_source_date kept, notes combined, higher-priority status kept.</p>
          <div className="max-h-72 space-y-2 overflow-auto">
            {phoneMerges.slice(0, 50).map((m, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-white/80 px-3 py-2 dark:bg-zinc-800/50">
                <div className="flex items-center gap-2 text-xs">
                  <Phone className="h-3 w-3 text-zinc-400" />
                  <span className="font-mono text-zinc-400">{m.phone}</span>
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">{m.keptName}</span>
                  <span className="rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-500/15 dark:text-green-400">kept</span>
                </div>
                <span className="text-[10px] text-zinc-500">merged {m.mergedCount} duplicate{m.mergedCount > 1 ? 's' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-zinc-400" />
        {[
          { key: 'lead_owner_manager', label: 'Manager' },
          { key: 'deal_owner', label: 'Deal Owner' },
          { key: 'lead_source', label: 'Source' },
          { key: 'region', label: 'Region' },
          { key: 'lead_status', label: 'Status' },
        ].map(f => (
          <div key={f.key} className="relative">
            <select
              value={filters[f.key] || ''}
              onChange={e => setFilters(prev => ({ ...prev, [f.key]: e.target.value }))}
              className="appearance-none rounded-lg border border-zinc-200 bg-white py-1.5 pl-3 pr-8 text-xs font-medium text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              <option value="">All {f.label}s</option>
              {(filterOptions[f.key as keyof typeof filterOptions] || []).map(v => <option key={v} value={v}>{v}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-zinc-400" />
          </div>
        ))}
        {Object.values(filters).some(Boolean) && (
          <button onClick={() => setFilters({})} className="text-xs text-amber-500 hover:text-amber-400">Clear all</button>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9">
        {[
          { label: 'Total Leads', value: total, color: 'text-blue-500', icon: Users },
          { label: 'Demo Booked', value: demoBooked, color: 'text-cyan-500', icon: Phone },
          { label: 'Demo Done', value: demoDone, color: 'text-purple-500', icon: Target },
          { label: 'Sales Done', value: saleDone, color: 'text-green-500', icon: TrendingUp },
          { label: 'Purchased', value: purchased, color: 'text-amber-500', icon: Award },
          { label: 'Priority', value: priority, color: 'text-pink-500', icon: Flame },
          { label: 'Prospects', value: prospects, color: 'text-indigo-500', icon: Target },
          { label: 'Qualified', value: qualified, color: 'text-red-500', icon: Award },
          { label: 'Key Companies', value: importantCompanies, color: 'text-blue-500', icon: Building2 },
        ].map(kpi => (
          <div key={kpi.label} className="rounded-xl border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="mb-1 flex items-center gap-1.5">
              <kpi.icon className={`h-3.5 w-3.5 ${kpi.color}`} />
              <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">{kpi.label}</span>
            </div>
            <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value.toLocaleString()}</p>
          </div>
        ))}
      </div>
      {/* Revenue KPIs */}
      {(totalRevenue > 0 || totalPricePitched > 0) && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {totalRevenue > 0 && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-3 dark:border-green-500/20 dark:bg-green-500/5">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-green-600">Annual Revenue</span>
              <p className="text-xl font-bold text-green-600">₹{(totalRevenue / 100000).toFixed(1)}L</p>
            </div>
          )}
          {totalPricePitched > 0 && (
            <div className="rounded-xl border border-purple-200 bg-purple-50 p-3 dark:border-purple-500/20 dark:bg-purple-500/5">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-purple-600">Price Pitched</span>
              <p className="text-xl font-bold text-purple-600">₹{(totalPricePitched / 100000).toFixed(1)}L</p>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-0 border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${activeTab === tab ? 'border-amber-500 text-amber-600 dark:text-amber-400' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'Overview' && <OverviewTab data={d} allData={allData} now={now} demoBooked={demoBooked} demoDone={demoDone} saleDone={saleDone} />}
      {activeTab === 'Pipeline' && <PipelineTab data={d} />}
      {activeTab === 'Team' && <TeamTab data={d} now={now} />}
      {activeTab === 'Sources' && <SourcesTab data={d} />}
      {activeTab === 'Aging' && <AgingTab data={d} now={now} />}
      {activeTab === 'Trends' && <TrendsTab data={d} />}
      {activeTab === 'Deep Dive' && <DeepDiveTab data={d} />}
    </div>
  )
}

function Card({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 ${className}`}>
      <h3 className="mb-3 text-sm font-semibold text-zinc-700 dark:text-zinc-200">{title}</h3>
      {children}
    </div>
  )
}

function InsightBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/20 dark:bg-amber-500/5">
      <h4 className="mb-1 text-sm font-semibold text-amber-700 dark:text-amber-400">{title}</h4>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{children}</p>
    </div>
  )
}

function SmartCard({ title, metric, desc, meta }: { title: string; metric: string; desc: string; meta: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-800/50">
      <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400">{title}</h4>
      <p className="my-1 text-lg font-bold text-zinc-800 dark:text-white">{metric}</p>
      <p className="text-xs text-zinc-500">{desc}</p>
      <p className="mt-1 text-[10px] text-zinc-400">{meta}</p>
    </div>
  )
}

function Badge({ children, color = 'zinc' }: { children: React.ReactNode; color?: string }) {
  const cls: Record<string, string> = {
    green: 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400',
    red: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
    amber: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400',
    purple: 'bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400',
    zinc: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-400',
  }
  return <span className={`inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${cls[color] || cls.zinc}`}>{children}</span>
}

// ---- OVERVIEW ----
function OverviewTab({ data, allData, now, demoBooked, demoDone, saleDone }: { data: Row[]; allData: Row[]; now: Date; demoBooked: number; demoDone: number; saleDone: number }) {
  const total = data.length
  const demoRate = total ? (demoDone / total * 100).toFixed(1) : '0'
  const saleRate = total ? (saleDone / total * 100).toFixed(1) : '0'
  const topSource = count(data, 'lead_source').filter(x => x[0])[0]

  const stale30 = data.filter(r => {
    const lt = parseDate(r.last_touched_date_new)
    return lt && daysBetween(lt, now) > 30 && !['Purchased', 'Rejected', 'DTA'].includes(r.lead_status)
  }).length

  const bookedNotDone = Math.max(0, demoBooked - demoDone)
  const saleDrop = Math.max(0, demoDone - saleDone)
  const stats = sourceStats(data, 'lead_source', 100)
  const bestSource = stats[0]
  const worstSource = stats[stats.length - 1]
  const ownerStats2 = sourceStats(data, 'deal_owner', 100)
  const topCloser = ownerStats2[0]
  const importantLeads = data.filter(r => matchesImportant((r.company_name || r.lead_name || '')))
  const importantSales = importantLeads.filter(r => r.sale_done === '1' || r.lead_status === 'Purchased').length

  const statusData = count(data, 'lead_status').slice(0, 10).map(([name, value]) => ({ name: name.length > 20 ? name.slice(0, 18) + '..' : name, value }))
  const srcData = count(data, 'lead_source').filter(x => x[0]).slice(0, 10).map(([name, value]) => ({ name: name.length > 22 ? name.slice(0, 20) + '..' : name, value }))

  const funnelSteps = [
    { label: 'Total Leads', value: total },
    { label: 'Demo Booked', value: demoBooked },
    { label: 'Demo Done', value: demoDone },
    { label: 'Trial Activated', value: data.filter(r => r.trial_activated === '1').length },
    { label: 'Prospect', value: data.filter(r => r.is_prospect === '1').length },
    { label: 'Sale Done', value: saleDone },
    { label: 'Purchased', value: data.filter(r => r.lead_status === 'Purchased').length },
  ]

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <InsightBox title="Key Insight: Conversion Funnel">
          Overall demo conversion is <strong>{demoRate}%</strong> and lead-to-sale rate is <strong>{saleRate}%</strong>.
          {topSource && <> Top lead source is <strong>{topSource[0]}</strong> with {topSource[1].toLocaleString()} leads.</>}
        </InsightBox>
        {stale30 > 0 && (
          <InsightBox title="Action Required">
            <strong>{stale30.toLocaleString()}</strong> active leads haven&apos;t been touched in 30+ days. Check the Aging tab for details.
          </InsightBox>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <SmartCard title="Biggest Funnel Drop" metric={`${Math.max(bookedNotDone, saleDrop).toLocaleString()} leads`} desc={bookedNotDone >= saleDrop ? `Booked → Done drop: ${demoBooked ? (bookedNotDone / demoBooked * 100).toFixed(1) : 0}%` : `Demo → Sale drop: ${demoDone ? (saleDrop / demoDone * 100).toFixed(1) : 0}%`} meta="Tune messaging and follow-ups" />
        <SmartCard title="Demo Backlog" metric={`${bookedNotDone.toLocaleString()} not done`} desc={`${demoBooked ? (bookedNotDone / demoBooked * 100).toFixed(1) : 0}% of booked demos pending`} meta="Push owners to confirm & complete" />
        <SmartCard title="Best Lead Source" metric={bestSource?.key || 'N/A'} desc={`Conversion ${bestSource ? (bestSource.saleRate * 100).toFixed(2) : 0}% from ${bestSource?.total.toLocaleString() || 0} leads`} meta="Scale if budget allows" />
        <SmartCard title="Weak Lead Source" metric={worstSource?.key || 'N/A'} desc={`Conversion ${worstSource ? (worstSource.saleRate * 100).toFixed(2) : 0}% from ${worstSource?.total.toLocaleString() || 0} leads`} meta="Refine targeting" />
        <SmartCard title="Top Closer" metric={topCloser?.key || 'N/A'} desc={`Conversion ${topCloser ? (topCloser.saleRate * 100).toFixed(2) : 0}% over ${topCloser?.total.toLocaleString() || 0} leads`} meta="Share best practices" />
        <SmartCard title="Key Companies" metric={`${importantLeads.length.toLocaleString()} leads`} desc={`Conversion ${importantLeads.length ? (importantSales / importantLeads.length * 100).toFixed(2) : 0}%`} meta="Prioritize these accounts" />
        <SmartCard title="Urgent Follow-up" metric={`${stale30.toLocaleString()} stale`} desc="Active leads untouched 30+ days" meta="Assign immediately" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Lead Status Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={110} paddingAngle={2}>
              {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /><Legend /></PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Top Lead Sources">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={srcData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
              <Tooltip /><Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Conversion Funnel">
        <div className="space-y-2 py-2">
          {funnelSteps.map((step, i) => {
            const w = total ? Math.max(8, (step.value / total) * 100) : 0
            return (
              <div key={step.label} className="flex items-center gap-3">
                <span className="w-28 text-right text-xs font-medium text-zinc-500">{step.label}</span>
                <div className="h-9 rounded-lg flex items-center px-3 text-xs font-bold text-white" style={{ width: `${w}%`, background: COLORS[i], minWidth: 60 }}>
                  {step.value.toLocaleString()}
                </div>
                <span className="text-xs text-zinc-400">{pct(step.value, total)}</span>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}

// ---- PIPELINE ----
function PipelineTab({ data }: { data: Row[] }) {
  const statusData = count(data, 'lead_status').slice(0, 15).map(([name, value]) => ({ name: name.length > 20 ? name.slice(0, 18) + '..' : name, value }))
  const stageData = count(data, 'sales_stage').filter(x => x[0]).map(([name, value]) => ({ name, value }))
  const demoBooked = data.filter(r => r.demo_booked === '1').length
  const demoDone = data.filter(r => r.demo_done === '1').length
  const noDemoBooked = data.length - demoBooked
  const demoMetrics = [
    { name: 'Demo Done', value: demoDone },
    { name: 'Booked (Not Done)', value: Math.max(0, demoBooked - demoDone) },
    { name: 'No Demo Booked', value: noDemoBooked },
  ]
  const dispData = count(data, 'call_disposition').filter(x => x[0]).slice(0, 12).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Lead Status Breakdown">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={statusData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} /><YAxis /><Tooltip /><Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Sales Stage">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={stageData} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill="#a855f7" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Demo Metrics">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart><Pie data={demoMetrics} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={100}>
              <Cell fill="#22c55e" /><Cell fill="#f59e0b" /><Cell fill="#ef4444" />
            </Pie><Tooltip /><Legend /></PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Call Disposition">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dispData} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill="#06b6d4" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}

// ---- TEAM ----
function TeamTab({ data, now }: { data: Row[]; now: Date }) {
  const managers = count(data, 'lead_owner_manager').filter(x => x[0])
  const ownerData = count(data, 'deal_owner').filter(x => x[0] && x[0] !== 'Onsite' && x[0] !== 'Offline Campaign').slice(0, 20)

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {managers.map(([mgr, total]) => {
          const ml = data.filter(r => r.lead_owner_manager === mgr)
          const demos = ml.filter(r => r.demo_done === '1').length
          const sales = ml.filter(r => r.sale_done === '1').length
          const pri = ml.filter(r => r.lead_status === 'Priority').length
          return (
            <Card key={mgr} title={mgr}>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-zinc-500">Total Leads</span><span className="font-semibold text-blue-500">{total.toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Demos Done</span><span className="font-semibold text-purple-500">{demos.toLocaleString()} ({pct(demos, total)})</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Sales Done</span><span className="font-semibold text-green-500">{sales.toLocaleString()} ({pct(sales, total)})</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Priority</span><span className="font-semibold text-amber-500">{pri.toLocaleString()}</span></div>
                <div className="h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-700"><div className="h-full rounded-full bg-green-500" style={{ width: `${Math.min(sales / Math.max(total, 1) * 100 * 10, 100)}%` }} /></div>
              </div>
            </Card>
          )
        })}
      </div>

      <Card title="Team Leaderboard">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:border-zinc-700">
              <th className="py-2 pr-3">Deal Owner</th><th className="py-2 pr-3">Manager</th><th className="py-2 pr-2">Total</th><th className="py-2 pr-2">Demo</th><th className="py-2 pr-2">Sales</th><th className="py-2 pr-2">Conv %</th><th className="py-2 pr-2">Priority</th><th className="py-2">Stale 30d+</th>
            </tr></thead>
            <tbody>
              {ownerData.map(([own, total]) => {
                const ol = data.filter(r => r.deal_owner === own)
                const mgr = ol.find(r => r.lead_owner_manager)?.lead_owner_manager || '-'
                const dd = ol.filter(r => r.demo_done === '1').length
                const sd = ol.filter(r => r.sale_done === '1').length
                const pri = ol.filter(r => r.lead_status === 'Priority').length
                const stale = ol.filter(r => { const lt = parseDate(r.last_touched_date_new); return lt && daysBetween(lt, now) > 30 && !['Purchased', 'Rejected', 'DTA'].includes(r.lead_status) }).length
                const convPct = total ? (sd / total * 100) : 0
                return (
                  <tr key={own} className="border-b border-zinc-100 dark:border-zinc-800">
                    <td className="py-2 pr-3 font-medium">{own}</td><td className="py-2 pr-3 text-zinc-500">{mgr}</td>
                    <td className="py-2 pr-2">{total.toLocaleString()}</td><td className="py-2 pr-2">{dd.toLocaleString()}</td>
                    <td className="py-2 pr-2">{sd.toLocaleString()}</td>
                    <td className="py-2 pr-2"><Badge color={convPct > 5 ? 'green' : convPct > 2 ? 'amber' : 'red'}>{pct(sd, total)}</Badge></td>
                    <td className="py-2 pr-2">{pri}</td><td className="py-2">{stale > 0 ? <Badge color="red">{stale}</Badge> : '0'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

// ---- SOURCES ----
function SourcesTab({ data }: { data: Row[] }) {
  const srcData = count(data, 'lead_source').filter(x => x[0]).slice(0, 15).map(([name, value]) => ({ name: name.length > 22 ? name.slice(0, 20) + '..' : name, value }))
  const srcConv = count(data, 'lead_source').filter(x => x[0]).slice(0, 12).map(([src, total]) => {
    const sl = data.filter(r => r.lead_source === src)
    return { name: src.length > 22 ? src.slice(0, 20) + '..' : src, saleRate: +(sl.filter(r => r.sale_done === '1').length / total * 100).toFixed(2), demoRate: +(sl.filter(r => r.demo_done === '1').length / total * 100).toFixed(2) }
  })
  const stData = count(data, 'lead_source_type').filter(x => x[0]).map(([name, value]) => ({ name, value }))
  const campData = count(data, 'campaign_name').filter(x => x[0]).slice(0, 15).map(([name, value]) => ({ name: name.length > 25 ? name.slice(0, 22) + '..' : name, value }))

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Lead Source Volume">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={srcData} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Source Conversion Rates">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={srcConv} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 10 }} /><Tooltip />
              <Bar dataKey="saleRate" name="Sale %" fill="#22c55e" /><Bar dataKey="demoRate" name="Demo %" fill="#a855f7" />
            <Legend /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Source Type">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart><Pie data={stData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={100}>
              {stData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /><Legend /></PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Campaign Performance">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={campData} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill="#f59e0b" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}

// ---- AGING ----
function AgingTab({ data, now }: { data: Row[]; now: Date }) {
  const ageBuckets: Record<string, number> = { '0-7d': 0, '8-30d': 0, '31-90d': 0, '91-180d': 0, '181-365d': 0, '1-2yr': 0, '2yr+': 0 }
  data.forEach(r => {
    const ud = parseDate(r.user_date)
    if (!ud) return
    const days = daysBetween(ud, now)
    if (days <= 7) ageBuckets['0-7d']++
    else if (days <= 30) ageBuckets['8-30d']++
    else if (days <= 90) ageBuckets['31-90d']++
    else if (days <= 180) ageBuckets['91-180d']++
    else if (days <= 365) ageBuckets['181-365d']++
    else if (days <= 730) ageBuckets['1-2yr']++
    else ageBuckets['2yr+']++
  })
  const ageData = Object.entries(ageBuckets).map(([name, value]) => ({ name, value }))
  const ageColors = ['#22c55e', '#84cc16', '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#991b1b']

  const touchBuckets: Record<string, number> = { '0-7d': 0, '8-14d': 0, '15-30d': 0, '31-60d': 0, '61-90d': 0, '90d+': 0, 'Never': 0 }
  data.forEach(r => {
    const lt = parseDate(r.last_touched_date_new)
    if (!lt) { touchBuckets['Never']++; return }
    const days = daysBetween(lt, now)
    if (days <= 7) touchBuckets['0-7d']++
    else if (days <= 14) touchBuckets['8-14d']++
    else if (days <= 30) touchBuckets['15-30d']++
    else if (days <= 60) touchBuckets['31-60d']++
    else if (days <= 90) touchBuckets['61-90d']++
    else touchBuckets['90d+']++
  })
  const touchData = Object.entries(touchBuckets).map(([name, value]) => ({ name, value }))

  const activeStatuses = ['Priority', 'Follow Up', 'Qualified', 'Demo Booked', 'Demo Done', 'User not attend session']
  const staleLeads = data.filter(r => {
    const lt = parseDate(r.last_touched_date_new)
    return lt && daysBetween(lt, now) > 30 && activeStatuses.includes(r.lead_status)
  }).sort((a, b) => {
    const da = parseDate(a.last_touched_date_new)!
    const db2 = parseDate(b.last_touched_date_new)!
    return da.getTime() - db2.getTime()
  })

  const hotP = data.filter(r => r.sales_stage === 'Very High Prospect' || r.sales_stage === 'High Prospect')

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Lead Age Distribution">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={ageData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" /><YAxis /><Tooltip />
              <Bar dataKey="value">{ageData.map((_, i) => <Cell key={i} fill={ageColors[i]} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Days Since Last Touch">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={touchData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" /><YAxis /><Tooltip />
              <Bar dataKey="value">{touchData.map((_, i) => <Cell key={i} fill={ageColors[Math.min(i, ageColors.length - 1)]} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={`Stale Leads — 30+ Days (${staleLeads.length.toLocaleString()})`}>
          <div className="max-h-80 overflow-auto">
            <table className="w-full text-left text-xs">
              <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase text-zinc-400 dark:border-zinc-700">
                <th className="py-2">Name</th><th className="py-2">Status</th><th className="py-2">Owner</th><th className="py-2">Days</th><th className="py-2">Phone</th>
              </tr></thead>
              <tbody>{staleLeads.slice(0, 50).map((r, i) => {
                const lt = parseDate(r.last_touched_date_new)
                const days = lt ? daysBetween(lt, now) : '-'
                return <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-1.5 font-medium">{r.lead_name || '-'}</td><td><Badge color="amber">{r.lead_status}</Badge></td><td className="text-zinc-500">{r.deal_owner || '-'}</td><td><Badge color="red">{days}d</Badge></td><td className="text-zinc-500">{r.lead_phone || '-'}</td></tr>
              })}</tbody>
            </table>
          </div>
        </Card>
        <Card title={`Hot Prospects (${hotP.length})`}>
          <div className="max-h-80 overflow-auto">
            <table className="w-full text-left text-xs">
              <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase text-zinc-400 dark:border-zinc-700">
                <th className="py-2">Name</th><th className="py-2">Stage</th><th className="py-2">Owner</th><th className="py-2">Company</th><th className="py-2">Phone</th>
              </tr></thead>
              <tbody>{hotP.slice(0, 50).map((r, i) => (
                <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-1.5 font-medium">{r.lead_name || '-'}</td><td><Badge color={r.sales_stage === 'Very High Prospect' ? 'green' : 'blue'}>{r.sales_stage}</Badge></td><td className="text-zinc-500">{r.deal_owner || r.lead_owner || '-'}</td><td className="text-zinc-500">{r.company_name || '-'}</td><td className="text-zinc-500">{r.lead_phone || '-'}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}

// ---- TRENDS ----
function TrendsTab({ data }: { data: Row[] }) {
  const monthlyMap: Record<string, { leads: number; demos: number; sales: number; purchased: number }> = {}
  data.forEach(r => {
    const ud = parseDate(r.user_date)
    if (!ud) return
    const key = `${ud.getFullYear()}-${String(ud.getMonth() + 1).padStart(2, '0')}`
    if (!monthlyMap[key]) monthlyMap[key] = { leads: 0, demos: 0, sales: 0, purchased: 0 }
    monthlyMap[key].leads++
    if (r.demo_done === '1') monthlyMap[key].demos++
    if (r.sale_done === '1') monthlyMap[key].sales++
    if (r.lead_status === 'Purchased') monthlyMap[key].purchased++
  })
  const months = Object.keys(monthlyMap).sort().slice(-24)
  const trendData = months.map(m => ({
    month: m,
    leads: monthlyMap[m].leads,
    demos: monthlyMap[m].demos,
    sales: monthlyMap[m].sales,
    purchased: monthlyMap[m].purchased,
    demoRate: +(monthlyMap[m].demos / Math.max(monthlyMap[m].leads, 1) * 100).toFixed(1),
    saleRate: +(monthlyMap[m].sales / Math.max(monthlyMap[m].leads, 1) * 100).toFixed(1),
  }))

  return (
    <div className="space-y-4">
      <Card title="Monthly Lead Intake">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis /><Tooltip />
            <Line type="monotone" dataKey="leads" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Monthly Demos Done">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trendData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={50} /><YAxis /><Tooltip /><Bar dataKey="demos" fill="#a855f7" radius={[4, 4, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Monthly Sales">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trendData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={50} /><YAxis /><Tooltip />
              <Bar dataKey="sales" fill="#22c55e" radius={[4, 4, 0, 0]} /><Bar dataKey="purchased" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            <Legend /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <Card title="Monthly Conversion Rates">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis /><Tooltip />
            <Line type="monotone" dataKey="demoRate" name="Demo Rate %" stroke="#a855f7" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="saleRate" name="Sale Rate %" stroke="#22c55e" strokeWidth={2} dot={false} />
          <Legend /></LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

// ---- DEEP DIVE ----
function DeepDiveTab({ data }: { data: Row[] }) {
  const profData = count(data, 'user_profession').filter(x => x[0]).slice(0, 12).map(([name, value]) => ({ name: name.length > 20 ? name.slice(0, 18) + '..' : name, value }))
  const tsData = count(data, 'Team_size').filter(x => x[0]).slice(0, 10).map(([name, value]) => ({ name, value }))
  const stateData = count(data, 'state_mobile').filter(x => x[0]).slice(0, 20).map(([name, value]) => ({ name: name.length > 15 ? name.slice(0, 13) + '..' : name, value }))
  const pqData = count(data, 'pre_qualification').filter(x => x[0]).map(([name, value]) => ({ name: 'Stage ' + name, value }))

  const notesLeads = data.filter(r => r.lead_notes?.trim() && r.lead_notes.trim().length > 10)
    .sort((a, b) => {
      const da = parseDate(a.notes_date)?.getTime() || 0
      const db2 = parseDate(b.notes_date)?.getTime() || 0
      return db2 - da
    })

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Profession Breakdown">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={profData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={110}>
              {profData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /><Legend /></PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Team Size Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tsData}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" tick={{ fontSize: 10 }} /><YAxis /><Tooltip /><Bar dataKey="value" fill="#06b6d4" radius={[4, 4, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="State/Region (Top 20)">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={stateData} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Pre-Qualification">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={pqData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={110}>
              {pqData.map((_, i) => <Cell key={i} fill={COLORS[(i + 5) % COLORS.length]} />)}
            </Pie><Tooltip /><Legend /></PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Notes Intelligence — Recent Actionable Notes">
        <div className="max-h-96 overflow-auto">
          <table className="w-full text-left text-xs">
            <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase text-zinc-400 dark:border-zinc-700">
              <th className="py-2">Name</th><th className="py-2">Status</th><th className="py-2">Stage</th><th className="py-2">Owner</th><th className="py-2">Date</th><th className="py-2">Notes</th>
            </tr></thead>
            <tbody>{notesLeads.slice(0, 80).map((r, i) => {
              const preview = (r.lead_notes || '').replace(/\n/g, ' ').slice(0, 120) + (r.lead_notes && r.lead_notes.length > 120 ? '...' : '')
              return (
                <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800">
                  <td className="py-1.5 font-medium">{r.lead_name || '-'}</td>
                  <td><Badge color={r.lead_status === 'Priority' ? 'amber' : r.lead_status === 'Purchased' ? 'green' : 'zinc'}>{r.lead_status || '-'}</Badge></td>
                  <td className="text-zinc-500">{r.sales_stage || '-'}</td>
                  <td className="text-zinc-500">{r.deal_owner || r.lead_owner || '-'}</td>
                  <td className="text-zinc-500">{r.notes_date || '-'}</td>
                  <td className="max-w-xs whitespace-normal text-zinc-500">{preview}</td>
                </tr>
              )
            })}</tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
