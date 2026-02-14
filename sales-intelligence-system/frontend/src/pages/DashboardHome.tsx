import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Flame,
  Phone,
  IndianRupee,
  Mail,
  Search,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  Target,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { getLeads, getTodayBrief, getAlerts, performLeadAction } from '../lib/api'
import { formatCurrency, formatRelative, getScoreColor, getStageColor, getSeverityColor } from '../lib/utils'
import type { Lead, DailyBrief, Alert } from '../lib/types'
import ScoreBadge from '../components/ui/ScoreBadge'
import { CardSkeleton, TableSkeleton, TextSkeleton } from '../components/ui/LoadingSkeleton'

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
  const [brief, setBrief] = useState<DailyBrief | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [briefLoading, setBriefLoading] = useState(true)
  const [alertsLoading, setAlertsLoading] = useState(true)
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
        setBrief(briefRes.value.data)
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
      setBriefLoading(false)
      setAlertsLoading(false)
    }
  }

  async function handleAction(leadId: string, action: string) {
    try {
      await performLeadAction(leadId, action)
    } catch (err) {
      console.error('Action failed:', err)
    }
  }

  const firstName = user?.full_name?.split(' ')[0] || 'there'
  const totalLeads = leads.length
  const hotLeads = leads.filter((l: any) => {
    const score = l.score?.overall_score ?? l.overall_score ?? 0
    return score >= 80
  }).length
  const pipelineValue = leads.reduce((sum, l) => sum + (l.deal_value || 0), 0)
  const briefContent = brief?.content as Record<string, any> | undefined
  const callsToday = briefContent?.calls_scheduled ?? briefContent?.calls_today ?? 0
  const topPriorityLeads = leads.slice(0, 5)

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => {
              setError(null)
              setLoading(true)
              fetchDashboardData()
            }}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {getGreeting()}, {firstName}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Here's your sales intelligence for today
        </p>
      </div>

      {/* Summary Cards */}
      {loading ? (
        <CardSkeleton count={4} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            icon={<Users className="w-5 h-5 text-blue-600" />}
            label="My Leads"
            value={totalLeads.toString()}
            trend={{ value: '+3 this week', up: true }}
            bgColor="bg-blue-50"
          />
          <SummaryCard
            icon={<Flame className="w-5 h-5 text-orange-600" />}
            label="Hot Leads"
            value={hotLeads.toString()}
            trend={{ value: 'Score >= 80', up: true }}
            bgColor="bg-orange-50"
          />
          <SummaryCard
            icon={<Phone className="w-5 h-5 text-green-600" />}
            label="Calls Today"
            value={callsToday.toString()}
            trend={{ value: 'Scheduled', up: false }}
            bgColor="bg-green-50"
          />
          <SummaryCard
            icon={<IndianRupee className="w-5 h-5 text-purple-600" />}
            label="Pipeline Value"
            value={formatCurrency(pipelineValue)}
            trend={{ value: 'Total active', up: true }}
            bgColor="bg-purple-50"
          />
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Brief + Priority Calls */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Brief */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                Today's Brief
              </h2>
              {brief && (
                <span className="text-xs text-gray-400">
                  {brief.lead_count} leads analyzed
                </span>
              )}
            </div>
            {briefLoading ? (
              <TextSkeleton lines={4} />
            ) : brief && briefContent ? (
              <div className="space-y-4">
                {/* Key Insights */}
                {briefContent.insights && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Key Insights</h3>
                    <ul className="space-y-1.5">
                      {(Array.isArray(briefContent.insights)
                        ? briefContent.insights
                        : [briefContent.insights]
                      ).map((insight: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                          <Target className="w-3.5 h-3.5 text-blue-500 mt-0.5 shrink-0" />
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {/* Suggested Actions */}
                {briefContent.suggested_actions && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Suggested Actions</h3>
                    <ul className="space-y-1.5">
                      {(Array.isArray(briefContent.suggested_actions)
                        ? briefContent.suggested_actions
                        : [briefContent.suggested_actions]
                      ).map((action: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                          <ChevronRight className="w-3.5 h-3.5 text-green-500 mt-0.5 shrink-0" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {/* Top Priority Leads from Brief */}
                {briefContent.top_priorities && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Top Priorities</h3>
                    <ul className="space-y-1.5">
                      {(Array.isArray(briefContent.top_priorities)
                        ? briefContent.top_priorities
                        : [briefContent.top_priorities]
                      ).map((priority: any, idx: number) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                          <Flame className="w-3.5 h-3.5 text-orange-500 mt-0.5 shrink-0" />
                          {typeof priority === 'string'
                            ? priority
                            : priority.company || priority.name || JSON.stringify(priority)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Lightbulb className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">
                  {brief === null ? 'Brief generating...' : 'No brief for today'}
                </p>
              </div>
            )}
          </div>

          {/* Priority Call List */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Phone className="w-5 h-5 text-green-600" />
                Priority Call List
              </h2>
            </div>
            {loading ? (
              <div className="p-4">
                <TableSkeleton rows={5} cols={6} />
              </div>
            ) : topPriorityLeads.length === 0 ? (
              <div className="text-center py-10">
                <Users className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No priority leads right now</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <th className="px-4 py-3 w-12">#</th>
                      <th className="px-4 py-3">Company</th>
                      <th className="px-4 py-3">Contact</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Deal Value</th>
                      <th className="px-4 py-3">Stage</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {topPriorityLeads.map((lead, idx) => {
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
                          <td className="px-4 py-3 text-gray-400 font-medium">
                            {idx + 1}
                          </td>
                          <td className="px-4 py-3 font-medium text-gray-900">
                            {lead.company_name}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {lead.contact_name}
                          </td>
                          <td className="px-4 py-3">
                            <ScoreBadge score={score} size="sm" />
                          </td>
                          <td className="px-4 py-3 text-gray-700 font-medium">
                            {formatCurrency(lead.deal_value)}
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
                            <div className="flex items-center gap-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleAction(lead.id, 'call')
                                }}
                                className="p-1.5 rounded-lg hover:bg-green-50 text-green-600 transition-colors"
                                title="Call"
                              >
                                <Phone className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleAction(lead.id, 'email')
                                }}
                                className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 transition-colors"
                                title="Email"
                              >
                                <Mail className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  navigate(`/leads/${lead.id}`)
                                }}
                                className="p-1.5 rounded-lg hover:bg-purple-50 text-purple-600 transition-colors"
                                title="Research"
                              >
                                <Search className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Alerts */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
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
            {alertsLoading ? (
              <TextSkeleton lines={6} />
            ) : alerts.length === 0 ? (
              <div className="text-center py-8">
                <AlertTriangle className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No recent alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() =>
                      alert.lead_id && navigate(`/leads/${alert.lead_id}`)
                    }
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${getSeverityColor(
                          alert.severity
                        )}`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-[10px] text-gray-400 shrink-0">
                        {formatRelative(alert.created_at)}
                      </span>
                    </div>
                    <h4 className="text-sm font-medium text-gray-900 mb-0.5">
                      {alert.title}
                    </h4>
                    <p className="text-xs text-gray-500 leading-relaxed">
                      {alert.message}
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

/* --- Summary Card Sub-Component --- */

interface SummaryCardProps {
  icon: React.ReactNode
  label: string
  value: string
  trend: { value: string; up: boolean }
  bgColor: string
}

function SummaryCard({ icon, label, value, trend, bgColor }: SummaryCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <span
          className={`inline-flex items-center justify-center w-9 h-9 rounded-lg ${bgColor}`}
        >
          {icon}
        </span>
        <div className="flex items-center gap-1 text-xs">
          {trend.up ? (
            <TrendingUp className="w-3 h-3 text-green-500" />
          ) : (
            <TrendingDown className="w-3 h-3 text-gray-400" />
          )}
          <span className={trend.up ? 'text-green-600' : 'text-gray-400'}>
            {trend.value}
          </span>
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  )
}
