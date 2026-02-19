-- App config (key-value) for integration secrets set via UI (e.g. Telegram bot token)
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS app_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE app_config IS 'Server-side config set via Admin/Settings (e.g. telegram_bot_token). Backend uses service role.';
