-- Smart Alerts: extend alerts table for agentic alert system
-- Run in Supabase SQL Editor

-- Add missing columns for smart alerts
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS severity TEXT DEFAULT 'medium';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS agent_name TEXT DEFAULT 'deal_owner';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Drop the strict alert_type constraint and replace with a broader one
ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_alert_type_check;
ALTER TABLE alerts ADD CONSTRAINT alerts_alert_type_check CHECK (alert_type IN (
  'morning_brief', 'new_lead', 'stale_7d', 'stale_14d', 'stale_30d',
  'hot_no_followup', 'deal_won', 'deal_lost',
  'weekly_report', 'performance_drop', 'low_conversion',
  'demo_dropout', 'priority_overload', 'inactive_agent',
  'top_performer', 'revenue_milestone', 'pipeline_risk',
  'follow_up_needed', 'custom'
));

-- Drop FK on lead_id (we don't store leads in the leads table)
ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_lead_id_fkey;

-- Make lead_id nullable text (not UUID FK)
ALTER TABLE alerts ALTER COLUMN lead_id DROP NOT NULL;

-- Allow service role to insert alerts
CREATE POLICY IF NOT EXISTS alerts_insert_service ON alerts FOR INSERT WITH CHECK (true);
CREATE POLICY IF NOT EXISTS alerts_all_service ON alerts FOR ALL USING (true) WITH CHECK (true);
