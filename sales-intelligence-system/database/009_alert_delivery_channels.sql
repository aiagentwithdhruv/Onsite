-- Alert delivery: user notification channels (Telegram, WhatsApp, Email)
-- Run in Supabase SQL Editor

-- Telegram: user links bot via /start; we store their chat_id
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_telegram BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_whatsapp BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_email BOOLEAN DEFAULT true;

COMMENT ON COLUMN users.telegram_chat_id IS 'Set when user sends /start to our Telegram bot; used to send smart alerts.';
COMMENT ON COLUMN users.notify_via_telegram IS 'If true, deliver smart alerts to this user via Telegram (priority).';
COMMENT ON COLUMN users.notify_via_whatsapp IS 'If true, deliver smart alerts via WhatsApp (phone from users.phone).';
COMMENT ON COLUMN users.notify_via_email IS 'If true, deliver smart alerts via email (users.email).';

-- Optional: log delivery for debugging (one row per alert per channel attempt)
CREATE TABLE IF NOT EXISTS alert_delivery_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(id),
  channel TEXT NOT NULL CHECK (channel IN ('telegram', 'whatsapp', 'email')),
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'skipped')),
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_alert_delivery_log_alert ON alert_delivery_log(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_delivery_log_user ON alert_delivery_log(user_id, sent_at DESC);

-- One-time tokens for "Link Telegram" flow: user opens t.me/Bot?start=TOKEN
CREATE TABLE IF NOT EXISTS telegram_link_tokens (
  token TEXT PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_link_tokens_expires ON telegram_link_tokens(expires_at);
