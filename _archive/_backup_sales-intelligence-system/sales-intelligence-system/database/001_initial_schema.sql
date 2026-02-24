-- ============================================
-- Sales Intelligence System — Initial Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================
-- TABLES
-- ============================================

-- Users (sales reps, managers, founder, admin)
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  auth_id UUID UNIQUE,  -- links to Supabase Auth user ID
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('rep', 'team_lead', 'manager', 'founder', 'admin')),
  team TEXT,
  team_lead_id UUID REFERENCES users(id),
  zoho_user_id TEXT UNIQUE,
  phone TEXT,
  whatsapp_opted_in BOOLEAN DEFAULT true,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leads (synced from Zoho CRM)
CREATE TABLE leads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  zoho_lead_id TEXT UNIQUE NOT NULL,
  company TEXT,
  contact_name TEXT,
  phone TEXT,
  email TEXT,
  source TEXT,
  stage TEXT DEFAULT 'new',
  deal_value NUMERIC(12,2),
  industry TEXT,
  geography TEXT,
  assigned_rep_id UUID REFERENCES users(id),
  zoho_created_at TIMESTAMPTZ,
  zoho_modified_at TIMESTAMPTZ,
  last_activity_at TIMESTAMPTZ,
  synced_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Scores (AI scoring output)
CREATE TABLE lead_scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  score TEXT NOT NULL CHECK (score IN ('hot', 'warm', 'cold')),
  score_numeric INTEGER CHECK (score_numeric BETWEEN 0 AND 100),
  score_reason TEXT NOT NULL,
  priority_rank INTEGER,
  model_used TEXT DEFAULT 'claude-haiku',
  scored_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Notes (from Zoho)
CREATE TABLE lead_notes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  zoho_note_id TEXT UNIQUE,
  note_text TEXT NOT NULL,
  note_source TEXT DEFAULT 'zoho' CHECK (note_source IN ('zoho', 'manual', 'ai_generated')),
  created_by UUID REFERENCES users(id),
  note_date TIMESTAMPTZ,
  synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Activities (calls, emails, meetings from Zoho)
CREATE TABLE lead_activities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  zoho_activity_id TEXT UNIQUE,
  activity_type TEXT NOT NULL CHECK (activity_type IN ('call', 'email', 'meeting', 'note', 'task', 'whatsapp')),
  subject TEXT,
  details TEXT,
  outcome TEXT,
  duration_minutes INTEGER,
  performed_by UUID REFERENCES users(id),
  activity_date TIMESTAMPTZ NOT NULL,
  synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Research (AI research output)
CREATE TABLE lead_research (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID UNIQUE NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  company_info JSONB,
  web_research TEXT,
  notes_summary TEXT,
  pain_points TEXT[],
  objections TEXT[],
  close_strategy TEXT,
  talking_points TEXT[],
  similar_deals JSONB,
  pricing_suggestion TEXT,
  model_used TEXT DEFAULT 'claude-sonnet',
  research_cost_usd NUMERIC(6,4),
  status TEXT DEFAULT 'complete' CHECK (status IN ('in_progress', 'complete', 'failed')),
  researched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Embeddings (for vector similarity — Match Past Wins)
CREATE TABLE lead_embeddings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE UNIQUE,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily Briefs (morning brief per rep)
CREATE TABLE daily_briefs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  rep_id UUID NOT NULL REFERENCES users(id),
  brief_content TEXT NOT NULL,
  priority_list JSONB NOT NULL,
  lead_count INTEGER,
  hot_count INTEGER,
  stale_count INTEGER,
  model_used TEXT DEFAULT 'claude-sonnet',
  brief_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(rep_id, brief_date)
);

-- Weekly Reports
CREATE TABLE weekly_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  report_content TEXT NOT NULL,
  insights TEXT,
  metrics JSONB NOT NULL,
  revenue_forecast JSONB,
  model_used TEXT DEFAULT 'claude-sonnet',
  week_start DATE NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts (WhatsApp + Email log)
CREATE TABLE alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_type TEXT NOT NULL CHECK (alert_type IN (
    'morning_brief', 'new_lead', 'stale_7d', 'stale_14d',
    'hot_no_followup', 'deal_won', 'deal_lost',
    'weekly_report', 'performance_drop', 'custom'
  )),
  message TEXT NOT NULL,
  target_user_id UUID NOT NULL REFERENCES users(id),
  lead_id UUID REFERENCES leads(id),
  channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'email', 'both')),
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  delivered BOOLEAN DEFAULT false,
  read_at TIMESTAMPTZ,
  delivery_error TEXT
);

-- Sync State (tracks Zoho sync health)
CREATE TABLE sync_state (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  module TEXT NOT NULL,
  last_sync_at TIMESTAMPTZ NOT NULL,
  records_synced INTEGER DEFAULT 0,
  sync_type TEXT DEFAULT 'delta' CHECK (sync_type IN ('delta', 'full')),
  status TEXT DEFAULT 'success' CHECK (status IN ('success', 'partial', 'failed')),
  error_message TEXT,
  duration_seconds INTEGER,
  api_credits_used INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Usage Log (cost tracking)
CREATE TABLE ai_usage_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  agent_type TEXT NOT NULL,
  model TEXT NOT NULL,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cost_usd NUMERIC(8,6) DEFAULT 0,
  lead_id UUID REFERENCES leads(id),
  triggered_by UUID REFERENCES users(id),
  duration_ms INTEGER,
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- leads
CREATE INDEX idx_leads_assigned_rep ON leads(assigned_rep_id);
CREATE INDEX idx_leads_zoho_id ON leads(zoho_lead_id);
CREATE INDEX idx_leads_stage ON leads(stage);
CREATE INDEX idx_leads_last_activity ON leads(last_activity_at);
CREATE INDEX idx_leads_zoho_modified ON leads(zoho_modified_at);
CREATE INDEX idx_leads_source ON leads(source);

-- lead_scores
CREATE INDEX idx_scores_lead_id ON lead_scores(lead_id);
CREATE INDEX idx_scores_scored_at ON lead_scores(scored_at DESC);

-- lead_notes
CREATE INDEX idx_notes_lead_id ON lead_notes(lead_id);
CREATE INDEX idx_notes_date ON lead_notes(note_date DESC);

-- lead_activities
CREATE INDEX idx_activities_lead_id ON lead_activities(lead_id);
CREATE INDEX idx_activities_date ON lead_activities(activity_date DESC);
CREATE INDEX idx_activities_performed_by ON lead_activities(performed_by);

-- lead_research
CREATE INDEX idx_research_lead_id ON lead_research(lead_id);

-- lead_embeddings (vector search)
CREATE INDEX idx_embeddings_vector ON lead_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- daily_briefs
CREATE INDEX idx_briefs_rep_date ON daily_briefs(rep_id, brief_date DESC);

-- alerts
CREATE INDEX idx_alerts_user ON alerts(target_user_id, sent_at DESC);
CREATE INDEX idx_alerts_unread ON alerts(target_user_id) WHERE read_at IS NULL;

-- sync_state
CREATE INDEX idx_sync_module ON sync_state(module, created_at DESC);

-- ai_usage
CREATE INDEX idx_ai_usage_date ON ai_usage_log(created_at DESC);
CREATE INDEX idx_ai_usage_agent ON ai_usage_log(agent_type, created_at DESC);

-- ============================================
-- TRIGGERS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_leads_updated_at BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- VIEWS (Dashboard Helpers)
-- ============================================

-- Stale leads: no activity in 7+ days
CREATE OR REPLACE VIEW v_stale_leads AS
SELECT
  l.*,
  ls.score,
  ls.score_reason,
  EXTRACT(DAY FROM NOW() - l.last_activity_at)::INTEGER AS days_since_activity
FROM leads l
LEFT JOIN LATERAL (
  SELECT score, score_reason FROM lead_scores
  WHERE lead_id = l.id ORDER BY scored_at DESC LIMIT 1
) ls ON true
WHERE l.stage NOT IN ('won', 'lost')
AND l.last_activity_at < NOW() - INTERVAL '7 days';

-- Rep performance summary
CREATE OR REPLACE VIEW v_rep_performance AS
SELECT
  u.id AS rep_id,
  u.name AS rep_name,
  u.team,
  COUNT(l.id) AS total_leads,
  COUNT(l.id) FILTER (WHERE l.stage = 'won') AS won,
  COUNT(l.id) FILTER (WHERE l.stage = 'lost') AS lost,
  COUNT(DISTINCT la.id) FILTER (WHERE la.activity_type = 'call' AND la.activity_date > NOW() - INTERVAL '7 days') AS calls_this_week,
  ROUND(
    COUNT(l.id) FILTER (WHERE l.stage = 'won')::NUMERIC /
    NULLIF(COUNT(l.id) FILTER (WHERE l.stage IN ('won', 'lost')), 0) * 100, 1
  ) AS conversion_rate,
  COALESCE(SUM(l.deal_value) FILTER (WHERE l.stage = 'won'), 0) AS revenue_won
FROM users u
LEFT JOIN leads l ON l.assigned_rep_id = u.id
LEFT JOIN lead_activities la ON la.lead_id = l.id AND la.performed_by = u.id
WHERE u.role = 'rep' AND u.is_active = true
GROUP BY u.id, u.name, u.team;

-- Pipeline funnel
CREATE OR REPLACE VIEW v_pipeline_funnel AS
SELECT
  stage,
  COUNT(*) AS count,
  COALESCE(SUM(deal_value), 0) AS total_value
FROM leads
WHERE stage NOT IN ('won', 'lost')
GROUP BY stage
ORDER BY
  CASE stage
    WHEN 'new' THEN 1
    WHEN 'contacted' THEN 2
    WHEN 'demo' THEN 3
    WHEN 'proposal' THEN 4
    WHEN 'negotiation' THEN 5
  END;

-- ============================================
-- VECTOR SEARCH FUNCTION (Match Past Wins)
-- ============================================

CREATE OR REPLACE FUNCTION match_similar_deals(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  lead_id UUID,
  company TEXT,
  deal_value NUMERIC,
  source TEXT,
  industry TEXT,
  geography TEXT,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    l.id AS lead_id,
    l.company,
    l.deal_value,
    l.source,
    l.industry,
    l.geography,
    1 - (le.embedding <=> query_embedding) AS similarity
  FROM lead_embeddings le
  JOIN leads l ON l.id = le.lead_id
  WHERE l.stage = 'won'
  AND 1 - (le.embedding <=> query_embedding) > match_threshold
  ORDER BY le.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Leads: reps see own, everyone else sees all
CREATE POLICY leads_select ON leads FOR SELECT USING (
  assigned_rep_id = auth.uid()
  OR EXISTS (
    SELECT 1 FROM users WHERE id = auth.uid()
    AND role IN ('team_lead', 'manager', 'founder', 'admin')
  )
);

-- Briefs: rep sees own, managers see all
CREATE POLICY briefs_select ON daily_briefs FOR SELECT USING (
  rep_id = auth.uid()
  OR EXISTS (
    SELECT 1 FROM users WHERE id = auth.uid()
    AND role IN ('manager', 'founder', 'admin')
  )
);

-- Alerts: user sees own only
CREATE POLICY alerts_select ON alerts FOR SELECT USING (
  target_user_id = auth.uid()
);
CREATE POLICY alerts_update ON alerts FOR UPDATE USING (
  target_user_id = auth.uid()
);

-- Scores, notes, activities, research follow the lead they belong to
CREATE POLICY scores_select ON lead_scores FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM leads WHERE leads.id = lead_scores.lead_id
    AND (
      leads.assigned_rep_id = auth.uid()
      OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('team_lead', 'manager', 'founder', 'admin'))
    )
  )
);

CREATE POLICY notes_select ON lead_notes FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM leads WHERE leads.id = lead_notes.lead_id
    AND (
      leads.assigned_rep_id = auth.uid()
      OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('team_lead', 'manager', 'founder', 'admin'))
    )
  )
);

CREATE POLICY activities_select ON lead_activities FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM leads WHERE leads.id = lead_activities.lead_id
    AND (
      leads.assigned_rep_id = auth.uid()
      OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('team_lead', 'manager', 'founder', 'admin'))
    )
  )
);

CREATE POLICY research_select ON lead_research FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM leads WHERE leads.id = lead_research.lead_id
    AND (
      leads.assigned_rep_id = auth.uid()
      OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('team_lead', 'manager', 'founder', 'admin'))
    )
  )
);
