-- Migration: 009_push_subscriptions
-- Created: 2026-05-20
-- Purpose: Per-user push subscription endpoints for the Task AI PWA.

CREATE TABLE IF NOT EXISTS push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  endpoint TEXT NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_used_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, endpoint)
);

CREATE INDEX IF NOT EXISTS push_subscriptions_user_idx ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS push_subscriptions_endpoint_idx ON push_subscriptions(endpoint);

-- Tenant isolation: a user can only see their own subscriptions.
-- Service-role writes (from API routes) bypass RLS as expected.
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS push_subscriptions_user_iso ON push_subscriptions;
CREATE POLICY push_subscriptions_user_iso ON push_subscriptions
  FOR ALL
  USING (user_id = auth.uid()::uuid)
  WITH CHECK (user_id = auth.uid()::uuid);

COMMENT ON TABLE push_subscriptions IS
  'Web Push subscriptions per Onsite user for the Task AI PWA. Endpoints expire — pruned on 404/410 responses from push gateways.';
