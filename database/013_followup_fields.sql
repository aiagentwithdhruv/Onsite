-- ============================================
-- Add follow-up, deal owner, remarks fields to leads
-- Run in Supabase SQL Editor
-- ============================================

-- Follow-up scheduling
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_date DATE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_time TIME;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_note TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_reminded BOOLEAN DEFAULT false;

-- Deal owner (Zoho Lead Owner name — maps to assigned_rep)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS deal_owner TEXT;

-- Remarks / last notes from sales rep
ALTER TABLE leads ADD COLUMN IF NOT EXISTS remarks TEXT;

-- Dates for tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_touch_date TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_source_date TIMESTAMPTZ;

-- Demo fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS demo_booked_date DATE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS demo_booked_time TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS demo_meeting_link TEXT;

-- Marketing context
ALTER TABLE leads ADD COLUMN IF NOT EXISTS marketing_method TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS whatsapp_marketing TEXT;

-- Add deal_owner_name to users if not exists (for rep mapping)
ALTER TABLE users ADD COLUMN IF NOT EXISTS deal_owner_name TEXT;

-- Index for follow-up reminder queries (find due follow-ups fast)
CREATE INDEX IF NOT EXISTS idx_leads_followup_due
  ON leads (follow_up_date, follow_up_time)
  WHERE follow_up_date IS NOT NULL AND follow_up_reminded = false;

-- Index for deal owner lookups
CREATE INDEX IF NOT EXISTS idx_leads_deal_owner
  ON leads (deal_owner)
  WHERE deal_owner IS NOT NULL;

-- Follow-up reminders log (track what was sent, avoid duplicates)
CREATE TABLE IF NOT EXISTS follow_up_reminders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id),
  follow_up_date DATE NOT NULL,
  follow_up_time TIME,
  reminder_type TEXT NOT NULL CHECK (reminder_type IN ('15min_before', 'at_time', 'overdue', 'morning_summary')),
  sent_via TEXT, -- 'telegram', 'whatsapp', 'email'
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'sent'
);

CREATE INDEX IF NOT EXISTS idx_followup_reminders_lead
  ON follow_up_reminders (lead_id, follow_up_date);
