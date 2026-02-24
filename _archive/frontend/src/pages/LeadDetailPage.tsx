import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Phone,
  Mail,
  Calendar,
  FileText,
  Building2,
  MapPin,
  Briefcase,
  Globe,
  User,
  Clock,
  IndianRupee,
  Brain,
  Sparkles,
  Loader2,
  X,
  ChevronDown,
  ExternalLink,
  Shield,
} from 'lucide-react'
import {
  getLeadDetail,
  performLeadAction,
  triggerResearch,
  getResearchStatus,
  getResearch,
} from '../lib/api'
import {
  formatCurrency,
  formatDate,
  formatRelative,
  getScoreColor,
  getStageColor,
  cn,
} from '../lib/utils'
import type { LeadDetail, LeadActivity, LeadNote, LeadResearch } from '../lib/types'
import ScoreBadge from '../components/ui/ScoreBadge'
import { TextSkeleton, CardSkeleton } from '../components/ui/LoadingSkeleton'

const ACTIVITY_ICONS: Record<string, typeof Phone> = {
  call: Phone,
  email: Mail,
  meeting: Calendar,
  note: FileText,
}

const NOTE_TYPES = ['General', 'Call Summary', 'Follow-up', 'Objection', 'Decision']
const STAGE_OPTIONS = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [lead, setLead] = useState<LeadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Research state
  const [researchData, setResearchData] = useState<LeadResearch[]>([])
  const [researchLoading, setResearchLoading] = useState(false)
  const [researchPolling, setResearchPolling] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Note modal state
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [noteType, setNoteType] = useState('General')
  const [noteSaving, setNoteSaving] = useState(false)

  // Stage change
  const [showStageDropdown, setShowStageDropdown] = useState(false)

  useEffect(() => {
    if (id) fetchLead()
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [id])

  async function fetchLead() {
    setLoading(true)
    setError(null)
    try {
      const res = await getLeadDetail(id!)
      const data = res.data
      setLead(data)
      setResearchData(data?.research || [])
    } catch (err) {
      console.error('Failed to fetch lead:', err)
      setError('Failed to load lead details')
    } finally {
      setLoading(false)
    }
  }

  async function handleAction(action: string) {
    if (!id) return
    try {
      await performLeadAction(id, action)
      // Refresh lead data after action
      fetchLead()
    } catch (err) {
      console.error('Action failed:', err)
    }
  }

  async function handleStageChange(newStage: string) {
    if (!id) return
    try {
      await performLeadAction(id, 'change_stage', newStage)
      setShowStageDropdown(false)
      fetchLead()
    } catch (err) {
      console.error('Stage change failed:', err)
    }
  }

  async function handleTriggerResearch() {
    if (!id) return
    setResearchLoading(true)
    try {
      await triggerResearch(id)
      setResearchPolling(true)
      // Poll for status every 3 seconds
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await getResearchStatus(id)
          const status = statusRes.data?.status || statusRes.data
          if (status === 'completed' || status === 'done' || status?.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current)
            setResearchPolling(false)
            // Fetch the actual research data
            const resRes = await getResearch(id)
            const resData = resRes.data
            setResearchData(
              Array.isArray(resData) ? resData : resData?.research ? resData.research : [resData]
            )
            setResearchLoading(false)
          } else if (status === 'failed' || status?.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current)
            setResearchPolling(false)
            setResearchLoading(false)
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current)
          setResearchPolling(false)
          setResearchLoading(false)
        }
      }, 3000)
    } catch (err) {
      console.error('Research trigger failed:', err)
      setResearchLoading(false)
    }
  }

  async function handleSaveNote() {
    if (!id || !noteContent.trim()) return
    setNoteSaving(true)
    try {
      await performLeadAction(id, 'add_note', JSON.stringify({ type: noteType, content: noteContent }))
      setShowNoteModal(false)
      setNoteContent('')
      setNoteType('General')
      fetchLead()
    } catch (err) {
      console.error('Note save failed:', err)
    } finally {
      setNoteSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gray-200 animate-pulse" />
          <div className="h-7 w-48 rounded bg-gray-200 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <CardSkeleton count={1} />
            <TextSkeleton lines={8} />
          </div>
          <div className="space-y-6">
            <CardSkeleton count={1} />
            <TextSkeleton lines={5} />
          </div>
        </div>
      </div>
    )
  }

  if (error || !lead) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600">{error || 'Lead not found'}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const score = lead.score
  const latestResearch = researchData.length > 0 ? researchData[0] : null
  const researchContent = latestResearch?.content as Record<string, any> | undefined

  return (
    <div className="space-y-6">
      {/* Back Button + Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <button
            onClick={() => navigate(-1)}
            className="mt-1 p-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-gray-500" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{lead.company_name}</h1>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
              <span className="text-sm text-gray-600">{lead.contact_name}</span>
              {lead.contact_email && (
                <a
                  href={`mailto:${lead.contact_email}`}
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                >
                  <Mail className="w-3.5 h-3.5" />
                  {lead.contact_email}
                </a>
              )}
              {lead.contact_phone && (
                <a
                  href={`tel:${lead.contact_phone}`}
                  className="inline-flex items-center gap-1 text-sm text-green-600 hover:text-green-800"
                >
                  <Phone className="w-3.5 h-3.5" />
                  {lead.contact_phone}
                </a>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Stage Badge with Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowStageDropdown(!showStageDropdown)}
              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium capitalize ${getStageColor(
                lead.stage
              )}`}
            >
              {lead.stage}
              <ChevronDown className="w-3 h-3" />
            </button>
            {showStageDropdown && (
              <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg border border-gray-200 shadow-lg z-20 py-1">
                {STAGE_OPTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleStageChange(s)}
                    className={cn(
                      'w-full text-left px-3 py-1.5 text-sm capitalize hover:bg-gray-50 transition-colors',
                      s === lead.stage ? 'font-medium text-blue-600' : 'text-gray-700'
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
          {score && <ScoreBadge score={score.overall_score} size="md" />}
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Info Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Lead Information</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <InfoItem
                icon={<IndianRupee className="w-4 h-4 text-purple-500" />}
                label="Deal Value"
                value={formatCurrency(lead.deal_value)}
              />
              <InfoItem
                icon={<Building2 className="w-4 h-4 text-blue-500" />}
                label="Industry"
                value={lead.industry || '-'}
              />
              <InfoItem
                icon={<MapPin className="w-4 h-4 text-red-500" />}
                label="Region"
                value={lead.region || '-'}
              />
              <InfoItem
                icon={<Briefcase className="w-4 h-4 text-amber-500" />}
                label="Project Type"
                value={lead.project_type || '-'}
              />
              <InfoItem
                icon={<Globe className="w-4 h-4 text-teal-500" />}
                label="Source"
                value={lead.source?.replace('_', ' ') || '-'}
              />
              <InfoItem
                icon={<User className="w-4 h-4 text-indigo-500" />}
                label="Assigned To"
                value={lead.assigned_rep_name || lead.assigned_to || '-'}
              />
              <InfoItem
                icon={<Clock className="w-4 h-4 text-gray-500" />}
                label="Created"
                value={formatDate(lead.created_at)}
              />
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Activity Timeline</h2>
            {lead.recent_activities && lead.recent_activities.length > 0 ? (
              <div className="space-y-0">
                {lead.recent_activities.map((activity, idx) => (
                  <ActivityItem
                    key={activity.id}
                    activity={activity}
                    isLast={idx === lead.recent_activities.length - 1}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Clock className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No activities recorded yet</p>
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900">Notes</h2>
              <button
                onClick={() => setShowNoteModal(true)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                + Add Note
              </button>
            </div>
            {lead.recent_notes && lead.recent_notes.length > 0 ? (
              <div className="space-y-3">
                {lead.recent_notes.map((note) => (
                  <NoteCard key={note.id} note={note} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No notes yet</p>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: 1/3 */}
        <div className="space-y-6">
          {/* AI Score Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              AI Score
            </h2>
            {score ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <ScoreBadge score={score.overall_score} size="lg" />
                </div>
                <div className="space-y-3">
                  <ScoreBar label="Engagement" value={score.engagement_score} />
                  <ScoreBar label="Fit" value={score.fit_score} />
                  <ScoreBar label="Timing" value={score.timing_score} />
                </div>
                {score.scoring_reason && (
                  <div className="mt-3 p-3 rounded-lg bg-gray-50 border border-gray-100">
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {score.scoring_reason}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <Brain className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">Score not yet calculated</p>
              </div>
            )}
          </div>

          {/* Research Intel Card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Research Intel
            </h2>
            {researchLoading || researchPolling ? (
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-3" />
                <p className="text-sm text-gray-500">Generating intel...</p>
                <p className="text-xs text-gray-400 mt-1">This may take a moment</p>
              </div>
            ) : latestResearch && researchContent ? (
              <div className="space-y-3">
                {researchContent.company_info && (
                  <ResearchSection title="Company" content={researchContent.company_info} />
                )}
                {researchContent.market_intel && (
                  <ResearchSection title="Market Intel" content={researchContent.market_intel} />
                )}
                {researchContent.key_contacts && (
                  <ResearchSection title="Key Contacts" content={researchContent.key_contacts} />
                )}
                {researchContent.strategy && (
                  <ResearchSection title="Strategy" content={researchContent.strategy} />
                )}
                {researchContent.summary && (
                  <ResearchSection title="Summary" content={researchContent.summary} />
                )}
                {/* Confidence + Sources */}
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span className="flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      Confidence: {Math.round(latestResearch.confidence_score * 100)}%
                    </span>
                    <span>{formatDate(latestResearch.created_at)}</span>
                  </div>
                  {latestResearch.sources && latestResearch.sources.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-gray-500">Sources:</p>
                      {latestResearch.sources.map((src, idx) => (
                        <a
                          key={idx}
                          href={src}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700 truncate"
                        >
                          <ExternalLink className="w-3 h-3 shrink-0" />
                          {src}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Sparkles className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400 mb-3">No research data yet</p>
                <button
                  onClick={handleTriggerResearch}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  Generate Intel
                </button>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-2">
              <ActionButton
                icon={<Phone className="w-4 h-4" />}
                label="Call"
                onClick={() => handleAction('call')}
                color="green"
              />
              <ActionButton
                icon={<Mail className="w-4 h-4" />}
                label="Email"
                onClick={() => handleAction('email')}
                color="blue"
              />
              <ActionButton
                icon={<FileText className="w-4 h-4" />}
                label="Add Note"
                onClick={() => setShowNoteModal(true)}
                color="amber"
              />
              <ActionButton
                icon={<Calendar className="w-4 h-4" />}
                label="Meeting"
                onClick={() => handleAction('meeting')}
                color="purple"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Add Note Modal */}
      {showNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Add Note</h3>
              <button
                onClick={() => setShowNoteModal(false)}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Note Type
                </label>
                <select
                  value={noteType}
                  onChange={(e) => setNoteType(e.target.value)}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
                >
                  {NOTE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content
                </label>
                <textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  rows={5}
                  placeholder="Write your note..."
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-gray-400 resize-none"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowNoteModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveNote}
                  disabled={noteSaving || !noteContent.trim()}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {noteSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Save Note
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* --- Sub-Components --- */

function InfoItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm font-medium text-gray-800 capitalize truncate">{value}</p>
      </div>
    </div>
  )
}

function ActivityItem({
  activity,
  isLast,
}: {
  activity: LeadActivity
  isLast: boolean
}) {
  const Icon = ACTIVITY_ICONS[activity.activity_type] || FileText
  const iconColors: Record<string, string> = {
    call: 'text-green-500 bg-green-50',
    email: 'text-blue-500 bg-blue-50',
    meeting: 'text-purple-500 bg-purple-50',
    note: 'text-gray-500 bg-gray-50',
  }
  const colorClass = iconColors[activity.activity_type] || 'text-gray-500 bg-gray-50'

  return (
    <div className="flex gap-3">
      {/* Timeline line + icon */}
      <div className="flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${colorClass}`}
        >
          <Icon className="w-4 h-4" />
        </div>
        {!isLast && <div className="w-px flex-1 bg-gray-200 my-1" />}
      </div>
      {/* Content */}
      <div className={cn('pb-4 min-w-0', isLast && 'pb-0')}>
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium text-gray-900">{activity.subject}</p>
          <span className="text-[10px] text-gray-400 shrink-0">
            {formatRelative(activity.activity_date)}
          </span>
        </div>
        {activity.description && (
          <p className="text-xs text-gray-500 leading-relaxed">{activity.description}</p>
        )}
      </div>
    </div>
  )
}

function NoteCard({ note }: { note: LeadNote }) {
  return (
    <div className="rounded-lg border border-gray-100 p-3">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-600 capitalize">
            {note.note_type}
          </span>
          <span className="text-[10px] text-gray-400">{note.source}</span>
        </div>
        <span className="text-[10px] text-gray-400">
          {formatRelative(note.created_at)}
        </span>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed">{note.content}</p>
    </div>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 80
      ? 'bg-green-500'
      : value >= 60
      ? 'bg-yellow-500'
      : value >= 40
      ? 'bg-orange-500'
      : 'bg-red-500'

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-800">{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

function ResearchSection({
  title,
  content,
}: {
  title: string
  content: unknown
}) {
  const text =
    typeof content === 'string'
      ? content
      : Array.isArray(content)
      ? content.join(', ')
      : JSON.stringify(content, null, 2)

  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
        {title}
      </h4>
      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  )
}

function ActionButton({
  icon,
  label,
  onClick,
  color,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  color: string
}) {
  const colorClasses: Record<string, string> = {
    green: 'text-green-600 bg-green-50 hover:bg-green-100 border-green-200',
    blue: 'text-blue-600 bg-blue-50 hover:bg-blue-100 border-blue-200',
    amber: 'text-amber-600 bg-amber-50 hover:bg-amber-100 border-amber-200',
    purple: 'text-purple-600 bg-purple-50 hover:bg-purple-100 border-purple-200',
  }

  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
        colorClasses[color] || colorClasses.blue
      }`}
    >
      {icon}
      {label}
    </button>
  )
}
