-- Migration: 010_wa_user_link
-- Created: 2026-05-21
-- Purpose: Map WhatsApp phone numbers → Onsite user_id for the bot.
--
-- Why: browser/PWA sessions carry the JWT directly. WhatsApp doesn't —
-- the bot receives a phone number on every incoming message and must
-- resolve it to an Onsite user so we can call Onsite APIs on their behalf.
--
-- Flow:
--   1. New phone messages the bot → bot replies "send 6-digit code from your app"
--   2. User opens Onsite Flutter / PWA → "Link WhatsApp" screen → 6-digit code
--   3. User types code into WhatsApp → bot verifies → inserts row here
--   4. Future incoming WhatsApps: look up by phone, decrypt refresh token,
--      mint short-lived JWT for Onsite calls
--
-- Security: refresh_token_encrypted is AES-GCM ciphertext. Encryption key
-- (WA_LINK_ENCRYPTION_KEY) lives in env, never in DB. Tokens never logged.

CREATE TABLE IF NOT EXISTS wa_user_link (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_e164 TEXT NOT NULL UNIQUE,            -- digits only, no +
  user_id UUID NOT NULL,
  display_name TEXT,                          -- WhatsApp profile name at link time
  -- Onsite-issued JWT for this user, AES-GCM encrypted. Onsite doesn't
  -- expose a refresh endpoint yet; we store the access token directly
  -- and rely on its 6-mo lifetime. Re-link prompt fires near expiry.
  access_token_encrypted TEXT,
  access_token_iv TEXT,
  token_expires_at TIMESTAMPTZ,
  linked_at TIMESTAMPTZ DEFAULT now(),
  last_active_at TIMESTAMPTZ DEFAULT now(),
  unlinked_at TIMESTAMPTZ                     -- soft delete; row retained for audit
);

CREATE INDEX IF NOT EXISTS wa_user_link_user_idx ON wa_user_link(user_id);
CREATE INDEX IF NOT EXISTS wa_user_link_active_idx ON wa_user_link(phone_e164) WHERE unlinked_at IS NULL;

-- Pending OTPs for linking (5-min TTL via expires_at)
-- Flow: Flutter/PWA app calls /start-link with the user's JWT →
-- we encrypt + stash the JWT here behind a 6-digit code → user types
-- code into WhatsApp → /confirm-link consumes the row + creates a
-- wa_user_link entry with the same encrypted JWT.
CREATE TABLE IF NOT EXISTS wa_link_otp (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  code TEXT NOT NULL,                         -- 6-digit
  access_token_encrypted TEXT NOT NULL,       -- AES-GCM ciphertext of the JWT
  access_token_iv TEXT NOT NULL,              -- AES-GCM IV
  token_expires_at TIMESTAMPTZ,
  phone_e164 TEXT,                            -- known after user replies on WhatsApp
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS wa_link_otp_user_idx ON wa_link_otp(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS wa_link_otp_active_idx ON wa_link_otp(code) WHERE consumed_at IS NULL;

-- RLS — phone owner is the only one who reads their own row.
ALTER TABLE wa_user_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa_link_otp ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS wa_user_link_user_iso ON wa_user_link;
CREATE POLICY wa_user_link_user_iso ON wa_user_link
  FOR ALL USING (user_id = auth.uid()::uuid) WITH CHECK (user_id = auth.uid()::uuid);

DROP POLICY IF EXISTS wa_link_otp_user_iso ON wa_link_otp;
CREATE POLICY wa_link_otp_user_iso ON wa_link_otp
  FOR ALL USING (user_id = auth.uid()::uuid) WITH CHECK (user_id = auth.uid()::uuid);

COMMENT ON TABLE wa_user_link IS
  'WhatsApp phone ↔ Onsite user mapping for the Task AI bot. Encrypted refresh tokens enable per-message JWT minting without storing the JWT itself.';
