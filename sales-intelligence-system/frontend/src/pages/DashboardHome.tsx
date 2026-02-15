import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Flame,
  Phone,
  IndianRupee,
  AlertTriangle,
  Lightbulb,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { getLeads, getTodayBrief, getAlerts } from '../lib/api'
import { formatCurrency, formatRelative, getStageColor, getSeverityColor } from '../lib/utils'
import type { Lead, Alert } from '../lib/types'
import ScoreBadge from '../components/ui/ScoreBadge'

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardHome() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [leads, setLeads] = useState<Lead[]>([])
  const [briefData, setBriefData] = useState<any>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  async function fetchDashboardData() {
    try {
      const [leadsRes, briefRes, alertsRes] = await Promise.allSettled([
        getLeads({ sort_by: 'score', limit: '50' }),
        getTodayBrief(),
        getAlerts({ limit: '3' }),
      ])

      if (leadsRes.status === 'fulfilled') {
        const data = leadsRes.value.data
        setLeads(data?.leads || (Array.isArray(data) ? data : []))
      }
      if (briefRes.status === 'fulfilled') {
        setBriefData(briefRes.value.data)
      }
      if (alertsRes.status === 'fulfilled') {
        const alertData = alertsRes.value.data?.alerts || alertsRes.value.data || []
        setAlerts(Array.isArray(alertData) ? alertData : [])
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const displayName = user?.full_name || user?.name || user?.email || 'there'
  const firstName = displayName.split(' ')[0]
  const totalLeads = leads.length
  const hotLeads = leads.filter((l: any) =>
    l.score === 'hot' || (typeof l.score_numeric === 'number' && l.score_numeric >= 80)
  ).length
  const pipelineValue = leads.reduce((sum, l) => sum + (l.deal_value || 0), 0)
  const topLeads = leads.slice(0, 8)
  const brief = briefData?.brief
  const briefContent = brief?.brief_content || brief?.content

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => { setError(null); setLoading(true); fetchDashboardData() }}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-full overflow-hidden">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {getGreeting()}, {firstName}
        </h1>
        <p className="text-sm text-gray-500 mt-1">Here's your sales intelligence for today</p>
      </div>

      {/* Summary Cards */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
              <div className="h-8 w-8 bg-gray-200 rounded-lg mb-3" />
              <div className="h-6 w-16 bg-gray-200 rounded mb-1" />
              <div className="h-3 w-20 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard
            icon={<Users className="w-5 h-5 text-blue-600" />}
            bg="bg-blue-50"
            label="My Leads"
            value={totalLeads}
          />
          <StatCard
            icon={<Flame className="w-5 h-5 text-orange-600" />}
            bg="bg-orange-50"
            label="Hot Leads"
            value={hotLeads}
          />
          <StatCard
            icon={<Phone className="w-5 h-5 text-green-600" />}
            bg="bg-green-50"
            label="Calls Today"
            value={0}
          />
          <StatCard
            icon={<IndianRupee className="w-5 h-5 text-purple-600" />}
            bg="bg-purple-50"
            label="Pipeline Value"
            value={formatCurrency(pipelineValue)}
          />
        </div>
      )}

      {/* Main Grid: Left = Brief + Leads, Right = Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Brief */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <h2 className="text-base font-semibold text-gray-900">Today's Brief</h2>
            </div>
            {briefContent ? (
              <p className="text-sm text-gray-600 leading-relaxed">
                {typeof briefContent === 'string' ? briefContent : 'Brief generated. Check Briefs page for details.'}
              </p>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">No brief for today</p>
            )}
          </div>

          {/* Priority Call List */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <Phone className="w-5 h-5 text-green-600" />
                Priority Call List
              </h2>
              <button
                onClick={() => navigate('/leads')}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5"
              >
                View all <ChevronRight className="w-3 h-3" />
              </button>
            </div>

            {loading ? (
              <div className="p-6 space-y-3">
                {[1,2,3].map(i => (
                  <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : topLeads.length === 0 ? (
              <div className="text-center py-10">
                <Users className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No leads yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {topLeads.map((lead, idx) => {
                  const company = (lead as any).company_name || (lead as any).company || 'Unknown'
                  const contact = (lead as any).contact_name || ''
                  const scoreVal = (lead as any).score ?? (lead as any).score_numeric ?? null
                  return (
                    <div
                      key={lead.id}
                      className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/leads/${lead.id}`)}
                    >
                      {/* Rank */}
                      <span className="text-xs font-medium text-gray-400 w-5 text-center shrink-0">
                        {idx + 1}
                      </span>

                      {/* Company + Contact */}
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">{company}</p>
                        {contact && (
                          <p className="text-xs text-gray-500 truncate">{contact}</p>
                        )}
                      </div>

                      {/* Score */}
                      <div className="shrink-0">
                        <ScoreBadge score={scoreVal} size="sm" />
                      </div>

                      {/* Deal value */}
                      <span className="text-sm font-medium text-gray-700 w-20 text-right shrink-0">
                        {formatCurrency(lead.deal_value || 0)}
                      </span>

                      {/* Stage */}
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium capitalize shrink-0 ${getStageColor(lead.stage)}`}
                      >
                        {lead.stage?.replace('_', ' ')}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Alerts */}
        <div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Recent Alerts
              </h2>
              <button
                onClick={() => navigate('/alerts')}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                View All
              </button>
            </div>

            {alerts.length === 0 ? (
              <div className="text-center py-8">
                <AlertTriangle className="w-10 h-10 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No recent alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => alert.lead_id && navigate(`/leads/${alert.lead_id}`)}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${getSeverityColor(alert.severity || 'low')}`}
                      >
                        {(alert.severity || alert.alert_type || 'info').toString().replace('_', ' ')}
                      </span>
                      <span className="text-[10px] text-gray-400 shrink-0">
                        {formatRelative(alert.created_at || alert.sent_at || new Date().toISOString())}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed line-clamp-2">
                      {alert.message || alert.title || 'New alert'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/* --- Stat Card --- */

interface StatCardProps {
  icon: React.ReactNode
  bg: string
  label: string
  value: number | string
}

function StatCard({ icon, bg, label, value }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className={`inline-flex items-center justify-center w-9 h-9 rounded-lg ${bg} mb-3`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
