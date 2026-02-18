export type Role = 'rep' | 'team_lead' | 'manager' | 'founder' | 'admin'

export interface User {
  id: string
  auth_id?: string
  email: string
  name?: string
  full_name?: string  // alias — some components use this
  role: Role
  team: string | null
  is_active: boolean
}

export interface Lead {
  id: string
  zoho_lead_id: string | null
  // DB uses 'company', API returns 'company'
  company: string | null
  company_name?: string  // alias for backwards compat
  contact_name: string | null
  // DB uses 'email'/'phone', keep aliases for components
  email: string | null
  contact_email?: string | null
  phone: string | null
  contact_phone?: string | null
  source: string | null
  status?: string
  stage: string
  deal_value: number | null
  industry: string | null
  geography?: string | null
  region?: string | null
  project_type?: string | null
  // DB uses 'assigned_rep_id'
  assigned_rep_id: string | null
  assigned_to?: string | null  // alias
  assigned_rep_name?: string
  last_activity_at: string | null
  created_at: string
  updated_at: string
  // Joined fields from API
  score?: string | number | null
  score_numeric?: number | null
}

export interface LeadScore {
  id: string
  lead_id: string
  score: string
  score_numeric?: number
  score_reason: string
  overall_score?: number
  engagement_score?: number
  fit_score?: number
  timing_score?: number
  scoring_reason?: string
  priority_rank: number | null
  model_used?: string
  scored_at: string
}

export interface LeadNote {
  id: string
  lead_id: string
  note_text?: string
  content?: string  // alias
  note_source?: string
  source?: string  // alias
  note_type?: string
  created_by?: string
  user_id?: string  // alias
  note_date?: string | null
  created_at?: string
}

export interface LeadActivity {
  id: string
  lead_id: string
  activity_type: string
  subject: string | null
  details?: string | null
  description?: string | null  // alias
  outcome?: string | null
  duration_minutes?: number | null
  performed_by?: string | null
  logged_by?: string | null  // alias
  activity_date: string
}

export interface LeadResearch {
  id: string
  lead_id: string
  company_info?: Record<string, unknown> | null
  web_research?: string | null
  notes_summary?: string | null
  pain_points?: string[] | null
  objections?: string[] | null
  close_strategy?: string | null
  talking_points?: string[] | null
  similar_deals?: Record<string, unknown> | null
  pricing_suggestion?: string | null
  research_type?: string
  content?: Record<string, unknown>
  sources?: string[]
  confidence_score?: number
  status?: 'in_progress' | 'complete' | 'failed'
  expires_at?: string
  researched_at?: string
  created_at?: string
}

export interface DailyBrief {
  id: string
  rep_id: string
  brief_date: string
  brief_content?: string
  content?: Record<string, unknown>  // alias
  priority_list?: Record<string, unknown>
  lead_count: number | null
  hot_count?: number | null
  stale_count?: number | null
  top_priority_lead_id?: string | null
  created_at: string
}

export interface Alert {
  id: string
  alert_type: string
  message: string
  target_user_id?: string
  user_id?: string  // alias
  lead_id: string | null
  channel?: 'whatsapp' | 'email' | 'both'
  severity?: 'low' | 'medium' | 'high' | 'critical'
  title?: string
  is_read?: boolean
  read_at?: string | null
  sent_at?: string
  sent_via?: string[]
  delivered?: boolean
  created_at?: string
}

export interface LeadDetail extends Lead {
  latest_score?: LeadScore | null
  score_obj?: LeadScore | null  // alias
  activities: LeadActivity[]
  recent_activities?: LeadActivity[]  // alias
  notes: LeadNote[]
  recent_notes?: LeadNote[]  // alias
  research: LeadResearch | LeadResearch[] | null
}

export interface PipelineFunnel {
  stage: string
  count: number
  total_value?: number
}

export interface RepPerformance {
  user_id?: string
  rep_id?: string
  name?: string
  rep_name?: string
  total_leads: number
  contacted?: number
  meetings?: number
  won?: number
  won_deals?: number
  lost?: number
  total_value?: number
  avg_score?: number
  conversion_rate: number
}

export interface SourceAnalysis {
  source: string
  total_leads?: number
  lead_count?: number
  won?: number
  won_count?: number
  lost?: number
  total_value?: number
  conversion_rate: number
}
