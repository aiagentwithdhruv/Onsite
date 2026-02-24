-- User deal-owner access: reps see only their own data (matched by deal_owner_name)
-- Run in Supabase SQL Editor

-- Allow admin to set which deal owner(s) a user sees (exact match to CSV deal_owner column)
ALTER TABLE users ADD COLUMN IF NOT EXISTS deal_owner_name TEXT;

-- Store per-deal-owner summary so reps get scoped dashboard (optional column)
ALTER TABLE dashboard_summary ADD COLUMN IF NOT EXISTS summary_by_owner JSONB DEFAULT '{}';

COMMENT ON COLUMN users.deal_owner_name IS 'For reps: exact deal_owner value from CSV. Data is filtered to this owner. Managers/admins see all.';
