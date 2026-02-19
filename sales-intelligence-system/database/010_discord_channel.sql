-- Discord alert delivery (same as Telegram: user adds channel via webhook URL)
-- Run in Supabase SQL Editor

ALTER TABLE users ADD COLUMN IF NOT EXISTS discord_webhook_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_via_discord BOOLEAN DEFAULT false;

COMMENT ON COLUMN users.discord_webhook_url IS 'Discord webhook URL; user creates in Channel Settings → Webhooks and pastes here.';
COMMENT ON COLUMN users.notify_via_discord IS 'If true, deliver smart alerts to this user via Discord webhook.';

-- Allow 'discord' in delivery log
ALTER TABLE alert_delivery_log DROP CONSTRAINT IF EXISTS alert_delivery_log_channel_check;
ALTER TABLE alert_delivery_log ADD CONSTRAINT alert_delivery_log_channel_check
  CHECK (channel IN ('telegram', 'whatsapp', 'email', 'discord'));
