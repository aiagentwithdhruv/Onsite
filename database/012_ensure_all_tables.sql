-- Ensure all required tables and columns exist
-- Safe to run multiple times (IF NOT EXISTS / IF NOT EXISTS guards)

-- Notification preference columns on users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_telegram BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_whatsapp BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_email BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS discord_webhook_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_discord BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deal_owner_name TEXT;

-- sync_state table (for admin sync status)
CREATE TABLE IF NOT EXISTS sync_state (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  module TEXT NOT NULL,
  last_sync_at TIMESTAMPTZ NOT NULL,
  records_synced INTEGER DEFAULT 0,
  sync_type TEXT DEFAULT 'delta',
  status TEXT DEFAULT 'success',
  error_message TEXT,
  duration_seconds INTEGER,
  api_credits_used INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- alert_delivery_log table
CREATE TABLE IF NOT EXISTS alert_delivery_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(id),
  channel TEXT NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'sent',
  error_message TEXT
);

-- app_config table (for Telegram bot token, LLM keys etc.)
CREATE TABLE IF NOT EXISTS app_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
