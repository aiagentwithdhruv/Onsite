export type Role = 'rep' | 'team_lead' | 'manager' | 'founder' | 'admin'

export interface User {
  id: string
  auth_id?: string
  email: string
  name: string
  role: Role
  team: string | null
  is_active: boolean
}

export interface Lead {
  id: string
  zoho_lead_id: string | null
  company: string | null
  contact_name: string | null
  email: string | null
  phone: string | null
  source: string | null
  stage: string
  deal_value: number | null
  industry: string | null
  geography: string | null
  assigned_rep_id: string | null
  last_activity_at: string | null
  created_at: string
  updated_at: string
  // Joined fields
  score?: string | null
  score_numeric?: number | null
}

export interface LeadScore {
  id: string
  lead_id: string
  score: 'hot' | 'warm' | 'cold'
  score_numeric: number
  score_reason: string
  priority_rank: number | null
  model_used: string
  scored_at: string
}

export interface LeadNote {
  id: string
  lead_id: string
  zoho_note_id: string | null
  note_text: string
  note_source: 'zoho' | 'manual' | 'ai_generated'
  created_by: string | null
  note_date: string | null
}

export interface LeadActivity {
  id: string
  lead_id: string
  zoho_activity_id: string | null
  activity_type: string
  subject: string | null
  details: string | null
  outcome: string | null
  duration_minutes: number | null
  performed_by: string | null
  activity_date: string
}

export interface LeadResearch {
  id: string
  lead_id: string
  company_info: Record<string, unknown> | null
  web_research: string | null
  notes_summary: string | null
  pain_points: string[] | null
  objections: string[] | null
  close_strategy: string | null
  talking_points: string[] | null
  similar_deals: Record<string, unknown> | null
  pricing_suggestion: string | null
  status: 'in_progress' | 'complete' | 'failed'
  researched_at: string
}

export interface DailyBrief {
  id: string
  rep_id: string
  brief_date: string
  brief_content: string
  priority_list: Record<string, unknown>
  lead_count: number | null
  hot_count: number | null
  stale_count: number | null
  created_at: string
}

export interface Alert {
  id: string
  alert_type: string
  message: string
  target_user_id: string
  lead_id: string | null
  channel: 'whatsapp' | 'email' | 'both'
  sent_at: string
  delivered: boolean
  read_at: string | null
}

export interface LeadDetail extends Lead {
  latest_score: LeadScore | null
  activities: LeadActivity[]
  notes: LeadNote[]
  research: LeadResearch | null
}

export interface PipelineFunnel {
  stage: string
  count: number
}

export interface RepPerformance {
  user_id: string
  name: string
  total_leads: number
  contacted: number
  meetings: number
  won: number
  lost: number
  conversion_rate: number
}

export interface SourceAnalysis {
  source: string
  total_leads: number
  won: number
  lost: number
  conversion_rate: number
}
