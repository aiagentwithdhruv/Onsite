-- Dashboard summary: stores computed analytics (small, ~1-2MB instead of 200MB raw data)
-- Run in Supabase SQL Editor

-- Drop old raw cache table if exists
DROP TABLE IF EXISTS intelligence_cache;

-- New lightweight summary table
CREATE TABLE IF NOT EXISTS dashboard_summary (
  id TEXT PRIMARY KEY DEFAULT 'current',
  kpis JSONB NOT NULL DEFAULT '{}',
  charts JSONB NOT NULL DEFAULT '{}',
  insights JSONB NOT NULL DEFAULT '{}',
  team_data JSONB NOT NULL DEFAULT '{}',
  source_data JSONB NOT NULL DEFAULT '{}',
  aging_data JSONB NOT NULL DEFAULT '{}',
  trend_data JSONB NOT NULL DEFAULT '{}',
  deep_dive JSONB NOT NULL DEFAULT '{}',
  sales_data JSONB NOT NULL DEFAULT '{}',
  action_items JSONB NOT NULL DEFAULT '[]',
  total_leads INTEGER DEFAULT 0,
  file_name TEXT,
  uploaded_by TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add sales_data column if table already exists (migration)
ALTER TABLE dashboard_summary ADD COLUMN IF NOT EXISTS sales_data JSONB NOT NULL DEFAULT '{}';

ALTER TABLE dashboard_summary ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS dashboard_summary_all ON dashboard_summary FOR ALL USING (true) WITH CHECK (true);
