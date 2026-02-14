export type Role = 'rep' | 'team_lead' | 'manager' | 'founder' | 'admin'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  team: string | null
  is_active: boolean
}

export interface Lead {
  id: string
  zoho_lead_id: string | null
  company_name: string
  contact_name: string
  contact_email: string | null
  contact_phone: string | null
  source: string
  status: string
  stage: string
  deal_value: number
  industry: string | null
  region: string | null
  project_type: string | null
  assigned_to: string | null
  assigned_rep_name?: string
  last_activity_at: string | null
  created_at: string
  updated_at: string
}

export interface LeadScore {
  id: string
  lead_id: string
  overall_score: number
  engagement_score: number
  fit_score: number
  timing_score: number
  scoring_reason: string
  priority_rank: number | null
  scored_at: string
}

export interface LeadNote {
  id: string
  lead_id: string
  user_id: string
  note_type: string
  content: string
  source: string
  created_at: string
}

export interface LeadActivity {
  id: string
  lead_id: string
  activity_type: string
  subject: string
  description: string | null
  activity_date: string
  logged_by: string | null
}

export interface LeadResearch {
  id: string
  lead_id: string
  research_type: string
  content: Record<string, unknown>
  sources: string[]
  confidence_score: number
  expires_at: string
  created_at: string
}

export interface DailyBrief {
  id: string
  rep_id: string
  brief_date: string
  content: Record<string, unknown>
  lead_count: number
  top_priority_lead_id: string | null
  created_at: string
}

export interface Alert {
  id: string
  user_id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  lead_id: string | null
  is_read: boolean
  sent_via: string[]
  created_at: string
}

export interface LeadDetail extends Lead {
  score: LeadScore | null
  recent_activities: LeadActivity[]
  recent_notes: LeadNote[]
  research: LeadResearch[]
}

export interface PipelineFunnel {
  stage: string
  count: number
  total_value: number
}

export interface RepPerformance {
  rep_id: string
  rep_name: string
  total_leads: number
  won_deals: number
  total_value: number
  avg_score: number
  conversion_rate: number
}

export interface SourceAnalysis {
  source: string
  lead_count: number
  won_count: number
  total_value: number
  conversion_rate: number
}
