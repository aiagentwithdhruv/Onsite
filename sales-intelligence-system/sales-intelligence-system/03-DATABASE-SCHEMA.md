# Database Schema — Supabase PostgreSQL

**All tables, indexes, RLS policies, and pgvector setup. Copy-paste ready SQL.**

---

## 1. Enable Extensions

```sql
-- Run these FIRST in Supabase SQL editor
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";    -- for pgvector (similar deal matching)
```

---

## 2. Tables

### users
```sql
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('rep', 'team_lead', 'manager', 'founder', 'admin')),
  team TEXT,                                    -- team name for grouping
  team_lead_id UUID REFERENCES users(id),       -- who is their team lead
  zoho_user_id TEXT UNIQUE,                     -- maps to Zoho CRM user
  phone TEXT,                                   -- for WhatsApp alerts
  whatsapp_opted_in BOOLEAN DEFAULT true,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### leads
```sql
CREATE TABLE leads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  zoho_lead_id TEXT UNIQUE NOT NULL,            -- dedup key
  company TEXT,
  contact_name TEXT,
  phone TEXT,
  email TEXT,
  source TEXT,                                  -- website, cold_call, referral, ads, etc.
  stage TEXT,                                   -- new, contacted, demo, proposal, negotiation, won, lost
  deal_value NUMERIC(12,2),
  industry TEXT,
  geography TEXT,                               -- city/region
  assigned_rep_id UUID REFERENCES users(id),
  zoho_created_at TIMESTAMPTZ,
  zoho_modified_at TIMESTAMPTZ,
  last_activity_at TIMESTAMPTZ,                 -- denormalized for fast stale detection
  synced_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### lead_scores
```sql
CREATE TABLE lead_scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  score TEXT NOT NULL CHECK (score IN ('hot', 'warm', 'cold')),
  score_numeric INTEGER CHECK (score_numeric BETWEEN 0 AND 100), -- 0-100 for ranking
  score_reason TEXT NOT NULL,                   -- AI explanation
  priority_rank INTEGER,                        -- 1 = call first, 2 = second...
  model_used TEXT DEFAULT 'claude-haiku',       -- which AI model scored this
  scored_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(lead_id, scored_at::date)              -- one score per lead per day
);
```

### lead_notes
```sql
CREATE TABLE lead_notes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  zoho_note_id TEXT UNIQUE,                     -- dedup for Zoho-sourced notes
  note_text TEXT NOT NULL,
  note_source TEXT DEFAULT 'zoho' CHECK (note_source IN ('zoho', 'manual', 'ai_generated')),
  created_by UUID REFERENCES users(id),
  note_date TIMESTAMPTZ,                        -- when the note was written (Zoho time)
  synced_at TIMESTAMPTZ DEFAULT NOW()
);
```

### lead_activities
```sql
CREATE TABLE lead_activities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  zoho_activity_id TEXT UNIQUE,
  activity_type TEXT NOT NULL CHECK (activity_type IN ('call', 'email', 'meeting', 'note', 'task', 'whatsapp')),
  subject TEXT,
  details TEXT,
  outcome TEXT,                                 -- for calls: connected, not_reachable, voicemail, etc.
  duration_minutes INTEGER,                     -- for calls
  performed_by UUID REFERENCES users(id),
  activity_date TIMESTAMPTZ NOT NULL,
  synced_at TIMESTAMPTZ DEFAULT NOW()
);
```

### lead_research
```sql
CREATE TABLE lead_research (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  company_info JSONB,                           -- structured company data from web
  web_research TEXT,                            -- raw web research summary
  notes_summary TEXT,                           -- AI summary of all CRM notes
  pain_points TEXT[],                           -- extracted from notes
  objections TEXT[],                            -- extracted from notes
  close_strategy TEXT,                          -- AI recommendation
  talking_points TEXT[],                        -- suggested talking points
  similar_deals JSONB,                          -- array of similar won deals
  pricing_suggestion TEXT,
  model_used TEXT DEFAULT 'claude-sonnet',
  research_cost_usd NUMERIC(6,4),              -- track AI cost per research
  researched_at TIMESTAMPTZ DEFAULT NOW(),
  is_stale BOOLEAN DEFAULT false,              -- true if new activity since research
  UNIQUE(lead_id)                              -- one research per lead (overwrite on re-research)
);
```

### lead_embeddings (for "Match Past Wins")
```sql
CREATE TABLE lead_embeddings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE UNIQUE,
  embedding vector(1536),                       -- OpenAI ada-002 or similar
  metadata JSONB,                               -- industry, deal_value, source, stage, geography
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### daily_briefs
```sql
CREATE TABLE daily_briefs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  rep_id UUID NOT NULL REFERENCES users(id),
  brief_content TEXT NOT NULL,                  -- formatted morning brief text
  priority_list JSONB NOT NULL,                 -- ordered list: [{lead_id, rank, reason}]
  lead_count INTEGER,
  hot_count INTEGER,
  stale_count INTEGER,
  model_used TEXT DEFAULT 'claude-sonnet',
  brief_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(rep_id, brief_date)                   -- one brief per rep per day
);
```

### weekly_reports
```sql
CREATE TABLE weekly_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  report_content TEXT NOT NULL,
  insights TEXT,                                -- AI-generated insights
  metrics JSONB NOT NULL,                       -- pipeline, conversions, per-rep stats
  revenue_forecast JSONB,                       -- projected closings
  model_used TEXT DEFAULT 'claude-sonnet',
  week_start DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(week_start)
);
```

### alerts
```sql
CREATE TABLE alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_type TEXT NOT NULL CHECK (alert_type IN (
    'morning_brief', 'new_lead', 'stale_7d', 'stale_14d',
    'hot_no_followup', 'deal_won', 'deal_lost',
    'weekly_report', 'performance_drop', 'custom'
  )),
  message TEXT NOT NULL,
  target_user_id UUID NOT NULL REFERENCES users(id),
  lead_id UUID REFERENCES leads(id),           -- optional: which lead triggered this
  channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'email', 'both')),
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  delivered BOOLEAN DEFAULT false,
  read_at TIMESTAMPTZ,
  delivery_error TEXT                           -- if send failed, log why
);
```

### sync_state (for tracking Zoho sync health)
```sql
CREATE TABLE sync_state (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  module TEXT NOT NULL,                         -- 'leads', 'deals', 'notes', 'activities', 'calls'
  last_sync_at TIMESTAMPTZ NOT NULL,
  records_synced INTEGER DEFAULT 0,
  sync_type TEXT DEFAULT 'delta' CHECK (sync_type IN ('delta', 'full')),
  status TEXT DEFAULT 'success' CHECK (status IN ('success', 'partial', 'failed')),
  error_message TEXT,
  duration_seconds INTEGER,
  api_credits_used INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### ai_usage_log (cost tracking)
```sql
CREATE TABLE ai_usage_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  agent_type TEXT NOT NULL,                     -- 'daily_pipeline', 'research', 'assignment', 'weekly_report'
  model TEXT NOT NULL,                          -- 'claude-sonnet-4.5', 'claude-haiku-4.5', 'gpt-4o'
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd NUMERIC(8,6),
  lead_id UUID REFERENCES leads(id),
  triggered_by UUID REFERENCES users(id),      -- null for scheduled, user_id for on-demand
  duration_ms INTEGER,
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Indexes (Critical for Performance)

```sql
-- leads: most queried table
CREATE INDEX idx_leads_assigned_rep ON leads(assigned_rep_id);
CREATE INDEX idx_leads_zoho_id ON leads(zoho_lead_id);
CREATE INDEX idx_leads_stage ON leads(stage);
CREATE INDEX idx_leads_last_activity ON leads(last_activity_at);
CREATE INDEX idx_leads_zoho_modified ON leads(zoho_modified_at);
CREATE INDEX idx_leads_source ON leads(source);

-- lead_scores: dashboard reads these constantly
CREATE INDEX idx_scores_lead_id ON lead_scores(lead_id);
CREATE INDEX idx_scores_scored_at ON lead_scores(scored_at DESC);
CREATE INDEX idx_scores_score ON lead_scores(score);

-- lead_notes: research agent reads all notes per lead
CREATE INDEX idx_notes_lead_id ON lead_notes(lead_id);
CREATE INDEX idx_notes_date ON lead_notes(note_date DESC);

-- lead_activities: timeline view + stale detection
CREATE INDEX idx_activities_lead_id ON lead_activities(lead_id);
CREATE INDEX idx_activities_date ON lead_activities(activity_date DESC);
CREATE INDEX idx_activities_type ON lead_activities(activity_type);
CREATE INDEX idx_activities_performed_by ON lead_activities(performed_by);

-- lead_research: one per lead, looked up by lead_id
CREATE INDEX idx_research_lead_id ON lead_research(lead_id);

-- lead_embeddings: vector similarity search
CREATE INDEX idx_embeddings_vector ON lead_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- daily_briefs: reps look up today's brief
CREATE INDEX idx_briefs_rep_date ON daily_briefs(rep_id, brief_date DESC);

-- alerts: user sees their unread alerts
CREATE INDEX idx_alerts_user ON alerts(target_user_id, sent_at DESC);
CREATE INDEX idx_alerts_unread ON alerts(target_user_id) WHERE read_at IS NULL;

-- sync_state: admin checks sync health
CREATE INDEX idx_sync_module ON sync_state(module, created_at DESC);

-- ai_usage: cost tracking
CREATE INDEX idx_ai_usage_date ON ai_usage_log(created_at DESC);
CREATE INDEX idx_ai_usage_agent ON ai_usage_log(agent_type, created_at DESC);
```

---

## 4. Row Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- LEADS: reps see own, team_leads see team, managers/founders/admins see all
CREATE POLICY leads_rep_policy ON leads
  FOR SELECT USING (
    assigned_rep_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid()
      AND role IN ('team_lead', 'manager', 'founder', 'admin')
    )
  );

-- Team leads: see leads assigned to reps in their team
CREATE POLICY leads_team_lead_policy ON leads
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM users u
      WHERE u.id = auth.uid()
      AND u.role = 'team_lead'
      AND leads.assigned_rep_id IN (
        SELECT id FROM users WHERE team_lead_id = auth.uid()
      )
    )
  );

-- DAILY BRIEFS: rep sees own brief only
CREATE POLICY briefs_own ON daily_briefs
  FOR SELECT USING (
    rep_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid()
      AND role IN ('manager', 'founder', 'admin')
    )
  );

-- ALERTS: user sees own alerts only
CREATE POLICY alerts_own ON alerts
  FOR SELECT USING (target_user_id = auth.uid());
CREATE POLICY alerts_own_update ON alerts
  FOR UPDATE USING (target_user_id = auth.uid());
```

---

## 5. Helper Views (for Dashboard Queries)

```sql
-- Stale leads view: leads with no activity in 7+ days
CREATE VIEW v_stale_leads AS
SELECT l.*, ls.score, ls.score_reason,
  EXTRACT(DAY FROM NOW() - l.last_activity_at) AS days_since_activity
FROM leads l
LEFT JOIN LATERAL (
  SELECT score, score_reason FROM lead_scores
  WHERE lead_id = l.id ORDER BY scored_at DESC LIMIT 1
) ls ON true
WHERE l.stage NOT IN ('won', 'lost')
AND l.last_activity_at < NOW() - INTERVAL '7 days';

-- Rep performance view
CREATE VIEW v_rep_performance AS
SELECT
  u.id AS rep_id,
  u.name AS rep_name,
  u.team,
  COUNT(l.id) AS total_leads,
  COUNT(l.id) FILTER (WHERE l.stage = 'won') AS won,
  COUNT(l.id) FILTER (WHERE l.stage = 'lost') AS lost,
  COUNT(la.id) FILTER (WHERE la.activity_type = 'call' AND la.activity_date > NOW() - INTERVAL '7 days') AS calls_this_week,
  ROUND(COUNT(l.id) FILTER (WHERE l.stage = 'won')::NUMERIC / NULLIF(COUNT(l.id), 0) * 100, 1) AS conversion_rate,
  SUM(l.deal_value) FILTER (WHERE l.stage = 'won') AS revenue_won
FROM users u
LEFT JOIN leads l ON l.assigned_rep_id = u.id
LEFT JOIN lead_activities la ON la.lead_id = l.id AND la.performed_by = u.id
WHERE u.role = 'rep'
GROUP BY u.id, u.name, u.team;
```

---

## 6. Updated_at Trigger

```sql
-- Auto-update updated_at on row changes
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
```
