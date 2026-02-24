export type Role = 'rep' | 'team_lead' | 'manager' | 'founder' | 'admin'

export interface User {
  id: string
  auth_id?: string
  email: string
  name?: string
  full_name?: string
  role: Role
  team: string | null
  is_active: boolean
}

export interface Lead {
  id: string
  zoho_lead_id: string | null
  company: string | null
  company_name?: string
  contact_name: string | null
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
  assigned_rep_id: string | null
  assigned_to?: string | null
  assigned_rep_name?: string
  last_activity_at: string | null
  created_at: string
  updated_at: string
  score?: string | number | null
  score_numeric?: number | null
}

export interface LeadScore {
  id: string
  lead_id: string
  score: string
  score_numeric?: number
  score_reason: string
  priority_rank: number | null
  model_used?: string
  scored_at: string
}

export interface LeadNote {
  id: string
  lead_id: string
  note_text?: string
  note_source?: string
  note_date?: string | null
  created_by?: string
  created_at?: string
}

export interface LeadActivity {
  id: string
  lead_id: string
  activity_type: string
  subject: string | null
  details?: string | null
  outcome?: string | null
  activity_date: string
  performed_by?: string | null
}

export interface LeadResearch {
  id: string
  lead_id: string
  company_info?: Record<string, unknown> | null
  web_research?: string | null
  close_strategy?: string | null
  talking_points?: string[] | null
  researched_at?: string
  status?: 'in_progress' | 'complete' | 'failed'
}

export interface DailyBrief {
  id: string
  rep_id: string
  brief_date: string
  brief_content?: string
  content?: Record<string, unknown>
  priority_list?: Record<string, unknown>
  lead_count: number | null
  hot_count?: number | null
  stale_count?: number | null
  created_at: string
}

export interface Alert {
  id: string
  alert_type: string
  message: string
  lead_id: string | null
  severity?: 'low' | 'medium' | 'high' | 'critical'
  title?: string
  is_read?: boolean
  read_at?: string | null
  created_at?: string
}

export interface LeadDetail extends Lead {
  latest_score?: LeadScore | null
  activities: LeadActivity[]
  notes: LeadNote[]
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
  total_value?: number
  conversion_rate: number
}

export interface SourceAnalysis {
  source: string
  total_leads?: number
  lead_count?: number
  won?: number
  conversion_rate: number
}
