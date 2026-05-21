-- Migration: alerts + domain (Phase 10)
-- Created: 2026-05-22
-- Purpose: 10 production-grade alert rules (M-15) + domain feature tables
--          (weather cache, geo-tagged progress, vendor scores, webhooks).

CREATE TABLE IF NOT EXISTS alert_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  rule_key TEXT NOT NULL,                       -- stale_task, critical_path_slip, ...
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  threshold JSONB NOT NULL DEFAULT '{}'::jsonb, -- per-rule config
  channels TEXT[] NOT NULL DEFAULT '{whatsapp,webpush}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, rule_key)
);

CREATE TABLE IF NOT EXISTS alert_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  rule_key TEXT NOT NULL,
  entity_id TEXT,                               -- e.g. task UUID, vendor name, project UUID
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'high', 'critical')),
  message TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  dedup_hash TEXT NOT NULL,                     -- sha256(tenant + rule + entity + day) — prevents spam
  delivered_channels TEXT[] NOT NULL DEFAULT '{}',
  fired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  acknowledged_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_alert_log_dedup ON alert_log (dedup_hash);
CREATE INDEX IF NOT EXISTS idx_alert_log_tenant ON alert_log (tenant_id, fired_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_log_unack ON alert_log (tenant_id, acknowledged_at) WHERE acknowledged_at IS NULL;

CREATE TABLE IF NOT EXISTS webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  url TEXT NOT NULL,
  secret TEXT,                                  -- HMAC signing secret
  events TEXT[] NOT NULL DEFAULT '{*}',         -- e.g. {alert.fired, document.ready}
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_success_at TIMESTAMPTZ,
  last_error TEXT,
  failure_count INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant ON webhooks (tenant_id) WHERE active;

CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
  event TEXT NOT NULL,
  payload JSONB NOT NULL,
  status_code INT,
  attempt INT NOT NULL DEFAULT 1,
  delivered_at TIMESTAMPTZ,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_pending
  ON webhook_deliveries (created_at)
  WHERE delivered_at IS NULL;

-- Geo-tagged progress: lat/lon captured at record time (with consent).
-- M-34: EXIF alone isn't trustworthy; server validates against project site.
CREATE TABLE IF NOT EXISTS progress_geo (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  progress_history_id TEXT NOT NULL,            -- ref Onsite billing_progress_history.id
  user_id TEXT NOT NULL,
  lat NUMERIC(9, 6),
  lon NUMERIC(9, 6),
  accuracy_meters NUMERIC(7, 2),
  exif_lat NUMERIC(9, 6),
  exif_lon NUMERIC(9, 6),
  distance_from_site_m NUMERIC(10, 2),
  ip_geo_country TEXT,
  device_user_agent TEXT,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  flagged BOOLEAN NOT NULL DEFAULT FALSE,       -- true if >500m from project site
  flag_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_progress_geo_tenant
  ON progress_geo (tenant_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_progress_geo_flagged
  ON progress_geo (tenant_id, flagged)
  WHERE flagged = TRUE;

-- Per-vendor reliability score (lift from Onsite Sales Intelligence).
-- Computed daily: on-time % + quality flags + cost-vs-quote deviation.
CREATE TABLE IF NOT EXISTS vendor_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  vendor_name TEXT NOT NULL,
  on_time_pct NUMERIC(5, 2),                    -- 0-100
  quality_flags_30d INT NOT NULL DEFAULT 0,
  avg_cost_deviation_pct NUMERIC(6, 2),         -- vs quote
  score INT NOT NULL CHECK (score >= 0 AND score <= 100),
  reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, vendor_name, computed_at)
);

CREATE INDEX IF NOT EXISTS idx_vendor_scores_latest
  ON vendor_scores (tenant_id, vendor_name, computed_at DESC);

-- Weather cache (M-35): per project location, 6h TTL. Without caching the
-- free tier 1M/mo dies in days.
CREATE TABLE IF NOT EXISTS weather_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  lat NUMERIC(9, 6) NOT NULL,
  lon NUMERIC(9, 6) NOT NULL,
  payload JSONB NOT NULL,                       -- raw OpenWeatherMap response
  forecast_horizon_h INT NOT NULL DEFAULT 24,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weather_cache_project ON weather_cache (tenant_id, project_id, expires_at DESC);

-- RLS for tenant isolation
ALTER TABLE alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_geo ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS alert_rules_iso ON alert_rules;
CREATE POLICY alert_rules_iso ON alert_rules FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS alert_log_iso ON alert_log;
CREATE POLICY alert_log_iso ON alert_log FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS webhooks_iso ON webhooks;
CREATE POLICY webhooks_iso ON webhooks FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS progress_geo_iso ON progress_geo;
CREATE POLICY progress_geo_iso ON progress_geo FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS vendor_scores_iso ON vendor_scores;
CREATE POLICY vendor_scores_iso ON vendor_scores FOR ALL
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

COMMENT ON TABLE alert_log IS '10 alert rule fires per M-15. dedup_hash prevents same-day repeats.';
COMMENT ON TABLE progress_geo IS 'Server-side geo validation. Source of truth, NOT photo EXIF (M-34).';
COMMENT ON TABLE weather_cache IS 'OpenWeatherMap response cache (M-35). 6h TTL keeps us within free tier.';
