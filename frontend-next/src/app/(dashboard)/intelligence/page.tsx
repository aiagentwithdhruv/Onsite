'use client'

import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import Papa from 'papaparse'
import {
  Upload, Filter, TrendingUp, Users, Phone, Target, Flame, Award,
  Building2, ChevronDown, Trash2, DollarSign, MapPin, Crown,
  BarChart2, CalendarCheck, ArrowUpRight, ArrowDownRight,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts'
import { getDashboardSummary, uploadIntelligenceCSV, clearDashboardSummary } from '@/lib/api'

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

const TABS = ['Overview', 'Sales', 'Pipeline', 'Team', 'Sources', 'Aging', 'Trends', 'Deep Dive'] as const
type Tab = typeof TABS[number]

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SummaryData = Record<string, any>

export default function IntelligencePage() {
  const [allData, setAllData] = useState<Row[]>([])
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [mode, setMode] = useState<'empty' | 'summary' | 'full'>('empty')
  const [loading, setLoading] = useState(true)
  const [loadingText, setLoadingText] = useState('Loading dashboard...')
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const fileRef = useRef<HTMLInputElement>(null)

  // Load saved summary from Supabase on mount (instant — ~1-2MB)
  useEffect(() => {
    getDashboardSummary().then(res => {
      if (res.data && res.data.total_leads > 0) {
        setSummary(res.data)
        setMode('summary')
      }
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleFile = useCallback((file: File) => {
    setLoading(true)
    setLoadingText('Uploading & processing...')

    // Upload to backend first (saves summary + agent profiles to Supabase)
    // AND parse client-side in parallel for instant display
    const backendUpload = uploadIntelligenceCSV(file)

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      transformHeader: (h: string) => h.trim().replace(/^\uFEFF/, ''),
      complete: (results) => {
        const data = (results.data as Row[]).filter(r => r.lead_name?.trim())
        setAllData(data)
        setMode('full')
        setLoading(false)
      },
      error: () => {
        setLoading(false)
        alert('Error parsing CSV.')
      },
    })

    // Wait for backend save (non-blocking for UI)
    backendUpload.then(res => {
      console.log(`Saved to Supabase: ${res.data?.total_rows} leads, ${res.data?.agents_updated} agents, ${res.data?.summary_size_kb}KB`)
    }).catch(err => {
      console.warn('Backend save failed:', err?.response?.data || err.message)
    })
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const handleClearAll = useCallback(() => {
    setAllData([])
    setSummary(null)
    setMode('empty')
    setFilters({})
    clearDashboardSummary().catch(() => {})
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

  // Upload screen (no data, no summary)
  if (mode === 'empty' && !loading) {
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

  // Summary mode: render from pre-computed Supabase data (no raw rows needed)
  if (mode === 'summary' && summary) {
    const k = summary.kpis || {}
    return (
      <div className="space-y-5">
        <SummaryDashboard
          summary={summary}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onUpload={() => fileRef.current?.click()}
          onClear={handleClearAll}
        />
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }} />
      </div>
    )
  }

  // Full mode: compute from raw data (after CSV upload)
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
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white">Sales Intelligence Dashboard</h1>
          <p className="text-sm text-zinc-500">Showing {d.length.toLocaleString()} of {allData.length.toLocaleString()} leads</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 transition-colors hover:border-amber-500 hover:text-amber-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
          >
            <Upload className="h-3.5 w-3.5" /> Upload New File
          </button>
          <button
            onClick={handleClearAll}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-500 transition-colors hover:border-red-400 hover:text-red-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-500"
            title="Clear data"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }} />
        </div>
      </div>

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
      {activeTab === 'Sales' && <SalesTab data={d} />}
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

// ---- SALES DASHBOARD ----
function SalesTab({ data }: { data: Row[] }) {
  const salesRows = data.filter(r => r.sale_done === '1' || r.lead_status === 'Purchased')
  const totalSales = salesRows.length
  const totalLeads = data.length

  const totalRevenue = salesRows.reduce((s, r) => s + (parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0), 0)
  const totalPricePitched = salesRows.reduce((s, r) => s + (parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0), 0)
  const allRevenue = data.reduce((s, r) => s + (parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0), 0)
  const avgDealSize = totalSales ? totalRevenue / totalSales : 0
  const conversionRate = totalLeads ? (totalSales / totalLeads * 100) : 0

  // Revenue by region
  const regionRevMap: Record<string, { revenue: number; sales: number; leads: number; pitched: number }> = {}
  data.forEach(r => {
    const region = (r.state_mobile || r.region || '').trim()
    if (!region) return
    if (!regionRevMap[region]) regionRevMap[region] = { revenue: 0, sales: 0, leads: 0, pitched: 0 }
    regionRevMap[region].leads += 1
    const rev = parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0
    const pitch = parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0
    regionRevMap[region].revenue += rev
    regionRevMap[region].pitched += pitch
    if (r.sale_done === '1' || r.lead_status === 'Purchased') regionRevMap[region].sales += 1
  })
  const regionData = Object.entries(regionRevMap)
    .map(([name, v]) => ({ name: name.length > 18 ? name.slice(0, 16) + '..' : name, ...v, convRate: v.leads ? +(v.sales / v.leads * 100).toFixed(1) : 0 }))
    .sort((a, b) => b.revenue - a.revenue).slice(0, 15)

  // Revenue by deal owner
  const ownerRevMap: Record<string, { revenue: number; sales: number; leads: number; pitched: number }> = {}
  data.forEach(r => {
    const owner = (r.deal_owner || '').trim()
    if (!owner || owner === 'Onsite' || owner === 'Offline Campaign') return
    if (!ownerRevMap[owner]) ownerRevMap[owner] = { revenue: 0, sales: 0, leads: 0, pitched: 0 }
    ownerRevMap[owner].leads += 1
    const rev = parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0
    const pitch = parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0
    ownerRevMap[owner].revenue += rev
    ownerRevMap[owner].pitched += pitch
    if (r.sale_done === '1' || r.lead_status === 'Purchased') ownerRevMap[owner].sales += 1
  })
  const ownerRevData = Object.entries(ownerRevMap)
    .map(([name, v]) => ({ name, ...v, avgDeal: v.sales ? v.revenue / v.sales : 0, convRate: v.leads ? +(v.sales / v.leads * 100).toFixed(1) : 0 }))
    .sort((a, b) => b.revenue - a.revenue)
  const topOwnerChart = ownerRevData.slice(0, 12).map(o => ({ name: o.name.length > 16 ? o.name.slice(0, 14) + '..' : o.name, revenue: +(o.revenue / 100000).toFixed(1), sales: o.sales }))

  // Monthly sales revenue trend
  const monthlyRevMap: Record<string, { revenue: number; sales: number; pitched: number }> = {}
  data.forEach(r => {
    if (r.sale_done !== '1' && r.lead_status !== 'Purchased') return
    const dateStr = r.sale_done_date || r.user_date || ''
    const d = parseDate(dateStr)
    if (!d) return
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    if (!monthlyRevMap[key]) monthlyRevMap[key] = { revenue: 0, sales: 0, pitched: 0 }
    monthlyRevMap[key].revenue += parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0
    monthlyRevMap[key].pitched += parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0
    monthlyRevMap[key].sales += 1
  })
  const monthlyRevTrend = Object.keys(monthlyRevMap).sort().slice(-18).map(m => ({
    month: m,
    revenue: +(monthlyRevMap[m].revenue / 100000).toFixed(1),
    sales: monthlyRevMap[m].sales,
    pitched: +(monthlyRevMap[m].pitched / 100000).toFixed(1),
  }))

  // Revenue by lead source
  const srcRevMap: Record<string, { revenue: number; sales: number; leads: number }> = {}
  data.forEach(r => {
    const src = (r.lead_source || '').trim()
    if (!src) return
    if (!srcRevMap[src]) srcRevMap[src] = { revenue: 0, sales: 0, leads: 0 }
    srcRevMap[src].leads += 1
    if (r.sale_done === '1' || r.lead_status === 'Purchased') {
      srcRevMap[src].revenue += parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0
      srcRevMap[src].sales += 1
    }
  })
  const srcRevData = Object.entries(srcRevMap)
    .map(([name, v]) => ({ name: name.length > 20 ? name.slice(0, 18) + '..' : name, revenue: +(v.revenue / 100000).toFixed(1), sales: v.sales, leads: v.leads, convRate: v.leads ? +(v.sales / v.leads * 100).toFixed(1) : 0 }))
    .filter(s => s.sales > 0)
    .sort((a, b) => b.revenue - a.revenue).slice(0, 10)

  // Top 20 sales by revenue
  const topDeals = salesRows
    .map(r => ({ name: r.lead_name || r.company_name || '-', company: r.company_name || '-', owner: r.deal_owner || '-', revenue: parseFloat(String(r.annual_revenue ?? '').replace(/,/g, '')) || 0, pitched: parseFloat(String(r.price_pitched ?? '').replace(/,/g, '')) || 0, date: r.sale_done_date || r.user_date || '-', region: r.state_mobile || r.region || '-', source: r.lead_source || '-' }))
    .sort((a, b) => b.revenue - a.revenue).slice(0, 20)

  // Key insights
  const topRegion = regionData[0]
  const topOwner = ownerRevData[0]
  const bestSourceRev = srcRevData[0]
  const recentMonth = monthlyRevTrend[monthlyRevTrend.length - 1]
  const prevMonth = monthlyRevTrend[monthlyRevTrend.length - 2]
  const momGrowth = recentMonth && prevMonth && prevMonth.revenue > 0 ? ((recentMonth.revenue - prevMonth.revenue) / prevMonth.revenue * 100) : null

  return (
    <div className="space-y-4">
      {/* Sales KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-green-200 bg-green-50 p-3 dark:border-green-500/20 dark:bg-green-500/5">
          <div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-green-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-green-600">Total Revenue</span></div>
          <p className="text-xl font-bold text-green-600">{totalRevenue > 10000000 ? `₹${(totalRevenue / 10000000).toFixed(2)}Cr` : `₹${(totalRevenue / 100000).toFixed(1)}L`}</p>
        </div>
        <div className="rounded-xl border border-purple-200 bg-purple-50 p-3 dark:border-purple-500/20 dark:bg-purple-500/5">
          <div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-purple-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-purple-600">Price Pitched</span></div>
          <p className="text-xl font-bold text-purple-600">{totalPricePitched > 10000000 ? `₹${(totalPricePitched / 10000000).toFixed(2)}Cr` : `₹${(totalPricePitched / 100000).toFixed(1)}L`}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/20 dark:bg-amber-500/5">
          <div className="mb-1 flex items-center gap-1.5"><BarChart2 className="h-3.5 w-3.5 text-amber-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">Avg Deal Size</span></div>
          <p className="text-xl font-bold text-amber-600">₹{(avgDealSize / 100000).toFixed(1)}L</p>
        </div>
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 dark:border-blue-500/20 dark:bg-blue-500/5">
          <div className="mb-1 flex items-center gap-1.5"><TrendingUp className="h-3.5 w-3.5 text-blue-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-blue-600">Total Sales</span></div>
          <p className="text-xl font-bold text-blue-600">{totalSales.toLocaleString()}</p>
        </div>
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-3 dark:border-indigo-500/20 dark:bg-indigo-500/5">
          <div className="mb-1 flex items-center gap-1.5"><Target className="h-3.5 w-3.5 text-indigo-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-indigo-600">Conversion</span></div>
          <p className="text-xl font-bold text-indigo-600">{conversionRate.toFixed(2)}%</p>
        </div>
        <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-3 dark:border-cyan-500/20 dark:bg-cyan-500/5">
          <div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-cyan-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-cyan-600">Pipeline Value</span></div>
          <p className="text-xl font-bold text-cyan-600">{allRevenue > 10000000 ? `₹${(allRevenue / 10000000).toFixed(2)}Cr` : `₹${(allRevenue / 100000).toFixed(1)}L`}</p>
        </div>
      </div>

      {/* Key Insights */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {topRegion && <SmartCard title="Top Revenue Region" metric={topRegion.name} desc={`₹${(topRegion.revenue / 100000).toFixed(1)}L from ${topRegion.sales} sales`} meta={`${topRegion.convRate}% conversion • ${topRegion.leads} total leads`} />}
        {topOwner && <SmartCard title="Top Revenue Closer" metric={topOwner.name} desc={`₹${(topOwner.revenue / 100000).toFixed(1)}L from ${topOwner.sales} sales`} meta={`Avg deal: ₹${(topOwner.avgDeal / 100000).toFixed(1)}L • ${topOwner.convRate}% conv`} />}
        {bestSourceRev && <SmartCard title="Best Revenue Source" metric={bestSourceRev.name} desc={`₹${bestSourceRev.revenue}L from ${bestSourceRev.sales} sales`} meta={`${bestSourceRev.convRate}% conversion • ${bestSourceRev.leads} leads`} />}
        {momGrowth !== null && (
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-800/50">
            <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400">Month-over-Month</h4>
            <div className="my-1 flex items-center gap-2">
              <p className="text-lg font-bold text-zinc-800 dark:text-white">{Math.abs(momGrowth).toFixed(1)}%</p>
              {momGrowth >= 0 ? <ArrowUpRight className="h-5 w-5 text-green-500" /> : <ArrowDownRight className="h-5 w-5 text-red-500" />}
            </div>
            <p className="text-xs text-zinc-500">{recentMonth?.month}: ₹{recentMonth?.revenue}L vs {prevMonth?.month}: ₹{prevMonth?.revenue}L</p>
            <p className="mt-1 text-[10px] text-zinc-400">Revenue trend</p>
          </div>
        )}
      </div>

      {/* Revenue Trend */}
      {monthlyRevTrend.length > 1 && (
        <Card title="Monthly Revenue Trend (₹ Lakhs)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyRevTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="month" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`₹${v}L`, '']} />
              <Bar dataKey="revenue" name="Revenue (₹L)" fill="#22c55e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="pitched" name="Pitched (₹L)" fill="#a855f7" radius={[4, 4, 0, 0]} />
              <Legend />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Monthly sales count + revenue line */}
      {monthlyRevTrend.length > 1 && (
        <Card title="Monthly Sales Count">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={monthlyRevTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="month" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="sales" name="Sales Count" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Region Revenue */}
        <Card title="Revenue by Region (₹ Lakhs)">
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={regionData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`₹${v.toLocaleString()}`, '']} />
              <Bar dataKey="revenue" name="Revenue" fill="#22c55e" radius={[0, 4, 4, 0]}>
                {regionData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Source Revenue */}
        <Card title="Revenue by Lead Source (₹ Lakhs)">
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={srcRevData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`₹${v}L`, '']} />
              <Bar dataKey="revenue" name="Revenue (₹L)" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Deal Owner Revenue Performance */}
      <Card title="Deal Owner Revenue Performance (₹ Lakhs)">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={topOwnerChart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={(v: number, n: string) => [n === 'revenue' ? `₹${v}L` : v, '']} />
            <Bar dataKey="revenue" name="Revenue (₹L)" fill="#22c55e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="sales" name="Sales Count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Legend />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Region Performance Table */}
      <Card title="Region Sales Performance">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:border-zinc-700">
              <th className="py-2 pr-3">Region</th><th className="py-2 pr-2">Leads</th><th className="py-2 pr-2">Sales</th><th className="py-2 pr-2">Conv %</th><th className="py-2 pr-2">Revenue</th><th className="py-2 pr-2">Pitched</th><th className="py-2">Avg/Sale</th>
            </tr></thead>
            <tbody>
              {regionData.map(r => (
                <tr key={r.name} className="border-b border-zinc-100 dark:border-zinc-800">
                  <td className="py-2 pr-3 font-medium">{r.name}</td>
                  <td className="py-2 pr-2">{r.leads.toLocaleString()}</td>
                  <td className="py-2 pr-2">{r.sales.toLocaleString()}</td>
                  <td className="py-2 pr-2"><Badge color={r.convRate > 5 ? 'green' : r.convRate > 2 ? 'amber' : 'red'}>{r.convRate}%</Badge></td>
                  <td className="py-2 pr-2 font-semibold text-green-600">₹{(r.revenue / 100000).toFixed(1)}L</td>
                  <td className="py-2 pr-2 text-purple-600">₹{(r.pitched / 100000).toFixed(1)}L</td>
                  <td className="py-2 text-zinc-500">{r.sales ? `₹${(r.revenue / r.sales / 100000).toFixed(1)}L` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Deal Owner Revenue Table */}
      <Card title="Deal Owner Revenue Leaderboard">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:border-zinc-700">
              <th className="py-2 pr-3">#</th><th className="py-2 pr-3">Deal Owner</th><th className="py-2 pr-2">Leads</th><th className="py-2 pr-2">Sales</th><th className="py-2 pr-2">Conv %</th><th className="py-2 pr-2">Revenue</th><th className="py-2 pr-2">Pitched</th><th className="py-2">Avg Deal</th>
            </tr></thead>
            <tbody>
              {ownerRevData.slice(0, 20).map((o, i) => (
                <tr key={o.name} className="border-b border-zinc-100 dark:border-zinc-800">
                  <td className="py-2 pr-3">{i < 3 ? <Crown className={`inline h-3.5 w-3.5 ${i === 0 ? 'text-amber-500' : i === 1 ? 'text-zinc-400' : 'text-amber-700'}`} /> : i + 1}</td>
                  <td className="py-2 pr-3 font-medium">{o.name}</td>
                  <td className="py-2 pr-2">{o.leads.toLocaleString()}</td>
                  <td className="py-2 pr-2">{o.sales.toLocaleString()}</td>
                  <td className="py-2 pr-2"><Badge color={o.convRate > 5 ? 'green' : o.convRate > 2 ? 'amber' : 'red'}>{o.convRate}%</Badge></td>
                  <td className="py-2 pr-2 font-semibold text-green-600">₹{(o.revenue / 100000).toFixed(1)}L</td>
                  <td className="py-2 pr-2 text-purple-600">₹{(o.pitched / 100000).toFixed(1)}L</td>
                  <td className="py-2 text-zinc-500">₹{(o.avgDeal / 100000).toFixed(1)}L</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Top Deals */}
      {topDeals.length > 0 && (
        <Card title="Top 20 Deals by Revenue">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead><tr className="border-b border-zinc-200 text-[10px] font-semibold uppercase tracking-wide text-zinc-400 dark:border-zinc-700">
                <th className="py-2 pr-3">#</th><th className="py-2 pr-3">Name</th><th className="py-2 pr-3">Company</th><th className="py-2 pr-2">Revenue</th><th className="py-2 pr-2">Pitched</th><th className="py-2 pr-2">Owner</th><th className="py-2 pr-2">Region</th><th className="py-2 pr-2">Source</th><th className="py-2">Date</th>
              </tr></thead>
              <tbody>
                {topDeals.map((d, i) => (
                  <tr key={i} className="border-b border-zinc-100 dark:border-zinc-800">
                    <td className="py-2 pr-3 font-bold text-amber-500">{i + 1}</td>
                    <td className="py-2 pr-3 font-medium">{d.name}</td>
                    <td className="py-2 pr-3 text-zinc-500">{d.company}</td>
                    <td className="py-2 pr-2 font-semibold text-green-600">₹{(d.revenue / 100000).toFixed(1)}L</td>
                    <td className="py-2 pr-2 text-purple-600">₹{(d.pitched / 100000).toFixed(1)}L</td>
                    <td className="py-2 pr-2 text-zinc-500">{d.owner}</td>
                    <td className="py-2 pr-2 text-zinc-500">{d.region}</td>
                    <td className="py-2 pr-2 text-zinc-500">{d.source}</td>
                    <td className="py-2 text-zinc-400">{d.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
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

// ---- SUMMARY DASHBOARD (renders from pre-computed Supabase data) ----
function SummaryDashboard({ summary, activeTab, setActiveTab, onUpload, onClear }: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  summary: any; activeTab: Tab; setActiveTab: (t: Tab) => void; onUpload: () => void; onClear: () => void
}) {
  const k = summary.kpis || {}
  const charts = summary.charts || {}
  const ins = summary.insights || {}
  const team = summary.team_data || {}
  const src = summary.source_data || {}
  const aging = summary.aging_data || {}
  const trends = summary.trend_data || []
  const dd = summary.deep_dive || {}

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white">Sales Intelligence Dashboard</h1>
          <p className="text-sm text-zinc-500">
            {(k.total || 0).toLocaleString()} leads &middot; Updated: {summary.updated_at ? new Date(summary.updated_at).toLocaleString() : 'N/A'}
            <span className="ml-2 text-xs text-green-600">Saved in database</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onUpload} className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:border-amber-500 hover:text-amber-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
            <Upload className="h-3.5 w-3.5" /> Upload New File
          </button>
          <button onClick={onClear} className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-500 hover:border-red-400 hover:text-red-500 dark:border-zinc-700 dark:bg-zinc-800">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9">
        {[
          { label: 'Total Leads', value: k.total || 0, color: 'text-blue-500', icon: Users },
          { label: 'Demo Booked', value: k.demo_booked || 0, color: 'text-cyan-500', icon: Phone },
          { label: 'Demo Done', value: k.demo_done || 0, color: 'text-purple-500', icon: Target },
          { label: 'Sales Done', value: k.sale_done || 0, color: 'text-green-500', icon: TrendingUp },
          { label: 'Purchased', value: k.purchased || 0, color: 'text-amber-500', icon: Award },
          { label: 'Priority', value: k.priority || 0, color: 'text-pink-500', icon: Flame },
          { label: 'Prospects', value: k.prospects || 0, color: 'text-indigo-500', icon: Target },
          { label: 'Qualified', value: k.qualified || 0, color: 'text-red-500', icon: Award },
          { label: 'Key Companies', value: k.important_companies || 0, color: 'text-blue-500', icon: Building2 },
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

      <div className="flex gap-0 border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${activeTab === tab ? 'border-amber-500 text-amber-600' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}>{tab}</button>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <div className="space-y-4">
          <InsightBox title="Conversion Funnel">Demo conversion: <strong>{ins.demo_rate || 0}%</strong>, Sale rate: <strong>{ins.sale_rate || 0}%</strong>. {ins.top_source && <>Top source: <strong>{ins.top_source.name}</strong> ({ins.top_source.value?.toLocaleString()} leads).</>}</InsightBox>
          {(ins.stale_30 || 0) > 0 && <InsightBox title="Action Required"><strong>{ins.stale_30?.toLocaleString()}</strong> active leads untouched 30+ days.</InsightBox>}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <SmartCard title="Demo Backlog" metric={`${(ins.booked_not_done || 0).toLocaleString()}`} desc="Booked but not done" meta="Push owners to complete" />
            {ins.best_source && <SmartCard title="Best Source" metric={ins.best_source.name} desc={`${ins.best_source.rate}% from ${ins.best_source.total?.toLocaleString()}`} meta="Scale this" />}
            {ins.top_closer && <SmartCard title="Top Closer" metric={ins.top_closer.name} desc={`${ins.top_closer.rate}% over ${ins.top_closer.total?.toLocaleString()}`} meta="Share practices" />}
            <SmartCard title="Stale Leads" metric={`${(ins.stale_30 || 0).toLocaleString()}`} desc="30+ days untouched" meta="Assign immediately" />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Lead Status"><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={charts.status || []} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={110}>{(charts.status || []).map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></Card>
            <Card title="Top Sources"><ResponsiveContainer width="100%" height={300}><BarChart data={charts.source || []} layout="vertical" margin={{ left: 20 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></Card>
          </div>
          <Card title="Conversion Funnel"><div className="space-y-2 py-2">{(charts.funnel || []).map((s: { label: string; value: number }, i: number) => (<div key={s.label} className="flex items-center gap-3"><span className="w-28 text-right text-xs font-medium text-zinc-500">{s.label}</span><div className="h-9 rounded-lg flex items-center px-3 text-xs font-bold text-white" style={{ width: `${k.total ? Math.max(8, s.value / k.total * 100) : 0}%`, background: COLORS[i], minWidth: 60 }}>{s.value.toLocaleString()}</div><span className="text-xs text-zinc-400">{pct(s.value, k.total)}</span></div>))}</div></Card>
        </div>
      )}

      {activeTab === 'Team' && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{(team.managers || []).map((m: { name: string; total: number; demos: number; sales: number; priority: number }) => (<Card key={m.name} title={m.name}><div className="space-y-2 text-sm"><div className="flex justify-between"><span className="text-zinc-500">Total</span><span className="font-semibold text-blue-500">{m.total.toLocaleString()}</span></div><div className="flex justify-between"><span className="text-zinc-500">Sales</span><span className="font-semibold text-green-500">{m.sales.toLocaleString()} ({pct(m.sales, m.total)})</span></div><div className="flex justify-between"><span className="text-zinc-500">Priority</span><span className="font-semibold text-amber-500">{m.priority}</span></div></div></Card>))}</div>
          <Card title="Team Leaderboard"><div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-[10px] font-semibold uppercase text-zinc-400"><th className="py-2 pr-3">Deal Owner</th><th className="py-2 pr-3">Manager</th><th className="py-2 pr-2">Total</th><th className="py-2 pr-2">Sales</th><th className="py-2 pr-2">Conv %</th><th className="py-2">Stale</th></tr></thead><tbody>{(team.owners || []).map((o: { name: string; manager: string; total: number; sales: number; stale: number }) => (<tr key={o.name} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-2 pr-3 font-medium">{o.name}</td><td className="py-2 pr-3 text-zinc-500">{o.manager}</td><td className="py-2 pr-2">{o.total.toLocaleString()}</td><td className="py-2 pr-2">{o.sales}</td><td className="py-2 pr-2"><Badge color={o.total ? (o.sales / o.total * 100 > 5 ? 'green' : 'red') : 'zinc'}>{pct(o.sales, o.total)}</Badge></td><td className="py-2">{o.stale > 0 ? <Badge color="red">{o.stale}</Badge> : '0'}</td></tr>))}</tbody></table></div></Card>
        </div>
      )}

      {activeTab === 'Trends' && (
        <div className="space-y-4">
          <Card title="Monthly Leads"><ResponsiveContainer width="100%" height={300}><LineChart data={trends}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis /><Tooltip /><Line type="monotone" dataKey="leads" stroke="#3b82f6" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Monthly Sales"><ResponsiveContainer width="100%" height={280}><BarChart data={trends}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={50} /><YAxis /><Tooltip /><Bar dataKey="sales" fill="#22c55e" radius={[4, 4, 0, 0]} /><Bar dataKey="purchased" fill="#f59e0b" radius={[4, 4, 0, 0]} /><Legend /></BarChart></ResponsiveContainer></Card>
            <Card title="Conversion Rates"><ResponsiveContainer width="100%" height={280}><LineChart data={trends}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis /><Tooltip /><Line type="monotone" dataKey="demoRate" name="Demo %" stroke="#a855f7" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="saleRate" name="Sale %" stroke="#22c55e" strokeWidth={2} dot={false} /><Legend /></LineChart></ResponsiveContainer></Card>
          </div>
        </div>
      )}

      {activeTab === 'Aging' && (
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Lead Age"><ResponsiveContainer width="100%" height={280}><BarChart data={aging.age_dist || []}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value">{(aging.age_dist || []).map((_: unknown, i: number) => <Cell key={i} fill={['#22c55e','#84cc16','#f59e0b','#f97316','#ef4444','#dc2626','#991b1b'][i] || '#666'} />)}</Bar></BarChart></ResponsiveContainer></Card>
            <Card title="Last Touch"><ResponsiveContainer width="100%" height={280}><BarChart data={aging.touch_dist || []}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value">{(aging.touch_dist || []).map((_: unknown, i: number) => <Cell key={i} fill={['#22c55e','#84cc16','#f59e0b','#f97316','#ef4444','#991b1b','#6b7280'][i] || '#666'} />)}</Bar></BarChart></ResponsiveContainer></Card>
          </div>
          <Card title={`Stale Leads (${(aging.stale_leads || []).length})`}><div className="max-h-80 overflow-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-[10px] font-semibold uppercase text-zinc-400"><th className="py-2">Name</th><th className="py-2">Status</th><th className="py-2">Owner</th><th className="py-2">Days</th></tr></thead><tbody>{(aging.stale_leads || []).slice(0, 30).map((r: { name: string; status: string; owner: string; days: number }, i: number) => (<tr key={i} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-1.5 font-medium">{r.name}</td><td><Badge color="amber">{r.status}</Badge></td><td className="text-zinc-500">{r.owner}</td><td><Badge color="red">{r.days}d</Badge></td></tr>))}</tbody></table></div></Card>
        </div>
      )}

      {activeTab === 'Sales' && (() => {
        const sd = summary.sales_data || {}
        const totalRev = sd.total_revenue || 0
        const totalPitched = sd.total_pitched || 0
        const avgDeal = sd.avg_deal || 0
        const totalSalesCount = sd.total_sales || 0
        const convRate = sd.conversion_rate || 0
        const pipelineVal = sd.pipeline_value || 0
        const regionRev = sd.region_revenue || []
        const ownerRev = sd.owner_revenue || []
        const monthlyRev = sd.monthly_revenue || []
        const srcRev = sd.source_revenue || []
        const topDeals = sd.top_deals || []
        const ownerChart = ownerRev.slice(0, 12).map((o: Record<string, unknown>) => ({ name: String(o.name || '').length > 16 ? String(o.name).slice(0, 14) + '..' : o.name, revenue: +((Number(o.revenue) || 0) / 100000).toFixed(1), sales: o.sales }))
        const recentM = monthlyRev[monthlyRev.length - 1]
        const prevM = monthlyRev[monthlyRev.length - 2]
        const momG = recentM && prevM && prevM.revenue > 0 ? ((recentM.revenue - prevM.revenue) / prevM.revenue * 100) : null

        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-xl border border-green-200 bg-green-50 p-3 dark:border-green-500/20 dark:bg-green-500/5"><div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-green-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-green-600">Total Revenue</span></div><p className="text-xl font-bold text-green-600">{totalRev > 10000000 ? `₹${(totalRev / 10000000).toFixed(2)}Cr` : `₹${(totalRev / 100000).toFixed(1)}L`}</p></div>
              <div className="rounded-xl border border-purple-200 bg-purple-50 p-3 dark:border-purple-500/20 dark:bg-purple-500/5"><div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-purple-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-purple-600">Price Pitched</span></div><p className="text-xl font-bold text-purple-600">{totalPitched > 10000000 ? `₹${(totalPitched / 10000000).toFixed(2)}Cr` : `₹${(totalPitched / 100000).toFixed(1)}L`}</p></div>
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/20 dark:bg-amber-500/5"><div className="mb-1 flex items-center gap-1.5"><BarChart2 className="h-3.5 w-3.5 text-amber-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">Avg Deal</span></div><p className="text-xl font-bold text-amber-600">₹{(avgDeal / 100000).toFixed(1)}L</p></div>
              <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 dark:border-blue-500/20 dark:bg-blue-500/5"><div className="mb-1 flex items-center gap-1.5"><TrendingUp className="h-3.5 w-3.5 text-blue-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-blue-600">Total Sales</span></div><p className="text-xl font-bold text-blue-600">{totalSalesCount.toLocaleString()}</p></div>
              <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-3 dark:border-indigo-500/20 dark:bg-indigo-500/5"><div className="mb-1 flex items-center gap-1.5"><Target className="h-3.5 w-3.5 text-indigo-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-indigo-600">Conversion</span></div><p className="text-xl font-bold text-indigo-600">{convRate}%</p></div>
              <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-3 dark:border-cyan-500/20 dark:bg-cyan-500/5"><div className="mb-1 flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-cyan-600" /><span className="text-[10px] font-semibold uppercase tracking-wide text-cyan-600">Pipeline</span></div><p className="text-xl font-bold text-cyan-600">{pipelineVal > 10000000 ? `₹${(pipelineVal / 10000000).toFixed(2)}Cr` : `₹${(pipelineVal / 100000).toFixed(1)}L`}</p></div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {regionRev[0] && <SmartCard title="Top Revenue Region" metric={regionRev[0].name} desc={`₹${(regionRev[0].revenue / 100000).toFixed(1)}L from ${regionRev[0].sales} sales`} meta={`${regionRev[0].convRate}% conv • ${regionRev[0].leads} leads`} />}
              {ownerRev[0] && <SmartCard title="Top Revenue Closer" metric={ownerRev[0].name} desc={`₹${(ownerRev[0].revenue / 100000).toFixed(1)}L from ${ownerRev[0].sales} sales`} meta={`Avg: ₹${(ownerRev[0].avgDeal / 100000).toFixed(1)}L • ${ownerRev[0].convRate}% conv`} />}
              {srcRev[0] && <SmartCard title="Best Revenue Source" metric={srcRev[0].name} desc={`₹${srcRev[0].revenue}L from ${srcRev[0].sales} sales`} meta={`${srcRev[0].convRate}% conv • ${srcRev[0].leads} leads`} />}
              {momG !== null && <SmartCard title="Month-over-Month" metric={`${momG >= 0 ? '+' : ''}${momG.toFixed(1)}%`} desc={`${recentM.month}: ₹${recentM.revenue}L vs ${prevM.month}: ₹${prevM.revenue}L`} meta="Revenue trend" />}
            </div>

            {monthlyRev.length > 1 && <Card title="Monthly Revenue Trend (₹ Lakhs)"><ResponsiveContainer width="100%" height={300}><BarChart data={monthlyRev}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="month" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={50} /><YAxis tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="revenue" name="Revenue (₹L)" fill="#22c55e" radius={[4, 4, 0, 0]} /><Bar dataKey="pitched" name="Pitched (₹L)" fill="#a855f7" radius={[4, 4, 0, 0]} /><Legend /></BarChart></ResponsiveContainer></Card>}

            <div className="grid gap-4 lg:grid-cols-2">
              <Card title="Revenue by Region"><ResponsiveContainer width="100%" height={380}><BarChart data={regionRev.map((r: Record<string, unknown>) => ({ ...r, rev: +((Number(r.revenue) || 0) / 100000).toFixed(1) }))} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" tick={{ fontSize: 10 }} /><YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="rev" name="Revenue (₹L)" fill="#22c55e" radius={[0, 4, 4, 0]}>{regionRev.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Bar></BarChart></ResponsiveContainer></Card>
              <Card title="Revenue by Source"><ResponsiveContainer width="100%" height={380}><BarChart data={srcRev} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis type="number" tick={{ fontSize: 10 }} /><YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="revenue" name="Revenue (₹L)" fill="#6366f1" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></Card>
            </div>

            <Card title="Deal Owner Revenue (₹ Lakhs)"><ResponsiveContainer width="100%" height={320}><BarChart data={ownerChart}><CartesianGrid strokeDasharray="3 3" stroke="#333" /><XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={60} /><YAxis tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="revenue" name="Revenue (₹L)" fill="#22c55e" radius={[4, 4, 0, 0]} /><Bar dataKey="sales" name="Sales" fill="#3b82f6" radius={[4, 4, 0, 0]} /><Legend /></BarChart></ResponsiveContainer></Card>

            <Card title="Region Performance Table"><div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-[10px] font-semibold uppercase text-zinc-400"><th className="py-2 pr-3">Region</th><th className="py-2 pr-2">Leads</th><th className="py-2 pr-2">Sales</th><th className="py-2 pr-2">Conv %</th><th className="py-2 pr-2">Revenue</th><th className="py-2">Avg/Sale</th></tr></thead><tbody>{regionRev.map((r: Record<string, unknown>) => (<tr key={String(r.name)} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-2 pr-3 font-medium">{String(r.name)}</td><td className="py-2 pr-2">{Number(r.leads).toLocaleString()}</td><td className="py-2 pr-2">{Number(r.sales).toLocaleString()}</td><td className="py-2 pr-2"><Badge color={Number(r.convRate) > 5 ? 'green' : Number(r.convRate) > 2 ? 'amber' : 'red'}>{String(r.convRate)}%</Badge></td><td className="py-2 pr-2 font-semibold text-green-600">₹{(Number(r.revenue) / 100000).toFixed(1)}L</td><td className="py-2 text-zinc-500">{Number(r.sales) ? `₹${(Number(r.revenue) / Number(r.sales) / 100000).toFixed(1)}L` : '-'}</td></tr>))}</tbody></table></div></Card>

            {topDeals.length > 0 && <Card title="Top Deals"><div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-[10px] font-semibold uppercase text-zinc-400"><th className="py-2 pr-3">#</th><th className="py-2 pr-3">Name</th><th className="py-2 pr-2">Revenue</th><th className="py-2 pr-2">Owner</th><th className="py-2 pr-2">Region</th><th className="py-2">Date</th></tr></thead><tbody>{topDeals.slice(0, 15).map((d: Record<string, unknown>, i: number) => (<tr key={i} className="border-b border-zinc-100 dark:border-zinc-800"><td className="py-2 pr-3 font-bold text-amber-500">{i + 1}</td><td className="py-2 pr-3 font-medium">{String(d.name)}</td><td className="py-2 pr-2 font-semibold text-green-600">₹{(Number(d.revenue) / 100000).toFixed(1)}L</td><td className="py-2 pr-2 text-zinc-500">{String(d.owner)}</td><td className="py-2 pr-2 text-zinc-500">{String(d.region)}</td><td className="py-2 text-zinc-400">{String(d.date)}</td></tr>))}</tbody></table></div></Card>}
          </div>
        )
      })()}

      {(activeTab === 'Pipeline' || activeTab === 'Sources' || activeTab === 'Deep Dive') && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-center dark:border-amber-500/20 dark:bg-amber-500/5">
          <p className="text-sm text-amber-700 dark:text-amber-400">Upload a fresh CSV for full {activeTab} analytics with filters and deep-dive data.</p>
          <button onClick={onUpload} className="mt-3 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-400">Upload CSV</button>
        </div>
      )}
    </div>
  )
}
