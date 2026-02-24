-- Agent Profiles: per-person performance memory for sales reps/deal owners
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS agent_profiles (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT DEFAULT 'deal_owner',
  manager TEXT,
  performance JSONB DEFAULT '{}',
  patterns JSONB DEFAULT '{}',
  strengths JSONB DEFAULT '[]',
  concerns JSONB DEFAULT '[]',
  monthly_history JSONB DEFAULT '[]',
  notes JSONB DEFAULT '[]',
  last_updated TIMESTAMPTZ DEFAULT NOW()
);
